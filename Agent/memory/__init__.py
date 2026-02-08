# -*- coding: utf-8 -*-
"""
Memory 模块
包含记忆管理代码，包括会话内存和会话管理
"""

from .session import SessionPool, SessionContext, get_session_pool

# 尝试导入Redis会话池
try:
    from .redis_session import RedisSessionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    RedisSessionPool = None

__all__ = [
    'SessionPool',
    'SessionContext',
    'get_session_pool',
    'RedisSessionPool',
    'REDIS_AVAILABLE'
]
