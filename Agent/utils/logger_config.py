# -*- coding: utf-8 -*-
"""
日志配置模块
配置loguru日志系统
"""

import os
import sys
from pathlib import Path
from loguru import logger
from Agent.config import config

def setup_logger():
    """
    设置日志配置
    """
    # 移除默认的日志处理器
    logger.remove()
    
    # 创建日志目录 - 使用绝对路径
    project_root = Path(__file__).resolve().parent.parent
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志文件路径
    log_file = log_dir / "agent.log"
    error_log_file = log_dir / "error.log"
    
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
        level="DEBUG",
        colorize=True
    )
    
    # 添加文件处理器
    logger.add(
        str(log_file),
        format=file_format,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8"
    )
    
    # 添加错误日志文件
    logger.add(
        str(error_log_file),
        format=file_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8"
    )
    
    logger.info(f"日志系统初始化完成，日志目录: {log_dir}")