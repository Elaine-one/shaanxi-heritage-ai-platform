# -*- coding: utf-8 -*-
"""
查询 Mixin — 知识图谱只读接口
提供非遗项目的多维度查询、邻近查询、关联查询等
"""

from typing import Dict, Any, List, Optional
from loguru import logger


class QueryMixin:
    """知识图谱查询操作"""

    driver: object = None

    # ──────────────────────────────
    # 基础查询
    # ──────────────────────────────

    def get_heritage_count(self) -> int:
        """获取非遗项目总数"""
        if not self.driver:
            return 0
        try:
            with self.driver.session() as session:
                result = session.run("MATCH (h:Heritage) RETURN count(h) as count")
                record = result.single()
                return record["count"] if record else 0
        except Exception as e:
            logger.error(f"查询非遗项目数量失败: {e}")
            return 0

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

    # ──────────────────────────────
    # ID 查询
    # ──────────────────────────────

    def query_heritage_by_ids(self, ids: List[int]) -> List[Dict[str, Any]]:
        """根据 ID 列表查询非遗项目"""
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

    # ──────────────────────────────
    # 关联查询
    # ──────────────────────────────

    def query_related_heritage(self, heritage_id: int, limit: int = 5,
                                relation_type: str = None) -> List[Dict[str, Any]]:
        """查询相关非遗项目

        Args:
            heritage_id: 非遗项目 ID
            limit: 返回数量
            relation_type: "category" / "region" / "level" 或 None(全部)
        """
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                if relation_type == "category":
                    query = """
                        MATCH (h1:Heritage {id: $id})-[:BELONGS_TO]->(c:Category)<-[:BELONGS_TO]-(h2:Heritage)
                        WHERE h1 <> h2
                        RETURN DISTINCT h2.id as id, h2.name as name, h2.category as category,
                               h2.region as region, h2.level as level, h2.description as description
                        LIMIT $limit
                    """
                elif relation_type == "region":
                    query = """
                        MATCH (h1:Heritage {id: $id})-[:LOCATED_AT]->(r:Region)<-[:LOCATED_AT]-(h2:Heritage)
                        WHERE h1 <> h2
                        RETURN DISTINCT h2.id as id, h2.name as name, h2.category as category,
                               h2.region as region, h2.level as level, h2.description as description
                        LIMIT $limit
                    """
                elif relation_type == "level":
                    query = """
                        MATCH (h1:Heritage {id: $id})-[:HAS_LEVEL]->(l:Level)<-[:HAS_LEVEL]-(h2:Heritage)
                        WHERE h1 <> h2
                        RETURN DISTINCT h2.id as id, h2.name as name, h2.category as category,
                               h2.region as region, h2.level as level, h2.description as description
                        LIMIT $limit
                    """
                else:
                    query = """
                        MATCH (h1:Heritage {id: $id})-[]-(h2:Heritage)
                        WHERE h1 <> h2
                        RETURN DISTINCT h2.id as id, h2.name as name, h2.category as category,
                               h2.region as region, h2.level as level, h2.description as description
                        LIMIT $limit
                    """

                result = session.run(query, id=heritage_id, limit=limit)

                related = []
                for record in result:
                    related.append(dict(record))
                return related
        except Exception as e:
            logger.error(f"查询相关非遗失败: {e}")
            return []

    # ──────────────────────────────
    # 维度查询
    # ──────────────────────────────

    def query_by_region(self, region: str, limit: int = 10) -> List[Dict[str, Any]]:
        """查询某地区的所有非遗项目"""
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
        """查询某类别的所有非遗项目"""
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
        """查询某级别的所有非遗项目"""
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

    # ──────────────────────────────
    # 邻近查询
    # ──────────────────────────────

    def query_nearby_heritages(self, latitude: float, longitude: float,
                                max_distance_km: float = 50,
                                limit: int = 10) -> List[Dict[str, Any]]:
        """根据坐标查询附近的非遗项目（内存 Haversine 计算）"""
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
        """根据已有 NEAR 关系查询附近非遗（图查询，免计算）"""
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

    def query_nearby_regions(self, region: str, distance_km: float = 100) -> List[str]:
        """查询邻近地区"""
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

    # ──────────────────────────────
    # 朝代查询
    # ──────────────────────────────

    def query_by_dynasty(self, dynasty_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """查询起源于某朝代的所有非遗项目"""
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:Heritage)-[:ORIGINATED_IN]->(d:Dynasty {name: $dynasty})
                    RETURN h.id as id, h.name as name, h.category as category,
                           h.region as region, h.level as level
                    ORDER BY h.name
                    LIMIT $limit
                """, dynasty=dynasty_name, limit=limit)

                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"查询朝代非遗失败: {e}")
            return []

    def query_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        """按朝代时间顺序排列非遗项目

        返回每个非遗的起源朝代信息，按 dynasty.start_year 排序。
        """
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:Heritage)-[:ORIGINATED_IN]->(d:Dynasty)
                    WHERE d.start_year IS NOT NULL
                    RETURN h.id as id, h.name as name, h.category as category,
                           h.region as region, h.level as level,
                           d.name as dynasty, d.start_year as dynasty_start
                    ORDER BY d.start_year, h.name
                    LIMIT $limit
                """, limit=limit)

                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"查询时间轴失败: {e}")
            return []

    def query_heritage_dynasties(self, heritage_id: int) -> List[Dict[str, Any]]:
        """查询单个非遗项目的所有起源朝代"""
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:Heritage {id: $id})-[:ORIGINATED_IN]->(d:Dynasty)
                    RETURN d.name as name, d.start_year as start_year,
                           d.end_year as end_year, d.capital as capital
                    ORDER BY d.start_year
                """, id=heritage_id)

                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"查询非遗朝代失败: {e}")
            return []

    # ──────────────────────────────
    # Region 层级查询
    # ──────────────────────────────

    def query_by_region_hierarchical(self, region: str, limit: int = 20) -> List[Dict[str, Any]]:
        """查询某地区及下属区县的所有非遗（支持 PART_OF 层级穿透）

        例如查询 '延安市' 会返回延安市及其下属安塞区、富县的所有非遗。
        """
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:Heritage)-[:LOCATED_AT]->(r:Region)
                    OPTIONAL MATCH (r)-[:PART_OF*0..2]->(parent:Region)
                    WHERE parent.name = $region OR r.name = $region
                    RETURN DISTINCT h.id as id, h.name as name, h.category as category,
                           h.level as level, r.name as region_name
                    ORDER BY h.name
                    LIMIT $limit
                """, region=region, limit=limit)

                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"层级查询地区非遗失败: {e}")
            return []

    def query_region_tree(self, region_name: str = '陕西省') -> List[Dict[str, Any]]:
        """查询地区层级子树（下属市/区县及非遗数量）"""
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (r:Region {name: $name})-[rel:PART_OF*0..1]->(child:Region)
                    OPTIONAL MATCH (h:Heritage)-[:LOCATED_AT]->(child)
                    RETURN child.name as name, child.level as level,
                           count(DISTINCT h) as heritage_count
                    ORDER BY child.level, child.name
                """, name=region_name)

                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"查询地区层级树失败: {e}")
            return []

    # ──────────────────────────────
    # 传承人查询
    # ──────────────────────────────

    def query_inheritors_by_heritage(self, heritage_id: int) -> List[Dict[str, Any]]:
        """查询指定非遗项目的所有传承人（含师承关系）

        一跳遍历 HAS_INHERITOR → Inheritor，同时查 STUDIED_UNDER 师徒链。
        """
        if not self.driver:
            return []

        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (h:Heritage {id: $id})-[:HAS_INHERITOR]->(i:Inheritor)
                    OPTIONAL MATCH (i)-[:STUDIED_UNDER]->(teacher:Inheritor)
                    OPTIONAL MATCH (student:Inheritor)-[:STUDIED_UNDER]->(i)
                    RETURN i.name as name,
                           COALESCE(i.level, '') as level,
                           i.birth_year as birth_year,
                           COALESCE(i.status, '') as status,
                           COALESCE(i.gender, '') as gender,
                           i.generation as generation,
                           COALESCE(i.bio, '') as bio,
                           COALESCE(teacher.name, '') as teacher,
                           collect(DISTINCT student.name) as students
                    ORDER BY i.generation, i.name
                """, id=heritage_id)

                inheritors = []
                for record in result:
                    inh = dict(record)
                    if inh.get('students'):
                        inh['students'] = [s for s in inh['students'] if s]
                    else:
                        inh['students'] = []
                    inheritors.append(inh)
                return inheritors
        except Exception as e:
            logger.error(f"查询传承人失败 (heritage_id={heritage_id}): {e}")
            return []

    # ──────────────────────────────
    # 附加关系
    # ──────────────────────────────

    def add_heritage_relation(self, from_id: int, to_id: int,
                               similarity: float = 0.5) -> bool:
        """添加非遗项目之间的 RELATED_TO 关系"""
        return self._merge_relation('Heritage', from_id, 'RELATED_TO',
                                    'Heritage', to_id, {'similarity': similarity})

    def add_region_near_relation(self, region1: str, region2: str,
                                  distance_km: float) -> bool:
        """添加地区邻近关系"""
        return self._merge_relation('Region', region1, 'NEAR',
                                    'Region', region2, {'distance_km': distance_km})
