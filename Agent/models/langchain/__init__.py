# -*- coding: utf-8 -*-
"""
LangChain Models 模块
包含 LangChain 模型包装器，支持多厂商切换
"""

from .llm import DashScopeLLM, get_dashscope_llm

__all__ = [
    'DashScopeLLM',
    'get_dashscope_llm'
]
