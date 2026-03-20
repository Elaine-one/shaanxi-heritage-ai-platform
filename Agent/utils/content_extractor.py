# -*- coding: utf-8 -*-
"""
内容提取器模块
负责从原始数据中提取各种信息
不使用正则表达式，使用字符串方法和JSON解析
"""

from typing import Dict, List, Any
from loguru import logger


DESTINATION_KEYWORDS = [
    '去', '到', '前往', '目的地', '游览', '参观', '游玩',
    'travel to', 'visit', 'go to'
]

DESTINATION_STOP_WORDS = [
    '想', '要', '准备', '计划', '打算', '希望', '可以', '能',
    '怎么', '如何', '什么', '为什么', '哪', '吗', '呢', '啊',
    '一下', '看看', '问问', '查查'
]


class ContentExtractor:
    """
    内容提取器，负责从原始数据中提取各种信息
    不使用正则表达式
    """
    
    def __init__(self):
        """初始化内容提取器"""
        logger.info("内容提取器初始化完成")
    
    def extract_destination(self, result: Dict[str, Any]) -> str:
        """提取目的地信息"""
        try:
            data = result.get('plan_data', result)
            if 'destination' in data:
                return str(data['destination'])
            if 'basic_info' in data and 'destination' in data['basic_info']:
                return str(data['basic_info']['destination'])
            
            history = self.extract_conversation_history_list(result)
            for msg in history:
                content = str(msg.get('content', ''))
                destination = self._extract_destination_from_text(content)
                if destination:
                    return destination
            
            return "非遗文化之旅"
        except Exception as e:
            logger.error(f"提取目的地失败: {str(e)}")
            return "未指定目的地"
    
    def _extract_destination_from_text(self, text: str) -> str:
        """从文本中提取目的地（不使用正则）"""
        if not text or len(text) > 50:
            return ""
        
        for keyword in DESTINATION_KEYWORDS:
            if keyword in text:
                idx = text.find(keyword)
                after_keyword = text[idx + len(keyword):].strip()
                
                destination = ""
                for char in after_keyword:
                    if self._is_chinese_char(char):
                        destination += char
                        if len(destination) >= 5:
                            break
                    elif destination:
                        break
                
                destination = destination.strip()
                if destination and destination not in DESTINATION_STOP_WORDS:
                    if len(destination) >= 2:
                        return destination
        
        return ""
    
    def _is_chinese_char(self, char: str) -> bool:
        """检查是否是中文字符"""
        code = ord(char)
        return 0x4e00 <= code <= 0x9fff
    
    def extract_travel_dates(self, result: Dict[str, Any]) -> str:
        """提取旅行日期信息"""
        try:
            data = result.get('plan_data', result)
            if 'travel_dates' in data:
                return str(data['travel_dates'])
            if 'dates' in data:
                return str(data['dates'])
            return "近期"
        except Exception:
            return "近期"
    
    def extract_travel_days(self, result: Dict[str, Any]) -> int:
        """提取旅行天数"""
        try:
            data = result.get('plan_data', result)
            if 'travel_days' in data:
                return int(data['travel_days'])
            if 'days' in data:
                return int(data['days'])
            if 'itinerary' in data and isinstance(data['itinerary'], list):
                return len(data['itinerary'])
            return 3
        except Exception:
            return 3

    def extract_conversation_history_list(self, result: Dict[str, Any]) -> List[Dict]:
        """深度提取对话历史列表"""
        if 'conversation_history' in result and isinstance(result['conversation_history'], list):
            return result['conversation_history']
        
        if 'plan_data' in result and isinstance(result['plan_data'], dict):
             if 'conversation_history' in result['plan_data']:
                 return result['plan_data']['conversation_history']
        
        if 'session_info' in result and isinstance(result['session_info'], dict):
             return result['session_info'].get('conversation_history', [])
             
        return []

    def extract_conversation_history(self, result: Dict[str, Any]) -> str:
        """提取对话历史为文本"""
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
        """
        格式化天气信息，提取详细预报数据
        """
        try:
            if not weather_info:
                return "暂无天气信息，建议出行前查询实时天气。"
            
            summary_text = ""
            summary = weather_info.get('summary', {})
            if summary:
                suitability = summary.get('overall_recommendation', '适宜')
                summary_text = f"整体建议：{suitability}。"
            
            details = []
            locations = weather_info.get('locations', {})
            
            if isinstance(locations, dict):
                for loc_name, loc_data in locations.items():
                    if 'forecast' in loc_data and isinstance(loc_data['forecast'], list):
                        daily_weather = []
                        for day in loc_data['forecast'][:5]:
                            date = day.get('date', '')
                            cond = day.get('weather_description', '未知')
                            min_t = day.get('min_temp', 0)
                            max_t = day.get('max_temp', 0)
                            temp_str = f"{min_t}-{max_t}°C"
                            
                            daily_weather.append(f"{date}({cond}, {temp_str})")
                        
                        if daily_weather:
                            short_name = loc_name.split(',')[0] if ',' in loc_name else loc_name
                            details.append(f"【{short_name}】: " + "；".join(daily_weather))
            
            elif 'forecast' in weather_info and isinstance(weather_info['forecast'], list):
                 daily_weather = []
                 for day in weather_info['forecast'][:5]:
                    date = day.get('date', '')
                    cond = day.get('weather_description', '未知')
                    min_t = day.get('min_temp', 0)
                    max_t = day.get('max_temp', 0)
                    daily_weather.append(f"{date}: {cond}, {min_t}-{max_t}°C")
                 if daily_weather:
                     details.append("；".join(daily_weather))

            if not details and not summary_text:
                return "暂无详细天气数据。"
            
            final_text = summary_text + "\n详细预报：\n" + "\n".join(details)
            return final_text

        except Exception as e:
            logger.warning(f"天气格式化异常: {str(e)}")
            return "天气数据解析异常，建议查询当地气象台。"
