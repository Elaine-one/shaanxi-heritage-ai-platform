# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from Agent.services.weather import get_weather_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/weather", tags=["天气服务"])


class MultiLocationRequest(BaseModel):
    locations: List[Dict[str, Any]]
    days: Optional[int] = 7


class LocationWeatherRequest(BaseModel):
    latitude: float
    longitude: float
    days: Optional[int] = 7


@router.post("/multi-location", summary="多位置天气")
async def get_multi_location_weather(request: MultiLocationRequest):
    """批量获取多个地理位置的天气信息"""
    try:
        weather_service = get_weather_service()
        result = await weather_service.get_multi_location_weather(request.locations, request.days)
        return result
    except Exception as e:
        logger.error(f"获取多位置天气失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取天气信息失败: {str(e)}")


@router.get("/forecast", summary="天气预报")
async def get_weather_forecast(latitude: float, longitude: float, days: int = 7):
    """获取指定位置未来几天的天气预报"""
    try:
        weather_service = get_weather_service()
        result = await weather_service.get_weather_forecast(latitude, longitude, days)
        return result
    except Exception as e:
        logger.error(f"获取天气预报失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取天气预报失败: {str(e)}")


@router.get("/current", summary="当前天气")
async def get_current_weather(latitude: float, longitude: float):
    """获取指定位置的实时天气状况"""
    try:
        weather_service = get_weather_service()
        result = await weather_service.get_current_weather(latitude, longitude)
        return result
    except Exception as e:
        logger.error(f"获取当前天气失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取当前天气失败: {str(e)}")
