# -*- coding: utf-8 -*-
"""
知识图谱基础设施
- 节点/关系标签定义
- 通用节点创建 (_merge_node)
- 通用关系创建 (_merge_relation)
- 工具方法 (calculate_distance)
"""

import math
from typing import Dict, Any, Optional
from loguru import logger


class EntityMixin:
    """Mixin 基类，提供所有实体 Mixin 共享的基础能力"""

    # — 节点标签：新增实体时在此扩展 —
    NODE_LABELS: Dict[str, str] = {
        'Heritage': '非遗项目',
        'Category': '类别',
        'Region': '地区',
        'Level': '级别',
        'Batch': '批次',
        'Inheritor': '传承人',
        'Dynasty': '朝代',
        'Location': '位置',
    }

    # — 关系类型：新增关系时在此扩展 —
    RELATION_TYPES: Dict[str, str] = {
        'BELONGS_TO': '属于类别',
        'LOCATED_AT': '位于地区',
        'HAS_LEVEL': '具有级别',
        'IN_BATCH': '属于批次',
        'HAS_INHERITOR': '有传承人',
        'STUDIED_UNDER': '师承于',
        'ORIGINATED_IN': '起源于',
        'PART_OF': '隶属于',
        'RELATED_TO': '相关',
        'NEAR': '邻近',
        'AT_LOCATION': '位于',
    }

    # — 属性声明，避免 IDE 类型检查告警 —
    driver: Optional[object] = None

    # ──────────────────────────────
    # 通用写操作：节点
    # ──────────────────────────────

    def _merge_node(self, label: str, key: str, **properties) -> bool:
        """通过 MERGE 创建/更新节点，幂等安全

        Args:
            label: 节点标签 (如 'Heritage', 'Inheritor')
            key:  唯一键属性名 (如 'id', 'name')
            **properties: 其余属性
        """
        if not self.driver:
            return False

        # 构建 SET 子句，排除 key 本身，自动添加 updated_at
        set_items = [f'n.{k} = ${k}' for k in properties.keys() if k != key]
        set_items.append("n.updated_at = datetime()")

        set_clause = ', '.join(set_items)
        params = {key: properties[key], **{k: v for k, v in properties.items() if k != key}}

        try:
            with self.driver.session() as session:
                session.run(
                    f"MERGE (n:{label} {{{key}: ${key}}}) SET {set_clause}",
                    **params
                )
            return True
        except Exception as e:
            logger.error(f"MERGE {label} 节点失败 [{key}={properties.get(key)}]: {e}")
            return False

    # ──────────────────────────────
    # 通用写操作：关系
    # ──────────────────────────────

    def _merge_relation(self, from_label: str, from_id: Any,
                        relation_type: str, to_label: str, to_id: Any,
                        properties: Dict = None) -> bool:
        """通过 MERGE 创建关系，幂等安全

        Args:
            from_label:    起始节点标签
            from_id:       起始节点唯一键值
            relation_type: 关系类型
            to_label:      目标节点标签
            to_id:         目标节点唯一键值
            properties:    关系属性 (可选)
        """
        if not self.driver:
            return False

        # Heritage 使用 id 作为唯一键，其余使用 name
        from_key = 'id' if from_label == 'Heritage' else 'name'
        to_key = 'id' if to_label == 'Heritage' else 'name'

        try:
            with self.driver.session() as session:
                query = (
                    f"MATCH (a:{from_label} {{{from_key}: $from_id}}) "
                    f"MATCH (b:{to_label} {{{to_key}: $to_id}}) "
                    f"MERGE (a)-[r:{relation_type}]->(b)"
                )
                params = {'from_id': from_id, 'to_id': to_id}

                if properties:
                    set_items = [f'r.{k} = ${k}' for k in properties]
                    set_clause = ', '.join(set_items)
                    merge_pos = query.index('MERGE')
                    query = (
                        query[:merge_pos]
                        + f'MERGE (a)-[r:{relation_type}]->(b) SET {set_clause}'
                    )
                    params.update(properties)

                session.run(query, **params)
            return True
        except Exception as e:
            logger.error(
                f"创建关系失败 ({from_label})-[:{relation_type}]->({to_label}): {e}"
            )
            return False

    # ──────────────────────────────
    # 工具方法
    # ──────────────────────────────

    @staticmethod
    def calculate_distance(lat1: float, lon1: float,
                           lat2: float, lon2: float) -> float:
        """Haversine 公式计算两点球面距离（公里）"""
        if None in [lat1, lon1, lat2, lon2]:
            return float('inf')

        R = 6371  # 地球半径 (km)

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2
             + math.cos(lat1_rad) * math.cos(lat2_rad)
             * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c
