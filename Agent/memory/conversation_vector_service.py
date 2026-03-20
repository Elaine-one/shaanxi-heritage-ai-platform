# -*- coding: utf-8 -*-
"""
对话向量存储服务
自动将对话存储到向量数据库，支持语义检索
"""

from typing import Dict, Any
from loguru import logger

from .vector_store import get_vector_store


class ConversationVectorService:
    """对话向量存储服务"""
    
    def __init__(self, vector_store=None):
        self.vector_store = vector_store or get_vector_store()
        if self.vector_store is None:
            logger.warning("向量存储不可用，对话向量服务受限")
    
    def save_conversation(self, session_id: str, user_id: str, 
                         role: str, content: str, 
                         metadata: Dict[str, Any] = None) -> bool:
        """
        保存对话到向量存储
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            role: 角色 (user/assistant)
            content: 对话内容
            metadata: 额外元数据
        
        Returns:
            是否保存成功
        """
        if self.vector_store is None:
            return False
        
        if not content or len(content.strip()) < 5:
            return False
        
        meta = metadata or {}
        
        return self.vector_store.add_conversation(
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            metadata=meta
        )
    
    def save_conversation_batch(self, conversations: list) -> int:
        """
        批量保存对话
        
        Args:
            conversations: 对话列表，每项包含 session_id, user_id, role, content, metadata
        
        Returns:
            成功保存的数量
        """
        if self.vector_store is None:
            return 0
        
        success_count = 0
        for conv in conversations:
            if self.save_conversation(
                session_id=conv.get('session_id'),
                user_id=conv.get('user_id'),
                role=conv.get('role'),
                content=conv.get('content'),
                metadata=conv.get('metadata')
            ):
                success_count += 1
        
        return success_count
    
    def search_similar_conversations(self, query: str, user_id: str = None, 
                                     top_k: int = 5) -> list:
        """
        检索相似对话
        
        Args:
            query: 查询文本
            user_id: 用户ID（可选，用于过滤）
            top_k: 返回数量
        
        Returns:
            相似对话列表
        """
        if self.vector_store is None:
            return []
        
        return self.vector_store.search_conversations(query, user_id, top_k)


_conversation_vector_service = None


def get_conversation_vector_service() -> ConversationVectorService:
    """获取对话向量服务单例"""
    global _conversation_vector_service
    if _conversation_vector_service is None:
        _conversation_vector_service = ConversationVectorService()
    return _conversation_vector_service
