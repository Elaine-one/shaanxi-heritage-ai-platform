#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话池管理系统
用于管理编辑会话的生命周期

存储职责：
- L0/L1 Redis (RedisSessionPool): 热数据 — 会话、最近对话、摘要
- L2 Neo4j: 长期偏好 — 用户偏好、兴趣地区
- L3 SQLite (l3_sqlite_ledger): 审计账本 — 对话事件记录

本基类仅提供内存存储，用于测试。生产环境必须使用 RedisSessionPool。
不再使用 SQLite 作为 Redis 的降级后端。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import threading
from dataclasses import dataclass, field


@dataclass
class SessionContext:
    """
    会话上下文数据类
    只保留必要的规划信息
    """
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
    
    def add_conversation(self, role: str, content: str):
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
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


class SessionPool:
    """
    会话池管理器
    负责会话的创建、维护、清理和持久化
    """
    
    def __init__(self, max_sessions: int = 100, cleanup_interval: int = 3600):
        self.max_sessions = max_sessions
        self.cleanup_interval = cleanup_interval
        
        self.sessions: Dict[str, SessionContext] = {}
        self.session_lock = threading.RLock()
        
        self._start_cleanup_task()
        
        logger.info(f"会话池初始化完成（内存模式），最大会话数: {max_sessions}，清理间隔: {cleanup_interval}秒")
    
    def get_redis_client(self):
        """获取 Redis 客户端（基类返回 None，RedisSessionPool 覆写）"""
        return None

    @staticmethod
    def get_user_sessions_key(user_id: str) -> str:
        """获取用户会话索引的 Redis Key"""
        return f"agent:user:{user_id}:sessions"

    def update_session_context(self, session_id: str, session_context) -> bool:
        """更新整个会话上下文（基类实现，RedisSessionPool 覆写）"""
        with self.session_lock:
            if session_id in self.sessions:
                self.sessions[session_id] = session_context
                return True
        return False

    def update_session_plan(self, session_id: str, new_plan) -> bool:
        """更新会话中的规划数据"""
        return self.update_session(session_id, new_plan)

    def get_optimized_context(self, session_id: str):
        """获取优化的AI上下文（基类实现，RedisSessionPool 覆写）"""
        session = self.get_session(session_id)
        if not session:
            return None
        return {
            'session_id': session.session_id,
            'plan_id': session.plan_id,
            'weather_info': session.weather_info,
            'heritage_items': session.selected_heritage_items,
            'location': session.location_coordinates,
            'budget': session.budget_constraints,
            'time_constraints': session.time_constraints,
        }
    
    def _start_cleanup_task(self):
        def cleanup_worker():
            while True:
                try:
                    self.cleanup_expired_sessions()
                    threading.Event().wait(self.cleanup_interval)
                except Exception as e:
                    logger.error(f"清理任务发生错误: {str(e)}")
                    threading.Event().wait(60)
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    async def create_session(self, 
                           plan_id: str, 
                           original_plan: Dict[str, Any],
                           user_id: Optional[str] = None) -> SessionContext:
        with self.session_lock:
            if len(self.sessions) >= self.max_sessions:
                self._cleanup_oldest_sessions(1)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            session_id = f"edit_{plan_id}_{timestamp}"
            
            session = SessionContext(
                session_id=session_id,
                plan_id=plan_id,
                user_id=user_id
            )
            
            self._extract_plan_info(session, original_plan)
            
            self.sessions[session_id] = session
            
            logger.info(f"创建会话: {session_id}, 用户: {user_id}, 出发地: {session.departure_location}")
            return session
    
    def _extract_plan_info(self, session: SessionContext, plan_data: Dict[str, Any]):
        basic_info = plan_data.get('basic_info', {})
        
        session.departure_location = (
            basic_info.get('departure') or 
            basic_info.get('departureLocation') or
            plan_data.get('departure') or
            plan_data.get('departure_location') or
            plan_data.get('departureLocation')
        )
        session.travel_mode = (
            basic_info.get('travel_mode') or 
            basic_info.get('travelMode') or
            plan_data.get('travel_mode') or
            plan_data.get('travelMode')
        )
        session.group_size = (
            basic_info.get('group_size') or 
            basic_info.get('groupSize') or
            plan_data.get('group_size') or
            plan_data.get('groupSize')
        )
        session.budget_range = (
            basic_info.get('budget_range') or 
            basic_info.get('budgetRange') or
            plan_data.get('budget_range') or
            plan_data.get('budgetRange')
        )
        session.travel_days = (
            basic_info.get('travel_days') or 
            basic_info.get('travelDays') or
            plan_data.get('travel_days') or
            plan_data.get('travelDays')
        )
        
        heritage_items = plan_data.get('heritage_items', [])
        if heritage_items:
            session.heritage_ids = [item.get('id') for item in heritage_items if item.get('id')]
            session.heritage_names = [item.get('name', '') for item in heritage_items if item.get('name')]
        
        session.special_requirements = (
            basic_info.get('special_requirements') or
            plan_data.get('special_requirements', [])
        )
        session.current_plan = plan_data.copy()
        session.original_plan = plan_data.copy()
        
        itinerary = plan_data.get('itinerary', [])
        if itinerary:
            summary_parts = []
            for day in itinerary[:3]:
                day_num = day.get('day', '')
                attractions = day.get('attractions', [])
                if attractions:
                    names = [a.get('name', '') for a in attractions[:2]]
                    summary_parts.append(f"第{day_num}天: {', '.join(names)}")
            session.itinerary_summary = '\n'.join(summary_parts) if summary_parts else None
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        with self.session_lock:
            session = self.sessions.get(session_id)
            if session:
                session.update_activity()
            return session
    
    def update_session(self, session_id: str, updated_plan: Dict[str, Any]) -> bool:
        with self.session_lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            self._extract_plan_info(session, updated_plan)
            session.last_updated = datetime.now().isoformat()
            session.edit_count += 1
            
            logger.info(f"会话 {session_id} 已更新，编辑次数: {session.edit_count}")
            return True
    
    def add_conversation(self, session_id: str, role: str, content: str, user_id: Optional[str] = None):
        with self.session_lock:
            session = self.sessions.get(session_id)
            if session:
                session.add_conversation(role, content)
    
    def remove_session(self, session_id: str) -> bool:
        with self.session_lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"会话 {session_id} 已移除")
                return True
            return False
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        with self.session_lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                last_activity = datetime.fromisoformat(session.last_activity)
                if last_activity < cutoff_time:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
            
            if expired_sessions:
                logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
    
    def _cleanup_oldest_sessions(self, count: int):
        if not self.sessions:
            return
        
        sorted_sessions = sorted(
            self.sessions.items(),
            key=lambda x: x[1].last_activity
        )
        
        for i in range(min(count, len(sorted_sessions))):
            session_id = sorted_sessions[i][0]
            del self.sessions[session_id]
            logger.info(f"清理最旧会话: {session_id}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        with self.session_lock:
            total_sessions = len(self.sessions)
            active_sessions = 0
            total_edits = 0
            
            recent_time = datetime.now() - timedelta(hours=1)
            
            for session in self.sessions.values():
                last_activity = datetime.fromisoformat(session.last_activity)
                if last_activity > recent_time:
                    active_sessions += 1
                total_edits += session.edit_count
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'max_sessions': self.max_sessions,
                'total_edits': total_edits,
                'average_edits_per_session': total_edits / max(total_sessions, 1)
            }
