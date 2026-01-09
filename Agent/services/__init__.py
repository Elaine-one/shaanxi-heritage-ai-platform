# -*- coding: utf-8 -*-
"""
Services 模块
包含服务层代码，包括天气服务、PDF 生成、内容整合、遗产分析等
"""

from .weather import WeatherService, get_weather_service
from .pdf_generator import PDFGenerator
from .content_integrator import AIContentIntegrator
from .pdf_content_integrator import PDFContentIntegrator
from .heritage_analyzer import HeritageAnalyzer, get_heritage_analyzer

__all__ = [
    # Weather services
    'WeatherService',
    'get_weather_service',
    # PDF services
    'PDFGenerator',
    # Content integration
    'AIContentIntegrator',
    'PDFContentIntegrator',
    # Heritage analysis
    'HeritageAnalyzer',
    'get_heritage_analyzer'
]
