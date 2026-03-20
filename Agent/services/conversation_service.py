#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对话记录管理服务
负责Redis实时存储和MinIO归档的协调
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from Agent.memory.redis_session import RedisSessionPool, get_session_pool
from Agent.config.settings import Config


class ConversationService:
    """
    对话记录管理服务
    管理会话中的消息记录，支持实时存储和归档
    """
    
    def __init__(self):
        """初始化对话服务"""
        self.session_pool: RedisSessionPool = get_session_pool()
        self.minio_service = None
        
        # 延迟加载MinIO服务
        try:
            from .minio_storage import get_minio_service
            self.minio_service = get_minio_service()
            logger.info("MinIO服务已加载")
        except Exception as e:
            logger.warning(f"MinIO服务加载失败: {str(e)}")
    
    def _get_message_key(self, session_id: str) -> str:
        """获取消息存储的Redis key"""
        return f"agent:conversation:{session_id}:messages"
    
    def _get_metadata_key(self, session_id: str) -> str:
        """获取元数据存储的Redis key"""
        return f"agent:conversation:{session_id}:metadata"
    
    def append_message(self, 
                      session_id: str, 
                      role: str, 
                      content: str,
                      message_type: str = "text",
                      extra_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        追加消息到对话记录
        
        Args:
            session_id: 会话ID
            role: 角色 (user/assistant/system)
            content: 消息内容
            message_type: 消息类型
            extra_data: 额外数据
        
        Returns:
            bool: 是否成功
        """
        try:
            message = {
                "id": f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
                "role": role,
                "content": content,
                "type": message_type,
                "timestamp": datetime.now().isoformat(),
                "extra_data": extra_data or {}
            }
            
            # 使用Redis列表存储消息
            redis_client = self.session_pool.redis_client
            message_key = self._get_message_key(session_id)
            
            # 将消息添加到列表
            redis_client.rpush(message_key, json.dumps(message, ensure_ascii=False))
            
            # 设置过期时间（与会话相同）
            redis_client.expire(message_key, Config.REDIS_SESSION_TTL)
            
            # 更新会话中的对话历史
            session = self.session_pool.get_session(session_id)
            if session:
                if session.conversation_history is None:
                    session.conversation_history = []
                session.conversation_history.append({
                    "role": role,
                    "content": content,
                    "timestamp": message["timestamp"]
                })
                self.session_pool.update_session_context(session_id, session)
            
            logger.debug(f"消息已追加到会话 {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"追加消息失败: {str(e)}")
            return False
    
    def get_conversation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取完整对话记录
        
        Args:
            session_id: 会话ID
        
        Returns:
            Optional[Dict]: 对话记录
        """
        try:
            redis_client = self.session_pool.redis_client
            message_key = self._get_message_key(session_id)
            metadata_key = self._get_metadata_key(session_id)
            
            # 获取所有消息
            messages_raw = redis_client.lrange(message_key, 0, -1)
            messages = [json.loads(m) for m in messages_raw]
            
            # 获取元数据
            metadata_raw = redis_client.get(metadata_key)
            metadata = json.loads(metadata_raw) if metadata_raw else {}
            
            # 获取会话信息
            session = self.session_pool.get_session(session_id)
            
            return {
                "session_id": session_id,
                "metadata": {
                    "created_at": metadata.get("created_at"),
                    "last_activity": datetime.now().isoformat(),
                    "message_count": len(messages),
                    "plan_id": session.plan_id if session else None,
                    "user_id": session.user_id if session else None,
                    **metadata
                },
                "context": {
                    "original_plan": session.original_plan if session else None,
                    "current_plan": session.current_plan if session else None,
                } if session else {},
                "messages": messages
            }
            
        except Exception as e:
            logger.error(f"获取对话记录失败: {str(e)}")
            return None
    
    def get_conversation_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取对话摘要（用于历史列表展示）
        
        Args:
            session_id: 会话ID
        
        Returns:
            Optional[Dict]: 对话摘要
        """
        try:
            session = self.session_pool.get_session(session_id)
            if not session:
                return None
            
            redis_client = self.session_pool.redis_client
            message_key = self._get_message_key(session_id)
            message_count = redis_client.llen(message_key)
            
            # 获取第一条用户消息作为标题
            first_message = redis_client.lindex(message_key, 0)
            title = "未命名会话"
            if first_message:
                msg_data = json.loads(first_message)
                if msg_data.get("role") == "user":
                    title = msg_data.get("content", "")[:30] + "..."
            
            return {
                "session_id": session_id,
                "plan_id": session.plan_id,
                "title": title,
                "destination": session.departure_location or "未知目的地",
                "message_count": message_count,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "status": "active" if message_count > 0 else "empty",
                "has_export": bool(session.current_plan)
            }
            
        except Exception as e:
            logger.error(f"获取对话摘要失败: {str(e)}")
            return None
    
    def archive_conversation(self, 
                            session_id: str, 
                            username: str) -> Dict[str, Any]:
        """
        归档对话记录到MinIO
        
        Args:
            session_id: 会话ID
            username: 用户名
        
        Returns:
            Dict: 归档结果
        """
        if not self.minio_service:
            return {"success": False, "error": "MinIO服务不可用"}
        
        try:
            # 获取完整对话记录
            conversation = self.get_conversation(session_id)
            if not conversation:
                return {"success": False, "error": "对话记录不存在"}
            
            # 添加归档元数据
            conversation["metadata"]["archived_at"] = datetime.now().isoformat()
            conversation["metadata"]["archived_by"] = username
            
            # 上传到MinIO
            result = self.minio_service.upload_conversation(
                username=username,
                session_id=session_id,
                conversation_data=conversation
            )
            
            if result.get("success"):
                # 更新会话的归档状态
                session = self.session_pool.get_session(session_id)
                if session:
                    # 可以在这里标记会话已归档
                    pass
                
                logger.info(f"对话记录已归档: {result['object_path']}")
                
                # 可选：归档后删除Redis中的消息（保留会话）
                if Config.AUTO_ARCHIVE_ENABLED:
                    self._cleanup_redis_messages(session_id)
            
            return result
            
        except Exception as e:
            logger.error(f"归档对话记录失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _cleanup_redis_messages(self, session_id: str):
        """清理Redis中的消息数据"""
        try:
            redis_client = self.session_pool.redis_client
            message_key = self._get_message_key(session_id)
            metadata_key = self._get_metadata_key(session_id)
            
            redis_client.delete(message_key, metadata_key)
            logger.info(f"已清理Redis消息数据: {session_id}")
        except Exception as e:
            logger.warning(f"清理Redis消息数据失败: {str(e)}")
    
    def get_user_conversations(self, 
                              user_id: str,
                              status: Optional[str] = None,
                              limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取用户的对话列表
        
        Args:
            user_id: 用户ID
            status: 状态筛选 (active, archived)
            limit: 返回数量限制
        
        Returns:
            List[Dict]: 对话列表
        """
        try:
            # 从Redis获取用户的会话索引
            redis_client = self.session_pool.redis_client
            user_sessions_key = f"agent:user:{user_id}:sessions"
            
            session_ids = redis_client.smembers(user_sessions_key)
            conversations = []
            
            for session_id in session_ids:
                summary = self.get_conversation_summary(session_id)
                if summary:
                    conversations.append(summary)
            
            # 按最后活动时间排序
            conversations.sort(
                key=lambda x: x.get("last_activity", ""), 
                reverse=True
            )
            
            return conversations[:limit]
            
        except Exception as e:
            logger.error(f"获取用户对话列表失败: {str(e)}")
            return []
    
    def search_conversations(self, 
                            user_id: str, 
                            keyword: str) -> List[Dict[str, Any]]:
        """
        搜索对话内容
        
        Args:
            user_id: 用户ID
            keyword: 搜索关键词
        
        Returns:
            List[Dict]: 匹配的对话列表
        """
        try:
            conversations = self.get_user_conversations(user_id)
            results = []
            
            for conv_summary in conversations:
                session_id = conv_summary["session_id"]
                conversation = self.get_conversation(session_id)
                
                if conversation:
                    # 搜索消息内容
                    matching_messages = []
                    for msg in conversation.get("messages", []):
                        if keyword.lower() in msg.get("content", "").lower():
                            matching_messages.append(msg)
                    
                    if matching_messages:
                        results.append({
                            **conv_summary,
                            "matches": len(matching_messages),
                            "matching_messages": matching_messages[:3]  # 只返回前3条匹配
                        })
            
            return results
            
        except Exception as e:
            logger.error(f"搜索对话失败: {str(e)}")
            return []
    
    def initialize_conversation_metadata(self, 
                                        session_id: str,
                                        metadata: Dict[str, Any]) -> bool:
        """
        初始化对话元数据
        
        Args:
            session_id: 会话ID
            metadata: 元数据
        
        Returns:
            bool: 是否成功
        """
        try:
            redis_client = self.session_pool.redis_client
            metadata_key = self._get_metadata_key(session_id)
            
            default_metadata = {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "message_count": 0,
                **metadata
            }
            
            redis_client.setex(
                metadata_key,
                Config.REDIS_SESSION_TTL,
                json.dumps(default_metadata, ensure_ascii=False)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"初始化对话元数据失败: {str(e)}")
            return False
    
    def update_conversation_metadata(self,
                                    session_id: str,
                                    updates: Dict[str, Any]) -> bool:
        """
        更新对话元数据
        
        Args:
            session_id: 会话ID
            updates: 更新的字段
        
        Returns:
            bool: 是否成功
        """
        try:
            redis_client = self.session_pool.redis_client
            metadata_key = self._get_metadata_key(session_id)
            
            # 获取现有元数据
            existing = redis_client.get(metadata_key)
            metadata = json.loads(existing) if existing else {}
            
            # 更新字段
            metadata.update(updates)
            metadata["last_updated"] = datetime.now().isoformat()
            
            # 保存
            redis_client.setex(
                metadata_key,
                Config.REDIS_SESSION_TTL,
                json.dumps(metadata, ensure_ascii=False)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"更新对话元数据失败: {str(e)}")
            return False


# 全局对话服务实例
_conversation_service_instance = None

def get_conversation_service() -> ConversationService:
    """
    获取全局对话服务实例
    
    Returns:
        ConversationService: 对话服务实例
    """
    global _conversation_service_instance
    if _conversation_service_instance is None:
        _conversation_service_instance = ConversationService()
    return _conversation_service_instance


def reset_conversation_service():
    """重置对话服务实例（用于测试）"""
    global _conversation_service_instance
    _conversation_service_instance = None
