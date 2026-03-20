# -*- coding: utf-8 -*-
"""
LangChain Tool 封装
将现有工具封装为 LangChain Tool 格式，支持 AgentExecutor 调用
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

from langchain.tools import BaseTool, tool
from pydantic import BaseModel, Field, field_validator


V1BaseModel = BaseModel

_async_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="async_tool_")


def _run_async(coro):
    """在独立线程中运行异步函数，避免事件循环冲突"""
    def run_in_thread():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coro)
        finally:
            try:
                pending = asyncio.all_tasks(new_loop)
                for task in pending:
                    task.cancel()
                if pending:
                    new_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            finally:
                new_loop.close()
    
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        future = _async_executor.submit(run_in_thread)
        return future.result(timeout=120)
    else:
        return asyncio.run(coro)


def _format_result(result: Dict[str, Any]) -> str:
    """格式化工具执行结果为字符串"""
    if result.get('success'):
        data = result.copy()
        data.pop('success', None)
        return json.dumps(data, ensure_ascii=False, indent=2)
    else:
        return f"执行失败: {result.get('error', '未知错误')}"


class HeritageSearchInput(V1BaseModel):
    """非遗搜索工具输入"""
    heritage_id: Optional[int] = Field(None, description="非遗项目ID（整数），如17、20")
    keywords: Optional[str] = Field(None, description="搜索关键词，如'皮影戏'")
    category: Optional[str] = Field(None, description="非遗类别，如'传统技艺'")
    region: Optional[str] = Field(None, description="地区，如'西安'")


class WeatherQueryInput(V1BaseModel):
    """天气查询工具输入"""
    city: str = Field(description="城市名称，如'西安'")
    days: int = Field(default=3, description="查询天数，默认3天")


class GeocodingInput(V1BaseModel):
    """地理编码工具输入"""
    address: str = Field(description="地址名称，如'西安'")


class PlanQueryInput(V1BaseModel):
    """规划查询工具输入"""
    query_type: str = Field(default="overview", description="查询类型: overview/itinerary/heritages")


class RouteDistanceInput(V1BaseModel):
    """路线距离工具输入"""
    origin: str = Field(description="出发地")
    destination: str = Field(description="目的地")
    travel_mode: str = Field(default="driving", description="出行方式: driving/walking/riding/transit")


class DrivingRouteInput(V1BaseModel):
    """驾车路线规划工具输入"""
    origin: str = Field(description="出发地名称，如'兴平市'")
    destination: str = Field(description="目的地名称，如'宝鸡市'")
    strategy: int = Field(default=0, description="策略: 0-速度优先, 1-费用优先, 2-距离优先")


class WalkingRouteInput(V1BaseModel):
    """步行路线规划工具输入"""
    origin: str = Field(description="出发地名称")
    destination: str = Field(description="目的地名称")


class RidingRouteInput(V1BaseModel):
    """骑行路线规划工具输入"""
    origin: str = Field(description="出发地名称")
    destination: str = Field(description="目的地名称")


class TransitRouteInput(V1BaseModel):
    """公交路线规划工具输入"""
    origin: str = Field(description="出发地名称")
    destination: str = Field(description="目的地名称")
    city: str = Field(description="起点城市")
    cityd: Optional[str] = Field(None, description="终点城市（跨城时必填）")


class RegeocodeInput(V1BaseModel):
    """逆地理编码工具输入"""
    location: str = Field(description="坐标，格式'经度,纬度'，如'108.94,34.34'")


class IpLocationInput(V1BaseModel):
    """IP定位工具输入"""
    ip: Optional[str] = Field(None, description="IP地址，不填则使用当前请求IP")


class RoutePreviewInput(V1BaseModel):
    """路线预览工具输入"""
    heritage_ids: Optional[List[int]] = Field(None, description="非遗项目ID列表")
    departure_location: Optional[str] = Field(None, description="出发地")
    max_routes: int = Field(default=3, description="返回的最大路线数量")
    
    @field_validator('heritage_ids', mode='before')
    @classmethod
    def parse_heritage_ids(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return None
        return v


class POISearchInput(V1BaseModel):
    """POI搜索工具输入"""
    query: str = Field(description="搜索关键词，如'餐厅'")
    region: Optional[str] = Field(None, description="城市名称")
    location: Optional[str] = Field(None, description="中心点坐标")
    radius: int = Field(default=2000, description="搜索半径(米)")


class NearbyHeritageInput(V1BaseModel):
    """邻近非遗查询工具输入"""
    heritage_id: Optional[int] = Field(None, description="非遗项目ID")
    heritage_name: Optional[str] = Field(None, description="非遗项目名称")
    limit: int = Field(default=5, description="返回数量限制")


class RelatedHeritageInput(V1BaseModel):
    """相关非遗查询工具输入"""
    heritage_id: Optional[int] = Field(None, description="非遗项目ID")
    heritage_name: Optional[str] = Field(None, description="非遗项目名称")
    relation_type: str = Field(default="all", description="关系类型: category/region/all")
    limit: int = Field(default=5, description="返回数量限制")


def create_heritage_search_tool() -> 'BaseTool':
    """创建非遗搜索工具"""
    @tool("heritage_search", args_schema=HeritageSearchInput)
    def heritage_search(heritage_id: Optional[int] = None,
                        keywords: Optional[str] = None,
                        category: Optional[str] = None,
                        region: Optional[str] = None) -> str:
        """搜索新的非物质文化遗产项目。仅用于用户想了解或添加新的非遗项目时使用。
        
        【重要】此工具不适用于以下场景：
        - 用户询问路线安排、怎么走、先去哪 -> 请使用 route_preview 工具
        - 用户询问距离、时间 -> 请使用 route_distance 工具
        - 用户询问已选项目的信息 -> 直接从规划上下文中获取
        
        【适用场景】用户想搜索新的非遗项目添加到行程中。"""
        from Agent.tools.base import get_tool_registry
        tool = get_tool_registry().get_tool("heritage_search")
        result = _run_async(tool.execute(
            heritage_id=heritage_id,
            keywords=keywords,
            category=category,
            region=region
        ))
        return _format_result(result)
    
    return heritage_search


def create_weather_query_tool() -> 'BaseTool':
    """创建天气查询工具"""
    @tool("weather_query", args_schema=WeatherQueryInput)
    def weather_query(city: str, days: int = 3) -> str:
        """查询指定城市的天气预报，包括温度、天气状况、湿度等信息。适用于旅行目的地天气查询。"""
        import requests
        from Agent.config.settings import Config
        
        api_key = Config.AMAP_API_KEY
        base_url = (Config.AMAP_API_URL or "https://restapi.amap.com/v3").rstrip('/')
        
        try:
            params = {
                'key': api_key,
                'city': city,
                'extensions': 'all',
                'output': 'json'
            }
            response = requests.get(f"{base_url}/weather/weatherInfo", params=params, timeout=30)
            data = response.json()
            
            if data.get('status') == '1':
                forecasts = data.get('forecasts', [])
                if forecasts:
                    result = {
                        'success': True,
                        'weather': {
                            'type': 'forecast',
                            'city': forecasts[0].get('city', ''),
                            'casts': forecasts[0].get('casts', [])
                        }
                    }
                    return _format_result(result)
            
            return _format_result({'success': False, 'error': f"API错误: {data.get('info', 'unknown')}"})
        except Exception as e:
            return _format_result({'success': False, 'error': str(e)})
    
    return weather_query


def create_geocoding_tool() -> 'BaseTool':
    """创建地理编码工具"""
    @tool("geocoding_query", args_schema=GeocodingInput)
    def geocoding_query(address: str) -> str:
        """查询指定地名或景点的地理坐标信息，返回经纬度。适用于需要获取位置坐标的场景。"""
        from Agent.tools.base import get_tool_registry
        tool = get_tool_registry().get_tool("geocoding_query")
        result = _run_async(tool.execute(address=address))
        return _format_result(result)
    
    return geocoding_query


def create_plan_query_tool() -> 'BaseTool':
    """创建规划查询工具"""
    @tool("plan_query", args_schema=PlanQueryInput)
    def plan_query(query_type: str = "overview") -> str:
        """查询用户当前的旅游规划信息。当用户询问"我的路线"、"行程安排"时使用。返回已选非遗项目、行程天数等信息。"""
        from Agent.tools.base import get_tool_registry
        from Agent.context.unified_context import get_current_context
        tool = get_tool_registry().get_tool("plan_query")
        context = get_current_context()
        context_dict = {}
        if context:
            context_dict = context.to_tool_context()
        result = _run_async(tool.execute(query_type=query_type, _context=context_dict))
        return _format_result(result)
    
    return plan_query


def create_route_distance_tool() -> 'BaseTool':
    """创建路线距离工具"""
    @tool("route_distance", args_schema=RouteDistanceInput)
    def route_distance(origin: str, destination: str, travel_mode: str = "driving") -> str:
        """查询地点之间的距离和行程时间。当用户询问"从A到B多远"、"开车要多久"时使用。"""
        from Agent.tools.base import get_tool_registry
        tool = get_tool_registry().get_tool("route_distance")
        result = _run_async(tool.execute(
            origin=origin,
            destination=destination,
            travel_mode=travel_mode
        ))
        return _format_result(result)
    
    return route_distance


def create_driving_route_tool() -> 'BaseTool':
    """创建驾车路线规划工具"""
    @tool("driving_route", args_schema=DrivingRouteInput)
    def driving_route(origin: str, destination: str, strategy: int = 0) -> str:
        """查询驾车路线详情，包括高速公路、距离、时间、费用。

适用场景：用户询问"驾车怎么走"、"高速路线"、"开车要多久"

【重要】origin 和 destination 参数：
- 使用城市名称（如"西安市"、"宝鸡市"）
- 或使用经纬度格式"经度,纬度"（如"108.9402,34.3416"）
- 不要使用非遗项目名称，高德地图无法识别

返回：距离、时间、高速费、途经高速、详细导航步骤"""
        from Agent.services.mcp_client import get_mcp_client
        from Agent.services.geocoding import get_geocoding_service
        
        async def _get_route():
            geocoding = get_geocoding_service()
            mcp_client = get_mcp_client()
            
            origin_coords = await geocoding.get_coordinates(origin)
            dest_coords = await geocoding.get_coordinates(destination)
            
            if not origin_coords:
                return {'success': False, 'error': f"无法获取出发地'{origin}'的坐标"}
            if not dest_coords:
                return {'success': False, 'error': f"无法获取目的地'{destination}'的坐标"}
            
            origin_str = f"{origin_coords[1]},{origin_coords[0]}"
            dest_str = f"{dest_coords[1]},{dest_coords[0]}"
            
            result = await mcp_client.maps_direction_driving(
                origin=origin_str,
                destination=dest_str,
                strategy=strategy
            )
            
            if result.get('success'):
                distance_km = round(result.get('distance', 0) / 1000, 1)
                duration_min = round(result.get('duration', 0) / 60)
                tolls = result.get('tolls', 0)
                toll_distance = result.get('toll_distance', 0)
                steps = result.get('steps', [])
                
                highways = []
                for step in steps:
                    road = step.get('road_name', '') or step.get('road', '')
                    if road and ('高速' in road or road.startswith('G') or road.startswith('S')):
                        if road not in highways:
                            highways.append(road)
                
                return {
                    'success': True,
                    'origin': origin,
                    'destination': destination,
                    'distance_km': distance_km,
                    'duration_minutes': duration_min,
                    'duration_text': f"{duration_min // 60}小时{duration_min % 60}分钟" if duration_min >= 60 else f"{duration_min}分钟",
                    'tolls': tolls,
                    'toll_distance_km': round(toll_distance / 1000, 1),
                    'highways': highways,
                    'steps': steps,
                    'message': f"从{origin}到{destination}，全程约{distance_km}公里，预计{duration_min}分钟，高速费约{tolls}元。"
                }
            return result
        
        return _format_result(_run_async(_get_route()))
    
    return driving_route


def create_walking_route_tool() -> 'BaseTool':
    """创建步行路线规划工具"""
    @tool("walking_route", args_schema=WalkingRouteInput)
    def walking_route(origin: str, destination: str) -> str:
        """查询步行路线详情，包括距离、时间和导航步骤。

适用场景：用户询问"步行怎么走"、"走路去"

【重要】origin 和 destination 参数：
- 使用城市名称（如"西安市"、"宝鸡市"）
- 或使用经纬度格式"经度,纬度"
- 不要使用非遗项目名称

返回：距离、时间、详细导航步骤"""
        async def _get_route():
            from Agent.services.mcp_client import get_mcp_client
            from Agent.services.geocoding import get_geocoding_service
            
            geocoding = get_geocoding_service()
            mcp_client = get_mcp_client()
            
            origin_coords = await geocoding.get_coordinates(origin)
            dest_coords = await geocoding.get_coordinates(destination)
            
            if not origin_coords:
                return {'success': False, 'error': f"无法获取出发地'{origin}'的坐标"}
            if not dest_coords:
                return {'success': False, 'error': f"无法获取目的地'{destination}'的坐标"}
            
            origin_str = f"{origin_coords[1]},{origin_coords[0]}"
            dest_str = f"{dest_coords[1]},{dest_coords[0]}"
            
            result = await mcp_client.maps_direction_walking(origin=origin_str, destination=dest_str)
            
            if result.get('success'):
                distance_km = round(result.get('distance', 0) / 1000, 1)
                duration_min = round(result.get('duration', 0) / 60)
                steps = result.get('steps', [])
                
                return {
                    'success': True,
                    'origin': origin,
                    'destination': destination,
                    'distance_km': distance_km,
                    'duration_minutes': duration_min,
                    'duration_text': f"{duration_min // 60}小时{duration_min % 60}分钟" if duration_min >= 60 else f"{duration_min}分钟",
                    'steps': steps,
                    'message': f"从{origin}步行到{destination}，全程约{distance_km}公里，预计{duration_min}分钟。"
                }
            return result
        
        return _format_result(_run_async(_get_route()))
    
    return walking_route


def create_riding_route_tool() -> 'BaseTool':
    """创建骑行路线规划工具"""
    @tool("riding_route", args_schema=RidingRouteInput)
    def riding_route(origin: str, destination: str) -> str:
        """查询骑行路线详情，包括距离、时间和导航步骤。

适用场景：用户询问"骑车怎么走"、"骑行路线"

【重要】origin 和 destination 参数：
- 使用城市名称（如"西安市"、"宝鸡市"）
- 或使用经纬度格式"经度,纬度"
- 不要使用非遗项目名称

返回：距离、时间、详细导航步骤"""
        async def _get_route():
            from Agent.services.mcp_client import get_mcp_client
            from Agent.services.geocoding import get_geocoding_service
            
            geocoding = get_geocoding_service()
            mcp_client = get_mcp_client()
            
            origin_coords = await geocoding.get_coordinates(origin)
            dest_coords = await geocoding.get_coordinates(destination)
            
            if not origin_coords:
                return {'success': False, 'error': f"无法获取出发地'{origin}'的坐标"}
            if not dest_coords:
                return {'success': False, 'error': f"无法获取目的地'{destination}'的坐标"}
            
            origin_str = f"{origin_coords[1]},{origin_coords[0]}"
            dest_str = f"{dest_coords[1]},{dest_coords[0]}"
            
            result = await mcp_client.maps_direction_riding(origin=origin_str, destination=dest_str)
            
            if result.get('success'):
                distance_km = round(result.get('distance', 0) / 1000, 1)
                duration_min = round(result.get('duration', 0) / 60)
                steps = result.get('steps', [])
                
                return {
                    'success': True,
                    'origin': origin,
                    'destination': destination,
                    'distance_km': distance_km,
                    'duration_minutes': duration_min,
                    'duration_text': f"{duration_min // 60}小时{duration_min % 60}分钟" if duration_min >= 60 else f"{duration_min}分钟",
                    'steps': steps,
                    'message': f"从{origin}骑行到{destination}，全程约{distance_km}公里，预计{duration_min}分钟。"
                }
            return result
        
        return _format_result(_run_async(_get_route()))
    
    return riding_route


def create_transit_route_tool() -> 'BaseTool':
    """创建公交路线规划工具"""
    @tool("transit_route", args_schema=TransitRouteInput)
    def transit_route(origin: str, destination: str, city: str, cityd: str = None) -> str:
        """查询公交/地铁路线详情，包括换乘方案、票价、时间。

适用场景：用户询问"公交怎么坐"、"坐车去"、"地铁怎么走"

【重要】origin 和 destination 参数：
- 使用城市名称（如"西安市"、"宝鸡市"）
- 或使用经纬度格式"经度,纬度"
- 不要使用非遗项目名称

返回：距离、时间、票价、换乘方案（公交线路、上下车站）"""
        async def _get_route():
            from Agent.services.mcp_client import get_mcp_client
            from Agent.services.geocoding import get_geocoding_service
            
            geocoding = get_geocoding_service()
            mcp_client = get_mcp_client()
            
            origin_coords = await geocoding.get_coordinates(origin)
            dest_coords = await geocoding.get_coordinates(destination)
            
            if not origin_coords:
                return {'success': False, 'error': f"无法获取出发地'{origin}'的坐标"}
            if not dest_coords:
                return {'success': False, 'error': f"无法获取目的地'{destination}'的坐标"}
            
            origin_str = f"{origin_coords[1]},{origin_coords[0]}"
            dest_str = f"{dest_coords[1]},{dest_coords[0]}"
            
            result = await mcp_client.maps_direction_transit(
                origin=origin_str,
                destination=dest_str,
                city=city,
                cityd=cityd
            )
            
            if result.get('success'):
                distance_km = round(result.get('distance', 0) / 1000, 1)
                duration_min = round(result.get('duration', 0) / 60)
                transits = result.get('transits', [])
                cost = result.get('cost', {})
                
                return {
                    'success': True,
                    'origin': origin,
                    'destination': destination,
                    'distance_km': distance_km,
                    'duration_minutes': duration_min,
                    'duration_text': f"{duration_min // 60}小时{duration_min % 60}分钟" if duration_min >= 60 else f"{duration_min}分钟",
                    'cost': cost,
                    'transits': transits,
                    'message': f"从{origin}到{destination}，全程约{distance_km}公里，预计{duration_min}分钟。"
                }
            return result
        
        return _format_result(_run_async(_get_route()))
    
    return transit_route


def create_regeocode_tool() -> 'BaseTool':
    """创建逆地理编码工具"""
    @tool("regeocode", args_schema=RegeocodeInput)
    def regeocode(location: str) -> str:
        """将坐标转换为详细地址信息。当用户询问"这个位置是哪里"、"坐标对应什么地址"时使用。"""
        async def _get_address():
            from Agent.services.mcp_client import get_mcp_client
            mcp_client = get_mcp_client()
            
            parts = location.split(',')
            if len(parts) == 2:
                lat, lng = float(parts[0]), float(parts[1])
                if lat > 90 or lat < -90:
                    location_str = location
                else:
                    location_str = f"{lng},{lat}"
            else:
                location_str = location
            
            result = await mcp_client.maps_regeocode(location=location_str)
            
            if result.get('success'):
                return {
                    'success': True,
                    'location': location,
                    'address': result.get('address', ''),
                    'addressComponent': result.get('addressComponent', {}),
                    'message': f"坐标{location}对应的地址是：{result.get('address', '未知')}"
                }
            return result
        
        return _format_result(_run_async(_get_address()))
    
    return regeocode


def create_ip_location_tool() -> 'BaseTool':
    """创建IP定位工具"""
    @tool("ip_location", args_schema=IpLocationInput)
    def ip_location(ip: str = None) -> str:
        """根据IP地址定位用户所在位置。当需要确定用户当前位置时使用。"""
        async def _get_location():
            from Agent.services.mcp_client import get_mcp_client
            mcp_client = get_mcp_client()
            
            result = await mcp_client.maps_ip_location(ip=ip)
            
            if result.get('success'):
                return {
                    'success': True,
                    'ip': ip,
                    'province': result.get('province', ''),
                    'city': result.get('city', ''),
                    'adcode': result.get('adcode', ''),
                    'message': f"IP地址位于：{result.get('province', '')}{result.get('city', '')}"
                }
            return result
        
        return _format_result(_run_async(_get_location()))
    
    return ip_location


def create_route_preview_tool() -> 'BaseTool':
    """创建路线预览工具"""
    @tool("route_preview", args_schema=RoutePreviewInput)
    def route_preview(heritage_ids: Optional[List[int]] = None,
                      departure_location: Optional[str] = None,
                      max_routes: int = 3) -> str:
        """查询非遗项目之间的最优游览顺序。

适用场景：用户询问"路线怎么安排"、"先去哪个地方"、"推荐路线"

返回内容：多条路线方案的顺序和距离，帮助用户选择最优游览顺序。

【重要】此工具只返回顺序建议，不包含具体交通方式。
如需具体交通规划，请根据用户出行方式调用：
- 驾车：driving_route
- 公交：transit_route  
- 骑行：riding_route

参数：
- heritage_ids: 非遗项目ID列表（可选）
- departure_location: 出发地（可选）"""
        from Agent.tools.base import get_tool_registry
        from Agent.context.unified_context import get_current_context
        tool = get_tool_registry().get_tool("route_preview")
        
        context = get_current_context()
        context_dict = context.to_tool_context() if context else {}
        result = _run_async(tool.execute(
            heritage_ids=heritage_ids,
            departure_location=departure_location,
            max_routes=max_routes,
            _context=context_dict
        ))
        return _format_result(result)
    
    return route_preview


def create_poi_search_tool() -> 'BaseTool':
    """创建POI搜索工具"""
    @tool("poi_search", args_schema=POISearchInput)
    def poi_search(query: str, region: Optional[str] = None,
                   location: Optional[str] = None, radius: int = 2000) -> str:
        """搜索周边兴趣点(POI)，如餐厅、酒店、景点、停车场等。返回名称、地址、坐标、距离等信息。"""
        from Agent.tools.base import get_tool_registry
        tool = get_tool_registry().get_tool("poi_search")
        result = _run_async(tool.execute(
            query=query,
            region=region,
            location=location,
            radius=radius
        ))
        return _format_result(result)
    
    return poi_search


def create_nearby_heritage_tool() -> 'BaseTool':
    """创建邻近非遗查询工具"""
    @tool("nearby_heritage_query", args_schema=NearbyHeritageInput)
    def nearby_heritage_query(heritage_id: Optional[int] = None,
                               heritage_name: Optional[str] = None,
                               limit: int = 5) -> str:
        """查询指定非遗项目邻近的其他非遗项目。基于知识图谱的地理位置关系，返回可顺访的非遗项目。"""
        from Agent.tools.base import get_tool_registry
        tool = get_tool_registry().get_tool("nearby_heritage_query")
        result = _run_async(tool.execute(
            heritage_id=heritage_id,
            heritage_name=heritage_name,
            limit=limit
        ))
        return _format_result(result)
    
    return nearby_heritage_query


def create_related_heritage_tool() -> 'BaseTool':
    """创建相关非遗查询工具"""
    @tool("related_heritage_query", args_schema=RelatedHeritageInput)
    def related_heritage_query(heritage_id: Optional[int] = None,
                                heritage_name: Optional[str] = None,
                                relation_type: str = "all",
                                limit: int = 5) -> str:
        """查询与指定非遗项目相关的其他非遗项目。基于类别、地区等关系，推荐同类或同地区的非遗项目。"""
        from Agent.tools.base import get_tool_registry
        tool = get_tool_registry().get_tool("related_heritage_query")
        result = _run_async(tool.execute(
            heritage_id=heritage_id,
            heritage_name=heritage_name,
            relation_type=relation_type,
            limit=limit
        ))
        return _format_result(result)
    
    return related_heritage_query


def create_mcp_geo_tool() -> 'BaseTool':
    """创建MCP地理编码工具"""
    @tool("maps_geo", args_schema=GeocodingInput)
    def maps_geo(address: str) -> str:
        """查询地址的经纬度坐标。输入地址名称，返回经纬度坐标。"""
        from Agent.services.mcp_client import get_mcp_client
        mcp_client = get_mcp_client()
        result = _run_async(mcp_client.maps_geo(address=address))
        return _format_result(result)
    
    return maps_geo


def create_mcp_weather_tool() -> 'BaseTool':
    """创建MCP天气查询工具"""
    @tool("maps_weather", args_schema=WeatherQueryInput)
    def maps_weather(city: str, days: int = 3) -> str:
        """查询城市天气信息。输入城市名称，返回天气详情。"""
        import requests
        from Agent.config.settings import Config
        
        api_key = Config.AMAP_API_KEY
        base_url = (Config.AMAP_API_URL or "https://restapi.amap.com/v3").rstrip('/')
        
        try:
            params = {
                'key': api_key,
                'city': city,
                'extensions': 'all',
                'output': 'json'
            }
            response = requests.get(f"{base_url}/weather/weatherInfo", params=params, timeout=30)
            data = response.json()
            
            if data.get('status') == '1':
                forecasts = data.get('forecasts', [])
                if forecasts:
                    result = {
                        'success': True,
                        'weather': {
                            'type': 'forecast',
                            'city': forecasts[0].get('city', ''),
                            'casts': forecasts[0].get('casts', [])
                        }
                    }
                    return _format_result(result)
            
            return _format_result({'success': False, 'error': f"API错误: {data.get('info', 'unknown')}"})
        except Exception as e:
            return _format_result({'success': False, 'error': str(e)})
    
    return maps_weather


def create_langchain_tools() -> List['BaseTool']:
    """创建所有 LangChain 工具"""
    tools = [
        create_heritage_search_tool(),
        create_weather_query_tool(),
        create_geocoding_tool(),
        create_plan_query_tool(),
        create_route_distance_tool(),
        create_driving_route_tool(),
        create_walking_route_tool(),
        create_riding_route_tool(),
        create_transit_route_tool(),
        create_regeocode_tool(),
        create_ip_location_tool(),
        create_route_preview_tool(),
        create_poi_search_tool(),
        create_nearby_heritage_tool(),
        create_related_heritage_tool(),
        create_mcp_geo_tool(),
        create_mcp_weather_tool(),
    ]
    
    tools = [t for t in tools if t is not None]
    
    logger.info(f"创建 LangChain 工具: {len(tools)} 个")
    return tools


class LangChainToolsManager:
    """LangChain 工具管理器"""
    
    def __init__(self):
        self._tools: List['BaseTool'] = []
        self._initialized = False
    
    def initialize(self) -> List['BaseTool']:
        """初始化工具"""
        if self._initialized:
            return self._tools
        
        self._tools = create_langchain_tools()
        self._initialized = True
        return self._tools
    
    def get_tools(self) -> List['BaseTool']:
        """获取工具列表"""
        if not self._initialized:
            self.initialize()
        return self._tools
    
    def get_tool_names(self) -> List[str]:
        """获取工具名称列表"""
        return [t.name for t in self.get_tools()]
    
    def get_tool_by_name(self, name: str) -> Optional['BaseTool']:
        """根据名称获取工具"""
        for tool in self.get_tools():
            if tool.name == name:
                return tool
        return None


_tools_manager: Optional[LangChainToolsManager] = None


def get_langchain_tools_manager() -> LangChainToolsManager:
    """获取工具管理器单例"""
    global _tools_manager
    if _tools_manager is None:
        _tools_manager = LangChainToolsManager()
    return _tools_manager


def get_langchain_tools() -> List['BaseTool']:
    """获取 LangChain 工具列表"""
    return get_langchain_tools_manager().get_tools()
