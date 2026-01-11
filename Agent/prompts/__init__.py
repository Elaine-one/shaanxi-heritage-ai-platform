# -*- coding: utf-8 -*-
"""
Prompts 模块
包含提示模板，包括 ReAct Agent 提示模板和对话摘要提示模板
"""

from .react import REACT_AGENT_PROMPT
from .conversation_summary import CONVERSATION_SUMMARY_PROMPT

__all__ = [
    'REACT_AGENT_PROMPT',
    'CONVERSATION_SUMMARY_PROMPT'
]
