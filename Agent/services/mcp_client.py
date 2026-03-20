# -*- coding: utf-8 -*-
"""
地图 MCP 客户端
提供路线规划、POI搜索、地理编码等能力
支持高德地图和百度地图
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, Tuple
from loguru import logger
from Agent.config.settings import Config


class BaiduMapsMCPClient:
    """
    百度地图 MCP 客户端
    封装百度地图API调用，提供路线规划、POI搜索、路况查询等能力
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
        
        self.ak = Config.BAIDU_MAP_AK
        self.base_url = (Config.BAIDU_MAP_API_URL or "https://api.map.baidu.com").rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_ttl = {
            'geocode': 86400,
            'directions': 1800,
            'distance_matrix': 1800,
            'places': 3600,
            'traffic': 300,
        }
        
        self._initialized = True
        logger.info(f"百度地图MCP客户端初始化完成, AK: {self.ak[:8]}..." if self.ak else "百度地图MCP客户端初始化失败: AK未配置")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    def _get_cache_key(self, method: str, **params) -> str:
        import hashlib
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{method}:{hashlib.md5(param_str.encode()).hexdigest()}"
    
    def _get_from_cache(self, key: str, ttl: int) -> Optional[Any]:
        import time
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < ttl:
                return data
            del self._cache[key]
        return None
    
    def _save_to_cache(self, key: str, data: Any):
        import time
        self._cache[key] = (data, time.time())
    
    async def _request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params['ak'] = self.ak
        params['output'] = 'json'
        
        session = await self._get_session()
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json(content_type=None)
                    if data.get('status') == 0:
                        return {'success': True, 'data': data.get('result', data)}
                    else:
                        return {
                            'success': False, 
                            'error': f"API错误: {data.get('message', 'unknown')}",
                            'status': data.get('status')
                        }
                else:
                    return {'success': False, 'error': f"HTTP错误: {response.status}"}
        except asyncio.TimeoutError:
            return {'success': False, 'error': '请求超时'}
        except Exception as e:
            logger.error(f"百度地图API请求失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def map_geocode(self, address: str, city: str = None) -> Dict[str, Any]:
        """
        地理编码：地址 -> 坐标
        
        Args:
            address: 地址字符串
            city: 城市名称（可选）
        
        Returns:
            {'success': True, 'location': {'lat': float, 'lng': float}, ...}
        """
        cache_key = self._get_cache_key('geocode', address=address, city=city)
        cached = self._get_from_cache(cache_key, self._cache_ttl['geocode'])
        if cached:
            return cached
        
        url = f"{self.base_url}/geocoding/v3/"
        params = {'address': address}
        if city:
            params['city'] = city
        
        result = await self._request(url, params)
        
        if result['success']:
            location = result['data'].get('location', {})
            result['location'] = location
            result['lat'] = location.get('lat')
            result['lng'] = location.get('lng')
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def map_directions(
        self, 
        origin: str, 
        destination: str, 
        model: str = "driving"
    ) -> Dict[str, Any]:
        """
        路线规划：获取两点之间的真实道路路线
        
        Args:
            origin: 起点坐标，格式 "纬度,经度"
            destination: 终点坐标，格式 "纬度,经度"
            model: 出行方式 driving/walking/riding/transit
        
        Returns:
            {
                'success': True,
                'distance': int,
                'duration': int,
                'steps': list,
                ...
            }
        """
        cache_key = self._get_cache_key('directions', origin=origin, destination=destination, model=model)
        cached = self._get_from_cache(cache_key, self._cache_ttl['directions'])
        if cached:
            return cached
        
        model_map = {
            'driving': 'driving',
            'walking': 'walking', 
            'riding': 'riding',
            'transit': 'transit'
        }
        api_model = model_map.get(model, 'driving')
        
        if api_model == 'transit':
            url = f"{self.base_url}/direction/v2/transit"
        else:
            url = f"{self.base_url}/direction/v2/{api_model}"
        
        params = {
            'origin': origin,
            'destination': destination
        }
        
        result = await self._request(url, params)
        
        if result['success']:
            routes = result['data'].get('routes', [])
            if routes:
                route = routes[0]
                result['distance'] = route.get('distance', 0)
                result['duration'] = route.get('duration', 0)
                result['steps'] = self._extract_steps(route, api_model)
        
        self._save_to_cache(cache_key, result)
        return result
    
    def _extract_steps(self, route: Dict, model: str):
        """提取导航步骤"""
        steps = []
        
        if model == 'transit':
            for leg in route.get('legs', []):
                for step in leg.get('steps', []):
                    steps.append({
                        'instruction': step.get('instructions', {}).get('text', ''),
                        'distance': step.get('distance', 0),
                        'duration': step.get('duration', 0),
                        'type': step.get('type', 0)
                    })
        else:
            for step in route.get('steps', []):
                steps.append({
                    'instruction': step.get('instruction', ''),
                    'distance': step.get('distance', 0),
                    'duration': step.get('duration', 0),
                    'road_name': step.get('road_name', ''),
                    'start_location': step.get('start_location', {}),
                    'end_location': step.get('end_location', {})
                })
        
        return steps
    
    async def map_distance_matrix(
        self, 
        origins: list, 
        destinations: list, 
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        批量算路：计算多起点到多终点的距离矩阵
        
        Args:
            origins: 起点坐标列表，每个元素格式 "纬度,经度"
            destinations: 终点坐标列表
            mode: 出行方式 driving/walking/riding
        
        Returns:
            {
                'success': True,
                'matrix': List[List[Dict]],
                ...
            }
        """
        cache_key = self._get_cache_key(
            'distance_matrix', 
            origins="|".join(origins), 
            destinations="|".join(destinations),
            mode=mode
        )
        cached = self._get_from_cache(cache_key, self._cache_ttl['distance_matrix'])
        if cached:
            return cached
        
        url = f"{self.base_url}/routematrix/v2/{mode}"
        
        params = {
            'origins': "|".join(origins),
            'destinations': "|".join(destinations)
        }
        
        result = await self._request(url, params)
        
        if result['success']:
            matrix = []
            result_data = result['data']
            
            if isinstance(result_data, list):
                for row in result_data:
                    row_data = []
                    if isinstance(row, list):
                        for cell in row:
                            row_data.append({
                                'distance': cell.get('distance', {}).get('value', 0) if isinstance(cell.get('distance'), dict) else cell.get('distance', 0),
                                'duration': cell.get('duration', {}).get('value', 0) if isinstance(cell.get('duration'), dict) else cell.get('duration', 0)
                            })
                    matrix.append(row_data)
            
            result['matrix'] = matrix
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def map_search_places(
        self, 
        query: str, 
        region: str = None,
        location: str = None, 
        radius: int = 2000,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        POI搜索：搜索指定区域内的兴趣点
        
        Args:
            query: 搜索关键词
            region: 城市名称
            location: 中心点坐标 "纬度,经度"
            radius: 搜索半径(米)
            page_size: 返回结果数量
        
        Returns:
            {
                'success': True,
                'places': List[Dict],
                ...
            }
        """
        cache_key = self._get_cache_key(
            'places', 
            query=query, 
            region=region, 
            location=location, 
            radius=radius
        )
        cached = self._get_from_cache(cache_key, self._cache_ttl['places'])
        if cached:
            return cached
        
        url = f"{self.base_url}/place/v2/search"
        
        params = {
            'query': query,
            'page_size': page_size,
            'page_num': 0
        }
        
        if region:
            params['region'] = region
            params['city_limit'] = 'true' if location is None else 'false'
        
        if location:
            params['location'] = location
            params['radius'] = radius
        
        result = await self._request(url, params)
        
        if result['success']:
            places = []
            for poi in result['data'].get('results', []):
                places.append({
                    'name': poi.get('name', ''),
                    'address': poi.get('address', ''),
                    'location': poi.get('location', {}),
                    'distance': poi.get('distance', 0),
                    'telephone': poi.get('telephone', ''),
                    'type': poi.get('detail_info', {}).get('type', ''),
                    'rating': poi.get('detail_info', {}).get('overall_rating', ''),
                    'price': poi.get('detail_info', {}).get('price', ''),
                    'uid': poi.get('uid', '')
                })
            result['places'] = places
            result['total'] = result['data'].get('total', 0)
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def map_road_traffic(
        self,
        model: str = "around",
        road_name: str = None,
        city: str = None,
        center: str = None,
        radius: int = 500
    ) -> Dict[str, Any]:
        """
        路况查询：查询实时交通拥堵情况
        
        Args:
            model: 查询类型 road/bound/polygon/around
            road_name: 道路名称 (model=road时必传)
            city: 城市名称 (model=road时必传)
            center: 圆形区域中心点 "纬度,经度" (model=around时必传)
            radius: 搜索半径(米) [1,1000]
        
        Returns:
            {
                'success': True,
                'traffic': Dict,
                ...
            }
        """
        cache_key = self._get_cache_key(
            'traffic', 
            model=model, 
            road_name=road_name, 
            city=city, 
            center=center, 
            radius=radius
        )
        cached = self._get_from_cache(cache_key, self._cache_ttl['traffic'])
        if cached:
            return cached
        
        url = f"{self.base_url}/traffic/v1/{model}"
        
        params = {}
        
        if model == 'road':
            if not road_name or not city:
                return {'success': False, 'error': 'road模式需要road_name和city参数'}
            params['road_name'] = road_name
            params['city'] = city
        elif model == 'around':
            if not center:
                return {'success': False, 'error': 'around模式需要center参数'}
            params['center'] = center
            params['radius'] = min(max(radius, 1), 1000)
        
        result = await self._request(url, params)
        
        if result['success']:
            evaluation = result['data'].get('evaluation', {})
            result['traffic'] = {
                'status': evaluation.get('status', '未知'),
                'status_desc': evaluation.get('status_desc', ''),
                'road_traffic': result['data'].get('road_traffic', [])
            }
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None


_mcp_client: Optional[Any] = None


def get_mcp_client():
    """获取地图客户端单例（根据配置选择高德或百度）"""
    global _mcp_client
    
    if _mcp_client is None:
        provider = Config.MAP_PROVIDER.lower()
        
        if provider == 'amap':
            from Agent.services.amap_mcp_client import get_amap_client
            _mcp_client = get_amap_client()
            logger.info("使用高德地图客户端")
        else:
            _mcp_client = BaiduMapsMCPClient()
            logger.info("使用百度地图客户端")
    
    return _mcp_client
