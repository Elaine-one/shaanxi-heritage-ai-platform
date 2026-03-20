# -*- coding: utf-8 -*-
"""
RAG 检索模块
实现检索增强生成，结合向量检索和 LLM 生成
"""

from typing import Dict, Any, List
from loguru import logger

from .vector_store import get_vector_store


class RAGRetriever:
    """RAG 检索器"""
    
    def __init__(self, vector_store=None):
        self.vector_store = vector_store or get_vector_store()
        if self.vector_store is None:
            logger.warning("向量存储不可用，RAG 功能受限")
    
    def retrieve_context(self, query: str, user_id: str = None, 
                        top_k: int = 3) -> Dict[str, Any]:
        """
        检索相关上下文
        
        Args:
            query: 用户查询
            user_id: 用户ID（用于检索用户相关对话）
            top_k: 每类返回的结果数量
        
        Returns:
            包含检索结果的字典
        """
        if self.vector_store is None:
            return {'conversations': [], 'heritage_knowledge': [], 'attractions': []}
        
        return self.vector_store.hybrid_search(query, user_id, top_k)
    
    def build_rag_prompt(self, query: str, user_id: str = None, 
                         top_k: int = 3) -> str:
        """
        构建 RAG 提示词
        
        Args:
            query: 用户查询
            user_id: 用户ID
            top_k: 检索数量
        
        Returns:
            包含检索上下文的提示词
        """
        context = self.retrieve_context(query, user_id, top_k)
        
        sections = []
        
        if context['conversations']:
            conv_section = self._format_conversations(context['conversations'])
            sections.append(conv_section)
        
        if context['heritage_knowledge']:
            knowledge_section = self._format_knowledge(context['heritage_knowledge'])
            sections.append(knowledge_section)
        
        if context['attractions']:
            attraction_section = self._format_attractions(context['attractions'])
            sections.append(attraction_section)
        
        if not sections:
            return ""
        
        return "\n\n".join(sections)
    
    def _format_conversations(self, conversations: List[Dict]) -> str:
        """格式化对话检索结果"""
        lines = ["【相关历史对话】"]
        for conv in conversations:
            metadata = conv.get('metadata', {})
            role = metadata.get('role', 'unknown')
            content = conv.get('content', '')[:200]
            lines.append(f"- [{role}] {content}")
        return '\n'.join(lines)
    
    def _format_knowledge(self, knowledge: List[Dict]) -> str:
        """格式化知识检索结果"""
        lines = ["【相关知识】"]
        for item in knowledge:
            metadata = item.get('metadata', {})
            name = metadata.get('name', '未知')
            content = item.get('content', '')[:300]
            lines.append(f"- **{name}**: {content}")
        return '\n'.join(lines)
    
    def _format_attractions(self, attractions: List[Dict]) -> str:
        """格式化景点检索结果"""
        lines = ["【相关景点】"]
        for item in attractions:
            metadata = item.get('metadata', {})
            name = metadata.get('name', '未知')
            content = item.get('content', '')[:200]
            lines.append(f"- **{name}**: {content}")
        return '\n'.join(lines)
    
    def get_relevant_heritage(self, query: str, top_k: int = 5) -> List[Dict]:
        """获取相关的非遗项目"""
        if self.vector_store is None:
            return []
        
        results = self.vector_store.search_heritage_knowledge(query, top_k)
        return [r.get('metadata', {}) for r in results]
    
    def get_relevant_attractions(self, query: str, top_k: int = 5) -> List[Dict]:
        """获取相关的景点"""
        if self.vector_store is None:
            return []
        
        results = self.vector_store.search_attractions(query, top_k)
        return [r.get('metadata', {}) for r in results]


_rag_retriever_instance = None


def get_rag_retriever() -> RAGRetriever:
    """获取 RAG 检索器单例"""
    global _rag_retriever_instance
    if _rag_retriever_instance is None:
        _rag_retriever_instance = RAGRetriever()
    return _rag_retriever_instance
