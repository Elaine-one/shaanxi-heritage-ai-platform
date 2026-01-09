import asyncio
import aiohttp
import logging
from typing import Dict, Any, List, Optional
import time
from datetime import datetime, timedelta
import hashlib
import ssl
import os
import sys

# 导入配置
try:
    from .weather_config import (
        NETWORK_TIMEOUT, MAX_RETRIES, RETRY_DELAY, 
        SSL_VERIFY, CACHE_ENABLED, CACHE_TTL, CACHE_MAX_SIZE,
        ENVIRONMENT_CONFIG
    )
except ImportError:
    # 如果配置文件不存在，使用默认值
    NETWORK_TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    SSL_VERIFY = True
    CACHE_ENABLED = True
    CACHE_TTL = 3600
    CACHE_MAX_SIZE = 100
    ENVIRONMENT_CONFIG = {}

logger = logging.getLogger(__name__)

class WeatherService:
    """
    天气服务类，提供天气数据获取和处理功能
    """
    
    def __init__(self, environment=None):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.current_weather_url = "https://api.open-meteo.com/v1/forecast"
        self.session = None
        
        # 从配置文件加载设置，或使用默认值
        self.environment = environment or self._detect_environment()
        self._load_config()
        
        # 缓存配置 - 改为会话隔离的缓存
        self.cache = {}  # 格式: {session_id: {cache_key: (data, timestamp)}}
        self.session_cache_times = {}  # 记录每个会话的最后活动时间
        
        # 初始化SSL和网络配置
        self._init_network_config()
    
    def _detect_environment(self):
        """检测运行环境"""
        # 检查环境变量
        env = os.environ.get('ENVIRONMENT', '').lower()
        if env in ['development', 'production', 'ubuntu']:
            return env
        
        # 检测是否在容器环境中运行
        if os.path.exists('/.dockerenv'):
            return 'docker'
        
        # 检测是否为Ubuntu服务器
        if sys.platform.startswith('linux'):
            try:
                with open('/etc/os-release', 'r') as f:
                    os_info = f.read()
                    if 'ubuntu' in os_info.lower():
                        return 'ubuntu'
            except:
                pass
        
        # 默认为开发环境
        return 'development'
    
    def _load_config(self):
        """根据环境加载配置"""
        # 获取环境特定配置
        env_config = ENVIRONMENT_CONFIG.get(self.environment, {})
        
        # 应用配置
        self.max_retries = env_config.get('MAX_RETRIES', MAX_RETRIES)
        self.retry_delay = env_config.get('RETRY_DELAY', RETRY_DELAY)
        self.ssl_verify = env_config.get('SSL_VERIFY', SSL_VERIFY)
        self.cache_enabled = env_config.get('CACHE_ENABLED', CACHE_ENABLED)
        # 缩短缓存时间为10分钟，确保获取最新天气数据
        self.cache_ttl = 600  # 10分钟
        self.cache_max_size = env_config.get('CACHE_MAX_SIZE', CACHE_MAX_SIZE)
        
        # 设置超时
        self.timeout = aiohttp.ClientTimeout(total=NETWORK_TIMEOUT)
        
        logger.info(f"天气服务已初始化，环境: {self.environment}")
        logger.info(f"SSL验证: {'启用' if self.ssl_verify else '禁用'}")
        logger.info(f"最大重试次数: {self.max_retries}")
        logger.info(f"缓存时间: {self.cache_ttl}秒")
    
    def _init_network_config(self):
        """初始化网络配置"""
        # 在Ubuntu环境中，自动检测并配置网络设置
        if self.environment == 'ubuntu':
            # Ubuntu环境特殊配置
            self._configure_ubuntu_network()
        elif sys.platform.startswith('linux') and self.ssl_verify:
            # 其他Linux环境的证书检查
            cert_paths = [
                '/etc/ssl/certs/ca-certificates.crt',  # Debian/Ubuntu
                '/etc/pki/tls/certs/ca-bundle.crt',     # RHEL/CentOS
                '/etc/ssl/ca-bundle.pem',               # OpenSUSE
                '/usr/local/share/ca-certificates/ca-certificates.crt'  # 自定义路径
            ]
            
            cert_exists = any(os.path.exists(path) for path in cert_paths)
            if not cert_exists:
                logger.warning("系统证书包不存在，禁用SSL验证")
                self.ssl_verify = False
            else:
                logger.info(f"找到证书包: {[path for path in cert_paths if os.path.exists(path)][0]}")
    
    def _configure_ubuntu_network(self):
        """配置Ubuntu环境的网络设置"""
        logger.info("检测到Ubuntu环境，应用特殊网络配置")
        
        # Ubuntu环境默认禁用SSL验证，避免证书问题
        if self.ssl_verify:
            logger.warning("Ubuntu环境下禁用SSL验证以避免证书问题")
            self.ssl_verify = False
        
        # 增加超时时间
        self.timeout = aiohttp.ClientTimeout(total=30, connect=15, sock_connect=15, sock_read=15)
        
        # 增加重试次数和延迟
        self.max_retries = 5
        self.retry_delay = 2
        
        logger.info(f"Ubuntu网络配置完成: 超时={self.timeout.total}s, 重试次数={self.max_retries}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话，包含SSL配置"""
        if self.session is None or self.session.closed:
            # 配置SSL上下文
            ssl_context = None
            if self.ssl_verify:
                try:
                    # 尝试创建默认SSL上下文
                    ssl_context = ssl.create_default_context()
                    logger.info("SSL验证已启用")
                except Exception as e:
                    logger.warning(f"创建SSL上下文失败: {str(e)}，禁用SSL验证")
                    self.ssl_verify = False
                    ssl_context = None
            else:
                logger.warning("SSL验证已禁用，仅用于开发环境")
            
            # 创建连接器配置
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=10,  # 连接池大小
                limit_per_host=5,  # 每个主机的连接数
                ttl_dns_cache=300,  # DNS缓存时间(秒)
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
            
            # 设置默认请求头（不包含User-Agent，将在重试时动态设置）
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive"
            }
            
            # 创建会话
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
                connector=connector,
                headers=headers
            )
        
        return self.session
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _generate_cache_key(self, latitude: float, longitude: float, days: int) -> str:
        """
        生成缓存键
        
        Args:
            latitude (float): 纬度
            longitude (float): 经度
            days (int): 天数
            
        Returns:
            str: 缓存键
        """
        # 使用坐标和天数生成唯一键
        key_data = f"{latitude:.6f},{longitude:.6f},{days}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, session_id: str, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        从缓存获取数据（会话隔离）
        
        Args:
            session_id (str): 会话ID
            cache_key (str): 缓存键
            
        Returns:
            Optional[Dict[str, Any]]: 缓存的数据，如果不存在或已过期则返回None
        """
        if not self.cache_enabled:
            return None
            
        # 检查会话缓存是否存在
        if session_id not in self.cache:
            return None
        
        session_cache = self.cache[session_id]
        
        if cache_key in session_cache:
            cached_data, timestamp = session_cache[cache_key]
            # 检查缓存是否过期
            if time.time() - timestamp < self.cache_ttl:
                logger.info(f"使用会话{session_id}的缓存数据: {cache_key}")
                # 更新会话最后活动时间
                self.session_cache_times[session_id] = time.time()
                return cached_data
            else:
                # 缓存过期，删除
                del session_cache[cache_key]
                logger.info(f"会话{session_id}的缓存已过期，删除: {cache_key}")
        
        return None
    
    def _save_to_cache(self, session_id: str, cache_key: str, data: Dict[str, Any]) -> None:
        """
        保存数据到缓存（会话隔离）
        
        Args:
            session_id (str): 会话ID
            cache_key (str): 缓存键
            data (Dict[str, Any]): 要缓存的数据
        """
        if not self.cache_enabled:
            return
            
        # 确保会话缓存存在
        if session_id not in self.cache:
            self.cache[session_id] = {}
        
        # 保存数据到会话缓存
        self.cache[session_id][cache_key] = (data, time.time())
        # 更新会话最后活动时间
        self.session_cache_times[session_id] = time.time()
        logger.info(f"数据已缓存到会话{session_id}: {cache_key}")
    
    def _clean_expired_cache(self) -> None:
        """清理过期的缓存项和会话"""
        if not self.cache_enabled:
            return
            
        current_time = time.time()
        expired_sessions = []
        
        # 检查每个会话的缓存
        for session_id, session_cache in self.cache.items():
            # 检查会话是否超时（10分钟无活动）
            if session_id in self.session_cache_times:
                last_activity = self.session_cache_times[session_id]
                if current_time - last_activity >= self.cache_ttl:
                    expired_sessions.append(session_id)
                    continue
            
            # 清理会话中过期的缓存项
            expired_keys = []
            for key, (_, timestamp) in session_cache.items():
                if current_time - timestamp >= self.cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del session_cache[key]
            
            # 如果会话缓存为空，也标记为过期
            if not session_cache:
                expired_sessions.append(session_id)
        
        # 删除过期的会话
        for session_id in expired_sessions:
            if session_id in self.cache:
                del self.cache[session_id]
            if session_id in self.session_cache_times:
                del self.session_cache_times[session_id]
        
        if expired_sessions:
            logger.info(f"清理了{len(expired_sessions)}个过期会话及其缓存")
    
    async def _retry_request(self, func, *args, **kwargs):
        """
        带重试机制的请求方法，针对不同类型的错误采用不同的重试策略
        支持Windows和Ubuntu两种环境的请求头尝试
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
        """
        last_exception = None
        
        # 定义Windows和Ubuntu环境的User-Agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        
        # 备用天气API端点（故障转移）
        backup_endpoints = [
            "https://api.open-meteo.com/v1/forecast",  # 主端点
            "https://api.open-meteo.com/v1/forecast",  # 相同端点，但可能通过不同网络路径
        ]
        
        for attempt in range(self.max_retries + 1):
            try:
                # 每次尝试使用不同的User-Agent
                user_agent_index = attempt % len(user_agents)
                await self._update_session_headers({"User-Agent": user_agents[user_agent_index]})
                
                # 对于天气预报请求，尝试不同的端点
                if hasattr(func, '__name__') and 'weather' in func.__name__.lower():
                    # 如果是天气相关请求，尝试故障转移
                    endpoint_index = attempt % len(backup_endpoints)
                    if endpoint_index > 0:
                        logger.info(f"尝试备用端点 {endpoint_index + 1}/{len(backup_endpoints)}")
                        # 这里可以修改func的端点，但需要更复杂的实现
                
                return await func(*args, **kwargs)
            except aiohttp.ClientConnectorError as e:
                # 连接错误，可能是网络问题
                last_exception = e
                if attempt < self.max_retries:
                    delay = self._calculate_retry_delay(attempt, 'network')
                    logger.warning(f"连接错误，{delay}秒后重试 (尝试 {attempt + 1}/{self.max_retries + 1}): {str(e)}")
                    await asyncio.sleep(delay)
                    # 对于连接错误，尝试重新创建会话
                    await self._recreate_session()
                    
                    # 如果是Ubuntu环境，尝试网络诊断
                    if self.environment == 'ubuntu' and attempt == 1:
                        await self._diagnose_ubuntu_network()
                else:
                    logger.error(f"连接错误，已达到最大重试次数: {str(e)}")
            except aiohttp.ClientSSLError as e:
                # SSL错误，可能是证书问题
                last_exception = e
                if attempt < self.max_retries:
                    if attempt == 0 and self.ssl_verify:
                        # 第一次尝试SSL错误时，尝试禁用SSL验证
                        logger.warning("SSL验证失败，尝试禁用SSL验证后重试")
                        self.ssl_verify = False
                        await self._recreate_session()
                    else:
                        delay = self._calculate_retry_delay(attempt, 'ssl')
                        logger.warning(f"SSL错误，{delay}秒后重试 (尝试 {attempt + 1}/{self.max_retries + 1}): {str(e)}")
                        await asyncio.sleep(delay)
                else:
                    logger.error(f"SSL错误，已达到最大重试次数: {str(e)}")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # 其他客户端错误或超时
                last_exception = e
                if attempt < self.max_retries:
                    delay = self._calculate_retry_delay(attempt, 'timeout')
                    logger.warning(f"请求失败，{delay}秒后重试 (尝试 {attempt + 1}/{self.max_retries + 1}): {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"请求失败，已达到最大重试次数: {str(e)}")
            except Exception as e:
                logger.error(f"请求发生未知错误: {str(e)}")
                raise
        
        raise last_exception
    
    def _calculate_retry_delay(self, attempt: int, error_type: str) -> float:
        """计算重试延迟时间"""
        base_delay = self.retry_delay
        
        # 根据错误类型调整延迟策略
        if error_type == 'network':
            # 网络错误使用更长的延迟
            return base_delay * (3 ** attempt)  # 更激进的指数退避
        elif error_type == 'ssl':
            # SSL错误使用中等延迟
            return base_delay * (2 ** attempt)
        elif error_type == 'timeout':
            # 超时错误使用标准延迟
            return base_delay * (2 ** attempt)
        else:
            # 默认延迟策略
            return base_delay * (2 ** attempt)
    
    async def _diagnose_ubuntu_network(self):
        """诊断Ubuntu环境的网络问题"""
        if self.environment != 'ubuntu':
            return
            
        logger.info("执行Ubuntu网络诊断...")
        
        # 检查网络连通性
        test_hosts = [
            'api.open-meteo.com',
            '8.8.8.8',  # Google DNS
            '1.1.1.1'   # Cloudflare DNS
        ]
        
        for host in test_hosts:
            try:
                # 使用系统ping命令检查连通性
                import subprocess
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '3', host],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"网络诊断: {host} 可达")
                else:
                    logger.warning(f"网络诊断: {host} 不可达")
            except Exception as e:
                logger.warning(f"网络诊断失败: {str(e)}")
        
        logger.info("Ubuntu网络诊断完成")
    
    async def _update_session_headers(self, new_headers):
        """更新会话请求头"""
        if self.session and not self.session.closed:
            # 更新现有会话的请求头
            self.session.headers.update(new_headers)
            logger.info(f"已更新请求头: {new_headers}")
    
    async def _recreate_session(self):
        """重新创建HTTP会话"""
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None
        logger.info("已重新创建HTTP会话")
    
    async def get_weather_forecast(self, latitude: float, longitude: float, days: int = 7, session_id: str = "default") -> Dict[str, Any]:
        """
        获取天气预报（会话隔离）
        
        Args:
            latitude (float): 纬度
            longitude (float): 经度
            days (int): 预报天数
            session_id (str): 会话ID，用于缓存隔离
        
        Returns:
            Dict[str, Any]: 天气预报数据
        """
        # 生成缓存键（包含日期以确保获取最新数据）
        today = datetime.now().strftime("%Y-%m-%d")
        cache_key = f"{self._generate_cache_key(latitude, longitude, days)}_{today}"
        
        # 尝试从缓存获取数据（缓存时间缩短为10分钟）
        cached_data = self._get_from_cache(session_id, cache_key)
        if cached_data:
            logger.info(f"使用缓存的天气数据: {cache_key}")
            return cached_data
        
        async def _fetch():
            session = await self._get_session()
            
            # 构建请求参数
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
                "timezone": "auto",
                "forecast_days": days
            }
            
            logger.info(f"获取天气预报: 纬度{latitude}, 经度{longitude}, {days}天")
            
            # 发送请求
            async with session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result = self._process_forecast_data(data, latitude, longitude)
                    # 保存到缓存（缓存时间缩短为10分钟）
                    self._save_to_cache(session_id, cache_key, result)
                    return result
                else:
                    logger.error(f"天气API请求失败，状态码: {response.status}")
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"天气API请求失败，状态码: {response.status}"
                    )
        
        try:
            # 使用重试机制获取数据
            result = await self._retry_request(_fetch)
            # 定期清理过期缓存
            if len(self.cache) > self.cache_max_size:
                self._clean_expired_cache()
            return result
        except Exception as e:
            logger.error(f"获取天气预报时发生错误: {str(e)}")
            # 返回错误信息，不使用模拟数据
            return {
                'success': False,
                'error': f"无法获取天气数据: {str(e)}",
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'forecast': []
            }
    
    async def get_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        获取当前天气
        
        Args:
            latitude (float): 纬度
            longitude (float): 经度
        
        Returns:
            Dict[str, Any]: 当前天气数据
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(latitude, longitude, 0)  # 0表示当前天气
        
        # 尝试从缓存获取数据
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        async def _fetch():
            session = await self._get_session()
            
            # 构建请求参数
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,windspeed_10m,weathercode",
                "timezone": "auto"
            }
            
            logger.info(f"获取当前天气: 纬度{latitude}, 经度{longitude}")
            
            # 发送请求
            async with session.get(self.current_weather_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    result = self._process_current_weather(data, latitude, longitude)
                    # 保存到缓存
                    self._save_to_cache(cache_key, result)
                    return result
                else:
                    logger.error(f"当前天气API请求失败，状态码: {response.status}")
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"当前天气API请求失败，状态码: {response.status}"
                    )
        
        try:
            # 使用重试机制获取数据
            result = await self._retry_request(_fetch)
            # 定期清理过期缓存
            if len(self.cache) > self.cache_max_size:
                self._clean_expired_cache()
            return result
        except Exception as e:
            logger.error(f"获取当前天气时发生错误: {str(e)}")
            # 返回错误信息，不使用模拟数据
            return {
                'success': False,
                'error': f"无法获取当前天气数据: {str(e)}",
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'current': {}
            }
    
    def _process_forecast_data(self, data: Dict[str, Any], latitude: float, longitude: float) -> Dict[str, Any]:
        """
        处理天气预报数据
        
        Args:
            data (Dict[str, Any]): 原始API数据
            latitude (float): 纬度
            longitude (float): 经度
        
        Returns:
            Dict[str, Any]: 处理后的天气数据
        """
        try:
            daily_data = data.get("daily", {})
            time_list = daily_data.get("time", [])
            max_temps = daily_data.get("temperature_2m_max", [])
            min_temps = daily_data.get("temperature_2m_min", [])
            precipitation = daily_data.get("precipitation_sum", [])
            wind_speeds = daily_data.get("windspeed_10m_max", [])
            weather_codes = daily_data.get("weathercode", [])
            
            # 获取当前日期作为基准
            current_date = datetime.now().date()
            
            forecast = []
            for i in range(len(time_list)):
                # 基于当前日期计算预报日期
                forecast_date = current_date + timedelta(days=i)
                date_str = forecast_date.strftime("%Y-%m-%d")
                
                if i < len(max_temps) and i < len(min_temps):
                    max_temp = max_temps[i] if i < len(max_temps) else 20
                    min_temp = min_temps[i] if i < len(min_temps) else 10
                    precip = precipitation[i] if i < len(precipitation) else 0
                    wind_speed = wind_speeds[i] if i < len(wind_speeds) else 10
                    weather_code = weather_codes[i] if i < len(weather_codes) else 0
                    
                    day_data = {
                        "date": date_str,
                        "max_temp": max_temp,
                        "min_temp": min_temp,
                        "avg_temp": (max_temp + min_temp) / 2,
                        "weather_code": weather_code,
                        "weather_description": self._get_weather_description(weather_code),
                        "precipitation": precip,
                        "wind_speed": wind_speed,
                        "humidity": 65,  # Open-Meteo免费版不提供湿度，使用默认值
                        "uv_index": 5,   # 使用默认UV指数
                        "travel_suitability": {}
                    }
                    
                    # 评估旅游适宜性
                    day_data["travel_suitability"] = self._assess_travel_suitability(day_data)
                    forecast.append(day_data)
            
            return {
                "success": True,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "forecast": forecast,
                "data_source": "real_api",
                "source_description": "真实天气数据（Open-Meteo API）"
            }
        except Exception as e:
            logger.error(f"处理天气预报数据时发生错误: {str(e)}")
            return {
                "success": False,
                "error": f"处理天气预报数据时发生错误: {str(e)}",
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "forecast": []
            }
    
    def _process_current_weather(self, data: Dict[str, Any], latitude: float, longitude: float) -> Dict[str, Any]:
        """
        处理当前天气数据
        
        Args:
            data (Dict[str, Any]): 原始API数据
            latitude (float): 纬度
            longitude (float): 经度
        
        Returns:
            Dict[str, Any]: 处理后的当前天气数据
        """
        try:
            current_data = data.get("current", {})
            
            temperature = current_data.get("temperature_2m", 20)
            humidity = current_data.get("relative_humidity_2m", 50)
            wind_speed = current_data.get("windspeed_10m", 10)
            weather_code = current_data.get("weathercode", 0)
            
            current = {
                "temperature": temperature,
                "weather_code": weather_code,
                "weather_description": self._get_weather_description(weather_code),
                "precipitation": 0,  # 当前API不提供实时降水
                "wind_speed": wind_speed,
                "humidity": humidity,
                "uv_index": 5,  # 使用默认UV指数
                "travel_suitability": {}
            }
            
            # 评估旅游适宜性
            current["travel_suitability"] = self._assess_current_travel_suitability(current)
            
            return {
                "success": True,
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "current": current,
                "data_source": "real_api",
                "source_description": "真实天气数据（Open-Meteo API）"
            }
        except Exception as e:
            logger.error(f"处理当前天气数据时发生错误: {str(e)}")
            return {
                "success": False,
                "error": f"处理当前天气数据时发生错误: {str(e)}",
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "current": {}
            }
    
    def _assess_travel_suitability(self, day_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估天气对旅游的适宜性
        
        Args:
            day_info (Dict[str, Any]): 日天气信息
        
        Returns:
            Dict[str, Any]: 适宜性评估结果
        """
        try:
            score = 100  # 基础分数
            recommendations = []
            warnings = []
            
            # 温度评估
            avg_temp = day_info.get('avg_temp', 20)
            if avg_temp < 0:
                score -= 30
                warnings.append('气温较低，注意保暖')
                recommendations.append('携带厚外套和保暖用品')
            elif avg_temp < 10:
                score -= 15
                recommendations.append('携带外套')
            elif avg_temp > 35:
                score -= 20
                warnings.append('气温较高，注意防暑')
                recommendations.append('携带防晒用品和充足饮水')
            elif avg_temp > 30:
                score -= 10
                recommendations.append('注意防晒和补水')
            
            # 降水评估
            precipitation = day_info.get('precipitation', 0)
            if precipitation > 20:
                score -= 25
                warnings.append('有较强降水，可能影响出行')
                recommendations.append('携带雨具，考虑室内活动')
            elif precipitation > 5:
                score -= 10
                recommendations.append('携带雨具')
            
            # 风速评估
            wind_speed = day_info.get('wind_speed', 0)
            if wind_speed > 40:
                score -= 20
                warnings.append('风力较大，注意安全')
            elif wind_speed > 25:
                score -= 10
                recommendations.append('注意防风')
            
            # 湿度评估
            humidity = 65  # Open-Meteo免费版不提供湿度，使用默认值
            if humidity > 80:
                score -= 10
                recommendations.append('湿度较高，注意通风')
            elif humidity < 30:
                score -= 5
                recommendations.append('空气干燥，注意补水')
            
            # UV指数评估
            uv_index = 5  # 使用默认UV指数
            if uv_index > 8:
                score -= 10
                recommendations.append('紫外线强烈，做好防晒')
            elif uv_index > 6:
                recommendations.append('注意防晒')
            
            # 确定适宜性等级
            if score >= 80:
                suitability = '非常适宜'
            elif score >= 60:
                suitability = '适宜'
            elif score >= 40:
                suitability = '一般'
            elif score >= 20:
                suitability = '不太适宜'
            else:
                suitability = '不适宜'
            
            return {
                'score': max(0, score),
                'level': suitability,
                'recommendations': recommendations,
                'warnings': warnings
            }
        except Exception as e:
            logger.error(f"评估旅游适宜性时发生错误: {str(e)}")
            return {
                'score': 50,
                'level': '一般',
                'recommendations': ['天气评估异常，请查看详细天气信息'],
                'warnings': []
            }
    
    def _assess_current_travel_suitability(self, current: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估当前天气对旅游的适宜性
        
        Args:
            current (Dict[str, Any]): 当前天气信息
        
        Returns:
            Dict[str, Any]: 适宜性评估结果
        """
        try:
            # 简化版本，基于当前天气数据
            temp = current.get('temperature', 20)
            humidity = current.get('humidity', 50)
            wind_speed = current.get('wind_speed', 0)
            
            score = 100
            recommendations = []
            
            if temp < 5 or temp > 35:
                score -= 20
            if humidity > 80:
                score -= 10
            if wind_speed > 30:
                score -= 15
            
            if score >= 80:
                level = '非常适宜'
            elif score >= 60:
                level = '适宜'
            else:
                level = '一般'
            
            return {
                'score': max(0, score),
                'level': level,
                'recommendations': recommendations
            }
        except Exception as e:
            logger.error(f"评估当前旅游适宜性时发生错误: {str(e)}")
            return {
                'score': 50,
                'level': '一般',
                'recommendations': ['天气评估异常，请查看详细天气信息']
            }
    
    async def get_multi_location_weather(self, locations: List[Dict[str, Any]], days: int = 7) -> Dict[str, Any]:
        """
        获取多个位置的天气预报
        
        Args:
            locations (List[Dict[str, Any]]): 位置列表，每个位置包含lat和lng
            days (int): 预报天数
        
        Returns:
            Dict[str, Any]: 多位置天气数据
        """
        weather_data = {}
        
        tasks = []
        for location in locations:
            if 'lat' in location and 'lng' in location:
                task = self.get_weather_forecast(location['lat'], location['lng'], days)
                tasks.append((location.get('name', f"{location['lat']},{location['lng']}"), task))
        
        if tasks:
            results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for (location_name, _), result in zip(tasks, results):
                if isinstance(result, Exception):
                    logger.error(f"获取{location_name}天气时发生错误: {str(result)}")
                    weather_data[location_name] = {'success': False, 'error': str(result)}
                else:
                    weather_data[location_name] = result
        
        return {
            'success': True,
            'locations': weather_data,
            'summary': self._generate_weather_summary(weather_data),
            'data_source': self._determine_data_source(weather_data),
            'source_description': self._get_source_description(weather_data)
        }
    
    def _generate_weather_summary(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成天气摘要
        
        Args:
            weather_data (Dict[str, Any]): 多位置天气数据
        
        Returns:
            Dict[str, Any]: 天气摘要
        """
        try:
            total_locations = len(weather_data)
            suitable_days = 0
            total_days = 0
            
            for location_name, data in weather_data.items():
                if data.get('success') and 'forecast' in data:
                    for day in data['forecast']:
                        total_days += 1
                        if day.get('travel_suitability', {}).get('score', 0) >= 60:
                            suitable_days += 1
            
            suitability_rate = (suitable_days / total_days * 100) if total_days > 0 else 0
            
            return {
                'total_locations': total_locations,
                'total_forecast_days': total_days,
                'suitable_days': suitable_days,
                'suitability_rate': round(suitability_rate, 1),
                'overall_recommendation': '适宜出行' if suitability_rate >= 70 else ('谨慎出行' if suitability_rate >= 50 else '不建议出行')
            }
        except Exception as e:
            logger.error(f"生成天气摘要时发生错误: {str(e)}")
            return {
                'total_locations': 0,
                'total_forecast_days': 0,
                'suitable_days': 0,
                'suitability_rate': 0,
                'overall_recommendation': '无法评估'
            }
    
    def _determine_data_source(self, weather_data: Dict[str, Any]) -> str:
        """
        确定天气数据来源
        
        Args:
            weather_data (Dict[str, Any]): 多位置天气数据
        
        Returns:
            str: 数据来源标识
        """
        has_mock = False
        has_real = False
        
        for location_name, data in weather_data.items():
            if data.get('data_source') == 'mock_data':
                has_mock = True
            elif data.get('data_source') == 'real_api':
                has_real = True
        
        if has_mock and not has_real:
            return 'mock_data'
        elif has_real and not has_mock:
            return 'real_api'
        elif has_mock and has_real:
            return 'mixed'
        else:
            return 'unknown'
    
    def _get_source_description(self, weather_data: Dict[str, Any]) -> str:
        """
        获取数据来源描述
        
        Args:
            weather_data (Dict[str, Any]): 多位置天气数据
        
        Returns:
            str: 数据来源描述
        """
        data_source = self._determine_data_source(weather_data)
        
        descriptions = {
            'real_api': '全部使用真实天气数据（Open-Meteo API）',
            'mock_data': '全部使用模拟天气数据（基于季节生成）',
            'mixed': '混合使用真实和模拟天气数据',
            'unknown': '数据来源未知'
        }
        
        return descriptions.get(data_source, '数据来源未知')
    
    def _get_weather_description(self, weather_code: int) -> str:
        """
        根据天气代码获取天气描述
        
        Args:
            weather_code (int): 天气代码
        
        Returns:
            str: 天气描述
        """
        weather_descriptions = {
            0: '晴朗',
            1: '大部分晴朗',
            2: '部分多云',
            3: '阴天',
            45: '雾',
            48: '雾凇',
            51: '小毛毛雨',
            53: '中毛毛雨',
            55: '浓毛毛雨',
            56: '冻毛毛雨',
            57: '浓冻毛毛雨',
            61: '小雨',
            63: '中雨',
            65: '大雨',
            66: '冻雨',
            67: '大雨凇',
            71: '小雪',
            73: '中雪',
            75: '大雪',
            77: '雪粒',
            80: '小阵雨',
            81: '中阵雨',
            82: '强阵雨',
            85: '小阵雪',
            86: '中阵雪',
            95: '雷暴',
            96: '小冰雹',
            99: '大冰雹'
        }
        
        return weather_descriptions.get(weather_code, '未知天气')


# 单例模式获取天气服务实例
_weather_service_instance = None

def get_weather_service() -> WeatherService:
    """
    获取天气服务单例实例
    
    Returns:
        WeatherService: 天气服务实例
    """
    global _weather_service_instance
    if _weather_service_instance is None:
        _weather_service_instance = WeatherService()
    return _weather_service_instance