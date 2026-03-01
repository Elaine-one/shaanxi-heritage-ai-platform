# -*- coding: utf-8 -*-
"""
Prompts 模块
包含提示模板
"""

from .react import REACT_SYSTEM_PROMPT
from .conversation_summary import CONVERSATION_SUMMARY_PROMPT, format_conversation_summary_prompt

__all__ = [
    'REACT_SYSTEM_PROMPT',
    'CONVERSATION_SUMMARY_PROMPT',
    'format_conversation_summary_prompt'
]
