# -*- coding: utf-8 -*-
"""
字体管理器
负责管理系统字体，特别是中文字体，用于PDF生成
"""

import os
import platform
from typing import Dict, List, Optional, Tuple
from loguru import logger


class FontManager:
    """
    字体管理器，负责管理和提供系统字体信息
    """
    
    def __init__(self):
        """初始化字体管理器"""
        self.system = platform.system()
        self.available_fonts = {}
        self._scan_system_fonts()
    
    def _scan_system_fonts(self):
        """扫描系统可用的中文字体"""
        try:
            if self.system == "Linux":
                self._scan_linux_fonts()
            elif self.system == "Windows":
                self._scan_windows_fonts()
            elif self.system == "Darwin":  # macOS
                self._scan_macos_fonts()
            else:
                logger.warning(f"不支持的操作系统: {self.system}")
        except Exception as e:
            logger.error(f"扫描系统字体时发生错误: {e}")
    
    def _scan_linux_fonts(self):
        """扫描Linux系统的中文字体"""
        # 常见的Linux中文字体路径
        font_paths = [
            # 文泉驿字体
            ('wqy-zenhei', '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'),
            ('wqy-microhei', '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'),
            # AR PL字体
            ('ar-uming', '/usr/share/fonts/truetype/arphic/uming.ttc'),
            ('ar-ukai', '/usr/share/fonts/truetype/arphic/ukai.ttc'),
            # Noto字体
            ('noto-cjk', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),
            ('noto-cjk-sc', '/usr/share/fonts/truetype/noto/NotoSansCJKsc-Regular.otf'),
            # Droid字体
            ('droid-fallback', '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'),
        ]
        
        for font_name, font_path in font_paths:
            if os.path.exists(font_path):
                self.available_fonts[font_name] = font_path
                logger.info(f"找到Linux中文字体: {font_name} -> {font_path}")
        
        # 如果没有找到字体，尝试使用fc-list命令查找
        if not self.available_fonts:
            try:
                import subprocess
                result = subprocess.run(['fc-list', ':lang=zh'], capture_output=True, text=True)
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            # 解析fc-list输出，格式通常为: /path/to/font: Font Name:style=Style
                            parts = line.split(':')
                            if len(parts) >= 1:
                                font_path = parts[0].strip()
                                if os.path.exists(font_path):
                                    # 从路径中提取字体名称
                                    font_file = os.path.basename(font_path)
                                    font_name = os.path.splitext(font_file)[0]
                                    self.available_fonts[font_name] = font_path
                                    logger.info(f"通过fc-list找到中文字体: {font_name} -> {font_path}")
            except Exception as e:
                logger.warning(f"使用fc-list查找字体时出错: {e}")
    
    def _scan_windows_fonts(self):
        """扫描Windows系统的中文字体"""
        # 常见的Windows中文字体路径
        font_paths = [
            ('simsun', 'C:/Windows/Fonts/simsun.ttc'),  # 宋体
            ('simhei', 'C:/Windows/Fonts/simhei.ttf'),  # 黑体
            ('msyh', 'C:/Windows/Fonts/msyh.ttc'),      # 微软雅黑
            ('fangsong', 'C:/Windows/Fonts/fangsong.ttf'),  # 仿宋
            ('kaiti', 'C:/Windows/Fonts/simkai.ttf'),       # 楷体
        ]
        
        for font_name, font_path in font_paths:
            if os.path.exists(font_path):
                self.available_fonts[font_name] = font_path
                logger.info(f"找到Windows中文字体: {font_name} -> {font_path}")
    
    def _scan_macos_fonts(self):
        """扫描macOS系统的中文字体"""
        # 常见的macOS中文字体路径
        font_paths = [
            ('pingfang', '/System/Library/Fonts/PingFang.ttc'),  # 苹方
            ('heiti', '/System/Library/Fonts/Heiti.ttc'),       # 黑体
            ('songti', '/System/Library/Fonts/Songti.ttc'),     # 宋体
            ('kaiti', '/System/Library/Fonts/Kaiti.ttc'),       # 楷体
        ]
        
        for font_name, font_path in font_paths:
            if os.path.exists(font_path):
                self.available_fonts[font_name] = font_path
                logger.info(f"找到macOS中文字体: {font_name} -> {font_path}")
    
    def get_chinese_font(self) -> Optional[Tuple[str, str]]:
        """
        获取第一个可用的中文字体
        
        Returns:
            Optional[Tuple[str, str]]: 字体名称和路径的元组，如果没有找到则返回None
        """
        if not self.available_fonts:
            logger.warning("没有找到可用的中文字体")
            return None
        
        # 返回第一个可用的中文字体
        font_name, font_path = next(iter(self.available_fonts.items()))
        logger.info(f"使用中文字体: {font_name} -> {font_path}")
        return font_name, font_path
    
    def get_font_path(self, font_name: str) -> Optional[str]:
        """
        根据字体名称获取字体路径
        
        Args:
            font_name: 字体名称
            
        Returns:
            Optional[str]: 字体路径，如果没有找到则返回None
        """
        return self.available_fonts.get(font_name)
    
    def list_available_fonts(self) -> Dict[str, str]:
        """
        列出所有可用的中文字体
        
        Returns:
            Dict[str, str]: 字体名称和路径的字典
        """
        return self.available_fonts.copy()
    
    def register_font_with_reportlab(self, font_name: str = None) -> Optional[str]:
        """
        使用ReportLab注册字体
        
        Args:
            font_name: 要注册的字体名称，如果为None则使用第一个可用字体
            
        Returns:
            Optional[str]: 注册成功后返回字体名称，失败返回None
        """
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            logger.error("ReportLab未安装，无法注册字体")
            return None
        
        if not font_name:
            font_result = self.get_chinese_font()
            if not font_result:
                logger.warning("没有可用的中文字体可以注册")
                return None
            font_name, font_path = font_result
        else:
            font_path = self.get_font_path(font_name)
            if not font_path:
                logger.warning(f"找不到字体: {font_name}")
                return None
        
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            logger.info(f"成功注册字体: {font_name} -> {font_path}")
            return font_name
        except Exception as e:
            logger.error(f"注册字体失败: {font_name} -> {font_path}, 错误: {e}")
            return None


# 全局字体管理器实例
_font_manager = None


def get_font_manager() -> FontManager:
    """
    获取全局字体管理器实例
    
    Returns:
        FontManager: 字体管理器实例
    """
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager


def register_chinese_font(font_name: str = None) -> Optional[str]:
    """
    注册中文字体的便捷函数
    
    Args:
        font_name: 要注册的字体名称，如果为None则使用第一个可用字体
        
    Returns:
        Optional[str]: 注册成功后返回字体名称，失败返回None
    """
    font_manager = get_font_manager()
    return font_manager.register_font_with_reportlab(font_name)