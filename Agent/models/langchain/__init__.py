# -*- coding: utf-8 -*-
"""
LangChain Models 模块
包含 LangChain 兼容的模型包装器
"""

from .llm import DashScopeLLM, get_dashscope_llm

__all__ = [
    'DashScopeLLM',
    'get_dashscope_llm'
]
