# -*- coding: utf-8 -*-
"""
Agent工具接口定义模块
将现有服务封装为标准化的工具接口，支持ReAct推理循环
"""

import asyncio
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from loguru import logger


def _filter_ids_from_data(data: Any) -> Any:
    """
    从数据中过滤掉ID字段，避免泄露给用户
    
    Args:
        data: 原始数据（字典、列表或其他类型）
    
    Returns:
        过滤后的数据
    """
    if isinstance(data, dict):
        filtered = {}
        for key, value in data.items():
            if key.lower() in ['id', 'session_id', 'plan_id', 'heritage_id', 'user_id']:
                continue
            filtered[key] = _filter_ids_from_data(value)
        return filtered
    elif isinstance(data, list):
        return [_filter_ids_from_data(item) for item in data]
    else:
        return data


class BaseTool(ABC):
    """工具基类，定义标准工具接口"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """参数Schema"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具调用"""
        pass


class HeritageSearchTool(BaseTool):
    """非遗项目查询工具"""

    @property
    def name(self) -> str:
        return "heritage_search"

    @property
    def description(self) -> str:
        return "查询非物质文化遗产项目的详细信息。支持两种查询方式：1) 通过heritage_id精确查询；2) 通过keywords关键词模糊搜索。返回结果包含项目ID、名称、类别、地区、描述等。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "heritage_id": {
                    "type": "integer",
                    "description": "非遗项目ID（整数），如17、20。用于精确查询特定项目"
                },
                "keywords": {
                    "type": "string",
                    "description": "搜索关键词，用于模糊匹配项目名称或描述，如'皮影戏'"
                },
                "category": {
                    "type": "string",
                    "description": "非遗类别筛选：传统技艺、民间文学、传统音乐、传统舞蹈、戏曲、曲艺、传统体育游艺与杂技、传统美术、传统医药、民俗"
                },
                "region": {
                    "type": "string",
                    "description": "地区筛选，如：西安、咸阳、宝鸡等陕西城市"
                }
            },
            "required": []
        }

    async def execute(self, heritage_id: int = None, category: str = None,
                      region: str = None, keywords: str = None) -> Dict[str, Any]:
        """执行非遗项目查询"""
        try:
            import aiohttp
            from Agent.config import config
            
            backend_url = config.BACKEND_API_URL
            
            if heritage_id:
                api_url = f"{backend_url}/items/?ids={heritage_id}"
            else:
                params = []
                if keywords:
                    params.append(f"search={keywords}")
                if category:
                    params.append(f"category={category}")
                if region:
                    params.append(f"region={region}")
                
                if params:
                    api_url = f"{backend_url}/items/?{'&'.join(params)}"
                else:
                    api_url = f"{backend_url}/items/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if isinstance(data, dict) and 'results' in data:
                            items = data['results']
                        elif isinstance(data, list):
                            items = data
                        else:
                            items = []
                        
                        filtered_items = _filter_ids_from_data(items)
                        
                        return {
                            'success': True,
                            'heritage_items': filtered_items,
                            'count': len(items)
                        }
                    else:
                        return {'success': False, 'error': f'API请求失败: {response.status}'}

        except Exception as e:
            logger.error(f"非遗查询失败: {str(e)}")
            return {'success': False, 'error': f"查询失败: {str(e)}"}


class WeatherQueryTool(BaseTool):
    """天气查询工具"""

    @property
    def name(self) -> str:
        return "weather_query"

    @property
    def description(self) -> str:
        return "查询指定城市或地区的天气预报，包括温度、天气状况、湿度、风力等信息。适用于回答用户关于旅行目的地天气的问题。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称，如：西安、北京、上海"
                },
                "days": {
                    "type": "integer",
                    "description": "查询天数，默认为3天，最长7天"
                }
            },
            "required": ["city"]
        }

    async def execute(self, city: str, days: int = 3) -> Dict[str, Any]:
        """执行天气查询"""
        try:
            from ..services.weather import get_weather_service
            weather_service = get_weather_service()

            # 将城市名称转换为坐标
            coordinates = await self._get_city_coordinates(city)
            if not coordinates:
                return {'success': False, 'error': f"无法获取城市'{city}'的坐标信息"}

            latitude, longitude = coordinates
            result = await weather_service.get_weather_forecast(latitude, longitude, days)

            if result.get('success'):
                return {
                    'success': True,
                    'weather': result.get('weather', {}),
                    'forecast': result.get('forecast', []),
                    'location': city,
                    'coordinates': {'latitude': latitude, 'longitude': longitude},
                    'data_source': result.get('data_source', 'unknown'),
                    'source_description': result.get('source_description', '数据来源未知')
                }
            else:
                return {'success': False, 'error': result.get('error', '天气查询失败')}

        except Exception as e:
            logger.error(f"天气查询失败: {str(e)}")
            return {'success': False, 'error': f"天气查询失败: {str(e)}"}

    async def _get_city_coordinates(self, city: str) -> Optional[tuple]:
        """
        获取城市坐标（通过统一地理编码服务）
        
        Args:
            city (str): 城市名称
            
        Returns:
            Optional[tuple]: (latitude, longitude) 或 None
        """
        from ..services.geocoding import get_geocoding_service
        
        geocoding = get_geocoding_service()
        coords = await geocoding.get_coordinates(city)
        
        if coords:
            logger.info(f"获取城市坐标成功: {city} -> {coords}")
            return coords
        
        default = geocoding.get_default_coordinates()
        logger.warning(f"未找到城市'{city}'的坐标，使用默认坐标: {default}")
        return default


class TravelRouteTool(BaseTool):
    """旅游路线规划工具"""

    @property
    def name(self) -> str:
        return "travel_route_planning"

    @property
    def description(self) -> str:
        return "根据非遗项目ID列表和用户偏好，生成优化的旅游路线规划。注意：heritage_ids必须是整数ID数组（如[17,20]），不能是项目名称。如需通过名称查找项目，请先使用heritage_search工具获取ID。"

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
                    "description": "出行方式：自驾、公共交通"
                },
                "budget_range": {
                    "type": "string",
                    "description": "预算范围：经济型、中等、豪华型"
                }
            },
            "required": ["heritage_ids", "travel_days"]
        }

    async def execute(self, heritage_ids: List[int], travel_days: int = 3,
                      departure_location: str = "西安", travel_mode: str = "自驾",
                      budget_range: str = "中等") -> Dict[str, Any]:
        """执行路线规划"""
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
                filtered_plan = _filter_ids_from_data(result.get('plan', {}))
                filtered_route = _filter_ids_from_data(result.get('route', []))
                
                return {
                    'success': True,
                    'plan': filtered_plan,
                    'route': filtered_route
                }
            else:
                return {'success': False, 'error': result.get('error', '路线规划失败')}

        except Exception as e:
            logger.error(f"路线规划失败: {str(e)}")
            return {'success': False, 'error': f"路线规划失败: {str(e)}"}


class KnowledgeBaseTool(BaseTool):
    """知识库问答工具"""

    @property
    def name(self) -> str:
        return "knowledge_base_qa"

    @property
    def description(self) -> str:
        return "回答关于陕西非物质文化遗产的一般性问题，包括历史背景、文化意义、保护现状等。适用于知识性问答。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "用户问题"
                },
                "category": {
                    "type": "string",
                    "description": "问题类别：历史、工艺、民俗、传承人、其他"
                }
            },
            "required": ["question"]
        }

    async def execute(self, question: str, category: str = "其他") -> Dict[str, Any]:
        """执行知识库问答"""
        try:
            from Agent.models.llm_model import get_llm_model
            llm_model = get_llm_model()

            prompt = self._build_knowledge_prompt(question, category)

            response = await llm_model._call_model(prompt)

            if response.get('success'):
                return {
                    'success': True,
                    'answer': response['content'],
                    'source': 'knowledge_base'
                }
            else:
                return {'success': False, 'error': response.get('error', '知识查询失败')}

        except Exception as e:
            logger.error(f"知识库查询失败: {str(e)}")
            return {'success': False, 'error': f"知识查询失败: {str(e)}"}

    def _build_knowledge_prompt(self, question: str, category: str) -> str:
        """构建知识库问答提示词"""
        from Agent.prompts import get_knowledge_qa_prompt
        return get_knowledge_qa_prompt(category=category, question=question)


class PlanEditTool(BaseTool):
    """规划编辑工具"""

    @property
    def name(self) -> str:
        return "plan_edit"

    @property
    def description(self) -> str:
        return "根据用户的修改要求，调整已有的旅游规划方案。包括修改日程安排、增减景点、调整路线等。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "current_plan": {
                    "type": "object",
                    "description": "当前规划数据"
                },
                "edit_request": {
                    "type": "string",
                    "description": "用户的修改请求，如：'把第三天的行程换成博物馆'、'减少一个景点'等"
                }
            },
            "required": ["current_plan", "edit_request"]
        }

    async def execute(self, current_plan: Dict[str, Any],
                      edit_request: str) -> Dict[str, Any]:
        """执行规划编辑"""
        try:
            from Agent.models.llm_model import get_llm_model
            llm_model = get_llm_model()

            prompt = self._build_edit_prompt(current_plan, edit_request)

            response = await llm_model._call_model(prompt)

            if response.get('success'):
                import json
                try:
                    edited_plan = json.loads(response['content'])
                    filtered_plan = _filter_ids_from_data(edited_plan)
                    return {
                        'success': True,
                        'edited_plan': filtered_plan,
                        'changes': f"已根据'{edit_request}'修改规划"
                    }
                except json.JSONDecodeError:
                    filtered_current = _filter_ids_from_data(current_plan)
                    return {
                        'success': True,
                        'edited_plan': filtered_current,
                        'changes': response['content']
                    }
            else:
                return {'success': False, 'error': response.get('error', '编辑失败')}

        except Exception as e:
            logger.error(f"规划编辑失败: {str(e)}")
            return {'success': False, 'error': f"编辑失败: {str(e)}"}

    def _build_edit_prompt(self, current_plan: Dict[str, Any],
                          edit_request: str) -> str:
        """构建规划编辑提示词"""
        import json
        from Agent.prompts import get_plan_edit_prompt
        return get_plan_edit_prompt(
            current_plan=json.dumps(current_plan, ensure_ascii=False, indent=2),
            edit_request=edit_request
        )


class GeocodingTool(BaseTool):
    """地理位置查询工具"""

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
        """执行地理坐标查询"""
        from ..services.geocoding import get_geocoding_service
        
        geocoding = get_geocoding_service()
        coords = await geocoding.get_coordinates(location_name)
        
        if coords:
            return {
                'success': True,
                'location': location_name,
                'latitude': coords[0],
                'longitude': coords[1],
                'coordinates': {'latitude': coords[0], 'longitude': coords[1]}
            }
        
        return {
            'success': False,
            'error': f"未找到'{location_name}'的坐标信息",
            'default_coordinates': geocoding.get_default_coordinates()
        }


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        default_tools = [
            HeritageSearchTool(),
            WeatherQueryTool(),
            TravelRouteTool(),
            KnowledgeBaseTool(),
            PlanEditTool(),
            GeocodingTool()
        ]

        for tool in default_tools:
            self.register(tool)
        
        logger.info(f"工具注册完成，共 {len(self._tools)} 个工具: {', '.join(self._tools.keys())}")

    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        return [
            {
                'name': tool.name,
                'description': tool.description,
                'parameters': tool.parameters
            }
            for tool in self._tools.values()
        ]

    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        """获取所有工具信息（用于ReAct推理）"""
        return self.list_tools()


# 全局工具注册表实例
_tool_registry = None


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表单例"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def get_available_tools() -> List[Dict[str, Any]]:
    """获取所有可用工具"""
    registry = get_tool_registry()
    return registry.list_tools()


def execute_tool(tool_name: str, **kwargs) -> Dict[str, Any]:
    """执行指定工具"""
    registry = get_tool_registry()
    tool = registry.get_tool(tool_name)

    if tool is None:
        return {'success': False, 'error': f"工具不存在: {tool_name}"}

    if asyncio.iscoroutinefunction(tool.execute):
        result = asyncio.run(tool.execute(**kwargs))
    else:
        result = tool.execute(**kwargs)

    return result
