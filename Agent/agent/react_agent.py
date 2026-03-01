# -*- coding: utf-8 -*-
"""
ReAct Agent 实现
使用自定义 ReAct 循环，支持多厂商 LLM 切换
"""

import json
import re
from typing import Dict, Any, List, Optional
from loguru import logger

from Agent.models.llm_factory import get_llm
from Agent.tools.base import get_tool_registry
from Agent.prompts import REACT_SYSTEM_PROMPT


class LangChainReActAgent:
    """自定义 ReAct Agent，支持多厂商 LLM"""

    def __init__(self):
        """
        初始化 ReAct Agent
        自动从配置加载 LLM（支持多厂商切换）
        """
        self.llm = get_llm()
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
        tool_desc = self._build_tool_descriptions()
        tool_names = ", ".join(self.tools)
        
        prompt = f"""{REACT_SYSTEM_PROMPT}

工具详情:
{tool_desc}

可用工具列表: [{tool_names}]

=== 输出格式（严格遵守）===

Thought: 分析问题，决定是否需要调用工具
Action: 工具名称（如需调用）
Action Input: {{"参数名": "参数值"}}

或者直接回答:

Thought: 分析问题，已知信息足够
Final Answer: 你的完整回答

=== 规则 ===

1. 简单问题（打招呼、常识问题）直接 Final Answer
2. 需要查询数据时，调用工具
3. 每次只调用一个工具
4. 收到 Observation 后，必须给出 Final Answer 或调用下一个工具
5. 不要重复调用同一工具
6. 【重要】Final Answer 必须包含完整的回答内容，不要把详细信息放在 Thought 中

{context}

=== 开始 ===

Question: {user_input}
Thought: """
        return prompt

    async def run(self, user_input: str, plan_summary: str = None, conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        运行 Agent
        
        Args:
            user_input: 用户输入
            plan_summary: 规划摘要（可选）
            conversation_history: 对话历史（可选）
        
        Returns:
            Dict包含: success(是否成功), answer(最终答案), intermediate_steps(中间步骤)
        """
        try:
            logger.info(f"ReAct Agent: 开始处理用户输入: {user_input[:50]}...")

            context = ""
            
            if plan_summary:
                context = f"""【当前用户规划信息 - 请务必参考】
{plan_summary}

"""
            
            if conversation_history:
                history_context = await self._build_conversation_context(conversation_history)
                if history_context:
                    context += f"【对话历史】\n{history_context}\n"
                    logger.info(f"包含对话历史上下文，历史消息数: {len(conversation_history)}")

            intermediate_steps = []
            current_input = user_input
            iteration = 0

            while iteration < self.max_iterations:
                iteration += 1
                logger.debug(f"ReAct 迭代 {iteration}/{self.max_iterations}")

                prompt = self._build_react_prompt(current_input, context)
                
                response = await self.llm.ainvoke(prompt)
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                parsed = self._parse_react_response(response_text)
                
                if parsed.get('final_answer'):
                    logger.info(f"ReAct Agent: 处理完成，输出长度: {len(parsed['final_answer'])}")
                    return {
                        'success': True,
                        'answer': parsed['final_answer'],
                        'intermediate_steps': intermediate_steps
                    }
                
                if parsed.get('action') and parsed.get('action_input'):
                    tool_name = parsed['action']
                    tool_input = parsed['action_input']
                    
                    if tool_name not in self.tools:
                        observation = f"错误: 未知工具 '{tool_name}'，可用工具: {list(self.tools)}"
                    else:
                        try:
                            logger.info(f"调用工具: {tool_name}, 参数: {tool_input}")
                            tool = self.tool_registry.get_tool(tool_name)
                            observation = await tool.execute(**tool_input)
                            observation = json.dumps(observation, ensure_ascii=False)
                            logger.info(f"工具返回: {observation[:200]}...")
                        except Exception as e:
                            observation = f"工具执行错误: {str(e)}"
                    
                    intermediate_steps.append({
                        'thought': parsed.get('thought', ''),
                        'action': tool_name,
                        'action_input': tool_input,
                        'observation': observation
                    })
                    
                    context += f"\nThought: {parsed.get('thought', '')}\nAction: {tool_name}\nAction Input: {json.dumps(tool_input, ensure_ascii=False)}\nObservation: {observation}\n"
                    current_input = "继续处理，根据观察结果给出回答或调用下一个工具。"
                else:
                    final_answer = parsed.get('thought', response_text)
                    logger.info(f"ReAct Agent: 处理完成（无工具调用），输出长度: {len(final_answer)}")
                    return {
                        'success': True,
                        'answer': final_answer,
                        'intermediate_steps': intermediate_steps
                    }

            return {
                'success': False,
                'error': '达到最大迭代次数',
                'answer': '抱歉，处理您的请求时超出了最大步骤限制，请简化您的问题后重试。'
            }

        except Exception as e:
            logger.error(f"ReAct Agent 执行失败: {str(e)}")
            logger.exception("完整错误堆栈:")
            
            error_msg = str(e)
            return {
                'success': False,
                'error': error_msg,
                'answer': f"抱歉，处理您的请求时遇到了问题: {error_msg}"
            }

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

    async def _build_conversation_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        构建对话历史上下文（基于 LLM 智能摘要）
        
        Args:
            conversation_history: 对话历史列表
        
        Returns:
            str: 对话历史摘要上下文字符串
        """
        if not conversation_history:
            return ""
        
        try:
            conversation_text = self._format_conversation_to_text(conversation_history)
            
            logger.info(f"开始对 {len(conversation_history)} 条对话历史进行智能摘要...")
            
            from Agent.prompts import CONVERSATION_SUMMARY_PROMPT
            summary_prompt = CONVERSATION_SUMMARY_PROMPT.format(
                conversation_history=conversation_text
            )
            
            summary_result = await self.llm.ainvoke(summary_prompt)
            summary = summary_result.content if hasattr(summary_result, 'content') else str(summary_result)
            
            logger.info(f"对话历史摘要生成完成，摘要长度: {len(summary)} 字符")
            
            return f"【对话历史摘要】\n{summary}"
            
        except Exception as e:
            logger.error(f"对话历史摘要生成失败，降级为简单截取: {str(e)}")
            return self._build_conversation_context_fallback(conversation_history)
    
    def _format_conversation_to_text(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        将对话历史转换为文本格式
        
        Args:
            conversation_history: 对话历史列表
        
        Returns:
            str: 格式化的对话文本
        """
        lines = []
        for idx, msg in enumerate(conversation_history, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if role == 'user':
                lines.append(f"{idx}. 用户: {content}")
            elif role == 'assistant':
                lines.append(f"{idx}. 助手: {content}")
        
        return "\n".join(lines)
    
    def _build_conversation_context_fallback(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        降级方案：构建对话历史上下文（简单截取）
        
        Args:
            conversation_history: 对话历史列表
        
        Returns:
            str: 对话历史上下文字符串
        """
        context_parts = ["【对话历史】"]
        
        recent_history = conversation_history[-5:]
        
        for msg in recent_history:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if role == 'user':
                context_parts.append(f"用户: {content}")
            elif role == 'assistant':
                context_parts.append(f"助手: {content}")
        
        return "\n".join(context_parts)


_agent_instance = None


def get_react_agent() -> LangChainReActAgent:
    """获取 ReAct Agent 单例"""
    global _agent_instance

    if _agent_instance is None:
        _agent_instance = LangChainReActAgent()

    return _agent_instance
