# -*- coding: utf-8 -*-
"""
ReAct Agent 实现
使用 LangChain 框架实现 ReAct 推理代理
"""

from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_react_agent
from loguru import logger

from Agent.models.langchain import get_dashscope_llm
from Agent.tools import get_langchain_tools
from Agent.prompts import REACT_AGENT_PROMPT


class LangChainReActAgent:
    """LangChain ReAct Agent 实现"""

    def __init__(self, ali_model=None):
        """
        初始化 LangChain ReAct Agent

        Args:
            ali_model: 阿里云模型实例（可选）
        """
        self.llm = get_dashscope_llm(ali_model)
        self.tools = get_langchain_tools()
        self.agent_executor = self._create_agent_executor()
        logger.info(f"LangChain ReAct Agent 初始化完成，工具数量: {len(self.tools)}")

    def _create_agent_executor(self) -> AgentExecutor:
        """创建 AgentExecutor"""
        from datetime import datetime
        
        # 获取当前日期
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=REACT_AGENT_PROMPT.partial(current_date=current_date)
        )

        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            early_stopping_method="force"
        )

        return agent_executor

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
            logger.info(f"LangChain Agent: 开始处理用户输入: {user_input[:50]}...")

            # 构建完整的输入，包含对话历史
            full_input = user_input
            
            if conversation_history:
                # 添加对话历史上下文
                history_context = self._build_conversation_context(conversation_history)
                if history_context:
                    full_input = f"{history_context}\n\n当前用户问题: {user_input}"
                    logger.info(f"包含对话历史上下文，历史消息数: {len(conversation_history)}")

            if plan_summary:
                full_input = f"{plan_summary}\n\n{full_input}"

            result = await self.agent_executor.ainvoke({"input": full_input})

            logger.info(f"LangChain Agent: 处理完成，输出长度: {len(result.get('output', ''))}")

            return {
                'success': True,
                'answer': result.get('output', ''),
                'intermediate_steps': result.get('intermediate_steps', [])
            }

        except Exception as e:
            logger.error(f"LangChain Agent 执行失败: {str(e)}")
            logger.exception("完整错误堆栈:")
            return {
                'success': False,
                'error': str(e),
                'answer': f"抱歉，处理您的请求时遇到了问题: {str(e)}"
            }

    def _build_conversation_context(self, conversation_history: List[Dict[str, Any]]) -> str:
        """
        构建对话历史上下文
        
        Args:
            conversation_history: 对话历史列表
        
        Returns:
            str: 对话历史上下文字符串
        """
        if not conversation_history:
            return ""
        
        context_parts = ["【对话历史】"]
        
        # 只取最近5条历史，避免上下文过长
        recent_history = conversation_history[-5:]
        
        for msg in recent_history:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if role == 'user':
                context_parts.append(f"用户: {content}")
            elif role == 'assistant':
                context_parts.append(f"助手: {content}")
        
        return "\n".join(context_parts)


# 全局 Agent 实例
_agent_instance = None


def get_react_agent(ali_model=None) -> LangChainReActAgent:
    """获取 LangChain ReAct Agent 单例"""
    global _agent_instance

    if _agent_instance is None:
        _agent_instance = LangChainReActAgent(ali_model)

    return _agent_instance
