# -*- coding: utf-8 -*-
"""
记忆模块
实现分层记忆架构，支持上下文融合和持久化存储

架构层次：
- L0/L1: 热数据层 (Redis) — 会话、最近对话、摘要
- L2: 长期偏好层 (Neo4j) — 用户偏好、兴趣地区
- L3: 审计账本层 (SQLite) — 对话事件记录（只写不读）
- RAG: 向量检索层 (ChromaDB) — 对话向量、非遗知识、景点信息
"""

from loguru import logger

from .session import SessionPool, SessionContext, get_session_pool
from .sifter import Sifter, get_sifter

try:
    from .coordinator import MemoryCoordinator, get_memory_coordinator
except Exception as e:
    MemoryCoordinator = None
    get_memory_coordinator = None
    logger.warning(f"coordinator 导入失败（可选依赖）: {e}")

try:
    from .l2_graph_store import L2GraphStore, get_l2_graph_store
except Exception as e:
    L2GraphStore = None
    get_l2_graph_store = None
    logger.warning(f"l2_graph_store 导入失败（可选依赖）: {e}")

try:
    from .l3_sqlite_ledger import L3SQLiteLedger, get_l3_sqlite_ledger
except Exception as e:
    L3SQLiteLedger = None
    get_l3_sqlite_ledger = None
    logger.warning(f"l3_sqlite_ledger 导入失败（可选依赖）: {e}")

try:
    from .vector_store import VectorStore, get_vector_store
except Exception as e:
    VectorStore = None
    get_vector_store = None
    logger.warning(f"vector_store 导入失败（可选依赖）: {e}")

try:
    from .rag_retriever import RAGRetriever, get_rag_retriever
except Exception as e:
    RAGRetriever = None
    get_rag_retriever = None
    logger.warning(f"rag_retriever 导入失败（可选依赖）: {e}")

try:
    from .knowledge_graph import KnowledgeGraph, get_knowledge_graph
except Exception as e:
    KnowledgeGraph = None
    get_knowledge_graph = None
    logger.warning(f"knowledge_graph 导入失败（可选依赖）: {e}")

try:
    from .heritage_query_service import HeritageQueryService, get_heritage_query_service
except Exception as e:
    HeritageQueryService = None
    get_heritage_query_service = None
    logger.warning(f"heritage_query_service 导入失败（可选依赖）: {e}")

__all__ = [
    'SessionPool',
    'SessionContext',
    'get_session_pool',
    'MemoryCoordinator',
    'get_memory_coordinator',
    'L2GraphStore',
    'get_l2_graph_store',
    'L3SQLiteLedger',
    'get_l3_sqlite_ledger',
    'Sifter',
    'get_sifter',
    'VectorStore',
    'get_vector_store',
    'RAGRetriever',
    'get_rag_retriever',
    'KnowledgeGraph',
    'get_knowledge_graph',
    'HeritageQueryService',
    'get_heritage_query_service',
]
