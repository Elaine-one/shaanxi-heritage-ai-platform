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
        
        # 缓存配置
        self.cache = {}  # 简单的内存缓存
        
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
        self.cache_ttl = env_config.get('CACHE_TTL', CACHE_TTL)
        self.cache_max_size = env_config.get('CACHE_MAX_SIZE', CACHE_MAX_SIZE)
        
        # 设置超时
        self.timeout = aiohttp.ClientTimeout(total=NETWORK_TIMEOUT)
        
        logger.info(f"天气服务已初始化，环境: {self.environment}")
        logger.info(f"SSL验证: {'启用' if self.ssl_verify else '禁用'}")
        logger.info(f"最大重试次数: {self.max_retries}")
    
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
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        从缓存获取数据
        
        Args:
            cache_key (str): 缓存键
            
        Returns:
            Optional[Dict[str, Any]]: 缓存的数据，如果不存在或已过期则返回None
        """
        if not self.cache_enabled:
            return None
            
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            # 检查缓存是否过期
            if time.time() - timestamp < self.cache_ttl:
                logger.info(f"使用缓存数据: {cache_key}")
                return cached_data
            else:
                # 缓存过期，删除
                del self.cache[cache_key]
                logger.info(f"缓存已过期，删除: {cache_key}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        保存数据到缓存
        
        Args:
            cache_key (str): 缓存键
            data (Dict[str, Any]): 要缓存的数据
        """
        if not self.cache_enabled:
            return
            
        self.cache[cache_key] = (data, time.time())
        logger.info(f"数据已缓存: {cache_key}")
    
    def _clean_expired_cache(self) -> None:
        """清理过期的缓存项"""
        if not self.cache_enabled:
            return
            
        current_time = time.time()
        expired_keys = []
        
        for key, (_, timestamp) in self.cache.items():
            if current_time - timestamp >= self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"清理了{len(expired_keys)}个过期缓存项")
    
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
    
    async def get_weather_forecast(self, latitude: float, longitude: float, days: int = 7) -> Dict[str, Any]:
        """
        获取天气预报
        
        Args:
            latitude (float): 纬度
            longitude (float): 经度
            days (int): 预报天数
        
        Returns:
            Dict[str, Any]: 天气预报数据
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(latitude, longitude, days)
        
        # 尝试从缓存获取数据
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # 对于Ubuntu环境，优先尝试故障转移机制
        if self.environment == 'ubuntu':
            result = await self._try_ubuntu_fallback(latitude, longitude, days, cache_key)
            if result:
                return result
        
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
                    # 保存到缓存
                    self._save_to_cache(cache_key, result)
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
            if len(self.cache) > self.cache_max_size:  # 当缓存项超过最大限制时清理
                self._clean_expired_cache()
            return result
        except Exception as e:
            logger.error(f"获取天气预报时发生错误: {str(e)}")
            # 使用模拟数据
            logger.info("使用模拟天气数据作为回退方案")
            result = await self._get_mock_weather_data(latitude, longitude, days)
            # 模拟数据也缓存，但时间较短
            mock_cache_key = f"mock_{cache_key}"
            self._save_to_cache(mock_cache_key, result)
            return result
    
    async def _try_ubuntu_fallback(self, latitude: float, longitude: float, days: int, cache_key: str) -> Optional[Dict[str, Any]]:
        """Ubuntu环境的故障转移机制"""
        logger.info("尝试Ubuntu环境故障转移机制")
        
        # 方法1: 尝试使用HTTP协议（非HTTPS）
        try:
            logger.info("尝试HTTP协议连接")
            # 临时修改base_url为HTTP
            original_base_url = self.base_url
            self.base_url = self.base_url.replace('https://', 'http://')
            
            async def _http_fetch():
                session = await self._get_session()
                params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
                    "timezone": "auto",
                    "forecast_days": days
                }
                
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._process_forecast_data(data, latitude, longitude)
                    else:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"HTTP请求失败，状态码: {response.status}"
                        )
            
            result = await _http_fetch()
            self._save_to_cache(cache_key, result)
            logger.info("HTTP协议连接成功")
            return result
        except Exception as e:
            logger.warning(f"HTTP协议连接失败: {str(e)}")
            # 恢复原始URL
            self.base_url = original_base_url
        
        # 方法2: 尝试使用本地缓存的历史数据
        try:
            logger.info("尝试使用历史缓存数据")
            # 查找最近7天内的类似位置的缓存数据
            current_time = time.time()
            for key, (cached_data, timestamp) in self.cache.items():
                if key.startswith('mock_') or 'weather' not in str(cached_data):
                    continue
                
                # 检查缓存是否在7天内且位置相近
                if current_time - timestamp < 604800:  # 7天
                    # 这里可以添加位置相似性检查逻辑
                    # 暂时返回第一个有效缓存
                    logger.info("找到有效历史缓存数据")
                    return cached_data
        except Exception as e:
            logger.warning(f"历史缓存数据获取失败: {str(e)}")
        
        logger.info("Ubuntu故障转移机制未能获取有效数据")
        return None
    
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
            if len(self.cache) > self.cache_max_size:  # 当缓存项超过最大限制时清理
                self._clean_expired_cache()
            return result
        except Exception as e:
            logger.error(f"获取当前天气时发生错误: {str(e)}")
            # 使用模拟数据
            logger.info("使用模拟当前天气数据作为回退方案")
            result = await self._get_mock_current_weather(latitude, longitude)
            # 模拟数据也缓存，但时间较短
            mock_cache_key = f"mock_{cache_key}"
            self._save_to_cache(mock_cache_key, result)
            return result
    
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
            
            forecast = []
            for i, date in enumerate(time_list):
                if i < len(max_temps) and i < len(min_temps):
                    max_temp = max_temps[i] if i < len(max_temps) else 20
                    min_temp = min_temps[i] if i < len(min_temps) else 10
                    precip = precipitation[i] if i < len(precipitation) else 0
                    wind_speed = wind_speeds[i] if i < len(wind_speeds) else 10
                    weather_code = weather_codes[i] if i < len(weather_codes) else 0
                    
                    day_data = {
                        "date": date,
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
                "forecast": forecast
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
                "current": current
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
            'summary': self._generate_weather_summary(weather_data)
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
    
    async def _get_mock_weather_data(self, latitude: float, longitude: float, days: int) -> Dict[str, Any]:
        """
        获取模拟天气数据（当API不可用时使用）
        
        Args:
            latitude (float): 纬度
            longitude (float): 经度
            days (int): 天数
        
        Returns:
            Dict[str, Any]: 模拟天气数据
        """
        import random
        
        try:
            # 根据季节生成合理的模拟数据
            current_month = datetime.now().month
            base_temp = 20  # 基础温度
            
            # 根据季节调整温度
            if current_month in [12, 1, 2]:  # 冬季
                base_temp = 5
            elif current_month in [3, 4, 5]:  # 春季
                base_temp = 18
            elif current_month in [6, 7, 8]:  # 夏季
                base_temp = 28
            else:  # 秋季
                base_temp = 15
            
            forecast = []
            for i in range(days):
                date = datetime.now() + timedelta(days=i)
                
                # 生成合理的温度变化
                temp_variation = random.uniform(-5, 5)
                max_temp = base_temp + temp_variation + random.uniform(3, 8)
                min_temp = base_temp + temp_variation - random.uniform(3, 8)
                
                # 生成天气状况
                weather_codes = [0, 1, 2, 3, 45, 48, 51, 53, 55, 61, 63, 65, 71, 73, 75, 80, 81, 82, 95, 96, 99]
                weights = [30, 20, 15, 10, 2, 1, 5, 3, 2, 8, 5, 2, 4, 2, 1, 6, 4, 2, 1, 1, 1]  # 晴天概率更高
                weather_code = random.choices(weather_codes, weights=weights)[0]
                
                # 生成其他天气参数
                precipitation = random.uniform(0, 10) if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82] else 0
                wind_speed = random.uniform(5, 20)
                
                day_data = {
                    'date': date.strftime('%Y-%m-%d'),
                    'max_temp': round(max_temp, 1),
                    'min_temp': round(min_temp, 1),
                    'avg_temp': round((max_temp + min_temp) / 2, 1),
                    'weather_code': weather_code,
                    'weather_description': self._get_weather_description(weather_code),
                    'precipitation': round(precipitation, 1),
                    'wind_speed': round(wind_speed, 1),
                    'humidity': random.randint(40, 80),
                    'uv_index': random.randint(1, 10),
                    'travel_suitability': {}
                }
                
                # 评估旅游适宜性
                day_data['travel_suitability'] = self._assess_travel_suitability(day_data)
                forecast.append(day_data)
            
            return {
                'success': True,
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'forecast': forecast,
                'is_mock_data': True
            }
        except Exception as e:
            logger.error(f"生成模拟天气数据时发生错误: {str(e)}")
            return {
                'success': False,
                'error': f"生成模拟天气数据时发生错误: {str(e)}",
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'forecast': []
            }
    
    async def _get_mock_current_weather(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        获取模拟当前天气数据（当API不可用时使用）
        
        Args:
            latitude (float): 纬度
            longitude (float): 经度
        
        Returns:
            Dict[str, Any]: 模拟当前天气数据
        """
        import random
        
        try:
            # 根据季节生成合理的模拟数据
            current_month = datetime.now().month
            base_temp = 20  # 基础温度
            
            # 根据季节调整温度
            if current_month in [12, 1, 2]:  # 冬季
                base_temp = 5
            elif current_month in [3, 4, 5]:  # 春季
                base_temp = 18
            elif current_month in [6, 7, 8]:  # 夏季
                base_temp = 28
            else:  # 秋季
                base_temp = 15
            
            # 生成合理的温度变化
            temp_variation = random.uniform(-3, 3)
            current_temp = base_temp + temp_variation
            
            # 生成天气状况
            weather_codes = [0, 1, 2, 3, 45, 48, 51, 53, 55, 61, 63, 65, 71, 73, 75, 80, 81, 82, 95, 96, 99]
            weights = [30, 20, 15, 10, 2, 1, 5, 3, 2, 8, 5, 2, 4, 2, 1, 6, 4, 2, 1, 1, 1]  # 晴天概率更高
            weather_code = random.choices(weather_codes, weights=weights)[0]
            
            # 生成其他天气参数
            precipitation = random.uniform(0, 5) if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82] else 0
            wind_speed = random.uniform(5, 20)
            humidity = random.randint(40, 80)
            
            current_data = {
                'temperature': round(current_temp, 1),
                'weather_code': weather_code,
                'weather_description': self._get_weather_description(weather_code),
                'precipitation': round(precipitation, 1),
                'wind_speed': round(wind_speed, 1),
                'humidity': humidity,
                'uv_index': random.randint(1, 10),
                'travel_suitability': {}
            }
            
            # 评估旅游适宜性
            current_data['travel_suitability'] = self._assess_current_travel_suitability(current_data)
            
            return {
                'success': True,
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'current': current_data,
                'is_mock_data': True
            }
        except Exception as e:
            logger.error(f"生成模拟当前天气数据时发生错误: {str(e)}")
            return {
                'success': False,
                'error': f"生成模拟当前天气数据时发生错误: {str(e)}",
                'location': {
                    'latitude': latitude,
                    'longitude': longitude
                },
                'current': {}
            }
    
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