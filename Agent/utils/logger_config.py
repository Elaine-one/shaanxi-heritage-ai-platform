# -*- coding: utf-8 -*-
"""
日志配置模块
配置loguru日志系统
"""

import os
import sys
from pathlib import Path
from loguru import logger
from config import config

def setup_logger():
    """
    设置日志配置
    """
    # 移除默认的日志处理器
    logger.remove()
    
    # 创建日志目录
    log_dir = Path(config.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 控制台日志格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    
    # 文件日志格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )
    
    # 添加控制台处理器
    logger.add(
        sys.stdout,
        format=console_format,
        level=config.LOG_LEVEL,
        colorize=True
    )
    
    # 添加文件处理器
    logger.add(
        config.LOG_FILE,
        format=file_format,
        level=config.LOG_LEVEL,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        encoding="utf-8"
    )
    
    # 添加错误日志文件
    error_log_file = str(Path(config.LOG_FILE).parent / "error.log")
    logger.add(
        error_log_file,
        format=file_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info("日志系统初始化完成")