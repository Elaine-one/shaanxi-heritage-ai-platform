# -*- coding: utf-8 -*-
"""
ReAct Agent 实现
使用自定义 ReAct 循环，支持多厂商 LLM 切换
"""

import asyncio
import json
import re
from typing import Dict, Any, List, Optional
from loguru import logger

from Agent.models.llm_factory import get_llm
from Agent.models.llm_model import LLMModel
from Agent.tools.base import get_tool_registry
from Agent.prompts import REACT_SYSTEM_PROMPT, get_react_prompt


class LangChainReActAgent:
    """自定义 ReAct Agent，支持多厂商 LLM"""

    def __init__(self):
        """
        初始化 ReAct Agent
        自动从配置加载 LLM（支持多厂商切换）
        """
        self.llm = get_llm()
        self.llm_model = LLMModel()
        self.tool_registry = get_tool_registry()
        self.tools = self.tool_registry.get_tool_names()
        self.max_iterations = 10
        logger.info(f"ReAct Agent 初始化完成，工具数量: {len(self.tools)}")

    def _build_tool_descriptions(self) -> str:
        """构建工具描述"""
        descriptions = []
        for tool_name in self.tools:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                desc = f"- {tool_name}: {tool.description}"
                descriptions.append(desc)
        return "\n".join(descriptions)

    def _build_react_prompt(self, user_input: str, context: str = "") -> str:
        """构建 ReAct 提示词"""
        from datetime import datetime
        current_date = datetime.now().strftime('%Y年%m月%d日')
        
        tool_desc = self._build_tool_descriptions()
        tool_names = ", ".join(self.tools)
        
        system_prompt = REACT_SYSTEM_PROMPT.format(current_date=current_date)
        system_prompt = system_prompt.replace('{{', '{').replace('}}', '}')
        
        return get_react_prompt(
            system_prompt=system_prompt,
            tool_descriptions=tool_desc,
            tool_names=tool_names,
            context=context,
            question=user_input
        )

    def _parse_react_response(self, response: str) -> Dict[str, Any]:
        """解析 ReAct 响应"""
        result = {
            'thought': '',
            'action': '',
            'action_input': {},
            'final_answer': ''
        }
        
        try:
            if 'Final Answer:' in response:
                parts = response.split('Final Answer:', 1)
                if len(parts) > 1:
                    result['final_answer'] = parts[1].strip()
                return result
            
            thought_match = re.search(r'Thought:\s*(.+?)(?=\nAction:|$)', response, re.DOTALL)
            if thought_match:
                result['thought'] = thought_match.group(1).strip()
            
            action_match = re.search(r'Action:\s*(\w+)', response)
            if action_match:
                result['action'] = action_match.group(1).strip()
            
            action_input_match = re.search(r'Action Input:\s*(\{.+?\})', response, re.DOTALL)
            if action_input_match:
                try:
                    result['action_input'] = json.loads(action_input_match.group(1))
                except json.JSONDecodeError:
                    result['action_input'] = {}
                    
        except Exception as e:
            logger.warning(f"解析 ReAct 响应失败: {str(e)}")
        
        return result

    async def run_stream(self, user_input: str, plan_summary: str = None, conversation_history: List[Dict[str, Any]] = None):
        """流式运行 Agent，只输出 Final Answer 之后的内容"""
        try:
            logger.info(f"🚀 ReAct Agent 开始处理 | 输入: {user_input[:50]}...")
            
            if plan_summary:
                logger.info(f"📋 包含规划摘要")
            
            if conversation_history:
                logger.info(f"💬 包含对话历史: {len(conversation_history)} 条")

            context = ""
            
            if plan_summary:
                context = f"""【当前用户规划信息 - 请务必参考】
{plan_summary}

"""
            
            if conversation_history:
                history_context = self._build_conversation_context(conversation_history)
                if history_context:
                    context += f"{history_context}\n"

            intermediate_steps = []
            current_input = user_input
            iteration = 0

            while iteration < self.max_iterations:
                iteration += 1
                logger.info(f"🔄 迭代 {iteration}/{self.max_iterations}")

                prompt = self._build_react_prompt(current_input, context)
                
                # 流式调用 LLM，先收集完整响应
                buffer = ""
                
                async for chunk in self.llm_model._call_model_stream(prompt):
                    buffer += chunk
                
                # 解析响应
                parsed = self._parse_react_response(buffer)
                
                # 打印思维链
                if parsed.get('thought'):
                    logger.info(f"🧠 {parsed.get('thought', '')[:100]}...")
                
                # 检查是否有Final Answer
                if parsed.get('final_answer'):
                    logger.info(f"✅ 最终答案 | 长度: {len(parsed['final_answer'])}")
                    # 流式输出 Final Answer
                    final_answer = parsed['final_answer']
                    chunk_size = 20
                    for i in range(0, len(final_answer), chunk_size):
                        yield final_answer[i:i + chunk_size]
                        await asyncio.sleep(0.01)
                    return
                
                # 检查是否需要调用工具
                if parsed.get('action') and parsed.get('action_input'):
                    tool_name = parsed['action']
                    tool_input = parsed['action_input']
                    
                    # 打印工具调用信息
                    logger.info(f"🔧 调用工具: {tool_name} | 参数: {json.dumps(tool_input, ensure_ascii=False)}")
                    
                    if tool_name not in self.tools:
                        observation = f"错误: 未知工具 '{tool_name}'，可用工具: {list(self.tools)}"
                        logger.error(f"❌ {observation}")
                    else:
                        try:
                            tool = self.tool_registry.get_tool(tool_name)
                            observation = await tool.execute(**tool_input)
                            observation = json.dumps(observation, ensure_ascii=False)
                            logger.info(f"✅ 工具成功 | 返回: {observation[:150]}...")
                        except Exception as e:
                            observation = f"工具执行错误: {str(e)}"
                            logger.error(f"❌ {observation}")
                    
                    intermediate_steps.append({
                        'thought': parsed.get('thought', ''),
                        'action': tool_name,
                        'action_input': tool_input,
                        'observation': observation
                    })
                    
                    context += f"\nThought: {parsed.get('thought', '')}\nAction: {tool_name}\nAction Input: {json.dumps(tool_input, ensure_ascii=False)}\nObservation: {observation}\n"
                    current_input = "继续处理，根据观察结果给出回答或调用下一个工具。"
                    
                    # 继续循环，让LLM决定下一步是调用工具还是给出Final Answer
                    continue
                else:
                    final_answer = parsed.get('thought', buffer)
                    logger.info(f"✅ 直接回答 | 长度: {len(final_answer)}")
                    # 流式输出
                    chunk_size = 20
                    for i in range(0, len(final_answer), chunk_size):
                        yield final_answer[i:i + chunk_size]
                        await asyncio.sleep(0.01)
                    return

            logger.error(f"⚠️ 超出最大步骤限制 ({self.max_iterations})")
            yield "抱歉，处理您的请求时超出了最大步骤限制，请简化您的问题后重试。"

        except Exception as e:
            logger.error(f"❌ ReAct Agent 执行失败: {str(e)}")
            logger.exception("完整错误堆栈:")
            yield f"抱歉，处理您的请求时遇到了问题: {str(e)}"

    def _build_conversation_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """构建对话历史上下文"""
        if not conversation_history:
            return ""
        
        # 直接格式化对话历史，传递给LLM自己理解
        lines = ["【对话历史】"]
        
        # 限制历史数量，避免token超限
        recent_history = conversation_history[-10:]
        
        for msg in recent_history:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if role == 'user':
                lines.append(f"用户: {content}")
            elif role == 'assistant':
                lines.append(f"助手: {content}")
        
        return "\n".join(lines)


_agent_instance = None


def get_react_agent() -> LangChainReActAgent:
    """获取 ReAct Agent 单例"""
    global _agent_instance

    if _agent_instance is None:
        _agent_instance = LangChainReActAgent()

    return _agent_instance
