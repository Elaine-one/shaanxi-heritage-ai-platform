# -*- coding: utf-8 -*-
"""
智能旅游规划Agent配置文件
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

config_dir = Path(__file__).parent.parent
env_file = config_dir / '.env'
load_dotenv(env_file)


class LLMConfig:
    """LLM 配置类"""
    
    PROVIDER_DEFAULTS = {
        'openai': {
            'base_url': 'https://api.openai.com/v1',
            'default_model': 'gpt-4o',
        },
        'dashscope': {
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'default_model': 'qwen-plus',
        },
        'deepseek': {
            'base_url': 'https://api.deepseek.com/v1',
            'default_model': 'deepseek-chat',
        },
        'zhipu': {
            'base_url': 'https://open.bigmodel.cn/api/paas/v4',
            'default_model': 'glm-4',
        },
        'moonshot': {
            'base_url': 'https://api.moonshot.cn/v1',
            'default_model': 'moonshot-v1-8k',
        },
        'ollama': {
            'base_url': 'http://localhost:11434/v1',
            'default_model': 'llama3',
        },
        'custom': {
            'base_url': '',
            'default_model': '',
        },
    }
    
    def __init__(self):
        self.provider = os.getenv('LLM_PROVIDER', '').lower()
        self.api_key = os.getenv('LLM_API_KEY', '')
        self.base_url = os.getenv('LLM_BASE_URL', '') or self.PROVIDER_DEFAULTS.get(self.provider, {}).get('base_url', '')
        self.model = os.getenv('LLM_MODEL', '') or self.PROVIDER_DEFAULTS.get(self.provider, {}).get('default_model', '')
        self.temperature = float(os.getenv('LLM_TEMPERATURE', '0'))
        self.max_tokens = int(os.getenv('LLM_MAX_TOKENS', '0'))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'provider': self.provider,
            'api_key': self.api_key,
            'base_url': self.base_url,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
        }


class Config:
    """配置类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._llm = LLMConfig()
    
    @property
    def llm(self) -> LLMConfig:
        return self._llm
    
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    WEATHER_API_URL = os.getenv('WEATHER_API_URL')
    
    BAIDU_MAP_AK = os.getenv('BAIDU_MAP_AK')
    BAIDU_MAP_API_URL = os.getenv('BAIDU_MAP_API_URL')
    
    AMAP_API_KEY = os.getenv('AMAP_API_KEY')
    AMAP_API_URL = os.getenv('AMAP_API_URL', 'https://restapi.amap.com/v3')
    
    MAP_PROVIDER = os.getenv('MAP_PROVIDER', 'amap').lower()
    
    DATABASE_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', '0')),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }
    
    BACKEND_API_URL = os.getenv('BACKEND_API_URL')
    
    LOG_LEVEL = os.getenv('LOG_LEVEL')
    LOG_FILE = os.getenv('LOG_FILE')

    AGENT_CORS_ALLOWED_ORIGINS = os.getenv('AGENT_CORS_ALLOWED_ORIGINS')
    
    TRAVEL_CONFIG = {
        'max_daily_attractions': int(os.getenv('TRAVEL_MAX_DAILY_ATTRACTIONS', '0')),
        'travel_speed_kmh': int(os.getenv('TRAVEL_SPEED_KMH', '0')),
        'visit_duration_hours': int(os.getenv('TRAVEL_VISIT_DURATION_HOURS', '0')),
        'daily_start_time': os.getenv('TRAVEL_DAILY_START_TIME'),
        'daily_end_time': os.getenv('TRAVEL_DAILY_END_TIME'),
        'max_travel_distance': int(os.getenv('TRAVEL_MAX_DISTANCE_KM', '0')),
    }
    
    CACHE_CONFIG = {
        'enabled': os.getenv('CACHE_ENABLED', '').lower() == 'true',
        'ttl': int(os.getenv('CACHE_TTL', '0')),
        'max_size': int(os.getenv('CACHE_MAX_SIZE', '0'))
    }
    
    SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME')
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    
    REDIS_HOST = os.getenv('REDIS_HOST')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '0'))
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    REDIS_SESSION_TTL = int(os.getenv('REDIS_SESSION_TTL', '0'))

    SESSION_STORAGE_MODE = os.getenv('SESSION_STORAGE_MODE')
    
    NEO4J_URI = os.getenv('NEO4J_URI')
    NEO4J_USER = os.getenv('NEO4J_USER')
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
    
    CHROMADB_PERSIST_DIRECTORY = os.getenv('CHROMADB_PERSIST_DIRECTORY')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')
    
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
    MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME')
    MINIO_SECURE = os.getenv('MINIO_SECURE', '').lower() == 'true'
    MINIO_REGION = os.getenv('MINIO_REGION')
    
    CONVERSATION_ARCHIVE_TTL = int(os.getenv('CONVERSATION_ARCHIVE_TTL', '0'))
    PDF_RETENTION_DAYS = int(os.getenv('PDF_RETENTION_DAYS', '0'))
    MEDIA_RETENTION_DAYS = int(os.getenv('MEDIA_RETENTION_DAYS', '0'))
    AUTO_ARCHIVE_ENABLED = os.getenv('AUTO_ARCHIVE_ENABLED', '').lower() == 'true'
    
    HERITAGE_DATA_SYNC_ENABLED = os.getenv('HERITAGE_DATA_SYNC_ENABLED', 'true').lower() == 'true'
    
    MAX_CONCURRENT_PLANNING = int(os.getenv('MAX_CONCURRENT_PLANNING', '5'))
    MAX_PLANNING_PER_USER = int(os.getenv('MAX_PLANNING_PER_USER', '2'))
    CLEANUP_INTERVAL = int(os.getenv('CLEANUP_INTERVAL', '300'))
    SESSION_MAX_AGE_HOURS = int(os.getenv('SESSION_MAX_AGE_HOURS', '12'))
    PROGRESS_MAX_AGE_HOURS = int(os.getenv('PROGRESS_MAX_AGE_HOURS', '1'))
    
    def validate_config(self) -> Dict[str, Any]:
        errors = []
        warnings = []
        
        if not self._llm.api_key:
            errors.append(f'LLM_API_KEY 未设置 (提供商: {self._llm.provider})')
        if not self._llm.model:
            errors.append('LLM_MODEL 未设置')
        if not self._llm.base_url and self._llm.provider == 'custom':
            warnings.append('LLM_BASE_URL 未设置')
        if not self.BAIDU_MAP_AK:
            warnings.append('BAIDU_MAP_AK 未设置')
        
        return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}
    
    def get_llm_config(self) -> LLMConfig:
        return self._llm


config = Config()

validation_result = config.validate_config()
if not validation_result['valid']:
    print(f"配置错误: {validation_result['errors']}")
if validation_result['warnings']:
    print(f"配置警告: {validation_result['warnings']}")
