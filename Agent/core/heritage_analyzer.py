# -*- coding: utf-8 -*-
"""
非遗项目分析器模块
负责分析用户选择的非遗项目，获取详细信息并进行初步处理
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from loguru import logger
from geopy.distance import geodesic
from config import config

class HeritageAnalyzer:
    """
    非遗项目分析器
    负责获取和分析非遗项目信息
    """
    
    def __init__(self):
        """
        初始化分析器
        """
        self.backend_api_url = config.BACKEND_API_URL
        logger.info("非遗项目分析器初始化完成")
    
    async def analyze_heritage_items(self, heritage_ids: List[int]) -> Dict[str, Any]:
        """
        分析选中的非遗项目
        
        Args:
            heritage_ids (List[int]): 非遗项目ID列表
        
        Returns:
            Dict[str, Any]: 分析结果
        """
        try:
            logger.info(f"开始分析非遗项目: {heritage_ids}")
            
            # 获取项目详细信息
            heritage_items = await self._fetch_heritage_details(heritage_ids)
            
            if not heritage_items:
                return {
                    'success': False,
                    'error': '无法获取非遗项目信息'
                }
            
            # 进行地理分析
            geo_analysis = self._analyze_geography(heritage_items)
            
            # 进行类别分析
            category_analysis = self._analyze_categories(heritage_items)
            
            # 进行时间估算
            time_analysis = self._analyze_time_requirements(heritage_items)
            
            # 生成推荐路线
            route_suggestions = self._generate_route_suggestions(heritage_items, geo_analysis)
            
            result = {
                'success': True,
                'heritage_items': heritage_items,
                'analysis': {
                    'geography': geo_analysis,
                    'categories': category_analysis,
                    'time_requirements': time_analysis,
                    'route_suggestions': route_suggestions
                },
                'summary': {
                    'total_items': len(heritage_items),
                    'regions_covered': len(set(item['region'] for item in heritage_items)),
                    'categories_covered': len(set(item['category'] for item in heritage_items)),
                    'estimated_days': time_analysis.get('recommended_days', 1)
                }
            }
            
            logger.info(f"非遗项目分析完成，共{len(heritage_items)}个项目")
            return result
            
        except Exception as e:
            logger.error(f"分析非遗项目时发生错误: {str(e)}")
            return {
                'success': False,
                'error': f'分析失败: {str(e)}'
            }
    
    async def _fetch_heritage_details(self, heritage_ids: List[int]) -> List[Dict[str, Any]]:
        """
        从后端API获取非遗项目详细信息
        
        Args:
            heritage_ids (List[int]): 项目ID列表
        
        Returns:
            List[Dict[str, Any]]: 项目详细信息列表
        """
        try:
            if not heritage_ids:
                logger.warning("非遗项目ID列表为空")
                return []
                
            logger.info(f"获取非遗项目信息: {heritage_ids}")
            
            # 构建API请求URL - 使用GET请求获取所有项目，然后过滤
            api_url = f"{self.backend_api_url}/items/"
            
            all_items = []
            next_url = api_url
            
            # 使用aiohttp调用后端API，处理分页
            async with aiohttp.ClientSession() as session:
                while next_url:
                    async with session.get(next_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # 检查API返回的数据结构
                            if isinstance(data, dict) and 'results' in data:
                                all_items.extend(data['results'])
                                
                                # 检查是否有下一页
                                next_url = data.get('next')
                                if next_url:
                                    logger.info(f"获取下一页数据: {next_url}")
                                else:
                                    logger.info(f"已获取所有{len(all_items)}个项目数据")
                                    break
                            else:
                                logger.warning(f"API返回数据结构异常: {data}")
                                return []
                        else:
                            logger.error(f"API请求失败，状态码: {response.status}")
                            return []
            
            # 过滤出指定ID的项目
            filtered_items = [item for item in all_items if item.get('id') in heritage_ids]
            logger.info(f"成功获取{len(filtered_items)}个非遗项目信息")
            return filtered_items
                        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP请求错误: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"获取非遗项目信息失败: {str(e)}")
            return []
    

    
    def _analyze_geography(self, heritage_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析地理分布
        
        Args:
            heritage_items (List[Dict[str, Any]]): 非遗项目列表
        
        Returns:
            Dict[str, Any]: 地理分析结果
        """
        if not heritage_items:
            return {}
        
        # 提取有效的地理坐标
        locations = []
        for item in heritage_items:
            if item.get('latitude') and item.get('longitude'):
                locations.append({
                    'name': item['name'],
                    'lat': float(item['latitude']),
                    'lng': float(item['longitude']),
                    'region': item.get('region', '未知'),
                    'category': item.get('category', '未分类')
                })
        
        if not locations:
            return {
                'error': '没有有效的地理坐标信息'
            }
        
        # 计算中心点
        center_lat = sum(loc['lat'] for loc in locations) / len(locations)
        center_lng = sum(loc['lng'] for loc in locations) / len(locations)
        
        # 计算距离矩阵
        distances = []
        for i, loc1 in enumerate(locations):
            for j, loc2 in enumerate(locations[i+1:], i+1):
                distance = geodesic(
                    (loc1['lat'], loc1['lng']),
                    (loc2['lat'], loc2['lng'])
                ).kilometers
                distances.append({
                    'from': loc1['name'],
                    'to': loc2['name'],
                    'distance_km': round(distance, 2)
                })
        
        # 计算总覆盖范围
        if distances:
            max_distance = max(d['distance_km'] for d in distances)
            avg_distance = sum(d['distance_km'] for d in distances) / len(distances)
        else:
            max_distance = 0
            avg_distance = 0
        
        return {
            'center_point': {
                'latitude': round(center_lat, 4),
                'longitude': round(center_lng, 4)
            },
            'locations': locations,
            'distances': distances,
            'coverage': {
                'max_distance_km': round(max_distance, 2),
                'avg_distance_km': round(avg_distance, 2),
                'total_locations': len(locations)
            },
            'regions': list(set(loc['region'] for loc in locations))
        }
    
    def _analyze_categories(self, heritage_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析项目类别分布
        
        Args:
            heritage_items (List[Dict[str, Any]]): 非遗项目列表
        
        Returns:
            Dict[str, Any]: 类别分析结果
        """
        categories = {}
        for item in heritage_items:
            category = item.get('category', '未分类')
            if category not in categories:
                categories[category] = {
                    'count': 0,
                    'items': []
                }
            categories[category]['count'] += 1
            categories[category]['items'].append(item['name'])
        
        return {
            'distribution': categories,
            'total_categories': len(categories),
            'most_common': max(categories.items(), key=lambda x: x[1]['count'])[0] if categories else None
        }
    
    def _analyze_time_requirements(self, heritage_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析时间需求
        
        Args:
            heritage_items (List[Dict[str, Any]]): 非遗项目列表
        
        Returns:
            Dict[str, Any]: 时间分析结果
        """
        total_visit_time = 0
        time_details = []
        
        for item in heritage_items:
            visit_duration = item.get('visit_duration', 2)  # 默认2小时
            total_visit_time += visit_duration
            time_details.append({
                'name': item['name'],
                'duration_hours': visit_duration,
                'best_time': item.get('best_visit_time', '全年')
            })
        
        # 考虑交通时间（估算）
        travel_time_estimate = len(heritage_items) * 1.5  # 每个地点间平均1.5小时交通
        total_time_with_travel = total_visit_time + travel_time_estimate
        
        # 推荐天数（每天8小时有效时间）
        recommended_days = max(1, round(total_time_with_travel / 8))
        
        return {
            'total_visit_hours': total_visit_time,
            'estimated_travel_hours': travel_time_estimate,
            'total_hours': total_time_with_travel,
            'recommended_days': recommended_days,
            'time_details': time_details,
            'daily_schedule_suggestion': {
                'hours_per_day': 8,
                'items_per_day': max(1, len(heritage_items) // recommended_days)
            }
        }
    
    def _generate_route_suggestions(self, 
                                  heritage_items: List[Dict[str, Any]], 
                                  geo_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成路线建议
        
        Args:
            heritage_items (List[Dict[str, Any]]): 非遗项目列表
            geo_analysis (Dict[str, Any]): 地理分析结果
        
        Returns:
            List[Dict[str, Any]]: 路线建议列表
        """
        if not geo_analysis.get('locations'):
            return []
        
        locations = geo_analysis['locations']
        
        # 简单的最近邻路线规划
        if len(locations) <= 1:
            return [{
                'route_name': '单点游览',
                'sequence': locations,
                'total_distance': 0,
                'description': '单个景点游览'
            }]
        
        # 找到最优路线（简化版TSP）
        optimized_route = self._optimize_route(locations)
        
        return [{
            'route_name': '推荐路线',
            'sequence': optimized_route['sequence'],
            'total_distance': optimized_route['total_distance'],
            'description': '基于地理位置优化的游览路线'
        }]
    
    def _optimize_route(self, locations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        优化路线（简化的旅行商问题解决方案）
        
        Args:
            locations (List[Dict[str, Any]]): 位置列表
        
        Returns:
            Dict[str, Any]: 优化后的路线
        """
        if len(locations) <= 2:
            return {
                'sequence': locations,
                'total_distance': 0 if len(locations) <= 1 else geodesic(
                    (locations[0]['lat'], locations[0]['lng']),
                    (locations[1]['lat'], locations[1]['lng'])
                ).kilometers
            }
        
        # 使用最近邻算法
        unvisited = locations[1:]
        route = [locations[0]]
        total_distance = 0
        
        current = locations[0]
        
        while unvisited:
            # 找到最近的未访问点
            nearest = min(unvisited, key=lambda loc: geodesic(
                (current['lat'], current['lng']),
                (loc['lat'], loc['lng'])
            ).kilometers)
            
            distance = geodesic(
                (current['lat'], current['lng']),
                (nearest['lat'], nearest['lng'])
            ).kilometers
            
            total_distance += distance
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return {
            'sequence': route,
            'total_distance': round(total_distance, 2)
        }
