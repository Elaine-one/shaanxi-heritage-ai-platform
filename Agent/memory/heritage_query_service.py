# -*- coding: utf-8 -*-
"""
非遗查询服务
统一查询接口，优先从知识图谱和向量数据库查询，完全解耦 MySQL
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from .knowledge_graph import get_knowledge_graph
from .vector_store import get_vector_store


class HeritageQueryService:
    """
    非遗统一查询服务
    提供统一的查询接口，优先使用知识图谱和向量数据库
    """
    
    def __init__(self):
        self.knowledge_graph = get_knowledge_graph()
        self.vector_store = get_vector_store()
    
    def query_by_ids(self, heritage_ids: List) -> List[Dict[str, Any]]:
        """
        根据 ID 列表精确查询非遗项目
        
        Args:
            heritage_ids: 非遗 ID 列表（支持整数或字符串）
        
        Returns:
            非遗项目列表
        """
        if not heritage_ids:
            return []
        
        converted_ids = []
        for hid in heritage_ids:
            if isinstance(hid, int):
                converted_ids.append(hid)
            elif isinstance(hid, str):
                if hid.isdigit():
                    converted_ids.append(int(hid))
                else:
                    logger.warning(f"heritage_id 是非数字字符串: {hid}，跳过")
            else:
                try:
                    converted_ids.append(int(hid))
                except (ValueError, TypeError):
                    logger.warning(f"无法转换 heritage_id: {hid}，跳过")
        
        if not converted_ids:
            logger.warning(f"没有有效的 heritage_id，原始输入: {heritage_ids}")
            return []
        
        if self.knowledge_graph and self.knowledge_graph.is_connected():
            results = self.knowledge_graph.query_heritage_by_ids(converted_ids)
            if results:
                logger.info(f"从知识图谱查询到 {len(results)} 条非遗数据")
                return results
        
        logger.warning(f"知识图谱查询失败，未找到 ID: {converted_ids}")
        return []
    
    def query_by_id(self, heritage_id: int) -> Optional[Dict[str, Any]]:
        """
        根据 ID 查询单个非遗项目
        
        Args:
            heritage_id: 非遗 ID
        
        Returns:
            非遗项目数据
        """
        results = self.query_by_ids([heritage_id])
        return results[0] if results else None
    
    def query_by_semantic(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not query or query.strip() == "":
            return []
        
        if self.vector_store:
            results = self.vector_store.search_heritage_knowledge(query, top_k)
            if results:
                logger.info(f"向量检索到 {len(results)} 条相关非遗")
                return [
                    {
                        'id': r['metadata'].get('heritage_id'),
                        'name': r['metadata'].get('name'),
                        'category': r['metadata'].get('category'),
                        'region': r['metadata'].get('region'),
                        'level': r['metadata'].get('level'),
                        'distance': r.get('distance', 0),
                        'content': r.get('content', '')
                    }
                    for r in results
                ]
        
        logger.warning(f"向量检索失败，降级到知识图谱关键词搜索: {query}")
        return self._fallback_kg_keyword_search(query, top_k)
    
    def _fallback_kg_keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.knowledge_graph or not self.knowledge_graph.is_connected():
            return []
        try:
            with self.knowledge_graph.driver.session() as session:
                result = session.run(
                    "MATCH (h:Heritage) "
                    "WHERE h.name CONTAINS $kw OR h.category CONTAINS $kw "
                    "OR h.region CONTAINS $kw OR h.description CONTAINS $kw "
                    "RETURN h.id AS id, h.name AS name, h.category AS category, "
                    "h.region AS region, h.level AS level "
                    "LIMIT $top_k",
                    kw=query, top_k=top_k,
                )
                items = [dict(r) for r in result]
            if items:
                logger.info(f"知识图谱关键词搜索到 {len(items)} 条非遗: {query}")
            return items
        except Exception as e:
            logger.debug(f"知识图谱关键词搜索失败: {e}")
            return []
    
    def query_related(self, heritage_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        查询相关非遗项目
        
        Args:
            heritage_id: 非遗 ID
            limit: 返回数量
        
        Returns:
            相关非遗项目列表
        """
        if self.knowledge_graph and self.knowledge_graph.is_connected():
            results = self.knowledge_graph.query_related_heritage(heritage_id, limit)
            if results:
                logger.info(f"查询到 {len(results)} 条相关非遗")
                return results
        
        return []
    
    def query_by_region(self, region: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        查询指定地区的非遗项目
        
        Args:
            region: 地区名称
            limit: 返回数量
        
        Returns:
            该地区的非遗项目列表
        """
        if self.knowledge_graph and self.knowledge_graph.is_connected():
            results = self.knowledge_graph.query_by_region(region, limit)
            if results:
                logger.info(f"查询到 {region} 地区 {len(results)} 条非遗")
                return results
        
        return []
    
    def query_nearby_regions(self, region: str, distance_km: float = 100) -> List[str]:
        """
        查询邻近地区
        
        Args:
            region: 地区名称
            distance_km: 距离阈值（公里）
        
        Returns:
            邻近地区列表
        """
        if self.knowledge_graph and self.knowledge_graph.is_connected():
            return self.knowledge_graph.query_nearby_regions(region, distance_km)
        return []
    
    def query_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        查询指定类别的非遗项目
        
        Args:
            category: 类别名称
            limit: 返回数量
        
        Returns:
            该类别的非遗项目列表
        """
        if self.knowledge_graph and self.knowledge_graph.is_connected():
            results = self.knowledge_graph.query_by_category(category, limit)
            if results:
                logger.info(f"查询到 {category} 类别 {len(results)} 条非遗")
                return results
        
        return []
    
    def hybrid_query(self, query: str, region: str = None, 
                    category: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        if not query or query.strip() == "":
            return []
        
        semantic_results = self.query_by_semantic(query, top_k * 2)
        
        filtered_results = []
        for item in semantic_results:
            if region and item.get('region') != region:
                continue
            if category and item.get('category') != category:
                continue
            filtered_results.append(item)
            if len(filtered_results) >= top_k:
                break
        
        if not filtered_results and (region or category):
            filtered_results = self._kg_structured_query(query, region, category, top_k)
        
        return filtered_results
    
    def _kg_structured_query(self, query: str, region: str, category: str, top_k: int) -> List[Dict[str, Any]]:
        if not self.knowledge_graph or not self.knowledge_graph.is_connected():
            return []
        try:
            conditions = ["h.name CONTAINS $kw OR h.category CONTAINS $kw OR h.description CONTAINS $kw"]
            if region:
                conditions.append("h.region CONTAINS $region")
            if category:
                conditions.append("h.category CONTAINS $category")
            where_clause = " AND ".join(conditions)
            params = {"kw": query, "top_k": top_k}
            if region:
                params["region"] = region
            if category:
                params["category"] = category
            
            with self.knowledge_graph.driver.session() as session:
                result = session.run(
                    f"MATCH (h:Heritage) WHERE {where_clause} "
                    "RETURN h.id AS id, h.name AS name, h.category AS category, "
                    "h.region AS region, h.level AS level "
                    "LIMIT $top_k",
                    **params,
                )
                items = [dict(r) for r in result]
            if items:
                logger.info(f"知识图谱结构化查询到 {len(items)} 条非遗: query={query}, region={region}, category={category}")
            return items
        except Exception as e:
            logger.debug(f"知识图谱结构化查询失败: {e}")
            return []
    
    def get_heritage_full_info(self, heritage_id: int) -> Dict[str, Any]:
        """
        获取非遗项目完整信息（包含关联信息）
        
        Args:
            heritage_id: 非遗 ID
        
        Returns:
            完整信息字典
        """
        heritage = self.query_by_id(heritage_id)
        if not heritage:
            return {}
        
        related = self.query_related(heritage_id, limit=5)
        
        return {
            'heritage': heritage,
            'related_heritage': related
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取查询服务统计信息"""
        stats = {
            'knowledge_graph': {
                'connected': False,
                'stats': {}
            },
            'vector_store': {
                'available': False,
                'stats': {}
            }
        }
        
        if self.knowledge_graph:
            stats['knowledge_graph']['connected'] = self.knowledge_graph.is_connected()
            if stats['knowledge_graph']['connected']:
                stats['knowledge_graph']['stats'] = self.knowledge_graph.get_stats()
        
        if self.vector_store:
            stats['vector_store']['available'] = True
            stats['vector_store']['stats'] = self.vector_store.get_collection_stats()
        
        return stats


_heritage_query_service_instance = None


def get_heritage_query_service() -> HeritageQueryService:
    """获取非遗查询服务单例"""
    global _heritage_query_service_instance
    if _heritage_query_service_instance is None:
        _heritage_query_service_instance = HeritageQueryService()
    return _heritage_query_service_instance
