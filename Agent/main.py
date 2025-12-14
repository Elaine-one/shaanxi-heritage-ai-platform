# -*- coding: utf-8 -*-
"""
智能旅游规划Agent主入口文件
提供旅游规划服务的核心接口
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config
from core.travel_planner import TravelPlanner
from core.heritage_analyzer import HeritageAnalyzer
from utils.logger_config import setup_logger

class TravelPlanningAgent:
    """
    智能旅游规划Agent主类
    负责协调各个模块，提供完整的旅游规划服务
    """
    
    def __init__(self):
        """
        初始化Agent
        """
        # 设置日志
        setup_logger()
        logger.info("初始化智能旅游规划Agent")
        
        # 验证配置
        validation_result = config.validate_config()
        if not validation_result['valid']:
            logger.error(f"配置验证失败: {validation_result['errors']}")
            raise ValueError("配置不完整，请检查环境变量")
        
        if validation_result['warnings']:
            logger.warning(f"配置警告: {validation_result['warnings']}")
        
        # 初始化核心组件
        self.heritage_analyzer = HeritageAnalyzer()
        self.travel_planner = TravelPlanner()
        
        # 暴露ali_model属性以供PDF导出使用
        self.ali_model = self.travel_planner.ali_model
        
        logger.info("Agent初始化完成")
    
    async def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        """
        处理用户聊天消息
        
        Args:
            message (str): 用户消息
            session_id (str): 会话ID
        
        Returns:
            Dict[str, Any]: 处理结果，包含AI响应
        """
        try:
            logger.info(f"处理用户消息: {session_id} - {message[:50]}...")
            
            # 导入plan_editor来处理聊天
            from core.plan_editor import get_plan_editor
            
            # 获取plan_editor实例
            plan_editor = get_plan_editor()
            
            # 使用plan_editor处理编辑请求
            result = await plan_editor.process_edit_request(session_id, message)
            
            if result['success']:
                # 格式化AI响应为Markdown格式
                ai_response = result.get('ai_response', '抱歉，我无法处理您的请求。')
                
                # 确保响应包含适当的Markdown格式
                formatted_response = self._format_response_as_markdown(ai_response)
                
                return {
                    'success': True,
                    'response': formatted_response,
                    'session_id': session_id,
                    'conversation_type': result.get('conversation_type', 'general'),
                    'changes_made': result.get('changes_made', False)
                }
            else:
                return {
                    'success': False,
                    'response': result.get('ai_response', '处理消息时发生错误'),
                    'error': result.get('error', '未知错误'),
                    'session_id': session_id
                }
                
        except Exception as e:
            logger.error(f"处理消息时发生错误: {str(e)}")
            return {
                'success': False,
                'response': f'抱歉，处理您的消息时发生了错误: {str(e)}',
                'error': str(e),
                'session_id': session_id
            }
    
    def _format_response_as_markdown(self, response: str) -> str:
        """
        将AI响应格式化为Markdown格式
        
        Args:
            response (str): 原始AI响应
        
        Returns:
            str: 格式化后的Markdown响应
        """
        try:
            # 如果响应已经包含Markdown格式，直接返回
            if any(marker in response for marker in ['###', '##', '#', '**', '*', '- ', '1. ']):
                return response
            
            # 否则，为响应添加基本的Markdown格式
            lines = response.split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    formatted_lines.append('')
                    continue
                
                # 检测是否为标题（包含关键词）
                if any(keyword in line for keyword in ['建议', '推荐', '注意', '提醒', '总结']):
                    formatted_lines.append(f'### {line}')
                # 检测是否为列表项
                elif line.startswith(('1.', '2.', '3.', '4.', '5.', '•', '-')):
                    if not line.startswith('- '):
                        formatted_lines.append(f'- {line}')
                    else:
                        formatted_lines.append(line)
                else:
                    formatted_lines.append(line)
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            logger.warning(f"格式化Markdown时发生错误: {str(e)}")
            return response
    
    async def create_travel_plan(self, 
                               user_id: int,
                               selected_heritage_ids: List[int],
                               start_location: str = None,
                               travel_days: int = None,
                               preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        创建旅游规划
        
        Args:
            user_id (int): 用户ID
            selected_heritage_ids (List[int]): 选中的非遗项目ID列表
            start_location (str, optional): 出发地点
            travel_days (int, optional): 旅游天数
            preferences (Dict[str, Any], optional): 用户偏好设置
        
        Returns:
            Dict[str, Any]: 完整的旅游规划结果
        """
        try:
            logger.info(f"开始为用户{user_id}创建旅游规划，选中项目: {selected_heritage_ids}")
            
            # 步骤1: 分析选中的非遗项目
            logger.info("步骤1: 分析非遗项目信息")
            heritage_analysis = await self.heritage_analyzer.analyze_heritage_items(
                selected_heritage_ids
            )
            
            if not heritage_analysis['success']:
                return {
                    'success': False,
                    'error': '非遗项目分析失败',
                    'details': heritage_analysis.get('error', '未知错误')
                }
            
            # 步骤2: 生成旅游规划
            logger.info("步骤2: 生成旅游规划")
            planning_request = {
                'heritage_ids': selected_heritage_ids,
                'start_location': start_location,
                'travel_days': travel_days,
                'preferences': preferences or {}
            }
            travel_plan = await self.travel_planner.create_travel_plan(planning_request)
            
            if not travel_plan['success']:
                return {
                    'success': False,
                    'error': '旅游规划生成失败',
                    'details': travel_plan.get('error', '未知错误')
                }
            
            # 步骤3: 整合结果
            logger.info("步骤3: 整合规划结果")
            final_result = {
                'success': True,
                'user_id': user_id,
                'plan_id': f"plan_{user_id}_{int(asyncio.get_event_loop().time())}",
                'heritage_analysis': heritage_analysis,
                'travel_plan': travel_plan['plan'],
                'recommendations': travel_plan.get('recommendations', []),
                'created_at': asyncio.get_event_loop().time()
            }
            
            logger.info(f"旅游规划创建成功，规划ID: {final_result['plan_id']}")
            return final_result
            
        except Exception as e:
            logger.error(f"创建旅游规划时发生错误: {str(e)}")
            return {
                'success': False,
                'error': '系统错误',
                'details': str(e)
            }
    
    async def get_plan_progress(self, plan_id: str) -> Dict[str, Any]:
        """
        获取规划进度
        
        Args:
            plan_id (str): 规划ID
        
        Returns:
            Dict[str, Any]: 进度信息
        """
        # 这里可以实现进度跟踪逻辑
        # 目前返回模拟进度
        return {
            'plan_id': plan_id,
            'progress': 100,
            'status': 'completed',
            'message': '规划已完成'
        }
    
    # 导出功能已移至API层实现，此处不再需要

# 全局Agent实例
agent = None

def get_agent() -> TravelPlanningAgent:
    """
    获取Agent实例（单例模式）
    
    Returns:
        TravelPlanningAgent: Agent实例
    """
    global agent
    if agent is None:
        agent = TravelPlanningAgent()
    return agent

async def main():
    """
    主函数，用于测试
    """
    try:
        # 创建Agent实例
        travel_agent = get_agent()
        
        logger.info("智能旅游规划Agent启动成功")
        
    except Exception as e:
        logger.error(f"启动过程中发生错误: {str(e)}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())