# -*- coding: utf-8 -*-
"""
LangChain 工具包装器
将现有工具包装为 LangChain 兼容的工具格式
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import StructuredTool
from loguru import logger

from Agent.tools.base import (
    HeritageSearchTool,
    WeatherQueryTool,
    TravelRouteTool,
    KnowledgeBaseTool,
    PlanEditTool,
    get_tool_registry
)
from .schemas import (
    HeritageSearchInput,
    WeatherQueryInput,
    TravelRouteInput,
    KnowledgeBaseInput,
    PlanEditInput
)


class LangChainToolWrapper:
    """LangChain 工具包装器"""

    def __init__(self):
        self._tool_registry = get_tool_registry()
        self._langchain_tools: Dict[str, StructuredTool] = {}
        self._init_tools()

    def _init_tools(self):
        """初始化 LangChain 工具"""
        
        async def heritage_search_wrapper(heritage_id: Optional[int] = None,
                                         category: Optional[str] = None,
                                         region: Optional[str] = None,
                                         keywords: Optional[str] = None) -> str:
            """非遗项目查询包装函数"""
            tool = self._tool_registry.get_tool("heritage_search")
            result = await tool.execute(
                heritage_id=heritage_id,
                category=category,
                region=region,
                keywords=keywords
            )
            return self._format_result(result)

        async def weather_query_wrapper(city: str, days: int = 3) -> str:
            """天气查询包装函数"""
            tool = self._tool_registry.get_tool("weather_query")
            result = await tool.execute(city=city, days=days)
            return self._format_result(result)

        async def travel_route_wrapper(heritage_ids: List[int], travel_days: int = 3,
                                       departure_location: str = "西安",
                                       travel_mode: str = "自驾",
                                       budget_range: str = "中等") -> str:
            """旅游路线规划包装函数"""
            tool = self._tool_registry.get_tool("travel_route_planning")
            result = await tool.execute(
                heritage_ids=heritage_ids,
                travel_days=travel_days,
                departure_location=departure_location,
                travel_mode=travel_mode,
                budget_range=budget_range
            )
            return self._format_result(result)

        async def knowledge_base_wrapper(question: str, category: str = "其他") -> str:
            """知识库问答包装函数"""
            tool = self._tool_registry.get_tool("knowledge_base_qa")
            result = await tool.execute(question=question, category=category)
            return self._format_result(result)

        async def plan_edit_wrapper(current_plan: Dict[str, Any],
                                    edit_request: str) -> str:
            """规划编辑包装函数"""
            tool = self._tool_registry.get_tool("plan_edit")
            result = await tool.execute(
                current_plan=current_plan,
                edit_request=edit_request
            )
            return self._format_result(result)

        self._langchain_tools["heritage_search"] = StructuredTool.from_function(
            func=heritage_search_wrapper,
            name="heritage_search",
            description="查询非物质文化遗产项目的详细信息，包括名称、类别、地区、描述、传承人信息等。适用于回答用户关于特定非遗项目的问题。",
            args_schema=HeritageSearchInput,
            return_direct=False
        )

        self._langchain_tools["weather_query"] = StructuredTool.from_function(
            func=weather_query_wrapper,
            name="weather_query",
            description="查询指定城市或地区的天气预报，包括温度、天气状况、湿度、风力等信息。适用于回答用户关于旅行目的地天气的问题。",
            args_schema=WeatherQueryInput,
            return_direct=False
        )

        self._langchain_tools["travel_route_planning"] = StructuredTool.from_function(
            func=travel_route_wrapper,
            name="travel_route_planning",
            description="根据非遗项目列表和用户偏好，生成优化的旅游路线规划。包括日程安排、交通路线、停留时间建议等。",
            args_schema=TravelRouteInput,
            return_direct=False
        )

        self._langchain_tools["knowledge_base_qa"] = StructuredTool.from_function(
            func=knowledge_base_wrapper,
            name="knowledge_base_qa",
            description="回答关于陕西非物质文化遗产的一般性问题，包括历史背景、文化意义、保护现状等。适用于知识性问答。",
            args_schema=KnowledgeBaseInput,
            return_direct=False
        )

        self._langchain_tools["plan_edit"] = StructuredTool.from_function(
            func=plan_edit_wrapper,
            name="plan_edit",
            description="根据用户的修改要求，调整已有的旅游规划方案。包括修改日程安排、增减景点、调整路线等。",
            args_schema=PlanEditInput,
            return_direct=False
        )

        logger.info(f"LangChain 工具初始化完成，共 {len(self._langchain_tools)} 个工具")

    def _format_result(self, result: Dict[str, Any]) -> str:
        """格式化工具执行结果为字符串"""
        if result.get('success'):
            import json
            return json.dumps(result, ensure_ascii=False, indent=2)
        else:
            return f"工具执行失败: {result.get('error', '未知错误')}"

    def get_tools(self) -> List[StructuredTool]:
        """获取所有 LangChain 工具"""
        return list(self._langchain_tools.values())

    def get_tool(self, name: str) -> Optional[StructuredTool]:
        """获取指定工具"""
        return self._langchain_tools.get(name)


# 全局工具包装器实例
_tool_wrapper = None


def get_langchain_tool_wrapper() -> LangChainToolWrapper:
    """获取 LangChain 工具包装器单例"""
    global _tool_wrapper
    if _tool_wrapper is None:
        _tool_wrapper = LangChainToolWrapper()
    return _tool_wrapper


def get_langchain_tools() -> List[StructuredTool]:
    """获取所有 LangChain 工具"""
    wrapper = get_langchain_tool_wrapper()
    return wrapper.get_tools()
