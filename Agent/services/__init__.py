# -*- coding: utf-8 -*-
"""
Services 模块
包含服务层代码，包括天气服务、PDF 生成、内容整合、遗产分析、地理编码等
"""

from .weather import WeatherService, get_weather_service
from .pdf_generator import PDFGenerator
from .content_integrator import AIContentIntegrator
from .pdf_content_integrator import PDFContentIntegrator
from .heritage_analyzer import HeritageAnalyzer, get_heritage_analyzer
from .geocoding import GeocodingService, get_geocoding_service
from .conversation_service import ConversationService, get_conversation_service
from .user_history_service import UserHistoryService, get_user_history_service
from .minio_storage import MinIOStorageService, get_minio_service

__all__ = [
    'WeatherService',
    'get_weather_service',
    'PDFGenerator',
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
]
