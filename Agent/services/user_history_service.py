#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户历史记录管理服务
维护用户会话历史索引和摘要
"""

import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from loguru import logger

from Agent.memory.redis_session import RedisSessionPool, get_session_pool
from Agent.config.settings import Config


class UserHistoryService:
    """
    用户历史记录管理服务
    管理用户的会话历史、统计信息和偏好
    """
    
    def __init__(self):
        """初始化用户历史服务"""
        self.session_pool: RedisSessionPool = get_session_pool()
        self.minio_service = None
        
        # 延迟加载MinIO服务
        try:
            from .minio_storage import get_minio_service
            self.minio_service = get_minio_service()
        except Exception as e:
            logger.warning(f"MinIO服务加载失败: {str(e)}")
    
    def _get_user_sessions_key(self, user_id: str) -> str:
        """获取用户会话索引的Redis key"""
        return f"agent:user:{user_id}:sessions"
    
    def _get_user_history_key(self, user_id: str) -> str:
        """获取用户历史摘要的Redis key"""
        return f"agent:user:{user_id}:history:summary"
    
    def _get_user_stats_key(self, user_id: str) -> str:
        """获取用户统计信息的Redis key"""
        return f"agent:user:{user_id}:stats"
    
    def _get_user_favorites_key(self, user_id: str) -> str:
        """获取用户收藏列表的Redis key"""
        return f"agent:user:{user_id}:favorites"
    
    def add_session_to_history(self, 
                              user_id: str, 
                              session_summary: Dict[str, Any]) -> bool:
        """
        添加会话到用户历史
        
        Args:
            user_id: 用户ID
            session_summary: 会话摘要信息
        
        Returns:
            bool: 是否成功
        """
        try:
            redis_client = self.session_pool.redis_client
            
            # 添加到用户会话索引
            user_sessions_key = self._get_user_sessions_key(user_id)
            session_id = session_summary.get("session_id")
            
            redis_client.sadd(user_sessions_key, session_id)
            redis_client.expire(user_sessions_key, Config.REDIS_SESSION_TTL * 7)  # 保留7天
            
            # 添加到历史摘要列表（Sorted Set，按时间排序）
            user_history_key = self._get_user_history_key(user_id)
            score = datetime.now().timestamp()
            
            # 序列化摘要信息
            summary_json = json.dumps(session_summary, ensure_ascii=False)
            redis_client.zadd(user_history_key, {summary_json: score})
            redis_client.expire(user_history_key, Config.REDIS_SESSION_TTL * 7)
            
            # 更新用户统计
            self._update_user_stats(user_id, session_summary)
            
            logger.info(f"会话已添加到用户历史: user={user_id}, session={session_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加会话到历史失败: {str(e)}")
            return False
    
    def _update_user_stats(self, user_id: str, session_summary: Dict[str, Any]):
        """更新用户统计信息"""
        try:
            redis_client = self.session_pool.redis_client
            stats_key = self._get_user_stats_key(user_id)
            
            # 获取现有统计
            stats_raw = redis_client.get(stats_key)
            stats = json.loads(stats_raw) if stats_raw else {
                "total_sessions": 0,
                "total_messages": 0,
                "total_exports": 0,
                "favorite_count": 0,
                "destinations": [],
                "first_session": None,
                "last_session": None
            }
            
            # 更新统计
            stats["total_sessions"] += 1
            stats["total_messages"] += session_summary.get("message_count", 0)
            stats["last_session"] = datetime.now().isoformat()
            
            if stats["first_session"] is None:
                stats["first_session"] = datetime.now().isoformat()
            
            # 记录目的地
            destination = session_summary.get("destination")
            if destination and destination not in stats["destinations"]:
                stats["destinations"].append(destination)
            
            # 保存统计
            redis_client.setex(
                stats_key,
                Config.REDIS_SESSION_TTL * 30,  # 统计保留30天
                json.dumps(stats, ensure_ascii=False)
            )
            
        except Exception as e:
            logger.error(f"更新用户统计失败: {str(e)}")
    
    def get_recent_sessions(self, 
                           user_id: str, 
                           limit: int = 10,
                           include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        获取用户最近会话
        
        Args:
            user_id: 用户ID
            limit: 返回数量
            include_archived: 是否包含已归档
        
        Returns:
            List[Dict]: 会话列表
        """
        try:
            redis_client = self.session_pool.redis_client
            user_history_key = self._get_user_history_key(user_id)
            
            # 获取最近的会话摘要（按时间倒序）
            results = redis_client.zrevrange(user_history_key, 0, limit - 1)
            
            sessions = []
            for result in results:
                try:
                    summary = json.loads(result)
                    
                    # 获取会话的当前状态
                    session_id = summary.get("session_id")
                    session = self.session_pool.get_session(session_id)
                    
                    if session:
                        summary["status"] = "active"
                        summary["current_plan"] = session.current_plan
                    else:
                        summary["status"] = "expired"
                    
                    sessions.append(summary)
                    
                except json.JSONDecodeError:
                    continue
            
            return sessions
            
        except Exception as e:
            logger.error(f"获取最近会话失败: {str(e)}")
            return []
    
    def get_session_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户会话统计信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict: 统计信息
        """
        try:
            redis_client = self.session_pool.redis_client
            stats_key = self._get_user_stats_key(user_id)
            
            stats_raw = redis_client.get(stats_key)
            if stats_raw:
                stats = json.loads(stats_raw)
            else:
                stats = {
                    "total_sessions": 0,
                    "total_messages": 0,
                    "total_exports": 0,
                    "favorite_count": 0,
                    "destinations": [],
                    "first_session": None,
                    "last_session": None
                }
            
            # 添加活跃会话数
            user_sessions_key = self._get_user_sessions_key(user_id)
            active_sessions = redis_client.scard(user_sessions_key)
            stats["active_sessions"] = active_sessions
            
            return stats
            
        except Exception as e:
            logger.error(f"获取会话统计失败: {str(e)}")
            return {}
    
    def get_timeline(self, 
                    user_id: str, 
                    days: int = 30) -> List[Dict[str, Any]]:
        """
        获取用户时间线视图
        
        Args:
            user_id: 用户ID
            days: 查询天数
        
        Returns:
            List[Dict]: 时间线数据
        """
        try:
            redis_client = self.session_pool.redis_client
            user_history_key = self._get_user_history_key(user_id)
            
            # 计算时间范围
            cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
            
            # 获取时间范围内的会话
            results = redis_client.zrevrangebyscore(
                user_history_key,
                "+inf",
                cutoff_time,
                withscores=True
            )
            
            timeline = []
            for result, score in results:
                try:
                    summary = json.loads(result)
                    summary["timestamp"] = datetime.fromtimestamp(score).isoformat()
                    timeline.append(summary)
                except json.JSONDecodeError:
                    continue
            
            return timeline
            
        except Exception as e:
            logger.error(f"获取时间线失败: {str(e)}")
            return []
    
    def add_favorite(self, user_id: str, session_id: str) -> bool:
        """
        收藏会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
        
        Returns:
            bool: 是否成功
        """
        try:
            redis_client = self.session_pool.redis_client
            favorites_key = self._get_user_favorites_key(user_id)
            
            redis_client.sadd(favorites_key, session_id)
            redis_client.expire(favorites_key, Config.REDIS_SESSION_TTL * 30)
            
            # 更新收藏数统计
            self._update_favorite_count(user_id, 1)
            
            logger.info(f"会话已收藏: user={user_id}, session={session_id}")
            return True
            
        except Exception as e:
            logger.error(f"收藏会话失败: {str(e)}")
            return False
    
    def remove_favorite(self, user_id: str, session_id: str) -> bool:
        """
        取消收藏会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
        
        Returns:
            bool: 是否成功
        """
        try:
            redis_client = self.session_pool.redis_client
            favorites_key = self._get_user_favorites_key(user_id)
            
            redis_client.srem(favorites_key, session_id)
            
            # 更新收藏数统计
            self._update_favorite_count(user_id, -1)
            
            logger.info(f"会话已取消收藏: user={user_id}, session={session_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消收藏失败: {str(e)}")
            return False
    
    def _update_favorite_count(self, user_id: str, delta: int):
        """更新收藏数"""
        try:
            redis_client = self.session_pool.redis_client
            stats_key = self._get_user_stats_key(user_id)
            
            stats_raw = redis_client.get(stats_key)
            if stats_raw:
                stats = json.loads(stats_raw)
                stats["favorite_count"] = max(0, stats.get("favorite_count", 0) + delta)
                
                redis_client.setex(
                    stats_key,
                    Config.REDIS_SESSION_TTL * 30,
                    json.dumps(stats, ensure_ascii=False)
                )
        except Exception as e:
            logger.error(f"更新收藏数失败: {str(e)}")
    
    def get_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户收藏的会话
        
        Args:
            user_id: 用户ID
        
        Returns:
            List[Dict]: 收藏的会话列表
        """
        try:
            redis_client = self.session_pool.redis_client
            favorites_key = self._get_user_favorites_key(user_id)
            
            session_ids = redis_client.smembers(favorites_key)
            favorites = []
            
            for session_id in session_ids:
                # 从会话池获取会话信息
                session = self.session_pool.get_session(session_id)
                if session:
                    favorites.append({
                        "session_id": session_id,
                        "plan_id": session.plan_id,
                        "destination": session.departure_location,
                        "created_at": session.created_at,
                        "last_activity": session.last_activity
                    })
            
            return favorites
            
        except Exception as e:
            logger.error(f"获取收藏列表失败: {str(e)}")
            return []
    
    def cleanup_old_sessions(self, 
                            user_id: str, 
                            days: int = 90) -> int:
        """
        清理用户的旧会话记录
        
        Args:
            user_id: 用户ID
            days: 保留天数
        
        Returns:
            int: 清理的数量
        """
        try:
            redis_client = self.session_pool.redis_client
            user_history_key = self._get_user_history_key(user_id)
            
            # 计算截止时间
            cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
            
            # 删除旧记录
            removed = redis_client.zremrangebyscore(
                user_history_key,
                "-inf",
                cutoff_time
            )
            
            logger.info(f"已清理用户 {user_id} 的 {removed} 条旧会话记录")
            return removed
            
        except Exception as e:
            logger.error(f"清理旧会话失败: {str(e)}")
            return 0
    
    def get_user_storage_usage(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户存储使用情况
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict: 存储使用情况
        """
        try:
            stats = self.get_session_stats(user_id)
            
            # 估算存储使用（实际需要从MinIO获取）
            estimated_usage = {
                "conversations_mb": stats.get("total_sessions", 0) * 0.5,  # 估算每个会话0.5MB
                "pdfs_mb": stats.get("total_exports", 0) * 2,  # 估算每个PDF 2MB
                "total_mb": 0,
                "total_gb": 0
            }
            estimated_usage["total_mb"] = (
                estimated_usage["conversations_mb"] + 
                estimated_usage["pdfs_mb"]
            )
            estimated_usage["total_gb"] = round(estimated_usage["total_mb"] / 1024, 2)
            
            return {
                "user_id": user_id,
                "estimated_usage": estimated_usage,
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"获取存储使用情况失败: {str(e)}")
            return {}


# 全局用户历史服务实例
_user_history_service_instance = None

def get_user_history_service() -> UserHistoryService:
    """
    获取全局用户历史服务实例
    
    Returns:
        UserHistoryService: 用户历史服务实例
    """
    global _user_history_service_instance
    if _user_history_service_instance is None:
        _user_history_service_instance = UserHistoryService()
    return _user_history_service_instance


def reset_user_history_service():
    """重置用户历史服务实例（用于测试）"""
    global _user_history_service_instance
    _user_history_service_instance = None
