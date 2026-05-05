# -*- coding: utf-8 -*-
"""
AI内容集成器
负责使用AI模型整合旅游规划数据
"""

import json
import hashlib
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from Agent.utils.content_extractor import ContentExtractor
from Agent.prompts import get_conversation_summary_prompt


class AIContentIntegrator:
    """
    AI内容集成器，负责使用AI模型整合旅游规划数据
    """
    
    def __init__(self, llm_model=None):
        self.llm_model = llm_model
        self._content_cache = {}
        self._cache_timeout = 300
        self.content_extractor = ContentExtractor()
        logger.info("AI内容集成器初始化完成")
    
    async def integrate_travel_plan_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        整合旅游规划内容入口
        """
        try:
            logger.info("开始AI自主整合旅游规划内容")
            
            actual_data = result.get('plan_data', result)
            
            conversation_history = result.get('conversation_history', [])
            if not conversation_history:
                conversation_history = actual_data.get('conversation_history', [])
            
            if not self.llm_model:
                logger.warning("未提供AI模型，使用基础整合")
                return self._create_fallback_content(actual_data)
            
            cache_key = self._generate_cache_key(result, conversation_history)
            cached_content = self._get_cached_content(cache_key)
            if cached_content:
                logger.info("使用缓存的AI整合内容")
                return cached_content
            
            integrated_content = await self._ai_autonomous_content_integration(result, conversation_history)
            
            logger.info("AI自主旅游规划内容整合完成")
            
            if integrated_content.get('content_type') != 'rich_text' or not integrated_content.get('text_content'):
                logger.warning("AI生成的内容不符合预期，使用备用方案")
                return self._create_fallback_content(result)
            
            self._content_cache[cache_key] = {
                'content': integrated_content,
                'timestamp': datetime.now().timestamp()
            }
            
            return integrated_content
            
        except Exception as e:
            logger.error(f"AI自主整合旅游规划内容时发生错误: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return self._create_fallback_content(result.get('plan_data', result))
    
    def _generate_cache_key(self, result: Dict[str, Any], conversation_history: List[Dict] = None) -> str:
        plan_id = result.get('plan_id', 'unknown')
        history_str = json.dumps(conversation_history[-3:] if conversation_history else [], ensure_ascii=False)
        content_hash = hashlib.md5(history_str.encode()).hexdigest()[:10]
        return f"{plan_id}_{content_hash}"
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        if not cache_entry:
            return False
        timestamp = cache_entry.get('timestamp', 0)
        return (datetime.now().timestamp() - timestamp) < self._cache_timeout
    
    def _get_cached_content(self, cache_key: str) -> Dict[str, Any]:
        entry = self._content_cache.get(cache_key)
        if self._is_cache_valid(entry):
            return entry['content']
        return {}
    
    def _extract_actual_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if 'plan_data' in result:
            return result['plan_data']
        return result
    
    def _format_recommendations(self, recommendations: Dict[str, Any]) -> str:
        if not recommendations:
            return "暂无系统建议"
        
        lines = []
        if 'travel_tips' in recommendations and recommendations['travel_tips']:
            lines.append("实用贴士：")
            for tip in recommendations['travel_tips']:
                lines.append(f"- {tip}")
        
        if 'packing_list' in recommendations and recommendations['packing_list']:
            lines.append("\n打包清单：")
            for item in recommendations['packing_list']:
                lines.append(f"- {item}")
        
        if 'budget_estimate' in recommendations:
             lines.append("\n预算建议：请根据实际情况参考系统估算。")
             
        return "\n".join(lines)
    
    def _extract_conversation_history_list(self, result: Dict[str, Any]) -> List[Dict]:
        if 'conversation_history' in result:
            return result['conversation_history']
        return []

    def _get_unified_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        尝试从 UnifiedContext 获取更完整的上下文信息
        """
        if not session_id:
            return None
        
        try:
            from Agent.context import get_context_builder
            context_builder = get_context_builder()
            unified_context = context_builder.build_from_session(session_id)
            
            if unified_context:
                return {
                    'plan_data': unified_context.plan_data.model_dump() if unified_context.plan_data else {},
                    'heritage_items': [h.model_dump() for h in unified_context.plan_data.heritage_items] if unified_context.plan_data else [],
                    'cached_data': unified_context.cached_data,
                    'detected_intent': unified_context.detected_intent.value if unified_context.detected_intent else 'unknown',
                }
        except Exception as e:
            logger.warning(f"获取UnifiedContext失败: {e}")
        
        return None

    def _calculate_day_dates(self, start_date: str, travel_days: int) -> List[str]:
        """
        根据起始日期计算每天的日期
        默认从第二天开始
        """
        dates = []
        try:
            if start_date and start_date != '未指定':
                base_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                base_date = datetime.now() + timedelta(days=1)  # 默认从明天开始
            
            for i in range(travel_days):
                day_date = base_date + timedelta(days=i)
                dates.append(day_date.strftime('%Y-%m-%d'))
        except Exception:
            dates = [f"第{i+1}天" for i in range(travel_days)]
        
        return dates

    async def _ai_autonomous_content_integration(self, result: Dict[str, Any], conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        AI自主整合旅游规划内容
        """
        try:
            actual_data = self._extract_actual_data(result)
            
            session_id = result.get('session_id', '')
            unified_context = self._get_unified_context(session_id)
            
            if unified_context and unified_context.get('plan_data'):
                plan_data = unified_context['plan_data']
                destination = plan_data.get('departure_location', '陕西')
                heritage_items = unified_context.get('heritage_items', [])
            else:
                destination = self.content_extractor.extract_destination(actual_data)
                heritage_items = actual_data.get('heritage_items', [])
            
            travel_dates = self.content_extractor.extract_travel_dates(actual_data)
            travel_days = self.content_extractor.extract_travel_days(actual_data)
            weather_summary = self.content_extractor.format_weather_info(actual_data.get('weather_info', {}))
            sys_recs = self._format_recommendations(actual_data.get('recommendations', {}))
            
            basic_info = actual_data.get('basic_info', {})
            start_location = basic_info.get('departure', actual_data.get('departure_location', '未指定'))
            travel_mode = basic_info.get('travel_mode', actual_data.get('travel_mode', '自驾'))
            group_size = basic_info.get('group_size', actual_data.get('group_size', 1))
            budget_range = basic_info.get('budget_range', actual_data.get('budget_range', '中等'))
            
            formatted_history = await self._build_conversation_summary(conversation_history, actual_data)

            itinerary_raw = actual_data.get('itinerary', [])
            planned_item_names = set()
            for day in itinerary_raw:
                for item in day.get('items', []):
                    planned_item_names.add(item.get('name'))

            if not heritage_items and 'heritage_overview' in actual_data:
                heritage_items = actual_data['heritage_overview'].get('heritage_items', [])
            
            heritage_context_list = []
            for item in heritage_items:
                name = item.get('name', '未知项目')
                if name in planned_item_names:
                    desc = item.get('full_description') or item.get('description', '暂无详细介绍')
                    heritage_context_list.append(f"- **{name}** ({item.get('region', '')}): {desc[:300]}...")
            
            heritage_context_str = "\n".join(heritage_context_list) or "请基于目的地文化背景进行扩写。"
            
            slim_itinerary = []
            for day in itinerary_raw:
                day_weather = day.get('weather', {})
                weather_text = ''
                if day_weather:
                    cond = day_weather.get('condition', '')
                    temp = day_weather.get('temperature', '')
                    if cond or temp:
                        weather_text = f"{cond} {temp}".strip()
                
                day_slim = {
                    "day": day.get('day'),
                    "date": day.get('date', ''),
                    "weekday": day.get('weekday', ''),
                    "theme": day.get('theme'),
                    "pace": day.get('pace_label', ''),
                    "weather": weather_text,
                    "start_location": day.get('start_location', ''),
                    "items": [
                        {
                            "name": i.get('name'),
                            "time": i.get('time', '待定'),
                            "region": i.get('region', ''),
                            "category": i.get('category', ''),
                            "visit_duration": i.get('visit_duration', ''),
                            "distance_from_prev": i.get('distance_from_prev', ''),
                            "travel_time_hours": i.get('travel_time_hours', '')
                        }
                        for i in day.get('items', [])
                    ]
                }
                slim_itinerary.append(day_slim)
            slim_itinerary_json = json.dumps(slim_itinerary, ensure_ascii=False)
            
            route_info = actual_data.get('route_info', {})
            total_distance = route_info.get('total_distance', 0)
            route_summary = f"{total_distance}公里" if total_distance else "详见行程"
            
            day_dates = self._calculate_day_dates(travel_dates.split('~')[0].strip() if '~' in travel_dates else travel_dates, travel_days)
            day_dates_str = "、".join(day_dates) if day_dates else "根据实际出行日期"

            from Agent.prompts import get_pdf_content_prompt
            prompt = get_pdf_content_prompt(
                destination=destination,
                start_location=start_location,
                travel_days=travel_days,
                travel_dates=travel_dates,
                travel_mode=travel_mode,
                group_size=group_size,
                budget_range=budget_range,
                weather_summary=weather_summary,
                formatted_history=formatted_history,
                slim_itinerary_json=slim_itinerary_json,
                heritage_context_str=heritage_context_str,
                sys_recs=sys_recs,
                day_dates_str=day_dates_str,
                route_summary=route_summary
            )

            logger.info(f"发送 AI 请求。Prompt 长度: {len(prompt)} 字符")
            
            response = await self._call_llm_with_retry(prompt, timeout=540, max_retries=0)
            if not response:
                logger.error("LLM主内容生成超时，使用降级内容")
                return self._create_fallback_content(actual_data)
            if not response.get('success'):
                logger.error(f"LLM主内容生成API错误: {response.get('error', '未知错误')}")
                return self._create_fallback_content(actual_data)
            
            return {
                'content_type': 'rich_text',
                'text_content': response.get('content', '').strip(),
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'ai_generated': True,
                'source_data': {'destination': destination, 'travel_dates': travel_dates}
            }
                
        except Exception as e:
            logger.error(f"AI自主内容整合失败: {str(e)}")
            return self._create_fallback_content(result.get('plan_data', result))
    
    async def _call_llm_with_retry(self, prompt: str, timeout: int = 480, max_retries: int = 1) -> Optional[Dict]:
        for attempt in range(max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.llm_model._call_model(prompt), timeout=timeout
                )
                if response and response.get('success'):
                    return response
                logger.warning(f"LLM返回无效响应(尝试 {attempt+1}/{max_retries+1})")
            except asyncio.TimeoutError:
                if attempt < max_retries:
                    logger.warning(f"LLM第{attempt+1}次超时({timeout}s)，{2}s后重试...")
                    await asyncio.sleep(2)
                else:
                    logger.warning(f"LLM主内容生成超时({timeout}s)，已重试{max_retries}次，使用降级内容")
                    return None
            except Exception as e:
                logger.error(f"LLM调用异常(尝试 {attempt+1}/{max_retries+1}): {e}")
                if attempt >= max_retries:
                    return None
        return None

    async def _build_conversation_summary(self, conversation_history: List[Dict] = None, actual_data: Dict = None) -> str:
        if not conversation_history and actual_data:
            conversation_history = self._extract_conversation_history_list(actual_data)
        
        if not conversation_history:
            return "暂无特殊要求。"
        
        try:
            conversation_text = self._format_conversation_to_text(conversation_history)
            
            logger.info(f"开始对 {len(conversation_history)} 条对话历史进行智能摘要...")
            
            summary_prompt = get_conversation_summary_prompt(
                conversation_history=conversation_text
            )
            
            try:
                response = await asyncio.wait_for(self.llm_model._call_model(summary_prompt), timeout=60)
            except asyncio.TimeoutError:
                logger.warning("LLM摘要生成超时(60s)，使用降级方案")
                return self._build_conversation_summary_fallback(conversation_history)
            
            if response and response.get('success'):
                summary = response.get('content', '').strip()
                logger.info(f"对话历史摘要生成完成，摘要长度: {len(summary)} 字符")
                return summary
            else:
                logger.warning("LLM 摘要生成失败，使用降级方案")
                return self._build_conversation_summary_fallback(conversation_history)
                
        except Exception as e:
            logger.error(f"对话历史摘要生成失败，降级为简单截取: {str(e)}")
            return self._build_conversation_summary_fallback(conversation_history)
    
    def _format_conversation_to_text(self, conversation_history: List[Dict]) -> str:
        lines = []
        for idx, msg in enumerate(conversation_history, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if role == 'user':
                lines.append(f"{idx}. 用户: {content}")
            elif role == 'assistant':
                lines.append(f"{idx}. 助手: {content}")
        
        return "\n".join(lines)
    
    def _build_conversation_summary_fallback(self, conversation_history: List[Dict]) -> str:
        user_demands = []
        
        for msg in conversation_history[-8:]:
            role = "用户" if msg.get('role') == 'user' else "助手"
            content = msg.get('content', '')[:200]
            user_demands.append(f"{role}: {content}")
        
        return "\n".join(user_demands) if user_demands else "暂无特殊要求。"
    
    def _create_fallback_content(self, result: Dict[str, Any]) -> Dict[str, Any]:
        actual_data = result if not isinstance(result, dict) or 'plan_data' not in result else result.get('plan_data', result)
        if not isinstance(actual_data, dict):
            actual_data = {}

        destination = actual_data.get('departure_location', '陕西')
        travel_days = actual_data.get('travel_days', 3)

        lines = [
            f"# {destination}非遗旅行路书",
            "",
            "> ⚠️ **导出异常**：AI内容生成超时，此PDF为空壳路书，请重新导出。",
            "",
            f"目的地：{destination} | 天数：{travel_days}天",
            "",
            "---",
            "",
            "此路书因AI生成超时未包含详细内容，请关闭后重新点击「导出包含修改的PDF」。",
        ]

        return {
            'content_type': 'rich_text',
            'text_content': "\n".join(lines),
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'ai_generated': False,
            'source_data': {'destination': destination, 'travel_days': travel_days}
        }
