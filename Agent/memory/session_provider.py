# -*- coding: utf-8 -*-
"""
统一会话池提供者
避免不同模块误用不同的 get_session_pool 实现导致记忆分裂。
"""

from loguru import logger

from Agent.config.settings import Config
from Agent.memory.session import SessionPool
from Agent.memory.redis_session import (
    REDIS_AVAILABLE,
    RedisSessionPool,
    get_session_pool as get_redis_session_pool,
)

_logged = False


def get_session_pool() -> SessionPool:
    """
    获取统一会话池实例。

    约定：
    - 生产环境必须使用 Redis (L1 热数据存储)，Redis 不可用时直接报错。
    - 不再降级到内存 SessionPool，每层存储各司其职。
    """
    global _logged
    pool = get_redis_session_pool()
    if not _logged:
        _logged = True
        logger.debug("SessionProvider 使用 RedisSessionPool (L1)")
    return pool
