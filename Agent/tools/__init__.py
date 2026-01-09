# -*- coding: utf-8 -*-
"""
Tools 模块
包含 Agent 可用的工具集合，包括基础工具接口和 LangChain 工具包装器
"""

from .base import (
    BaseTool,
    HeritageSearchTool,
    WeatherQueryTool,
    TravelRouteTool,
    KnowledgeBaseTool,
    PlanEditTool,
    ToolRegistry,
    get_tool_registry
)
from .langchain_wrappers import (
    LangChainToolWrapper,
    get_langchain_tools
)
from .schemas import (
    HeritageSearchInput,
    WeatherQueryInput,
    TravelRouteInput,
    KnowledgeBaseInput,
    PlanEditInput
)

__all__ = [
    # Base tools
    'BaseTool',
    'HeritageSearchTool',
    'WeatherQueryTool',
    'TravelRouteTool',
    'KnowledgeBaseTool',
    'PlanEditTool',
    'ToolRegistry',
    'get_tool_registry',
    # LangChain wrappers
    'LangChainToolWrapper',
    'get_langchain_tools',
    # Schemas
    'HeritageSearchInput',
    'WeatherQueryInput',
    'TravelRouteInput',
    'KnowledgeBaseInput',
    'PlanEditInput'
]
