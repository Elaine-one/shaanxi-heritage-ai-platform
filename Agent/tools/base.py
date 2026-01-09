# -*- coding: utf-8 -*-
"""
Agent工具接口定义模块
将现有服务封装为标准化的工具接口，支持ReAct推理循环
"""

import asyncio
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from loguru import logger


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
        return "查询非物质文化遗产项目的详细信息，包括名称、类别、地区、描述、传承人信息等。适用于回答用户关于特定非遗项目的问题。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "heritage_id": {
                    "type": "integer",
                    "description": "非遗项目ID（可选，如果不知道ID可使用关键词搜索）"
                },
                "category": {
                    "type": "string",
                    "description": "非遗类别，如：传统技艺、民间文学、传统音乐、传统舞蹈、戏曲、曲艺、传统体育游艺与杂技、传统美术、传统医药、民俗"
                },
                "region": {
                    "type": "string",
                    "description": "地区名称，如：西安、咸阳、宝鸡等陕西城市"
                },
                "keywords": {
                    "type": "string",
                    "description": "搜索关键词，用于模糊匹配名称或描述"
                }
            },
            "required": []
        }

    async def execute(self, heritage_id: int = None, category: str = None,
                      region: str = None, keywords: str = None) -> Dict[str, Any]:
        """执行非遗项目查询"""
        try:
            from .heritage_analyzer import HeritageAnalyzer
            analyzer = HeritageAnalyzer()

            if heritage_id:
                result = await analyzer.analyze_heritage_items([heritage_id])
            else:
                result = await analyzer.analyze_heritage_items([])

            if result.get('success') and result.get('heritage_items'):
                items = result['heritage_items']
                filtered_items = items

                if category:
                    filtered_items = [item for item in filtered_items
                                     if category in item.get('category', '')]
                if region:
                    filtered_items = [item for item in filtered_items
                                     if region in item.get('region', '')]
                if keywords:
                    kw = keywords.lower()
                    filtered_items = [item for item in filtered_items
                                     if kw in item.get('name', '').lower()
                                     or kw in item.get('description', '').lower()]

                return {
                    'success': True,
                    'heritage_items': filtered_items,
                    'count': len(filtered_items)
                }

            return {'success': False, 'error': result.get('error', '未找到相关项目')}

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
        获取城市坐标
        
        Args:
            city (str): 城市名称
            
        Returns:
            Optional[tuple]: (latitude, longitude) 或 None
        """
        # 主要城市坐标映射
        city_coordinates = {
            '西安': (34.3416, 108.9398),
            '北京': (39.9042, 116.4074),
            '上海': (31.2304, 121.4737),
            '广州': (23.1291, 113.2644),
            '深圳': (22.5431, 114.0579),
            '成都': (30.5728, 104.0668),
            '杭州': (30.2741, 120.1551),
            '武汉': (30.5928, 114.3055),
            '重庆': (29.4316, 106.9123),
            '南京': (32.0603, 118.7969),
            '天津': (39.3434, 117.3616),
            '苏州': (31.2990, 120.5853),
            '长沙': (28.2282, 112.9388),
            '郑州': (34.7466, 113.6254),
            '西安': (34.3416, 108.9398),
            '咸阳': (34.3296, 108.7089),
            '宝鸡': (34.3616, 107.2365),
            '渭南': (34.5023, 109.5099),
            '延安': (36.5853, 109.4897),
            '汉中': (33.0677, 107.0286),
            '榆林': (38.2852, 109.7343),
            '安康': (32.6849, 109.0293),
            '商洛': (33.8697, 109.9404),
            '铜川': (34.8960, 108.9459),
            '兴平': (34.2976, 108.4901),
            '韩城': (35.4791, 110.4424),
            '华阴': (34.5661, 110.0894),
            '华县': (34.5124, 109.7323),
            '合阳': (35.2389, 110.1492),
            '蒲城': (34.9565, 109.5903),
            '富平': (34.7519, 109.1801),
            '三原': (34.6159, 108.9315),
            '泾阳': (34.5325, 108.8435),
            '乾县': (34.5294, 108.2426),
            '礼泉': (34.4846, 108.4262),
            '永寿': (34.6909, 108.1445),
            '彬县': (35.0342, 108.0849),
            '长武': (35.2061, 107.7955),
            '旬邑': (35.1137, 108.3391),
            '淳化': (34.7955, 108.5801),
            '武功': (34.2594, 108.2033)
        }
        
        # 查找城市坐标
        for city_name, coords in city_coordinates.items():
            if city in city_name or city_name in city:
                logger.info(f"找到城市坐标: {city} -> {coords}")
                return coords
        
        # 如果找不到，尝试使用百度地图API
        try:
            from ..agent.travel_planner import get_travel_planner
            planner = get_travel_planner()
            coords = await planner._get_coordinates(city)
            if coords:
                logger.info(f"通过百度API获取城市坐标: {city} -> {coords}")
                return coords
        except Exception as e:
            logger.warning(f"使用百度API获取坐标失败: {str(e)}")
        
        logger.warning(f"未找到城市'{city}'的坐标信息")
        return None


class TravelRouteTool(BaseTool):
    """旅游路线规划工具"""

    @property
    def name(self) -> str:
        return "travel_route_planning"

    @property
    def description(self) -> str:
        return "根据非遗项目列表和用户偏好，生成优化的旅游路线规划。包括日程安排、交通路线、停留时间建议等。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "heritage_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "非遗项目ID列表"
                },
                "travel_days": {
                    "type": "integer",
                    "description": "旅行天数"
                },
                "departure_location": {
                    "type": "string",
                    "description": "出发地城市"
                },
                "travel_mode": {
                    "type": "string",
                    "description": "出行方式：自驾、公共交通、步行等"
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
            from .travel_planner import get_travel_planner
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
                return {
                    'success': True,
                    'plan': result.get('plan', {}),
                    'route': result.get('route', [])
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
            from .ali_model import get_ali_model
            ali_model = get_ali_model()

            prompt = self._build_knowledge_prompt(question, category)

            response = await ali_model._call_model(prompt)

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
        return f"""你是一个陕西非物质文化遗产专家。请根据你的知识回答以下问题：

问题类别：{category}
问题：{question}

请提供准确、详细的回答。如果涉及具体项目，请尽量包含历史背景、文化意义和特色亮点。

回答："""


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
            from .ali_model import get_ali_model
            ali_model = get_ali_model()

            prompt = self._build_edit_prompt(current_plan, edit_request)

            response = await ali_model._call_model(prompt)

            if response.get('success'):
                import json
                try:
                    edited_plan = json.loads(response['content'])
                    return {
                        'success': True,
                        'edited_plan': edited_plan,
                        'changes': f"已根据'{edit_request}'修改规划"
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'edited_plan': current_plan,
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
        return f"""你是一个专业的旅游规划师。请根据用户的要求修改旅游规划。

当前规划：
{json.dumps(current_plan, ensure_ascii=False, indent=2)}

用户修改要求：{edit_request}

请分析用户意图，修改规划并返回完整的JSON格式规划数据。确保修改后：
1. 行程安排合理
2. 路线逻辑清晰
3. 包含必要的非遗项目信息

如果用户要求不合理，请提供替代建议。

请只返回JSON数据，不要其他解释："""


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
            PlanEditTool()
        ]

        for tool in default_tools:
            self.register(tool)

    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
        logger.debug(f"工具已注册: {tool.name}")

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
