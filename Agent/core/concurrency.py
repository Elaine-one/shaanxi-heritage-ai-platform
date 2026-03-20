# -*- coding: utf-8 -*-
"""
并发控制模块
提供动态并发控制能力
"""

import asyncio
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class ConcurrencyStats:
    """并发统计"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_wait_time: float = 0.0
    last_adjust_time: float = field(default_factory=time.time)
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    def record_success(self):
        self.total_requests += 1
        self.successful_requests += 1
    
    def record_failure(self):
        self.total_requests += 1
        self.failed_requests += 1
    
    def record_wait(self, wait_time: float):
        self.total_wait_time += wait_time


class AdaptiveSemaphore:
    """
    自适应信号量
    
    功能：
    - 动态调整并发数
    - 基于成功率自动扩缩容
    - 支持最小/最大并发限制
    """
    
    def __init__(
        self, 
        initial: int = 4, 
        min_val: int = 1, 
        max_val: int = 10,
        adjust_interval: float = 60.0
    ):
        self._semaphore = asyncio.Semaphore(initial)
        self._current = initial
        self._min = min_val
        self._max = max_val
        self._adjust_interval = adjust_interval
        self._stats = ConcurrencyStats()
        self._lock = asyncio.Lock()
        
        logger.info(f"自适应信号量初始化: initial={initial}, min={min_val}, max={max_val}")
    
    @property
    def current(self) -> int:
        return self._current
    
    @property
    def stats(self) -> ConcurrencyStats:
        return self._stats
    
    async def acquire(self) -> bool:
        """获取信号量"""
        start_time = time.time()
        result = await self._semaphore.acquire()
        wait_time = time.time() - start_time
        self._stats.record_wait(wait_time)
        return result
    
    def release(self):
        """释放信号量"""
        self._semaphore.release()
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()
        if exc_type is None:
            self._stats.record_success()
        else:
            self._stats.record_failure()
        await self._maybe_adjust()
        return False
    
    async def _maybe_adjust(self):
        """检查是否需要调整并发数"""
        now = time.time()
        if now - self._stats.last_adjust_time < self._adjust_interval:
            return
        
        async with self._lock:
            if now - self._stats.last_adjust_time < self._adjust_interval:
                return
            
            success_rate = self._stats.success_rate
            
            if success_rate >= 0.95 and self._current < self._max:
                self._increase()
            elif success_rate < 0.8 and self._current > self._min:
                self._decrease()
            
            self._stats.last_adjust_time = now
    
    def _increase(self):
        """增加并发数"""
        old = self._current
        self._current = min(self._current + 1, self._max)
        self._semaphore = asyncio.Semaphore(self._current)
        logger.info(f"并发数增加: {old} -> {self._current}, 成功率: {self._stats.success_rate:.2%}")
    
    def _decrease(self):
        """减少并发数"""
        old = self._current
        self._current = max(self._current - 1, self._min)
        self._semaphore = asyncio.Semaphore(self._current)
        logger.warning(f"并发数减少: {old} -> {self._current}, 成功率: {self._stats.success_rate:.2%}")
    
    def force_adjust(self, value: int):
        """强制调整并发数"""
        value = max(self._min, min(value, self._max))
        if value != self._current:
            old = self._current
            self._current = value
            self._semaphore = asyncio.Semaphore(self._current)
            logger.info(f"并发数强制调整: {old} -> {self._current}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return {
            'current_concurrency': self._current,
            'min_concurrency': self._min,
            'max_concurrency': self._max,
            'success_rate': self._stats.success_rate,
            'total_requests': self._stats.total_requests,
            'successful_requests': self._stats.successful_requests,
            'failed_requests': self._stats.failed_requests,
            'total_wait_time': self._stats.total_wait_time
        }


class ProviderAwareConcurrency:
    """
    提供商感知的并发控制
    
    不同 LLM 提供商可能有不同的并发限制
    """
    
    DEFAULT_CONFIGS = {
        'dashscope': {'initial': 4, 'min': 1, 'max': 8},
        'zhipu': {'initial': 3, 'min': 1, 'max': 6},
        'deepseek': {'initial': 5, 'min': 1, 'max': 10},
        'openai': {'initial': 10, 'min': 1, 'max': 20},
        'moonshot': {'initial': 3, 'min': 1, 'max': 6},
        'ollama': {'initial': 5, 'min': 1, 'max': 10},
    }
    
    def __init__(self):
        self._semaphores: Dict[str, AdaptiveSemaphore] = {}
    
    def get_semaphore(self, provider: str) -> AdaptiveSemaphore:
        """获取指定提供商的信号量"""
        provider = provider.lower()
        
        if provider not in self._semaphores:
            config = self.DEFAULT_CONFIGS.get(provider, {'initial': 4, 'min': 1, 'max': 10})
            self._semaphores[provider] = AdaptiveSemaphore(**config)
            logger.info(f"为提供商 '{provider}' 创建信号量: {config}")
        
        return self._semaphores[provider]
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有提供商的状态"""
        return {
            provider: semaphore.get_status()
            for provider, semaphore in self._semaphores.items()
        }


_concurrency_manager: Optional[ProviderAwareConcurrency] = None


def get_concurrency_manager() -> ProviderAwareConcurrency:
    """获取并发管理器单例"""
    global _concurrency_manager
    if _concurrency_manager is None:
        _concurrency_manager = ProviderAwareConcurrency()
    return _concurrency_manager
