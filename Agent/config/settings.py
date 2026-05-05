# -*- coding: utf-8 -*-
"""
智能旅游规划Agent配置文件

本模块管理除记忆预算外的所有配置项。
记忆与上下文预算相关配置请参见 Agent.config.memory_budget。

配置优先级: .env 环境变量 > PROVIDER_DEFAULTS 内置默认值
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

config_dir = Path(__file__).parent.parent
env_file = config_dir / '.env'
load_dotenv(env_file)


class LLMConfig:
    """
    LLM 大语言模型配置

    环境变量:
        LLM_PROVIDER  - 提供商名称，决定 base_url 和 default_model 的回退值
        LLM_API_KEY   - API 密钥（必填）
        LLM_BASE_URL  - API 基础地址（可选，未设置时从 PROVIDER_DEFAULTS 获取）
        LLM_MODEL     - 模型名称（可选，未设置时从 PROVIDER_DEFAULTS 获取）
        LLM_TEMPERATURE - 温度参数 0.0-1.0，默认 0.7
        LLM_MAX_TOKENS  - 最大输出 token 数，0 表示由 memory_budget.output_budget_max 决定
    """

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
        # LLM 提供商: openai | dashscope | deepseek | zhipu | moonshot | ollama | custom
        self.provider = os.getenv('LLM_PROVIDER', '').lower()
        # API 密钥（必填）
        self.api_key = os.getenv('LLM_API_KEY', '')
        # API 基础地址，未设置时按 provider 自动选择
        self.base_url = os.getenv('LLM_BASE_URL', '') or self.PROVIDER_DEFAULTS.get(self.provider, {}).get('base_url', '')
        # 模型名称，未设置时按 provider 自动选择
        self.model = os.getenv('LLM_MODEL', '') or self.PROVIDER_DEFAULTS.get(self.provider, {}).get('default_model', '')
        # 温度参数 0.0-1.0，值越低越确定性，默认 0.7
        self.temperature = float(os.getenv('LLM_TEMPERATURE', '0.7'))
        # 最大输出 token 数，0 表示由 memory_budget.output_budget_max 决定
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
    """
    全局配置类（单例模式）

    注意: 记忆与上下文预算相关配置已迁移至 Agent.config.memory_budget，
    本类不再管理 MEMORY_COORDINATOR_* / GRAPH_MEMORY_* 等参数。
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
        self._initialized = True
        self._llm = LLMConfig()

    @property
    def llm(self) -> LLMConfig:
        return self._llm

    # ── 天气服务 ──────────────────────────────────────────
    # Open-Meteo 免费 API，无需密钥
    # 环境变量: WEATHER_API_KEY  默认: None
    WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
    # 环境变量: WEATHER_API_URL  默认: None
    WEATHER_API_URL = os.getenv('WEATHER_API_URL')

    # ── 百度地图 ──────────────────────────────────────────
    # 用于 geocoding.py 地理编码服务
    # 环境变量: BAIDU_MAP_AK  默认: None
    BAIDU_MAP_AK = os.getenv('BAIDU_MAP_AK')
    # 环境变量: BAIDU_MAP_API_URL  默认: None
    BAIDU_MAP_API_URL = os.getenv('BAIDU_MAP_API_URL')

    # ── 高德地图 ──────────────────────────────────────────
    # 用于 REST API 和 MCP Server，申请地址: https://console.amap.com/dev/key/app
    # 环境变量: AMAP_API_KEY  默认: None
    AMAP_API_KEY = os.getenv('AMAP_API_KEY')
    # 环境变量: AMAP_API_URL  默认: https://restapi.amap.com/v3
    AMAP_API_URL = os.getenv('AMAP_API_URL', 'https://restapi.amap.com/v3')
    # 高德 MCP Server URL（SSE 协议）
    # 环境变量: AMAP_MCP_URL  默认: https://mcp.amap.com/sse
    AMAP_MCP_URL = os.getenv('AMAP_MCP_URL', 'https://mcp.amap.com/sse')

    # 地图服务提供商选择: amap | baidu
    # 环境变量: MAP_PROVIDER  默认: amap
    MAP_PROVIDER = os.getenv('MAP_PROVIDER', 'amap').lower()

    # ── 数据库 ────────────────────────────────────────────
    # MySQL 数据库连接配置
    DATABASE_CONFIG = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', '0')),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }

    # ── 后端 API ──────────────────────────────────────────
    # 前端后端 API 地址
    # 环境变量: BACKEND_API_URL  默认: None
    BACKEND_API_URL = os.getenv('BACKEND_API_URL')

    # ── 日志 ──────────────────────────────────────────────
    # 环境变量: LOG_LEVEL  默认: None（由 loguru 自身控制）
    LOG_LEVEL = os.getenv('LOG_LEVEL')
    # 环境变量: LOG_FILE  默认: None
    LOG_FILE = os.getenv('LOG_FILE')

    # ── CORS ──────────────────────────────────────────────
    # 跨域允许的源，* 表示允许所有
    # 环境变量: AGENT_CORS_ALLOWED_ORIGINS  默认: None
    AGENT_CORS_ALLOWED_ORIGINS = os.getenv('AGENT_CORS_ALLOWED_ORIGINS')

    # ── 旅游规划参数 ──────────────────────────────────────
    TRAVEL_CONFIG = {
        'max_daily_attractions': int(os.getenv('TRAVEL_MAX_DAILY_ATTRACTIONS', '0')),
        'travel_speed_kmh': int(os.getenv('TRAVEL_SPEED_KMH', '0')),
        'visit_duration_hours': int(os.getenv('TRAVEL_VISIT_DURATION_HOURS', '0')),
        'daily_start_time': os.getenv('TRAVEL_DAILY_START_TIME'),
        'daily_end_time': os.getenv('TRAVEL_DAILY_END_TIME'),
        'max_travel_distance': int(os.getenv('TRAVEL_MAX_DISTANCE_KM', '0')),
    }

    # ── 缓存 ──────────────────────────────────────────────
    CACHE_CONFIG = {
        'enabled': os.getenv('CACHE_ENABLED', '').lower() == 'true',
        'ttl': int(os.getenv('CACHE_TTL', '0')),
        'max_size': int(os.getenv('CACHE_MAX_SIZE', '0'))
    }

    # ── Session ───────────────────────────────────────────
    # 环境变量: SESSION_COOKIE_NAME  默认: None
    SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME')
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    # 会话存储模式: redis | memory
    # 环境变量: SESSION_STORAGE_MODE  默认: None
    SESSION_STORAGE_MODE = os.getenv('SESSION_STORAGE_MODE')

    # ── Redis ─────────────────────────────────────────────
    # 环境变量: REDIS_HOST  默认: None
    REDIS_HOST = os.getenv('REDIS_HOST')
    # 环境变量: REDIS_PORT  默认: 0
    REDIS_PORT = int(os.getenv('REDIS_PORT', '0'))
    # 环境变量: REDIS_DB  默认: 0
    REDIS_DB = int(os.getenv('REDIS_DB', '0'))
    # 环境变量: REDIS_PASSWORD  默认: None
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    # Redis 会话 TTL（秒），0 会导致 setex 异常，务必设置合理值
    # 环境变量: REDIS_SESSION_TTL  默认: 86400（1天）
    REDIS_SESSION_TTL = int(os.getenv('REDIS_SESSION_TTL', '86400'))

    # ── Neo4j 知识图谱（可选）─────────────────────────────
    # 环境变量: NEO4J_URI  默认: None
    NEO4J_URI = os.getenv('NEO4J_URI')
    # 环境变量: NEO4J_USER  默认: None
    NEO4J_USER = os.getenv('NEO4J_USER')
    # 环境变量: NEO4J_PASSWORD  默认: None
    NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

    # ── ChromaDB 向量数据库（可选）────────────────────────
    # 环境变量: CHROMADB_PERSIST_DIRECTORY  默认: None
    CHROMADB_PERSIST_DIRECTORY = os.getenv('CHROMADB_PERSIST_DIRECTORY')
    # 环境变量: EMBEDDING_MODEL  默认: None
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL')

    # ── MinIO 对象存储 ────────────────────────────────────
    # 环境变量: MINIO_ENDPOINT  默认: None
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
    # 环境变量: MINIO_ACCESS_KEY  默认: None
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
    # 环境变量: MINIO_SECRET_KEY  默认: None
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
    # 环境变量: MINIO_BUCKET_NAME  默认: None
    MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME')
    # 环境变量: MINIO_SECURE  默认: false
    MINIO_SECURE = os.getenv('MINIO_SECURE', '').lower() == 'true'
    # 环境变量: MINIO_REGION  默认: None
    MINIO_REGION = os.getenv('MINIO_REGION')

    # ── 数据归档 ──────────────────────────────────────────
    # 对话归档 TTL（秒）
    # 环境变量: CONVERSATION_ARCHIVE_TTL  默认: 0
    CONVERSATION_ARCHIVE_TTL = int(os.getenv('CONVERSATION_ARCHIVE_TTL', '0'))
    # PDF 保留天数
    # 环境变量: PDF_RETENTION_DAYS  默认: 0
    PDF_RETENTION_DAYS = int(os.getenv('PDF_RETENTION_DAYS', '0'))
    # 媒体文件保留天数
    # 环境变量: MEDIA_RETENTION_DAYS  默认: 0
    MEDIA_RETENTION_DAYS = int(os.getenv('MEDIA_RETENTION_DAYS', '0'))
    # 自动归档开关
    # 环境变量: AUTO_ARCHIVE_ENABLED  默认: false
    AUTO_ARCHIVE_ENABLED = os.getenv('AUTO_ARCHIVE_ENABLED', '').lower() == 'true'

    # ── 数据同步 ──────────────────────────────────────────
    # 启动时同步非遗数据到知识图谱和向量数据库
    # 环境变量: HERITAGE_DATA_SYNC_ENABLED  默认: true
    HERITAGE_DATA_SYNC_ENABLED = os.getenv('HERITAGE_DATA_SYNC_ENABLED', 'true').lower() == 'true'

    # ── 并发控制 ──────────────────────────────────────────
    # 最大并发规划任务数
    # 环境变量: MAX_CONCURRENT_PLANNING  默认: 5
    MAX_CONCURRENT_PLANNING = int(os.getenv('MAX_CONCURRENT_PLANNING', '5'))
    # 每用户最大并发规划任务数
    # 环境变量: MAX_PLANNING_PER_USER  默认: 2
    MAX_PLANNING_PER_USER = int(os.getenv('MAX_PLANNING_PER_USER', '2'))

    # ── 资源清理 ──────────────────────────────────────────
    # 清理间隔（秒）
    # 环境变量: CLEANUP_INTERVAL  默认: 300
    CLEANUP_INTERVAL = int(os.getenv('CLEANUP_INTERVAL', '300'))
    # 会话最大存活时间（小时）
    # 环境变量: SESSION_MAX_AGE_HOURS  默认: 12
    SESSION_MAX_AGE_HOURS = int(os.getenv('SESSION_MAX_AGE_HOURS', '12'))
    # 进度缓存最大存活时间（小时）
    # 环境变量: PROGRESS_MAX_AGE_HOURS  默认: 1
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
        if not self.AMAP_API_KEY:
            warnings.append('AMAP_API_KEY 未设置，地图工具将不可用')

        return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}

    def get_llm_config(self) -> LLMConfig:
        return self._llm


config = Config()

validation_result = config.validate_config()
if not validation_result['valid']:
    print(f"配置错误: {validation_result['errors']}")
if validation_result['warnings']:
    print(f"配置警告: {validation_result['warnings']}")
