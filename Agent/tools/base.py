# -*- coding: utf-8 -*-
"""
Agent工具接口定义模块
将现有服务封装为标准化的工具接口，支持ReAct推理循环
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from functools import wraps
from loguru import logger


def require_knowledge_graph(func: Callable) -> Callable:
    """
    知识图谱连接检查装饰器
    
    自动检查知识图谱连接状态，并在连接失败时返回标准错误响应。
    成功连接后，将 kg 实例作为参数传递给被装饰函数。
    """
    @wraps(func)
    async def wrapper(self, **kwargs) -> Dict[str, Any]:
        from Agent.memory.knowledge_graph import get_knowledge_graph
        kg = get_knowledge_graph()
        if not kg or not kg.is_connected():
            return {"success": False, "error": "知识图谱未连接"}
        return await func(self, kg=kg, **kwargs)
    return wrapper


def resolve_heritage_id(kg, heritage_id: int = None, heritage_name: str = None) -> Optional[int]:
    """
    解析 heritage_id，支持通过名称查找
    
    Args:
        kg: 知识图谱实例
        heritage_id: 非遗项目ID（优先使用）
        heritage_name: 非遗项目名称（备选）
    
    Returns:
        Optional[int]: 解析后的 heritage_id，或 None
    """
    if heritage_id:
        return heritage_id
    if heritage_name:
        try:
            from Agent.memory.heritage_query_service import get_heritage_query_service
            query_service = get_heritage_query_service()
            results = query_service.hybrid_query(heritage_name, top_k=1)
            if results:
                return results[0].get('id')
        except Exception as e:
            logger.warning(f"通过名称解析heritage_id失败: {e}")
    return None


def _filter_ids_from_data(data: Any) -> Any:
    """
    从数据中过滤掉内部ID字段，但保留业务需要的ID
    
    Args:
        data: 原始数据（字典、列表或其他类型）
    
    Returns:
        过滤后的数据
    """
    INTERNAL_IDS = ['session_id', 'user_id', '_id']
    
    if isinstance(data, dict):
        filtered = {}
        for key, value in data.items():
            if key.lower() in INTERNAL_IDS:
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
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        raise NotImplementedError

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """参数Schema"""
        raise NotImplementedError

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具调用"""
        raise NotImplementedError

    async def safe_execute(self, **kwargs) -> Dict[str, Any]:
        """安全执行工具调用，统一异常处理"""
        try:
            return await self.execute(**kwargs)
        except Exception as e:
            logger.error(f"{self.name}执行失败: {e}")
            return {"success": False, "error": str(e)}


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
                      region: str = None, keywords: str = None,
                      include_nearby: bool = True) -> Dict[str, Any]:
        """执行非遗项目查询 - 使用知识图谱和向量数据库，支持返回邻近项目"""
        try:
            from Agent.memory.heritage_query_service import get_heritage_query_service
            from Agent.memory.knowledge_graph import get_knowledge_graph
            
            query_service = get_heritage_query_service()
            kg = get_knowledge_graph()
            
            if heritage_id is not None:
                if isinstance(heritage_id, str):
                    if heritage_id.isdigit():
                        heritage_id = int(heritage_id)
                    else:
                        keywords = heritage_id
                        heritage_id = None
                        logger.info(f"heritage_id 是字符串，转为 keywords 搜索: {keywords}")
                
                if heritage_id is not None:
                    heritage = query_service.query_by_id(heritage_id)
                    if heritage:
                        result = {
                            'success': True,
                            'heritage_items': [heritage],
                            'count': 1
                        }
                        
                        if include_nearby and kg and kg.is_connected():
                            try:
                                nearby = kg.query_nearby_heritages_by_id(heritage_id, limit=3)
                                if nearby:
                                    result['nearby_heritages'] = nearby
                                    result['nearby_hint'] = f"发现{len(nearby)}个邻近非遗项目可顺访"
                            except Exception as e:
                                logger.debug(f"查询邻近项目失败: {e}")
                        
                        return result
                    else:
                        return {
                            'success': False,
                            'error': f'未找到ID为 {heritage_id} 的非遗项目'
                        }
            
            if keywords and keywords.strip():
                results = query_service.hybrid_query(keywords, region, category, top_k=10)
            elif region and region.strip():
                results = query_service.query_by_region(region, limit=10)
            elif category and category.strip():
                results = query_service.query_by_category(category, limit=10)
            else:
                return {
                    'success': False,
                    'error': '请提供至少一个有效的查询参数：heritage_id、keywords、region 或 category'
                }
            
            result = {
                'success': True,
                'heritage_items': results,
                'count': len(results)
            }
            
            if include_nearby and results and kg and kg.is_connected():
                first_item = results[0]
                hid = first_item.get('id')
                if hid:
                    try:
                        nearby = kg.query_nearby_heritages_by_id(hid, limit=3)
                        if nearby:
                            result['nearby_heritages'] = nearby
                            result['nearby_hint'] = f"发现{len(nearby)}个邻近非遗项目可顺访"
                    except Exception as e:
                        logger.debug(f"查询邻近项目失败: {e}")
            
            return result

        except Exception as e:
            logger.error(f"非遗查询失败: {str(e)}")
            return {'success': False, 'error': f"查询失败: {str(e)}"}


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

            logger.info(f"LLM 原始返回: {response}")

            if response.get('success'):
                import json
                content = response['content'].strip()
                if content.startswith('```'):
                    lines = content.split('\n')
                    content = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])
                logger.info(f"LLM content (cleaned): {content}")
                try:
                    edited_plan = json.loads(content)
                    logger.info(f"解析后的 edited_plan: {edited_plan}")
                    filtered_plan = _filter_ids_from_data(edited_plan)

                    self._update_current_context(filtered_plan)

                    return {
                        'success': True,
                        'edited_plan': filtered_plan,
                        'changes': f"已根据'{edit_request}'修改规划"
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析失败: {e}, content: {content}")
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

    def _update_current_context(self, edited_plan: Dict[str, Any]):
        """更新当前上下文的 plan_data 和 Redis session"""
        try:
            from Agent.context.unified_context import get_current_context
            context = get_current_context()
            if not context:
                logger.debug("无当前上下文，跳过更新")
                return

            if context.plan_data:
                if 'travel_days' in edited_plan:
                    context.plan_data.travel_days = edited_plan['travel_days']
                if 'departure' in edited_plan:
                    context.plan_data.departure_location = edited_plan['departure']
                    logger.info(f"✅ 更新 departure_location = {edited_plan['departure']}")
                if 'departure_location' in edited_plan:
                    context.plan_data.departure_location = edited_plan['departure_location']
                    logger.info(f"✅ 更新 departure_location = {edited_plan['departure_location']}")
                if 'travel_mode' in edited_plan:
                    context.plan_data.travel_mode = edited_plan['travel_mode']
                if 'group_size' in edited_plan:
                    context.plan_data.group_size = edited_plan['group_size']
                if 'budget_range' in edited_plan:
                    context.plan_data.budget_range = edited_plan['budget_range']
                if 'heritage_names' in edited_plan or 'heritage_items' in edited_plan:
                    if 'heritage_items' in edited_plan:
                        from Agent.context.unified_context import HeritageItem
                        context.plan_data.heritage_items = [
                            HeritageItem(**{k: v for k, v in item.items() if k in ('id', 'name', 'region', 'category', 'level', 'latitude', 'longitude')})
                            for item in edited_plan['heritage_items'] if isinstance(item, dict)
                        ]
                        logger.info(f"✅ 更新 heritage_items, count={len(context.plan_data.heritage_items)}")
                    elif 'heritage_names' in edited_plan:
                        logger.info(f"✅ heritage_names 更新: {edited_plan['heritage_names']}")

                logger.info(f"✅ 上下文 plan_data 已更新: travel_days={context.plan_data.travel_days}, departure={context.plan_data.departure_location}")

            try:
                from Agent.memory.session_provider import get_session_pool
                session_pool = get_session_pool()
                if session_pool and context.session_id:
                    if hasattr(session_pool, 'update_session_plan'):
                        session_pool.update_session_plan(context.session_id, edited_plan)
                        logger.info(f"✅ Session 已更新: session_id={context.session_id}, travel_days={edited_plan.get('travel_days')}")
                    elif hasattr(session_pool, 'update_session'):
                        session_pool.update_session(context.session_id, edited_plan)
                        logger.info(f"✅ Session 已通过 update_session 更新: session_id={context.session_id}")
                    else:
                        session = session_pool.get_session(context.session_id)
                        if session:
                            if 'travel_days' in edited_plan:
                                session.travel_days = edited_plan['travel_days']
                            if 'departure' in edited_plan:
                                session.departure_location = edited_plan['departure']
                            if 'travel_mode' in edited_plan:
                                session.travel_mode = edited_plan['travel_mode']
                            if 'group_size' in edited_plan:
                                session.group_size = edited_plan['group_size']
                            if 'budget_range' in edited_plan:
                                session.budget_range = edited_plan['budget_range']
                            session.current_plan = edited_plan
                            logger.info(f"✅ Session 已直接更新: session_id={context.session_id}")
            except Exception as e:
                logger.error(f"更新 session 失败: {e}")

        except Exception as e:
            logger.warning(f"更新上下文失败: {e}")

    def _build_edit_prompt(self, current_plan: Dict[str, Any],
                          edit_request: str) -> str:
        """构建规划编辑提示词"""
        import json
        from Agent.prompts import get_plan_edit_prompt
        prompt = get_plan_edit_prompt(
            current_plan=json.dumps(current_plan, ensure_ascii=False, indent=2),
            edit_request=edit_request
        )
        logger.info(f"plan_edit prompt:\n{prompt[:500]}...")
        return prompt


class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        from .knowledge_graph_tools import (
            NearbyHeritageTool, 
            RelatedHeritageTool, 
            NearbyRegionTool, 
            RouteHintTool,
            UserRecommendTool
        )
        from .plan_tools import PlanQueryTool, RouteDistanceTool, RoutePreviewTool
        
        default_tools = [
            HeritageSearchTool(),
            PlanEditTool(),
            NearbyHeritageTool(),
            RelatedHeritageTool(),
            NearbyRegionTool(),
            RouteHintTool(),
            UserRecommendTool(),
            PlanQueryTool(),
            RouteDistanceTool(),
            RoutePreviewTool()
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
