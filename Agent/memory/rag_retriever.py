# -*- coding: utf-8 -*-
"""
RAG 检索模块
实现双轨混合检索增强生成，融合 ChromaDB 向量检索与 Neo4j 知识图谱检索
"""

import concurrent.futures
from typing import Dict, Any, List, Optional
from loguru import logger

from .vector_store import get_vector_store

from Agent.config.memory_budget import memory_budget

# 单个RAG条目的字符上限，从 rag_context_max_chars 派生（约为1/4，最少200）
_RAG_ITEM_MAX_CHARS = max(memory_budget.rag_context_max_chars // 4, 200)


class RAGRetriever:
    """
    双轨混合 RAG 检索器
    
    轨道1: ChromaDB 向量语义检索 —— 基于嵌入相似度匹配相关文档
    轨道2: Neo4j 知识图谱检索 —— 基于实体关系锚定事实，抑制知识幻觉
    
    两轨结果去重合并后统一注入 LLM 上下文，实现"向量语义召回 + 图谱结构化锚定"的互补增强。
    """

    def __init__(self, vector_store=None, knowledge_graph=None):
        self.vector_store = vector_store or get_vector_store()
        if self.vector_store is None:
            logger.warning("向量存储不可用，RAG 功能受限")
        self._knowledge_graph = knowledge_graph
        self._kg_checked = False

    @property
    def knowledge_graph(self):
        if not self._kg_checked:
            self._kg_checked = True
            if self._knowledge_graph is None:
                try:
                    from .knowledge_graph import get_knowledge_graph
                    self._knowledge_graph = get_knowledge_graph()
                except Exception as e:
                    logger.debug(f"知识图谱加载失败: {e}")
                    self._knowledge_graph = None
        return self._knowledge_graph

    def _kg_available(self) -> bool:
        kg = self.knowledge_graph
        return kg is not None and kg.is_connected()

    def retrieve_context(self, query: str, user_id: str = None,
                        top_k: int = 3) -> Dict[str, Any]:
        """
        双轨混合检索相关上下文（并行执行）

        轨道1: ChromaDB 向量检索（对话、知识、景点）
        轨道2: Neo4j 知识图谱检索（实体关系、结构化事实）

        两轨 I/O 独立，并行执行以降低延迟 ~40-50%。

        Args:
            query: 用户查询
            user_id: 用户ID（用于检索用户相关对话）
            top_k: 每类返回的结果数量

        Returns:
            包含双轨检索结果的字典
        """
        vector_results = {'conversations': [], 'heritage_knowledge': [], 'attractions': []}
        graph_results = []

        has_vector = self.vector_store is not None
        has_kg = self._kg_available()

        if has_vector and has_kg:
            # 双轨并行检索
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                v_future = executor.submit(self.vector_store.hybrid_search, query, user_id, top_k)
                kg_future = executor.submit(self._retrieve_from_knowledge_graph, query, top_k)
                try:
                    vector_results = v_future.result(timeout=30)
                except Exception as e:
                    logger.debug(f"向量检索失败: {e}")
                try:
                    graph_results = kg_future.result(timeout=30)
                except Exception as e:
                    logger.debug(f"知识图谱检索失败: {e}")
        elif has_vector:
            vector_results = self.vector_store.hybrid_search(query, user_id, top_k)
        elif has_kg:
            graph_results = self._retrieve_from_knowledge_graph(query, top_k)

        vector_results['knowledge_graph'] = graph_results
        return vector_results

    def _retrieve_from_knowledge_graph(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        从 Neo4j 知识图谱检索结构化事实
        
        策略:
        1. 关键词匹配查询非遗项目节点
        2. 沿关系边扩展查询关联实体（类别、地区、级别）
        3. 返回带关系锚定的结构化事实
        """
        kg = self.knowledge_graph
        if not kg or not kg.is_connected():
            return []

        results = []
        try:
            with kg.driver.session() as session:
                cypher = """
                    MATCH (h:Heritage)
                    WHERE h.name CONTAINS $kw 
                       OR h.category CONTAINS $kw 
                       OR h.region CONTAINS $kw
                       OR h.description CONTAINS $kw
                    OPTIONAL MATCH (h)-[:BELONGS_TO]->(c:Category)
                    OPTIONAL MATCH (h)-[:LOCATED_AT]->(r:Region)
                    OPTIONAL MATCH (h)-[:HAS_LEVEL]->(l:Level)
                    RETURN h.id AS id, h.name AS name, h.category AS category,
                           h.region AS region, h.level AS level,
                           h.description AS description,
                           collect(DISTINCT c.name) AS related_categories,
                           collect(DISTINCT r.name) AS related_regions,
                           collect(DISTINCT l.name) AS related_levels
                    LIMIT $top_k
                """
                result = session.run(cypher, kw=query, top_k=top_k)
                for record in result:
                    item = {
                        'id': record.get('id'),
                        'name': record.get('name', ''),
                        'category': record.get('category', ''),
                        'region': record.get('region', ''),
                        'level': record.get('level', ''),
                        'description': (record.get('description') or '')[:_RAG_ITEM_MAX_CHARS],
                        'related_categories': [c for c in record.get('related_categories', []) if c],
                        'related_regions': [r for r in record.get('related_regions', []) if r],
                        'related_levels': [l for l in record.get('related_levels', []) if l],
                        'source': 'knowledge_graph',
                    }
                    results.append(item)
            if results:
                logger.info(f"知识图谱检索到 {len(results)} 条结构化事实: {query}")
        except Exception as e:
            logger.debug(f"知识图谱检索失败: {e}")
        return results

    def build_rag_prompt(self, query: str, user_id: str = None,
                         top_k: int = 3) -> str:
        """
        构建双轨混合 RAG 提示词
        
        将向量检索结果与知识图谱检索结果合并，去重后注入上下文。
        图谱结果提供实体关系锚定，向量结果提供语义相似内容，
        两者互补增强，有效抑制知识幻觉。
        
        Args:
            query: 用户查询
            user_id: 用户ID
            top_k: 检索数量
        
        Returns:
            包含双轨检索上下文的提示词
        """
        context = self.retrieve_context(query, user_id, top_k)

        sections = []

        if context['conversations']:
            conv_section = self._format_conversations(context['conversations'])
            sections.append(conv_section)

        vector_names = set()
        if context['heritage_knowledge']:
            for item in context['heritage_knowledge']:
                name = item.get('metadata', {}).get('name', '')
                if name:
                    vector_names.add(name)
            knowledge_section = self._format_knowledge(context['heritage_knowledge'])
            sections.append(knowledge_section)

        if context.get('knowledge_graph'):
            graph_section = self._format_graph_facts(
                context['knowledge_graph'], exclude_names=vector_names
            )
            if graph_section:
                sections.append(graph_section)

        if context['attractions']:
            attraction_section = self._format_attractions(context['attractions'])
            sections.append(attraction_section)

        if not sections:
            return ""

        return "\n\n".join(sections)

    def _format_conversations(self, conversations: List[Dict]) -> str:
        lines = ["【相关历史对话】"]
        for conv in conversations:
            metadata = conv.get('metadata', {})
            role = metadata.get('role', 'unknown')
            content = conv.get('content', '')[:_RAG_ITEM_MAX_CHARS]
            lines.append(f"- [{role}] {content}")
        return '\n'.join(lines)

    def _format_knowledge(self, knowledge: List[Dict]) -> str:
        lines = ["【相关知识（向量检索）】"]
        for item in knowledge:
            metadata = item.get('metadata', {})
            name = metadata.get('name', '未知')
            content = item.get('content', '')[:_RAG_ITEM_MAX_CHARS]
            lines.append(f"- **{name}**: {content}")
        return '\n'.join(lines)

    def _format_graph_facts(self, graph_results: List[Dict], exclude_names: set = None) -> str:
        """
        格式化知识图谱检索结果，突出实体关系锚定
        
        与向量检索结果去重：如果某个非遗项目已通过向量检索返回，
        则跳过图谱中的同名项目，避免冗余。
        """
        if not graph_results:
            return ""
        exclude_names = exclude_names or set()
        lines = ["【知识图谱事实锚定（图谱检索）】"]
        for item in graph_results:
            name = item.get('name', '')
            if name in exclude_names:
                continue
            fact_parts = [f"- **{name}**"]
            if item.get('category'):
                fact_parts.append(f"  类别: {item['category']}")
            if item.get('region'):
                fact_parts.append(f"  地区: {item['region']}")
            if item.get('level'):
                fact_parts.append(f"  级别: {item['level']}")
            if item.get('description'):
                fact_parts.append(f"  描述: {item['description'][:_RAG_ITEM_MAX_CHARS]}")
            related_cats = item.get('related_categories', [])
            if related_cats:
                fact_parts.append(f"  关联类别: {', '.join(related_cats[:3])}")
            related_regions = item.get('related_regions', [])
            if related_regions:
                fact_parts.append(f"  关联地区: {', '.join(related_regions[:3])}")
            lines.append('\n'.join(fact_parts))
        if len(lines) <= 1:
            return ""
        return '\n'.join(lines)

    def _format_attractions(self, attractions: List[Dict]) -> str:
        lines = ["【相关景点】"]
        for item in attractions:
            metadata = item.get('metadata', {})
            name = metadata.get('name', '未知')
            content = item.get('content', '')[:_RAG_ITEM_MAX_CHARS]
            lines.append(f"- **{name}**: {content}")
        return '\n'.join(lines)

    def get_relevant_heritage(self, query: str, top_k: int = 5) -> List[Dict]:
        if self.vector_store is None:
            return []
        results = self.vector_store.search_heritage_knowledge(query, top_k)
        return [r.get('metadata', {}) for r in results]

    def get_relevant_attractions(self, query: str, top_k: int = 5) -> List[Dict]:
        if self.vector_store is None:
            return []
        results = self.vector_store.search_attractions(query, top_k)
        return [r.get('metadata', {}) for r in results]


_rag_retriever_instance: Optional[RAGRetriever] = None


def get_rag_retriever() -> RAGRetriever:
    global _rag_retriever_instance
    if _rag_retriever_instance is None:
        _rag_retriever_instance = RAGRetriever()
    return _rag_retriever_instance
