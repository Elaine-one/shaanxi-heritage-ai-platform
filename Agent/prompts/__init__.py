# -*- coding: utf-8 -*-
"""
Agent 提示模板模块
"""

from .react import REACT_SYSTEM_PROMPT
from .templates import (
    REACT_PROMPT_TEMPLATE,
    AI_SUGGESTIONS_PROMPT,
    CONVERSATION_SUMMARY_PROMPT,
    KNOWLEDGE_QA_PROMPT,
    PLAN_EDIT_PROMPT,
    get_react_prompt,
    get_ai_suggestions_prompt,
    get_conversation_summary_prompt,
    get_knowledge_qa_prompt,
    get_plan_edit_prompt
)
from .langchain_prompt import (
    SYSTEM_PROMPT as LANGCHAIN_SYSTEM_PROMPT,
    get_system_prompt,
    format_plan_context,
)

__all__ = [
    'REACT_SYSTEM_PROMPT',
    'REACT_PROMPT_TEMPLATE',
    'AI_SUGGESTIONS_PROMPT',
    'CONVERSATION_SUMMARY_PROMPT',
    'KNOWLEDGE_QA_PROMPT',
    'PLAN_EDIT_PROMPT',
    'get_react_prompt',
    'get_ai_suggestions_prompt',
    'get_conversation_summary_prompt',
    'get_knowledge_qa_prompt',
    'get_plan_edit_prompt',
    'LANGCHAIN_SYSTEM_PROMPT',
    'get_system_prompt',
    'format_plan_context',
]
