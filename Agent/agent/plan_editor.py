#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旅游规划编辑器模块
集成 LangGraph ReAct Agent，支持工具调用
使用统一上下文管理
"""

import json
from typing import Dict, Any, List
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
        """
        初始化规划编辑器
        """
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
                               user_id: str = None) -> Dict[str, Any]:
        """开始编辑会话"""
        try:
            session_pool = get_session_pool()
             
            session_context = await session_pool.create_session(
                plan_id=plan_id,
                original_plan=original_plan,
                user_id=user_id
            )
            
            if not session_context:
                return {
                    'success': False,
                    'error': '创建会话失败',
                    'error_type': 'session_creation_error',
                    'timestamp': datetime.now().isoformat()
                }
            
            session_id = session_context.session_id
            
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
            
            full_response = ""
            async for chunk in self.langchain_agent.run_stream(user_message, context):
                full_response += chunk
                yield chunk
            
            if full_response:
                context.add_conversation_turn('assistant', full_response)
                
                last_turn = context.conversation_history[-1] if context.conversation_history else None
                if last_turn and last_turn.role == 'assistant':
                    session_pool.add_conversation(session_id, 'assistant', full_response)
                logger.debug(f"会话 {session_id} AI响应已保存，长度: {len(full_response)}")
            
        except Exception as e:
            logger.error(f"流式处理编辑请求时发生错误: {str(e)}")
            logger.exception("完整错误堆栈:")
            yield f"错误: 处理编辑请求失败: {str(e)}"
    
    def _generate_plan_understanding(self, plan: Dict[str, Any]) -> str:
        """生成规划理解文本"""
        try:
            understanding_parts = []
            
            # 基本信息
            destination = plan.get('destination', '未指定目的地')
            understanding_parts.append(f"📍 目的地: {destination}")
            
            travel_days = plan.get('travel_days') or plan.get('duration')
            if travel_days:
                understanding_parts.append(f"⏰ 行程天数: {travel_days}天")
            
            # 预算信息
            budget = plan.get('budget')
            if budget:
                understanding_parts.append(f"💰 预算: {budget}元")
            
            # 日程安排
            itinerary = plan.get('itinerary', [])
            if itinerary:
                understanding_parts.append("\n📅 行程安排:")
                for i, day_plan in enumerate(itinerary, 1):
                    day_title = day_plan.get('day', f'第{i}天')
                    understanding_parts.append(f"  {day_title}:")
                    
                    activities = day_plan.get('activities', [])
                    for activity in activities:
                        if isinstance(activity, dict):
                            name = activity.get('name', '未知活动')
                            time = activity.get('time', '')
                            if time:
                                understanding_parts.append(f"    • {time} - {name}")
                            else:
                                understanding_parts.append(f"    • {name}")
                        else:
                            understanding_parts.append(f"    • {activity}")
            
            # 偏好设置
            preferences = plan.get('preferences', {})
            if preferences:
                understanding_parts.append("\n🎯 偏好设置:")
                for key, value in preferences.items():
                    if value:
                        understanding_parts.append(f"  • {key}: {value}")
            
            return "\n".join(understanding_parts)
            
        except Exception as e:
            logger.warning(f"生成规划理解时发生错误: {str(e)}")
            return f"规划信息: {json.dumps(plan, ensure_ascii=False, indent=2)}"
    
    def _build_plan_summary(self, plan: Dict[str, Any]) -> str:
        """构建规划摘要"""
        try:
            summary_parts = []
            
            # 从basic_info中获取用户信息
            basic_info = plan.get('basic_info', {})
            
            # 基本信息
            destination = plan.get('destination', basic_info.get('title', '未指定'))
            summary_parts.append(f"目的地: {destination}")
            
            days = basic_info.get('duration', plan.get('travel_days') or plan.get('duration', '未指定'))
            summary_parts.append(f"天数: {days}")
            
            # 用户偏好信息 - 从basic_info获取
            departure_location = basic_info.get('departure', plan.get('departure_location', '未指定'))
            if departure_location and departure_location != '未指定':
                summary_parts.append(f"出发地: {departure_location}")
            
            travel_mode = basic_info.get('travel_mode', plan.get('travel_mode', '未指定'))
            if travel_mode and travel_mode != '未指定':
                summary_parts.append(f"交通方式: {travel_mode}")
            
            group_size = basic_info.get('group_size', plan.get('group_size'))
            if group_size:
                summary_parts.append(f"人数: {group_size}人")
            
            budget_range = basic_info.get('budget_range', plan.get('budget_range', '未指定'))
            if budget_range and budget_range != '未指定':
                summary_parts.append(f"预算范围: {budget_range}")
            
            budget = plan.get('budget', '未指定')
            if budget and budget != '未指定':
                summary_parts.append(f"预算: {budget}元")
            
            # 特殊要求
            special_requirements = plan.get('special_requirements', [])
            if special_requirements:
                summary_parts.append(f"特殊要求: {', '.join(special_requirements)}")
            
            # 行程安排
            itinerary = plan.get('itinerary', [])
            if itinerary:
                summary_parts.append(f"\n行程安排: 共{len(itinerary)}天")
            
            # 非遗项目
            heritage_items = plan.get('heritage_items', [])
            if heritage_items:
                summary_parts.append("\n已选择的非遗项目:")
                for i, item in enumerate(heritage_items, 1):
                    name = item.get('name', item.get('title', '未知项目'))
                    location = item.get('location', item.get('region', '未知地点'))
                    summary_parts.append(f"  {i}. {name} ({location})")
            
            return '\n'.join(summary_parts)
            
        except Exception as e:
            logger.error(f"构建规划摘要失败: {str(e)}")
            return str(plan)
    
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
    
    async def generate_comprehensive_plan(self, session_id: str) -> Dict[str, Any]:
        """生成包含对话内容和天气信息的综合规划"""
        try:
            session_pool = get_session_pool()
            session_context = session_pool.get_session(session_id)
            
            if not session_context:
                return {
                    'success': False,
                    'error': '会话不存在'
                }
            
            current_plan = session_context.current_plan
            conversation_history = session_context.conversation_history if session_context.conversation_history else []
            
            # 获取天气信息
            weather_info = None
            destination = current_plan.get('destination')
            if destination:
                # 这里需要根据目的地获取坐标，简化处理
                weather_info = await self._get_destination_weather(destination)
            
            # 合并所有信息
            comprehensive_plan = {
                'basic_info': current_plan,
                'conversation_summary': self._summarize_conversation(conversation_history),
                'weather_forecast': weather_info,
                'generated_at': datetime.now().isoformat(),
                'session_id': session_id
            }
            
            return {
                'success': True,
                'comprehensive_plan': comprehensive_plan
            }
            
        except Exception as e:
            logger.error(f"生成综合规划时发生错误: {str(e)}")
            return {
                'success': False,
                'error': f'生成综合规划失败: {str(e)}'
            }
    
    # PDF导出功能已移至pdf_content_integrator.py
    # 请使用PDFContentIntegrator类进行PDF导出
    
    async def _get_destination_weather(self, destination: str) -> Dict[str, Any]:
        """根据目的地获取天气信息"""
        try:
            # 使用地理编码服务获取坐标
            from Agent.services.geocoding import get_geocoding_service
            geocoding = get_geocoding_service()
            coords = await geocoding.get_coordinates(destination)
            
            if coords:
                lat, lon = coords
                weather_data = await self.weather_service.get_weather_forecast(lat, lon, 7)
                return weather_data
            else:
                return {
                    'success': False,
                    'message': f'暂不支持{destination}的天气查询'
                }
                
        except Exception as e:
            logger.error(f"获取目的地天气时发生错误: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _summarize_conversation(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """总结对话内容"""
        try:
            if not conversation_history:
                return {
                    'total_messages': 0,
                    'summary': '暂无对话记录'
                }
            
            user_messages = [msg for msg in conversation_history if msg['role'] == 'user']
            ai_messages = [msg for msg in conversation_history if msg['role'] == 'assistant']
            
            # 提取关键信息
            key_topics = []
            for msg in user_messages[-5:]:  # 最近5条用户消息
                content = msg['content'][:100]  # 截取前100字符
                key_topics.append(content)
            
            return {
                'total_messages': len(conversation_history),
                'user_messages': len(user_messages),
                'ai_messages': len(ai_messages),
                'key_topics': key_topics,
                'last_conversation_time': conversation_history[-1]['timestamp'] if conversation_history else None
            }
            
        except Exception as e:
            logger.error(f"总结对话时发生错误: {str(e)}")
            return {
                'total_messages': 0,
                'summary': f'对话总结失败: {str(e)}'
            }
    
    # PDF文档创建功能已移至pdf_content_integrator.py
    # 请使用PDFContentIntegrator类的相关方法
    
    async def apply_plan_changes(self, session_id: str, final_plan: Dict[str, Any]) -> Dict[str, Any]:
        """应用规划修改，覆盖原有规划"""
        try:
            logger.info(f"开始应用规划修改，会话ID: {session_id}")
            
            session_pool = get_session_pool()
            session_context = session_pool.get_session(session_id)
            
            # 检查会话是否存在
            if not session_context:
                return {
                    'success': False,
                    'error': f'会话 {session_id} 不存在或已过期',
                    'error_type': 'session_not_found'
                }
            
            # 备份原始规划
            original_plan = session_context.original_plan.copy()
            
            # 更新会话中的当前规划
            session_context.current_plan = final_plan.copy()
            session_context.last_updated = datetime.now().isoformat()
            
            # 记录应用操作到对话历史
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

# 全局实例
_plan_editor_instance = None

def get_plan_editor() -> PlanEditor:
    """
    获取规划编辑器实例（单例模式）
    
    Returns:
        PlanEditor: 规划编辑器实例
    """
    global _plan_editor_instance
    if _plan_editor_instance is None:
        _plan_editor_instance = PlanEditor()
    return _plan_editor_instance