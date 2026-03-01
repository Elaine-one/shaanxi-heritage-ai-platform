# -*- coding: utf-8 -*-
"""
LLM 模型包装器
将 LLM 模型包装为 LangChain 聊天模型
支持多厂商切换
"""

from typing import Dict, Any, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from loguru import logger

from Agent.models.llm_model import LLMModel


class DashScopeLLM(BaseChatModel):
    """LLM 包装器，支持多厂商 LLM"""
    
    llm_model: LLMModel
    
    def __init__(self, llm_model: LLMModel):
        super().__init__(llm_model=llm_model)

    @property
    def _llm_type(self) -> str:
        return "dashscope"

    @property
    def model_name(self) -> str:
        return "dashscope-qwen"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """同步生成响应"""
        import asyncio
        
        prompt = self._messages_to_string(messages)
        
        response = asyncio.run(self.llm_model._call_model(prompt))
        
        if response['success']:
            content = response['content']
        else:
            content = f"Error: {response.get('error', 'Unknown error')}"
        
        generation = ChatGeneration(message=AIMessage(content=content))
        
        return ChatResult(generations=[generation])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """异步生成响应"""
        prompt = self._messages_to_string(messages)
        
        response = await self.llm_model._call_model(prompt)
        
        if response['success']:
            content = response['content']
        else:
            content = f"Error: {response.get('error', 'Unknown error')}"
        
        generation = ChatGeneration(message=AIMessage(content=content))
        
        return ChatResult(generations=[generation])

    def _messages_to_string(self, messages: List[BaseMessage]) -> str:
        """将消息列表转换为字符串"""
        result = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                result.append(f"用户: {msg.content}")
            elif isinstance(msg, AIMessage):
                result.append(f"助手: {msg.content}")
            elif isinstance(msg, SystemMessage):
                result.append(f"系统: {msg.content}")
            else:
                result.append(msg.content)
        return "\n".join(result)

    def bind_tools(self, tools: List[Any], **kwargs: Any) -> "DashScopeLLM":
        """绑定工具"""
        return self

    def with_structured_output(self, schema: Any, **kwargs: Any) -> "DashScopeLLM":
        """结构化输出"""
        return self


_llm_instance = None


def get_dashscope_llm(llm_model: LLMModel = None) -> DashScopeLLM:
    """获取 LLM 单例"""
    global _llm_instance

    if _llm_instance is None:
        if llm_model is None:
            from Agent.models.llm_model import get_llm_model
            llm_model = get_llm_model()
        _llm_instance = DashScopeLLM(llm_model)
        logger.info("LLM 初始化完成")

    return _llm_instance
