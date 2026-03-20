#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis会话池管理系统
将会话数据持久化存储到Redis，支持分布式部署
"""

import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import asdict
from loguru import logger

from .session import SessionContext, SessionPool
from Agent.config.settings import Config

try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    Redis = None
    REDIS_AVAILABLE = False
    logger.warning("Redis库未安装，Redis会话存储不可用")

class RedisSessionPool(SessionPool):
    """
    基于Redis的会话池管理器
    继承自SessionPool，集成用户历史服务和对话记录服务
    """
    
    def __init__(self, max_sessions: int = 100, cleanup_interval: int = 3600):
        """初始化Redis会话池"""
        self.max_sessions = max_sessions
        self.cleanup_interval = cleanup_interval
        self.redis_client: Optional[Redis] = None
        self.session_key_prefix = "agent:session:"
        self.session_index_key = "agent:session:index"
        
        # 初始化服务（延迟加载）
        self._user_history_service = None
        self._conversation_service = None
        
        # 初始化Redis连接
        self._init_redis()
        
        # 启动定时清理任务（仅用于清理孤儿索引）
        self._cleanup_task = None
        self._start_cleanup_task()
        
        logger.info(f"Redis会话池初始化完成，最大会话数: {max_sessions}")
    
    @property
    def user_history_service(self):
        """延迟加载用户历史服务"""
        if self._user_history_service is None:
            try:
                from Agent.services.user_history_service import get_user_history_service
                self._user_history_service = get_user_history_service()
            except Exception as e:
                logger.warning(f"用户历史服务加载失败: {str(e)}")
        return self._user_history_service
    
    @property
    def conversation_service(self):
        """延迟加载对话服务"""
        if self._conversation_service is None:
            try:
                from Agent.services.conversation_service import get_conversation_service
                self._conversation_service = get_conversation_service()
            except Exception as e:
                logger.warning(f"对话服务加载失败: {str(e)}")
        return self._conversation_service
    
    def _init_redis(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None,
                decode_responses=True,  # 自动解码字符串
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            # 测试连接
            self.redis_client.ping()
            logger.info(f"Redis连接成功: {Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            raise RuntimeError(f"无法连接到Redis: {str(e)}")
    
    def _get_session_key(self, session_id: str) -> str:
        """获取会话在Redis中的key"""
        return f"{self.session_key_prefix}{session_id}"
    
    def _session_to_dict(self, session: SessionContext) -> Dict[str, Any]:
        """将会话对象转换为字典"""
        data = asdict(session)
        # 确保datetime对象被正确序列化
        for key in ['created_at', 'last_updated', 'last_activity']:
            if isinstance(data.get(key), datetime):
                data[key] = data[key].isoformat()
        return data
    
    def _dict_to_session(self, data: Dict[str, Any]) -> SessionContext:
        """将字典转换为会话对象"""
        return SessionContext(**data)
    
    async def create_session(self, 
                           plan_id: str, 
                           original_plan: Dict[str, Any],
                           user_id: Optional[str] = None) -> SessionContext:
        """创建新的编辑会话"""
        # 检查会话数量限制
        current_count = self.redis_client.zcard(self.session_index_key)
        if current_count >= self.max_sessions:
            # 清理最旧的会话
            await self._cleanup_oldest_sessions_redis(1)
        
        # 生成会话ID (使用更简洁的格式)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_id = f"edit_{plan_id}_{timestamp}"
        
        # 提取核心信息
        core_info = self._extract_core_info(original_plan)
        
        # 创建会话上下文
        session_context = SessionContext(
            session_id=session_id,
            plan_id=plan_id,
            user_id=user_id,
            current_plan=original_plan.copy(),
            original_plan=original_plan.copy(),
            **core_info
        )
        
        # 存储到Redis
        self._save_session_to_redis(session_context)
        
        # 添加到用户历史（如果有user_id）
        if user_id and self.user_history_service:
            try:
                session_summary = {
                    "session_id": session_id,
                    "plan_id": plan_id,
                    "user_id": user_id,
                    "title": f"规划会话 {plan_id}",
                    "destination": core_info.get("departure_location", "未知"),
                    "created_at": session_context.created_at,
                    "last_activity": session_context.last_activity,
                    "message_count": 0,
                    "status": "active"
                }
                self.user_history_service.add_session_to_history(user_id, session_summary)
            except Exception as e:
                logger.warning(f"添加会话到用户历史失败: {str(e)}")
        
        # 初始化对话记录元数据
        if self.conversation_service:
            try:
                self.conversation_service.initialize_conversation_metadata(
                    session_id,
                    {
                        "plan_id": plan_id,
                        "user_id": user_id,
                        "created_at": session_context.created_at
                    }
                )
            except Exception as e:
                logger.warning(f"初始化对话元数据失败: {str(e)}")
        
        logger.info(f"创建新会话: {session_id}，当前会话数: {self.redis_client.zcard(self.session_index_key)}")
        return session_context
    
    def _save_session_to_redis(self, session: SessionContext):
        """将会话保存到Redis"""
        session_key = self._get_session_key(session.session_id)
        session_data = self._session_to_dict(session)
        
        # 使用pipeline提高性能
        pipe = self.redis_client.pipeline()
        
        # 存储会话数据
        pipe.setex(
            session_key,
            Config.REDIS_SESSION_TTL,
            json.dumps(session_data, ensure_ascii=False)
        )
        
        # 更新索引（按最后活动时间排序）
        score = datetime.fromisoformat(session.last_activity).timestamp()
        pipe.zadd(self.session_index_key, {session.session_id: score})
        
        # 设置索引过期时间（比会话稍长）
        pipe.expire(self.session_index_key, Config.REDIS_SESSION_TTL + 3600)
        
        pipe.execute()
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """
        获取会话上下文
        
        Args:
            session_id (str): 会话ID
        
        Returns:
            Optional[SessionContext]: 会话上下文
        """
        session_key = self._get_session_key(session_id)
        session_data = self.redis_client.get(session_key)
        
        if not session_data:
            return None
        
        try:
            data = json.loads(session_data)
            session = self._dict_to_session(data)
            
            # 更新最后活动时间
            session.last_activity = datetime.now().isoformat()
            self._save_session_to_redis(session)
            
            return session
        except Exception as e:
            logger.error(f"解析会话数据失败: {str(e)}")
            return None
    
    def update_session_context(self, session_id: str, session_context: SessionContext) -> bool:
        """更新整个会话上下文"""
        session_key = self._get_session_key(session_id)
        
        # 检查会话是否存在
        if not self.redis_client.exists(session_key):
            return False
        
        # 更新时间戳
        session_context.last_updated = datetime.now().isoformat()
        session_context.last_activity = datetime.now().isoformat()
        
        # 保存到Redis
        self._save_session_to_redis(session_context)
        
        return True
    
    def update_session(self, session_id: str, updated_plan: Dict[str, Any]) -> bool:
        """更新会话的规划数据"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # 更新规划数据
        session.current_plan = updated_plan.copy()
        session.last_updated = datetime.now().isoformat()
        session.edit_count += 1
        
        # 重新提取核心信息
        core_info = self._extract_core_info(updated_plan)
        session.weather_info = core_info.get('weather_info')
        session.selected_heritage_items = core_info.get('selected_heritage_items', [])
        session.location_coordinates = core_info.get('location_coordinates', {})
        session.budget_constraints = core_info.get('budget_constraints', {})
        session.time_constraints = core_info.get('time_constraints', {})
        
        # 保存到Redis
        self._save_session_to_redis(session)
        
        logger.info(f"会话 {session_id} 已更新，编辑次数: {session.edit_count}")
        return True
    
    def remove_session(self, session_id: str) -> bool:
        """移除会话"""
        session_key = self._get_session_key(session_id)
        
        # 使用pipeline删除会话和索引
        pipe = self.redis_client.pipeline()
        pipe.delete(session_key)
        pipe.zrem(self.session_index_key, session_id)
        result = pipe.execute()
        
        if result[0]:  # 删除成功
            logger.info(f"会话 {session_id} 已移除")
            return True
        return False
    
    def update_session_plan(self, session_id: str, new_plan: Dict[str, Any]) -> bool:
        """更新会话中的规划数据"""
        return self.update_session(session_id, new_plan)
    
    def get_optimized_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取优化的AI上下文（只包含必要信息）"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        return {
            'session_id': session.session_id,
            'plan_id': session.plan_id,
            'weather_info': session.weather_info,
            'heritage_items': session.selected_heritage_items,
            'location': session.location_coordinates,
            'budget': session.budget_constraints,
            'time_constraints': session.time_constraints,
            'edit_count': session.edit_count,
            'last_updated': session.last_updated
        }
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """
        清理过期会话
        Redis会自动清理过期的key，这里只清理孤儿索引
        """
        # Redis的TTL机制会自动清理过期会话
        # 这里只需要清理索引中不存在的会话ID
        try:
            session_ids = self.redis_client.zrange(self.session_index_key, 0, -1)
            removed_count = 0
            
            for session_id in session_ids:
                session_key = self._get_session_key(session_id)
                if not self.redis_client.exists(session_key):
                    # 会话已过期，从索引中移除
                    self.redis_client.zrem(self.session_index_key, session_id)
                    removed_count += 1
            
            if removed_count > 0:
                logger.info(f"清理了 {removed_count} 个孤儿索引")
        except Exception as e:
            logger.error(f"清理会话索引时发生错误: {str(e)}")
    
    async def _cleanup_oldest_sessions_redis(self, count: int):
        """清理最旧的会话（Redis实现）"""
        try:
            # 获取最旧的会话ID
            oldest_sessions = self.redis_client.zrange(
                self.session_index_key, 0, count - 1
            )
            
            for session_id in oldest_sessions:
                self.remove_session(session_id)
                logger.info(f"清理最旧会话: {session_id}")
        except Exception as e:
            logger.error(f"清理最旧会话时发生错误: {str(e)}")
    
    def _cleanup_oldest_sessions(self, count: int):
        """清理指定数量的最旧会话"""
        # 使用异步方法
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._cleanup_oldest_sessions_redis(count))
            else:
                loop.run_until_complete(self._cleanup_oldest_sessions_redis(count))
        except Exception as e:
            logger.error(f"清理最旧会话时发生错误: {str(e)}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话池统计信息"""
        try:
            total_sessions = self.redis_client.zcard(self.session_index_key)
            
            # 计算活跃会话（最近1小时有活动）
            one_hour_ago = (datetime.now() - timedelta(hours=1)).timestamp()
            active_sessions = self.redis_client.zcount(
                self.session_index_key, one_hour_ago, '+inf'
            )
            
            # 获取总编辑次数
            total_edits = 0
            session_ids = self.redis_client.zrange(self.session_index_key, 0, -1)
            for session_id in session_ids:
                session = self.get_session(session_id)
                if session:
                    total_edits += session.edit_count
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'max_sessions': self.max_sessions,
                'total_edits': total_edits,
                'average_edits_per_session': total_edits / max(total_sessions, 1),
                'storage_mode': 'redis'
            }
        except Exception as e:
            logger.error(f"获取会话统计信息失败: {str(e)}")
            return {
                'total_sessions': 0,
                'active_sessions': 0,
                'max_sessions': self.max_sessions,
                'total_edits': 0,
                'average_edits_per_session': 0,
                'storage_mode': 'redis',
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Redis连接健康检查"""
        try:
            self.redis_client.ping()
            info = self.redis_client.info()
            return {
                'status': 'healthy',
                'redis_version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_human': info.get('used_memory_human'),
                'total_sessions': self.redis_client.zcard(self.session_index_key)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# 全局会话池实例
_session_pool_instance = None

def get_session_pool() -> SessionPool:
    """
    获取全局会话池实例
    根据配置返回内存或Redis实现
    
    Returns:
        SessionPool: 会话池实例
    """
    global _session_pool_instance
    if _session_pool_instance is None:
        if Config.SESSION_STORAGE_MODE == 'redis' and REDIS_AVAILABLE:
            try:
                _session_pool_instance = RedisSessionPool()
                logger.info("使用Redis会话存储")
            except Exception as e:
                logger.warning(f"Redis会话池初始化失败，回退到内存存储: {str(e)}")
                _session_pool_instance = SessionPool()
        else:
            _session_pool_instance = SessionPool()
            logger.info("使用内存会话存储")
    return _session_pool_instance


def reset_session_pool():
    """重置会话池实例（用于测试）"""
    global _session_pool_instance
    _session_pool_instance = None
