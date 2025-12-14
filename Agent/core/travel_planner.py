# -*- coding: utf-8 -*-
"""
旅游规划核心模块
负责整合各种信息，生成完整的旅游规划
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from .heritage_analyzer import HeritageAnalyzer
from .weather_service import get_weather_service
from .ali_model import get_ali_model

class TravelPlanner:
    """
    旅游规划器
    负责生成完整的旅游规划方案
    """
    
    def __init__(self):
        """
        初始化旅游规划器
        """
        self.heritage_analyzer = HeritageAnalyzer()
        self.weather_service = get_weather_service()
        self.ali_model = get_ali_model()
        self.planning_progress = {}
        logger.info("旅游规划器初始化完成")
    
    async def create_travel_plan(self, 
                               planning_request: Dict[str, Any],
                               progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        创建旅游规划
        
        Args:
            planning_request (Dict[str, Any]): 规划请求参数
            progress_callback (Optional[callable]): 进度回调函数
        
        Returns:
            Dict[str, Any]: 旅游规划结果
        """
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
                    '优化路线规划',
                    '生成完整方案',
                    '完成规划'
                ],
                'start_time': datetime.now().isoformat()
            }
            
            if progress_callback:
                await progress_callback(plan_id, self.planning_progress[plan_id])
            
            # 步骤1: 分析非遗项目
            await self._update_progress(plan_id, 1, '分析非遗项目', progress_callback)
            heritage_analysis = await self.heritage_analyzer.analyze_heritage_items(
                planning_request.get('heritage_ids', [])
            )
            
            if not heritage_analysis.get('success'):
                return self._create_error_result(plan_id, '非遗项目分析失败', heritage_analysis.get('error'))
            
            # 步骤2: 获取天气信息
            await self._update_progress(plan_id, 2, '获取天气信息', progress_callback)
            weather_data = await self._get_weather_for_locations(
                heritage_analysis['heritage_items'],
                planning_request.get('travel_days', 3)
            )
            
            # 步骤3: 生成AI建议
            await self._update_progress(plan_id, 3, '生成AI建议', progress_callback)
            ai_suggestions = await self._generate_ai_suggestions(
                heritage_analysis,
                weather_data,
                planning_request
            )
            
            # 步骤4: 优化路线规划
            await self._update_progress(plan_id, 4, '优化路线规划', progress_callback)
            optimized_route = await self._optimize_travel_route(
                heritage_analysis,
                weather_data,
                planning_request
            )
            
            # 步骤5: 生成完整方案
            await self._update_progress(plan_id, 5, '生成完整方案', progress_callback)
            complete_plan = await self._generate_complete_plan(
                heritage_analysis,
                weather_data,
                ai_suggestions,
                optimized_route,
                planning_request
            )
            
            # 步骤6: 完成规划
            await self._update_progress(plan_id, 6, '完成规划', progress_callback)
            
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
            return self._create_error_result(plan_id, '规划创建失败', str(e))
    
    async def _update_progress(self, 
                             plan_id: str, 
                             step: int, 
                             step_name: str, 
                             progress_callback: Optional[callable] = None):
        """
        更新规划进度
        
        Args:
            plan_id (str): 规划ID
            step (int): 当前步骤
            step_name (str): 步骤名称
            progress_callback (Optional[callable]): 进度回调函数
        """
        if plan_id in self.planning_progress:
            progress = min(95, int((step / 6) * 100))  # 最大95%，留5%给最终完成，转换为整数
            self.planning_progress[plan_id].update({
                'progress': progress,
                'current_step': step_name
            })
            
            if progress_callback:
                await progress_callback(plan_id, self.planning_progress[plan_id])
    
    async def _get_weather_for_locations(self, 
                                       heritage_items: List[Dict[str, Any]], 
                                       days: int) -> Dict[str, Any]:
        """
        获取所有位置的天气信息
        
        Args:
            heritage_items (List[Dict[str, Any]]): 非遗项目列表
            days (int): 天数
        
        Returns:
            Dict[str, Any]: 天气信息
        """
        locations = []
        for item in heritage_items:
            if item.get('latitude') and item.get('longitude'):
                locations.append({
                    'name': item['name'],
                    'lat': float(item['latitude']),
                    'lng': float(item['longitude'])
                })
        
        if not locations:
            logger.warning("没有有效的地理位置信息")
            return {'success': False, 'error': '没有有效的地理位置信息'}
        
        return await self.weather_service.get_multi_location_weather(locations, days)
    
    async def _generate_ai_suggestions(self, 
                                     heritage_analysis: Dict[str, Any],
                                     weather_data: Dict[str, Any],
                                     planning_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成AI建议
        
        Args:
            heritage_analysis (Dict[str, Any]): 非遗项目分析结果
            weather_data (Dict[str, Any]): 天气数据
            planning_request (Dict[str, Any]): 规划请求
        
        Returns:
            Dict[str, Any]: AI建议
        """
        try:
            # 构建AI提示词的上下文
            context = {
                'heritage_items': heritage_analysis.get('heritage_items', []),
                'heritage_summary': heritage_analysis.get('summary', {}),
                'weather_summary': weather_data.get('summary', {}),
                'user_preferences': {
                    'travel_days': planning_request.get('travel_days', 3),
                    'departure_location': planning_request.get('departure_location', ''),
                    'travel_mode': planning_request.get('travel_mode', '自驾'),
                    'budget_range': planning_request.get('budget_range', '中等'),
                    'group_size': planning_request.get('group_size', 2),
                    'special_requirements': planning_request.get('special_requirements', [])
                }
            }
            
            # 从heritage_analysis中提取主要地区作为location
            heritage_items = heritage_analysis.get('heritage_items', [])
            main_location = "陕西"
            if heritage_items:
                # 尝试从第一个项目中获取地区信息
                first_item = heritage_items[0]
                region = first_item.get('region', '陕西')
                main_location = region if region else "陕西"
            
            # 根据当前时间推断季节
            current_month = datetime.now().month
            if current_month in [12, 1, 2]:
                season = "冬季"
            elif current_month in [3, 4, 5]:
                season = "春季"
            elif current_month in [6, 7, 8]:
                season = "夏季"
            else:
                season = "秋季"
            
            # 获取旅游天数
            duration = planning_request.get('travel_days', 3)
            
            # 调用AI模型生成建议
            ai_response = await self.ali_model.generate_travel_suggestions(
                main_location,
                season,
                duration
            )
            
            return ai_response
            
        except Exception as e:
            logger.error(f"生成AI建议时发生错误: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback_suggestions': self._generate_fallback_suggestions(heritage_analysis, weather_data)
            }
    
    def _generate_fallback_suggestions(self, 
                                     heritage_analysis: Dict[str, Any],
                                     weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成智能备用建议（当AI调用失败时）
        
        Args:
            heritage_analysis (Dict[str, Any]): 非遗项目分析
            weather_data (Dict[str, Any]): 天气数据
        
        Returns:
            Dict[str, Any]: 智能备用建议
        """
        heritage_items = heritage_analysis.get('heritage_items', [])
        heritage_summary = heritage_analysis.get('summary', {})
        
        # 基础旅行建议
        travel_tips = [
            '📅 建议提前1-2周预订住宿和热门景点门票，避免临时涨价',
            '👟 携带舒适的防滑步行鞋，部分非遗场所可能需要较多步行',
            '📸 准备相机或手机充电宝，记录珍贵的非遗文化瞬间',
            '📚 提前了解当地非遗文化背景，增强体验深度和意义'
        ]
        
        # 智能打包清单
        packing_list = [
            '📋 必备证件：身份证、学生证（如有优惠）、健康码',
            '🔌 电子设备：手机充电器、移动电源、相机存储卡',
            '💊 健康用品：常用药品、口罩、免洗洗手液',
            '🌂 天气用品：根据天气预报准备雨具或防晒用品'
        ]
        
        # 智能预算估算
        budget_estimate = self._calculate_intelligent_budget(heritage_items, weather_data)
        
        # 根据非遗项目类型添加专业建议
        specialized_tips = self._generate_specialized_tips(heritage_items)
        travel_tips.extend(specialized_tips)
        
        # 根据天气条件优化建议
        weather_tips = self._generate_weather_specific_tips(weather_data)
        travel_tips.extend(weather_tips)
        packing_list.extend(self._generate_weather_packing_list(weather_data))
        
        # 文化体验建议
        cultural_tips = self._generate_cultural_experience_tips(heritage_items)
        
        # 安全和礼仪提醒
        safety_tips = [
            '🛡️ 尊重当地文化传统，遵守参观规则和拍照限制',
            '🤝 与非遗传承人交流时保持礼貌，可适当给予小费表示尊重',
            '⚠️ 注意保护文物古迹，不触摸、不攀爬、不乱涂乱画',
            '📱 保存当地紧急联系方式，包括景区服务电话和医疗机构'
        ]
        
        return {
            'travel_tips': travel_tips[:8],  # 限制数量避免信息过载
            'packing_list': packing_list,
            'budget_estimate': budget_estimate,
            'cultural_experience': cultural_tips,
            'safety_reminders': safety_tips,
            'best_practices': self._generate_best_practices(heritage_items)
        }
    
    def _calculate_intelligent_budget(self, heritage_items: List[Dict[str, Any]], weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能计算预算估算
        
        Args:
            heritage_items: 非遗项目列表
            weather_data: 天气数据
        
        Returns:
            详细预算估算
        """
        num_items = len(heritage_items)
        
        # 基础费用估算
        base_budget = {
            'transportation': {
                'local_transport': f'{num_items * 20}-{num_items * 50}元',
                'description': '市内交通费用，包括公交、地铁、出租车等'
            },
            'accommodation': {
                'budget': '150-300元/晚',
                'mid_range': '300-600元/晚', 
                'luxury': '600-1200元/晚',
                'description': '根据住宿标准和位置选择'
            },
            'meals': {
                'daily_cost': '80-200元/天',
                'local_specialties': '50-150元/餐',
                'description': '包含当地特色美食体验'
            },
            'tickets': {
                'average_cost': f'{num_items * 30}-{num_items * 80}元',
                'description': '景点门票费用，部分非遗体验可能需要额外费用'
            },
            'shopping': {
                'souvenirs': '100-500元',
                'handicrafts': '200-1000元',
                'description': '非遗手工艺品和纪念品'
            },
            'experiences': {
                'workshops': '100-300元/次',
                'performances': '80-200元/场',
                'description': '非遗体验活动和表演观赏'
            }
        }
        
        # 根据天气调整预算
        if weather_data.get('success'):
            weather_summary = weather_data.get('summary', {})
            if weather_summary.get('suitability_rate', 100) < 70:
                base_budget['contingency'] = {
                    'weather_backup': '100-200元',
                    'description': '天气不佳时的室内活动备用费用'
                }
        
        return base_budget
    
    def _generate_specialized_tips(self, heritage_items: List[Dict[str, Any]]) -> List[str]:
        """
        根据非遗项目类型生成专业建议
        
        Args:
            heritage_items: 非遗项目列表
        
        Returns:
            专业建议列表
        """
        tips = []
        item_types = [item.get('type', '').lower() for item in heritage_items]
        
        if any('手工艺' in t or '工艺' in t for t in item_types):
            tips.append('🎨 参与手工艺体验时，建议穿着不怕弄脏的衣物，带上围裙')
        
        if any('表演' in t or '戏曲' in t or '音乐' in t for t in item_types):
            tips.append('🎭 观看表演时请提前到场，关闭手机或调至静音模式')
        
        if any('美食' in t or '小吃' in t for t in item_types):
            tips.append('🍜 品尝传统美食时，可询问制作工艺和文化背景，增加体验价值')
        
        if any('建筑' in t or '古迹' in t for t in item_types):
            tips.append('🏛️ 参观古建筑时注意脚下安全，部分区域可能有台阶或不平路面')
        
        return tips
    
    def _generate_weather_specific_tips(self, weather_data: Dict[str, Any]) -> List[str]:
        """
        生成天气相关建议
        
        Args:
            weather_data: 天气数据
        
        Returns:
            天气建议列表
        """
        tips = []
        
        if not weather_data.get('success'):
            return ['🌤️ 请关注实时天气预报，合理安排行程']
        
        weather_summary = weather_data.get('summary', {})
        suitability_rate = weather_summary.get('suitability_rate', 100)
        
        if suitability_rate < 50:
            tips.append('⚠️ 天气条件较差，建议优先安排室内非遗项目，准备雨具')
        elif suitability_rate < 70:
            tips.append('🌦️ 天气条件一般，建议灵活安排行程，准备应对天气变化')
        else:
            tips.append('☀️ 天气条件良好，适合户外非遗项目和文化体验')
        
        return tips
    
    def _generate_weather_packing_list(self, weather_data: Dict[str, Any]) -> List[str]:
        """
        生成天气相关打包清单
        
        Args:
            weather_data: 天气数据
        
        Returns:
            天气打包清单
        """
        items = []
        
        if not weather_data.get('success'):
            return ['🌈 根据天气预报准备相应衣物和用品']
        
        weather_summary = weather_data.get('summary', {})
        
        if weather_summary.get('rain_probability', 0) > 30:
            items.append('☔ 雨具：雨伞、雨衣，保护电子设备的防水袋')
        
        if weather_summary.get('max_temperature', 25) > 28:
            items.append('🌞 防暑用品：防晒霜、遮阳帽、充足的饮用水')
        
        if weather_summary.get('min_temperature', 15) < 10:
            items.append('🧥 保暖用品：外套、围巾、手套等保暖衣物')
        
        return items
    
    def _generate_cultural_experience_tips(self, heritage_items: List[Dict[str, Any]]) -> List[str]:
        """
        生成文化体验建议
        
        Args:
            heritage_items: 非遗项目列表
        
        Returns:
            文化体验建议
        """
        tips = [
            '📖 建议提前阅读相关非遗项目的历史背景和文化内涵',
            '🗣️ 主动与传承人交流，了解技艺传承的故事和心得',
            '📝 记录体验过程和感受，可以写旅行日记或分享社交媒体',
            '🎁 考虑购买正宗的非遗手工艺品作为纪念，支持传承人'
        ]
        
        # 根据项目数量调整建议
        if len(heritage_items) > 5:
            tips.append('⏰ 项目较多，建议合理分配时间，避免走马观花')
        
        return tips
    
    def _generate_best_practices(self, heritage_items: List[Dict[str, Any]]) -> List[str]:
        """
        生成最佳实践建议
        
        Args:
            heritage_items: 非遗项目列表
        
        Returns:
            最佳实践建议
        """
        practices = [
            '🕐 合理安排时间，每个项目预留充足的体验时间',
            '👥 如果是团体出行，提前协调好集合时间和地点',
            '📞 保存景区和传承人的联系方式，便于沟通协调',
            '💡 保持开放心态，积极参与互动体验活动',
            '🌟 尊重传统文化，以学习和传承的心态参与体验'
        ]
        
        return practices
    
    async def _optimize_travel_route(self, 
                                   heritage_analysis: Dict[str, Any],
                                   weather_data: Dict[str, Any],
                                   planning_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        优化旅行路线
        
        Args:
            heritage_analysis (Dict[str, Any]): 非遗项目分析
            weather_data (Dict[str, Any]): 天气数据
            planning_request (Dict[str, Any]): 规划请求
        
        Returns:
            Dict[str, Any]: 优化后的路线
        """
        try:
            heritage_items = heritage_analysis.get('heritage_items', [])
            travel_days = planning_request.get('travel_days', 3)
            
            if not heritage_items:
                return {'success': False, 'error': '没有有效的非遗项目'}
            
            # 基于地理位置和天气优化路线
            geo_analysis = heritage_analysis.get('analysis', {}).get('geography', {})
            route_suggestions = heritage_analysis.get('analysis', {}).get('route_suggestions', [])
            
            if not route_suggestions:
                return {'success': False, 'error': '无法生成路线建议'}
            
            # 获取基础路线
            base_route = route_suggestions[0]
            optimized_sequence = base_route.get('sequence', [])
            
            # 根据天数分组
            daily_itinerary = self._group_items_by_days(optimized_sequence, travel_days)
            
            # 考虑天气因素调整
            if weather_data.get('success'):
                daily_itinerary = self._adjust_for_weather(daily_itinerary, weather_data)
            
            return {
                'success': True,
                'daily_itinerary': daily_itinerary,
                'total_distance': base_route.get('total_distance', 0),
                'estimated_travel_time': self._calculate_travel_time(daily_itinerary),
                'optimization_notes': [
                    '路线已根据地理位置优化',
                    '考虑了天气因素',
                    '平衡了每日行程安排'
                ]
            }
            
        except Exception as e:
            logger.error(f"优化旅行路线时发生错误: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _group_items_by_days(self, 
                           items: List[Dict[str, Any]], 
                           days: int) -> List[Dict[str, Any]]:
        """
        智能按天数分组项目，考虑地理位置、游览时间和体验质量
        
        Args:
            items (List[Dict[str, Any]]): 项目列表
            days (int): 天数
        
        Returns:
            List[Dict[str, Any]]: 按天分组的行程
        """
        if not items or days <= 0:
            return []
        
        # 智能分组算法：均匀分配项目到指定天数
        daily_itinerary = []
        remaining_items = items.copy()
        
        # 计算每天应该分配的项目数量（均匀分配）
        items_per_day = len(items) // days
        extra_items = len(items) % days
        
        for day in range(days):
            day_items = []
            daily_duration = 0
            max_daily_hours = 8  # 每天最多8小时游览时间
            
            # 计算当天目标项目数量
            target_items_today = items_per_day + (1 if day < extra_items else 0)
            
            # 智能选择当天项目，优先考虑均匀分配
            items_selected = 0
            while remaining_items and items_selected < target_items_today and daily_duration < max_daily_hours:
                # 优先选择地理位置相近的项目
                best_item = self._select_best_next_item(day_items, remaining_items, daily_duration, max_daily_hours)
                if best_item:
                    day_items.append(best_item)
                    remaining_items.remove(best_item)
                    daily_duration += self._calculate_item_duration(best_item)
                    items_selected += 1
                else:
                    break
            
            # 如果是最后一天且还有剩余项目，全部分配给最后一天
            if day == days - 1 and remaining_items:
                for item in remaining_items:
                    if daily_duration + self._calculate_item_duration(item) <= max_daily_hours * 1.2:  # 允许最后一天稍微超时
                        day_items.append(item)
                        daily_duration += self._calculate_item_duration(item)
                remaining_items = []
            
            # 确保每一天都有记录，即使没有项目也要创建空天数
            if day_items:
                # 优化当天路线顺序
                optimized_items = self._optimize_daily_route(day_items)
                
                # 计算精确的时间预估
                time_estimation = self._calculate_precise_timing(optimized_items)
                
                daily_itinerary.append({
                    'day': day + 1,
                    'date': (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d'),
                    'items': optimized_items,
                    'estimated_duration': time_estimation['visit_time'],
                    'travel_time': time_estimation['travel_time'],
                    'total_time': time_estimation['total_time'],
                    'difficulty_level': self._assess_daily_difficulty(optimized_items),
                    'highlights': self._extract_daily_highlights(optimized_items),
                    'recommendations': [],
                    'schedule': time_estimation['detailed_schedule']
                })
            else:
                # 创建空天数记录，确保天数匹配
                daily_itinerary.append({
                    'day': day + 1,
                    'date': (datetime.now() + timedelta(days=day)).strftime('%Y-%m-%d'),
                    'items': [],
                    'estimated_duration': 0,
                    'travel_time': 0,
                    'total_time': 0,
                    'difficulty_level': '轻松',
                    'highlights': ['自由活动时间'],
                    'recommendations': ['可以休息或自由探索当地'],
                    'schedule': []
                })
        
        return daily_itinerary
    
    def _select_best_next_item(self, current_items: List[Dict[str, Any]], 
                              remaining_items: List[Dict[str, Any]], 
                              current_duration: float, 
                              max_duration: float) -> Optional[Dict[str, Any]]:
        """
        智能选择下一个最佳项目
        
        Args:
            current_items: 当天已选项目
            remaining_items: 剩余项目
            current_duration: 当前累计时间
            max_duration: 最大允许时间
        
        Returns:
            最佳下一个项目或None
        """
        if not remaining_items:
            return None
        
        best_item = None
        best_score = -1
        
        for item in remaining_items:
            item_duration = self._calculate_item_duration(item)
            
            # 检查时间是否允许
            if current_duration + item_duration > max_duration:
                continue
            
            # 计算综合评分
            score = self._calculate_item_score(item, current_items)
            
            if score > best_score:
                best_score = score
                best_item = item
        
        return best_item
    
    def _calculate_item_duration(self, item: Dict[str, Any]) -> float:
        """
        计算项目游览时间（包含交通时间）
        
        Args:
            item: 项目信息
        
        Returns:
            预估时间（小时）
        """
        base_duration = item.get('visit_duration', 2.0)
        
        # 根据项目类型调整时间
        item_type = item.get('type', '').lower()
        if '博物馆' in item_type or '展览' in item_type:
            base_duration *= 1.2  # 博物馆需要更多时间
        elif '表演' in item_type or '演出' in item_type:
            base_duration *= 1.5  # 表演有固定时长
        elif '手工艺' in item_type or '体验' in item_type:
            base_duration *= 1.3  # 体验活动需要更多时间
        
        # 添加交通时间（平均30分钟）
        travel_time = 0.5
        
        return base_duration + travel_time
    
    def _calculate_item_score(self, item: Dict[str, Any], current_items: List[Dict[str, Any]]) -> float:
        """
        计算项目综合评分
        
        Args:
            item: 待评估项目
            current_items: 当天已选项目
        
        Returns:
            综合评分
        """
        score = 0.0
        
        # 基础评分：项目重要性
        importance = item.get('importance_score', 5.0)
        score += importance * 2
        
        # 地理位置评分：与已选项目的距离
        if current_items:
            avg_distance = self._calculate_average_distance(item, current_items)
            # 距离越近评分越高
            distance_score = max(0, 10 - avg_distance)
            score += distance_score
        
        # 类型多样性评分
        item_type = item.get('type', '')
        current_types = [i.get('type', '') for i in current_items]
        if item_type not in current_types:
            score += 3  # 鼓励类型多样性
        
        # 难度平衡评分
        difficulty = item.get('difficulty_level', 3)
        current_avg_difficulty = sum(i.get('difficulty_level', 3) for i in current_items) / max(len(current_items), 1)
        if abs(difficulty - current_avg_difficulty) < 2:
            score += 2  # 鼓励难度平衡
        
        return score
    
    def _calculate_average_distance(self, item: Dict[str, Any], items: List[Dict[str, Any]]) -> float:
        """
        计算项目与其他项目的平均距离
        
        Args:
            item: 目标项目
            items: 参考项目列表
        
        Returns:
            平均距离（公里）
        """
        if not items:
            return 0.0
        
        total_distance = 0.0
        count = 0
        
        item_location = item.get('location', {})
        item_lat = item_location.get('latitude', 0)
        item_lng = item_location.get('longitude', 0)
        
        for other_item in items:
            other_location = other_item.get('location', {})
            other_lat = other_location.get('latitude', 0)
            other_lng = other_location.get('longitude', 0)
            
            if item_lat and item_lng and other_lat and other_lng:
                # 简化的距离计算（实际应用中可使用更精确的地理计算）
                distance = ((item_lat - other_lat) ** 2 + (item_lng - other_lng) ** 2) ** 0.5 * 111  # 转换为公里
                total_distance += distance
                count += 1
        
        return total_distance / count if count > 0 else 0.0
    
    def _optimize_daily_route(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        优化当天路线顺序
        
        Args:
            items: 当天项目列表
        
        Returns:
            优化后的项目列表
        """
        if len(items) <= 1:
            return items
        
        # 简化的TSP算法：最近邻居法
        optimized = []
        remaining = items.copy()
        
        # 选择起始点（可以是地理中心或第一个项目）
        current = remaining.pop(0)
        optimized.append(current)
        
        while remaining:
            nearest = min(remaining, key=lambda x: self._calculate_average_distance(current, [x]))
            optimized.append(nearest)
            remaining.remove(nearest)
            current = nearest
        
        return optimized
    
    def _calculate_precise_timing(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算精确的时间安排
        
        Args:
            items: 项目列表
        
        Returns:
            详细时间安排
        """
        total_visit_time = 0.0
        total_travel_time = 0.0
        detailed_schedule = []
        
        current_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)  # 从上午9点开始
        
        for i, item in enumerate(items):
            # 计算到达时间（包含交通时间）
            if i > 0:
                travel_duration = 0.5  # 平均30分钟交通时间
                current_time += timedelta(hours=travel_duration)
                total_travel_time += travel_duration
            
            # 游览时间
            visit_duration = self._calculate_item_duration(item) - 0.5  # 减去交通时间
            total_visit_time += visit_duration
            
            # 添加到详细时间表
            detailed_schedule.append({
                'item_name': item.get('name', '未知项目'),
                'start_time': current_time.strftime('%H:%M'),
                'end_time': (current_time + timedelta(hours=visit_duration)).strftime('%H:%M'),
                'duration': f"{visit_duration:.1f}小时",
                'type': item.get('type', ''),
                'category': item.get('category', '未分类'),
                'priority': item.get('importance_score', 5)
            })
            
            current_time += timedelta(hours=visit_duration)
        
        return {
            'visit_time': total_visit_time,
            'travel_time': total_travel_time,
            'total_time': total_visit_time + total_travel_time,
            'detailed_schedule': detailed_schedule,
            'end_time': current_time.strftime('%H:%M')
        }
    
    def _assess_daily_difficulty(self, items: List[Dict[str, Any]]) -> str:
        """
        评估当天行程难度
        
        Args:
            items: 项目列表
        
        Returns:
            难度等级
        """
        if not items:
            return '轻松'
        
        avg_difficulty = sum(item.get('difficulty_level', 3) for item in items) / len(items)
        total_time = sum(self._calculate_item_duration(item) for item in items)
        
        if avg_difficulty >= 4 or total_time >= 8:
            return '较高'
        elif avg_difficulty >= 3 or total_time >= 6:
            return '中等'
        else:
            return '轻松'
    
    def _extract_daily_highlights(self, items: List[Dict[str, Any]]) -> List[str]:
        """
        提取当天亮点
        
        Args:
            items: 项目列表
        
        Returns:
            亮点列表
        """
        highlights = []
        
        for item in items:
            # 提取高评分项目作为亮点
            if item.get('importance_score', 0) >= 8:
                highlights.append(f"★ {item.get('name', '未知项目')} - {item.get('description', '精彩体验')[:30]}...")
            
            # 提取特殊类型项目
            item_type = item.get('type', '').lower()
            if '国家级' in item_type or '世界' in item_type:
                highlights.append(f"🏆 {item.get('name', '未知项目')} - 国家级非遗项目")
        
        return highlights[:3]  # 最多3个亮点
    
    def _adjust_for_weather(self, 
                          daily_itinerary: List[Dict[str, Any]], 
                          weather_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        根据天气调整行程
        
        Args:
            daily_itinerary (List[Dict[str, Any]]): 每日行程
            weather_data (Dict[str, Any]): 天气数据
        
        Returns:
            List[Dict[str, Any]]: 调整后的行程
        """
        locations_weather = weather_data.get('locations', {})
        
        for day_plan in daily_itinerary:
            day_recommendations = []
            
            # 检查当天天气
            day_index = day_plan['day'] - 1
            
            for location_name, location_weather in locations_weather.items():
                if location_weather.get('success') and 'forecast' in location_weather:
                    forecast = location_weather['forecast']
                    if day_index < len(forecast):
                        day_weather = forecast[day_index]
                        suitability = day_weather.get('travel_suitability', {})
                        
                        if suitability.get('score', 100) < 60:
                            day_recommendations.extend(suitability.get('warnings', []))
                            day_recommendations.extend(suitability.get('recommendations', []))
                        
                        # 添加天气信息到当天计划
                        day_plan['weather'] = {
                            'condition': day_weather.get('weather_description'),
                            'temperature': f"{day_weather.get('min_temp')}-{day_weather.get('max_temp')}°C",
                            'precipitation': day_weather.get('precipitation', 0),
                            'suitability': suitability.get('level', '适宜')
                        }
                        break
            
            day_plan['recommendations'].extend(list(set(day_recommendations)))
        
        return daily_itinerary
    
    def _calculate_travel_time(self, daily_itinerary: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算精确的总旅行时间统计
        
        Args:
            daily_itinerary (List[Dict[str, Any]]): 每日行程
        
        Returns:
            Dict[str, Any]: 详细时间统计
        """
        if not daily_itinerary:
            return {
                'total_visit_hours': 0,
                'total_travel_hours': 0,
                'total_hours': 0,
                'average_hours_per_day': 0,
                'daily_breakdown': [],
                'efficiency_score': 0,
                'recommendations': []
            }
        
        total_visit_time = 0.0
        total_travel_time = 0.0
        daily_breakdown = []
        efficiency_scores = []
        
        for day_plan in daily_itinerary:
            day_visit_time = day_plan.get('estimated_duration', 0)
            day_travel_time = day_plan.get('travel_time', 0)
            day_total_time = day_plan.get('total_time', day_visit_time + day_travel_time)
            
            total_visit_time += day_visit_time
            total_travel_time += day_travel_time
            
            # 计算当天效率分数（游览时间占比）
            day_efficiency = (day_visit_time / day_total_time * 100) if day_total_time > 0 else 0
            efficiency_scores.append(day_efficiency)
            
            # 当天时间分解
            daily_breakdown.append({
                'day': day_plan.get('day', 0),
                'visit_hours': round(day_visit_time, 1),
                'travel_hours': round(day_travel_time, 1),
                'total_hours': round(day_total_time, 1),
                'efficiency': round(day_efficiency, 1),
                'difficulty': day_plan.get('difficulty_level', '中等'),
                'items_count': len(day_plan.get('items', [])),
                'start_time': day_plan.get('schedule', [{}])[0].get('start_time', '09:00') if day_plan.get('schedule') else '09:00',
                'end_time': day_plan.get('schedule', [{}])[-1].get('end_time', '17:00') if day_plan.get('schedule') else '17:00'
            })
        
        # 计算总体效率分数
        overall_efficiency = sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0
        
        # 生成时间优化建议
        recommendations = self._generate_time_recommendations(daily_breakdown, overall_efficiency)
        
        return {
            'total_visit_hours': round(total_visit_time, 1),
            'total_travel_hours': round(total_travel_time, 1),
            'total_hours': round(total_visit_time + total_travel_time, 1),
            'average_hours_per_day': round((total_visit_time + total_travel_time) / len(daily_itinerary), 1),
            'daily_breakdown': daily_breakdown,
            'efficiency_score': round(overall_efficiency, 1),
            'recommendations': recommendations,
            'summary': {
                'most_intensive_day': max(daily_breakdown, key=lambda x: x['total_hours'])['day'] if daily_breakdown else 0,
                'most_efficient_day': max(daily_breakdown, key=lambda x: x['efficiency'])['day'] if daily_breakdown else 0,
                'total_items': sum(day['items_count'] for day in daily_breakdown),
                'average_items_per_day': round(sum(day['items_count'] for day in daily_breakdown) / len(daily_breakdown), 1) if daily_breakdown else 0
            }
        }
    
    def _generate_time_recommendations(self, daily_breakdown: List[Dict[str, Any]], overall_efficiency: float) -> List[str]:
        """
        生成时间优化建议
        
        Args:
            daily_breakdown: 每日时间分解
            overall_efficiency: 总体效率分数
        
        Returns:
            时间优化建议列表
        """
        recommendations = []
        
        # 效率分析建议
        if overall_efficiency < 60:
            recommendations.append('⚠️ 行程中交通时间占比较高，建议优化路线或选择相近景点')
        elif overall_efficiency > 85:
            recommendations.append('✅ 行程安排高效，游览时间充足，体验质量较好')
        
        # 强度分析建议
        high_intensity_days = [day for day in daily_breakdown if day['total_hours'] > 8]
        if high_intensity_days:
            recommendations.append(f'🕐 第{"、".join(str(day["day"]) for day in high_intensity_days)}天行程较紧张，建议适当调整或准备充足体力')
        
        # 平衡性建议
        max_hours = max(day['total_hours'] for day in daily_breakdown) if daily_breakdown else 0
        min_hours = min(day['total_hours'] for day in daily_breakdown) if daily_breakdown else 0
        if max_hours - min_hours > 3:
            recommendations.append('⚖️ 各天行程时间差异较大，建议重新平衡分配')
        
        # 项目数量建议
        max_items = max(day['items_count'] for day in daily_breakdown) if daily_breakdown else 0
        if max_items > 4:
            recommendations.append('📍 部分天数景点较多，建议预留充足时间，避免走马观花')
        
        # 时间段建议
        late_end_days = [day for day in daily_breakdown if day['end_time'] > '18:00']
        if late_end_days:
            recommendations.append('🌅 部分天数结束时间较晚，建议合理安排晚餐和休息时间')
        
        return recommendations[:5]  # 限制建议数量
    
    async def _generate_complete_plan(self, 
                                    heritage_analysis: Dict[str, Any],
                                    weather_data: Dict[str, Any],
                                    ai_suggestions: Dict[str, Any],
                                    optimized_route: Dict[str, Any],
                                    planning_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成完整的旅游规划
        
        Args:
            heritage_analysis (Dict[str, Any]): 非遗项目分析
            weather_data (Dict[str, Any]): 天气数据
            ai_suggestions (Dict[str, Any]): AI建议
            optimized_route (Dict[str, Any]): 优化路线
            planning_request (Dict[str, Any]): 规划请求
        
        Returns:
            Dict[str, Any]: 完整旅游规划
        """
        plan_id = planning_request.get('plan_id', f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        complete_plan = {
            'success': True,
            'plan_id': plan_id,
            'created_at': datetime.now().isoformat(),
            'user_id': planning_request.get('user_id'),
            
            # 基本信息
            'basic_info': {
                'title': self._generate_attractive_title(heritage_analysis, planning_request),
                'duration': f"{planning_request.get('travel_days', 3)}天",
                'departure': planning_request.get('departure_location', ''),
                'travel_mode': planning_request.get('travel_mode', '自驾'),
                'group_size': planning_request.get('group_size', 2),
                'budget_range': planning_request.get('budget_range', '中等')
            },
            
            # 项目概览
            'heritage_overview': {
                'total_items': len(heritage_analysis.get('heritage_items', [])),
                'heritage_items': heritage_analysis.get('heritage_items', []),
                'categories': heritage_analysis.get('analysis', {}).get('categories', {}),
                'regions': heritage_analysis.get('analysis', {}).get('geography', {}).get('regions', []),
                'estimated_days': heritage_analysis.get('summary', {}).get('estimated_days', 1)
            },
            
            # 详细行程
            'itinerary': optimized_route.get('daily_itinerary', []),
            
            # 天气信息
            'weather_info': {
                'summary': weather_data.get('summary', {}),
                'overall_suitability': weather_data.get('summary', {}).get('overall_recommendation', '适宜出行')
            },
            
            # AI建议
            'recommendations': {
                'ai_suggestions': ai_suggestions.get('suggestions', ai_suggestions.get('fallback_suggestions', {})),
                'travel_tips': ai_suggestions.get('travel_tips', []),
                'packing_list': ai_suggestions.get('packing_list', []),
                'budget_estimate': ai_suggestions.get('budget_estimate', {})
            },
            
            # 路线信息
            'route_info': {
                'total_distance': optimized_route.get('total_distance', 0),
                'estimated_travel_time': optimized_route.get('estimated_travel_time', {}),
                'optimization_notes': optimized_route.get('optimization_notes', [])
            },
            
            # 导出信息
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
        
        Args:
            plan_id (str): 规划ID
            error_type (str): 错误类型
            error_message (str): 错误消息
        
        Returns:
            Dict[str, Any]: 错误结果
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
        
        Args:
            plan_id (str): 规划ID
        
        Returns:
            Dict[str, Any]: 进度信息
        """
        return self.planning_progress.get(plan_id, {
            'status': 'not_found',
            'error': '规划不存在'
        })
    
    def get_planning_result(self, plan_id: str) -> Dict[str, Any]:
        """
        获取规划结果
        
        Args:
            plan_id (str): 规划ID
        
        Returns:
            Dict[str, Any]: 规划结果，如果不存在返回None
        """
        progress_data = self.planning_progress.get(plan_id, {})
        if progress_data.get('status') == 'completed':
            return progress_data.get('result')
        return None
    
    def _generate_attractive_title(self, heritage_analysis: Dict[str, Any], planning_request: Dict[str, Any]) -> str:
        """
        生成吸引人的旅游规划标题
        
        Args:
            heritage_analysis (Dict[str, Any]): 非遗项目分析
            planning_request (Dict[str, Any]): 规划请求
        
        Returns:
            str: 吸引人的标题
        """
        heritage_items = heritage_analysis.get('heritage_items', [])
        
        if not heritage_items:
            return f"非遗文化之旅 - {planning_request.get('travel_days', 3)}天"
        
        # 提取主要非遗类别
        categories = [item.get('category', '') for item in heritage_items]
        main_category = max(set(categories), key=categories.count) if categories else "非遗文化"
        
        # 提取地区信息
        regions = [item.get('region', '') for item in heritage_items]
        unique_regions = list(set(regions))
        region_text = "-".join(unique_regions[:2]) if len(unique_regions) > 1 else unique_regions[0] if unique_regions else "陕西"
        
        # 生成吸引人的标题前缀
        title_prefixes = [
            "探寻", "漫步", "邂逅", "品味", "体验", "感受", "沉浸", "发现"
        ]
        
        # 根据主要类别选择合适的前缀
        category_prefixes = {
            "传统音乐": "聆听",
            "传统舞蹈": "舞动",
            "传统戏剧": "观赏",
            "传统技艺": "体验",
            "传统美术": "欣赏",
            "民俗": "感受",
            "传统体育": "参与"
        }
        
        prefix = category_prefixes.get(main_category, title_prefixes[len(heritage_items) % len(title_prefixes)])
        
        # 生成标题
        title = f"{prefix}{region_text}{main_category}之旅"
        
        # 添加天数信息
        days = planning_request.get('travel_days', 3)
        title += f" - {days}天非遗文化体验"
        
        return title
    
    def cleanup_old_progress(self, hours: int = 24):
        """
        清理旧的进度记录
        
        Args:
            hours (int): 保留小时数，默认24小时
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
    
    Returns:
        TravelPlanner: 旅游规划器实例
    """
    global _travel_planner_instance
    if _travel_planner_instance is None:
        _travel_planner_instance = TravelPlanner()
    return _travel_planner_instance