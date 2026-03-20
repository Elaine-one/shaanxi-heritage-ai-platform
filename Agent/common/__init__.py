# -*- coding: utf-8 -*-
"""
通用模块
提供统一的结果类型、异常定义和接口抽象
"""

from .result import Result, Success, Failure
from .exceptions import (
    AgentException,
    ToolExecutionError,
    LLMError,
    SessionNotFoundError,
    ConfigurationError
)

__all__ = [
    'Result',
    'Success',
    'Failure',
    'AgentException',
    'ToolExecutionError',
    'LLMError',
    'SessionNotFoundError',
    'ConfigurationError'
]
