# -*- coding: utf-8 -*-
"""
工具上下文管理器
在工具执行前注入用户偏好、知识图谱上下文、RAG检索结果
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from loguru import logger

from Agent.memory.session import get_session_pool
from Agent.memory.knowledge_graph import get_knowledge_graph
from Agent.memory.vector_store import get_vector_store


@dataclass
class ToolContext:
    """工具执行上下文"""
    
    session_id: str = ""
    user_id: Optional[int] = None
    
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    
    current_plan: Dict[str, Any] = field(default_factory=dict)
    
    plan_summary: Dict[str, Any] = field(default_factory=dict)
    
    heritage_ids: List[int] = field(default_factory=list)
    
    nearby_heritages: Dict[int, List[Dict]] = field(default_factory=dict)
    
    rag_context: str = ""
    
    conversation_summary: str = ""
    
    kg_connected: bool = False
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        return self.user_preferences.get(key, default)
    
    def has_plan(self) -> bool:
        return bool(self.current_plan) or bool(self.plan_summary)
    
    def get_departure(self) -> str:
        return self.user_preferences.get('departure') or self.current_plan.get('departure_location', '') or self.plan_summary.get('departure_location', '')
    
    def get_travel_mode(self) -> str:
        return self.user_preferences.get('travel_mode') or self.current_plan.get('travel_mode', 'driving') or self.plan_summary.get('travel_mode', 'driving')


class ToolContextManager:
    """工具上下文管理器"""
    
    def __init__(self):
        self.session_pool = get_session_pool()
        self.kg = get_knowledge_graph()
        self.vector_store = get_vector_store()
        logger.info("工具上下文管理器初始化完成")

    def _summarize_conversation(self, history: List[Dict]) -> str:
        """简要总结对话历史"""
        if not history:
            return ""
        
        user_msgs = [m.get('content', '') for m in history if m.get('role') == 'user']
        if user_msgs:
            return f"用户最近询问: {user_msgs[-1][:100]}"
        return ""


_context_manager: Optional[ToolContextManager] = None


def get_context_manager() -> ToolContextManager:
    """获取上下文管理器单例"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ToolContextManager()
    return _context_manager
