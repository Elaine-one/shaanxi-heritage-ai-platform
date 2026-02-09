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
    # 阿里云API密钥
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
    # 阿里云模型名称
    DASHSCOPE_MODEL = os.getenv('DASHSCOPE_MODEL')
    
    # 天气API配置 - Open-Meteo免费服务
    # 天气API密钥（可选，使用Open-Meteo时为空）
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    # 天气API地址
    WEATHER_API_URL = os.getenv('WEATHER_API_URL')
    
    # 百度地图API配置
    # 百度地图API密钥
    BAIDU_MAP_AK = os.getenv('BAIDU_MAP_AK')
    # 百度地图API地址
    BAIDU_MAP_API_URL = os.getenv('BAIDU_MAP_API_URL')
    
    # 数据库配置
    DATABASE_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT')),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }
    
    # Django后端API配置
    # 用于Session验证和用户数据获取
    BACKEND_API_URL = os.getenv('BACKEND_API_URL')
    
    # 日志配置
    # 控制日志输出级别和文件路径
    LOG_LEVEL = os.getenv('LOG_LEVEL')
    LOG_FILE = os.getenv('LOG_FILE')

    # Agent API CORS配置
    # 允许的跨域来源，逗号分隔
    AGENT_CORS_ALLOWED_ORIGINS = os.getenv('AGENT_CORS_ALLOWED_ORIGINS')
    
    # 旅游规划配置
    TRAVEL_CONFIG = {
        'max_daily_attractions': int(os.getenv('TRAVEL_MAX_DAILY_ATTRACTIONS')),
        'travel_speed_kmh': int(os.getenv('TRAVEL_SPEED_KMH')),
        'visit_duration_hours': int(os.getenv('TRAVEL_VISIT_DURATION_HOURS')),
        'daily_start_time': os.getenv('TRAVEL_DAILY_START_TIME'),
        'daily_end_time': os.getenv('TRAVEL_DAILY_END_TIME'),
        'max_travel_distance': int(os.getenv('TRAVEL_MAX_DISTANCE_KM')),
    }
    
    # 缓存配置
    CACHE_CONFIG = {
        'enabled': os.getenv('CACHE_ENABLED', 'true').lower() == 'true',
        'ttl': int(os.getenv('CACHE_TTL')),
        'max_size': int(os.getenv('CACHE_MAX_SIZE'))
    }
    
    # Session认证配置
    # Session Cookie名称
    SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME')
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # Session存储引擎
    
    # Redis配置
    # Redis主机地址
    REDIS_HOST = os.getenv('REDIS_HOST')
    # Redis端口
    REDIS_PORT = int(os.getenv('REDIS_PORT'))
    # Redis数据库索引
    REDIS_DB = int(os.getenv('REDIS_DB'))
    # Redis密码
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    # Redis会话过期时间
    REDIS_SESSION_TTL = int(os.getenv('REDIS_SESSION_TTL'))

    
    # 会话存储模式: 'memory' 或 'redis'
    SESSION_STORAGE_MODE = os.getenv('SESSION_STORAGE_MODE')
    
    # MinIO配置
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
    MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME')
    MINIO_SECURE = os.getenv('MINIO_SECURE').lower() == 'true'
    MINIO_REGION = os.getenv('MINIO_REGION')
    
    # 归档配置
    CONVERSATION_ARCHIVE_TTL = int(os.getenv('CONVERSATION_ARCHIVE_TTL'))
    PDF_RETENTION_DAYS = int(os.getenv('PDF_RETENTION_DAYS'))
    MEDIA_RETENTION_DAYS = int(os.getenv('MEDIA_RETENTION_DAYS'))
    AUTO_ARCHIVE_ENABLED = os.getenv('AUTO_ARCHIVE_ENABLED').lower() == 'true'
    
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