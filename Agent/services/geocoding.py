# -*- coding: utf-8 -*-
"""
地理编码服务模块
统一管理地理位置坐标查询，支持高德地图API和百度地图API
"""

import asyncio
import aiohttp
import json
from pathlib import Path
from typing import Optional, Dict, Tuple
from loguru import logger
from Agent.config import config


class GeocodingService:
    """
    地理编码服务
    提供地址到坐标的转换功能
    支持高德地图和百度地图
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.provider = config.MAP_PROVIDER.lower()
        
        self.amap_key = config.AMAP_API_KEY
        self.amap_url = (config.AMAP_API_URL or 'https://restapi.amap.com/v3').rstrip('/')
        
        self.baidu_ak = config.BAIDU_MAP_AK
        self.baidu_api_url = (config.BAIDU_MAP_API_URL or '').rstrip('/')
        
        self._cache: Dict[str, Tuple[float, float]] = {}
        self._load_local_cache()
        self._initialized = True
        logger.info(f"地理编码服务初始化完成，提供商: {self.provider}，缓存数量: {len(self._cache)}")
    
    def _load_local_cache(self):
        """加载本地坐标缓存文件"""
        try:
            json_path = Path(__file__).parent.parent / 'data' / 'city_coords.json'
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for city, coords in data.items():
                        if isinstance(coords, list) and len(coords) == 2:
                            self._cache[city] = tuple(coords)
                logger.info(f"已加载 {len(self._cache)} 个本地坐标缓存")
            else:
                logger.warning(f"坐标缓存文件不存在: {json_path}")
        except Exception as e:
            logger.error(f"加载坐标缓存失败: {str(e)}")
    
    async def get_coordinates(self, location_name: str) -> Optional[Tuple[float, float]]:
        """
        获取地理位置坐标
        
        Args:
            location_name: 地名（城市、区县、景点等）
            
        Returns:
            Optional[Tuple[float, float]]: (纬度, 经度) 或 None
        """
        if not location_name:
            return None
        
        location_key = location_name.strip()
        
        if location_key in self._cache:
            logger.debug(f"命中缓存: {location_key}")
            return self._cache[location_key]
        
        if self.provider == 'amap':
            coords = await self._query_from_amap(location_key)
        else:
            coords = await self._query_from_baidu(location_key)
        
        if coords:
            self._cache[location_key] = coords
            return coords
        
        for cached_name, cached_coords in self._cache.items():
            if cached_name in location_key or location_key in cached_name:
                logger.debug(f"模糊匹配缓存: {location_key} -> {cached_name}")
                self._cache[location_key] = cached_coords
                return cached_coords
        
        logger.warning(f"未找到坐标: {location_key}")
        return None
    
    async def _query_from_amap(self, address: str) -> Optional[Tuple[float, float]]:
        """
        调用高德地图 Geocoding API 获取坐标
        """
        if not self.amap_key:
            logger.debug("高德地图API未配置，跳过API查询")
            return None
        
        clean_address = address.replace('中国', '').replace('陕西省', '')
        
        url = f"{self.amap_url}/geocode/geo"
        params = {
            'address': clean_address,
            'output': 'json',
            'key': self.amap_key,
            'city': '陕西省'
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request('GET', url, params=params) as response:
                    if response.status == 200:
                        data = await response.json(content_type=None)
                        
                        if data.get('status') == '1':
                            geocodes = data.get('geocodes', [])
                            if geocodes:
                                location = geocodes[0].get('location', '')
                                if location:
                                    lng, lat = location.split(',')
                                    coords = (float(lat), float(lng))
                                    logger.info(f"高德地图定位成功: {clean_address} -> {coords}")
                                    return coords
                        else:
                            logger.warning(f"高德地图API业务错误: {data.get('info', 'unknown')}")
                    else:
                        logger.warning(f"高德地图HTTP错误: {response.status}")
                        
        except asyncio.TimeoutError:
            logger.warning(f"高德地图API超时: {clean_address}")
        except Exception as e:
            logger.error(f"调用高德地图API失败: {str(e)}")
            
        return None
    
    async def _query_from_baidu(self, address: str) -> Optional[Tuple[float, float]]:
        """
        调用百度地图 Geocoding API 获取坐标
        """
        if not self.baidu_ak or not self.baidu_api_url:
            logger.debug("百度地图API未配置，跳过API查询")
            return None
        
        clean_address = address.replace('中国', '').replace('陕西省', '')
        
        url = f"{self.baidu_api_url}/geocoding/v3/"
        params = {
            'address': clean_address,
            'output': 'json',
            'ak': self.baidu_ak,
            'city': '陕西省'
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request('GET', url, params=params) as response:
                    if response.status == 200:
                        data = await response.json(content_type=None)
                        
                        if data.get('status') == 0:
                            location = data['result']['location']
                            coords = (location['lat'], location['lng'])
                            logger.info(f"百度地图定位成功: {clean_address} -> {coords}")
                            return coords
                        else:
                            logger.warning(f"百度地图API业务错误: {data.get('message', 'unknown')}")
                    else:
                        logger.warning(f"百度地图HTTP错误: {response.status}")
                        
        except asyncio.TimeoutError:
            logger.warning(f"百度地图API超时: {clean_address}")
        except Exception as e:
            logger.error(f"调用百度地图API失败: {str(e)}")
            
        return None
    
    def get_default_coordinates(self) -> Tuple[float, float]:
        """获取默认坐标（西安）"""
        return (34.3416, 108.9398)
    
    def add_to_cache(self, name: str, lat: float, lng: float):
        """手动添加坐标到缓存"""
        self._cache[name] = (lat, lng)
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        return {
            'total_cached': len(self._cache),
            'provider': self.provider,
            'has_amap_api': bool(self.amap_key),
            'has_baidu_api': bool(self.baidu_ak and self.baidu_api_url)
        }


_geocoding_service: Optional[GeocodingService] = None


def get_geocoding_service() -> GeocodingService:
    """获取地理编码服务单例"""
    global _geocoding_service
    if _geocoding_service is None:
        _geocoding_service = GeocodingService()
    return _geocoding_service
