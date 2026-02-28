# -*- coding: utf-8 -*-
"""
LangChain 工具输入模式
定义工具的 Pydantic 输入模式
"""

from typing import Dict, Any, List, Optional, Union
try:
    from pydantic.v1 import BaseModel, Field, validator
except ImportError:
    from pydantic import BaseModel, Field, validator


class HeritageSearchInput(BaseModel):
    """非遗项目查询工具输入"""
    heritage_id: Optional[int] = Field(None, description="非遗项目 ID（可选）")
    category: Optional[str] = Field(None, description="非遗类别")
    region: Optional[str] = Field(None, description="地区名称")
    keywords: Optional[str] = Field(None, description="搜索关键词")
    
    @validator('heritage_id', pre=True)
    def parse_heritage_id(cls, v):
        """解析 heritage_id，支持字符串或整数"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return int(v)


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
    
    @validator('heritage_ids', pre=True)
    def parse_heritage_ids(cls, v):
        """解析 heritage_ids，支持字符串、列表或其他类型"""
        if v is None:
            return []
        if isinstance(v, str):
            try:
                import json
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    # 如果解析结果是字典，尝试获取 heritage_ids 字段
                    v = parsed.get('heritage_ids', parsed.get('heritage_id', []))
                else:
                    v = parsed
            except:
                # 如果不是 JSON 格式，尝试解析为逗号分隔的字符串
                v = [int(x.strip()) for x in v.replace('[', '').replace(']', '').split(',') if x.strip()]
        elif isinstance(v, list):
            # 如果是列表，确保所有元素都是整数
            v = [int(x) for x in v]
        elif isinstance(v, dict):
            # 如果是字典，尝试获取 heritage_ids 字段
            v = v.get('heritage_ids', v.get('heritage_id', []))
            if isinstance(v, list):
                v = [int(x) for x in v]
        else:
            # 其他类型，尝试转换为整数列表
            try:
                v = [int(v)]
            except:
                v = []
        return v


class KnowledgeBaseInput(BaseModel):
    """知识库问答工具输入"""
    question: str = Field(..., description="用户问题")
    category: str = Field("其他", description="问题类别")


class PlanEditInput(BaseModel):
    """规划编辑工具输入"""
    current_plan: Dict[str, Any] = Field(..., description="当前规划数据")
    edit_request: str = Field(..., description="用户的修改请求")


class GeocodingInput(BaseModel):
    """地理坐标查询工具输入"""
    location_name: str = Field(..., description="地名、城市名或景点名称")
