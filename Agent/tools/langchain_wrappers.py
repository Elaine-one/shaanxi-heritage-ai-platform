# -*- coding: utf-8 -*-
"""
LangChain 工具包装器
使用原生函数定义工具
"""

import json
import asyncio
from typing import Dict, Any, List, Optional

from loguru import logger
from Agent.tools.base import get_tool_registry


def _run_async(coro):
    """同步执行异步函数"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


def _format_result(result: Dict[str, Any]) -> str:
    """格式化工具执行结果为字符串"""
    if result.get('success'):
        return json.dumps(result, ensure_ascii=False, indent=2)
    else:
        return f"工具执行失败: {result.get('error', '未知错误')}"


def heritage_search(heritage_id: Optional[int] = None,
                    category: Optional[str] = None,
                    region: Optional[str] = None,
                    keywords: Optional[str] = None) -> str:
    """
    查询非遗项目信息。
    
    输入: keywords(关键词) 或 heritage_id(ID) 或 region(地区)
    输出: 项目名称、类别、地区、描述等。
    """
    tool = get_tool_registry().get_tool("heritage_search")
    result = _run_async(tool.execute(
        heritage_id=heritage_id,
        category=category,
        region=region,
        keywords=keywords
    ))
    return _format_result(result)


def weather_query(city: str, days: int = 3) -> str:
    """
    查询城市天气预报。
    
    输入: city(城市名), days(天数,默认3)
    输出: 日期、温度、天气状况、出行建议。
    """
    tool = get_tool_registry().get_tool("weather_query")
    result = _run_async(tool.execute(city=city, days=days))
    return _format_result(result)


def travel_route_planning(heritage_ids: Any, travel_days: int = 3,
                          departure_location: str = "西安",
                          travel_mode: str = "自驾",
                          budget_range: str = "中等") -> str:
    """
    生成旅游路线规划。
    
    输入: heritage_ids(非遗ID列表), travel_days(天数), departure_location(出发地), travel_mode(出行方式), budget_range(预算)
    输出: 完整行程规划。
    """
    if isinstance(heritage_ids, str):
        try:
            heritage_ids = json.loads(heritage_ids)
        except:
            heritage_ids = [int(x.strip()) for x in heritage_ids.replace('[', '').replace(']', '').split(',') if x.strip()]
    elif not isinstance(heritage_ids, list):
        heritage_ids = [int(heritage_ids)]
    
    heritage_ids = [int(x) for x in heritage_ids]
    
    tool = get_tool_registry().get_tool("travel_route_planning")
    result = _run_async(tool.execute(
        heritage_ids=heritage_ids,
        travel_days=travel_days,
        departure_location=departure_location,
        travel_mode=travel_mode,
        budget_range=budget_range
    ))
    return _format_result(result)


def knowledge_base_qa(question: str, category: str = "其他") -> str:
    """
    回答非遗知识性问题。
    
    输入: question(问题), category(类别)
    输出: 专业解答。
    """
    tool = get_tool_registry().get_tool("knowledge_base_qa")
    result = _run_async(tool.execute(question=question, category=category))
    return _format_result(result)


def plan_edit(current_plan: Dict[str, Any], edit_request: str) -> str:
    """
    修改已有旅游规划。
    
    输入: current_plan(当前规划), edit_request(修改要求)
    输出: 调整后的规划。
    """
    tool = get_tool_registry().get_tool("plan_edit")
    result = _run_async(tool.execute(current_plan=current_plan, edit_request=edit_request))
    return _format_result(result)


def geocoding_query(location_name: str) -> str:
    """
    查询地点坐标。
    
    输入: location_name(地点名)
    输出: 经纬度坐标。
    """
    tool = get_tool_registry().get_tool("geocoding_query")
    result = _run_async(tool.execute(location_name=location_name))
    return _format_result(result)


def poi_search(query: str, region: str = None, location: str = None, 
               radius: int = 2000) -> str:
    """
    搜索周边兴趣点(POI)，如餐厅、酒店、景点、停车场等。
    
    输入: query(搜索关键词), region(城市名) 或 location(中心点坐标), radius(搜索半径)
    输出: POI列表，包含名称、地址、坐标、距离等信息。
    """
    tool = get_tool_registry().get_tool("poi_search")
    result = _run_async(tool.execute(
        query=query,
        region=region,
        location=location,
        radius=radius
    ))
    return _format_result(result)


def traffic_query(model: str = "around", road_name: str = None,
                  city: str = None, center: str = None, 
                  radius: int = 500) -> str:
    """
    查询实时交通拥堵情况。
    
    输入: model(查询类型: road按道路名/around按坐标周边), road_name(道路名), city(城市), center(中心点坐标), radius(半径)
    输出: 路况状态、拥堵程度等信息。
    """
    tool = get_tool_registry().get_tool("traffic_query")
    result = _run_async(tool.execute(
        model=model,
        road_name=road_name,
        city=city,
        center=center,
        radius=radius
    ))
    return _format_result(result)


def get_langchain_tools() -> List:
    """
    获取所有工具函数列表
    自动从函数签名和 docstring 提取工具描述
    """
    return [
        heritage_search,
        weather_query,
        travel_route_planning,
        knowledge_base_qa,
        plan_edit,
        geocoding_query,
        poi_search,
        traffic_query,
    ]


class LangChainToolWrapper:
    """LangChain 工具包装器"""
    
    def __init__(self):
        self._tools = get_langchain_tools()
        logger.info(f"LangChain 工具初始化完成，共 {len(self._tools)} 个工具")
    
    def get_tools(self) -> List:
        return self._tools
    
    def get_tool(self, name: str) -> Optional[Any]:
        for tool in self._tools:
            if tool.__name__ == name:
                return tool
        return None


_tool_wrapper = None


def get_langchain_tool_wrapper() -> LangChainToolWrapper:
    """获取工具包装器单例"""
    global _tool_wrapper
    if _tool_wrapper is None:
        _tool_wrapper = LangChainToolWrapper()
    return _tool_wrapper
