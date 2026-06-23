# -*- coding: utf-8 -*-
"""
核心实体 Mixin — Heritage / Category / Region / Level / Batch / Location
负责节点创建、基础关系和邻近关系的构建
"""

from typing import Dict, Any, List
from loguru import logger


class HeritageMixin:
    """Heritage 及其附属实体 (Category/Region/Level/Batch/Location) 的写操作"""

    driver: object = None

    # ──────────────────────────────
    # Heritage 节点
    # ──────────────────────────────

    def create_heritage_node(self, heritage_data: Dict[str, Any]) -> bool:
        """创建/更新非遗项目节点

        Args:
            heritage_data: 非遗数据，需含 id 及 content 字段
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
                    longitude=heritage_data.get('longitude'),
                )
            return True
        except Exception as e:
            logger.error(f"创建非遗节点失败: {e}")
            return False

    # ──────────────────────────────
    # Location 节点
    # ──────────────────────────────

    def create_location_node(self, name: str, latitude: float,
                             longitude: float, location_type: str = 'heritage',
                             region: str = '') -> bool:
        """创建位置节点"""
        return self._merge_node('Location', 'name',
                                name=name, latitude=latitude, longitude=longitude,
                                type=location_type, region=region)

    # ──────────────────────────────
    # Category / Region / Level / Batch 节点
    # ──────────────────────────────

    def create_category_node(self, name: str, description: str = '') -> bool:
        """创建类别节点"""
        return self._merge_node('Category', 'name',
                                name=name, description=description)

    def create_region_node(self, name: str, province: str = '陕西省',
                           city: str = '', level: str = '',
                           latitude: float = None,
                           longitude: float = None) -> bool:
        """创建地区节点，level: 省/地级市/区县"""
        return self._merge_node('Region', 'name',
                                name=name, province=province, city=city,
                                level=level, latitude=latitude,
                                longitude=longitude)

    def create_level_node(self, name: str, priority: int = 0) -> bool:
        """创建级别节点"""
        return self._merge_node('Level', 'name',
                                name=name, priority=priority)

    def create_batch_node(self, name: str, year: int = None) -> bool:
        """创建批次节点"""
        return self._merge_node('Batch', 'name', name=name, year=year)

    # ──────────────────────────────
    # Region 层级树
    # ──────────────────────────────

    # 陕西非遗区县级 Region 树（省→市→区县）
    REGION_TREE: Dict[str, list] = {
        '西安市': ['鄠邑区', '长安区', '蓝田县', '高陵区', '新城区', '雁塔区', '莲湖区', '碑林区'],
        '延安市': ['安塞区', '富县'],
        '渭南市': ['合阳县', '华阴市', '韩城市', '临渭区', '富平县'],
        '宝鸡市': ['陈仓区', '凤翔区', '陇县', '金台区'],
        '咸阳市': ['秦都区', '杨陵区'],
        '铜川市': ['耀州区', '王益区'],
        '榆林市': ['府谷县'],
        '汉中市': ['镇巴县'],
        '安康市': ['紫阳县'],
        '商洛市': ['洛南县'],
    }

    # 区县→市反向映射
    DISTRICT_TO_CITY: Dict[str, str] = {
        '鄠邑区': '西安市', '长安区': '西安市', '蓝田县': '西安市',
        '高陵区': '西安市', '新城区': '西安市', '雁塔区': '西安市',
        '莲湖区': '西安市', '碑林区': '西安市',
        '安塞区': '延安市', '富县': '延安市',
        '合阳县': '渭南市', '华阴市': '渭南市', '韩城市': '渭南市',
        '临渭区': '渭南市', '富平县': '渭南市',
        '陈仓区': '宝鸡市', '凤翔区': '宝鸡市', '陇县': '宝鸡市',
        '金台区': '宝鸡市',
        '秦都区': '咸阳市', '杨陵区': '咸阳市',
        '耀州区': '铜川市', '王益区': '铜川市',
        '府谷县': '榆林市',
        '镇巴县': '汉中市',
        '紫阳县': '安康市',
        '洛南县': '商洛市',
    }

    def create_region_part_of_relation(self, child_region: str,
                                       parent_region: str) -> bool:
        """创建 Region -[PART_OF]-> Region 层级关系"""
        return self._merge_relation('Region', child_region,
                                    'PART_OF', 'Region', parent_region)

    def expand_region_tree(self) -> Dict[str, int]:
        """展开陕西非遗 Region 层级树（省→市→区县三级）

        创建所有层级 Region 节点和 PART_OF 关系。
        返回 {region_nodes: int, part_of_relations: int}。
        """
        region_count = 0
        relation_count = 0

        # 省级
        if self.create_region_node('陕西省', province='陕西省', level='省',
                                   latitude=34.2658, longitude=108.9541):
            region_count += 1

        for city, districts in self.REGION_TREE.items():
            if self.create_region_node(city, province='陕西省', level='地级市'):
                region_count += 1
            if self.create_region_part_of_relation(city, '陕西省'):
                relation_count += 1

            for district in districts:
                if self.create_region_node(district, province='陕西省',
                                           city=city, level='区县'):
                    region_count += 1
                if self.create_region_part_of_relation(district, city):
                    relation_count += 1

        logger.info(
            f"Region 层级树展开完成: "
            f"{region_count} 个节点, {relation_count} 条 PART_OF 关系"
        )
        return {'region_nodes': region_count, 'part_of_relations': relation_count}

    # ──────────────────────────────
    # Heritage 关系构建
    # ──────────────────────────────

    def build_heritage_relations(self, heritage_id: int, category: str,
                                 region: str, level: str, batch: str,
                                 latitude: float = None, longitude: float = None,
                                 name: str = '') -> bool:
        """构建单个非遗项目的全部基础关系 (BELONGS_TO / LOCATED_AT / HAS_LEVEL / IN_BATCH / AT_LOCATION)"""
        results = []

        if category:
            self.create_category_node(category, '')
            results.append(self._merge_relation(
                'Heritage', heritage_id, 'BELONGS_TO', 'Category', category))

        if region:
            self.create_region_node(region, '陕西', '')
            results.append(self._merge_relation(
                'Heritage', heritage_id, 'LOCATED_AT', 'Region', region))

        if level:
            self.create_level_node(level, 0)
            results.append(self._merge_relation(
                'Heritage', heritage_id, 'HAS_LEVEL', 'Level', level))

        if batch:
            self.create_batch_node(batch)
            results.append(self._merge_relation(
                'Heritage', heritage_id, 'IN_BATCH', 'Batch', batch))

        if latitude and longitude and name:
            self.create_location_node(name, latitude, longitude, 'heritage', region or '')
            results.append(self._merge_relation(
                'Heritage', heritage_id, 'AT_LOCATION', 'Location', name))

        return all(results) if results else True

    def refine_heritage_region(self, heritage_id: int, text: str) -> bool:
        """将 Heritage 关联到最细粒度区县 Region

        从 description/history 文本中匹配区县名，
        若匹配到则同时创建 Heritage → District Region 的 LOCATED_AT 关系。
        """
        if not text:
            return False
        matched = False
        for district, city in self.DISTRICT_TO_CITY.items():
            if district in text:
                self.create_region_node(district, province='陕西省',
                                        city=city, level='区县')
                self._merge_relation('Heritage', heritage_id,
                                     'LOCATED_AT', 'Region', district)
                matched = True
        return matched

    # ──────────────────────────────
    # NEAR 邻近关系
    # ──────────────────────────────

    def build_near_relations(self, max_distance_km: float = 100) -> int:
        """全量重建 Heritage 间的 NEAR 关系

        先清除旧 NEAR 边（仅 Heritage-Heritage），再基于当前坐标重新计算。
        """
        if not self.driver:
            return 0

        try:
            # 清除旧 NEAR
            with self.driver.session() as session:
                result = session.run(
                    "MATCH (:Heritage)-[r:NEAR]->(:Heritage) DELETE r")
                deleted = result.consume().counters.relationships_deleted
                if deleted:
                    logger.info(f"清除了 {deleted} 条旧 Heritage NEAR 关系")

            heritages = self.get_all_heritages_with_coordinates()
            if not heritages:
                return 0

            relation_count = 0
            for i, h1 in enumerate(heritages):
                for h2 in heritages[i + 1:]:
                    distance = self.calculate_distance(
                        h1['latitude'], h1['longitude'],
                        h2['latitude'], h2['longitude'])
                    if distance <= max_distance_km:
                        self.create_near_relation(
                            h1['id'], h2['id'], distance)
                        relation_count += 1

            logger.info(f"创建了 {relation_count} 个邻近关系")
            return relation_count

        except Exception as e:
            logger.error(f"构建邻近关系失败: {e}")
            return 0

    def create_near_relation(self, heritage_id1: int, heritage_id2: int,
                             distance_km: float) -> bool:
        """创建两个 Heritage 之间的 NEAR 关系"""
        return self._merge_relation(
            'Heritage', heritage_id1, 'NEAR', 'Heritage', heritage_id2,
            {'distance_km': round(distance_km, 2)})
