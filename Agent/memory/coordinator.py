# -*- coding: utf-8 -*-
"""
MemoryCoordinator（第一版）
统一记忆写入入口，提供 L1 滚动窗口与摘要维护能力。
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from Agent.memory.session_provider import get_session_pool
from Agent.memory.redis_session import RedisSessionPool
from Agent.services.conversation_service import get_conversation_service
from Agent.config.settings import Config
from Agent.config.memory_budget import memory_budget
from Agent.memory.sifter import get_sifter

try:
    from Agent.memory.l2_graph_store import get_l2_graph_store
except Exception:
    get_l2_graph_store = None

try:
    from Agent.memory.l3_sqlite_ledger import get_l3_sqlite_ledger
except Exception:
    get_l3_sqlite_ledger = None

try:
    from Agent.memory.vector_store import get_vector_store
except Exception:
    get_vector_store = None


class MemoryCoordinator:
    """
    第一版能力：
    1) 统一 append_turn 写入
    2) 维护 Redis L1 recent_turns（可配置轮数）
    3) 维护 Redis L1 session_summary（增量摘要）
    """

    def __init__(self):
        self.session_pool = get_session_pool()
        self.conversation_service = get_conversation_service()
        self._redis = self.session_pool.get_redis_client()
        self.l2_store = get_l2_graph_store() if get_l2_graph_store else None
        self.l3_ledger = get_l3_sqlite_ledger() if get_l3_sqlite_ledger else None
        self.vector_store = get_vector_store() if get_vector_store else None
        self.sifter = get_sifter()
        self.l2_enabled = memory_budget.l2_memory_enabled and self.l2_store is not None
        self.l3_enabled = memory_budget.l3_ledger_enabled and self.l3_ledger is not None
        self.rag_enabled = self.vector_store is not None
        self.sifter_enabled = memory_budget.sifter_enabled
        self._stats = {
            "turns_written": 0,
            "turn_write_failures": 0,
            "summary_rollups": 0,
            "l1_write_failures": 0,
            "l3_writes": 0,
            "l3_write_failures": 0,
            "l2_upserts": 0,
            "l2_upsert_failures": 0,
            "rag_index_writes": 0,
            "rag_index_write_failures": 0,
        }

    def _recent_key(self, session_id: str) -> str:
        return f"agent:memory:{session_id}:recent_turns"

    def _summary_key(self, session_id: str) -> str:
        return f"agent:memory:{session_id}:session_summary"

    def _summary_meta_key(self, session_id: str) -> str:
        return f"agent:memory:{session_id}:summary_meta"

    async def append_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        message_type: str = "text",
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not session_id or not content:
            return False

        try:
            self.session_pool.add_conversation(session_id, role, content, user_id=user_id)
        except Exception as e:
            logger.warning(f"session_pool.add_conversation 失败: {e}")
            self._stats["turn_write_failures"] += 1

        self._update_l1_memory(session_id, role, content)
        await self._post_process_turn(session_id=session_id, user_id=user_id, username=username, role=role, content=content)
        self._stats["turns_written"] += 1
        return True

    def _update_l1_memory(self, session_id: str, role: str, content: str):
        """
        L1 协议：
        - recent_turns 保留最近10条
        - 超出后弹出最旧2条，生成增量摘要写入 session_summary
        """
        if self._redis is None:
            return

        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        recent_key = self._recent_key(session_id)
        summary_key = self._summary_key(session_id)
        summary_meta_key = self._summary_meta_key(session_id)

        try:
            self._redis.rpush(recent_key, json.dumps(turn, ensure_ascii=False))
            ttl = Config.REDIS_SESSION_TTL
            if ttl:
                self._redis.expire(recent_key, ttl)

            size = self._redis.llen(recent_key)
            if size > memory_budget.l1_recent_limit:
                popped_raw = self._redis.lrange(recent_key, 0, memory_budget.l1_rolling_drop_count - 1)
                if popped_raw:
                    self._redis.ltrim(recent_key, memory_budget.l1_rolling_drop_count, -1)
                    popped_turns = []
                    for item in popped_raw:
                        try:
                            popped_turns.append(json.loads(item))
                        except Exception:
                            continue
                    if popped_turns:
                        inc_summary = self._build_incremental_summary(popped_turns)
                        existing = self._redis.get(summary_key) or ""
                        merged = self._merge_summary(existing, inc_summary)
                        self._redis.set(summary_key, merged)
                        self._stats["summary_rollups"] += 1
                        self._redis.hset(
                            summary_meta_key,
                            mapping={
                                "updated_at": datetime.now().isoformat(),
                                "recent_size": self._redis.llen(recent_key),
                            },
                        )
            logger.debug(f"L1记忆更新完成: session={session_id}")
        except Exception as e:
            logger.warning(f"更新L1记忆失败: {e}")
            self._stats["l1_write_failures"] += 1

    def _build_incremental_summary(self, turns: List[Dict[str, Any]]) -> str:
        """
        第一版摘要策略：规则压缩，确保简短稳定。
        后续可替换为异步LLM摘要。
        """
        if not turns:
            return ""
        parts = []
        for turn in turns:
            role = "用户" if turn.get("role") == "user" else "助手"
            text = (turn.get("content") or "").replace("\n", " ").strip()
            if len(text) > memory_budget.l1_turn_summary_max_chars:
                text = text[:memory_budget.l1_turn_summary_max_chars] + "..."
            if text:
                parts.append(f"{role}:{text}")
        summary = "；".join(parts)
        return summary[:50]

    def _merge_summary(self, existing: str, incoming: str) -> str:
        if not existing:
            return incoming
        if not incoming:
            return existing
        merged = f"{existing} | {incoming}"
        return merged[-memory_budget.l1_summary_max_chars:]

    async def _post_process_turn(self, session_id: str, user_id: Optional[str], username: Optional[str], role: str, content: str):
        """
        写后处理：
        1) L3 账本追加
        2) RAG 向量索引（对话写入 ChromaDB）
        3) L2 偏好沉淀（仅对 user 消息做 Sifter 提取）
        4) L2 用户活跃时间更新（每次对话都更新）
        """
        if self.l2_enabled and user_id:
            self.l2_store.touch_user_active(user_id, username=username)

        if self.l3_enabled:
            ok = self.l3_ledger.append_event(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                meta={},
            )
            if ok:
                self._stats["l3_writes"] += 1
            else:
                self._stats["l3_write_failures"] += 1
                logger.warning(f"L3审计写入失败: session={session_id}")

        if self.rag_enabled and user_id and content:
            try:
                self.vector_store.add_conversation(
                    session_id=session_id,
                    user_id=user_id,
                    role=role,
                    content=content,
                )
                self._stats["rag_index_writes"] += 1
            except Exception as e:
                self._stats["rag_index_write_failures"] += 1
                logger.debug(f"RAG向量索引写入失败: {e}")

        if self.l2_enabled and self.sifter_enabled and role == "user" and user_id:
            should = await self.sifter.should_persist_async(role, content)
            if should:
                prefs = await self.sifter.extract_preferences_async(content)
                if prefs:
                    ok = self.l2_store.upsert_user_preferences(user_id=user_id, preferences=prefs, username=username)
                    if ok:
                        self._stats["l2_upserts"] += 1
                        logger.debug(f"L2偏好写入成功: user={user_id}, prefs={prefs}")
                    else:
                        self._stats["l2_upsert_failures"] += 1
                        logger.warning(f"L2偏好写入失败: user={user_id}")

                    for pref in prefs:
                        if pref.get("type") == "heritage_interest":
                            try:
                                await self._link_heritage_interest(user_id, pref)
                            except Exception as e:
                                logger.debug(f"非遗兴趣关联失败（不影响主流程）: {e}")

    async def _link_heritage_interest(self, user_id: str, pref: Dict[str, Any]):
        if not self.l2_enabled:
            return
        value = pref.get("value", {})
        heritage_id = None
        heritage_name = None
        if isinstance(value, dict):
            heritage_id = value.get("heritage_id")
            heritage_name = value.get("heritage_name")
        elif isinstance(value, str):
            heritage_name = value

        if heritage_id:
            try:
                self.l2_store.link_user_heritage(
                    user_id, int(heritage_id),
                    rel_type="PREFERS",
                    confidence=float(pref.get("confidence", 0.6)),
                    source="dialogue",
                )
                logger.debug(f"对话意图→非遗关联: user={user_id}, heritage_id={heritage_id}")
            except Exception as e:
                logger.debug(f"对话意图→非遗关联失败: {e}")
        elif heritage_name:
            resolved_id = self._resolve_heritage_by_name(heritage_name)
            if resolved_id:
                try:
                    self.l2_store.link_user_heritage(
                        user_id, resolved_id,
                        rel_type="PREFERS",
                        confidence=float(pref.get("confidence", 0.5)),
                        source="dialogue",
                    )
                    logger.debug(f"对话意图→非遗关联(名称解析): user={user_id}, name={heritage_name}→id={resolved_id}")
                except Exception as e:
                    logger.debug(f"对话意图→非遗关联(名称解析)失败: {e}")

    def _resolve_heritage_by_name(self, name: str) -> Optional[int]:
        try:
            from Agent.memory.heritage_query_service import get_heritage_query_service
            service = get_heritage_query_service()
            results = service.hybrid_query(name, top_k=1)
            if results and results[0].get('id'):
                return int(results[0]['id'])
        except Exception as e:
            logger.debug(f"解析非遗名称失败: {e}")
        return None

    def get_l1_snapshot(self, session_id: str) -> Dict[str, Any]:
        """
        调试与后续上下文组装使用。
        """
        if self._redis is None:
            return {"recent_turns": [], "summary": ""}
        recent_raw = self._redis.lrange(self._recent_key(session_id), 0, -1)
        recent_turns = []
        for item in recent_raw:
            try:
                recent_turns.append(json.loads(item))
            except Exception:
                continue
        summary = self._redis.get(self._summary_key(session_id)) or ""
        return {
            "recent_turns": recent_turns,
            "summary": summary,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "l2_enabled": self.l2_enabled,
            "l3_enabled": self.l3_enabled,
            "sifter_enabled": self.sifter_enabled,
        }


_memory_coordinator_instance: Optional[MemoryCoordinator] = None


def get_memory_coordinator() -> MemoryCoordinator:
    global _memory_coordinator_instance
    if _memory_coordinator_instance is None:
        _memory_coordinator_instance = MemoryCoordinator()
    return _memory_coordinator_instance
