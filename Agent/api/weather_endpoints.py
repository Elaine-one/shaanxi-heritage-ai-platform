# -*- coding: utf-8 -*-
"""
天气API端点
提供天气信息相关的API接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from Agent.services.weather import get_weather_service

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由路由器
router = APIRouter(prefix="/weather", tags=["weather"])

class MultiLocationRequest(BaseModel):
    """多位置天气请求模型"""
    locations: List[Dict[str, Any]]
    days: Optional[int] = 7

class LocationWeatherRequest(BaseModel):
    """单位置天气请求模型"""
    latitude: float
    longitude: float
    days: Optional[int] = 7

@router.post("/multi-location")
async def get_multi_location_weather(request: MultiLocationRequest):
    """
    获取多个位置的天气信息
    
    Args:
        request (MultiLocationRequest): 多位置天气请求
        
    Returns:
        Dict[str, Any]: 多位置天气数据
    """
    try:
        weather_service = get_weather_service()
        result = await weather_service.get_multi_location_weather(request.locations, request.days)
        return result
    except Exception as e:
        logger.error(f"获取多位置天气信息时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取天气信息失败: {str(e)}")

@router.get("/forecast")
async def get_weather_forecast(latitude: float, longitude: float, days: int = 7):
    """
    获取指定位置的天气预报
    
    Args:
        latitude (float): 纬度
        longitude (float): 经度
        days (int): 预报天数，默认7天
        
    Returns:
        Dict[str, Any]: 天气预报数据
    """
    try:
        weather_service = get_weather_service()
        result = await weather_service.get_weather_forecast(latitude, longitude, days)
        return result
    except Exception as e:
        logger.error(f"获取天气预报时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取天气预报失败: {str(e)}")

@router.get("/current")
async def get_current_weather(latitude: float, longitude: float):
    """
    获取指定位置的当前天气
    
    Args:
        latitude (float): 纬度
        longitude (float): 经度
        
    Returns:
        Dict[str, Any]: 当前天气数据
    """
    try:
        weather_service = get_weather_service()
        result = await weather_service.get_current_weather(latitude, longitude)
        return result
    except Exception as e:
        logger.error(f"获取当前天气时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取当前天气失败: {str(e)}")