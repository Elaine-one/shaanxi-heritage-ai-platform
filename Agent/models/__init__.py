# -*- coding: utf-8 -*-
"""
Models 模块
包含模型相关代码，支持多厂商 LLM 切换
基于 LangChain 1.0 实现
"""

from .llm_factory import LLMFactory, get_llm, create_llm
from .llm_model import LLMModel, get_llm_model

__all__ = [
    'LLMFactory',
    'get_llm',
    'create_llm',
    'LLMModel',
    'get_llm_model'
]
