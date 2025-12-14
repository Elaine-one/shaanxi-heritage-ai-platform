##--- START OF FILE ali_model.py ---

# -*- coding: utf-8 -*-
"""
阿里云模型调用模块 (完整版)
实现与DashScope API的集成，提供智能对话和分析能力
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from loguru import logger
import dashscope
from dashscope import Generation
from config import config

class AliCloudModel:
    """
    阿里云模型调用类
    封装DashScope API调用逻辑
    """
    
    def __init__(self):
        """
        初始化阿里云模型
        """
        # 设置API密钥
        dashscope.api_key = config.DASHSCOPE_API_KEY
        
        # 模型配置
        self.model_config = config.get_model_config()
        
        # 【关键配置修正】
        # 强制提升 max_tokens 以支持长文档生成
        if self.model_config.get('max_tokens', 1500) < 4500:
            logger.info("AliModel: 自动提升 max_tokens 至 4500")
            self.model_config['max_tokens'] = 4500
            
        logger.info(f"阿里云模型初始化完成，使用模型: {self.model_config['model']}")
    
    async def _call_model(self, prompt: str) -> Dict[str, Any]:
        """
        调用阿里云模型 - 核心基础方法
        """
        try:
            logger.debug(f"调用模型，提示词长度: {len(prompt)}")
            
            messages = [
                {
                    'role': 'system',
                    'content': '你是一个专业的旅游规划助手，专门为用户制定陕西非物质文化遗产相关的旅游计划。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            # 调用API
            response = Generation.call(
                model=self.model_config['model'],
                messages=messages,
                temperature=0.7,  # 适度增加创造性
                max_tokens=self.model_config['max_tokens'],
                top_p=self.model_config['top_p'],
                result_format='message'
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                logger.debug(f"模型响应成功，内容长度: {len(content)}")
                return {
                    'success': True,
                    'content': content
                }
            else:
                logger.error(f"模型调用失败: {response.message}")
                return {
                    'success': False,
                    'error': f'API调用失败: {response.message}'
                }
                
        except Exception as e:
            logger.error(f"模型调用异常: {str(e)}")
            return {
                'success': False,
                'error': f'调用异常: {str(e)}'
            }
    
    # ------------------------------------------------------------------
    # 业务方法 (完整保留)
    # ------------------------------------------------------------------

    async def generate_travel_plan(self, 
                                 heritage_items: List[Dict[str, Any]], 
                                 user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成结构化旅游规划 (用于API接口)
        """
        try:
            prompt = self._build_travel_plan_prompt(heritage_items, user_preferences)
            response = await self._call_model(prompt)
            
            if response['success']:
                plan_data = self._parse_json_response(response['content'])
                return {'success': True, 'plan': plan_data}
            else:
                return {'success': False, 'error': response.get('error', '模型调用失败')}
        except Exception as e:
            logger.error(f"生成规划异常: {str(e)}")
            return {'success': False, 'error': f'生成规划失败: {str(e)}'}
    
    async def analyze_heritage_compatibility(self, heritage_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析非遗项目兼容性"""
        try:
            prompt = self._build_compatibility_prompt(heritage_items)
            response = await self._call_model(prompt)
            if response['success']:
                return {'success': True, 'analysis': self._parse_json_response(response['content'])}
            return {'success': False, 'error': response.get('error', '分析失败')}
        except Exception as e:
            return {'success': False, 'error': f'分析失败: {str(e)}'}
    
    async def generate_travel_suggestions(self, 
                                        location: str, 
                                        season: str, 
                                        duration: int) -> Dict[str, Any]:
        """生成旅游建议"""
        try:
            prompt = self._build_suggestions_prompt(location, season, duration)
            response = await self._call_model(prompt)
            if response['success']:
                suggestions = self._parse_suggestions_response(response['content'])
                return {'success': True, 'suggestions': suggestions}
            else:
                return {'success': False, 'error': response.get('error', '生成建议失败')}
        except Exception as e:
            return {'success': False, 'error': f'生成建议失败: {str(e)}'}

    # ------------------------------------------------------------------
    # Prompt 构建器 (完整保留)
    # ------------------------------------------------------------------
    
    def _build_travel_plan_prompt(self, heritage_items: List[Dict[str, Any]], user_preferences: Dict[str, Any] = None) -> str:
        heritage_info = "\n".join([
            f"- {item['name']} ({item.get('category','文化')}, {item.get('region','陕西')})"
            for item in heritage_items
        ])
        
        pref_text = ""
        if user_preferences:
            pref_text = f"""
用户需求:
- 出发地: {user_preferences.get('start_location', '未指定')}
- 天数: {user_preferences.get('travel_days', '未指定')}
- 交通: {user_preferences.get('transport_preference', '不限')}
- 预算: {user_preferences.get('budget_range', '不限')}
"""
        
        prompt = f"""
请为以下陕西非遗项目制定{user_preferences.get('travel_days', 3) if user_preferences else 3}天旅游规划:

{heritage_info}
{pref_text}

要求:
1. 每天安排1-2个主要非遗项目，穿插附近景点
2. 行程灵活，留有余地
3. 突出文化体验深度
4. 必须返回纯 JSON 格式，包含 itinerary, travel_tips, cultural_notes
"""
        return prompt
    
    def _build_compatibility_prompt(self, heritage_items: List[Dict[str, Any]]) -> str:
        heritage_info = "\n".join([f"- {item['name']}" for item in heritage_items])
        prompt = f"""
请分析以下非遗项目的最佳组合方案:
{heritage_info}
主要分析地理位置是否集中、文化主题关联度。JSON格式返回。
"""
        return prompt
    
    def _build_suggestions_prompt(self, location: str, season: str, duration: int) -> str:
        prompt = f"""
请提供{location}{season}{duration}天非遗旅游建议，重点包括必玩项目、穿搭、美食。要求简洁实用。
"""
        return prompt
    
    # ------------------------------------------------------------------
    # 响应解析器 (完整保留)
    # ------------------------------------------------------------------

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """尝试解析JSON响应"""
        try:
            # 清洗Markdown代码块
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            # 查找JSON边界
            if '{' in content and '}' in content:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                json_content = content[json_start:json_end]
                return json.loads(json_content)
                
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("无法解析JSON响应，返回原始内容")
            return {
                'raw_content': content,
                'format': 'text'
            }
            
    def _parse_suggestions_response(self, content: str) -> Dict[str, Any]:
        return {
            'content': content,
            'format': 'text'
        }

# 全局模型实例
_model_instance = None

def get_ali_model() -> AliCloudModel:
    """
    获取阿里云模型实例（单例模式）
    """
    global _model_instance
    if _model_instance is None:
        _model_instance = AliCloudModel()
    return _model_instance