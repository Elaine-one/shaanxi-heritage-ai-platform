# -*- coding: utf-8 -*-
"""
Models 模块
包含模型相关代码，包括 DashScope LLM 和 LangChain 模型包装器
"""

from .dashscope import AliCloudModel, get_ali_model
from .langchain.llm import DashScopeLLM, get_dashscope_llm

__all__ = [
    # DashScope models
    'AliCloudModel',
    'get_ali_model',
    # LangChain models
    'DashScopeLLM',
    'get_dashscope_llm'
]
