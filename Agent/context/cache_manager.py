# -*- coding: utf-8 -*-
"""
分层缓存管理器
实现 L1(内存) -> L2(Redis) 三层缓存架构
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
import threading
import json
import hashlib
from loguru import logger

try:
    from cachetools import TTLCache
    CACHE_TOOLS_AVAILABLE = True
except ImportError:
    CACHE_TOOLS_AVAILABLE = False


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    access_count: int = 0
    priority: int = 0
    
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def touch(self):
        self.access_count += 1


class LayeredCacheManager:
    """
    分层缓存管理器
    实现 L1(内存) -> L2(Redis) 三层缓存
    
    特性:
    - L1: 进程内内存缓存，响应时间 <1ms
    - L2: Redis分布式缓存，响应时间 1-10ms
    - 自动回填: L2命中时自动回填L1
    - 缓存预热: 支持预加载关键数据
    - 统计监控: 完善的命中率统计
    """
    
    L1_MAX_SIZE = 1000
    L1_TTL_SECONDS = 300
    L2_TTL_SECONDS = 86400
    
    def __init__(self, redis_client=None):
        self._lock = threading.RLock()
        
        if CACHE_TOOLS_AVAILABLE:
            self._l1_cache = TTLCache(maxsize=self.L1_MAX_SIZE, ttl=self.L1_TTL_SECONDS)
        else:
            self._l1_cache = OrderedDict()
        
        self._redis = redis_client
        self._l2_enabled = redis_client is not None
        
        self._stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'writes': 0,
            'invalidations': 0,
        }
        
        logger.info(f"分层缓存管理器初始化完成, L2(Redis): {'启用' if self._l2_enabled else '禁用'}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值 (L1 -> L2 -> default)
        """
        with self._lock:
            value = self._get_l1(key)
            if value is not None:
                self._stats['l1_hits'] += 1
                return value
            
            self._stats['l1_misses'] += 1
            
            if self._l2_enabled:
                value = self._get_l2(key)
                if value is not None:
                    self._stats['l2_hits'] += 1
                    self._set_l1(key, value)
                    return value
            
            self._stats['l2_misses'] += 1
            return default
    
    def set(self, key: str, value: Any, ttl: int = None, priority: int = 0):
        """
        设置缓存值 (同时写入L1和L2)
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)，None使用默认值
            priority: 优先级 0=普通, 1=重要, 2=关键
        """
        with self._lock:
            self._set_l1(key, value, ttl, priority)
            
            if self._l2_enabled:
                self._set_l2(key, value, ttl)
            
            self._stats['writes'] += 1
    
    def _get_l1(self, key: str) -> Any:
        """从L1获取"""
        try:
            if CACHE_TOOLS_AVAILABLE:
                entry = self._l1_cache.get(key)
            else:
                entry = self._l1_cache.get(key)
            
            if entry is None:
                return None
            
            if isinstance(entry, CacheEntry):
                if entry.is_expired():
                    self._delete_l1(key)
                    return None
                entry.touch()
                return entry.value
            
            return entry
        except Exception as e:
            logger.warning(f"L1缓存读取失败: {e}")
            return None
    
    def _set_l1(self, key: str, value: Any, ttl: int = None, priority: int = 0):
        """写入L1"""
        try:
            expires_at = None
            if ttl:
                expires_at = datetime.now() + timedelta(seconds=ttl)
            elif CACHE_TOOLS_AVAILABLE:
                expires_at = datetime.now() + timedelta(seconds=self.L1_TTL_SECONDS)
            
            entry = CacheEntry(
                key=key,
                value=value,
                expires_at=expires_at,
                priority=priority
            )
            
            if CACHE_TOOLS_AVAILABLE:
                self._l1_cache[key] = entry
            else:
                if len(self._l1_cache) >= self.L1_MAX_SIZE:
                    self._evict_lru()
                self._l1_cache[key] = entry
        except Exception as e:
            logger.warning(f"L1缓存写入失败: {e}")
    
    def _evict_lru(self):
        """LRU淘汰策略"""
        if not self._l1_cache:
            return
        
        low_priority_keys = [
            k for k, v in self._l1_cache.items()
            if isinstance(v, CacheEntry) and v.priority == 0
        ]
        
        if low_priority_keys:
            key_to_evict = low_priority_keys[0]
            del self._l1_cache[key_to_evict]
        else:
            self._l1_cache.popitem(last=False)
    
    def _delete_l1(self, key: str):
        """删除L1条目"""
        try:
            if key in self._l1_cache:
                del self._l1_cache[key]
        except Exception:
            pass
    
    def _get_l2(self, key: str) -> Any:
        """从L2(Redis)获取"""
        if not self._l2_enabled:
            return None
        
        try:
            redis_key = f"context:cache:{key}"
            data = self._redis.get(redis_key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"L2缓存读取失败: {e}")
            return None
    
    def _set_l2(self, key: str, value: Any, ttl: int = None):
        """写入L2(Redis)"""
        if not self._l2_enabled:
            return
        
        try:
            redis_key = f"context:cache:{key}"
            ttl = ttl or self.L2_TTL_SECONDS
            self._redis.setex(redis_key, ttl, json.dumps(value, ensure_ascii=False, default=str))
        except Exception as e:
            logger.warning(f"L2缓存写入失败: {e}")
    
    def invalidate(self, key: str):
        """使缓存失效"""
        with self._lock:
            self._delete_l1(key)
            if self._l2_enabled:
                try:
                    self._redis.delete(f"context:cache:{key}")
                except Exception:
                    pass
            self._stats['invalidations'] += 1
    
    def invalidate_pattern(self, pattern: str):
        """批量使缓存失效"""
        with self._lock:
            keys_to_delete = [k for k in self._l1_cache.keys() if pattern in k]
            for k in keys_to_delete:
                self._delete_l1(k)
            
            if self._l2_enabled:
                try:
                    cursor = 0
                    while True:
                        cursor, keys = self._redis.scan(
                            cursor, match=f"context:cache:*{pattern}*", count=100
                        )
                        if keys:
                            self._redis.delete(*keys)
                        if cursor == 0:
                            break
                except Exception as e:
                    logger.warning(f"L2批量删除失败: {e}")
            
            self._stats['invalidations'] += len(keys_to_delete)
    
    def warmup(self, session_id: str, session_data: Dict[str, Any]):
        """
        缓存预热
        在会话开始时预加载关键数据
        """
        if session_data.get('plan_id'):
            self.set(
                f"plan:{session_id}:core",
                {
                    'departure': session_data.get('departure_location'),
                    'heritage_ids': session_data.get('heritage_ids', []),
                    'heritage_names': session_data.get('heritage_names', []),
                    'travel_days': session_data.get('travel_days'),
                    'travel_mode': session_data.get('travel_mode'),
                },
                priority=2
            )
        
        heritage_names = list(session_data.get('heritage_names', []))
        departure = session_data.get('departure_location')
        if departure:
            heritage_names.append(departure)
        
        for name in set(heritage_names):
            cache_key = f"geo:{name}"
            if self.get(cache_key) is None:
                logger.debug(f"预热地理编码: {name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self._stats['l1_hits'] + self._stats['l1_misses']
        l1_hit_rate = self._stats['l1_hits'] / max(total_requests, 1)
        
        l2_requests = self._stats['l2_hits'] + self._stats['l2_misses']
        l2_hit_rate = self._stats['l2_hits'] / max(l2_requests, 1)
        
        return {
            'l1_size': len(self._l1_cache),
            'l1_max_size': self.L1_MAX_SIZE,
            'l1_hits': self._stats['l1_hits'],
            'l1_misses': self._stats['l1_misses'],
            'l1_hit_rate': f"{l1_hit_rate:.2%}",
            'l2_hits': self._stats['l2_hits'],
            'l2_misses': self._stats['l2_misses'],
            'l2_hit_rate': f"{l2_hit_rate:.2%}",
            'total_writes': self._stats['writes'],
            'total_invalidations': self._stats['invalidations'],
            'l2_enabled': self._l2_enabled,
        }
    
    def clear(self):
        """清空所有缓存"""
        with self._lock:
            if CACHE_TOOLS_AVAILABLE:
                self._l1_cache.clear()
            else:
                self._l1_cache = OrderedDict()
            
            if self._l2_enabled:
                try:
                    cursor = 0
                    while True:
                        cursor, keys = self._redis.scan(
                            cursor, match="context:cache:*", count=100
                        )
                        if keys:
                            self._redis.delete(*keys)
                        if cursor == 0:
                            break
                except Exception as e:
                    logger.warning(f"清空L2缓存失败: {e}")
    
    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """生成缓存键"""
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = ":".join(key_parts)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()[:16]


_cache_manager_instance: Optional[LayeredCacheManager] = None


def get_cache_manager() -> LayeredCacheManager:
    """获取缓存管理器单例"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        try:
            from Agent.config.settings import Config
            if Config.SESSION_STORAGE_MODE == 'redis':
                import redis
                redis_client = redis.Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    db=Config.REDIS_DB,
                    password=Config.REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                redis_client.ping()
                _cache_manager_instance = LayeredCacheManager(redis_client)
                logger.info("缓存管理器使用Redis后端")
            else:
                _cache_manager_instance = LayeredCacheManager()
                logger.info("缓存管理器使用内存后端")
        except Exception as e:
            logger.warning(f"缓存管理器初始化失败，使用内存模式: {e}")
            _cache_manager_instance = LayeredCacheManager()
    return _cache_manager_instance


def reset_cache_manager():
    """重置缓存管理器（用于测试）"""
    global _cache_manager_instance
    if _cache_manager_instance:
        _cache_manager_instance.clear()
    _cache_manager_instance = None
