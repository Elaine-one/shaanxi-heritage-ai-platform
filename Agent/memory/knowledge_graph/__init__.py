# -*- coding: utf-8 -*-
"""
知识图谱模块
使用 Neo4j 存储非遗项目知识图谱，支持关联推理和精确查询

架构:
  _base.py     — EntityMixin: 通用 MERGE 写操作 + Haversine 距离计算
  heritage.py  — HeritageMixin: 核心实体 (Heritage/Category/Region/Level/Batch/Location)
  inheritor.py — InheritorMixin: 传承人正则解析 + 节点/关系/批量同步
  queries.py   — QueryMixin: 多维度查询 (ID/关联/维度/邻近)
  admin.py     — AdminMixin: 管理操作 (删除/更新/统计/清空)
"""

import os
import math
import time
import logging
from typing import Dict, Any, List, Optional
from loguru import logger

os.environ["NEO4J_PYTHON_DRIVER_LOG_LEVEL"] = "ERROR"

from neo4j import GraphDatabase

neo4j_logger = logging.getLogger("neo4j")
neo4j_logger.setLevel(logging.CRITICAL)

# is_connected() 缓存 TTL（秒）
_CONNECTED_CACHE_TTL_OK = 30
_CONNECTED_CACHE_TTL_FAIL = 5

from ._base import EntityMixin
from .heritage import HeritageMixin
from .inheritor import InheritorMixin
from .dynasty import DynastyMixin
from .queries import QueryMixin
from .admin import AdminMixin


class KnowledgeGraph(EntityMixin, HeritageMixin, InheritorMixin, DynastyMixin, QueryMixin, AdminMixin):
    """知识图谱管理器 — 由 6 个功能 Mixin 组装而成

    继承链:
      EntityMixin     → _merge_node / _merge_relation / calculate_distance
      HeritageMixin   → create_heritage_node / build_heritage_relations / build_near_relations / expand_region_tree
      InheritorMixin  → parse_inheritors_from_text / create_inheritor_node / sync_inheritors_from_heritage_list
      DynastyMixin    → match_dynasties_from_text / create_dynasty_node / sync_dynasties_from_heritage_list
      QueryMixin      → query_heritage_by_id(s) / query_by_(region|category|level) / query_nearby_*
      AdminMixin      → delete_heritage / update_heritage / get_stats / clear_all
    """

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        from Agent.config.settings import config
        self.uri = uri or config.NEO4J_URI
        self.user = user or config.NEO4J_USER
        self.password = password or config.NEO4J_PASSWORD

        self.driver = None
        self._last_conn_check: float = 0
        self._last_conn_ok: bool = False
        self._connect()

    # ──────────────────────────────
    # 连接生命周期
    # ──────────────────────────────

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

    def is_connected(self, force: bool = False) -> bool:
        """检查连接状态（带缓存，避免每次调用都发网络请求）

        Args:
            force: 跳过缓存，强制执行连接检查
        """
        if not self.driver:
            return False

        now = time.time()
        if not force and self._last_conn_check > 0:
            ttl = _CONNECTED_CACHE_TTL_OK if self._last_conn_ok else _CONNECTED_CACHE_TTL_FAIL
            if now - self._last_conn_check < ttl:
                return self._last_conn_ok

        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            self._last_conn_ok = True
        except Exception as e:
            self._last_conn_ok = False
            logger.error(f"Neo4j连接检测失败: {e}")
        self._last_conn_check = now
        return self._last_conn_ok


# ──────────────────────────────
# 单例
# ──────────────────────────────

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
