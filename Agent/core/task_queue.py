# -*- coding: utf-8 -*-
"""
规划任务队列
支持用户级别的并发限制
"""

import asyncio
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger


@dataclass
class Task:
    id: str
    user_id: str
    request: Dict[str, Any]
    status: str = 'pending'
    result: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskQueue:
    """规划任务队列"""
    
    def __init__(self, max_concurrent: int = 5, max_per_user: int = 2):
        self.max_concurrent = max_concurrent
        self.max_per_user = max_per_user
        
        self.pending: deque[Task] = deque()
        self.running: Dict[str, Task] = {}
        self.completed: Dict[str, Task] = {}
        
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        
        logger.info(f"任务队列初始化: 最大并发={max_concurrent}, 每用户最大={max_per_user}")
    
    async def submit(self, task: Task) -> bool:
        """提交任务"""
        async with self._lock:
            user_running = sum(1 for t in self.running.values() if t.user_id == task.user_id)
            
            if user_running >= self.max_per_user:
                logger.warning(f"用户 {task.user_id} 达到并发限制 ({self.max_per_user})")
                return False
            
            self.pending.append(task)
            logger.info(f"任务 {task.id} 已加入队列，当前队列长度: {len(self.pending)}")
            return True
    
    async def acquire(self) -> Optional[Task]:
        """获取任务"""
        await self._semaphore.acquire()
        
        async with self._lock:
            if not self.pending:
                self._semaphore.release()
                return None
            
            task = self.pending.popleft()
            task.status = 'running'
            task.started_at = datetime.now()
            self.running[task.id] = task
            
            logger.info(f"任务 {task.id} 开始执行")
            return task
    
    async def complete(self, task_id: str, result: Dict):
        """完成任务"""
        async with self._lock:
            if task_id in self.running:
                task = self.running.pop(task_id)
                task.status = 'completed'
                task.result = result
                task.completed_at = datetime.now()
                self.completed[task_id] = task
                
                if len(self.completed) > 100:
                    oldest = list(self.completed.keys())[:50]
                    for tid in oldest:
                        del self.completed[tid]
                
                logger.info(f"任务 {task_id} 完成")
                self._semaphore.release()
    
    async def fail(self, task_id: str, error: str):
        """标记任务失败"""
        async with self._lock:
            if task_id in self.running:
                task = self.running.pop(task_id)
                task.status = 'failed'
                task.result = {'error': error}
                task.completed_at = datetime.now()
                
                logger.error(f"任务 {task_id} 失败: {error}")
                self._semaphore.release()
    
    async def cancel(self, task_id: str) -> bool:
        """取消任务"""
        async with self._lock:
            if task_id in self.running:
                task = self.running.pop(task_id)
                task.status = 'cancelled'
                self._semaphore.release()
                logger.info(f"任务 {task_id} 已取消")
                return True
            
            for i, task in enumerate(self.pending):
                if task.id == task_id:
                    self.pending.remove(task)
                    task.status = 'cancelled'
                    logger.info(f"任务 {task_id} 已从队列中取消")
                    return True
            
            return False
    
    def get_user_tasks(self, user_id: str) -> Dict[str, Any]:
        """获取用户的所有任务"""
        return {
            'pending': [t for t in self.pending if t.user_id == user_id],
            'running': [t for t in self.running.values() if t.user_id == user_id],
            'completed': [t for t in self.completed.values() if t.user_id == user_id]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        return {
            'pending_count': len(self.pending),
            'running_count': len(self.running),
            'completed_count': len(self.completed),
            'max_concurrent': self.max_concurrent,
            'max_per_user': self.max_per_user
        }


_task_queue = None


def get_task_queue() -> TaskQueue:
    """获取任务队列单例"""
    global _task_queue
    if _task_queue is None:
        from Agent.config.settings import config
        max_concurrent = getattr(config, 'MAX_CONCURRENT_PLANNING', 5)
        max_per_user = getattr(config, 'MAX_PLANNING_PER_USER', 2)
        _task_queue = TaskQueue(max_concurrent=max_concurrent, max_per_user=max_per_user)
    return _task_queue
