# -*- coding: utf-8 -*-
"""
日志配置模块
配置loguru日志系统
"""

import sys
from pathlib import Path
from loguru import logger

_logger_initialized = False

def setup_logger():
    """
    设置日志配置
    """
    global _logger_initialized
    
    if _logger_initialized:
        return
    
    _logger_initialized = True
    
    logger.remove()
    
    project_root = Path(__file__).resolve().parent.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "agent.log"
    error_log_file = log_dir / "error.log"
    
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    
    logger.add(
        sys.stdout,
        format=console_format,
        level="INFO",
        colorize=True,
        filter=lambda record: record["name"].startswith("Agent")
    )
    
    logger.add(
        str(log_file),
        format=file_format,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8"
    )
    
    logger.add(
        str(error_log_file),
        format=file_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8"
    )
    
    logger.info(f"日志系统初始化完成，日志目录: {log_dir}")