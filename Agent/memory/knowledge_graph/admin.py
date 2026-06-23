# -*- coding: utf-8 -*-
"""
管理 Mixin — 知识图谱维护操作
负责节点删除、更新、统计与清空
"""

from typing import Dict, Any
from loguru import logger


class AdminMixin:
    """知识图谱管理操作"""

    driver: object = None

    # ──────────────────────────────
    # 删除
    # ──────────────────────────────

    def delete_heritage(self, heritage_id: int) -> bool:
        """删除非遗项目节点及其关联的所有关系"""
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

    # ──────────────────────────────
    # 更新
    # ──────────────────────────────

    def update_heritage(self, heritage_id: int, updates: Dict[str, Any]) -> bool:
        """更新非遗项目节点属性"""
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

    # ──────────────────────────────
    # 统计
    # ──────────────────────────────

    def get_stats(self) -> Dict[str, int]:
        """获取知识图谱统计信息（所有节点标签和关系类型数量）"""
        if not self.driver:
            return {}

        # 需统计的节点标签
        _STAT_LABELS = [
            'Heritage', 'Category', 'Region', 'Level', 'Batch',
            'Inheritor', 'Dynasty', 'Location',
        ]
        # 需统计的关系类型
        _STAT_RELATIONS = [
            'BELONGS_TO', 'LOCATED_AT', 'HAS_LEVEL', 'IN_BATCH',
            'HAS_INHERITOR', 'STUDIED_UNDER', 'ORIGINATED_IN',
            'PART_OF', 'NEAR', 'AT_LOCATION',
        ]

        try:
            with self.driver.session() as session:
                stats = {}

                for label in _STAT_LABELS:
                    result = session.run(
                        f"MATCH (n:{label}) RETURN count(n) as count")
                    record = result.single()
                    stats[f'{label.lower()}_count'] = record['count'] if record else 0

                for rel in _STAT_RELATIONS:
                    result = session.run(
                        f"MATCH ()-[r:{rel}]->() RETURN count(r) as count")
                    record = result.single()
                    stats[f'{rel.lower()}_count'] = record['count'] if record else 0

                stats['total_nodes'] = sum(
                    stats.get(f'{l.lower()}_count', 0) for l in _STAT_LABELS)
                stats['total_relations'] = sum(
                    stats.get(f'{r.lower()}_count', 0) for r in _STAT_RELATIONS)

                return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    # ──────────────────────────────
    # 清空
    # ──────────────────────────────

    def clear_all(self) -> bool:
        """清空知识图谱所有数据（危险操作）"""
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
