# -*- coding: utf-8 -*-
"""
会话上下文数据结构 — SessionContext dataclass
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class SessionContext:
    """会话上下文数据类，只保留必要的规划信息"""

    session_id: str
    plan_id: str
    user_id: Optional[str] = None
    username: Optional[str] = None

    departure_location: Optional[str] = None
    travel_mode: Optional[str] = None
    group_size: Optional[int] = None
    budget_range: Optional[str] = None
    travel_days: Optional[int] = None
    heritage_ids: List[int] = field(default_factory=list)
    heritage_names: List[str] = field(default_factory=list)
    special_requirements: List[str] = field(default_factory=list)

    current_plan: Dict[str, Any] = field(default_factory=dict)
    original_plan: Dict[str, Any] = field(default_factory=dict)
    itinerary_summary: Optional[str] = None

    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    weather_info: Optional[Dict[str, Any]] = None
    selected_heritage_items: List[Dict[str, Any]] = field(default_factory=list)
    location_coordinates: Dict[str, Any] = field(default_factory=dict)
    budget_constraints: Dict[str, Any] = field(default_factory=dict)
    time_constraints: Dict[str, Any] = field(default_factory=dict)

    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    edit_count: int = 0

    def update_activity(self):
        self.last_activity = datetime.now().isoformat()

    def add_conversation(self, role: str, content: str, tool_interactions: list = None):
        turn = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        if tool_interactions:
            turn['tool_interactions'] = tool_interactions
        self.conversation_history.append(turn)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
        self.update_activity()

    def get_recent_conversations(self, limit: int = 10) -> List[Dict[str, str]]:
        return self.conversation_history[-limit:] if self.conversation_history else []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'plan_id': self.plan_id,
            'user_id': self.user_id,
            'departure_location': self.departure_location,
            'travel_mode': self.travel_mode,
            'group_size': self.group_size,
            'budget_range': self.budget_range,
            'travel_days': self.travel_days,
            'heritage_ids': self.heritage_ids,
            'heritage_names': self.heritage_names,
            'special_requirements': self.special_requirements,
            'current_plan': self.current_plan,
            'original_plan': self.original_plan,
            'itinerary_summary': self.itinerary_summary,
            'conversation_history': self.conversation_history,
            'weather_info': self.weather_info,
            'selected_heritage_items': self.selected_heritage_items,
            'location_coordinates': self.location_coordinates,
            'budget_constraints': self.budget_constraints,
            'time_constraints': self.time_constraints,
            'created_at': self.created_at,
            'last_updated': self.last_updated,
            'last_activity': self.last_activity,
            'edit_count': self.edit_count
        }
