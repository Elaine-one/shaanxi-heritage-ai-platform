# -*- coding: utf-8 -*-
"""
Services 模块
包含服务层代码，包括天气服务、PDF 生成、内容整合、遗产分析、地理编码、MCP客户端等
"""

from .weather import WeatherService, get_weather_service
from .pdf_generator_optimized import OptimizedPDFGenerator, get_optimized_pdf_generator
from .content_integrator import AIContentIntegrator
from .pdf_content_integrator import PDFContentIntegrator
from .heritage_analyzer import HeritageAnalyzer, get_heritage_analyzer
from .geocoding import GeocodingService, get_geocoding_service
from .conversation_service import ConversationService, get_conversation_service
from .user_history_service import UserHistoryService, get_user_history_service
from .minio_storage import MinIOStorageService, get_minio_service
from .mcp_client import BaiduMapsMCPClient, get_mcp_client

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
    'BaiduMapsMCPClient',
    'get_mcp_client',
]
