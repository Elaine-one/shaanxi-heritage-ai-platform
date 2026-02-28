# -*- coding: utf-8 -*-
"""
LangChain 工具包装器
将自定义工具包装成 LangChain 兼容的格式
"""

import asyncio
import json
import concurrent.futures
from typing import Dict, Any, List, Optional
from langchain_core.tools import StructuredTool
from loguru import logger

from Agent.tools.base import (
    HeritageSearchTool,
    WeatherQueryTool,
    TravelRouteTool,
    KnowledgeBaseTool,
    PlanEditTool,
    GeocodingTool,
    get_tool_registry
)
from Agent.tools.schemas import (
    HeritageSearchInput,
    WeatherQueryInput,
    TravelRouteInput,
    KnowledgeBaseInput,
    PlanEditInput,
    GeocodingInput
)


def run_async(coro):
    """同步执行异步函数 - 在异步上下文中不应该被调用"""
    # 这个函数只在没有运行事件循环时使用
    return asyncio.run(coro)


class LangChainToolWrapper:
    """LangChain 工具包装器"""

    def __init__(self):
        self._tool_registry = get_tool_registry()
        self._langchain_tools: Dict[str, StructuredTool] = {}
        self._init_tools()

    def _init_tools(self):
        """初始化 LangChain 工具"""

        # 同步包装函数（用于非异步上下文）
        def heritage_search_wrapper(heritage_id: Optional[int] = None,
                                         category: Optional[str] = None,
                                         region: Optional[str] = None,
                                         keywords: Optional[str] = None) -> str:
            """非遗项目查询包装函数"""
            tool = self._tool_registry.get_tool("heritage_search")
            result = run_async(tool.execute(
                heritage_id=heritage_id,
                category=category,
                region=region,
                keywords=keywords
            ))
            return self._format_result(result)

        def weather_query_wrapper(city: str, days: int = 3) -> str:
            """天气查询包装函数"""
            tool = self._tool_registry.get_tool("weather_query")
            result = run_async(tool.execute(city=city, days=days))
            return self._format_result(result)

        def travel_route_wrapper(heritage_ids: Any, travel_days: int = 3,
                                       departure_location: str = "西安",
                                       travel_mode: str = "自驾",
                                       budget_range: str = "中等") -> str:
            """旅游路线规划包装函数"""
            # 处理 heritage_ids 可能是字符串的情况
            if isinstance(heritage_ids, str):
                try:
                    heritage_ids = json.loads(heritage_ids)
                except:
                    heritage_ids = [int(x.strip()) for x in heritage_ids.replace('[', '').replace(']', '').split(',') if x.strip()]
            elif not isinstance(heritage_ids, list):
                heritage_ids = [int(heritage_ids)]
            
            # 确保所有元素都是整数
            heritage_ids = [int(x) for x in heritage_ids]
            
            tool = self._tool_registry.get_tool("travel_route_planning")
            result = run_async(tool.execute(
                heritage_ids=heritage_ids,
                travel_days=travel_days,
                departure_location=departure_location,
                travel_mode=travel_mode,
                budget_range=budget_range
            ))
            return self._format_result(result)

        def knowledge_base_wrapper(question: str, category: str = "其他") -> str:
            """知识库问答包装函数"""
            tool = self._tool_registry.get_tool("knowledge_base_qa")
            result = run_async(tool.execute(question=question, category=category))
            return self._format_result(result)

        def plan_edit_wrapper(current_plan: Dict[str, Any],
                                    edit_request: str) -> str:
            """规划编辑包装函数"""
            tool = self._tool_registry.get_tool("plan_edit")
            result = run_async(tool.execute(
                current_plan=current_plan,
                edit_request=edit_request
            ))
            return self._format_result(result)

        def geocoding_wrapper(location_name: str) -> str:
            """地理坐标查询包装函数"""
            tool = self._tool_registry.get_tool("geocoding_query")
            result = run_async(tool.execute(location_name=location_name))
            return self._format_result(result)

        # 异步包装函数（用于异步上下文）
        async def heritage_search_async(heritage_id: Optional[int] = None,
                                         category: Optional[str] = None,
                                         region: Optional[str] = None,
                                         keywords: Optional[str] = None) -> str:
            """非遗项目查询异步包装函数"""
            tool = self._tool_registry.get_tool("heritage_search")
            result = await tool.execute(
                heritage_id=heritage_id,
                category=category,
                region=region,
                keywords=keywords
            )
            return self._format_result(result)

        async def weather_query_async(city: str, days: int = 3) -> str:
            """天气查询异步包装函数"""
            tool = self._tool_registry.get_tool("weather_query")
            result = await tool.execute(city=city, days=days)
            return self._format_result(result)

        async def travel_route_async(heritage_ids: Any, travel_days: int = 3,
                                       departure_location: str = "西安",
                                       travel_mode: str = "自驾",
                                       budget_range: str = "中等") -> str:
            """旅游路线规划异步包装函数"""
            # 处理 heritage_ids 可能是字符串的情况
            if isinstance(heritage_ids, str):
                try:
                    heritage_ids = json.loads(heritage_ids)
                except:
                    heritage_ids = [int(x.strip()) for x in heritage_ids.replace('[', '').replace(']', '').split(',') if x.strip()]
            elif not isinstance(heritage_ids, list):
                heritage_ids = [int(heritage_ids)]
            
            # 确保所有元素都是整数
            heritage_ids = [int(x) for x in heritage_ids]
            
            tool = self._tool_registry.get_tool("travel_route_planning")
            result = await tool.execute(
                heritage_ids=heritage_ids,
                travel_days=travel_days,
                departure_location=departure_location,
                travel_mode=travel_mode,
                budget_range=budget_range
            )
            return self._format_result(result)

        async def knowledge_base_async(question: str, category: str = "其他") -> str:
            """知识库问答异步包装函数"""
            tool = self._tool_registry.get_tool("knowledge_base_qa")
            result = await tool.execute(question=question, category=category)
            return self._format_result(result)

        async def plan_edit_async(current_plan: Dict[str, Any],
                                    edit_request: str) -> str:
            """规划编辑异步包装函数"""
            tool = self._tool_registry.get_tool("plan_edit")
            result = await tool.execute(
                current_plan=current_plan,
                edit_request=edit_request
            )
            return self._format_result(result)

        async def geocoding_async(location_name: str) -> str:
            """地理坐标查询异步包装函数"""
            tool = self._tool_registry.get_tool("geocoding_query")
            result = await tool.execute(location_name=location_name)
            return self._format_result(result)

        self._langchain_tools["heritage_search"] = StructuredTool.from_function(
            func=heritage_search_wrapper,
            coroutine=heritage_search_async,
            name="heritage_search",
            description="查询非遗项目信息。输入: keywords(关键词) 或 heritage_id(ID) 或 region(地区)。输出: 项目名称、类别、地区、描述等。",
            args_schema=HeritageSearchInput,
            return_direct=False
        )

        self._langchain_tools["weather_query"] = StructuredTool.from_function(
            func=weather_query_wrapper,
            coroutine=weather_query_async,
            name="weather_query",
            description="查询城市天气预报。输入: city(城市名), days(天数,默认3)。输出: 日期、温度、天气状况、出行建议。",
            args_schema=WeatherQueryInput,
            return_direct=False
        )

        self._langchain_tools["travel_route_planning"] = StructuredTool.from_function(
            func=travel_route_wrapper,
            coroutine=travel_route_async,
            name="travel_route_planning",
            description="生成旅游路线规划。输入: heritage_ids(非遗ID列表), travel_days(天数), departure_location(出发地), travel_mode(出行方式), budget_range(预算)。输出: 完整行程规划。",
            args_schema=TravelRouteInput,
            return_direct=False
        )

        self._langchain_tools["knowledge_base_qa"] = StructuredTool.from_function(
            func=knowledge_base_wrapper,
            coroutine=knowledge_base_async,
            name="knowledge_base_qa",
            description="回答非遗知识性问题。输入: question(问题), category(类别)。输出: 专业解答。",
            args_schema=KnowledgeBaseInput,
            return_direct=False
        )

        self._langchain_tools["plan_edit"] = StructuredTool.from_function(
            func=plan_edit_wrapper,
            coroutine=plan_edit_async,
            name="plan_edit",
            description="修改已有旅游规划。输入: current_plan(当前规划), edit_request(修改要求)。输出: 调整后的规划。",
            args_schema=PlanEditInput,
            return_direct=False
        )

        self._langchain_tools["geocoding_query"] = StructuredTool.from_function(
            func=geocoding_wrapper,
            coroutine=geocoding_async,
            name="geocoding_query",
            description="查询地点坐标。输入: location_name(地点名)。输出: 经纬度坐标。",
            args_schema=GeocodingInput,
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
