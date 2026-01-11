# -*- coding: utf-8 -*-
"""
LangChain 工具输入模式
定义工具的 Pydantic 输入模式
"""

from typing import Dict, Any, List, Optional
try:
    from pydantic.v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field


class HeritageSearchInput(BaseModel):
    """非遗项目查询工具输入"""
    heritage_id: Optional[int] = Field(None, description="非遗项目ID（可选）")
    category: Optional[str] = Field(None, description="非遗类别")
    region: Optional[str] = Field(None, description="地区名称")
    keywords: Optional[str] = Field(None, description="搜索关键词")


class WeatherQueryInput(BaseModel):
    """天气查询工具输入"""
    city: str = Field(..., description="城市名称")
    days: int = Field(3, description="查询天数")


class TravelRouteInput(BaseModel):
    """旅游路线规划工具输入"""
    heritage_ids: List[int] = Field(..., description="非遗项目ID列表")
    travel_days: int = Field(3, description="旅行天数")
    departure_location: str = Field("西安", description="出发地城市")
    travel_mode: str = Field("自驾", description="出行方式")
    budget_range: str = Field("中等", description="预算范围")


class KnowledgeBaseInput(BaseModel):
    """知识库问答工具输入"""
    question: str = Field(..., description="用户问题")
    category: str = Field("其他", description="问题类别")


class PlanEditInput(BaseModel):
    """规划编辑工具输入"""
    current_plan: Dict[str, Any] = Field(..., description="当前规划数据")
    edit_request: str = Field(..., description="用户的修改请求")
