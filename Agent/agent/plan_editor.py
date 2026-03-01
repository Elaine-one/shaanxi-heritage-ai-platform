#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
旅游规划编辑器模块
集成LangChain ReAct Agent，支持工具调用
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from Agent.models.llm_model import get_llm_model
from Agent.services.weather import get_weather_service
from Agent.tools.base import get_tool_registry
from Agent.agent.react_agent import get_react_agent
from Agent.memory import get_session_pool

# PDF功能已整合到pdf_content_integrator.py中

class PlanEditor:
    """
    简化的旅游规划编辑器
    专注于AI对话和规划内容展示
    """
    
    def __init__(self):
        """
        初始化规划编辑器
        """
        self.llm_model = get_llm_model()
        self.weather_service = get_weather_service()
        self.tool_registry = get_tool_registry()
        self.react_agent = get_react_agent()
    
    async def start_edit_session(self, 
                               plan_id: str, 
                               original_plan: Dict[str, Any],
                               user_id: str = None) -> Dict[str, Any]:
        """
        开始编辑会话
        
        Args:
            plan_id (str): 规划ID
            original_plan (Dict[str, Any]): 原始规划数据
            user_id (str, optional): 用户ID
        
        Returns:
            Dict[str, Any]: 编辑会话信息
        """
        try:
            session_pool = get_session_pool()
             
            # 在会话池中创建会话
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
    
    async def process_edit_request(self, 
                                 session_id: str, 
                                 user_message: str) -> Dict[str, Any]:
        """
        处理用户的对话请求
        
        Args:
            session_id (str): 编辑会话ID
            user_message (str): 用户消息
        
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            session_pool = get_session_pool()
            
            # 检查会话是否存在
            session_context = session_pool.get_session(session_id)
            
            if not session_context:
                return {
                    'success': False,
                    'error': '编辑会话不存在或已过期',
                    'error_type': 'session_not_found'
                }
            
            # 获取当前规划数据
            current_plan = session_context.current_plan
            
            # 初始化对话历史
            if session_context.conversation_history is None:
                session_context.conversation_history = []
            
            # 记录用户消息
            session_context.conversation_history.append({
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            })
            
            # 获取对话历史
            conversation_history = session_context.conversation_history
            
            # 使用ReAct推理生成AI响应
            ai_response = await self._generate_ai_response_with_react(
                session_id, user_message, current_plan, conversation_history
            )
            
            # 记录AI响应
            session_context.conversation_history.append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now().isoformat()
            })
            
            # 更新会话上下文
            session_pool.update_session_context(session_id, session_context)
            
            # 生成综合规划（合并对话内容和天气信息）
            comprehensive_result = await self.generate_comprehensive_plan(session_id)
            
            # 构建最终响应，包含AI回复和导出选项
            final_response = ai_response
            if comprehensive_result['success']:
                final_response += "\n\n" + "="*50 + "\n"
                final_response += "📋 **综合规划摘要**\n"
                
                comprehensive_plan = comprehensive_result['comprehensive_plan']
                
                # 添加基本信息
                basic_info = comprehensive_plan.get('basic_info', {})
                if basic_info.get('destination'):
                    final_response += f"🎯 **目的地**: {basic_info['destination']}\n"
                if basic_info.get('duration') or basic_info.get('travel_days'):
                    days = basic_info.get('duration', basic_info.get('travel_days', ''))
                    final_response += f"📅 **行程天数**: {days}天\n"
                if basic_info.get('budget'):
                    final_response += f"💰 **预算**: {basic_info['budget']}元\n"
                
                # 添加天气信息
                weather_info = comprehensive_plan.get('weather_forecast')
                if weather_info and weather_info.get('success'):
                    final_response += "\n🌤️ **天气预报**:\n"
                    forecast = weather_info.get('forecast', [])
                    for i, day in enumerate(forecast[:3]):  # 显示前3天
                        final_response += f"  {day.get('date', '')}: {day.get('condition', '')} {day.get('min_temp', '')}°C~{day.get('max_temp', '')}°C\n"
                
                # 添加对话摘要
                conv_summary = comprehensive_plan.get('conversation_summary', {})
                if conv_summary.get('total_messages', 0) > 0:
                    final_response += f"\n💬 **对话统计**: 共{conv_summary['total_messages']}条消息\n"
                
                final_response += "\n" + "="*50 + "\n"
                final_response += "📄 **导出规划**: 您可以通过主系统导出精美的PDF出行表格\n"
                final_response += "💡 PDF导出功能已整合到专门的内容整合器中，提供更智能的AI内容整合。"
            
            return {
                'success': True,
                'response': final_response,
                'changes_made': False,
                'session_id': session_id,
                'comprehensive_plan_available': comprehensive_result['success']
            }
            
        except Exception as e:
            logger.error(f"处理编辑请求时发生错误: {str(e)}")
            logger.exception("完整错误堆栈:")
            return {
                'success': False,
                'error': f'处理编辑请求失败: {str(e)}',
                'error_type': 'edit_request_error',
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_plan_understanding(self, plan: Dict[str, Any]) -> str:
        """
        生成规划理解文本
        
        Args:
            plan (Dict[str, Any]): 规划数据
        
        Returns:
            str: 规划理解文本
        """
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
    
    async def _generate_ai_response_with_react(
        self, 
        session_id: str, 
        user_message: str, 
        current_plan: Dict[str, Any],
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """
        使用LangChain ReAct Agent生成AI响应
        
        Args:
            session_id (str): 会话ID
            user_message (str): 用户消息
            current_plan (Dict[str, Any]): 当前规划
            conversation_history (List[Dict[str, Any]]): 对话历史
        
        Returns:
            str: AI响应
        """
        try:
            logger.info(f"LangChain Agent: 开始处理用户输入: {user_message[:50]}...")
            
            # 调试：打印规划数据结构
            logger.debug(f"current_plan keys: {list(current_plan.keys()) if current_plan else 'None'}")
            logger.debug(f"basic_info: {current_plan.get('basic_info', 'missing')}")
            
            # 构建规划摘要
            plan_summary = self._build_plan_summary(current_plan)
            logger.debug(f"plan_summary: {plan_summary}")
            
            # 调用LangChain Agent
            agent_result = await self.react_agent.run(
                user_input=user_message,
                plan_summary=plan_summary,
                conversation_history=conversation_history
            )
            
            logger.info(f"LangChain Agent: 处理完成，success={agent_result.get('success')}")
            
            if agent_result.get('success'):
                answer = agent_result.get('answer', '')
                logger.info(f"LangChain Agent: 成功返回答案，长度={len(answer)}")
                return answer
            else:
                error = agent_result.get('error', '未知错误')
                logger.error(f"LangChain Agent: 处理失败: {error}")
                return f"抱歉，处理您的请求时遇到了问题: {error}"
                
        except Exception as e:
            logger.error(f"LangChain Agent执行异常: {str(e)}")
            logger.exception("完整错误堆栈:")
            return f"抱歉，处理您的消息时出现了问题: {str(e)}"
    
    def _build_plan_summary(self, plan: Dict[str, Any]) -> str:
        """
        构建规划摘要
        
        Args:
            plan (Dict[str, Any]): 规划数据
        
        Returns:
            str: 规划摘要
        """
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
                summary_parts.append(f"\n已选择的非遗项目:")
                for i, item in enumerate(heritage_items, 1):
                    name = item.get('name', item.get('title', '未知项目'))
                    location = item.get('location', item.get('region', '未知地点'))
                    summary_parts.append(f"  {i}. {name} ({location})")
            
            return '\n'.join(summary_parts)
            
        except Exception as e:
            logger.error(f"构建规划摘要失败: {str(e)}")
            return str(plan)
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        结束编辑会话
        
        Args:
            session_id (str): 会话ID
        
        Returns:
            Dict[str, Any]: 结束结果
        """
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
        """
        获取会话信息
        
        Args:
            session_id (str): 会话ID
        
        Returns:
            Dict[str, Any]: 会话信息
        """
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
        """
        生成包含对话内容和天气信息的综合规划
        
        Args:
            session_id (str): 会话ID
        
        Returns:
            Dict[str, Any]: 综合规划数据
        """
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
        """
        根据目的地获取天气信息
        
        Args:
            destination (str): 目的地名称
        
        Returns:
            Dict[str, Any]: 天气信息
        """
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
        """
        总结对话内容
        
        Args:
            conversation_history (List[Dict[str, Any]]): 对话历史
        
        Returns:
            Dict[str, Any]: 对话摘要
        """
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
        """
        应用规划修改，覆盖原有规划
        
        Args:
            session_id (str): 会话ID
            final_plan (Dict[str, Any]): 最终规划数据
        
        Returns:
            Dict[str, Any]: 应用结果
        """
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
            
            # 更新会话上下文
            session_pool.update_session_context(session_id, session_context)
            
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