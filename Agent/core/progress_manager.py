# -*- coding: utf-8 -*-
"""
进度管理器
支持 Redis 分布式存储和内存模式降级
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, Callable, Awaitable
from abc import ABC, abstractmethod
from loguru import logger


class ProgressBackend(ABC):
    """进度存储后端接口"""
    
    @abstractmethod
    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
        """设置进度"""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """获取进度"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除进度"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查是否存在"""
        pass


class MemoryBackend(ProgressBackend):
    """内存存储后端（开发环境）"""
    
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._ttl: Dict[str, float] = {}
        self._lock = asyncio.Lock()
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
        async with self._lock:
            self._store[key] = value
            self._ttl[key] = time.time() + ttl
            return True
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            if key not in self._store:
                return None
            if time.time() > self._ttl.get(key, 0):
                del self._store[key]
                del self._ttl[key]
                return None
            return self._store[key]
    
    async def delete(self, key: str) -> bool:
        async with self._lock:
            if key in self._store:
                del self._store[key]
                del self._ttl[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        return await self.get(key) is not None


class RedisBackend(ProgressBackend):
    """Redis 存储后端（生产环境）"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
        try:
            await self.redis.setex(
                f"progress:{key}",
                ttl,
                json.dumps(value, ensure_ascii=False)
            )
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            data = await self.redis.get(f"progress:{key}")
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        try:
            await self.redis.delete(f"progress:{key}")
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        try:
            return await self.redis.exists(f"progress:{key}") > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False


class ProgressManager:
    """
    进度管理器
    
    功能：
    - 支持进度更新和查询
    - 支持 SSE 推送
    - 支持 Redis 分布式存储
    - 支持内存模式降级
    """
    
    DEFAULT_TTL = 3600
    
    def __init__(self, backend: ProgressBackend = None):
        self._backend = backend or MemoryBackend()
        self._callbacks: Dict[str, list] = {}
        self._sse_queues: Dict[str, asyncio.Queue] = {}
    
    @classmethod
    def create(cls, use_redis: bool = False, redis_url: str = None) -> 'ProgressManager':
        """工厂方法创建进度管理器"""
        if use_redis:
            try:
                import redis.asyncio as redis
                redis_client = redis.from_url(redis_url or "redis://localhost:6379/0")
                backend = RedisBackend(redis_client)
                logger.info("进度管理器使用 Redis 后端")
                return cls(backend)
            except Exception as e:
                logger.warning(f"Redis 连接失败，降级为内存模式: {e}")
        
        logger.info("进度管理器使用内存后端")
        return cls(MemoryBackend())
    
    async def update_progress(
        self, 
        plan_id: str, 
        progress: int, 
        status: str,
        message: str = None,
        data: Dict[str, Any] = None
    ) -> bool:
        """更新进度"""
        progress_data = {
            'plan_id': plan_id,
            'progress': progress,
            'status': status,
            'message': message,
            'data': data or {},
            'timestamp': time.time()
        }
        
        result = await self._backend.set(plan_id, progress_data, self.DEFAULT_TTL)
        
        if result:
            await self._notify_callbacks(plan_id, progress_data)
            await self._push_sse(plan_id, progress_data)
        
        return result
    
    async def get_progress(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """获取进度"""
        return await self._backend.get(plan_id)
    
    async def delete_progress(self, plan_id: str) -> bool:
        """删除进度"""
        result = await self._backend.delete(plan_id)
        if plan_id in self._callbacks:
            del self._callbacks[plan_id]
        if plan_id in self._sse_queues:
            del self._sse_queues[plan_id]
        return result
    
    async def exists(self, plan_id: str) -> bool:
        """检查进度是否存在"""
        return await self._backend.exists(plan_id)
    
    def register_callback(self, plan_id: str, callback: Callable[[Dict], Awaitable[None]]):
        """注册进度回调"""
        if plan_id not in self._callbacks:
            self._callbacks[plan_id] = []
        self._callbacks[plan_id].append(callback)
    
    def unregister_callback(self, plan_id: str, callback: Callable[[Dict], Awaitable[None]]):
        """取消注册进度回调"""
        if plan_id in self._callbacks:
            try:
                self._callbacks[plan_id].remove(callback)
            except ValueError:
                pass
    
    async def subscribe_sse(self, plan_id: str) -> asyncio.Queue:
        """订阅 SSE 事件"""
        if plan_id not in self._sse_queues:
            self._sse_queues[plan_id] = asyncio.Queue()
        return self._sse_queues[plan_id]
    
    async def unsubscribe_sse(self, plan_id: str):
        """取消订阅 SSE"""
        if plan_id in self._sse_queues:
            del self._sse_queues[plan_id]
    
    async def _notify_callbacks(self, plan_id: str, data: Dict[str, Any]):
        """通知回调"""
        callbacks = self._callbacks.get(plan_id, [])
        for callback in callbacks:
            try:
                await callback(data)
            except Exception as e:
                logger.warning(f"回调执行失败: {e}")
    
    async def _push_sse(self, plan_id: str, data: Dict[str, Any]):
        """推送 SSE 事件"""
        if plan_id in self._sse_queues:
            try:
                await self._sse_queues[plan_id].put(data)
            except Exception as e:
                logger.warning(f"SSE 推送失败: {e}")


_progress_manager: Optional[ProgressManager] = None


def get_progress_manager() -> ProgressManager:
    """获取进度管理器单例"""
    global _progress_manager
    if _progress_manager is None:
        from Agent.config.settings import Config
        use_redis = Config.SESSION_STORAGE_MODE == 'redis'
        redis_url = f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}"
        _progress_manager = ProgressManager.create(use_redis=use_redis, redis_url=redis_url)
    return _progress_manager
