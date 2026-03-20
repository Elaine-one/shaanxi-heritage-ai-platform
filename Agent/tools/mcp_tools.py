# -*- coding: utf-8 -*-
"""
MCP 工具类定义
支持高德地图和百度地图MCP客户端实现路线规划、POI搜索、地理编码工具
"""

from typing import Dict, Any, List
from loguru import logger
from Agent.tools.base import BaseTool
from Agent.config.settings import Config


def get_map_client():
    """获取地图客户端（根据配置选择高德或百度）"""
    if Config.MAP_PROVIDER.lower() == 'amap':
        from Agent.services.amap_mcp_client import get_amap_client
        return get_amap_client()
    else:
        from Agent.services.mcp_client import get_mcp_client
        return get_mcp_client()


class MCPRouteTool(BaseTool):
    """
    路线规划工具 - 基于百度地图真实道路距离
    替代原有的 TravelRouteTool，提供更准确的路线规划
    """

    @property
    def name(self) -> str:
        return "travel_route_planning"

    @property
    def description(self) -> str:
        return """根据非遗项目ID列表和用户偏好，生成优化的旅游路线规划。
使用百度地图真实道路距离计算，支持驾车、步行、骑行、公交等多种出行方式。
返回结果包含：真实道路距离、预计时间、详细导航步骤、按天分配的行程安排。
注意：heritage_ids必须是整数ID数组（如[17,20]），不能是项目名称。"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "heritage_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "非遗项目ID数组（整数），如[17, 20]。必须是数字ID，不能是名称字符串"
                },
                "travel_days": {
                    "type": "integer",
                    "description": "旅行天数（整数），如3"
                },
                "departure_location": {
                    "type": "string",
                    "description": "出发地城市名称，如'西安'"
                },
                "travel_mode": {
                    "type": "string",
                    "description": "出行方式：driving(驾车)、walking(步行)、riding(骑行)、transit(公交)",
                    "enum": ["driving", "walking", "riding", "transit"]
                },
                "budget_range": {
                    "type": "string",
                    "description": "预算范围：经济型、中等、豪华型"
                }
            },
            "required": ["heritage_ids", "travel_days"]
        }

    async def execute(self, heritage_ids: List[int], travel_days: int = 3,
                      departure_location: str = "西安", travel_mode: str = "driving",
                      budget_range: str = "中等") -> Dict[str, Any]:
        """
        执行路线规划 - 使用百度地图真实道路距离
        """
        try:
            from Agent.agent.travel_planner import get_travel_planner
            planner = get_travel_planner()
            
            planning_request = {
                'heritage_ids': heritage_ids,
                'travel_days': travel_days,
                'departure_location': departure_location,
                'travel_mode': travel_mode,
                'budget_range': budget_range
            }

            result = await planner.create_travel_plan(planning_request)

            if result.get('success'):
                from Agent.tools.base import _filter_ids_from_data
                filtered_plan = _filter_ids_from_data(result.get('plan', {}))
                filtered_route = _filter_ids_from_data(result.get('route', []))
                
                return {
                    'success': True,
                    'plan': filtered_plan,
                    'route': filtered_route,
                    'distance_type': '真实道路距离',
                    'travel_mode': travel_mode
                }
            else:
                return {'success': False, 'error': result.get('error', '路线规划失败')}

        except Exception as e:
            logger.error(f"路线规划失败: {str(e)}")
            return {'success': False, 'error': f"路线规划失败: {str(e)}"}


class MCPPOISearchTool(BaseTool):
    """
    POI搜索工具 - 搜索周边兴趣点
    新增能力：搜索餐厅、酒店、景点、停车场等
    """

    @property
    def name(self) -> str:
        return "poi_search"

    @property
    def description(self) -> str:
        return """搜索指定区域内的兴趣点(POI)，如餐厅、酒店、景点、停车场、洗手间等。
支持按城市搜索或按坐标周边搜索。
返回结果包含：名称、地址、坐标、距离、评分、电话等信息。
适用于用户询问"附近有什么好吃的"、"周边酒店推荐"等场景。"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，如：餐厅、酒店、停车场、洗手间、景点"
                },
                "region": {
                    "type": "string",
                    "description": "城市名称，如：西安、北京。与location二选一"
                },
                "location": {
                    "type": "string",
                    "description": "中心点坐标，格式'纬度,经度'，如'34.3416,108.9398'。与region二选一"
                },
                "radius": {
                    "type": "integer",
                    "description": "搜索半径(米)，默认2000，范围1-50000"
                },
                "page_size": {
                    "type": "integer",
                    "description": "返回结果数量，默认10，最大20"
                }
            },
            "required": ["query"]
        }

    async def execute(self, query: str, region: str = None, location: str = None,
                      radius: int = 2000, page_size: int = 10) -> Dict[str, Any]:
        """
        执行POI搜索
        """
        try:
            client = get_map_client()
            
            if Config.MAP_PROVIDER.lower() == 'amap':
                if location:
                    result = await client.maps_around_search(
                        keywords=query,
                        location=location,
                        radius=radius,
                        page_size=page_size
                    )
                else:
                    result = await client.maps_text_search(
                        keywords=query,
                        city=region,
                        citylimit=bool(region),
                        page_size=page_size
                    )
            else:
                result = await client.map_search_places(
                    query=query,
                    region=region,
                    location=location,
                    radius=radius,
                    page_size=page_size
                )

            if result.get('success'):
                places = result.get('places', [])
                return {
                    'success': True,
                    'places': places,
                    'total': result.get('total', len(places)),
                    'query': query,
                    'search_area': region or f"坐标{location}周边{radius}米"
                }
            else:
                return {'success': False, 'error': result.get('error', 'POI搜索失败')}

        except Exception as e:
            logger.error(f"POI搜索失败: {str(e)}")
            return {'success': False, 'error': f"POI搜索失败: {str(e)}"}


class MCPTrafficTool(BaseTool):
    """
    路况查询工具 - 实时交通拥堵情况
    新增能力：查询道路拥堵状态，帮助用户规划出行时间
    """

    @property
    def name(self) -> str:
        return "traffic_query"

    @property
    def description(self) -> str:
        return """查询实时交通拥堵情况，帮助用户规划出行时间。
支持两种查询方式：
1. 按道路名称查询：需要提供道路名称和城市
2. 按坐标周边查询：需要提供中心点坐标和搜索半径
返回结果包含：路况状态（畅通/缓行/拥堵）、平均速度等信息。
适用于用户询问"现在去XX堵车吗"、"路况怎么样"等场景。"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "model": {
                    "type": "string",
                    "description": "查询类型：road(按道路名) 或 around(按坐标周边)",
                    "enum": ["road", "around"]
                },
                "road_name": {
                    "type": "string",
                    "description": "道路名称，如'长安路'。model=road时必传"
                },
                "city": {
                    "type": "string",
                    "description": "城市名称，如'西安'。model=road时必传"
                },
                "center": {
                    "type": "string",
                    "description": "圆形区域中心点坐标，格式'纬度,经度'。model=around时必传"
                },
                "radius": {
                    "type": "integer",
                    "description": "搜索半径(米)，默认500，范围1-1000"
                }
            },
            "required": []
        }

    async def execute(self, model: str = "around", road_name: str = None,
                      city: str = None, center: str = None, 
                      radius: int = 500) -> Dict[str, Any]:
        """
        执行路况查询
        """
        try:
            client = get_map_client()
            
            if Config.MAP_PROVIDER.lower() == 'amap':
                return {
                    'success': True,
                    'traffic': {
                        'status': '未知',
                        'status_desc': '高德地图暂不支持独立路况查询API，建议使用路径规划获取路况信息'
                    },
                    'query_type': model,
                    'query_area': f"{road_name}, {city}" if model == 'road' else f"坐标{center}周边{radius}米"
                }
            else:
                result = await client.map_road_traffic(
                    model=model,
                    road_name=road_name,
                    city=city,
                    center=center,
                    radius=radius
                )

                if result.get('success'):
                    traffic = result.get('traffic', {})
                    return {
                        'success': True,
                        'traffic': traffic,
                        'query_type': model,
                        'query_area': f"{road_name}, {city}" if model == 'road' else f"坐标{center}周边{radius}米"
                    }
                else:
                    return {'success': False, 'error': result.get('error', '路况查询失败')}

        except Exception as e:
            logger.error(f"路况查询失败: {str(e)}")
            return {'success': False, 'error': f"路况查询失败: {str(e)}"}


class MCPGeocodingTool(BaseTool):
    """
    地理编码工具 - 基于MCP客户端
    提供更稳定的地理编码服务
    """

    @property
    def name(self) -> str:
        return "geocoding_query"

    @property
    def description(self) -> str:
        return "查询指定地名或景点的地理坐标信息，返回经纬度。适用于需要获取位置坐标的场景，如天气查询、路线规划等。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "location_name": {
                    "type": "string",
                    "description": "地名、城市名或景点名称，如：西安、兵马俑、大雁塔等"
                }
            },
            "required": ["location_name"]
        }

    async def execute(self, location_name: str) -> Dict[str, Any]:
        """
        执行地理坐标查询
        """
        try:
            client = get_map_client()
            
            if Config.MAP_PROVIDER.lower() == 'amap':
                result = await client.maps_geo(address=location_name)
            else:
                result = await client.map_geocode(address=location_name)
            
            if result.get('success'):
                lat = result.get('lat')
                lng = result.get('lng')
                
                if lat and lng:
                    return {
                        'success': True,
                        'location': location_name,
                        'latitude': lat,
                        'longitude': lng,
                        'coordinates': {'latitude': lat, 'longitude': lng}
                    }
            
            return {
                'success': False,
                'error': f"未找到'{location_name}'的坐标信息"
            }

        except Exception as e:
            logger.error(f"地理编码失败: {str(e)}")
            return {'success': False, 'error': f"地理编码失败: {str(e)}"}
