##--- START OF FILE ali_model.py ---

# -*- coding: utf-8 -*-
"""
阿里云模型调用模块 (完整版)
实现与DashScope API的集成，提供智能对话和分析能力
包含ReAct推理支持
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from loguru import logger
import dashscope
from dashscope import Generation
from Agent.config import config

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
    
    # ------------------------------------------------------------------
    # ReAct 推理方法 (新增)
    # ------------------------------------------------------------------

    async def react推理(self, 
                       user_input: str,
                       tools_info: List[Dict[str, Any]],
                       conversation_history: List[Dict[str, str]] = None,
                       plan_summary: str = None,
                       max_iterations: int = 5) -> Dict[str, Any]:
        """
        执行ReAct推理循环
        
        Args:
            user_input: 用户输入
            tools_info: 可用工具信息列表
            conversation_history: 对话历史
            plan_summary: 规划摘要信息
            max_iterations: 最大迭代次数
            
        Returns:
            Dict包含: thought(思考), action(动作), observation(观察), final_answer(最终答案)
        """
        try:
            # 构建ReAct系统提示
            system_prompt = self._build_react_system_prompt(tools_info)
            
            # 构建对话上下文
            history_text = ""
            if conversation_history:
                history_text = "\n".join([
                    f"{msg['role']}: {msg['content'][:200]}"  # 限制历史长度
                    for msg in conversation_history[-5:]  # 只保留最近5轮
                ])
            
            # 构建规划摘要上下文
            plan_context = ""
            if plan_summary:
                plan_context = f"""
当前旅游规划摘要:
{plan_summary}
"""
            
            user_prompt = f"""
用户输入: {user_input}
{plan_context}
对话历史:
{history_text}

请按照以下格式回复：
Thought: 你对这个问题的思考分析
Action: 工具名称 | 参数JSON (如果没有需要调用的工具，填"final_answer")
Observation: 工具返回结果 (如果没有调用工具，填"无")

开始分析：
"""
            
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            
            # 调用模型
            response = Generation.call(
                model=self.model_config['model'],
                messages=messages,
                temperature=0.3,  # 较低温度保证推理准确
                max_tokens=1000,
                top_p=self.model_config.get('top_p', 0.95),
                result_format='message'
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                
                # 解析ReAct响应
                parsed = self._parse_react_response(content)
                
                logger.info(f"ReAct推理完成: thought={parsed.get('thought','')[:50]}...")
                
                # 如果action是final_answer，使用observation作为最终答案
                if parsed.get('action', '').strip() == 'final_answer':
                    parsed['final_answer'] = parsed.get('observation', parsed.get('thought', ''))
                
                return {
                    'success': True,
                    **parsed
                }
            else:
                return {
                    'success': False,
                    'error': f'推理失败: {response.message}'
                }
                
        except Exception as e:
            logger.error(f"ReAct推理异常: {str(e)}")
            return {
                'success': False,
                'error': f'推理异常: {str(e)}'
            }
    
    def _build_react_system_prompt(self, tools_info: List[Dict[str, Any]]) -> str:
        """构建ReAct系统提示词"""
        tools_desc = "\n".join([
            f"- 工具名: {t['name']}\n  描述: {t['description']}\n  参数: {json.dumps(t.get('parameters',{}), ensure_ascii=False)}"
            for t in tools_info
        ])
        
        return f"""你是一个智能旅游规划Agent，擅长通过思考和调用工具来回答用户问题。

可用工具:
{tools_desc}

推理规则:
1. 先思考用户需求，判断是否需要调用工具
2. 如果需要工具，明确选择哪个工具并构造正确参数
3. 如果不需要工具，直接给出最终回答
4. 每次只调用一个工具
5. 参数必须是有效的JSON格式

回复格式严格遵守:
Thought: <你的思考分析>
Action: <工具名> | <参数JSON> 或 final_answer
Observation: <工具返回结果> 或 无

【重要】当 Action 是 final_answer 时：
- Observation 必须包含你准备回复给用户的完整内容
- 不要只写"无"，要写出你打算说的完整回答
- 这是用户会看到的最终回复，所以要友好、完整、有帮助

示例1 - 需要调用工具:
Thought: 用户想知道西安的天气情况，需要调用天气查询工具
Action: weather_query | {{"city": "西安", "days": 3}}
Observation: {{"success": true, "weather": {{"温度": "15-22°C", "天气": "多云"}}}}

示例2 - 不需要工具（直接给出回答）:
Thought: 用户询问当前行程中包含的非遗项目，这是一个关于当前规划的问题，可以直接回答
Action: final_answer
Observation: 根据您当前的旅游规划，您选择了以下非遗项目：
1. 咸阳 - 马嵬驿民俗文化体验园
2. 宝鸡 - 凤翔剪纸艺术

现在开始处理用户问题："""
    
    def _parse_react_response(self, content: str) -> Dict[str, str]:
        """解析ReAct响应"""
        result = {
            'thought': '',
            'action': '',
            'observation': ''
        }
        
        try:
            # 提取Thought
            thought_match = re.search(r'Thought:\s*(.+?)(?=\nAction:|$)', content, re.DOTALL)
            if thought_match:
                result['thought'] = thought_match.group(1).strip()
            
            # 提取Action
            action_match = re.search(r'Action:\s*(.+?)(?=\nObservation:|$)', content, re.DOTALL)
            if action_match:
                result['action'] = action_match.group(1).strip()
            
            # 提取Observation
            obs_match = re.search(r'Observation:\s*(.+?)(?=$)', content, re.DOTALL)
            if obs_match:
                result['observation'] = obs_match.group(1).strip()
                
        except Exception as e:
            logger.warning(f"解析ReAct响应失败: {str(e)}")
        
        return result
    
    async def 生成最终答案(self,
                          thought: str,
                          observation: Dict[str, Any],
                          context: str = "") -> Dict[str, Any]:
        """
        根据观察结果生成最终答案
        
        Args:
            thought: 之前的思考
            observation: 工具调用结果
            context: 上下文信息
            
        Returns:
            最终回答
        """
        try:
            observation_text = json.dumps(observation, ensure_ascii=False, indent=2)
            
            prompt = f"""
根据以下信息生成最终回答：

思考过程:
{thought}

工具返回结果:
{observation_text}

上下文:
{context}

请基于工具返回的结果，用友好的语气回答用户。如果结果中有数据，提供具体信息。

回答："""
            
            messages = [
                {
                    'role': 'system',
                    'content': '你是一个专业的旅游规划助手，根据工具返回的信息生成准确、友好的回答。'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            response = Generation.call(
                model=self.model_config['model'],
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                top_p=self.model_config.get('top_p', 0.95),
                result_format='message'
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                return {'success': True, 'answer': content}
            else:
                return {'success': False, 'error': response.message}
                
        except Exception as e:
            logger.error(f"生成最终答案失败: {str(e)}")
            return {'success': False, 'error': str(e)}

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