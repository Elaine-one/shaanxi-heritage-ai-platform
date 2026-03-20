# -*- coding: utf-8 -*-
"""
高德地图 MCP 客户端
提供地理编码、路径规划、POI搜索、天气查询等能力
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, Tuple, List
from loguru import logger
from Agent.config.settings import Config

AMAP_QPS_LIMIT = 3
AMAP_QPS_SEMAPHORE = asyncio.Semaphore(AMAP_QPS_LIMIT)
_last_request_time = 0.0
_request_interval = 1.0 / AMAP_QPS_LIMIT


class AmapMCPClient:
    """
    高德地图 MCP 客户端
    封装高德地图API调用，提供路线规划、POI搜索、地理编码等能力
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
        
        self.api_key = Config.AMAP_API_KEY
        self.base_url = (Config.AMAP_API_URL or "https://restapi.amap.com/v3").rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_loop = None
        
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._cache_ttl = {
            'geocode': 86400,
            'directions': 1800,
            'distance': 1800,
            'places': 3600,
            'weather': 1800,
        }
        
        self._initialized = True
        logger.info(f"高德地图MCP客户端初始化完成, API Key: {self.api_key[:8]}..." if self.api_key else "高德地图MCP客户端初始化失败: API Key未配置")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        current_loop = asyncio.get_running_loop()
        if self.session is None or self.session.closed or self._session_loop != current_loop:
            if self.session and not self.session.closed:
                try:
                    await self.session.close()
                except:
                    pass
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5, force_close=False)
            self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
            self._session_loop = current_loop
            logger.debug(f"创建新的 aiohttp session, loop: {current_loop}")
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
        params['key'] = self.api_key
        params['output'] = 'json'
        
        global _last_request_time
        async with AMAP_QPS_SEMAPHORE:
            import time
            current_time = time.time()
            time_since_last = current_time - _last_request_time
            if time_since_last < _request_interval:
                await asyncio.sleep(_request_interval - time_since_last)
            _last_request_time = time.time()
            
            session = await self._get_session()
            
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json(content_type=None)
                        if data.get('status') == '1':
                            return {'success': True, 'data': data}
                        else:
                            return {
                                'success': False,
                                'error': f"API错误: {data.get('info', 'unknown')}",
                                'status': data.get('status')
                            }
                    else:
                        return {'success': False, 'error': f"HTTP错误: {response.status}"}
            except asyncio.TimeoutError:
                return {'success': False, 'error': '请求超时'}
            except Exception as e:
                logger.error(f"高德地图API请求失败: {str(e)}")
                return {'success': False, 'error': str(e)}
    
    async def maps_geo(self, address: str, city: str = None) -> Dict[str, Any]:
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
        
        url = f"{self.base_url}/geocode/geo"
        params = {'address': address}
        if city:
            params['city'] = city
        
        result = await self._request(url, params)
        
        if result['success']:
            geocodes = result['data'].get('geocodes', [])
            if geocodes:
                location_str = geocodes[0].get('location', '')
                if location_str:
                    lng, lat = location_str.split(',')
                    result['location'] = {'lat': float(lat), 'lng': float(lng)}
                    result['lat'] = float(lat)
                    result['lng'] = float(lng)
                    result['formatted_address'] = geocodes[0].get('formatted_address', '')
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def maps_regeocode(self, location: str) -> Dict[str, Any]:
        """
        逆地理编码：坐标 -> 地址
        
        Args:
            location: 坐标，格式 "经度,纬度"
        
        Returns:
            {'success': True, 'address': str, ...}
        """
        cache_key = self._get_cache_key('regeocode', location=location)
        cached = self._get_from_cache(cache_key, self._cache_ttl['geocode'])
        if cached:
            return cached
        
        url = f"{self.base_url}/geocode/regeo"
        params = {'location': location}
        
        result = await self._request(url, params)
        
        if result['success']:
            regeocode = result['data'].get('regeocode', {})
            result['address'] = regeocode.get('formatted_address', '')
            result['addressComponent'] = regeocode.get('addressComponent', {})
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def maps_direction_driving(
        self,
        origin: str,
        destination: str,
        strategy: int = 0
    ) -> Dict[str, Any]:
        """
        驾车路径规划
        
        Args:
            origin: 起点坐标，格式 "经度,纬度"
            destination: 终点坐标，格式 "经度,纬度"
            strategy: 策略 0-速度优先 1-费用优先 2-距离优先
        
        Returns:
            {'success': True, 'distance': int, 'duration': int, 'steps': list}
        """
        cache_key = self._get_cache_key('direction_driving', origin=origin, destination=destination, strategy=strategy)
        cached = self._get_from_cache(cache_key, self._cache_ttl['directions'])
        if cached:
            return cached
        
        url = f"{self.base_url}/direction/driving"
        params = {
            'origin': origin,
            'destination': destination,
            'strategy': strategy
        }
        
        result = await self._request(url, params)
        
        if result['success']:
            route = result['data'].get('route', {})
            paths = route.get('paths', [])
            if paths:
                path = paths[0]
                result['distance'] = self._safe_int(path.get('distance'))
                result['duration'] = self._safe_int(path.get('duration'))
                result['steps'] = self._extract_driving_steps(path.get('steps', []))
                result['tolls'] = self._safe_int(path.get('tolls'))
                result['toll_distance'] = self._safe_int(path.get('toll_distance'))
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def maps_direction_walking(
        self,
        origin: str,
        destination: str
    ) -> Dict[str, Any]:
        """
        步行路径规划
        
        Args:
            origin: 起点坐标，格式 "经度,纬度"
            destination: 终点坐标，格式 "经度,纬度"
        
        Returns:
            {'success': True, 'distance': int, 'duration': int, 'steps': list}
        """
        cache_key = self._get_cache_key('direction_walking', origin=origin, destination=destination)
        cached = self._get_from_cache(cache_key, self._cache_ttl['directions'])
        if cached:
            return cached
        
        url = f"{self.base_url}/direction/walking"
        params = {
            'origin': origin,
            'destination': destination
        }
        
        result = await self._request(url, params)
        
        if result['success']:
            route = result['data'].get('route', {})
            paths = route.get('paths', [])
            if paths:
                path = paths[0]
                result['distance'] = self._safe_int(path.get('distance'))
                result['duration'] = self._safe_int(path.get('duration'))
                result['steps'] = self._extract_walking_steps(path.get('steps', []))
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def maps_direction_riding(
        self,
        origin: str,
        destination: str
    ) -> Dict[str, Any]:
        """
        骑行路径规划
        
        Args:
            origin: 起点坐标，格式 "经度,纬度"
            destination: 终点坐标，格式 "经度,纬度"
        
        Returns:
            {'success': True, 'distance': int, 'duration': int, 'steps': list}
        """
        cache_key = self._get_cache_key('direction_riding', origin=origin, destination=destination)
        cached = self._get_from_cache(cache_key, self._cache_ttl['directions'])
        if cached:
            return cached
        
        url = f"{self.base_url}/direction/riding"
        params = {
            'origin': origin,
            'destination': destination
        }
        
        result = await self._request(url, params)
        
        if result['success']:
            route = result['data'].get('route', {})
            paths = route.get('paths', [])
            if paths:
                path = paths[0]
                result['distance'] = self._safe_int(path.get('distance'))
                result['duration'] = self._safe_int(path.get('duration'))
                result['steps'] = self._extract_riding_steps(path.get('rides', []))
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def map_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        路线规划（兼容旧接口）
        
        Args:
            origin: 起点坐标，格式 "纬度,经度" 或 "经度,纬度"
            destination: 终点坐标
            mode: 出行方式 driving/walking/riding/transit
        
        Returns:
            {'success': True, 'route': {'distance': int, 'duration': int}}
        """
        if ',' in origin:
            parts = origin.split(',')
            if len(parts) == 2:
                lat, lng = float(parts[0]), float(parts[1])
                if lat > 90 or lat < -90:
                    origin = f"{parts[0]},{parts[1]}"
                else:
                    origin = f"{lng},{lat}"
        
        if ',' in destination:
            parts = destination.split(',')
            if len(parts) == 2:
                lat, lng = float(parts[0]), float(parts[1])
                if lat > 90 or lat < -90:
                    destination = f"{parts[0]},{parts[1]}"
                else:
                    destination = f"{lng},{lat}"
        
        mode_map = {
            'driving': self.maps_direction_driving,
            'walking': self.maps_direction_walking,
            'riding': self.maps_direction_riding,
            'transit': self.maps_direction_transit
        }
        
        method = mode_map.get(mode, self.maps_direction_driving)
        result = await method(origin=origin, destination=destination)
        
        if result.get('success'):
            return {
                'success': True,
                'route': {
                    'distance': result.get('distance', 0),
                    'duration': result.get('duration', 0),
                    'steps': result.get('steps', [])
                }
            }
        return result
    
    async def maps_direction_transit(
        self,
        origin: str,
        destination: str,
        city: str,
        cityd: str = None
    ) -> Dict[str, Any]:
        """
        公交路径规划
        
        Args:
            origin: 起点坐标，格式 "经度,纬度"
            destination: 终点坐标，格式 "经度,纬度"
            city: 起点城市
            cityd: 终点城市（跨城时必填）
        
        Returns:
            {'success': True, 'distance': int, 'duration': int, 'steps': list}
        """
        cache_key = self._get_cache_key('direction_transit', origin=origin, destination=destination, city=city, cityd=cityd)
        cached = self._get_from_cache(cache_key, self._cache_ttl['directions'])
        if cached:
            return cached
        
        url = f"{self.base_url}/direction/transit/integrated"
        params = {
            'origin': origin,
            'destination': destination,
            'city': city
        }
        if cityd:
            params['cityd'] = cityd
        
        result = await self._request(url, params)
        
        if result['success']:
            route = result['data'].get('route', {})
            transits = route.get('transits', [])
            
            all_transits = []
            for transit in transits:
                transit_info = {
                    'distance': self._safe_int(transit.get('distance')),
                    'duration': self._safe_int(transit.get('duration')),
                    'walking_distance': self._safe_int(transit.get('walking_distance')),
                    'cost': transit.get('cost', {}),
                    'segments': self._extract_transit_steps(transit.get('segments', []))
                }
                all_transits.append(transit_info)
            
            result['transits'] = all_transits
            result['distance'] = all_transits[0]['distance'] if all_transits else 0
            result['duration'] = all_transits[0]['duration'] if all_transits else 0
            result['steps'] = all_transits[0]['segments'] if all_transits else []
        
        self._save_to_cache(cache_key, result)
        return result
    
    def _extract_driving_steps(self, steps: List[Dict]) -> List[Dict]:
        """提取驾车导航步骤"""
        result = []
        for step in steps:
            result.append({
                'instruction': step.get('instruction', ''),
                'road_name': step.get('road', ''),
                'distance': self._safe_int(step.get('distance')),
                'duration': self._safe_int(step.get('duration')),
                'action': step.get('action', ''),
                'assistant_action': step.get('assistant_action', '')
            })
        return result
    
    def _extract_walking_steps(self, steps: List[Dict]) -> List[Dict]:
        """提取步行导航步骤"""
        result = []
        for step in steps:
            result.append({
                'instruction': step.get('instruction', ''),
                'distance': self._safe_int(step.get('distance')),
                'duration': self._safe_int(step.get('duration')),
                'action': step.get('action', '')
            })
        return result
    
    def _extract_riding_steps(self, steps: List[Dict]) -> List[Dict]:
        """提取骑行导航步骤"""
        result = []
        for step in steps:
            result.append({
                'instruction': step.get('instruction', ''),
                'distance': self._safe_int(step.get('distance')),
                'duration': self._safe_int(step.get('duration')),
                'action': step.get('action', '')
            })
        return result
    
    def _safe_int(self, val, default=0):
        """安全转换为整数"""
        if val is None:
            return default
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str):
            try:
                return int(val)
            except:
                return default
        return default
    
    def _extract_transit_steps(self, segments: List[Dict]) -> List[Dict]:
        """提取公交导航步骤"""
        result = []
        for segment in segments:
            if 'bus' in segment:
                bus = segment['bus']
                buslines = bus.get('buslines', [])
                if buslines and len(buslines) > 0:
                    busline = buslines[0]
                    result.append({
                        'type': 'bus',
                        'line_name': busline.get('name', ''),
                        'departure_stop': busline.get('departure_stop', {}).get('name', ''),
                        'arrival_stop': busline.get('arrival_stop', {}).get('name', ''),
                        'distance': self._safe_int(busline.get('distance')),
                        'duration': self._safe_int(busline.get('duration'))
                    })
            elif 'walking' in segment:
                walking = segment['walking']
                result.append({
                    'type': 'walking',
                    'instruction': walking.get('instruction', ''),
                    'distance': self._safe_int(walking.get('distance')),
                    'duration': self._safe_int(walking.get('duration'))
                })
        return result
    
    async def maps_distance(
        self,
        origins: str,
        destination: str,
        distance_type: str = "1"
    ) -> Dict[str, Any]:
        """
        距离测量
        
        Args:
            origins: 起点坐标，格式 "经度,纬度"，多个用 | 分隔
            destination: 终点坐标，格式 "经度,纬度"，多个用 | 分隔
            distance_type: 1-驾车 3-步行
        
        Returns:
            {'success': True, 'results': list}
        """
        cache_key = self._get_cache_key('distance', origins=origins, destination=destination, type=distance_type)
        cached = self._get_from_cache(cache_key, self._cache_ttl['distance'])
        if cached:
            return cached
        
        url = f"{self.base_url}/distance"
        params = {
            'origins': origins,
            'destination': destination,
            'type': distance_type
        }
        
        result = await self._request(url, params)
        
        if result['success']:
            results = result['data'].get('results', [])
            result['results'] = results
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def maps_distance_matrix(
        self,
        origins: List[str],
        destinations: List[str],
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        批量算路：计算多起点到多终点的距离矩阵
        
        Args:
            origins: 起点坐标列表，每个元素格式 "纬度,经度"
            destinations: 终点坐标列表
            mode: 出行方式 driving/walking
        
        Returns:
            {'success': True, 'matrix': List[List[Dict]]}
        """
        distance_type = "1" if mode == "driving" else "3"
        
        matrix = []
        for i, origin in enumerate(origins):
            origin_str = f"{origin.split(',')[1]},{origin.split(',')[0]}" if ',' in origin else origin
            row = []
            for j, dest in enumerate(destinations):
                dest_str = f"{dest.split(',')[1]},{dest.split(',')[0]}" if ',' in dest else dest
                
                result = await self.maps_distance(origin_str, dest_str, distance_type)
                
                if result['success'] and result.get('results'):
                    info = result['results'][0] if result['results'] else {}
                    row.append({
                        'distance': int(info.get('distance', 0)),
                        'duration': int(info.get('duration', 0))
                    })
                else:
                    row.append({'distance': float('inf'), 'duration': 0})
            matrix.append(row)
        
        return {'success': True, 'matrix': matrix}
    
    async def map_distance_matrix(
        self,
        origins: List[str],
        destinations: List[str],
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        批量算路（兼容旧接口名）
        """
        return await self.maps_distance_matrix(origins, destinations, mode)
    
    async def maps_text_search(
        self,
        keywords: str,
        city: str = None,
        citylimit: bool = False,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        POI关键词搜索
        
        Args:
            keywords: 搜索关键词
            city: 城市名称
            citylimit: 是否限制城市内
            page_size: 返回结果数量
        
        Returns:
            {'success': True, 'places': list}
        """
        cache_key = self._get_cache_key('text_search', keywords=keywords, city=city, citylimit=citylimit)
        cached = self._get_from_cache(cache_key, self._cache_ttl['places'])
        if cached:
            return cached
        
        url = f"{self.base_url}/place/text"
        params = {
            'keywords': keywords,
            'offset': page_size
        }
        if city:
            params['city'] = city
            params['citylimit'] = 'true' if citylimit else 'false'
        
        result = await self._request(url, params)
        
        if result['success']:
            pois = result['data'].get('pois', [])
            places = []
            for poi in pois:
                location = poi.get('location', '').split(',')
                places.append({
                    'name': poi.get('name', ''),
                    'address': poi.get('address', ''),
                    'location': {
                        'lat': float(location[1]) if len(location) == 2 else 0,
                        'lng': float(location[0]) if len(location) == 2 else 0
                    },
                    'type': poi.get('type', ''),
                    'tel': poi.get('tel', ''),
                    'rating': poi.get('biz_ext', {}).get('rating', ''),
                    'cost': poi.get('biz_ext', {}).get('cost', ''),
                    'id': poi.get('id', '')
                })
            result['places'] = places
            result['total'] = int(result['data'].get('count', 0))
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def maps_around_search(
        self,
        keywords: str,
        location: str,
        radius: int = 2000,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        POI周边搜索
        
        Args:
            keywords: 搜索关键词
            location: 中心点坐标，格式 "经度,纬度"
            radius: 搜索半径(米)
            page_size: 返回结果数量
        
        Returns:
            {'success': True, 'places': list}
        """
        cache_key = self._get_cache_key('around_search', keywords=keywords, location=location, radius=radius)
        cached = self._get_from_cache(cache_key, self._cache_ttl['places'])
        if cached:
            return cached
        
        url = f"{self.base_url}/place/around"
        params = {
            'keywords': keywords,
            'location': location,
            'radius': radius,
            'offset': page_size
        }
        
        result = await self._request(url, params)
        
        if result['success']:
            pois = result['data'].get('pois', [])
            places = []
            for poi in pois:
                poi_location = poi.get('location', '').split(',')
                places.append({
                    'name': poi.get('name', ''),
                    'address': poi.get('address', ''),
                    'location': {
                        'lat': float(poi_location[1]) if len(poi_location) == 2 else 0,
                        'lng': float(poi_location[0]) if len(poi_location) == 2 else 0
                    },
                    'distance': int(poi.get('distance', 0)),
                    'type': poi.get('type', ''),
                    'tel': poi.get('tel', ''),
                    'rating': poi.get('biz_ext', {}).get('rating', ''),
                    'cost': poi.get('biz_ext', {}).get('cost', ''),
                    'id': poi.get('id', '')
                })
            result['places'] = places
            result['total'] = int(result['data'].get('count', 0))
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def maps_weather(
        self,
        city: str,
        extensions: str = "base"
    ) -> Dict[str, Any]:
        """
        天气查询
        
        Args:
            city: 城市名称或adcode
            extensions: base-实况天气 all-预报天气
        
        Returns:
            {'success': True, 'weather': dict}
        """
        cache_key = self._get_cache_key('weather', city=city, extensions=extensions)
        cached = self._get_from_cache(cache_key, self._cache_ttl['weather'])
        if cached:
            return cached
        
        url = f"{self.base_url}/weather/weatherInfo"
        params = {
            'city': city,
            'extensions': extensions
        }
        
        result = await self._request(url, params)
        
        if result['success']:
            lives = result['data'].get('lives', [])
            forecasts = result['data'].get('forecasts', [])
            
            if lives:
                result['weather'] = {
                    'type': 'live',
                    'city': lives[0].get('city', ''),
                    'weather': lives[0].get('weather', ''),
                    'temperature': lives[0].get('temperature', ''),
                    'wind_direction': lives[0].get('winddirection', ''),
                    'wind_power': lives[0].get('windpower', ''),
                    'humidity': lives[0].get('humidity', ''),
                    'report_time': lives[0].get('reporttime', '')
                }
            elif forecasts:
                result['weather'] = {
                    'type': 'forecast',
                    'city': forecasts[0].get('city', ''),
                    'casts': forecasts[0].get('casts', [])
                }
        
        self._save_to_cache(cache_key, result)
        return result
    
    async def maps_ip_location(self, ip: str = None) -> Dict[str, Any]:
        """
        IP定位
        
        Args:
            ip: IP地址，不传则定位当前请求IP
        
        Returns:
            {'success': True, 'location': dict}
        """
        url = f"{self.base_url}/ip"
        params = {}
        if ip:
            params['ip'] = ip
        
        result = await self._request(url, params)
        
        if result['success']:
            rectangle = result['data'].get('rectangle', '')
            if isinstance(rectangle, list):
                rectangle = ';'.join(rectangle) if rectangle else ''
            result['location'] = {
                'province': result['data'].get('province', ''),
                'city': result['data'].get('city', ''),
                'adcode': result['data'].get('adcode', ''),
                'rectangle': rectangle
            }
        
        return result
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None


_amap_client: Optional[AmapMCPClient] = None


def get_amap_client() -> AmapMCPClient:
    """获取高德地图客户端单例"""
    global _amap_client
    if _amap_client is None:
        _amap_client = AmapMCPClient()
    return _amap_client
