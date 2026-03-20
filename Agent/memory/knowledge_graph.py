# -*- coding: utf-8 -*-
"""
知识图谱模块
使用 Neo4j 存储非遗项目知识图谱，支持关联推理和精确查询
"""

import math
import logging
import os
from typing import Dict, Any, List, Optional
from loguru import logger

os.environ["NEO4J_PYTHON_DRIVER_LOG_LEVEL"] = "ERROR"

from neo4j import GraphDatabase

neo4j_logger = logging.getLogger("neo4j")
neo4j_logger.setLevel(logging.CRITICAL)


class KnowledgeGraph:
    """
    知识图谱管理器
    负责非遗项目知识的存储、查询和推理
    """
    
    NODE_LABELS = {
        'Heritage': '非遗项目',
        'Category': '类别',
        'Region': '地区',
        'Level': '级别',
        'Batch': '批次',
        'Inheritor': '传承人',
        'Location': '位置'
    }
    
    RELATION_TYPES = {
        'BELONGS_TO': '属于类别',
        'LOCATED_AT': '位于地区',
        'HAS_LEVEL': '具有级别',
        'IN_BATCH': '属于批次',
        'HAS_INHERITOR': '有传承人',
        'RELATED_TO': '相关',
        'NEAR': '邻近',
        'AT_LOCATION': '位于'
    }
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        from Agent.config.settings import config
        self.uri = uri or config.NEO4J_URI
        self.user = user or config.NEO4J_USER
        self.password = password or config.NEO4J_PASSWORD
        
        self.driver = None
        self._connect()
    
    def _connect(self):
        """连接 Neo4j 数据库"""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info(f"知识图谱连接成功: {self.uri}")
        except Exception as e:
            logger.warning(f"知识图谱连接失败: {e}")
            self.driver = None
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def is_connected(self) -> bool:
        """检查连接状态"""
        if not self.driver:
            return False
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except:
            return False
    
    def get_heritage_count(self) -> int:
        """获取非遗项目数量"""
        if not self.driver:
            return 0
        try:
            with self.driver.session() as session:
                result = session.run("MATCH (h:Heritage) RETURN count(h) as count")
                record = result.single()
                return record["count"] if record else 0
        except:
            return 0
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        计算两点之间的距离（公里）
        使用 Haversine 公式
        
        Args:
            lat1: 点1纬度
            lon1: 点1经度
            lat2: 点2纬度
            lon2: 点2经度
        
        Returns:
            距离（公里）
        """
        if None in [lat1, lon1, lat2, lon2]:
            return float('inf')
        
        R = 6371
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def create_heritage_node(self, heritage_data: Dict[str, Any]) -> bool:
        """
        创建非遗项目节点
        
        Args:
            heritage_data: 非遗项目数据，包含 id, name, category, region 等字段
        
        Returns:
            是否创建成功
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (h:Heritage {id: $id})
                    SET h.name = $name,
                        h.pinyin_name = $pinyin_name,
                        h.level = $level,
                        h.category = $category,
                        h.region = $region,
                        h.batch = $batch,
                        h.description = $description,
                        h.history = $history,
                        h.features = $features,
                        h.value = $value,
                        h.status = $status,
                        h.protection_measures = $protection_measures,
                        h.inheritors = $inheritors,
                        h.related_works = $related_works,
                        h.latitude = $latitude,
                        h.longitude = $longitude,
                        h.updated_at = datetime()
                """, 
                    id=heritage_data.get('id'),
                    name=heritage_data.get('name', ''),
                    pinyin_name=heritage_data.get('pinyin_name', ''),
                    level=heritage_data.get('level', ''),
                    category=heritage_data.get('category', ''),
                    region=heritage_data.get('region', ''),
                    batch=heritage_data.get('batch', ''),
                    description=heritage_data.get('description', ''),
                    history=heritage_data.get('history', ''),
                    features=heritage_data.get('features', ''),
                    value=heritage_data.get('value', ''),
                    status=heritage_data.get('status', ''),
                    protection_measures=heritage_data.get('protection_measures', ''),
                    inheritors=heritage_data.get('inheritors', ''),
                    related_works=heritage_data.get('related_works', ''),
                    latitude=heritage_data.get('latitude'),
                    longitude=heritage_data.get('longitude')
                )
            return True
        except Exception as e:
            logger.error(f"创建非遗节点失败: {e}")
            return False
    
    def create_location_node(self, name: str, latitude: float, 
                            longitude: float, location_type: str = 'heritage',
                            region: str = '') -> bool:
        """
        创建位置节点
        
        Args:
            name: 位置名称
            latitude: 纬度
            longitude: 经度
            location_type: 位置类型 (heritage, attraction, city)
            region: 所属地区
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (l:Location {name: $name})
                    SET l.latitude = $latitude,
                        l.longitude = $longitude,
                        l.type = $location_type,
                        l.region = $region
                """, name=name, latitude=latitude, longitude=longitude,
                     location_type=location_type, region=region)
            return True
        except Exception as e:
            logger.error(f"创建位置节点失败: {e}")
            return False
    
    def create_category_node(self, name: str, description: str = '') -> bool:
        """创建类别节点"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (c:Category {name: $name})
                    SET c.description = $description
                """, name=name, description=description)
            return True
        except Exception as e:
            logger.error(f"创建类别节点失败: {e}")
            return False
    
    def create_region_node(self, name: str, province: str = '陕西省', 
                          city: str = '', latitude: float = None, 
                          longitude: float = None) -> bool:
        """创建地区节点"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (r:Region {name: $name})
                    SET r.province = $province,
                        r.city = $city,
                        r.latitude = $latitude,
                        r.longitude = $longitude
                """, name=name, province=province, city=city, 
                     latitude=latitude, longitude=longitude)
            return True
        except Exception as e:
            logger.error(f"创建地区节点失败: {e}")
            return False
    
    def create_level_node(self, name: str, priority: int = 0) -> bool:
        """创建级别节点"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (l:Level {name: $name})
                    SET l.priority = $priority
                """, name=name, priority=priority)
            return True
        except Exception as e:
            logger.error(f"创建级别节点失败: {e}")
            return False
    
    def create_batch_node(self, name: str, year: int = None) -> bool:
        """创建批次节点"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (b:Batch {name: $name})
                    SET b.year = $year
                """, name=name, year=year)
            return True
        except Exception as e:
            logger.error(f"创建批次节点失败: {e}")
            return False
    
    def create_relation(self, from_label: str, from_id: Any, 
                       relation_type: str, to_label: str, 
                       to_id: Any, properties: Dict = None) -> bool:
        """
        创建关系
        
        Args:
            from_label: 起始节点标签
            from_id: 起始节点 ID
            relation_type: 关系类型
            to_label: 目标节点标签
            to_id: 目标节点 ID
            properties: 关系属性
        """
        if not self.driver:
            return False
        
        id_field = 'id' if from_label == 'Heritage' else 'name'
        to_id_field = 'id' if to_label == 'Heritage' else 'name'
        
        try:
            with self.driver.session() as session:
                query = f"""
                    MATCH (a:{from_label} {{{id_field}: $from_id}})
                    MATCH (b:{to_label} {{{to_id_field}: $to_id}})
                    MERGE (a)-[r:{relation_type}]->(b)
                """
                if properties:
                    set_clause = ', '.join([f'r.{k} = ${k}' for k in properties.keys()])
                    query = query.replace('MERGE (a)-[r:{relation_type}]->(b)', 
                                         f'MERGE (a)-[r:{relation_type}]->(b) SET {set_clause}')
                    session.run(query, from_id=from_id, to_id=to_id, **properties)
                else:
                    session.run(query, from_id=from_id, to_id=to_id)
            return True
        except Exception as e:
            logger.error(f"创建关系失败: {e}")
            return False
    
    def build_heritage_relations(self, heritage_id: int, category: str, 
                                 region: str, level: str, batch: str,
                                 latitude: float = None, longitude: float = None,
                                 name: str = '') -> bool:
        """
        构建非遗项目的所有关系
        
        Args:
            heritage_id: 非遗项目 ID
            category: 类别名称
            region: 地区名称
            level: 级别名称
            batch: 批次名称
            latitude: 纬度
            longitude: 经度
            name: 非遗名称
        """
        results = []
        
        if category:
            self.create_category_node(category, '')
            results.append(self.create_relation('Heritage', heritage_id, 'BELONGS_TO', 'Category', category))
        
        if region:
            self.create_region_node(region, '陕西', '')
            results.append(self.create_relation('Heritage', heritage_id, 'LOCATED_AT', 'Region', region))
        
        if level:
            self.create_level_node(level, 0)
            results.append(self.create_relation('Heritage', heritage_id, 'HAS_LEVEL', 'Level', level))
        
        if batch:
            self.create_batch_node(batch)
            results.append(self.create_relation('Heritage', heritage_id, 'IN_BATCH', 'Batch', batch))
        
        if latitude and longitude and name:
            self.create_location_node(name, latitude, longitude, 'heritage', region or '')
            results.append(self.create_relation('Heritage', heritage_id, 'AT_LOCATION', 'Location', name))
        
        return all(results) if results else True
    
    def build_near_relations(self, max_distance_km: float = 100) -> int:
        """
        构建所有非遗项目之间的邻近关系
        
        Args:
            max_distance_km: 最大距离（公里）
        
        Returns:
            创建的关系数量
        """
        if not self.driver:
            return 0
        
        try:
            heritages = self.get_all_heritages_with_coordinates()
            
            if not heritages:
                return 0
            
            relation_count = 0
            
            for i, h1 in enumerate(heritages):
                for h2 in heritages[i + 1:]:
                    distance = self.calculate_distance(
                        h1['latitude'], h1['longitude'],
                        h2['latitude'], h2['longitude']
                    )
                    
                    if distance <= max_distance_km:
                        self.create_near_relation(
                            h1['id'], h2['id'], distance
                        )
                        relation_count += 1
            
            logger.info(f"创建了 {relation_count} 个邻近关系")
            return relation_count
            
        except Exception as e:
            logger.error(f"构建邻近关系失败: {e}")
            return 0
    
    def create_near_relation(self, heritage_id1: int, heritage_id2: int, 
                            distance_km: float) -> bool:
        """
        创建两个非遗项目之间的邻近关系
        
        Args:
            heritage_id1: 非遗项目1 ID
            heritage_id2: 非遗项目2 ID
            distance_km: 距离（公里）
        """
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (h1:Heritage {id: $id1})
                    MATCH (h2:Heritage {id: $id2})
                    MERGE (h1)-[r:NEAR]->(h2)
                    SET r.distance_km = $distance_km
                """, id1=heritage_id1, id2=heritage_id2, distance_km=round(distance_km, 2))
            return True
        except Exception as e:
            logger.error(f"创建邻近关系失败: {e}")
            return False
    
    def get_all_heritages_with_coordinates(self) -> List[Dict[str, Any]]:
        """获取所有有经纬度的非遗项目"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:Heritage)
                    WHERE h.latitude IS NOT NULL AND h.longitude IS NOT NULL
                    RETURN h.id as id, h.name as name, h.latitude as latitude, 
                           h.longitude as longitude, h.region as region
                """)
                
                heritages = []
                for record in result:
                    heritages.append(dict(record))
                return heritages
        except Exception as e:
            logger.error(f"获取非遗坐标失败: {e}")
            return []
    
    def query_nearby_heritages(self, latitude: float, longitude: float, 
                               max_distance_km: float = 50,
                               limit: int = 10) -> List[Dict[str, Any]]:
        """
        查询附近的非遗项目
        
        Args:
            latitude: 纬度
            longitude: 经度
            max_distance_km: 最大距离（公里）
            limit: 返回数量
        
        Returns:
            附近的非遗项目列表
        """
        if not self.driver:
            return []
        
        try:
            heritages = self.get_all_heritages_with_coordinates()
            
            nearby = []
            for h in heritages:
                distance = self.calculate_distance(
                    latitude, longitude,
                    h['latitude'], h['longitude']
                )
                if distance <= max_distance_km:
                    h['distance_km'] = round(distance, 2)
                    nearby.append(h)
            
            nearby.sort(key=lambda x: x['distance_km'])
            return nearby[:limit]
            
        except Exception as e:
            logger.error(f"查询附近非遗失败: {e}")
            return []
    
    def query_nearby_heritages_by_id(self, heritage_id: int, 
                                     max_distance_km: float = 100,
                                     limit: int = 5) -> List[Dict[str, Any]]:
        """
        查询指定非遗项目附近的其他非遗项目
        
        Args:
            heritage_id: 非遗项目 ID
            max_distance_km: 最大距离（公里）
            limit: 返回数量
        
        Returns:
            附近的非遗项目列表
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h1:Heritage {id: $id})-[n:NEAR]->(h2:Heritage)
                    WHERE n.distance_km <= $max_distance
                    RETURN h2.id as id, h2.name as name, h2.region as region,
                           h2.category as category, h2.level as level,
                           n.distance_km as distance_km
                    ORDER BY n.distance_km
                    LIMIT $limit
                """, id=heritage_id, max_distance=max_distance_km, limit=limit)
                
                nearby = []
                for record in result:
                    nearby.append(dict(record))
                return nearby
        except Exception as e:
            logger.error(f"查询附近非遗失败: {e}")
            return []
    
    def query_heritage_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """
        根据 ID 列表查询非遗项目
        
        Args:
            ids: 非遗项目 ID 列表
        
        Returns:
            非遗项目列表
        """
        if not self.driver or not ids:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:Heritage)
                    WHERE h.id IN $ids
                    RETURN h.id as id, h.name as name, 
                           COALESCE(h.pinyin_name, '') as pinyin_name,
                           COALESCE(h.level, '') as level, 
                           COALESCE(h.category, '') as category, 
                           COALESCE(h.region, '') as region,
                           COALESCE(h.batch, '') as batch, 
                           COALESCE(h.description, '') as description, 
                           COALESCE(h.history, '') as history,
                           COALESCE(h.features, '') as features, 
                           COALESCE(h.value, '') as value, 
                           COALESCE(h.status, '') as status,
                           COALESCE(h.protection_measures, '') as protection_measures, 
                           COALESCE(h.inheritors, '') as inheritors,
                           COALESCE(h.related_works, '') as related_works, 
                           h.latitude as latitude, h.longitude as longitude
                    ORDER BY h.id
                """, ids=ids)
                
                heritages = []
                for record in result:
                    heritages.append(dict(record))
                return heritages
        except Exception as e:
            logger.error(f"查询非遗失败: {e}")
            return []
    
    def query_heritage_by_id(self, heritage_id: int) -> Optional[Dict[str, Any]]:
        """根据 ID 查询单个非遗项目"""
        results = self.query_heritage_by_ids([heritage_id])
        return results[0] if results else None
    
    def query_related_heritage(self, heritage_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        查询相关非遗项目
        
        Args:
            heritage_id: 非遗项目 ID
            limit: 返回数量
        
        Returns:
            相关非遗项目列表
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h1:Heritage {id: $id})-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(h2:Heritage)
                    WHERE h1 <> h2
                    RETURN DISTINCT h2.id as id, h2.name as name, h2.category as category,
                           h2.region as region, h2.level as level, h2.description as description
                    LIMIT $limit
                """, id=heritage_id, limit=limit)
                
                related = []
                for record in result:
                    related.append(dict(record))
                return related
        except Exception as e:
            logger.error(f"查询相关非遗失败: {e}")
            return []
    
    def query_by_region(self, region: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        查询某地区的所有非遗项目
        
        Args:
            region: 地区名称
            limit: 返回数量
        
        Returns:
            非遗项目列表
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:Heritage)-[:LOCATED_AT]->(r:Region)
                    WHERE r.name CONTAINS $region
                    RETURN h.id as id, h.name as name, h.category as category,
                           h.level as level, h.description as description,
                           h.latitude as latitude, h.longitude as longitude
                    LIMIT $limit
                """, region=region, limit=limit)
                
                heritages = []
                for record in result:
                    heritages.append(dict(record))
                return heritages
        except Exception as e:
            logger.error(f"查询地区非遗失败: {e}")
            return []
    
    def query_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        查询某类别的所有非遗项目
        
        Args:
            category: 类别名称
            limit: 返回数量
        
        Returns:
            非遗项目列表
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:Heritage)-[:BELONGS_TO]->(c:Category)
                    WHERE c.name CONTAINS $category
                    RETURN h.id as id, h.name as name, h.region as region,
                           h.level as level, h.description as description,
                           h.latitude as latitude, h.longitude as longitude
                    LIMIT $limit
                """, category=category, limit=limit)
                
                heritages = []
                for record in result:
                    heritages.append(dict(record))
                return heritages
        except Exception as e:
            logger.error(f"查询类别非遗失败: {e}")
            return []
    
    def query_by_level(self, level: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        查询某级别的所有非遗项目
        
        Args:
            level: 级别名称
            limit: 返回数量
        
        Returns:
            非遗项目列表
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:Heritage)-[:HAS_LEVEL]->(l:Level)
                    WHERE l.name CONTAINS $level
                    RETURN h.id as id, h.name as name, h.region as region,
                           h.category as category, h.description as description,
                           h.latitude as latitude, h.longitude as longitude
                    LIMIT $limit
                """, level=level, limit=limit)
                
                heritages = []
                for record in result:
                    heritages.append(dict(record))
                return heritages
        except Exception as e:
            logger.error(f"查询级别非遗失败: {e}")
            return []
    
    def query_nearby_regions(self, region: str, distance_km: float = 100) -> List[str]:
        """
        查询邻近地区
        
        Args:
            region: 地区名称
            distance_km: 距离阈值（公里）
        
        Returns:
            邻近地区列表
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (r1:Region {name: $region})-[n:NEAR]->(r2:Region)
                    WHERE n.distance_km <= $distance_km
                    RETURN r2.name as name
                    ORDER BY n.distance_km
                """, region=region, distance_km=distance_km)
                
                regions = []
                for record in result:
                    regions.append(record['name'])
                return regions
        except Exception as e:
            logger.error(f"查询邻近地区失败: {e}")
            return []
    
    def add_heritage_relation(self, from_id: int, to_id: int, 
                              similarity: float = 0.5) -> bool:
        """
        添加非遗项目之间的关联关系
        
        Args:
            from_id: 起始非遗 ID
            to_id: 目标非遗 ID
            similarity: 相似度
        """
        return self.create_relation('Heritage', from_id, 'RELATED_TO', 
                                   'Heritage', to_id, {'similarity': similarity})
    
    def add_region_near_relation(self, region1: str, region2: str, 
                                 distance_km: float) -> bool:
        """
        添加地区邻近关系
        
        Args:
            region1: 地区1名称
            region2: 地区2名称
            distance_km: 距离（公里）
        """
        return self.create_relation('Region', region1, 'NEAR', 
                                   'Region', region2, {'distance_km': distance_km})
    
    def delete_heritage(self, heritage_id: int) -> bool:
        """删除非遗项目节点及其关系"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (h:Heritage {id: $id})
                    DETACH DELETE h
                """, id=heritage_id)
            return True
        except Exception as e:
            logger.error(f"删除非遗失败: {e}")
            return False
    
    def update_heritage(self, heritage_id: int, updates: Dict[str, Any]) -> bool:
        """更新非遗项目节点"""
        if not self.driver or not updates:
            return False
        
        try:
            set_clause = ', '.join([f'h.{k} = ${k}' for k in updates.keys()])
            
            with self.driver.session() as session:
                session.run(f"""
                    MATCH (h:Heritage {{id: $id}})
                    SET {set_clause}, h.updated_at = datetime()
                """, id=heritage_id, **updates)
            return True
        except Exception as e:
            logger.error(f"更新非遗失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """获取知识图谱统计信息"""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                stats = {}
                
                result = session.run("MATCH (h:Heritage) RETURN count(h) as count")
                record = result.single()
                stats['heritage_count'] = record['count'] if record else 0
                
                result = session.run("MATCH (c:Category) RETURN count(c) as count")
                record = result.single()
                stats['category_count'] = record['count'] if record else 0
                
                result = session.run("MATCH (r:Region) RETURN count(r) as count")
                record = result.single()
                stats['region_count'] = record['count'] if record else 0
                
                result = session.run("MATCH (l:Location) RETURN count(l) as count")
                record = result.single()
                stats['location_count'] = record['count'] if record else 0
                
                result = session.run("MATCH ()-[n:NEAR]->() RETURN count(n) as count")
                record = result.single()
                stats['near_count'] = record['count'] if record else 0
                
                return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def clear_all(self) -> bool:
        """清空所有数据（谨慎使用）"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
            logger.warning("知识图谱已清空")
            return True
        except Exception as e:
            logger.error(f"清空知识图谱失败: {e}")
            return False


_knowledge_graph_instance = None


def get_knowledge_graph() -> KnowledgeGraph:
    """获取知识图谱单例"""
    global _knowledge_graph_instance
    if _knowledge_graph_instance is None:
        try:
            _knowledge_graph_instance = KnowledgeGraph()
        except Exception as e:
            logger.warning(f"知识图谱初始化失败: {e}")
            return None
    return _knowledge_graph_instance
