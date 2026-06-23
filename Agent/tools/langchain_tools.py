# -*- coding: utf-8 -*-
"""
LangChain Tool 封装
将业务工具封装为 LangChain Tool 格式，地图工具通过 MCP 自动获取
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

from loguru import logger

from langchain.tools import BaseTool, tool
from pydantic import BaseModel, Field, field_validator
from Agent.config.memory_budget import memory_budget


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
    def _truncate(text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + f"\n...（结果已截断，原始长度 {len(text)} 字符）"

    if result.get('success'):
        data = result.copy()
        data.pop('success', None)
        serialized = json.dumps(data, ensure_ascii=False, indent=2)
        return _truncate(serialized, memory_budget.tool_result_max_chars)
    else:
        msg = f"执行失败: {result.get('error', '未知错误')}"
        return _truncate(msg, memory_budget.tool_result_max_chars)


class HeritageSearchInput(V1BaseModel):
    """非遗搜索工具输入"""
    heritage_id: Optional[int] = Field(None, description="非遗项目ID（整数），如17、20")
    keywords: Optional[str] = Field(None, description="搜索关键词，如'皮影戏'")
    category: Optional[str] = Field(None, description="非遗类别，如'传统技艺'")
    region: Optional[str] = Field(None, description="地区，如'西安'")


class PlanQueryInput(V1BaseModel):
    """规划查询工具输入"""
    query_type: str = Field(default="overview", description="查询类型: overview/itinerary/heritages")


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
            except json.JSONDecodeError as e:
                logger.warning(f"heritage_ids JSON解析失败: {v[:50]}..., 错误: {e}")
                return None
        return v


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


class UserRecommendInput(V1BaseModel):
    """个性化推荐工具输入"""
    user_id: str = Field(description="用户ID")
    limit: int = Field(default=5, description="推荐数量，默认5")


class NearbyRegionInput(V1BaseModel):
    """邻近地区查询工具输入"""
    region_name: str = Field(description="地区名称，如'西安市'")


class RouteHintInput(V1BaseModel):
    """路线提示工具输入"""
    heritage_ids: List[int] = Field(description="非遗项目ID列表")


def create_heritage_search_tool() -> 'BaseTool':
    """创建非遗搜索工具"""
    @tool("heritage_search", args_schema=HeritageSearchInput)
    def heritage_search(heritage_id: Optional[int] = None,
                        keywords: Optional[str] = None,
                        category: Optional[str] = None,
                        region: Optional[str] = None) -> str:
        """搜索非物质文化遗产项目信息。

适用场景：用户想了解某非遗项目详情、按类别/地区搜索非遗、按关键词模糊查找。

返回：项目名称、类别、地区、描述等详情。通过heritage_id精确查询时，结果会自动附带最多3个邻近非遗项目供顺访参考。如需专门查询邻近项目（更多结果、可控数量），请使用 nearby_heritage_query。

注意：此工具用于搜索非遗项目，不适用于查询路线或距离。"""
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


def create_plan_query_tool() -> 'BaseTool':
    """创建规划查询工具"""
    @tool("plan_query", args_schema=PlanQueryInput)
    def plan_query(query_type: str = "overview") -> str:
        """查询用户当前的旅游规划信息。

适用场景：用户问"我的路线有哪些"、"行程安排是什么"、"选了哪几个项目"。

查询类型（query_type）：
- overview：概览（出发地、天数、项目数）
- itinerary：每日详细行程
- heritages：已选非遗项目列表

注意：只读取已有规划，不创建新规划。如用户尚无规划会返回提示。"""
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


def create_plan_edit_tool() -> 'BaseTool':
    """创建规划编辑工具"""
    from pydantic import BaseModel, Field

    class PlanEditInput(BaseModel):
        current_plan: Dict[str, Any] = Field(description="当前规划数据")
        edit_request: str = Field(description="用户的修改请求，如：'把第三天的行程换成博物馆'、'减少一个景点'等")

    @tool("plan_edit", args_schema=PlanEditInput)
    def plan_edit(current_plan: Dict[str, Any], edit_request: str) -> str:
        """根据用户的修改要求，调整已有的旅游规划方案。

适用场景：用户要求修改行程参数，如"改成7天"、"增加延安景点"、"预算调整为5000"。

注意：修改会立即更新用户的当前上下文和会话数据（UnifiedContext + Redis），无需额外保存操作。参数修改支持：travel_days、departure_location、travel_mode、group_size、budget_range、heritage_items。"""
        from Agent.tools.base import get_tool_registry
        tool = get_tool_registry().get_tool("plan_edit")
        result = _run_async(tool.execute(current_plan=current_plan, edit_request=edit_request))
        return _format_result(result)

    return plan_edit


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
如需具体交通规划，请根据用户出行方式调用高德地图工具：
- 驾车：maps_direction_driving
- 公交：maps_direction_transit  
- 骑行：maps_direction_riding
- 步行：maps_direction_walking

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


def create_nearby_heritage_tool() -> 'BaseTool':
    """创建邻近非遗查询工具"""
    @tool("nearby_heritage_query", args_schema=NearbyHeritageInput)
    def nearby_heritage_query(heritage_id: Optional[int] = None,
                               heritage_name: Optional[str] = None,
                               limit: int = 5) -> str:
        """查询指定非遗项目邻近的其他非遗项目。

适用场景：用户问"XX附近还有什么非遗"、"去了A还能顺路去哪"、"周边有什么可看的"。

基于知识图谱中 NEAR 边和 Haversine 距离计算，返回按距离排序的邻近非遗列表（含距离信息）。与 heritage_search 不同，本工具专门用于邻近查询，结果更全（默认5条），且不会混入项目详情搜索的结果。

参数：heritage_id/heritage_name 二选一，limit 控制返回数量。"""
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
        """查询与指定非遗项目相关的其他非遗项目。

适用场景：用户问"还有什么类似的传统技艺"、"XX地区还有哪些非遗"、"有没有同类的"。

基于知识图谱关系网络：category（同类）通过 BELONGS_TO 边查找同类别项目，region（同地区）通过 LOCATED_AT 边查找同地区项目，all 返回全部。

参数：heritage_id/heritage_name 二选一，relation_type 控制关系类型，limit 控制数量。"""
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


def create_user_recommend_tool() -> 'BaseTool':
    """创建个性化非遗推荐工具"""
    @tool("user_heritage_recommend", args_schema=UserRecommendInput)
    def user_heritage_recommend(user_id: str, limit: int = 5) -> str:
        """基于用户历史偏好、规划记录和导出行为，推荐可能感兴趣的非遗项目。

适用场景：用户问"有什么推荐的"、"根据我的喜好推荐非遗"、"还有哪些值得去的"。

通过知识图谱四级推理：语义映射 → 偏好桥接 → 关联推荐 → 行为分析，综合推荐。需要 L2 图谱中有用户偏好数据才能给出个性化结果，新用户或无偏好数据时推荐较少。

参数：user_id（必填），limit（默认5）。"""
        from Agent.tools.base import get_tool_registry
        tool = get_tool_registry().get_tool("user_heritage_recommend")
        result = _run_async(tool.execute(user_id=user_id, limit=limit))
        return _format_result(result)

    return user_heritage_recommend


def create_nearby_region_tool() -> 'BaseTool':
    """创建邻近地区查询工具"""
    @tool("nearby_region_query", args_schema=NearbyRegionInput)
    def nearby_region_query(region_name: str) -> str:
        """查询指定地区周边的其他区县或城市，基于知识图谱中的地区邻近关系。

适用场景：用户问"西安周边有哪些区县"、"目的地周边文化资源分布"。

返回：邻近地区列表及位置关系。"""
        from Agent.tools.base import get_tool_registry
        tool = get_tool_registry().get_tool("nearby_region_query")
        result = _run_async(tool.execute(region_name=region_name))
        return _format_result(result)

    return nearby_region_query


def create_route_hint_tool() -> 'BaseTool':
    """创建路线提示工具"""
    @tool("heritage_route_hint", args_schema=RouteHintInput)
    def heritage_route_hint(heritage_ids: List[int]) -> str:
        """基于知识图谱分析已选非遗项目，提供顺访推荐和路线提示。

适用场景：用户已选定多个非遗项目，想问"还有什么可顺访"、"路线怎么优化"。

与 route_preview 的区别：本工具基于知识图谱关系（轻量、快速），route_preview 基于高德地图真实驾驶距离（精确、耗时）。轻量级路线探索优先使用本工具。

返回：每个项目的邻近推荐、项目间途经地区建议。"""
        from Agent.tools.base import get_tool_registry
        tool = get_tool_registry().get_tool("heritage_route_hint")
        result = _run_async(tool.execute(heritage_ids=heritage_ids))
        return _format_result(result)

    return heritage_route_hint


def create_business_tools() -> List['BaseTool']:
    """创建业务工具（非地图工具）"""
    tools = [
        create_heritage_search_tool(),
        create_plan_query_tool(),
        create_plan_edit_tool(),
        create_route_preview_tool(),
        create_nearby_heritage_tool(),
        create_related_heritage_tool(),
        create_user_recommend_tool(),
        create_nearby_region_tool(),
        create_route_hint_tool(),
    ]
    
    tools = [t for t in tools if t is not None]
    logger.info(f"创建业务工具: {len(tools)} 个")
    return tools


async def get_mcp_tools_async() -> List['BaseTool']:
    """
    异步获取 MCP 工具列表
    
    Returns:
        List: MCP 工具列表
    """
    try:
        from Agent.services.amap_mcp_service import get_amap_mcp_service
        service = await get_amap_mcp_service()
        if service.is_initialized:
            return service.get_tools()
        else:
            logger.warning("MCP 服务未初始化，返回空工具列表")
            return []
    except Exception as e:
        logger.error(f"获取 MCP 工具失败: {e}")
        return []


class LangChainToolsManager:
    """LangChain 工具管理器"""
    
    def __init__(self):
        self._tools: List['BaseTool'] = []
        self._mcp_tools: List['BaseTool'] = []
        self._initialized = False
        self._mcp_initialized = False
    
    def initialize(self) -> List['BaseTool']:
        """初始化业务工具（同步）"""
        if self._initialized:
            return self._tools
        
        self._tools = create_business_tools()
        self._initialized = True
        return self._tools
    
    async def initialize_mcp(self) -> bool:
        """
        初始化 MCP 工具（异步）
        
        Returns:
            bool: 是否初始化成功
        """
        if self._mcp_initialized:
            return True
        
        try:
            self._mcp_tools = await get_mcp_tools_async()
            self._mcp_initialized = True
            logger.info(f"MCP 工具初始化成功， 工具数量: {len(self._mcp_tools)}")
            return True
        except Exception as e:
            logger.error(f"初始化 MCP 工具失败: {e}")
            return False
    
    async def get_all_tools(self) -> List['BaseTool']:
        """
        获取所有工具（异步）
        
        Returns:
            List: 完整的工具列表
        """
        if not self._initialized:
            self.initialize()
        
        if not self._mcp_initialized:
            await self.initialize_mcp()
        
        all_tools = self._tools + self._mcp_tools
        logger.info(f"工具加载完成: 业务工具 {len(self._tools)} 个, MCP 工具 {len(self._mcp_tools)} 个, 共计 {len(all_tools)} 个")
        
        return all_tools
    
    def get_tools(self) -> List['BaseTool']:
        """获取业务工具列表（同步，仅业务工具）"""
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
