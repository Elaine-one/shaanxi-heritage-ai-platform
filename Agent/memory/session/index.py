# -*- coding: utf-8 -*-
"""
会话索引服务 — SessionIndex
提供跨会话语义检索能力，在 ChromaDB session_archives 集合中检索
"""

from typing import Any, Dict, List, Optional

from loguru import logger


class SessionIndex:
    """会话索引 — 跨会话检索"""

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

    def search_similar_sessions(
        self,
        query: str,
        user_id: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """在用户的历史归档会话中检索语义相似的会话"""
        if not self.vector_store or not query:
            return []

        try:
            collection = self.vector_store.collections.get("session_archives")
            if collection is None or collection.count() == 0:
                return []

            query_embedding = self.vector_store.embedding_model.encode_single(query)
            where_filter = {"user_id": user_id}

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, collection.count()),
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )

            formatted = []
            if results.get("documents") and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                    distance = results["distances"][0][i] if results.get("distances") else 0
                    formatted.append({
                        "session_id": meta.get("session_id", ""),
                        "topic": meta.get("topic", ""),
                        "timestamp": meta.get("timestamp", ""),
                        "document": doc,
                        "distance": distance,
                    })

            return formatted

        except Exception as e:
            logger.debug(f"跨会话检索失败: {e}")
            return []

    def get_recent_sessions(
        self, user_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """获取用户最近的归档会话摘要"""
        try:
            collection = self.vector_store.collections.get("session_archives")
            if collection is None or collection.count() == 0:
                return []

            results = collection.get(
                where={"user_id": user_id},
                include=["metadatas"],
            )

            if not results.get("metadatas"):
                return []

            sessions = []
            for meta in results["metadatas"]:
                sessions.append({
                    "session_id": meta.get("session_id", ""),
                    "topic": meta.get("topic", ""),
                    "timestamp": meta.get("timestamp", ""),
                })

            sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return sessions[:limit]

        except Exception as e:
            logger.debug(f"获取最近会话失败: {e}")
            return []


_session_index: Optional[SessionIndex] = None


def get_session_index() -> SessionIndex:
    """获取会话索引单例"""
    global _session_index
    if _session_index is None:
        _session_index = SessionIndex()
    return _session_index
