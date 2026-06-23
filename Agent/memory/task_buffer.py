# -*- coding: utf-8 -*-
"""
TaskMemBuffer — ReAct 环形缓冲

与 ReAct 循环绑定，存储 thought → action → observation 步骤。
新任务开始时清空，任务执行时追加，溢出时自动淘汰最旧步骤。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from loguru import logger
from Agent.config.memory_budget import memory_budget


@dataclass
class TaskStep:
    """ReAct 循环中的单步"""
    step_index: int
    thought: str = ""
    action: str = ""
    action_input: str = ""
    observation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    is_complete: bool = False


@dataclass
class TaskBuffer:
    """固定容量的环形缓冲"""
    task_id: str
    description: str = ""
    steps: List[TaskStep] = field(default_factory=list)
    max_steps: int = 8

    @property
    def is_full(self) -> bool:
        return len(self.steps) >= self.max_steps

    @property
    def current_step(self) -> Optional[TaskStep]:
        for step in reversed(self.steps):
            if not step.is_complete:
                return step
        return None

    @property
    def completed_steps(self) -> List[TaskStep]:
        return [s for s in self.steps if s.is_complete]


class TaskMemBuffer:
    """任务记忆缓冲区管理器 — 与 ReAct 循环绑定"""

    def __init__(self, max_steps: int = None):
        self.max_steps = max_steps or memory_budget.task_buffer_max_steps
        self._current_task: Optional[TaskBuffer] = None
        self._step_index: int = 0

    # ── 任务生命周期 ──

    def start_task(self, task_id: str, description: str = "") -> TaskBuffer:
        """开始新任务 → 清空旧 buffer"""
        self._current_task = TaskBuffer(
            task_id=task_id,
            description=description,
            max_steps=self.max_steps,
        )
        self._step_index = 0
        logger.debug(f"TaskMemBuffer 新任务: {task_id}")
        return self._current_task

    def complete_task(self) -> Optional[TaskBuffer]:
        """当前任务完成，返回 buffer 供归档"""
        task = self._current_task
        self._current_task = None
        self._step_index = 0
        return task

    def clear_task(self):
        """放弃当前任务"""
        self._current_task = None
        self._step_index = 0

    # ── 步骤追加 ──

    def _ensure_step(self) -> TaskStep:
        if self._current_task is None:
            self.start_task("auto", "")
        task = self._current_task
        # 溢出时淘汰最旧步骤
        if task.is_full:
            task.steps.pop(0)
        step = TaskStep(step_index=self._step_index)
        task.steps.append(step)
        return step

    def add_thought(self, thought: str):
        step = self._ensure_step()
        step.thought = thought

    def add_action(self, action: str, action_input: str = ""):
        if self._current_task is None:
            self.start_task("auto", "")
        task = self._current_task
        step = task.current_step
        if step is None or step.action:
            # 创建新步骤
            step = self._ensure_step()
            self._step_index += 1
        step.action = action
        step.action_input = action_input

    def add_observation(self, observation: str):
        if self._current_task is None:
            return
        step = self._current_task.current_step
        if step is None:
            return
        step.observation = observation
        step.is_complete = True

    # ── 查询 ──

    def get_recent_steps(self, n: int = 5) -> List[TaskStep]:
        """获取当前任务最近 N 步"""
        if not self._current_task:
            return []
        return self._current_task.steps[-n:]

    def get_task_context(self, max_chars: int = 500) -> str:
        """格式化当前任务上下文，供 WMA 注入"""
        if not self._current_task or not self._current_task.steps:
            return ""

        parts = ["\n# 任务缓冲"]
        steps = self._current_task.steps

        for s in steps[-5:]:  # 最近5步
            step_info = []
            if s.thought:
                step_info.append(f"思考: {s.thought[:120]}")
            if s.action:
                step_info.append(f"动作: {s.action}({s.action_input[:60]})")
            if s.observation:
                obs_short = s.observation[:150].replace('\n', ' ')
                step_info.append(f"结果: {obs_short}")

            status = "✓" if s.is_complete else "…"
            parts.append(f"- [{status}] {' | '.join(step_info)}")

        content = '\n'.join(parts)
        if len(content) > max_chars:
            content = content[:max_chars] + "\n...(已截断)"
        return content

    def has_active_task(self) -> bool:
        return self._current_task is not None

    @property
    def current_task(self) -> Optional[TaskBuffer]:
        return self._current_task


_task_buffer: Optional[TaskMemBuffer] = None


def get_task_mem_buffer() -> TaskMemBuffer:
    global _task_buffer
    if _task_buffer is None:
        _task_buffer = TaskMemBuffer()
    return _task_buffer
