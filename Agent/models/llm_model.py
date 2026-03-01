# -*- coding: utf-8 -*-
"""
LLM 模型调用模块
实现与 LLM API 的集成，提供智能对话和分析能力
支持多厂商切换（DashScope/OpenAI/DeepSeek/GLM 等）
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from Agent.config import config


class LLMModel:
    """
    LLM 模型调用类
    封装 LLM API 调用逻辑，支持多厂商
    """
    
    def __init__(self):
        """
        初始化 LLM 模型
        """
        llm_config = config.get_llm_config()
        
        self.llm = ChatOpenAI(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            model=llm_config.model,
            temperature=llm_config.temperature,
            max_tokens=max(llm_config.max_tokens, 4500),
        )
        
        self.model_name = llm_config.model
        logger.info(f"LLM 模型初始化完成，使用模型: {self.model_name}")
    
    async def _call_model(self, prompt: str) -> Dict[str, Any]:
        """
        调用 LLM 模型 - 核心基础方法
        """
        try:
            logger.debug(f"调用模型，提示词长度: {len(prompt)}")
            
            messages = [
                SystemMessage(content='你是一个专业的旅游规划助手，专门为用户制定陕西非物质文化遗产相关的旅游计划。'),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            content = response.content
            logger.debug(f"模型响应成功，内容长度: {len(content)}")
            return {
                'success': True,
                'content': content
            }
                
        except Exception as e:
            logger.error(f"模型调用异常: {str(e)}")
            return {
                'success': False,
                'error': f'调用异常: {str(e)}'
            }

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

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """尝试解析JSON响应"""
        try:
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
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

    async def react_inference(self, 
                       user_input: str,
                       tools_info: List[Dict[str, Any]],
                       conversation_history: List[Dict[str, str]] = None,
                       plan_summary: str = None,
                       max_iterations: int = 5) -> Dict[str, Any]:
        """
        执行 ReAct 推理循环
        """
        try:
            system_prompt = self._build_react_system_prompt(tools_info)
            
            history_text = ""
            if conversation_history:
                history_text = "\n".join([
                    f"{msg['role']}: {msg['content'][:200]}"
                    for msg in conversation_history[-5:]
                ])
            
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
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            content = response.content
            
            parsed = self._parse_react_response(content)
            
            logger.info(f"ReAct推理完成: thought={parsed.get('thought','')[:50]}...")
            
            if parsed.get('action', '').strip() == 'final_answer':
                parsed['final_answer'] = parsed.get('observation', parsed.get('thought', ''))
            
            return {
                'success': True,
                **parsed
            }
                
        except Exception as e:
            logger.error(f"ReAct推理异常: {str(e)}")
            return {
                'success': False,
                'error': f'推理异常: {str(e)}'
            }
    
    def _build_react_system_prompt(self, tools_info: List[Dict[str, Any]]) -> str:
        """构建 ReAct 系统提示词"""
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
        """解析 ReAct 响应"""
        result = {
            'thought': '',
            'action': '',
            'observation': ''
        }
        
        try:
            thought_match = re.search(r'Thought:\s*(.+?)(?=\nAction:|$)', content, re.DOTALL)
            if thought_match:
                result['thought'] = thought_match.group(1).strip()
            
            action_match = re.search(r'Action:\s*(.+?)(?=\nObservation:|$)', content, re.DOTALL)
            if action_match:
                result['action'] = action_match.group(1).strip()
            
            obs_match = re.search(r'Observation:\s*(.+?)(?=$)', content, re.DOTALL)
            if obs_match:
                result['observation'] = obs_match.group(1).strip()
                
        except Exception as e:
            logger.warning(f"解析ReAct响应失败: {str(e)}")
        
        return result
    
    async def generate_final_answer(self,
                          thought: str,
                          observation: Dict[str, Any],
                          context: str = "") -> Dict[str, Any]:
        """
        根据观察结果生成最终答案
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
                SystemMessage(content='你是一个专业的旅游规划助手，根据工具返回的信息生成准确、友好的回答。'),
                HumanMessage(content=prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            content = response.content
            return {'success': True, 'answer': content}
                
        except Exception as e:
            logger.error(f"生成最终答案失败: {str(e)}")
            return {'success': False, 'error': str(e)}

_model_instance = None

def get_llm_model() -> LLMModel:
    """
    获取 LLM 模型实例（单例模式）
    """
    global _model_instance
    if _model_instance is None:
        _model_instance = LLMModel()
    return _model_instance
