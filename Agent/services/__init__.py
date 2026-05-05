# -*- coding: utf-8 -*-
"""
Services 模块
包含服务层代码，包括天气服务、PDF 生成、内容整合、遗产分析、地理编码、MCP服务等
"""

from loguru import logger

from .weather import WeatherService, get_weather_service
from .pdf_generator_optimized import OptimizedPDFGenerator, get_optimized_pdf_generator
from .content_integrator import AIContentIntegrator
from .pdf_content_integrator import PDFContentIntegrator
from .heritage_analyzer import HeritageAnalyzer, get_heritage_analyzer
from .geocoding import GeocodingService, get_geocoding_service
from .conversation_service import ConversationService, get_conversation_service
from .user_history_service import UserHistoryService, get_user_history_service

try:
    from .minio_storage import MinIOStorageService, get_minio_service
except Exception as e:
    MinIOStorageService = None
    get_minio_service = None
    logger.warning(f"minio_storage 导入失败（可选依赖）: {e}")

try:
    from .amap_mcp_client import AmapMCPClient, get_amap_client
except Exception as e:
    AmapMCPClient = None
    get_amap_client = None
    logger.warning(f"amap_mcp_client 导入失败（可选依赖）: {e}")

try:
    from .amap_mcp_service import AmapMCPService, get_amap_mcp_service, get_mcp_tools
except Exception as e:
    AmapMCPService = None
    get_amap_mcp_service = None
    get_mcp_tools = None
    logger.warning(f"amap_mcp_service 导入失败（可选依赖）: {e}")

__all__ = [
    'WeatherService',
    'get_weather_service',
    'OptimizedPDFGenerator',
    'get_optimized_pdf_generator',
    'AIContentIntegrator',
    'PDFContentIntegrator',
    'HeritageAnalyzer',
    'get_heritage_analyzer',
    'GeocodingService',
    'get_geocoding_service',
    'ConversationService',
    'get_conversation_service',
    'UserHistoryService',
    'get_user_history_service',
    'MinIOStorageService',
    'get_minio_service',
    'AmapMCPClient',
    'get_amap_client',
    'AmapMCPService',
    'get_amap_mcp_service',
    'get_mcp_tools',
]
