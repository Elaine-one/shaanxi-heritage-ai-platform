# -*- coding: utf-8 -*-
"""
会话管理子包

架构:
  context.py   — SessionContext 数据结构
  pool.py      — SessionPool 基类（内存实现）
  redis_pool.py — RedisSessionPool（Redis 实现 + 单例）
  lifecycle.py — SessionLifecycle（会话开/关钩子）
  archiver.py  — SessionArchiver（归档管线：LLM摘要→向量索引→L2增强）
  index.py     — SessionIndex（跨会话语义检索）
"""

from loguru import logger

from .context import SessionContext
from .pool import SessionPool
from .redis_pool import (
    REDIS_AVAILABLE,
    RedisSessionPool,
    get_redis_session_pool,
    reset_session_pool,
)
from .lifecycle import SessionLifecycle, get_session_lifecycle
from .archiver import SessionArchive, SessionArchiver
from .index import SessionIndex, get_session_index


# ── 统一会话池入口 ──

_logged = False


def get_session_pool() -> SessionPool:
    """获取统一会话池实例（生产环境使用 RedisSessionPool）"""
    global _logged
    pool = get_redis_session_pool()
    if not _logged:
        _logged = True
        logger.debug("SessionProvider 使用 RedisSessionPool (L1)")
    return pool


__all__ = [
    'SessionContext',
    'SessionPool',
    'RedisSessionPool',
    'SessionLifecycle',
    'SessionArchive',
    'SessionArchiver',
    'SessionIndex',
    'REDIS_AVAILABLE',
    'get_session_pool',
    'get_redis_session_pool',
    'get_session_lifecycle',
    'get_session_index',
    'reset_session_pool',
]
