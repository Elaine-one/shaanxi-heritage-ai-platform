#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话池管理系统
用于管理编辑会话的生命周期，优化AI上下文，实现真实的规划修改
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import threading
from dataclasses import dataclass, asdict

@dataclass
class SessionContext:
    """
    会话上下文数据类
    只保留AI编辑所需的核心信息
    """
    session_id: str
    plan_id: str
    user_id: Optional[str]
    
    # 核心规划数据
    current_plan: Dict[str, Any]
    original_plan: Dict[str, Any]
    
    # AI所需的核心信息
    weather_info: Optional[Dict[str, Any]] = None
    selected_heritage_items: List[Dict[str, Any]] = None
    location_coordinates: Dict[str, float] = None  # {"lat": xx, "lng": xx}
    budget_constraints: Dict[str, Any] = None
    time_constraints: Dict[str, Any] = None
    conversation_history: List[Dict[str, Any]] = None
    
    # 用户基本信息
    departure_location: Optional[str] = None
    travel_mode: Optional[str] = None
    group_size: Optional[int] = None
    budget_range: Optional[str] = None
    special_requirements: List[str] = None
    
    # 会话管理信息
    created_at: str = None
    last_updated: str = None
    last_activity: str = None
    edit_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()
        if self.last_activity is None:
            self.last_activity = datetime.now().isoformat()
        if self.selected_heritage_items is None:
            self.selected_heritage_items = []
        if self.location_coordinates is None:
            self.location_coordinates = {}
        if self.budget_constraints is None:
            self.budget_constraints = {}
        if self.time_constraints is None:
            self.time_constraints = {}
        if self.conversation_history is None:
            self.conversation_history = []
        if self.special_requirements is None:
            self.special_requirements = []

class SessionPool:
    """
    会话池管理器
    负责会话的创建、维护、清理和优化
    """
    
    def __init__(self, max_sessions: int = 100, cleanup_interval: int = 3600):
        """
        初始化会话池
        
        Args:
            max_sessions (int): 最大会话数量
            cleanup_interval (int): 清理间隔（秒）
        """
        self.max_sessions = max_sessions
        self.cleanup_interval = cleanup_interval
        
        # 会话存储
        self.sessions: Dict[str, SessionContext] = {}
        self.session_lock = threading.RLock()
        
        # 启动定时清理任务
        self._cleanup_task = None
        self._start_cleanup_task()
        
        logger.info(f"会话池初始化完成，最大会话数: {max_sessions}，清理间隔: {cleanup_interval}秒")
    
    def _start_cleanup_task(self):
        """
        启动定时清理任务
        """
        def cleanup_worker():
            while True:
                try:
                    self.cleanup_expired_sessions()
                    threading.Event().wait(self.cleanup_interval)
                except Exception as e:
                    logger.error(f"清理任务发生错误: {str(e)}")
                    threading.Event().wait(60)  # 出错后等待1分钟再重试
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("定时清理任务已启动")
    
    async def create_session(self, 
                           plan_id: str, 
                           original_plan: Dict[str, Any],
                           user_id: Optional[str] = None) -> SessionContext:
        """
        创建新的编辑会话
        
        Args:
            plan_id (str): 规划ID
            original_plan (Dict[str, Any]): 原始规划数据
            user_id (Optional[str]): 用户ID
        
        Returns:
            SessionContext: 会话上下文
        """
        with self.session_lock:
            # 检查会话数量限制
            if len(self.sessions) >= self.max_sessions:
                # 清理最旧的会话
                self._cleanup_oldest_sessions(1)
            
            # 生成会话ID
            session_id = f"edit_{plan_id}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # 提取核心信息
            core_info = self._extract_core_info(original_plan)
            
            # 创建会话上下文
            session_context = SessionContext(
                session_id=session_id,
                plan_id=plan_id,
                user_id=user_id,
                current_plan=original_plan.copy(),
                original_plan=original_plan.copy(),
                **core_info
            )
            
            # 存储会话
            self.sessions[session_id] = session_context
            
            logger.info(f"创建新会话: {session_id}，当前会话数: {len(self.sessions)}")
            return session_context
    
    def _extract_core_info(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        从规划数据中提取AI所需的核心信息
        
        Args:
            plan (Dict[str, Any]): 规划数据
        
        Returns:
            Dict[str, Any]: 核心信息
        """
        core_info = {
            'weather_info': None,
            'selected_heritage_items': [],
            'location_coordinates': {},
            'budget_constraints': {},
            'time_constraints': {}
        }
        
        try:
            # 提取用户基本信息
            basic_info = plan.get('basic_info', {})
            
            if 'departure' in basic_info:
                core_info['departure_location'] = basic_info['departure']
            elif 'departure_location' in plan:
                core_info['departure_location'] = plan['departure_location']
            
            if 'travel_mode' in basic_info:
                core_info['travel_mode'] = basic_info['travel_mode']
            elif 'travel_mode' in plan:
                core_info['travel_mode'] = plan['travel_mode']
            
            if 'group_size' in basic_info:
                core_info['group_size'] = basic_info['group_size']
            elif 'group_size' in plan:
                core_info['group_size'] = plan['group_size']
            
            if 'budget_range' in basic_info:
                core_info['budget_range'] = basic_info['budget_range']
            elif 'budget_range' in plan:
                core_info['budget_range'] = plan['budget_range']
            
            if 'special_requirements' in basic_info:
                core_info['special_requirements'] = basic_info['special_requirements']
            elif 'special_requirements' in plan:
                core_info['special_requirements'] = plan['special_requirements']
            
            # 提取天气信息
            if 'weather' in plan:
                core_info['weather_info'] = plan['weather']
            
            # 提取非遗项目信息
            if 'heritage_items' in plan:
                heritage_items = plan['heritage_items']
                if isinstance(heritage_items, list):
                    # 只保留必要的项目信息
                    core_info['selected_heritage_items'] = [
                        {
                            'id': item.get('id'),
                            'name': item.get('name'),
                            'location': item.get('location'),
                            'coordinates': item.get('coordinates'),
                            'category': item.get('category')
                        }
                        for item in heritage_items
                        if isinstance(item, dict)
                    ]
            
            # 提取位置坐标
            if 'destination' in plan:
                dest = plan['destination']
                if isinstance(dest, dict):
                    if 'coordinates' in dest:
                        core_info['location_coordinates'] = dest['coordinates']
                    elif 'lat' in dest and 'lng' in dest:
                        core_info['location_coordinates'] = {
                            'lat': dest['lat'],
                            'lng': dest['lng']
                        }
            
            # 提取预算约束
            if 'budget_analysis' in plan:
                budget = plan['budget_analysis']
                if isinstance(budget, dict):
                    core_info['budget_constraints'] = {
                        'total_budget': budget.get('total_budget'),
                        'accommodation': budget.get('accommodation'),
                        'transportation': budget.get('transportation'),
                        'food': budget.get('food'),
                        'activities': budget.get('activities')
                    }
            
            # 提取时间约束
            if 'itinerary' in plan:
                itinerary = plan['itinerary']
                if isinstance(itinerary, dict):
                    core_info['time_constraints'] = {
                        'start_date': itinerary.get('start_date'),
                        'end_date': itinerary.get('end_date'),
                        'duration': itinerary.get('duration'),
                        'daily_schedule': len(itinerary.get('daily_plans', []))
                    }
            
        except Exception as e:
            logger.warning(f"提取核心信息时发生错误: {str(e)}")
        
        return core_info
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """
        获取会话上下文
        
        Args:
            session_id (str): 会话ID
        
        Returns:
            Optional[SessionContext]: 会话上下文
        """
        with self.session_lock:
            session = self.sessions.get(session_id)
            if session:
                # 更新最后活动时间
                session.last_activity = datetime.now().isoformat()
            return session
    
    def update_session_context(self, session_id: str, session_context: SessionContext) -> bool:
        """
        更新整个会话上下文
        
        Args:
            session_id (str): 会话ID
            session_context (SessionContext): 更新的会话上下文
        
        Returns:
            bool: 更新是否成功
        """
        with self.session_lock:
            if session_id not in self.sessions:
                return False
            
            # 更新会话上下文
            self.sessions[session_id] = session_context
            session_context.last_updated = datetime.now().isoformat()
            session_context.last_activity = datetime.now().isoformat()
            
            return True
    
    def update_session(self, session_id: str, updated_plan: Dict[str, Any]) -> bool:
        """
        更新会话的规划数据
        
        Args:
            session_id (str): 会话ID
            updated_plan (Dict[str, Any]): 更新的规划数据
        
        Returns:
            bool: 更新是否成功
        """
        with self.session_lock:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            # 更新规划数据
            session.current_plan = updated_plan.copy()
            session.last_updated = datetime.now().isoformat()
            session.last_activity = datetime.now().isoformat()
            session.edit_count += 1
            
            # 重新提取核心信息
            core_info = self._extract_core_info(updated_plan)
            session.weather_info = core_info['weather_info']
            session.selected_heritage_items = core_info['selected_heritage_items']
            session.location_coordinates = core_info['location_coordinates']
            session.budget_constraints = core_info['budget_constraints']
            session.time_constraints = core_info['time_constraints']
            
            logger.info(f"会话 {session_id} 已更新，编辑次数: {session.edit_count}")
            return True
    
    def remove_session(self, session_id: str) -> bool:
        """
        移除会话
        
        Args:
            session_id (str): 会话ID
        
        Returns:
            bool: 移除是否成功
        """
        with self.session_lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"会话 {session_id} 已移除")
                return True
            return False
    
    def update_session_plan(self, session_id: str, new_plan: Dict[str, Any]) -> bool:
        """
        更新会话中的规划数据
        
        Args:
            session_id (str): 会话ID
            new_plan (Dict[str, Any]): 新的规划数据
        
        Returns:
            bool: 更新是否成功
        """
        if session_id in self.sessions:
            self.sessions[session_id].current_plan = new_plan
            self.sessions[session_id].last_activity = datetime.now()
            return True
        return False
    
    def get_optimized_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取优化的AI上下文（只包含必要信息）
        
        Args:
            session_id (str): 会话ID
        
        Returns:
            Optional[Dict[str, Any]]: 优化的上下文
        """
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
            'edit_count': session.edit_count,
            'last_updated': session.last_updated
        }
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """
        清理过期会话
        
        Args:
            max_age_hours (int): 最大会话年龄（小时）
        """
        with self.session_lock:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                last_activity = datetime.fromisoformat(session.last_activity)
                if last_activity < cutoff_time:
                    expired_sessions.append(session_id)
            
            # 删除过期会话
            for session_id in expired_sessions:
                del self.sessions[session_id]
            
            if expired_sessions:
                logger.info(f"清理了 {len(expired_sessions)} 个过期会话")
    
    def _cleanup_oldest_sessions(self, count: int):
        """
        清理最旧的会话
        
        Args:
            count (int): 要清理的会话数量
        """
        if not self.sessions:
            return
        
        # 按最后活动时间排序
        sorted_sessions = sorted(
            self.sessions.items(),
            key=lambda x: x[1].last_activity
        )
        
        # 删除最旧的会话
        for i in range(min(count, len(sorted_sessions))):
            session_id = sorted_sessions[i][0]
            del self.sessions[session_id]
            logger.info(f"清理最旧会话: {session_id}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        获取会话池统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self.session_lock:
            total_sessions = len(self.sessions)
            active_sessions = 0
            total_edits = 0
            
            # 计算活跃会话（最近1小时有活动）
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

# 全局会话池实例
_session_pool_instance = None

def get_session_pool() -> SessionPool:
    """
    获取全局会话池实例
    
    Returns:
        SessionPool: 会话池实例
    """
    global _session_pool_instance
    if _session_pool_instance is None:
        _session_pool_instance = SessionPool()
    return _session_pool_instance
