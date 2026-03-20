# -*- coding: utf-8 -*-
"""
LLM 模型调用模块
基于 LangChain 1.0 实现，支持多厂商切换
实现并发控制，适配智谱 API 并发限制
"""

from typing import Dict, Any, AsyncIterator
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage
from Agent.config import config
import asyncio


LLM_SEMAPHORE = asyncio.Semaphore(4)


class LLMModel:
    """
    LLM 模型调用类
    基于 LangChain 1.0 ChatOpenAI 实现
    实现并发控制，限制同时请求数
    """

    PROVIDER_MODEL_PATTERNS = {
        'dashscope': ['qwen', 'qwq', 'qvl'],
        'zhipu': ['glm', 'chatglm'],
        'deepseek': ['deepseek'],
        'openai': ['gpt'],
        'moonshot': ['moonshot'],
        'ollama': ['llama', 'mistral', 'gemma', 'phi'],
    }

    def __init__(self):
        """
        初始化 LLM 模型
        """
        llm_config = config.get_llm_config()

        self._check_provider_model_match(llm_config.provider, llm_config.model)

        self.llm = ChatOpenAI(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            model=llm_config.model,
            temperature=llm_config.temperature,
            max_tokens=max(llm_config.max_tokens, 4096) if llm_config.max_tokens > 0 else 4096,
            request_timeout=600,
            max_retries=2,
        )

        self.model_name = llm_config.model

        self._validate_api_key()

        logger.info(f"LLM 模型初始化完成，使用模型: {self.model_name}")

    def _check_provider_model_match(self, provider: str, model: str) -> None:
        """
        检查 Provider 和 Model 是否匹配

        Args:
            provider: LLM 提供商
            model: 模型名称

        Raises:
            ValueError: 当 Provider 和 Model 不匹配时
        """
        if provider not in self.PROVIDER_MODEL_PATTERNS:
            return

        patterns = self.PROVIDER_MODEL_PATTERNS[provider]
        model_lower = model.lower()

        for pattern in patterns:
            if pattern in model_lower:
                return

        provider_names = {
            'dashscope': '阿里云百炼',
            'zhipu': '智谱AI',
            'deepseek': '深度求索',
            'openai': 'OpenAI',
            'moonshot': '月之暗面',
            'ollama': 'Ollama',
        }

        provider_cn = provider_names.get(provider, provider)
        suggested_models = ', '.join([f"{pattern}-*" for pattern in patterns])

        raise ValueError(
            f"Provider 与 Model 不匹配: {provider_cn} ({provider}) 不支持模型 {model}，"
            f"请使用 {suggested_models} 系列模型"
        )

    def _validate_api_key(self) -> None:
        """
        验证 API Key 有效性

        Raises:
            ValueError: 当 API Key 验证失败时
        """
        try:
            messages = [HumanMessage(content="Hi")]
            response = asyncio.run(self.llm.ainvoke(messages, timeout=15))
            if response.content:
                return
        except Exception as e:
            error_msg = str(e)
            if '401' in error_msg or 'invalid_api_key' in error_msg:
                raise ValueError("API Key 无效")
            elif '403' in error_msg or 'insufficient_quota' in error_msg:
                raise ValueError("API 配额不足")
            elif 'model_not_found' in error_msg or '400' in error_msg:
                raise ValueError(f"模型 {self.model_name} 不存在")
            elif 'timeout' in error_msg.lower():
                raise ValueError("连接超时，请检查网络或稍后重试")
            elif 'connection' in error_msg.lower():
                raise ValueError("网络连接失败")
            else:
                raise ValueError("API Key 验证失败")
    
    async def _call_model(self, prompt: str) -> Dict[str, Any]:
        """
        调用 LLM 模型（带并发控制）
        
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
            
            async with LLM_SEMAPHORE:
                logger.debug("获取到信号量，开始调用 LLM")
                response = await self.llm.ainvoke(messages)
            
            content = response.content
            logger.debug(f"模型响应成功，内容长度: {len(content)}")
            return {
                'success': True,
                'content': content
            }
                
        except asyncio.TimeoutError:
            logger.error("模型调用超时")
            return {
                'success': False,
                'error': '模型调用超时，请稍后重试'
            }
        except Exception as e:
            error_msg = str(e) if str(e) else type(e).__name__
            logger.error(f"模型调用异常: {error_msg}")
            return {
                'success': False,
                'error': f'调用异常: {error_msg}'
            }

    async def _call_model_stream(self, prompt: str) -> AsyncIterator[str]:
        """
        流式调用 LLM 模型（带并发控制）
        
        Args:
            prompt: 提示词（已包含完整上下文）
        
        Yields:
            str: 流式输出的文本块
        """
        async with LLM_SEMAPHORE:
            try:
                logger.debug(f"流式调用模型，提示词长度: {len(prompt)}")
                
                messages = [HumanMessage(content=prompt)]
                
                chunk_count = 0
                async for chunk in self.llm.astream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        chunk_count += 1
                        yield chunk.content
                
                logger.debug(f"流式输出完成，共 {chunk_count} 个块")
                        
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
