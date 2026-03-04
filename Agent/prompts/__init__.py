# -*- coding: utf-8 -*-
"""
Agent 提示模板模块
使用 LangChain 1.0 PromptTemplate 统一管理
"""

from .react import REACT_SYSTEM_PROMPT
from .templates import (
    REACT_PROMPT_TEMPLATE,
    TRAVEL_PLAN_PROMPT,
    AI_SUGGESTIONS_PROMPT,
    CONVERSATION_SUMMARY_PROMPT,
    KNOWLEDGE_QA_PROMPT,
    PLAN_EDIT_PROMPT,
    get_react_prompt,
    get_travel_plan_prompt,
    get_ai_suggestions_prompt,
    get_conversation_summary_prompt,
    get_knowledge_qa_prompt,
    get_plan_edit_prompt
)

__all__ = [
    'REACT_SYSTEM_PROMPT',
    'REACT_PROMPT_TEMPLATE',
    'TRAVEL_PLAN_PROMPT',
    'AI_SUGGESTIONS_PROMPT',
    'CONVERSATION_SUMMARY_PROMPT',
    'KNOWLEDGE_QA_PROMPT',
    'PLAN_EDIT_PROMPT',
    'get_react_prompt',
    'get_travel_plan_prompt',
    'get_ai_suggestions_prompt',
    'get_conversation_summary_prompt',
    'get_knowledge_qa_prompt',
    'get_plan_edit_prompt'
]
