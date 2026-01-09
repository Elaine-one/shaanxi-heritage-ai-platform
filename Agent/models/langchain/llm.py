# -*- coding: utf-8 -*-
"""
DashScope LLM 模型包装器
将阿里云 DashScope 模型包装为 LangChain 兼容的聊天模型
"""

from typing import Dict, Any, List, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from loguru import logger

from Agent.models.dashscope import AliCloudModel


class DashScopeLLM(BaseChatModel):
    """DashScope LLM 包装器，兼容 LangChain"""
    
    ali_model: AliCloudModel
    
    def __init__(self, ali_model: AliCloudModel):
        super().__init__(ali_model=ali_model)

    @property
    def _llm_type(self) -> str:
        return "dashscope"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """生成响应"""
        import asyncio
        
        # 将消息转换为字符串
        prompt = self._messages_to_string(messages)
        
        # 调用阿里云模型
        response = asyncio.run(self.ali_model._call_model(prompt))
        
        if response['success']:
            content = response['content']
        else:
            content = f"Error: {response.get('error', 'Unknown error')}"
        
        # 创建 ChatGeneration
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
            else:
                result.append(msg.content)
        return "\n".join(result)


# 全局 LLM 实例
_llm_instance = None


def get_dashscope_llm(ali_model: AliCloudModel = None) -> DashScopeLLM:
    """获取 DashScope LLM 单例"""
    global _llm_instance

    if _llm_instance is None:
        if ali_model is None:
            from Agent.models.dashscope import get_ali_model
            ali_model = get_ali_model()
        _llm_instance = DashScopeLLM(ali_model)
        logger.info("DashScope LLM 初始化完成")

    return _llm_instance
