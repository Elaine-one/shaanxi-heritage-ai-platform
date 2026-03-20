# -*- coding: utf-8 -*-
"""
上下文工程模块
P9级别上下文管理系统

核心组件:
- UnifiedContext: 统一上下文模型
- ContextBuilder: 上下文构建器 (集成缓存)
- LayeredCacheManager: 分层缓存管理器 (L1内存 + L2 Redis)
- ContextCompressor: 上下文压缩器 (Token预算控制)
"""

from .unified_context import (
    UnifiedContext,
    PlanData,
    HeritageItem,
    ConversationTurn,
    IntentType
)

from .context_builder import (
    ContextBuilder,
    get_context_builder,
    build_context
)

from .cache_manager import (
    LayeredCacheManager,
    get_cache_manager
)

from .context_compressor import (
    ContextCompressor,
    get_context_compressor
)

__all__ = [
    'UnifiedContext',
    'PlanData',
    'HeritageItem',
    'ConversationTurn',
    'IntentType',
    'ContextBuilder',
    'get_context_builder',
    'build_context',
    'LayeredCacheManager',
    'get_cache_manager',
    'ContextCompressor',
    'get_context_compressor',
]
