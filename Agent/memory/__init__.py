# -*- coding: utf-8 -*-
"""
记忆模块
实现分层记忆架构，支持上下文融合和持久化存储

架构层次：
- Level 1: 会话层 (内存) - 毫秒级
- Level 2: 持久化层 - 秒级
- Level 3: 向量层 - 秒级
- Level 4: 知识图谱层 (Neo4j) - 秒级
"""

from .session import SessionPool, SessionContext, get_session_pool
from .sqlite_store import SQLiteStore, get_sqlite_store
from .user_profile import UserProfileManager, get_user_profile_manager
from .vector_store import VectorStore, get_vector_store
from .rag_retriever import RAGRetriever, get_rag_retriever
from .conversation_vector_service import ConversationVectorService, get_conversation_vector_service
from .knowledge_graph import KnowledgeGraph, get_knowledge_graph
from .heritage_query_service import HeritageQueryService, get_heritage_query_service

__all__ = [
    'SessionPool',
    'SessionContext',
    'get_session_pool',
    'SQLiteStore',
    'get_sqlite_store',
    'UserProfileManager',
    'get_user_profile_manager',
    'VectorStore',
    'get_vector_store',
    'RAGRetriever',
    'get_rag_retriever',
    'ConversationVectorService',
    'get_conversation_vector_service',
    'KnowledgeGraph',
    'get_knowledge_graph',
    'HeritageQueryService',
    'get_heritage_query_service',
]
