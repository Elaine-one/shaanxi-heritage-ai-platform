# -*- coding: utf-8 -*-
"""
智能旅游规划Agent配置文件
包含阿里云模型配置、API密钥、数据库连接等配置信息
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量 - 从 Agent 目录加载 .env 文件
config_dir = Path(__file__).parent.parent
env_file = config_dir / '.env'
load_dotenv(env_file)

class Config:
    """
    配置类，管理所有配置信息
    """
    
    # 阿里云DashScope配置
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
    DASHSCOPE_MODEL = os.getenv('DASHSCOPE_MODEL')
    
    # 天气API配置 - Open-Meteo免费服务
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY', '')  # Open-Meteo不需要API密钥
    WEATHER_API_URL = os.getenv('WEATHER_API_URL', 'https://api.open-meteo.com/v1')
    
    # 百度地图API配置
    BAIDU_MAP_AK = os.getenv('BAIDU_MAP_AK', '')
    BAIDU_MAP_API_URL = 'https://api.map.baidu.com'
    
    # 数据库配置
    DATABASE_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }
    
    # Django后端API配置
    BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:8000/api')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/agent.log')
    
    # 旅游规划配置
    TRAVEL_CONFIG = {
        'max_daily_attractions': 4,  # 每日最多景点数
        'travel_speed_kmh': 90,      # 平均行驶速度(公里/小时)
        'visit_duration_hours': 6,   # 每个景点平均游览时间(小时)
        'daily_start_time': '09:00', # 每日开始时间
        'daily_end_time': '21:00',   # 每日结束时间
        'max_travel_distance': 1000,  # 最大旅行距离(公里)
    }
    
    # 缓存配置
    CACHE_CONFIG = {
        'enabled': True,
        'ttl': 3600,  # 缓存时间(秒)
        'max_size': 1000  # 最大缓存条目数
    }
    
    # Session认证配置
    SESSION_COOKIE_NAME = 'sessionid'  # Django session cookie名称
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Session存储引擎
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """
        验证配置是否完整
        
        Returns:
            Dict[str, Any]: 验证结果
        """
        errors = []
        warnings = []
        
        # 检查必需的API密钥
        if not cls.DASHSCOPE_API_KEY:
            errors.append('DASHSCOPE_API_KEY未设置')
            
        # 检查模型配置
        if not cls.DASHSCOPE_MODEL:
            errors.append('DASHSCOPE_MODEL未设置')
            
        # Open-Meteo不需要API密钥，注释掉此验证
        # if not cls.WEATHER_API_KEY:
        #     warnings.append('WEATHER_API_KEY未设置，天气功能将不可用')
            
        if not cls.BAIDU_MAP_AK:
            warnings.append('BAIDU_MAP_AK未设置，地图功能将受限')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """
        获取模型配置
        
        Returns:
            Dict[str, Any]: 模型配置信息
        """
        return {
            'api_key': cls.DASHSCOPE_API_KEY,
            'model': cls.DASHSCOPE_MODEL,
            'temperature': 0.7,
            'max_tokens': 2000,
            'top_p': 0.8
        }

# 全局配置实例
config = Config()

# 验证配置
validation_result = config.validate_config()
if not validation_result['valid']:
    print(f"配置错误: {validation_result['errors']}")
if validation_result['warnings']:
    print(f"配置警告: {validation_result['warnings']}")