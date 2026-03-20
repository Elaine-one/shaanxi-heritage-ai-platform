# -*- coding: utf-8 -*-
"""
上下文构建器
从会话数据构建统一上下文，集成分层缓存
"""

from loguru import logger
from typing import Dict, Any, Optional
from .unified_context import (
    UnifiedContext, 
    PlanData, 
    HeritageItem, 
    ConversationTurn,
    IntentType
)


class ContextBuilder:
    """上下文构建器 - 从会话数据构建统一上下文
    
    集成:
    - LayeredCacheManager: 分层缓存 (L1内存 + L2 Redis)
    - 意图检测: detect_intent()
    - 缓存预热: warmup_cache()
    """
    
    def __init__(self):
        from Agent.memory.session import get_session_pool
        self.session_pool = get_session_pool()
        
        self._cache_manager = None
        self._stats = {
            'contexts_built': 0,
            'cache_hits': 0,
            'cache_misses': 0,
        }
    
    @property
    def cache_manager(self):
        """延迟加载缓存管理器"""
        if self._cache_manager is None:
            from .cache_manager import get_cache_manager
            self._cache_manager = get_cache_manager()
        return self._cache_manager
    
    def build_from_session(self, session_id: str) -> UnifiedContext:
        """从会话构建上下文 - 带缓存"""
        self._stats['contexts_built'] += 1
        
        if not session_id:
            logger.warning("session_id 为空，返回空上下文")
            return UnifiedContext(session_id="")
        
        cache_key = f"context:{session_id}"
        cached_context = self.cache_manager.get(cache_key)
        if cached_context:
            self._stats['cache_hits'] += 1
            logger.debug(f"📦 上下文缓存命中: {session_id}")
            return self._dict_to_context(cached_context)
        
        self._stats['cache_misses'] += 1
        
        context = UnifiedContext(session_id=session_id)
        
        session = self.session_pool.get_session(session_id)
        if not session:
            logger.warning(f"会话不存在: {session_id}")
            return context
        
        context.user_id = session.user_id
        context.plan_id = session.plan_id
        
        context.plan_data = self._build_plan_data(session)
        
        if hasattr(session, 'conversation_history') and session.conversation_history:
            for m in session.conversation_history:
                if isinstance(m, dict):
                    context.conversation_history.append(ConversationTurn(
                        role=m.get('role', ''),
                        content=m.get('content', ''),
                        timestamp=m.get('timestamp', '')
                    ))
        
        context.cached_data = self._get_cached_data(session)
        
        context_dict = self._context_to_dict(context)
        self.cache_manager.set(cache_key, context_dict, ttl=300, priority=1)
        
        logger.info(f"📦 上下文构建完成: session={session_id}")
        logger.info(f"  - heritages: {len(context.plan_data.heritage_items)} items")
        logger.info(f"  - cached_data: {len(context.cached_data)} items")
        logger.debug(f"  - heritage_ids: {context.plan_data.get_heritage_ids()}")
        logger.debug(f"  - departure: {context.plan_data.departure_location}")
        
        return context
    
    def _context_to_dict(self, context: UnifiedContext) -> Dict[str, Any]:
        """将上下文转换为字典用于缓存"""
        return {
            'session_id': context.session_id,
            'user_id': context.user_id,
            'plan_id': context.plan_id,
            'plan_data': {
                'departure_location': context.plan_data.departure_location,
                'travel_days': context.plan_data.travel_days,
                'travel_mode': context.plan_data.travel_mode,
                'group_size': context.plan_data.group_size,
                'budget_range': context.plan_data.budget_range,
                'special_requirements': context.plan_data.special_requirements,
                'heritage_items': [
                    {'id': h.id, 'name': h.name, 'region': h.region, 
                     'category': h.category, 'level': h.level}
                    for h in context.plan_data.heritage_items
                ],
                'itinerary': context.plan_data.itinerary,
            },
            'conversation_history': [
                {'role': t.role, 'content': t.content, 'timestamp': t.timestamp}
                for t in context.conversation_history
            ],
            'detected_intent': context.detected_intent.value if context.detected_intent else 'UNKNOWN',
            'cached_data': context.cached_data,
        }
    
    def _dict_to_context(self, data: Dict[str, Any]) -> UnifiedContext:
        """从字典恢复上下文"""
        context = UnifiedContext(session_id=data.get('session_id', ''))
        context.user_id = data.get('user_id')
        context.plan_id = data.get('plan_id', '')
        
        plan_data = data.get('plan_data', {})
        context.plan_data = PlanData(
            departure_location=plan_data.get('departure_location', ''),
            travel_days=plan_data.get('travel_days', 0),
            travel_mode=plan_data.get('travel_mode', 'driving'),
            group_size=plan_data.get('group_size', 1),
            budget_range=plan_data.get('budget_range', ''),
            special_requirements=plan_data.get('special_requirements', []),
            itinerary=plan_data.get('itinerary', []),
        )
        
        for item in plan_data.get('heritage_items', []):
            heritage = HeritageItem(
                id=item.get('id', 0),
                name=item.get('name', ''),
                region=item.get('region', ''),
                category=item.get('category', ''),
                level=item.get('level', ''),
            )
            if heritage.id:
                context.plan_data.heritage_items.append(heritage)
        
        for t in data.get('conversation_history', []):
            context.conversation_history.append(ConversationTurn(
                role=t.get('role', ''),
                content=t.get('content', ''),
                timestamp=t.get('timestamp', ''),
            ))
        
        intent_str = data.get('detected_intent', 'UNKNOWN')
        try:
            context.detected_intent = IntentType(intent_str)
        except ValueError:
            context.detected_intent = IntentType.UNKNOWN
        
        context.cached_data = data.get('cached_data', {})
        
        return context
    
    def invalidate_cache(self, session_id: str):
        """使上下文缓存失效"""
        self.cache_manager.invalidate(f"context:{session_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取构建统计"""
        total = self._stats['contexts_built']
        hit_rate = self._stats['cache_hits'] / max(total, 1)
        return {
            **self._stats,
            'cache_hit_rate': f"{hit_rate:.2%}",
            'cache_manager_stats': self.cache_manager.get_stats(),
        }
    
    def _get_cached_data(self, session) -> Dict[str, Any]:
        """收集所有缓存数据，避免重复查询"""
        cached = {}
        
        try:
            from Agent.services.geocoding import get_geocoding_service
            geo_service = get_geocoding_service()
            
            heritage_names = []
            if hasattr(session, 'heritage_names') and session.heritage_names:
                heritage_names = list(session.heritage_names)
            
            if hasattr(session, 'departure_location') and session.departure_location:
                heritage_names.append(session.departure_location)
            
            current_plan = getattr(session, 'current_plan', {}) or {}
            heritage_items = current_plan.get('heritage_items', [])
            for item in heritage_items:
                if isinstance(item, dict) and item.get('name'):
                    heritage_names.append(item['name'])
                    if item.get('region'):
                        heritage_names.append(item['region'])
            
            for name in set(heritage_names):
                coords = geo_service._cache.get(name)
                if coords:
                    cached[f"coords_{name}"] = {"lat": coords[0], "lng": coords[1]}
        except Exception as e:
            logger.warning(f"获取地理缓存失败: {e}")
        
        if hasattr(session, 'weather_info') and session.weather_info:
            cached['weather'] = session.weather_info
        
        if hasattr(session, 'location_coordinates') and session.location_coordinates:
            cached['coordinates'] = session.location_coordinates
        
        return cached
    
    def _build_plan_data(self, session) -> PlanData:
        """构建规划数据"""
        plan_data = PlanData()
        
        plan_data.departure_location = getattr(session, 'departure_location', '') or ''
        plan_data.travel_days = getattr(session, 'travel_days', 0) or 0
        plan_data.travel_mode = getattr(session, 'travel_mode', 'driving') or 'driving'
        plan_data.group_size = getattr(session, 'group_size', 1) or 1
        plan_data.budget_range = getattr(session, 'budget_range', '') or ''
        plan_data.special_requirements = list(getattr(session, 'special_requirements', []) or [])
        
        current_plan = getattr(session, 'current_plan', {}) or {}
        if isinstance(current_plan, dict):
            heritage_items = current_plan.get('heritage_items', [])
            if heritage_items:
                for item in heritage_items:
                    if isinstance(item, dict):
                        heritage = HeritageItem(
                            id=self._safe_int(item.get('id')),
                            name=item.get('name', ''),
                            region=item.get('region', item.get('location', '')),
                            category=item.get('category', ''),
                            level=item.get('level', ''),
                            latitude=self._safe_float(item.get('latitude')),
                            longitude=self._safe_float(item.get('longitude'))
                        )
                        if heritage.id:
                            plan_data.heritage_items.append(heritage)
            
            plan_data.itinerary = current_plan.get('itinerary', []) or []
        
        if not plan_data.heritage_items:
            heritage_ids = list(getattr(session, 'heritage_ids', []) or [])
            heritage_names = list(getattr(session, 'heritage_names', []) or [])
            
            for i, hid in enumerate(heritage_ids):
                heritage = HeritageItem(
                    id=self._safe_int(hid),
                    name=heritage_names[i] if i < len(heritage_names) else f'项目{hid}'
                )
                if heritage.id:
                    plan_data.heritage_items.append(heritage)
        
        basic_info = current_plan.get('basic_info', {}) if current_plan else {}
        if basic_info:
            if not plan_data.departure_location:
                plan_data.departure_location = basic_info.get('departure', '')
            if not plan_data.travel_days:
                plan_data.travel_days = basic_info.get('duration', 0)
            if not plan_data.travel_mode:
                plan_data.travel_mode = basic_info.get('travel_mode', 'driving')
            if not plan_data.group_size:
                plan_data.group_size = basic_info.get('group_size', 1)
            if not plan_data.budget_range:
                plan_data.budget_range = basic_info.get('budget_range', '')
        
        return plan_data
    
    def _safe_int(self, value: Any) -> int:
        """安全转换为整数"""
        if value is None:
            return 0
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            if value.isdigit():
                return int(value)
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """安全转换为浮点数"""
        if value is None:
            return None
        if isinstance(value, float):
            return value
        if isinstance(value, int):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return None
        return None
    
    def detect_intent(self, user_input: str, context: UnifiedContext) -> IntentType:
        """检测用户意图"""
        if not user_input:
            return IntentType.UNKNOWN
        
        input_lower = user_input.lower()
        
        plan_keywords = ['我的规划', '我的行程', '我的路线', '已选', '行程安排', '规划是什么', '行程是什么']
        weather_keywords = ['天气', '气温', '下雨', '晴天', '温度', '天气预报']
        heritage_keywords = ['非遗', '项目介绍', '历史', '特色', '什么是', '介绍一下']
        route_keywords = ['路线', '怎么走', '距离', '多远', '路线安排', '先去哪', '顺序']
        modify_keywords = ['修改', '调整', '增加', '删除', '换', '改一下', '去掉']
        geo_keywords = ['经纬度', '坐标', '位置', '在哪', '地址']
        
        if any(kw in input_lower for kw in plan_keywords):
            return IntentType.PLAN_RELATED
        
        if any(kw in input_lower for kw in weather_keywords):
            return IntentType.WEATHER_QUERY
        
        if any(kw in input_lower for kw in route_keywords):
            return IntentType.ROUTE_QUERY
        
        if any(kw in input_lower for kw in modify_keywords):
            return IntentType.MODIFICATION
        
        if any(kw in input_lower for kw in heritage_keywords):
            return IntentType.HERITAGE_QUERY
        
        if any(kw in input_lower for kw in geo_keywords):
            return IntentType.GENERAL_QUERY
        
        return IntentType.GENERAL_QUERY
    
    def build_from_dict(self, data: Dict[str, Any]) -> UnifiedContext:
        """从字典构建上下文（用于测试和兼容）"""
        context = UnifiedContext()
        
        context.session_id = data.get('session_id', '')
        context.user_id = data.get('user_id')
        context.plan_id = data.get('plan_id', '')
        
        plan_data = data.get('plan_data', data.get('plan_summary', {}))
        if isinstance(plan_data, dict):
            context.plan_data = PlanData(
                departure_location=plan_data.get('departure_location', ''),
                travel_days=plan_data.get('travel_days', 0),
                travel_mode=plan_data.get('travel_mode', 'driving'),
                group_size=plan_data.get('group_size', 1),
                budget_range=plan_data.get('budget_range', ''),
                special_requirements=plan_data.get('special_requirements', []),
                itinerary=plan_data.get('itinerary', [])
            )
            
            heritage_items = plan_data.get('heritage_items', [])
            for item in heritage_items:
                if isinstance(item, dict):
                    heritage = HeritageItem(
                        id=self._safe_int(item.get('id')),
                        name=item.get('name', ''),
                        region=item.get('region', ''),
                        category=item.get('category', ''),
                        level=item.get('level', '')
                    )
                    if heritage.id:
                        context.plan_data.heritage_items.append(heritage)
        
        return context


_context_builder: Optional[ContextBuilder] = None


def get_context_builder() -> ContextBuilder:
    """获取上下文构建器单例"""
    global _context_builder
    if _context_builder is None:
        _context_builder = ContextBuilder()
    return _context_builder


def build_context(session_id: str) -> UnifiedContext:
    """便捷函数：构建上下文"""
    return get_context_builder().build_from_session(session_id)
