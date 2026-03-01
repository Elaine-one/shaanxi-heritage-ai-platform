# -*- coding: utf-8 -*-
"""
Models 模块
包含模型相关代码，支持多厂商 LLM 切换
"""

from .llm_factory import LLMFactory, get_llm, create_llm
from .llm_model import LLMModel, get_llm_model
from .langchain.llm import DashScopeLLM, get_dashscope_llm

__all__ = [
    'LLMFactory',
    'get_llm',
    'create_llm',
    'LLMModel',
    'get_llm_model',
    'DashScopeLLM',
    'get_dashscope_llm'
]
