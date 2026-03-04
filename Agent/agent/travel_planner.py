# -*- coding: utf-8 -*-
"""
旅游规划核心模块
负责整合各种信息，生成符合地理逻辑的旅游规划，移除生硬时间计算，增加行程节奏分析
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from geopy.distance import geodesic
from Agent.services.heritage_analyzer import get_heritage_analyzer
from Agent.services.weather import get_weather_service
from Agent.models.llm_model import get_llm_model

class TravelPlanner:
    """
    旅游规划器
    负责生成完整的旅游规划方案
    """
    
    def __init__(self):
        """
        初始化旅游规划器
        """
        self.heritage_analyzer = get_heritage_analyzer()
        self.weather_service = get_weather_service()
        self.llm_model = get_llm_model()
        self.planning_progress = {}
        
        logger.info("旅游规划器初始化完成")
    
    async def create_travel_plan(self, 
                               planning_request: Dict[str, Any],
                               progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """创建旅游规划"""
        try:
            plan_id = planning_request.get('plan_id', f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            logger.info(f"开始创建旅游规划: {plan_id}")
            
            # 初始化进度
            self.planning_progress[plan_id] = {
                'status': 'processing',
                'progress': 0,
                'current_step': '初始化',
                'steps': [
                    '分析非遗项目',
                    '获取天气信息',
                    '生成AI建议',
                    '路径规划计算',
                    '生成路书',
                    '完成'
                ],
                'start_time': datetime.now().isoformat()
            }
            
            if progress_callback:
                await progress_callback(plan_id, self.planning_progress[plan_id])
            
            await self._update_progress(plan_id, 10, '分析非遗项目', progress_callback)
            heritage_analysis = await self.heritage_analyzer.analyze_heritage_items(
                planning_request.get('heritage_ids', [])
            )
            
            if not heritage_analysis.get('success'):
                return self._create_error_result(plan_id, '非遗项目分析失败', heritage_analysis.get('error'))
            
            # 步骤2: 获取天气信息
            await self._update_progress(plan_id, 30, '获取天气信息', progress_callback)
            weather_data = await self._get_weather_for_locations(
                heritage_analysis['heritage_items'],
                planning_request.get('travel_days', 3)
            )
            
            # 步骤3: 生成AI建议
            await self._update_progress(plan_id, 50, '生成AI建议', progress_callback)
            ai_suggestions = await self._generate_ai_suggestions(
                heritage_analysis,
                weather_data,
                planning_request
            )
            
            # 步骤4: 优化路线规划
            await self._update_progress(plan_id, 70, '优化路线规划', progress_callback)
            # 使用 v2 版本的路径规划，强制考虑出发地
            optimized_route = await self._optimize_travel_route_v2(
                heritage_analysis['heritage_items'],
                weather_data,
                planning_request
            )
            
            # 步骤5: 生成完整方案
            await self._update_progress(plan_id, 90, '生成路书', progress_callback)
            complete_plan = await self._generate_complete_plan(
                heritage_analysis,
                weather_data,
                ai_suggestions,
                optimized_route,
                planning_request
            )
            
            # 确保返回数据中包含前端需要的 estimated_time
            complete_plan['estimated_time'] = "2-5分钟"

            # 步骤6: 完成规划
            await self._update_progress(plan_id, 100, '完成', progress_callback)
            
            # 更新最终状态
            self.planning_progress[plan_id].update({
                'status': 'completed',
                'progress': 100,
                'current_step': '规划完成',
                'end_time': datetime.now().isoformat(),
                'result': complete_plan
            })
            
            if progress_callback:
                await progress_callback(plan_id, self.planning_progress[plan_id])
            
            logger.info(f"旅游规划创建完成: {plan_id}")
            return complete_plan
            
        except Exception as e:
            logger.error(f"创建旅游规划时发生错误: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return self._create_error_result(plan_id, '规划创建失败', str(e))
    
    async def _update_progress(self, 
                             plan_id: str, 
                             step: int, 
                             step_name: str, 
                             progress_callback: Optional[callable] = None):
        """
        更新规划进度
        """
        if plan_id in self.planning_progress:
            current_progress = self.planning_progress[plan_id].get('progress', 0)
            new_progress = max(current_progress, min(95, step))
            
            self.planning_progress[plan_id].update({
                'progress': new_progress,
                'current_step': step_name
            })
            
            logger.info(f"进度更新: {plan_id} -> {new_progress}% - {step_name}")
            
            if progress_callback:
                await progress_callback(plan_id, self.planning_progress[plan_id])
    
    async def _get_weather_for_locations(self, 
                                       heritage_items: List[Dict[str, Any]], 
                                       days: int) -> Dict[str, Any]:
        """
        获取所有位置的天气信息
        """
        locations = []
        for item in heritage_items:
            try:
                lat = float(item.get('latitude', 0))
                lng = float(item.get('longitude', 0))
                if lat and lng:
                    locations.append({
                        'name': item['name'],
                        'lat': lat,
                        'lng': lng
                    })
            except:
                continue
        
        if not locations:
            # 如果没有有效坐标，尝试给一个默认的西安坐标，防止天气模块报错
            return await self.weather_service.get_multi_location_weather(
                [{'name': '西安', 'lat': 34.3416, 'lng': 108.9398}], days
            )
        
        return await self.weather_service.get_multi_location_weather(locations, days)
    
    async def _generate_ai_suggestions(self, 
                                     heritage_analysis: Dict[str, Any],
                                     weather_data: Dict[str, Any],
                                     planning_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成AI建议，基于用户参数提供个性化建议
        """
        try:
            from Agent.prompts import get_ai_suggestions_prompt
            
            travel_days = planning_request.get('travel_days', 3)
            departure_location = planning_request.get('departure_location', '')
            group_size = planning_request.get('group_size', 2)
            budget_range = planning_request.get('budget_range', '中等')
            travel_mode = planning_request.get('travel_mode', '自驾')
            special_requirements = planning_request.get('special_requirements', [])
            
            heritage_items = heritage_analysis.get('heritage_items', [])
            heritage_names = ', '.join([item['name'] for item in heritage_items])
            
            prompt = get_ai_suggestions_prompt(
                departure_location=departure_location,
                travel_days=travel_days,
                people_count=group_size,
                budget_range=budget_range,
                travel_mode=travel_mode,
                heritage_names=heritage_names
            )
            
            ai_response = await self.llm_model._call_model(prompt)
            
            logger.info(f"AI建议生成完成")
            
            return {
                'suggestions': ai_response.get('content', '请参考生成的深度路书'),
                'travel_tips': [],
                'packing_list': [],
                'budget_estimate': {},
                'user_params': {
                    'departure_location': departure_location,
                    'travel_days': travel_days,
                    'group_size': group_size,
                    'budget_range': budget_range,
                    'travel_mode': travel_mode
                }
            }
        except Exception as e:
            logger.error(f"生成AI建议时发生错误: {str(e)}")
            return {
                'suggestions': '请参考生成的深度路书',
                'travel_tips': [],
                'packing_list': [],
                'budget_estimate': {},
                'error': str(e)
            }

    # 百度地图 API 集成

    async def _get_coordinates(self, location_name: str) -> tuple:
        """
        获取地理位置坐标（通过统一地理编码服务）
        """
        from ..services.geocoding import get_geocoding_service
        
        geocoding = get_geocoding_service()
        coords = await geocoding.get_coordinates(location_name)
        return coords if coords else geocoding.get_default_coordinates()

    async def _optimize_travel_route_v2(self, 
                                      items: List[Dict[str, Any]], 
                                      weather_data: Dict[str, Any],
                                      request: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于出发地的路径优化算法 (贪婪算法 + 距离加权)
        解决"路线乱跳"和"回头路"问题
        """
        try:
            start_location = request.get('departure_location', '')
            travel_days = request.get('travel_days', 3)
            
            # 确保天数至少为1天，防止除零错误
            safe_travel_days = max(1, int(travel_days))
            
            logger.info(f"开始路径规划，出发地: {start_location}, 项目数: {len(items)}, 天数: {safe_travel_days}")
            
            if not items:
                return {'daily_itinerary': []}

            # 1. 确定起点坐标
            start_coords = await self._get_coordinates(start_location)
            
            # 2. 准备所有待访问点
            unvisited = []
            for item in items:
                try:
                    lat = float(item.get('latitude', 0))
                    lng = float(item.get('longitude', 0))
                    
                    # 尝试补全坐标
                    if not lat or not lng:
                        addr = item.get('address') or item.get('region') or item.get('name')
                        c = await self._get_coordinates(addr)
                        if c:
                            lat, lng = c
                            # 回填，方便后续使用
                            item['latitude'] = lat
                            item['longitude'] = lng

                    if lat and lng:
                        # 确保 visit_duration 有默认值
                        item['visit_duration'] = float(item.get('visit_duration') or 2.0)
                        unvisited.append({
                            'id': item.get('id'),
                            'data': item,
                            'coords': (lat, lng)
                        })
                except:
                    continue
            
            # 如果没有坐标，就按原顺序返回（兜底）
            if not unvisited:
                return self._fallback_itinerary(items, safe_travel_days)

            # 3. 路径排序 (贪婪算法：每次找离当前点最近的点)
            ordered_route = []
            current_coords = start_coords
            
            while unvisited:
                # 寻找最近的下一个点
                nearest_idx = -1
                min_dist = float('inf')
                
                for i, point in enumerate(unvisited):
                    dist = geodesic(current_coords, point['coords']).kilometers
                    if dist < min_dist:
                        min_dist = dist
                        nearest_idx = i
                
                if nearest_idx != -1:
                    next_point = unvisited.pop(nearest_idx)
                    # 加上路程信息
                    dist_val = round(min_dist, 1)
                    next_point['data']['distance_from_prev'] = dist_val
                    # 简单估算车程 (60km/h)
                    next_point['data']['travel_time_hours'] = round(dist_val / 60, 1)
                    
                    ordered_route.append(next_point['data'])
                    current_coords = next_point['coords']
                else:
                    break
            
            # 4. 按天分组 (考虑每天的容量)
            daily_itinerary = []
            # 使用安全的天数变量
            items_per_day = len(ordered_route) / safe_travel_days
            
            current_item_idx = 0
            
            # 获取全量天气位置映射
            weather_locations = weather_data.get('locations', {}) if weather_data.get('success') else {}
            
            for day in range(1, safe_travel_days + 1):
                day_items = []
                
                # 计算当天应该分配到的索引范围
                end_idx = int(round(items_per_day * day))
                
                while current_item_idx < end_idx and current_item_idx < len(ordered_route):
                    day_items.append(ordered_route[current_item_idx])
                    current_item_idx += 1
                
                # 如果是最后一天，把剩下的全塞进去
                if day == safe_travel_days:
                    while current_item_idx < len(ordered_route):
                        day_items.append(ordered_route[current_item_idx])
                        current_item_idx += 1

                # 注入当天特定地点的天气
                day_weather_info = None
                if day_items and weather_locations:
                    # 规则：以当天第一个景点作为该天的天气参考中心
                    representative_item = day_items[0].get('name')
                    # 从天气库中查找对应的地点数据
                    specific_location_weather = weather_locations.get(representative_item)
                    
                    # 兜底：如果没找到对应地点，尝试取第一个可用的位置
                    if not specific_location_weather:
                        specific_location_weather = list(weather_locations.values())[0] if weather_locations else None
                    
                    if specific_location_weather:
                        forecast_list = specific_location_weather.get('forecast', [])
                        # 按天数索引提取匹配的预报（注意 day 从 1 开始，索引从 0 开始）
                        if forecast_list and (day - 1) < len(forecast_list):
                            w = forecast_list[day - 1]
                            day_weather_info = {
                                'condition': w.get('weather_description', '未知'),
                                'temperature': f"{w.get('min_temp', 0)}~{w.get('max_temp', 0)}°C",
                                'suitability': w.get('travel_suitability', {}).get('level', '适宜'),
                                'location_ref': representative_item  # 记录参考地点方便前端展示
                            }

                # 生成当天的行程结构
                day_plan = {
                    'day': day,
                    'theme': self._generate_day_theme(day_items),
                    'items': day_items,
                    'start_location': start_location if day == 1 else "上一个目的地",
                    'weather': day_weather_info,
                    'pace_label': self._analyze_pace_label(len(day_items)),
                    'recommendations': []
                }
                daily_itinerary.append(day_plan)
            
            return {
                'daily_itinerary': daily_itinerary,
                'total_distance': 0, 
                'optimization_notes': [f"路线已优化：从 {start_location} 出发，顺路游览"]
            }
            
        except Exception as e:
            logger.error(f"路径规划失败: {str(e)}")
            return self._fallback_itinerary(items, request.get('travel_days', 3))

    def _analyze_pace_label(self, item_count):
        """分析当天的节奏"""
        if item_count <= 1: return "🧘 悠闲漫游"
        if item_count == 2: return "🚶 舒适探索"
        if item_count == 3: return "🏃 充实紧凑"
        return "🔥 特种兵打卡"

    def _fallback_itinerary(self, items, days):
        """兜底的行程生成逻辑"""
        daily = []
        if days <= 0: days = 3
        per_day = len(items) // days + 1
        for i in range(days):
            batch = items[i*per_day : (i+1)*per_day]
            daily.append({
                'day': i+1, 
                'items': batch, 
                'theme': '文化探索',
                'pace_label': '🧘 悠闲漫游'
            })
        return {'daily_itinerary': daily}

    def _generate_day_theme(self, items: List[Dict]) -> str:
        """根据当天的项目生成一个主题词"""
        if not items: return "自由探索与休整"
        
        # 统计地区
        regions = list(set([i.get('region', '').replace('市','').replace('省','').replace('区','').replace('县','') for i in items]))
        if regions:
            return f"{'/'.join(regions[:2])}深度体验"
        
        # 统计类别
        categories = [i.get('category', '') for i in items]
        if '民俗' in categories: return "民俗风情体验"
        if '传统技艺' in categories: return "匠心技艺探访"
        
        return "非遗文化之旅"
    
    async def _generate_complete_plan(self, 
                                    heritage_analysis: Dict[str, Any],
                                    weather_data: Dict[str, Any],
                                    ai_suggestions: Dict[str, Any],
                                    optimized_route: Dict[str, Any],
                                    planning_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成完整的旅游规划结构
        """
        plan_id = planning_request.get('plan_id', f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        itinerary = optimized_route.get('daily_itinerary', [])
        
        # 行程节奏分析
        pace_summary = {
            'overall_pace': "舒适", # 默认
            'busy_days': [d['day'] for d in itinerary if '特种兵' in d.get('pace_label','')],
            'relax_days': [d['day'] for d in itinerary if '悠闲' in d.get('pace_label','')],
            'highlights': [i['name'] for day in itinerary for i in day['items']][:5]
        }
        
        complete_plan = {
            'success': True,
            'plan_id': plan_id,
            'created_at': datetime.now().isoformat(),
            'user_id': planning_request.get('user_id'),
            
            # 基本信息
            'basic_info': {
                'title': f"{planning_request.get('departure_location', '陕西')}出发 - 非遗深度游",
                'duration': f"{planning_request.get('travel_days', 3)}天",
                'departure': planning_request.get('departure_location', ''),
                'travel_mode': planning_request.get('travel_mode', '自驾'),
                'group_size': planning_request.get('group_size', 2),
                'budget_range': planning_request.get('budget_range', '中等')
            },
            
            'heritage_items': heritage_analysis.get('heritage_items', []),
            'itinerary': itinerary,
            'pace_analysis': pace_summary,  # 行程节奏分析
            'weather_info': weather_data,
            'heritage_overview': {
                'heritage_items': heritage_analysis.get('heritage_items', []) # 确保数据在 overview 里也有一份
            },
            'route_info': {
                'total_distance': optimized_route.get('total_distance', 0),
                'optimization_notes': optimized_route.get('optimization_notes', [])
            },
            'export_info': {
                'exportable': True,
                'formats': ['PDF', 'CSV', 'JSON'],
                'filename': f"非遗旅游规划_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
        }
        
        return complete_plan
    
    def _create_error_result(self, plan_id: str, error_type: str, error_message: str) -> Dict[str, Any]:
        """
        创建错误结果
        """
        if plan_id in self.planning_progress:
            self.planning_progress[plan_id].update({
                'status': 'error',
                'error_type': error_type,
                'error_message': error_message,
                'end_time': datetime.now().isoformat()
            })
        
        return {
            'success': False,
            'plan_id': plan_id,
            'error_type': error_type,
            'error_message': error_message,
            'created_at': datetime.now().isoformat()
        }
    
    def get_planning_progress(self, plan_id: str) -> Dict[str, Any]:
        """
        获取规划进度
        """
        return self.planning_progress.get(plan_id, {
            'status': 'not_found',
            'error': '规划不存在'
        })
    
    def get_planning_result(self, plan_id: str) -> Dict[str, Any]:
        """
        获取规划结果
        """
        progress_data = self.planning_progress.get(plan_id, {})
        if progress_data.get('status') == 'completed':
            return progress_data.get('result')
        return None
    
    def cleanup_old_progress(self, hours: int = 24):
        """
        清理旧的进度记录
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        to_remove = []
        for plan_id, progress in self.planning_progress.items():
            start_time_str = progress.get('start_time')
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str)
                    if start_time < cutoff_time:
                        to_remove.append(plan_id)
                except ValueError:
                    to_remove.append(plan_id)
        
        for plan_id in to_remove:
            del self.planning_progress[plan_id]
        
        if to_remove:
            logger.info(f"清理了{len(to_remove)}个过期的规划进度记录")

# 单例模式获取旅游规划器实例
_travel_planner_instance = None

def get_travel_planner() -> TravelPlanner:
    """
    获取旅游规划器单例实例
    """
    global _travel_planner_instance
    if _travel_planner_instance is None:
        _travel_planner_instance = TravelPlanner()
    return _travel_planner_instance