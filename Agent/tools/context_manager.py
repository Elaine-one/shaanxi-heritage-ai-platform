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
    
    async def build_context(self, session_id: str, heritage_ids: List[int] = None) -> ToolContext:
        """
        构建工具执行上下文
        
        Args:
            session_id: 会话ID
            heritage_ids: 当前涉及的非遗项目ID列表
        
        Returns:
            ToolContext: 完整的工具上下文
        """
        context = ToolContext(session_id=session_id)
        
        session = self.session_pool.get_session(session_id)
        if session:
            context.user_id = session.user_id
            
            if hasattr(session, 'user_preferences'):
                context.user_preferences = session.user_preferences or {}
            
            if hasattr(session, 'current_plan') and session.current_plan:
                context.current_plan = session.current_plan
                if 'heritage_ids' in session.current_plan:
                    context.heritage_ids = session.current_plan['heritage_ids']
            
            heritage_items = []
            if hasattr(session, 'current_plan') and session.current_plan:
                heritage_items = session.current_plan.get('heritage_items', [])
            
            if not heritage_items and hasattr(session, 'heritage_ids'):
                heritage_items = [{'id': hid, 'name': name} for hid, name in zip(
                    session.heritage_ids or [],
                    session.heritage_names or []
                )]
            
            if heritage_items or hasattr(session, 'departure_location'):
                context.plan_summary = {
                    'heritage_items': heritage_items,
                    'departure_location': getattr(session, 'departure_location', ''),
                    'travel_days': getattr(session, 'travel_days', 0),
                    'travel_mode': getattr(session, 'travel_mode', 'driving'),
                    'itinerary': getattr(session, 'itinerary', [])
                }
                if heritage_items and not context.heritage_ids:
                    context.heritage_ids = [h.get('id') for h in heritage_items if h.get('id')]
            
            if hasattr(session, 'conversation_history') and session.conversation_history:
                context.conversation_summary = self._summarize_conversation(session.conversation_history[-5:])
        
        if heritage_ids:
            context.heritage_ids = heritage_ids
        
        if self.kg and self.kg.is_connected():
            context.kg_connected = True
            
            if context.heritage_ids:
                for hid in context.heritage_ids[:3]:
                    try:
                        nearby = self.kg.query_nearby_heritages_by_id(hid, limit=3)
                        if nearby:
                            context.nearby_heritages[hid] = nearby
                    except Exception as e:
                        logger.warning(f"查询邻近非遗失败 (ID:{hid}): {e}")
        
        if context.heritage_ids:
            try:
                rag_results = self.vector_store.search(
                    query=f"非遗项目 {' '.join(str(hid) for hid in context.heritage_ids[:3])}",
                    collection_name='heritage_knowledge',
                    top_k=3
                )
                if rag_results:
                    context.rag_context = "\n".join([
                        r.get('content', '')[:200] for r in rag_results[:2]
                    ])
            except Exception as e:
                logger.warning(f"RAG检索失败: {e}")
        
        logger.debug(f"工具上下文构建完成: session={session_id}, heritage_ids={context.heritage_ids}, nearby={len(context.nearby_heritages)}")
        
        return context
    
    def _summarize_conversation(self, history: List[Dict]) -> str:
        """简要总结对话历史"""
        if not history:
            return ""
        
        user_msgs = [m.get('content', '') for m in history if m.get('role') == 'user']
        if user_msgs:
            return f"用户最近询问: {user_msgs[-1][:100]}"
        return ""
    
    def inject_to_tool(self, tool_instance: Any, context: ToolContext):
        """
        将上下文注入到工具实例
        
        Args:
            tool_instance: 工具实例
            context: 工具上下文
        """
        tool_instance._context = context
        
        if hasattr(tool_instance, 'user_preferences'):
            tool_instance.user_preferences = context.user_preferences
        
        if hasattr(tool_instance, 'current_plan'):
            tool_instance.current_plan = context.current_plan
        
        if hasattr(tool_instance, 'nearby_heritages'):
            tool_instance.nearby_heritages = context.nearby_heritages
        
        logger.debug(f"上下文已注入到工具: {tool_instance.__class__.__name__}")


_context_manager: Optional[ToolContextManager] = None


def get_context_manager() -> ToolContextManager:
    """获取上下文管理器单例"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ToolContextManager()
    return _context_manager


async def build_tool_context(session_id: str, heritage_ids: List[int] = None) -> ToolContext:
    """便捷函数：构建工具上下文"""
    return await get_context_manager().build_context(session_id, heritage_ids)
