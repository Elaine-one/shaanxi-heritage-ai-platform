# -*- coding: utf-8 -*-
"""
偏好值向量化器

将 L2 Neo4j 中的结构化偏好转为向量表示，存入现有 ChromaDB 集合，
参与语义召回。复用 vector_store 的 embedding 缓存。
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from loguru import logger


# 偏好类型→自然语言模板
_PREF_TYPE_TEMPLATES = {
    "budget": "用户偏好预算范围为{value}",
    "travel_mode": "用户偏好出行方式为{value}",
    "region_interest": "用户对{value}地区感兴趣",
    "interest": "用户兴趣偏好: {value}",
    "heritage_interest": "用户对非遗项目{value}感兴趣",
    "group_preference": "用户出行团队偏好: {value}",
    "pace": "用户旅行节奏偏好: {value}",
    "food_interest": "用户美食偏好: {value}",
    "accommodation_preference": "用户住宿偏好: {value}",
}


@dataclass
class PreferenceVector:
    pref_id: str
    user_id: str
    pref_type: str
    pref_text: str          # 自然语言描述
    value: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5


class PreferenceVectorizer:
    """将结构化偏好转为向量，存入 ChromaDB user_preferences 集合"""

    def __init__(self):
        self._vector_store = None

    @property
    def vector_store(self):
        if self._vector_store is None:
            try:
                from Agent.memory.vector_store import get_vector_store
                self._vector_store = get_vector_store()
            except Exception:
                pass
        return self._vector_store

    def value_to_text(self, pref_type: str, value: Any) -> str:
        """将结构化值转为自然语言描述"""
        template = _PREF_TYPE_TEMPLATES.get(pref_type, "用户偏好: {value}")

        if isinstance(value, dict):
            if pref_type == "heritage_interest":
                name = value.get("heritage_name", "") or value.get("name", "")
                return template.format(value=name) if name else ""
            elif pref_type == "region_interest":
                regions = value.get("regions", [])
                region_str = "、".join(str(r) for r in regions[:3])
                return template.format(value=region_str) if region_str else ""
            elif pref_type == "budget":
                amount = value.get("amount", "")
                return f"用户预算约{amount}元" if amount else ""
            else:
                return template.format(value=str(value)[:300])
        elif isinstance(value, str) and value.strip():
            return template.format(value=value.strip()[:300])
        return ""

    def vectorize_preference(self, pref_id: str, user_id: str,
                              pref_type: str, value: Any,
                              confidence: float = 0.5) -> Optional[PreferenceVector]:
        """将单条偏好转为向量并存储（使用独立的 user_preferences 集合）"""
        pref_text = self.value_to_text(pref_type, value)
        if not pref_text or not self.vector_store:
            return None

        try:
            ok = self.vector_store.add_user_preference(
                pref_id=pref_id,
                user_id=user_id,
                pref_type=pref_type,
                content=pref_text,
                metadata={"confidence": confidence},
            )
            if not ok:
                return None

            return PreferenceVector(
                pref_id=pref_id,
                user_id=user_id,
                pref_type=pref_type,
                pref_text=pref_text,
                value=value if isinstance(value, dict) else {"raw": str(value)},
                confidence=confidence,
            )
        except Exception as e:
            logger.debug(f"偏好向量化失败(pref_id={pref_id}): {e}")
            return None

    def search_similar_preferences(
        self, user_id: str, query: str,
        top_k: int = 5,
        pref_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """语义搜索相似偏好（使用独立的 user_preferences 集合）"""
        if not self.vector_store:
            return []

        try:
            return self.vector_store.search_user_preferences(
                user_id=user_id,
                query=query,
                top_k=top_k,
                pref_types=pref_types,
            )
        except Exception as e:
            logger.debug(f"偏好向量搜索失败: {e}")
            return []

    def delete_preference_vector(self, pref_id: str):
        """删除偏好向量"""
        if not self.vector_store:
            return
        try:
            collection = self.vector_store.collections.get("user_preferences")
            if collection:
                collection.delete(ids=[f"pref_{pref_id}"])
        except Exception as e:
            logger.debug(f"删除偏好向量失败(pref_id={pref_id}): {e}")


_preference_vectorizer: Optional[PreferenceVectorizer] = None


def get_preference_vectorizer() -> PreferenceVectorizer:
    global _preference_vectorizer
    if _preference_vectorizer is None:
        _preference_vectorizer = PreferenceVectorizer()
    return _preference_vectorizer
