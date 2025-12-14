#--- START OF FILE core/content_extractor.py ---

# -*- coding: utf-8 -*-
"""
内容提取器模块
负责从原始数据中提取各种信息
"""

import json
import re
import hashlib
from typing import Dict, List, Any
from loguru import logger

class ContentExtractor:
    """
    内容提取器，负责从原始数据中提取各种信息
    """
    
    def __init__(self):
        """初始化内容提取器"""
        logger.info("内容提取器初始化完成")
    
    def extract_destination(self, result: Dict[str, Any]) -> str:
        """提取目的地信息"""
        try:
            # 优先从 plan_data 提取
            data = result.get('plan_data', result)
            
            if 'destination' in data:
                return str(data['destination'])
            if 'basic_info' in data and 'destination' in data['basic_info']:
                return str(data['basic_info']['destination'])
            
            # 尝试从对话历史推断
            history = self.extract_conversation_history_list(result)
            for msg in history:
                content = str(msg.get('content', '')).lower()
                if '去' in content and len(content) < 20:
                    match = re.search(r'去([\u4e00-\u9fa5]{2,5})', content)
                    if match:
                        return match.group(1)
            
            return "非遗文化之旅"
        except Exception as e:
            logger.error(f"提取目的地失败: {str(e)}")
            return "未指定目的地"
    
    def extract_travel_dates(self, result: Dict[str, Any]) -> str:
        """提取旅行日期信息"""
        try:
            data = result.get('plan_data', result)
            if 'travel_dates' in data:
                return str(data['travel_dates'])
            if 'dates' in data:
                return str(data['dates'])
            return "待定"
        except Exception:
            return "待定"
    
    def extract_travel_days(self, result: Dict[str, Any]) -> int:
        """提取旅行天数"""
        try:
            data = result.get('plan_data', result)
            if 'travel_days' in data:
                return int(data['travel_days'])
            if 'days' in data:
                return int(data['days'])
            if 'itinerary' in data:
                return len(data['itinerary'])
            return 3
        except Exception:
            return 3

    def extract_conversation_history_list(self, result: Dict[str, Any]) -> List[Dict]:
        """
        深度提取对话历史列表
        """
        # 1. 根目录
        if 'conversation_history' in result and isinstance(result['conversation_history'], list):
            return result['conversation_history']
        
        # 2. plan_data 目录
        if 'plan_data' in result and isinstance(result['plan_data'], dict):
             if 'conversation_history' in result['plan_data']:
                 return result['plan_data']['conversation_history']
        
        # 3. session_info 目录 (PlanEditor 结构)
        if 'session_info' in result and isinstance(result['session_info'], dict):
             return result['session_info'].get('conversation_history', [])
             
        return []

    def extract_conversation_history(self, result: Dict[str, Any]) -> str:
        """
        提取对话历史为文本（向后兼容）
        """
        history = self.extract_conversation_history_list(result)
        if not history:
            return "无对话记录"
        
        parts = []
        for msg in history:
            role = "用户" if msg.get('role') == 'user' else "AI"
            content = msg.get('content', '').strip()
            if content:
                parts.append(f"{role}: {content}")
        return "\n".join(parts)
    
    def format_weather_info(self, weather_info: Dict[str, Any]) -> str:
        """格式化天气信息"""
        try:
            if not weather_info:
                return "暂无天气信息"
            
            summary = weather_info.get('summary', {})
            if summary:
                suitability = summary.get('overall_recommendation', '适宜')
                return f"整体{suitability}，请关注实时预报"
            return "暂无详细数据"
        except Exception:
            return "天气信息解析失败"

