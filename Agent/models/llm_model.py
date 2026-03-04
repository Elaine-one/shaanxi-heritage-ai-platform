# -*- coding: utf-8 -*-
"""
LLM 模型调用模块
基于 LangChain 1.0 实现，支持多厂商切换
"""

from typing import Dict, Any, AsyncIterator
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from Agent.config import config


class LLMModel:
    """
    LLM 模型调用类
    基于 LangChain 1.0 ChatOpenAI 实现
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
        调用 LLM 模型
        
        Args:
            prompt: 提示词
        
        Returns:
            Dict[str, Any]: 包含 success 和 content/error 的字典
        """
        try:
            from datetime import datetime
            current_date = datetime.now().strftime('%Y年%m月%d日')
            
            logger.debug(f"调用模型，提示词长度: {len(prompt)}")
            
            messages = [
                SystemMessage(content=f'你是一个专业的旅游规划助手，专门为用户制定陕西非物质文化遗产相关的旅游计划。当前日期是：{current_date}。在生成行程时，请使用当前日期作为出发日期，不要使用过去的日期。'),
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

    async def _call_model_stream(self, prompt: str) -> AsyncIterator[str]:
        """
        流式调用 LLM 模型
        
        Args:
            prompt: 提示词
        
        Yields:
            str: 流式输出的文本块
        """
        try:
            from datetime import datetime
            current_date = datetime.now().strftime('%Y年%m月%d日')
            
            logger.debug(f"流式调用模型，提示词长度: {len(prompt)}")
            
            messages = [
                SystemMessage(content=f'你是一个专业的旅游规划助手，专门为用户制定陕西非物质文化遗产相关的旅游计划。当前日期是：{current_date}。在生成行程时，请使用当前日期作为出发日期，不要使用过去的日期。'),
                HumanMessage(content=prompt)
            ]
            
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            logger.error(f"流式模型调用异常: {str(e)}")
            yield f"Error: {str(e)}"


_model_instance = None


def get_llm_model() -> LLMModel:
    """
    获取 LLM 模型实例（单例模式）
    """
    global _model_instance
    if _model_instance is None:
        _model_instance = LLMModel()
    return _model_instance
