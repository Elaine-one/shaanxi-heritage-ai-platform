# -*- coding: utf-8 -*-
"""
L2 图记忆存储
负责长期结构化偏好与实体关系沉淀。

节点设计：
- User: {user_id, username, created_at, last_active}
- Preference: {user_id, type, value, confidence, source, updated_at, name}
- Heritage/Region/Category: 复用知识图谱已有节点

关系设计：
- (User)-[:HAS_PREFERENCE]->(Preference)
- (User)-[:PREFERS]->(Heritage)       对话意图沉淀
- (User)-[:PLANNED]->(Heritage)       规划选择沉淀
- (User)-[:EXPORTED]->(Heritage)      导出行为沉淀
- (User)-[:INTERESTED_IN]->(Region)
- (Preference)-[:TARGETS]->(Category) 偏好桥接
- (Preference)-[:TARGETS]->(Region)   偏好桥接

用户隔离保障：
- 所有查询以 user_id 为锚点，仅沿出边遍历
- 禁止从共享节点反向遍历到 User
- Preference 含 user_id 复合键，天然隔离
"""

import json
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger

from Agent.memory.knowledge_graph import get_knowledge_graph

_VALID_REL_TYPES = {"PREFERS", "PLANNED", "EXPORTED"}

_MERGE_USER_CYPHER = """
MERGE (u:User {user_id: $user_id})
ON CREATE SET u.created_at = $now
SET u.last_active = $now
SET u.username = CASE
    WHEN $username IS NOT NULL THEN $username
    ELSE CASE WHEN u.username IS NULL THEN 'unknown' ELSE u.username END
END
"""

_REL_SET_CLAUSES = {
    "PREFERS": (
        "r.confidence = CASE WHEN r.confidence IS NULL THEN $confidence "
        "ELSE CASE WHEN $confidence > r.confidence THEN $confidence ELSE r.confidence END END, "
        "r.source = $source, r.updated_at = $now"
    ),
    "PLANNED": "r.source = $source, r.timestamp = $now, r.updated_at = $now",
    "EXPORTED": "r.source = $source, r.timestamp = $now, r.updated_at = $now",
}

_PREF_TYPE_LABELS = {
    "interest": "兴趣偏好",
    "region_interest": "地区偏好",
    "budget": "预算偏好",
    "pace": "节奏偏好",
    "group_size": "人数偏好",
    "travel_mode": "出行方式偏好",
    "heritage_interest": "非遗兴趣",
    "food_interest": "美食兴趣",
    "accommodation_preference": "住宿偏好",
}


def _require_user_id(default=None):
    def decorator(func):
        def wrapper(self, user_id: str, *args, **kwargs):
            if not user_id:
                logger.warning(f"L2查询缺少user_id锚点，拒绝执行: {func.__name__}")
                return default
            return func(self, user_id, *args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def _neo4j_safe(default=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"L2 {func.__name__}失败: {e}")
                return default
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def _parse_json_value(val):
    try:
        parsed = json.loads(val)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return val


class L2GraphStore:

    def __init__(self):
        self.kg = get_knowledge_graph()
        self._categories_cache: List[str] = []
        self._categories_cache_time: float = 0

    def is_available(self) -> bool:
        return bool(self.kg and self.kg.is_connected())

    # ─── Core helpers ───────────────────────────────────────────────

    def _ensure_user_node(self, session, user_id: str, username: str = None, now_iso: str = None):
        session.run(
            _MERGE_USER_CYPHER,
            user_id=user_id,
            now=now_iso or datetime.now().isoformat(),
            username=username,
        )

    def _query_heritages_by_rel(self, session, user_id: str, rel_type: str,
                                 return_props: str = "h.id AS id, h.name AS name, h.category AS category, h.region AS region",
                                 order_by: str = "h.name") -> List[Dict]:
        result = session.run(
            f"MATCH (u:User {{user_id: $user_id}})-[:{rel_type}]->(h:Heritage) "
            f"RETURN {return_props} ORDER BY {order_by}",
            user_id=user_id,
        )
        return [dict(r) for r in result]

    # ─── User activity ──────────────────────────────────────────────

    @_neo4j_safe(default=None)
    def touch_user_active(self, user_id: str, username: str = None):
        if not user_id or not self.is_available():
            return
        now_iso = datetime.now().isoformat()
        with self.kg.driver.session() as session:
            self._ensure_user_node(session, user_id, username, now_iso)

    # ─── Preference management ──────────────────────────────────────

    @_neo4j_safe(default=False)
    def upsert_user_preferences(self, user_id: str, preferences: List[Dict[str, Any]],
                                 username: str = None) -> bool:
        if not user_id or not preferences:
            return False
        if not self.is_available():
            return False

        now_iso = datetime.now().isoformat()
        with self.kg.driver.session() as session:
            self._ensure_user_node(session, user_id, username, now_iso)

            for pref in preferences:
                p_type = pref.get("type", "unknown")
                raw_value = pref.get("value", "")
                p_value = json.dumps(raw_value, ensure_ascii=False) if isinstance(raw_value, dict) else str(raw_value)[:200]
                p_confidence = float(pref.get("confidence", 0.5))
                p_source = pref.get("source", "sifter")
                p_name = self._generate_preference_name(p_type, raw_value)

                session.run(
                    """
                    MATCH (u:User {user_id: $user_id})
                    MERGE (p:Preference {user_id: $user_id, type: $p_type})
                    SET p.value = $p_value,
                        p.confidence = CASE
                            WHEN p.confidence IS NULL THEN $p_confidence
                            ELSE CASE WHEN $p_confidence > p.confidence THEN $p_confidence ELSE p.confidence END
                        END,
                        p.source = $p_source,
                        p.updated_at = $now,
                        p.name = $p_name
                    MERGE (u)-[r:HAS_PREFERENCE]->(p)
                    SET r.updated_at = $now
                    """,
                    user_id=user_id, p_type=p_type, p_value=p_value,
                    p_confidence=p_confidence, p_source=p_source,
                    now=now_iso, p_name=p_name,
                )

                self._upsert_region_interests(session, user_id, p_type, raw_value, p_confidence, now_iso)
                self._link_preference_targets(session, user_id, p_type, raw_value, p_confidence)

        logger.info(f"L2 偏好写入成功: user={user_id}, count={len(preferences)}")
        return True

    def _generate_preference_name(self, p_type: str, raw_value: Any) -> str:
        label = _PREF_TYPE_LABELS.get(p_type, p_type)
        if isinstance(raw_value, dict):
            detail = raw_value.get("category") or raw_value.get("detail") or raw_value.get("regions", [""])[0]
            if isinstance(detail, list):
                detail = detail[0] if detail else ""
            if detail and len(detail) > 20:
                detail = detail[:18] + ".."
            return f"{label}: {detail}" if detail else label
        elif isinstance(raw_value, str) and raw_value:
            return f"{label}: {raw_value[:20]}" if len(raw_value) > 20 else f"{label}: {raw_value}"
        return label

    def _upsert_region_interests(self, session, user_id: str, p_type: str,
                                   raw_value: Any, confidence: float, now_iso: str):
        if p_type != "region_interest":
            return

        region_names = []
        if isinstance(raw_value, dict) and "regions" in raw_value:
            region_names = raw_value["regions"]
        elif isinstance(raw_value, str):
            region_names = [raw_value]

        valid_regions = self.get_valid_regions()
        for name in region_names:
            if not name or not isinstance(name, str):
                continue
            matched_name = self._match_region_name(name, valid_regions)
            if not matched_name:
                logger.debug(f"跳过无效Region(不在知识图谱中): {name}")
                continue
            try:
                session.run(
                    """
                    MATCH (u:User {user_id: $user_id})
                    MERGE (r:Region {name: $region_name})
                    MERGE (u)-[rel:INTERESTED_IN]->(r)
                    SET rel.confidence = $conf, rel.updated_at = $now
                    """,
                    user_id=user_id, region_name=matched_name,
                    conf=confidence, now=now_iso,
                )
            except Exception as e:
                logger.debug(f"地区兴趣写入失败(region={name}): {e}")

    def _match_region_name(self, input_name: str, valid_regions: set) -> Optional[str]:
        if input_name in valid_regions:
            return input_name
        for vr in valid_regions:
            if vr.startswith(input_name) or input_name.startswith(vr):
                return vr
        for vr in valid_regions:
            common = sum(1 for a, b in zip(input_name, vr) if a == b)
            min_len = min(len(input_name), len(vr))
            if min_len > 0 and common / min_len > 0.7:
                return vr
        return None

    def _link_preference_targets(self, session, user_id: str, p_type: str,
                                   raw_value: Any, confidence: float):
        if p_type == "interest" and isinstance(raw_value, dict):
            category_name = raw_value.get("category")
            if category_name:
                try:
                    session.run(
                        """
                        MATCH (u:User {user_id: $user_id})-[:HAS_PREFERENCE]->(p:Preference {type: 'interest'})
                        MERGE (c:Category {name: $category_name})
                        MERGE (p)-[t:TARGETS]->(c)
                        SET t.confidence = $confidence
                        """,
                        user_id=user_id, category_name=category_name, confidence=confidence,
                    )
                except Exception as e:
                    logger.debug(f"偏好桥接Category失败: {e}")
        elif p_type == "region_interest" and isinstance(raw_value, dict):
            for region_name in raw_value.get("regions", []):
                if region_name and isinstance(region_name, str):
                    try:
                        session.run(
                            """
                            MATCH (u:User {user_id: $user_id})-[:HAS_PREFERENCE]->(p:Preference {type: 'region_interest'})
                            MERGE (r:Region {name: $region_name})
                            MERGE (p)-[t:TARGETS]->(r)
                            SET t.confidence = $confidence
                            """,
                            user_id=user_id, region_name=region_name, confidence=confidence,
                        )
                    except Exception as e:
                        logger.debug(f"偏好桥接Region失败(region={region_name}): {e}")

    # ─── Heritage relation management ───────────────────────────────

    @_require_user_id(default=False)
    @_neo4j_safe(default=False)
    def link_user_heritage(self, user_id: str, heritage_id: int,
                           rel_type: str = "PREFERS", confidence: float = 0.6,
                           source: str = "dialogue", extra_props: dict = None) -> bool:
        if not self.is_available():
            return False
        if rel_type not in _VALID_REL_TYPES:
            logger.warning(f"非法关系类型: {rel_type}，允许值: {_VALID_REL_TYPES}")
            return False
        if not isinstance(heritage_id, int) or heritage_id <= 0:
            logger.warning(f"非法heritage_id: {heritage_id}")
            return False
        return self._create_heritage_rels(
            user_id=user_id, heritage_ids=[heritage_id],
            rel_type=rel_type, confidence=confidence,
            source=source, extra_props=extra_props,
        )

    @_require_user_id(default=False)
    @_neo4j_safe(default=False)
    def batch_link_heritages(self, user_id: str, heritage_ids: List[int],
                              rel_type: str = "PLANNED", source: str = "plan",
                              extra_props: dict = None) -> bool:
        if not self.is_available():
            return False
        if rel_type not in _VALID_REL_TYPES:
            logger.warning(f"非法关系类型: {rel_type}，允许值: {_VALID_REL_TYPES}")
            return False
        if not heritage_ids:
            return True
        return self._create_heritage_rels(
            user_id=user_id, heritage_ids=heritage_ids,
            rel_type=rel_type, confidence=0.6,
            source=source, extra_props=extra_props,
        )

    def _create_heritage_rels(self, user_id: str, heritage_ids: List[int],
                                rel_type: str, confidence: float,
                                source: str, extra_props: dict = None) -> bool:
        now_iso = datetime.now().isoformat()
        props = extra_props or {}
        heritage_data = [{"id": int(hid)} for hid in heritage_ids if isinstance(hid, int) and hid > 0]
        if not heritage_data:
            return False

        set_clause = _REL_SET_CLAUSES[rel_type]
        cypher = (
            f"UNWIND $heritage_data AS hd "
            f"MATCH (u:User {{user_id: $user_id}}) "
            f"MATCH (h:Heritage {{id: hd.id}}) "
            f"MERGE (u)-[r:{rel_type}]->(h) "
            f"SET {set_clause} "
            f"SET r += $extra_props"
        )

        with self.kg.driver.session() as session:
            session.run(
                cypher, user_id=user_id, heritage_data=heritage_data,
                confidence=confidence, source=source, now=now_iso, extra_props=props,
            )

        logger.info(f"L2 关联成功: user={user_id}, rel={rel_type}, count={len(heritage_data)}")
        return True

    # ─── Query methods ──────────────────────────────────────────────

    @_require_user_id(default={})
    @_neo4j_safe(default={})
    def fetch_user_memory(self, user_id: str) -> Dict[str, Any]:
        if not self.is_available():
            return {}

        with self.kg.driver.session() as session:
            pref_result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[:HAS_PREFERENCE]->(p:Preference)
                RETURN p.type AS type, p.value AS value, p.confidence AS confidence
                ORDER BY p.confidence DESC
                """,
                user_id=user_id,
            )
            preferences = [
                {"type": r["type"], "value": _parse_json_value(r["value"]), "confidence": r["confidence"]}
                for r in pref_result
            ]

            region_result = session.run(
                "MATCH (u:User {user_id: $user_id})-[:INTERESTED_IN]->(r:Region) "
                "RETURN r.name AS region_name ORDER BY r.name",
                user_id=user_id,
            )
            interested_regions = [r["region_name"] for r in region_result]

            preferred = self._query_heritages_by_rel(session, user_id, "PREFERS")
            planned = self._query_heritages_by_rel(session, user_id, "PLANNED")
            exported = self._query_heritages_by_rel(session, user_id, "EXPORTED")

        return {
            "user_id": user_id,
            "preferences": preferences,
            "interested_regions": interested_regions,
            "preferred_heritages": preferred,
            "planned_heritages": planned,
            "exported_heritages": exported,
        }

    @_require_user_id(default={})
    @_neo4j_safe(default={})
    def fetch_user_heritage_graph(self, user_id: str) -> Dict[str, Any]:
        if not self.is_available():
            return {}

        with self.kg.driver.session() as session:
            prefers_result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[r:PREFERS]->(h:Heritage)
                RETURN h.id AS id, h.name AS name, h.category AS category,
                       h.region AS region, r.confidence AS confidence, r.source AS source
                ORDER BY r.confidence DESC
                """,
                user_id=user_id,
            )
            preferred = [dict(r) for r in prefers_result]

            planned_result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[r:PLANNED]->(h:Heritage)
                RETURN h.id AS id, h.name AS name, h.category AS category,
                       h.region AS region, r.plan_id AS plan_id, r.timestamp AS timestamp
                ORDER BY r.timestamp DESC
                """,
                user_id=user_id,
            )
            planned = [dict(r) for r in planned_result]

            exported_result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[r:EXPORTED]->(h:Heritage)
                RETURN h.id AS id, h.name AS name, h.category AS category,
                       h.region AS region, r.timestamp AS timestamp
                ORDER BY r.timestamp DESC
                """,
                user_id=user_id,
            )
            exported = [dict(r) for r in exported_result]

            targets_result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[:HAS_PREFERENCE]->(p:Preference)-[t:TARGETS]->(target)
                RETURN p.type AS pref_type, labels(target)[0] AS target_label,
                       target.name AS target_name, t.confidence AS confidence
                """,
                user_id=user_id,
            )
            preference_targets = [dict(r) for r in targets_result]

        return {
            "user_id": user_id,
            "preferred": preferred,
            "planned": planned,
            "exported": exported,
            "preference_targets": preference_targets,
        }

    # ─── Cleanup methods ────────────────────────────────────────────

    @_require_user_id(default={})
    @_neo4j_safe(default={})
    def cleanup_stale_user_relations(self, user_id: str, max_age_days: int = 30) -> Dict[str, int]:
        if not self.is_available():
            return {}

        cutoff = datetime.now().isoformat()
        removed = {"planned": 0, "exported": 0, "preferences": 0, "orphan_preferences": 0}
        with self.kg.driver.session() as session:
            for rel_type in ["PLANNED", "EXPORTED"]:
                r = session.run(
                    f"MATCH (u:User {{user_id: $user_id}})-[r:{rel_type}]->(h:Heritage) "
                    f"WHERE r.updated_at < $cutoff OR r.timestamp < $cutoff "
                    f"DELETE r RETURN count(r) AS cnt",
                    user_id=user_id, cutoff=cutoff,
                )
                record = r.single()
                removed[rel_type.lower()] = record["cnt"] if record else 0

            r = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[r:HAS_PREFERENCE]->(p:Preference)
                WHERE p.updated_at < $cutoff
                WITH p, r DELETE r RETURN count(p) AS cnt
                """,
                user_id=user_id, cutoff=cutoff,
            )
            record = r.single()
            removed["preferences"] = record["cnt"] if record else 0

            r = session.run(
                "MATCH (p:Preference) WHERE NOT (p)<-[:HAS_PREFERENCE]-(:User) "
                "OPTIONAL MATCH (p)-[t:TARGETS]->(target) DETACH DELETE p, t "
                "RETURN count(p) AS cnt"
            )
            record = r.single()
            removed["orphan_preferences"] = record["cnt"] if record else 0

        logger.info(f"L2 用户关系清理完成: user={user_id}, {removed}")
        return removed

    @_require_user_id(default=0)
    @_neo4j_safe(default=0)
    def cleanup_user_planned_relations(self, user_id: str) -> int:
        if not self.is_available():
            return 0

        with self.kg.driver.session() as session:
            r = session.run(
                "MATCH (u:User {user_id: $user_id})-[r:PLANNED]->(h:Heritage) "
                "DELETE r RETURN count(r) AS cnt",
                user_id=user_id,
            )
            record = r.single()
            cnt = record["cnt"] if record else 0

        logger.info(f"L2 清理用户PLANNED关系: user={user_id}, count={cnt}")
        return cnt

    # ─── Recommendation engine ──────────────────────────────────────

    @_require_user_id(default=[])
    @_neo4j_safe(default=[])
    def recommend_for_user(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.is_available():
            return []

        recommendations = []
        seen_ids = set()

        with self.kg.driver.session() as session:
            existing_ids = self._get_existing_heritage_ids(session, user_id)

            strategies = [
                self._recommend_by_preference,
                self._recommend_by_prefers_near,
                self._recommend_by_region,
                self._recommend_by_semantic,
                self._recommend_by_association,
            ]
            for strategy in strategies:
                if len(recommendations) >= limit:
                    break
                remaining = limit - len(recommendations)
                new_recs = strategy(session, user_id, existing_ids, seen_ids, remaining)
                for rec in new_recs:
                    if rec["id"] not in seen_ids:
                        seen_ids.add(rec["id"])
                        recommendations.append(rec)

        return recommendations

    def _get_existing_heritage_ids(self, session, user_id: str) -> set:
        result = session.run(
            "MATCH (u:User {user_id: $user_id})-[:PREFERS|PLANNED|EXPORTED]->(h:Heritage) "
            "RETURN collect(h.id) AS ids",
            user_id=user_id,
        )
        ids = set()
        for r in result:
            ids.update(r["ids"])
        return ids

    def _recommend_by_preference(self, session, user_id: str, existing_ids: set,
                                   seen_ids: set, remaining: int) -> List[Dict]:
        result = session.run(
            """
            MATCH (u:User {user_id: $user_id})-[:HAS_PREFERENCE]->(p:Preference)-[:TARGETS]->(c:Category)
                  <-[:BELONGS_TO]-(h:Heritage)
            WHERE NOT h.id IN $existing_ids
            RETURN DISTINCT h.id AS id, h.name AS name, h.category AS category,
                   h.region AS region, h.level AS level, max(p.confidence) AS pref_conf
            ORDER BY pref_conf DESC LIMIT $remaining
            """,
            user_id=user_id, existing_ids=list(existing_ids), remaining=remaining,
        )
        return [
            {"id": r["id"], "name": r["name"], "category": r["category"],
             "region": r["region"], "level": r["level"], "reason": "偏好匹配",
             "confidence": r["pref_conf"]}
            for r in result
        ]

    def _recommend_by_prefers_near(self, session, user_id: str, existing_ids: set,
                                     seen_ids: set, remaining: int) -> List[Dict]:
        result = session.run(
            """
            MATCH (u:User {user_id: $user_id})-[pref:PREFERS]->(h1:Heritage)
                  -[near:NEAR|RELATED_TO]->(h2:Heritage)
            WHERE NOT h2.id IN $existing_ids AND NOT h2.id IN $seen_ids
            RETURN DISTINCT h2.id AS id, h2.name AS name, h2.category AS category,
                   h2.region AS region, h2.level AS level,
                   pref.confidence AS confidence, near.distance_km AS distance
            ORDER BY pref.confidence DESC, near.distance_km ASC LIMIT $remaining
            """,
            user_id=user_id, existing_ids=list(existing_ids),
            seen_ids=list(seen_ids), remaining=remaining,
        )
        return [
            {"id": r["id"], "name": r["name"], "category": r["category"],
             "region": r["region"], "level": r["level"], "reason": "兴趣关联",
             "confidence": r.get("confidence", 0)}
            for r in result
        ]

    def _recommend_by_region(self, session, user_id: str, existing_ids: set,
                               seen_ids: set, remaining: int) -> List[Dict]:
        result = session.run(
            """
            MATCH (u:User {user_id: $user_id})-[:INTERESTED_IN]->(r:Region)
                  <-[:LOCATED_AT]-(h:Heritage)
            WHERE NOT h.id IN $existing_ids AND NOT h.id IN $seen_ids
            RETURN DISTINCT h.id AS id, h.name AS name, h.category AS category,
                   h.region AS region, h.level AS level, r.name AS matched_region
            ORDER BY r.name LIMIT $remaining
            """,
            user_id=user_id, existing_ids=list(existing_ids),
            seen_ids=list(seen_ids), remaining=remaining,
        )
        return [
            {"id": r["id"], "name": r["name"], "category": r["category"],
             "region": r["region"], "level": r["level"],
             "reason": f"地区偏好({r['matched_region']})"}
            for r in result
        ]

    def _recommend_by_semantic(self, session, user_id: str, existing_ids: set,
                                 seen_ids: set, remaining: int) -> List[Dict]:
        if remaining <= 0:
            return []

        prefs_result = session.run(
            """
            MATCH (u:User {user_id: $user_id})-[:HAS_PREFERENCE]->(p:Preference)
            WHERE p.type IN ['interest', 'heritage_interest']
            RETURN p.type AS p_type, p.value AS p_value, p.confidence AS p_conf
            ORDER BY p.confidence DESC LIMIT 3
            """,
            user_id=user_id,
        )
        prefs = [
            {"type": r["p_type"], "value": _parse_json_value(r["p_value"]), "confidence": r["p_conf"]}
            for r in prefs_result
        ]
        if not prefs:
            return []

        graph_categories = self.get_graph_categories()
        if not graph_categories:
            return []

        all_mapped = set()
        for pref in prefs:
            all_mapped.update(self._map_preference_to_categories(pref["value"], graph_categories))
        if not all_mapped:
            return []

        result = session.run(
            """
            MATCH (c:Category) WHERE c.name IN $cat_names
            MATCH (h:Heritage)-[:BELONGS_TO]->(c)
            WHERE NOT h.id IN $existing_ids AND NOT h.id IN $seen_ids
            RETURN DISTINCT h.id AS id, h.name AS name, h.category AS category,
                   h.region AS region, h.level AS level LIMIT $remaining
            """,
            cat_names=list(all_mapped), existing_ids=list(existing_ids),
            seen_ids=list(seen_ids), remaining=remaining,
        )
        return [
            {"id": r["id"], "name": r["name"], "category": r["category"],
             "region": r["region"], "level": r["level"], "reason": "语义推荐",
             "mapped_categories": list(all_mapped)}
            for r in result if r["id"] not in seen_ids
        ]

    def _recommend_by_association(self, session, user_id: str, existing_ids: set,
                                    seen_ids: set, remaining: int) -> List[Dict]:
        if remaining <= 0 or not existing_ids:
            return []

        result = session.run(
            """
            MATCH (u:User {user_id: $user_id})-[:PLANNED|EXPORTED]->(h1:Heritage)
                  -[:BELONGS_TO|LOCATED_AT]->(node)<-[:BELONGS_TO|LOCATED_AT]-(h2:Heritage)
            WHERE h1 <> h2 AND NOT h2.id IN $existing_ids AND NOT h2.id IN $seen_ids
            RETURN DISTINCT h2.id AS id, h2.name AS name, h2.category AS category,
                   h2.region AS region, h2.level AS level, count(node) AS overlap
            ORDER BY overlap DESC LIMIT $remaining
            """,
            user_id=user_id, existing_ids=list(existing_ids),
            seen_ids=list(seen_ids), remaining=remaining,
        )
        return [
            {"id": r["id"], "name": r["name"], "category": r["category"],
             "region": r["region"], "level": r["level"], "reason": "关联推荐",
             "overlap": r["overlap"]}
            for r in result
        ]

    # ─── Category / Region helpers ──────────────────────────────────

    @_neo4j_safe(default=set())
    def get_valid_regions(self) -> set:
        if not self.is_available():
            return set()
        with self.kg.driver.session() as session:
            result = session.run(
                "MATCH (r:Region)<-[:LOCATED_AT]-(:Heritage) RETURN DISTINCT r.name AS name"
            )
            return {r["name"] for r in result if r["name"]}

    @_neo4j_safe(default=[])
    def get_graph_categories(self) -> List[str]:
        now = time.time()
        if self._categories_cache and (now - self._categories_cache_time) < 3600:
            return self._categories_cache
        if not self.is_available():
            return self._categories_cache

        with self.kg.driver.session() as session:
            result = session.run("MATCH (c:Category) RETURN c.name AS name ORDER BY name")
            cats = [r["name"] for r in result if r["name"]]
            if cats:
                self._categories_cache = cats
                self._categories_cache_time = now
            return cats

    def _map_preference_to_categories(self, pref_value: Any, graph_categories: List[str]) -> List[str]:
        if not graph_categories:
            return []
        try:
            from Agent.models.llm_model import get_llm_model
            llm = get_llm_model()
            if not llm:
                return self._keyword_map_preference(pref_value, graph_categories)

            pref_desc = ""
            if isinstance(pref_value, dict):
                pref_desc = pref_value.get("category", "") or pref_value.get("detail", "") or str(pref_value)
            else:
                pref_desc = str(pref_value)
            if not pref_desc.strip():
                return []

            cat_list = "、".join(graph_categories)
            prompt = (
                f"用户表达了以下旅行偏好：\"{pref_desc}\"\n\n"
                f"以下是知识图谱中存在的非遗类别：{cat_list}\n\n"
                f"请从上述类别中，选出与用户偏好最相关的1-3个类别，按相关度排序。\n"
                f"只返回类别名称，用逗号分隔，不要包含其他文字。\n"
                f"如果没有匹配的类别，返回空。"
            )

            import asyncio
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                return self._keyword_map_preference(pref_value, graph_categories)

            response = asyncio.run(asyncio.wait_for(llm._call_model(prompt), timeout=10))
            if response and response.get("success"):
                raw = response.get("content", "").strip()
                if not raw or raw in ("空", "无", "没有"):
                    return []
                mapped = [c.strip() for c in raw.replace("，", ",").split(",") if c.strip()]
                valid = [c for c in mapped if c in graph_categories]
                if valid:
                    logger.info(f"LLM语义映射: '{pref_desc}' → {valid}")
                    return valid
                fuzzy = [gc for gc in graph_categories for m in mapped if m in gc or gc in m]
                if fuzzy:
                    return list(dict.fromkeys(fuzzy))[:3]
            return self._keyword_map_preference(pref_value, graph_categories)
        except Exception as e:
            logger.debug(f"LLM语义映射失败，降级关键词: {e}")
            return self._keyword_map_preference(pref_value, graph_categories)

    def _keyword_map_preference(self, pref_value: Any, graph_categories: List[str]) -> List[str]:
        pref_desc = ""
        if isinstance(pref_value, dict):
            pref_desc = (pref_value.get("category", "") or pref_value.get("detail", "") or str(pref_value))
        else:
            pref_desc = str(pref_value)
        if not pref_desc.strip():
            return []

        matched = [gc for gc in graph_categories if gc in pref_desc or pref_desc in gc]
        if matched:
            return matched[:3]

        char_matches = []
        for gc in graph_categories:
            overlap = sum(1 for ch in gc if ch in pref_desc)
            if overlap >= len(gc) * 0.4:
                char_matches.append(gc)
        return char_matches[:3]


_l2_graph_store_instance: Optional[L2GraphStore] = None


def get_l2_graph_store() -> L2GraphStore:
    global _l2_graph_store_instance
    if _l2_graph_store_instance is None:
        _l2_graph_store_instance = L2GraphStore()
    return _l2_graph_store_instance
