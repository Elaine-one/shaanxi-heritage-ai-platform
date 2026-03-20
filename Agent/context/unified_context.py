# -*- coding: utf-8 -*-
"""
统一上下文模型
P9级别上下文工程核心模块
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from loguru import logger
import json
import threading

_current_context: Optional['UnifiedContext'] = None
_context_lock = threading.Lock()


def set_current_context(context: 'UnifiedContext') -> None:
    """设置当前线程的上下文"""
    global _current_context
    with _context_lock:
        _current_context = context


def get_current_context() -> Optional['UnifiedContext']:
    """获取当前线程的上下文"""
    with _context_lock:
        return _current_context


def clear_current_context() -> None:
    """清除当前线程的上下文"""
    global _current_context
    with _context_lock:
        _current_context = None


class IntentType(str, Enum):
    """用户意图类型"""
    PLAN_RELATED = "plan_related"
    GENERAL_QUERY = "general_query"
    WEATHER_QUERY = "weather_query"
    HERITAGE_QUERY = "heritage_query"
    ROUTE_QUERY = "route_query"
    MODIFICATION = "modification"
    UNKNOWN = "unknown"


class HeritageItem(BaseModel):
    """非遗项目信息"""
    id: int
    name: str
    region: str = ""
    category: str = ""
    level: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    class Config:
        extra = "allow"


class PlanData(BaseModel):
    """规划数据"""
    departure_location: str = ""
    travel_days: int = 0
    travel_mode: str = "driving"
    group_size: int = 1
    budget_range: str = ""
    heritage_items: List[HeritageItem] = Field(default_factory=list)
    itinerary: List[Dict[str, Any]] = Field(default_factory=list)
    special_requirements: List[str] = Field(default_factory=list)
    
    class Config:
        extra = "allow"
    
    def has_heritages(self) -> bool:
        return len(self.heritage_items) > 0
    
    def get_heritage_ids(self) -> List[int]:
        return [h.id for h in self.heritage_items if h.id]
    
    def get_heritage_names(self) -> List[str]:
        return [h.name for h in self.heritage_items]
    
    def get_heritage_by_id(self, heritage_id: int) -> Optional[HeritageItem]:
        for h in self.heritage_items:
            if h.id == heritage_id:
                return h
        return None


class ConversationTurn(BaseModel):
    """对话轮次"""
    role: str
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    class Config:
        extra = "allow"


class UnifiedContext(BaseModel):
    """统一上下文模型 - 贯穿整个请求生命周期"""
    
    session_id: str = ""
    user_id: Optional[str] = None
    plan_id: str = ""
    
    plan_data: PlanData = Field(default_factory=PlanData)
    
    conversation_history: List[ConversationTurn] = Field(default_factory=list)
    
    detected_intent: IntentType = IntentType.UNKNOWN
    
    intermediate_steps: List[Dict[str, Any]] = Field(default_factory=list)
    action_history: List[str] = Field(default_factory=list)
    failed_count: int = 0
    no_progress_count: int = 0
    
    cached_data: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
    
    def has_plan(self) -> bool:
        """是否有规划数据"""
        return self.plan_data.has_heritages() or bool(self.plan_data.departure_location)
    
    def get_recent_conversation(self, n: int = 5) -> List[ConversationTurn]:
        """获取最近n轮对话"""
        return self.conversation_history[-n:] if self.conversation_history else []
    
    def add_conversation_turn(self, role: str, content: str):
        """添加对话轮次"""
        self.conversation_history.append(ConversationTurn(
            role=role,
            content=content
        ))
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def add_step(self, thought: str, action: str, action_input: Dict, observation: str):
        """添加执行步骤"""
        self.intermediate_steps.append({
            'thought': thought,
            'action': action,
            'action_input': action_input,
            'observation': observation
        })
        if action:
            action_key = f"{action}_{json.dumps(action_input, sort_keys=True)}"
            self.action_history.append(action_key)
    
    def is_repeated_action(self, action: str, action_input: Dict = None) -> bool:
        """检测重复动作（检查action和参数）"""
        if len(self.action_history) < 1:
            return False
        
        if action_input:
            action_key = f"{action}_{json.dumps(action_input, sort_keys=True)}"
            return action_key in self.action_history
        
        return self.action_history[-1].startswith(f"{action}_")
    
    def should_terminate(self) -> tuple:
        """判断是否应该终止"""
        if self.failed_count >= 3:
            return True, "工具执行失败次数过多"
        if self.no_progress_count >= 3:
            return True, "多次迭代无进展"
        if len(self.action_history) >= 3:
            last_actions = self.action_history[-3:]
            if all(act == last_actions[0] for act in last_actions):
                return True, "检测到相同动作重复执行"
        return False, ""
    
    def to_tool_context(self) -> Dict[str, Any]:
        """转换为工具上下文字典"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'plan_summary': self.plan_data.model_dump(),
            'heritage_items': [h.model_dump() for h in self.plan_data.heritage_items],
            'heritage_ids': self.plan_data.get_heritage_ids(),
            'departure_location': self.plan_data.departure_location,
            'travel_mode': self.plan_data.travel_mode,
            'travel_days': self.plan_data.travel_days,
            'budget_range': self.plan_data.budget_range,
            'special_requirements': self.plan_data.special_requirements,
        }
    
    def build_plan_summary_text(self) -> str:
        """构建规划摘要文本（用于提示词）"""
        parts = []
        
        if self.plan_data.departure_location:
            parts.append(f"出发地: {self.plan_data.departure_location}")
        if self.plan_data.travel_days:
            parts.append(f"天数: {self.plan_data.travel_days}天")
        if self.plan_data.travel_mode:
            parts.append(f"交通方式: {self.plan_data.travel_mode}")
        if self.plan_data.group_size:
            parts.append(f"人数: {self.plan_data.group_size}人")
        if self.plan_data.budget_range:
            parts.append(f"预算: {self.plan_data.budget_range}")
        
        if self.plan_data.heritage_items:
            names = self.plan_data.get_heritage_names()
            parts.append(f"已选非遗: {', '.join(names)}")
        
        if self.plan_data.special_requirements:
            parts.append(f"特殊要求: {', '.join(self.plan_data.special_requirements)}")
        
        return '\n'.join(parts)
    
    def log_context_state(self, prefix: str = ""):
        """记录上下文状态"""
        logger.info(f"📦 {prefix}上下文状态:")
        logger.info(f"  - session_id: {self.session_id}")
        logger.info(f"  - intent: {self.detected_intent}")
        logger.info(f"  - heritages: {len(self.plan_data.heritage_items)} items")
        logger.debug(f"  - heritage_ids: {self.plan_data.get_heritage_ids()}")
        logger.debug(f"  - departure: {self.plan_data.departure_location}")
        logger.debug(f"  - travel_mode: {self.plan_data.travel_mode}")
