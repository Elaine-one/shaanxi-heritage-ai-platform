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
import contextvars

_current_context: contextvars.ContextVar[Optional['UnifiedContext']] = contextvars.ContextVar(
    '_current_context', default=None
)


def set_current_context(context: 'UnifiedContext') -> None:
    """设置当前协程的上下文"""
    _current_context.set(context)


def get_current_context() -> Optional['UnifiedContext']:
    """获取当前协程的上下文"""
    return _current_context.get()


def clear_current_context() -> None:
    """清除当前协程的上下文"""
    _current_context.set(None)


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
    tool_interactions: Optional[List[Dict]] = None  # [{tool_name, tool_args, tool_call_id, result}, ...]

    class Config:
        extra = "allow"


class UnifiedContext(BaseModel):
    """统一上下文模型 - 贯穿整个请求生命周期"""
    
    session_id: str = ""
    user_id: Optional[str] = None
    username: Optional[str] = None
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
    
    def add_conversation_turn(self, role: str, content: str, tool_interactions: List[Dict] = None):
        """添加对话轮次"""
        self.conversation_history.append(ConversationTurn(
            role=role,
            content=content,
            tool_interactions=tool_interactions
        ))
        from Agent.config.memory_budget import memory_budget
        max_turns = memory_budget.conversation_history_max_turns
        if len(self.conversation_history) > max_turns:
            self.conversation_history = self.conversation_history[-max_turns:]
    
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
