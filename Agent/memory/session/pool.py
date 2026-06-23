# -*- coding: utf-8 -*-
"""
会话池基类 — SessionPool
提供内存存储实现，生产环境由 RedisSessionPool 覆写
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import threading

from .context import SessionContext


class SessionPool:
    """会话池管理器 — 负责会话的创建、维护、清理和持久化"""

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
        return f"agent:user:{user_id}:sessions"

    def update_session_context(self, session_id: str, session_context) -> bool:
        """更新整个会话上下文（基类实现，RedisSessionPool 覆写）"""
        with self.session_lock:
            if session_id in self.sessions:
                self.sessions[session_id] = session_context
                return True
        return False

    def update_session_plan(self, session_id: str, new_plan) -> bool:
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
            session.heritage_ids = [
                item.get('id') if isinstance(item, dict) else item
                for item in heritage_items
                if (isinstance(item, dict) and item.get('id')) or isinstance(item, int)
            ]
            session.heritage_names = [
                item.get('name', '') for item in heritage_items
                if isinstance(item, dict) and item.get('name')
            ]

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

    def add_conversation(self, session_id: str, role: str, content: str, user_id: Optional[str] = None, tool_interactions: list = None):
        with self.session_lock:
            session = self.sessions.get(session_id)
            if session:
                session.add_conversation(role, content, tool_interactions)

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
