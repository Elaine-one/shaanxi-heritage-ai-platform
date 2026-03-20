# -*- coding: utf-8 -*-
"""
用户偏好管理模块
管理 Level 3 记忆（用户偏好）
"""

from typing import Dict, Any, List
from loguru import logger
from .sqlite_store import get_sqlite_store


class UserProfileManager:
    def __init__(self):
        self.sqlite_store = get_sqlite_store()
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        profile = self.sqlite_store.get_user_profile(user_id)
        
        if profile:
            return {
                'user_id': profile['user_id'],
                'username': profile['username'],
                'preferred_departure': profile['preferred_departure'],
                'preferred_travel_mode': profile['preferred_travel_mode'],
                'preferred_budget_range': profile['preferred_budget_range'],
                'preferred_group_size': profile['preferred_group_size'],
                'interested_heritage_types': self._parse_json(profile.get('interested_heritage_types')),
                'travel_history': self._parse_json(profile.get('travel_history'))
            }
        
        return self._create_default_profile(user_id)
    
    def _create_default_profile(self, user_id: str) -> Dict[str, Any]:
        return {
            'user_id': user_id,
            'username': None,
            'preferred_departure': None,
            'preferred_travel_mode': None,
            'preferred_budget_range': None,
            'preferred_group_size': None,
            'interested_heritage_types': [],
            'travel_history': []
        }
    
    def _parse_json(self, data: str) -> List:
        if not data:
            return []
        try:
            import json
            return json.loads(data)
        except:
            return []
    
    def update_user_preference(self, user_id: str, preference: Dict[str, Any]):
        self.sqlite_store.update_user_profile(user_id, preference)
        logger.info(f"更新用户偏好: user_id={user_id}")
    
    def update_from_session(self, user_id: str, session_data: Dict[str, Any]):
        preference_updates = {}
        
        if session_data.get('departure_location'):
            preference_updates['preferred_departure'] = session_data['departure_location']
        
        if session_data.get('travel_mode'):
            preference_updates['preferred_travel_mode'] = session_data['travel_mode']
        
        if session_data.get('budget_range'):
            preference_updates['preferred_budget_range'] = session_data['budget_range']
        
        if session_data.get('group_size'):
            preference_updates['preferred_group_size'] = session_data['group_size']
        
        if preference_updates:
            self.update_user_preference(user_id, preference_updates)
    
    def get_user_context_for_prompt(self, user_id: str) -> str:
        profile = self.get_user_profile(user_id)
        
        if not profile.get('preferred_departure') and not profile.get('interested_heritage_types'):
            return ""
        
        lines = ["【用户偏好 - 作为参考，优先级低于本次规划】"]
        
        if profile.get('preferred_departure'):
            lines.append(f"- 常用出发地：{profile['preferred_departure']}")
        
        if profile.get('preferred_travel_mode'):
            lines.append(f"- 偏好出行方式：{profile['preferred_travel_mode']}")
        
        if profile.get('preferred_budget_range'):
            lines.append(f"- 偏好预算：{profile['preferred_budget_range']}")
        
        if profile.get('interested_heritage_types'):
            heritage_names = [h.get('name') for h in profile['interested_heritage_types'] if isinstance(h, dict) and h.get('name')]
            if heritage_names:
                lines.append(f"- 感兴趣的非遗类型：{', '.join(heritage_names[:5])}")
        
        return '\n'.join(lines)


_user_profile_manager = None


def get_user_profile_manager() -> UserProfileManager:
    global _user_profile_manager
    if _user_profile_manager is None:
        _user_profile_manager = UserProfileManager()
    return _user_profile_manager
