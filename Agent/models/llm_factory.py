# -*- coding: utf-8 -*-
"""
通用 LLM 工厂类
支持多厂商 LLM 切换
"""

from typing import Optional
from loguru import logger

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from Agent.config import config


class LLMFactory:
    """LLM 工厂类，创建统一的 LLM 实例"""
    
    _instance: Optional[BaseChatModel] = None
    _provider: Optional[str] = None
    
    @classmethod
    def create_llm(cls) -> BaseChatModel:
        """创建 LLM 实例"""
        llm_config = config.get_llm_config()
        
        if cls._instance is not None and cls._provider == llm_config.provider:
            return cls._instance
        
        logger.info(f"创建 LLM 实例: provider={llm_config.provider}, model={llm_config.model}")
        
        cls._instance = ChatOpenAI(
            api_key=llm_config.api_key,
            base_url=llm_config.base_url,
            model=llm_config.model,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens,
        )
        cls._provider = llm_config.provider
        
        logger.info(f"LLM 实例创建成功: {llm_config.provider} / {llm_config.model}")
        
        return cls._instance
    
    @classmethod
    def get_llm(cls) -> BaseChatModel:
        """获取 LLM 单例"""
        if cls._instance is None:
            return cls.create_llm()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """重置 LLM 实例（用于切换配置后重新创建）"""
        cls._instance = None
        cls._provider = None


def get_llm() -> BaseChatModel:
    """获取 LLM 实例"""
    return LLMFactory.get_llm()


def create_llm() -> BaseChatModel:
    """创建新的 LLM 实例"""
    return LLMFactory.create_llm()
