#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旅游规划编辑器模块
集成 LangGraph ReAct Agent，支持工具调用
使用统一上下文管理
"""

from typing import Dict, Any
from datetime import datetime
from loguru import logger
from Agent.models.llm_model import get_llm_model
from Agent.services.weather import get_weather_service
from Agent.tools.base import get_tool_registry
from Agent.memory.session import get_session_pool
from Agent.context import get_context_builder
from .langchain_agent import get_langchain_agent_executor


class PlanEditor:
    """
    简化的旅游规划编辑器
    专注于AI对话和规划内容展示
    使用统一上下文管理
    """
    
    def __init__(self):
        self.llm_model = get_llm_model()
        self.weather_service = get_weather_service()
        self.tool_registry = get_tool_registry()
        self._langchain_agent = None
        self.context_builder = get_context_builder()
    
    @property
    def langchain_agent(self):
        """延迟加载 LangGraph Agent"""
        if self._langchain_agent is None:
            self._langchain_agent = get_langchain_agent_executor()
        return self._langchain_agent
    
    async def start_edit_session(self, 
                               plan_id: str, 
                               original_plan: Dict[str, Any],
                               user_id: str = None,
                               username: str = None) -> Dict[str, Any]:
        """开始编辑会话"""
        try:
            session_pool = get_session_pool()
             
            session_context = await session_pool.create_session(
                plan_id=plan_id,
                original_plan=original_plan,
                user_id=user_id,
                username=username
            )
            
            if not session_context:
                return {
                    'success': False,
                    'error': '创建会话失败',
                    'error_type': 'session_creation_error',
                    'timestamp': datetime.now().isoformat()
                }
            
            session_id = session_context.session_id
            
            self._persist_session_preferences(user_id, username, original_plan)
            
            logger.info(f"编辑会话 {session_id} 已创建，用户: {user_id}")
            
            return {
                'success': True,
                'session_id': session_id,
                'message': '编辑会话已创建，您可以开始与我对话了。',
                'plan_understanding': None
            }
            
        except Exception as e:
            logger.error(f"开始编辑会话时发生错误: {str(e)}")
            logger.exception("完整错误堆栈:")
            return {
                'success': False,
                'error': f'开始编辑会话失败: {str(e)}',
                'error_type': 'session_start_error',
                'timestamp': datetime.now().isoformat()
            }
    
    async def process_edit_request_stream(self, 
                                       session_id: str, 
                                       user_message: str):
        """流式处理用户的对话请求 - 使用统一上下文"""
        try:
            session_pool = get_session_pool()
            
            session_context = session_pool.get_session(session_id)
            
            if not session_context:
                yield "错误: 编辑会话不存在或已过期"
                return
            
            context = self.context_builder.build_from_session(session_id)
            
            context.detected_intent = self.context_builder.detect_intent(user_message, context)
            
            logger.info("📦 上下文构建完成:")
            logger.info(f"  - session_id: {context.session_id}")
            logger.info(f"  - intent: {context.detected_intent}")
            logger.info(f"  - heritages: {len(context.plan_data.heritage_items)} items")
            logger.debug(f"  - heritage_ids: {context.plan_data.get_heritage_ids()}")
            
            context.add_conversation_turn('user', user_message)
            self.context_builder.invalidate_cache(session_id)

            full_response = ""
            async for event in self.langchain_agent.run_stream(user_message, context):
                yield event
                if isinstance(event, dict) and event.get("type") == "content":
                    full_response += event.get("content", "")
            
            if full_response:
                context.add_conversation_turn('assistant', full_response)
                
                try:
                    from Agent.memory.coordinator import get_memory_coordinator
                    coordinator = get_memory_coordinator()
                    await coordinator.append_turn(
                        session_id=session_id,
                        role="user",
                        content=user_message,
                        user_id=context.user_id,
                        username=context.username,
                    )
                    await coordinator.append_turn(
                        session_id=session_id,
                        role="assistant",
                        content=full_response,
                        user_id=context.user_id,
                        username=context.username,
                    )
                except Exception as coord_err:
                    logger.debug(f"MemoryCoordinator 写入失败（不影响主流程）: {coord_err}")
                logger.debug(f"会话 {session_id} AI响应已保存，长度: {len(full_response)}")
            
        except Exception as e:
            logger.error(f"流式处理编辑请求时发生错误: {str(e)}")
            logger.exception("完整错误堆栈:")
            yield f"错误: 处理编辑请求失败: {str(e)}"
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """结束编辑会话"""
        try:
            session_pool = get_session_pool()
            result = session_pool.remove_session(session_id)
            
            if result:
                logger.info(f"编辑会话 {session_id} 已结束")
                return {
                    'success': True,
                    'message': '会话已结束'
                }
            else:
                return {
                    'success': False,
                    'error': '会话不存在或已过期'
                }
            
        except Exception as e:
            logger.error(f"结束会话时发生错误: {str(e)}")
            return {
                'success': False,
                'error': f'结束会话失败: {str(e)}'
            }
    
    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """获取会话信息"""
        try:
            session_pool = get_session_pool()
            session_context = session_pool.get_session(session_id)
            
            if session_context:
                return {
                    'success': True,
                    'session_info': {
                        'session_id': session_context.session_id,
                        'plan_id': session_context.plan_id,
                        'user_id': session_context.user_id,
                        'current_plan': session_context.current_plan,
                        'conversation_history': session_context.conversation_history,
                        'created_at': session_context.created_at,
                        'last_updated': session_context.last_updated,
                        'edit_count': session_context.edit_count
                    }
                }
            else:
                return {
                    'success': False,
                    'error': '会话不存在'
                }
        except Exception as e:
            logger.error(f"获取会话信息时发生错误: {str(e)}")
            return {
                'success': False,
                'error': f'获取会话信息失败: {str(e)}'
            }
    
    async def apply_plan_changes(self, session_id: str, final_plan: Dict[str, Any]) -> Dict[str, Any]:
        """应用规划修改，覆盖原有规划"""
        try:
            logger.info(f"开始应用规划修改，会话ID: {session_id}")
            
            session_pool = get_session_pool()
            session_context = session_pool.get_session(session_id)
            
            if not session_context:
                return {
                    'success': False,
                    'error': f'会话 {session_id} 不存在或已过期',
                    'error_type': 'session_not_found'
                }
            
            original_plan = session_context.original_plan.copy()
            
            session_context.current_plan = final_plan.copy()
            session_context.last_updated = datetime.now().isoformat()
            
            if session_context.conversation_history is None:
                session_context.conversation_history = []
            
            apply_message = {
                'timestamp': datetime.now().isoformat(),
                'type': 'system',
                'content': '用户应用了规划修改，原有规划已被覆盖',
                'action': 'apply_changes'
            }
            session_context.conversation_history.append(apply_message)
            
            session_pool.update_session(session_id, final_plan)
            
            self._persist_plan_to_graph(session_context, final_plan, session_id)
            
            logger.info(f"规划修改已成功应用，会话ID: {session_id}")
            
            return {
                'success': True,
                'message': '规划修改已成功应用，原有规划已被覆盖',
                'updated_plan': final_plan,
                'original_plan': original_plan,
                'session_id': session_id
            }
            
        except Exception as e:
            logger.error(f"应用规划修改时发生错误: {str(e)}")
            return {
                'success': False,
                'error': f'应用修改失败: {str(e)}',
                'error_type': 'apply_error'
            }

    def _persist_plan_to_graph(self, session_context, final_plan: Dict[str, Any], session_id: str):
        try:
            from Agent.memory.l2_graph_store import get_l2_graph_store
            l2_store = get_l2_graph_store()
            if not l2_store.is_available() or not session_context.user_id:
                return
            heritage_ids = []
            for item in final_plan.get('heritage_items', []):
                hid = item.get('id')
                if hid is not None:
                    try:
                        heritage_ids.append(int(hid))
                    except (ValueError, TypeError):
                        pass
            if heritage_ids:
                l2_store.batch_link_heritages(
                    user_id=session_context.user_id,
                    heritage_ids=heritage_ids,
                    rel_type="PLANNED",
                    source="plan_apply",
                    extra_props={
                        "plan_id": session_context.plan_id or "",
                        "session_id": session_id,
                    },
                )
                logger.info(f"规划非遗沉淀到图谱: user={session_context.user_id}, count={len(heritage_ids)}")
        except Exception as e:
            logger.debug(f"规划非遗沉淀到图谱失败（不影响主流程）: {e}")

    def _persist_session_preferences(self, user_id: str, username: str, original_plan: Dict[str, Any]):
        try:
            from Agent.memory.l2_graph_store import get_l2_graph_store
            l2_store = get_l2_graph_store()
            if not l2_store.is_available() or not user_id:
                return
            structured_prefs = []
            basic_info = original_plan.get('basic_info', {})
            budget = basic_info.get('budget')
            if budget:
                try:
                    structured_prefs.append({
                        "type": "budget",
                        "value": {"amount": float(budget), "currency": "CNY"},
                        "confidence": 0.9,
                        "source": "plan_structure",
                    })
                except (ValueError, TypeError):
                    pass
            travel_mode = basic_info.get('travel_mode')
            if travel_mode:
                structured_prefs.append({
                    "type": "travel_mode",
                    "value": {"prefer": [travel_mode]},
                    "confidence": 0.85,
                    "source": "plan_structure",
                })
            group_size = basic_info.get('group_size') or original_plan.get('group_size')
            if group_size:
                structured_prefs.append({
                    "type": "group_preference",
                    "value": {"group_type": str(group_size) + "人出行", "notes": ""},
                    "confidence": 0.7,
                    "source": "plan_structure",
                })
            if structured_prefs:
                l2_store.upsert_user_preferences(
                    user_id=user_id,
                    preferences=structured_prefs,
                    username=username,
                )
                logger.info(f"规划结构化偏好沉淀: user={user_id}, count={len(structured_prefs)}")
        except Exception as e:
            logger.debug(f"规划结构化偏好沉淀失败（不影响主流程）: {e}")

_plan_editor_instance = None

def get_plan_editor() -> PlanEditor:
    global _plan_editor_instance
    if _plan_editor_instance is None:
        _plan_editor_instance = PlanEditor()
    return _plan_editor_instance
