# -*- coding: utf-8 -*-
"""
规划查询工具
用于Agent查询用户已有的规划信息，不触发新的规划创建
"""

from typing import Dict, Any, List
from loguru import logger
from Agent.tools.base import BaseTool


class PlanQueryTool(BaseTool):
    """
    规划查询工具 - 查询用户已有的旅游规划信息
    
    设计原则：
    - 只读取已有数据，不创建新规划
    - 用于用户询问"我的路线"、"行程安排"等问题
    - 规划创建由前端直接调用 /api/travel-plan/create 接口
    """

    @property
    def name(self) -> str:
        return "plan_query"

    @property
    def description(self) -> str:
        return """查询用户当前的旅游规划信息。
当用户询问"我的路线有哪些"、"行程安排是什么"、"去哪几个地方"时使用此工具。
返回结果包含：已选非遗项目、行程天数、出发地、每日安排概览等信息。
注意：此工具只读取已有规划，不会创建新规划。"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query_type": {
                    "type": "string",
                    "description": "查询类型：overview(概览)、itinerary(详细行程)、heritages(非遗项目列表)",
                    "enum": ["overview", "itinerary", "heritages"]
                }
            },
            "required": []
        }

    async def execute(self, query_type: str = "overview", **kwargs) -> Dict[str, Any]:
        """
        执行规划查询
        
        Args:
            query_type: 查询类型
            **kwargs: 可能包含 _context 上下文信息
        """
        try:
            context = kwargs.get('_context', {})
            
            if isinstance(context, dict):
                plan_summary = context.get('plan_summary', {})
                heritage_items = context.get('heritage_items', [])
            else:
                plan_summary = getattr(context, 'plan_summary', {}) if hasattr(context, 'plan_summary') else {}
                heritage_items = getattr(context, 'heritage_items', []) if hasattr(context, 'heritage_items') else []
            
            logger.debug(f"📋 PlanQueryTool 上下文: heritage_items={len(heritage_items)}")
            
            if not plan_summary and not heritage_items:
                return {
                    'success': False,
                    'error': '当前没有可用的规划信息。请先在页面上选择非遗项目并点击"进行规划"按钮创建规划。',
                    'hint': '用户尚未创建规划，引导用户使用页面功能'
                }
            
            if not plan_summary:
                plan_summary = {'heritage_items': heritage_items}
            
            if query_type == "overview":
                return self._query_overview(plan_summary)
            elif query_type == "itinerary":
                return self._query_itinerary(plan_summary)
            elif query_type == "heritages":
                return self._query_heritages(plan_summary)
            else:
                return self._query_overview(plan_summary)
                
        except Exception as e:
            logger.error(f"规划查询失败: {str(e)}")
            return {'success': False, 'error': f"查询失败: {str(e)}"}
    
    def _query_overview(self, plan_summary: Dict[str, Any]) -> Dict[str, Any]:
        """查询规划概览"""
        heritage_items = plan_summary.get('heritage_items', [])
        
        return {
            'success': True,
            'query_type': 'overview',
            'plan_info': {
                'departure': plan_summary.get('departure_location', '未设置'),
                'travel_days': plan_summary.get('travel_days', 0),
                'travel_mode': plan_summary.get('travel_mode', '自驾'),
                'heritage_count': len(heritage_items),
                'heritage_names': [h.get('name', '') for h in heritage_items],
                'regions': list(set([h.get('region', '') for h in heritage_items if h.get('region')]))
            },
            'message': f"您已规划从{plan_summary.get('departure_location', '未设置')}出发的{plan_summary.get('travel_days', 0)}天行程，包含{len(heritage_items)}个非遗项目。"
        }
    
    def _query_itinerary(self, plan_summary: Dict[str, Any]) -> Dict[str, Any]:
        """查询详细行程"""
        itinerary = plan_summary.get('itinerary', [])
        heritage_items = plan_summary.get('heritage_items', [])
        
        if not itinerary:
            return {
                'success': True,
                'query_type': 'itinerary',
                'itinerary': [],
                'message': '详细行程尚未生成，请点击"进行规划"按钮生成完整行程。'
            }
        
        daily_summary = []
        for day_plan in itinerary:
            day_num = day_plan.get('day', 0)
            items = day_plan.get('items', [])
            daily_summary.append({
                'day': day_num,
                'date': day_plan.get('date', ''),
                'theme': day_plan.get('theme', ''),
                'places': [i.get('name', '') for i in items],
                'pace': day_plan.get('pace_label', '')
            })
        
        return {
            'success': True,
            'query_type': 'itinerary',
            'daily_summary': daily_summary,
            'total_days': len(itinerary),
            'message': f"您的{len(itinerary)}天行程已安排完毕。"
        }
    
    def _query_heritages(self, plan_summary: Dict[str, Any]) -> Dict[str, Any]:
        """查询非遗项目列表"""
        heritage_items = plan_summary.get('heritage_items', [])
        
        heritage_list = []
        for h in heritage_items:
            heritage_list.append({
                'id': h.get('id'),
                'name': h.get('name', ''),
                'category': h.get('category', ''),
                'region': h.get('region', ''),
                'level': h.get('level', '')
            })
        
        return {
            'success': True,
            'query_type': 'heritages',
            'heritage_items': heritage_list,
            'count': len(heritage_list),
            'message': f"您已选择{len(heritage_list)}个非遗项目作为目的地。"
        }


class RouteDistanceTool(BaseTool):
    """
    路线距离查询工具 - 计算地点之间的距离
    
    设计原则：
    - 只计算距离，不创建规划
    - 用于用户询问"距离多远"、"开车多久"等问题
    """

    @property
    def name(self) -> str:
        return "route_distance"

    @property
    def description(self) -> str:
        return """查询地点之间的距离和行程时间。
当用户询问"从A到B多远"、"开车要多久"、"距离多少公里"时使用此工具。
返回结果包含：距离（公里）、预计时间、出行方式建议。
注意：此工具只计算距离，不会创建旅游规划。"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "origin": {
                    "type": "string",
                    "description": "出发地名称，如'西安'、'兴平市'"
                },
                "destination": {
                    "type": "string",
                    "description": "目的地名称，如'韩城'、'华阴'"
                },
                "travel_mode": {
                    "type": "string",
                    "description": "出行方式：driving(驾车)、walking(步行)、riding(骑行)、transit(公交)",
                    "enum": ["driving", "walking", "riding", "transit"],
                    "default": "driving"
                }
            },
            "required": ["origin", "destination"]
        }

    async def execute(self, origin: str, destination: str, 
                      travel_mode: str = "driving", **kwargs) -> Dict[str, Any]:
        """
        执行距离查询
        """
        try:
            from Agent.services.mcp_client import get_mcp_client
            from Agent.services.geocoding import get_geocoding_service
            
            geocoding = get_geocoding_service()
            mcp_client = get_mcp_client()
            
            origin_coords = await geocoding.get_coordinates(origin)
            dest_coords = await geocoding.get_coordinates(destination)
            
            if not origin_coords:
                return {
                    'success': False,
                    'error': f"无法获取出发地'{origin}'的坐标"
                }
            
            if not dest_coords:
                return {
                    'success': False,
                    'error': f"无法获取目的地'{destination}'的坐标"
                }
            
            origin_str = f"{origin_coords[0]},{origin_coords[1]}"
            dest_str = f"{dest_coords[0]},{dest_coords[1]}"
            
            result = await mcp_client.map_directions(
                origin=origin_str,
                destination=dest_str,
                mode=travel_mode
            )
            
            if result.get('success'):
                route = result.get('route', {})
                distance = route.get('distance', 0)
                duration = route.get('duration', 0)
                
                distance_km = round(distance / 1000, 1)
                duration_hours = round(duration / 3600, 1)
                duration_minutes = round(duration / 60)
                
                mode_names = {
                    'driving': '驾车',
                    'walking': '步行',
                    'riding': '骑行',
                    'transit': '公交'
                }
                
                return {
                    'success': True,
                    'origin': origin,
                    'destination': destination,
                    'travel_mode': mode_names.get(travel_mode, travel_mode),
                    'distance_km': distance_km,
                    'duration_hours': duration_hours,
                    'duration_minutes': duration_minutes,
                    'duration_text': self._format_duration(duration),
                    'message': f"从{origin}到{destination}，{mode_names.get(travel_mode, travel_mode)}距离约{distance_km}公里，预计{self._format_duration(duration)}。"
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', '路线查询失败')
                }
                
        except Exception as e:
            logger.error(f"距离查询失败: {str(e)}")
            return {'success': False, 'error': f"查询失败: {str(e)}"}
    
    def _format_duration(self, seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            return f"{round(seconds / 60)}分钟"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            if minutes > 0:
                return f"{hours}小时{minutes}分钟"
            return f"{hours}小时"


class RoutePreviewTool(BaseTool):
    """
    路线预览工具 - 预览非遗项目之间的路线安排
    
    设计原则：
    - 基于已选非遗项目，计算多种可选路线方案
    - 不创建完整规划，只返回路线概览
    - 用于用户询问"路线怎么走"、"先去哪个"、"有几条路线"等问题
    """

    @property
    def name(self) -> str:
        return "route_preview"

    @property
    def description(self) -> str:
        return """预览非遗项目之间的多种可选路线方案。
当用户询问"路线怎么安排"、"先去哪个地方"、"怎么走最顺路"、"有几条路线"时使用此工具。
返回结果包含：多条可选路线方案（按总距离排序）、每条方案的详细行程、总距离、预计时间。
注意：此工具只预览路线，不会创建完整规划。如需详细规划请点击页面上的"进行规划"按钮。"""

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "heritage_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "非遗项目ID数组（可选，不传则使用用户已选项目）"
                },
                "departure_location": {
                    "type": "string",
                    "description": "出发地（可选，不传则使用用户设置的出发地）"
                },
                "max_routes": {
                    "type": "integer",
                    "description": "返回的最大路线数量，默认3条",
                    "default": 3
                }
            },
            "required": []
        }

    async def execute(self, heritage_ids: List[int] = None, 
                      departure_location: str = None,
                      max_routes: int = 3, **kwargs) -> Dict[str, Any]:
        """
        执行路线预览 - 返回多种可选路线方案
        """
        try:
            context = kwargs.get('_context', None)
            
            if context and hasattr(context, 'get'):
                plan_summary = context.get('plan_summary', {})
                heritage_items = context.get('heritage_items', [])
                context_heritage_ids = context.get('heritage_ids', [])
            elif hasattr(context, 'plan_summary'):
                plan_summary = context.plan_summary if hasattr(context.plan_summary, 'get') else {}
                heritage_items = context.heritage_items if hasattr(context, 'heritage_items') else []
                context_heritage_ids = context.heritage_ids if hasattr(context, 'heritage_ids') else []
            else:
                plan_summary = {}
                heritage_items = []
                context_heritage_ids = []
            
            logger.debug("📋 RoutePreviewTool 上下文:")
            logger.debug(f"  - heritage_items: {len(heritage_items)}")
            logger.debug(f"  - heritage_ids from context: {context_heritage_ids}")
            logger.debug(f"  - departure_location: {departure_location}")
            
            if heritage_ids is None:
                if context_heritage_ids:
                    heritage_ids = context_heritage_ids
                else:
                    heritage_ids = [h.get('id') for h in heritage_items if h.get('id')]
            
            if heritage_ids:
                converted_ids = []
                for hid in heritage_ids:
                    if isinstance(hid, str):
                        if hid.isdigit():
                            converted_ids.append(int(hid))
                        else:
                            logger.warning(f"heritage_id 是非数字字符串: {hid}，跳过")
                    elif isinstance(hid, int):
                        converted_ids.append(hid)
                    else:
                        try:
                            converted_ids.append(int(hid))
                        except (ValueError, TypeError):
                            logger.warning(f"无法转换 heritage_id: {hid}，跳过")
                heritage_ids = converted_ids
                logger.info(f"转换后的 heritage_ids: {heritage_ids}")
            
            if departure_location is None:
                departure_location = plan_summary.get('departure_location', '') if plan_summary else ''
                if not departure_location:
                    departure_location = context.get('departure_location', '西安') if context else '西安'
            
            logger.info("📋 RoutePreviewTool 最终参数:")
            logger.info(f"  - heritage_ids: {heritage_ids}")
            logger.info(f"  - departure_location: {departure_location}")
            
            if not heritage_ids:
                return {
                    'success': False,
                    'error': '没有可用的非遗项目。请先在页面上选择要游览的非遗项目。'
                }
            
            if len(heritage_ids) > 6:
                return {
                    'success': False,
                    'error': f'非遗项目数量过多（{len(heritage_ids)}个），建议不超过6个以获得更好的路线规划体验。'
                }
            
            from Agent.memory.heritage_query_service import get_heritage_query_service
            from Agent.services.mcp_client import get_mcp_client
            from Agent.services.geocoding import get_geocoding_service
            from itertools import permutations
            
            query_service = get_heritage_query_service()
            mcp_client = get_mcp_client()
            geocoding = get_geocoding_service()
            
            heritages = []
            for hid in heritage_ids:
                h = query_service.query_by_id(hid)
                if h:
                    heritages.append(h)
            
            if not heritages:
                return {
                    'success': False,
                    'error': '未找到指定的非遗项目信息'
                }
            
            start_coords = await geocoding.get_coordinates(departure_location)
            if not start_coords:
                start_coords = (34.3416, 108.9398)
            
            locations = [{'name': departure_location, 'coords': start_coords, 'is_start': True}]
            for h in heritages:
                lat = h.get('latitude')
                lng = h.get('longitude')
                if lat and lng:
                    locations.append({
                        'name': h.get('name', ''),
                        'coords': (lat, lng),
                        'region': h.get('region', ''),
                        'is_start': False,
                        'heritage_id': h.get('id')
                    })
            
            if len(locations) < 3:
                return {
                    'success': False,
                    'error': '非遗项目缺少位置信息'
                }
            
            start_loc = locations[0]
            dest_locs = locations[1:]
            
            all_location_strs = [f"{loc['coords'][0]},{loc['coords'][1]}" for loc in locations]
            
            logger.info(f"计算距离矩阵: {len(all_location_strs)} 个位置")
            matrix_result = await mcp_client.map_distance_matrix(
                origins=all_location_strs,
                destinations=all_location_strs,
                mode='driving'
            )
            
            if not matrix_result.get('success'):
                return {
                    'success': False,
                    'error': f"距离计算失败: {matrix_result.get('error')}"
                }
            
            matrix = matrix_result.get('matrix', [])
            
            def get_distance(from_idx: int, to_idx: int) -> tuple:
                try:
                    cell = matrix[from_idx][to_idx]
                    return cell.get('distance', float('inf')), cell.get('duration', 0)
                except (IndexError, TypeError):
                    return float('inf'), 0
            
            route_plans = []
            
            n_dest = len(dest_locs)
            if n_dest <= 5:
                for perm in permutations(range(n_dest)):
                    total_dist = 0
                    total_duration = 0
                    route_steps = []
                    
                    current_idx = 0
                    for dest_order in perm:
                        dest_idx = dest_order + 1
                        dist, dur = get_distance(current_idx, dest_idx)
                        total_dist += dist
                        total_duration += dur
                        
                        route_steps.append({
                            'from': locations[current_idx]['name'],
                            'to': dest_locs[dest_order]['name'],
                            'distance_km': round(dist / 1000, 1),
                            'duration_minutes': round(dur / 60)
                        })
                        current_idx = dest_idx
                    
                    route_plans.append({
                        'order': [dest_locs[i]['name'] for i in perm],
                        'order_indices': list(perm),
                        'total_distance_km': round(total_dist / 1000, 1),
                        'total_duration_hours': round(total_duration / 3600, 1),
                        'steps': route_steps
                    })
            else:
                for _ in range(min(max_routes * 2, 10)):
                    import random
                    perm = list(range(n_dest))
                    random.shuffle(perm)
                    
                    total_dist = 0
                    total_duration = 0
                    route_steps = []
                    
                    current_idx = 0
                    for dest_order in perm:
                        dest_idx = dest_order + 1
                        dist, dur = get_distance(current_idx, dest_idx)
                        total_dist += dist
                        total_duration += dur
                        
                        route_steps.append({
                            'from': locations[current_idx]['name'],
                            'to': dest_locs[dest_order]['name'],
                            'distance_km': round(dist / 1000, 1),
                            'duration_minutes': round(dur / 60)
                        })
                        current_idx = dest_idx
                    
                    route_plans.append({
                        'order': [dest_locs[i]['name'] for i in perm],
                        'order_indices': list(perm),
                        'total_distance_km': round(total_dist / 1000, 1),
                        'total_duration_hours': round(total_duration / 3600, 1),
                        'steps': route_steps
                    })
            
            route_plans.sort(key=lambda x: x['total_distance_km'])
            
            unique_routes = []
            seen_orders = set()
            for route in route_plans:
                order_key = tuple(route['order'])
                if order_key not in seen_orders:
                    seen_orders.add(order_key)
                    unique_routes.append(route)
                if len(unique_routes) >= max_routes:
                    break
            
            # 为最优路线获取详细导航步骤
            if unique_routes:
                best_route = unique_routes[0]
                try:
                    # 获取用户的出行方式
                    travel_mode = plan_summary.get('travel_mode', 'driving') if plan_summary else 'driving'
                    
                    # 构建路径规划的起终点坐标列表
                    route_coords = [start_loc['coords']]  # 出发地
                    order_indices = best_route.get('order_indices', [])
                    for idx in order_indices:
                        if idx < len(dest_locs):
                            route_coords.append(dest_locs[idx]['coords'])
                    
                    # 调用高德路径规划 API 获取详细导航
                    detailed_steps = []
                    for i in range(len(route_coords) - 1):
                        origin_str = f"{route_coords[i][1]},{route_coords[i][0]}"
                        dest_str = f"{route_coords[i+1][1]},{route_coords[i+1][0]}"
                        
                        if travel_mode == 'driving':
                            detail_result = await mcp_client.maps_direction_driving(
                                origin=origin_str, destination=dest_str
                            )
                        elif travel_mode == 'walking':
                            detail_result = await mcp_client.maps_direction_walking(
                                origin=origin_str, destination=dest_str
                            )
                        elif travel_mode == 'riding':
                            detail_result = await mcp_client.maps_direction_riding(
                                origin=origin_str, destination=dest_str
                            )
                        elif travel_mode == 'transit':
                            detail_result = await mcp_client.maps_direction_transit(
                                origin=origin_str, destination=dest_str,
                                city=departure_location.split('市')[0] if '市' in departure_location else departure_location
                            )
                        else:
                            detail_result = await mcp_client.maps_direction_driving(
                                origin=origin_str, destination=dest_str
                            )
                        
                        if detail_result.get('success'):
                            from_name = departure_location if i == 0 else dest_locs[order_indices[i-1]]['name']
                            to_name = dest_locs[order_indices[i]]['name']
                            detailed_steps.append({
                                'from': from_name,
                                'to': to_name,
                                'distance_km': round(detail_result.get('distance', 0) / 1000, 1),
                                'duration_minutes': round(detail_result.get('duration', 0) / 60),
                                'steps': detail_result.get('steps', [])[:5]  # 只保留前5个导航步骤
                            })
                    
                    best_route['detailed_navigation'] = detailed_steps
                    logger.info(f"获取详细导航成功，共 {len(detailed_steps)} 段")
                except Exception as e:
                    logger.warning(f"获取详细导航失败: {e}")
            
            for i, route in enumerate(unique_routes):
                route['route_id'] = chr(65 + i)
                route['route_name'] = f"方案{chr(65 + i)}"
            
            summary_lines = []
            for route in unique_routes:
                route_text = " → ".join([departure_location] + route['order'])
                summary_lines.append(
                    f"**{route['route_name']}**：{route_text}（总距离 {route['total_distance_km']}km，约 {route['total_duration_hours']}小时）"
                )
            
            summary_text = "\n".join(summary_lines)
            
            return {
                'success': True,
                'departure': departure_location,
                'destination_count': len(dest_locs),
                'routes': unique_routes,
                'best_route': best_route,
                'summary': summary_text,
                'message': f"为您找到{len(unique_routes)}条可选路线，推荐**方案A**（最短路线）。\n\n【最终答案】请直接向用户展示以下路线方案，不要再调用任何工具：\n\n{summary_text}",
                'final_answer': True
            }
            
        except Exception as e:
            logger.error(f"路线预览失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {'success': False, 'error': f"预览失败: {str(e)}"}
