# -*- coding: utf-8 -*-
"""
旅游规划核心模块
负责整合各种信息，生成符合地理逻辑的旅游规划，使用真实道路距离进行路线优化
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from Agent.services.heritage_analyzer import get_heritage_analyzer
from Agent.services.weather import get_weather_service
from Agent.services.mcp_client import get_mcp_client
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
                               progress_callback: Optional[callable] = None,
                               skip_ai_suggestions: bool = False) -> Dict[str, Any]:
        """创建旅游规划
        
        Args:
            planning_request: 规划请求参数
            progress_callback: 进度回调函数
            skip_ai_suggestions: 是否跳过AI建议生成（简单规划模式）
        """
        try:
            plan_id = planning_request.get('plan_id', f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            logger.info(f"开始创建旅游规划: {plan_id}, 简单模式: {skip_ai_suggestions}")
            
            steps = [
                '分析非遗项目',
                '获取天气信息',
                '路径规划计算',
                '生成路书',
                '完成'
            ]
            if not skip_ai_suggestions:
                steps.insert(2, '生成AI建议')
            
            self.planning_progress[plan_id] = {
                'status': 'processing',
                'progress': 0,
                'current_step': '初始化',
                'steps': steps,
                'start_time': datetime.now().isoformat(),
                'simple_mode': skip_ai_suggestions
            }
            
            if progress_callback:
                await progress_callback(plan_id, self.planning_progress[plan_id])
            
            progress_step = 10
            await self._update_progress(plan_id, progress_step, '分析非遗项目', progress_callback)
            heritage_analysis = await self.heritage_analyzer.analyze_heritage_items(
                planning_request.get('heritage_ids', [])
            )
            
            if not heritage_analysis.get('success'):
                return self._create_error_result(plan_id, '非遗项目分析失败', heritage_analysis.get('error'))
            
            progress_step = 30
            await self._update_progress(plan_id, progress_step, '获取天气信息', progress_callback)
            weather_data = await self._get_weather_for_locations(
                heritage_analysis['heritage_items'],
                planning_request.get('travel_days', 3)
            )
            
            ai_suggestions = {'suggestions': '', 'travel_tips': [], 'packing_list': []}
            if not skip_ai_suggestions:
                progress_step = 50
                await self._update_progress(plan_id, progress_step, '生成AI建议', progress_callback)
                ai_suggestions = await self._generate_ai_suggestions(
                    heritage_analysis,
                    weather_data,
                    planning_request
                )
            
            progress_step = 70 if skip_ai_suggestions else 70
            await self._update_progress(plan_id, progress_step, '路径规划计算', progress_callback)
            optimized_route = await self._optimize_travel_route_v2(
                heritage_analysis['heritage_items'],
                weather_data,
                planning_request
            )
            
            progress_step = 90
            await self._update_progress(plan_id, progress_step, '生成路书', progress_callback)
            complete_plan = await self._generate_complete_plan(
                heritage_analysis,
                weather_data,
                ai_suggestions,
                optimized_route,
                planning_request
            )
            
            complete_plan['estimated_time'] = "2-5分钟"
            complete_plan['simple_mode'] = skip_ai_suggestions

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
            
            special_req_str = '、'.join(special_requirements) if special_requirements else '无'
            
            prompt = get_ai_suggestions_prompt(
                departure_location=departure_location,
                travel_days=travel_days,
                people_count=group_size,
                budget_range=budget_range,
                travel_mode=travel_mode,
                heritage_names=heritage_names,
                special_requirements=special_req_str,
                current_date=datetime.now().strftime('%Y年%m月%d日')
            )
            
            ai_response = await self.llm_model._call_model(prompt)
            
            logger.info("AI建议生成完成")
            
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
                    'travel_mode': travel_mode,
                    'special_requirements': special_requirements
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
        基于出发地的路径优化算法 (使用百度地图真实道路距离)
        解决"路线乱跳"和"回头路"问题，提供准确的距离和时间估算
        """
        try:
            start_location = request.get('departure_location', '')
            travel_days = request.get('travel_days', 3)
            travel_mode = request.get('travel_mode', 'driving')
            
            mode_map = {
                '自驾': 'driving',
                '公共交通': 'transit', 
                '步行': 'walking',
                '骑行': 'riding'
            }
            api_mode = mode_map.get(travel_mode, 'driving')
            
            safe_travel_days = max(1, int(travel_days))
            
            logger.info(f"开始路径规划(真实道路距离)，出发地: {start_location}, 项目数: {len(items)}, 天数: {safe_travel_days}, 出行方式: {api_mode}")
            
            if not items:
                return {'daily_itinerary': []}

            mcp_client = get_mcp_client()

            start_coords = await self._get_coordinates(start_location)
            
            unvisited = []
            for item in items:
                try:
                    lat = float(item.get('latitude', 0))
                    lng = float(item.get('longitude', 0))
                    
                    if not lat or not lng:
                        addr = item.get('address') or item.get('region') or item.get('name')
                        c = await self._get_coordinates(addr)
                        if c:
                            lat, lng = c
                            item['latitude'] = lat
                            item['longitude'] = lng

                    if lat and lng:
                        item['visit_duration'] = float(item.get('visit_duration') or 2.0)
                        unvisited.append({
                            'id': item.get('id'),
                            'data': item,
                            'coords': (lat, lng),
                            'location_str': f"{lat},{lng}"
                        })
                except:
                    continue
            
            if not unvisited:
                return self._fallback_itinerary(items, safe_travel_days)

            start_location_str = f"{start_coords[0]},{start_coords[1]}"
            all_locations = [start_location_str] + [p['location_str'] for p in unvisited]
            
            logger.info(f"计算距离矩阵: {len(all_locations)} 个位置")
            
            matrix_result = await mcp_client.map_distance_matrix(
                origins=all_locations,
                destinations=all_locations,
                mode=api_mode
            )
            
            if matrix_result.get('success') and matrix_result.get('matrix'):
                distance_matrix = matrix_result['matrix']
                logger.info("距离矩阵计算成功，使用真实道路距离")
                use_real_distance = True
            else:
                logger.warning(f"距离矩阵计算失败: {matrix_result.get('error')}，使用直线距离")
                use_real_distance = False
                distance_matrix = None

            ordered_route = []
            current_idx = 0
            remaining_indices = list(range(1, len(all_locations)))
            
            while remaining_indices:
                nearest_idx = -1
                min_dist = float('inf')
                min_duration = 0
                
                for idx in remaining_indices:
                    if use_real_distance and distance_matrix:
                        try:
                            cell = distance_matrix[current_idx][idx]
                            dist = cell.get('distance', float('inf'))
                            duration = cell.get('duration', 0)
                        except (IndexError, TypeError):
                            from geopy.distance import geodesic as geo_geodesic
                            coord1 = (float(all_locations[current_idx].split(',')[0]), 
                                     float(all_locations[current_idx].split(',')[1]))
                            coord2 = (float(all_locations[idx].split(',')[0]),
                                     float(all_locations[idx].split(',')[1]))
                            dist = geo_geodesic(coord1, coord2).kilometers * 1000
                            duration = dist / 1000 / 60 * 3600
                    else:
                        from geopy.distance import geodesic as geo_geodesic
                        coord1 = (float(all_locations[current_idx].split(',')[0]), 
                                 float(all_locations[current_idx].split(',')[1]))
                        coord2 = (float(all_locations[idx].split(',')[0]),
                                 float(all_locations[idx].split(',')[1]))
                        dist = geo_geodesic(coord1, coord2).kilometers * 1000
                        duration = dist / 1000 / 60 * 3600
                    
                    if dist < min_dist:
                        min_dist = dist
                        min_duration = duration
                        nearest_idx = idx
                
                if nearest_idx != -1:
                    remaining_indices.remove(nearest_idx)
                    
                    point = unvisited[nearest_idx - 1]
                    point_data = point['data'].copy()
                    
                    dist_km = round(min_dist / 1000, 1)
                    duration_hours = round(min_duration / 3600, 1)
                    
                    point_data['distance_from_prev'] = dist_km
                    point_data['travel_time_hours'] = duration_hours
                    point_data['distance_type'] = '真实道路距离' if use_real_distance else '直线距离'
                    
                    ordered_route.append(point_data)
                    current_idx = nearest_idx
                else:
                    break
            
            daily_itinerary = []
            items_per_day = len(ordered_route) / safe_travel_days
            
            current_item_idx = 0
            
            weather_locations = weather_data.get('locations', {}) if weather_data.get('success') else {}
            
            from datetime import datetime, timedelta
            today = datetime.now().date()
            start_date = today + timedelta(days=1)
            
            for day in range(1, safe_travel_days + 1):
                day_items = []
                
                end_idx = int(round(items_per_day * day))
                
                while current_item_idx < end_idx and current_item_idx < len(ordered_route):
                    day_items.append(ordered_route[current_item_idx])
                    current_item_idx += 1
                
                if day == safe_travel_days:
                    while current_item_idx < len(ordered_route):
                        day_items.append(ordered_route[current_item_idx])
                        current_item_idx += 1

                day_date = start_date + timedelta(days=day - 1)
                day_date_str = day_date.strftime('%Y年%m月%d日')
                day_weekday = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][day_date.weekday()]

                day_weather_info = None
                if day_items and weather_locations:
                    representative_item = day_items[0].get('name')
                    specific_location_weather = weather_locations.get(representative_item)
                    
                    if not specific_location_weather:
                        specific_location_weather = list(weather_locations.values())[0] if weather_locations else None
                    
                    if specific_location_weather:
                        forecast_list = specific_location_weather.get('forecast', [])
                        if forecast_list and (day - 1) < len(forecast_list):
                            w = forecast_list[day - 1]
                            day_weather_info = {
                                'condition': w.get('weather_description', '未知'),
                                'temperature': f"{w.get('min_temp', 0)}~{w.get('max_temp', 0)}°C",
                                'suitability': w.get('travel_suitability', {}).get('level', '适宜'),
                                'location_ref': representative_item
                            }

                day_plan = {
                    'day': day,
                    'date': day_date_str,
                    'weekday': day_weekday,
                    'theme': self._generate_day_theme(day_items),
                    'items': day_items,
                    'start_location': start_location if day == 1 else "上一个目的地",
                    'weather': day_weather_info,
                    'pace_label': self._analyze_pace_label(len(day_items)),
                    'recommendations': []
                }
                daily_itinerary.append(day_plan)
            
            total_distance = sum(item.get('distance_from_prev', 0) for item in ordered_route)
            
            return {
                'daily_itinerary': daily_itinerary,
                'total_distance': total_distance,
                'optimization_notes': [
                    f"路线已优化：从 {start_location} 出发，顺路游览",
                    f"使用{'真实道路距离' if use_real_distance else '直线距离'}计算",
                    f"出行方式：{travel_mode}"
                ]
            }
            
        except Exception as e:
            logger.error(f"路径规划失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
                'travel_days': planning_request.get('travel_days', 3),
                'group_size': planning_request.get('group_size', 2),
                'budget_range': planning_request.get('budget_range', '中等'),
                'special_requirements': planning_request.get('special_requirements', [])
            },
            
            'heritage_items': heritage_analysis.get('heritage_items', []),
            'itinerary': itinerary,
            'pace_analysis': pace_summary,
            'weather_info': weather_data,
            'heritage_overview': {
                'heritage_items': heritage_analysis.get('heritage_items', [])
            },
            'route_info': {
                'total_distance': optimized_route.get('total_distance', 0),
                'optimization_notes': optimized_route.get('optimization_notes', [])
            },
            'special_requirements': planning_request.get('special_requirements', []),
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