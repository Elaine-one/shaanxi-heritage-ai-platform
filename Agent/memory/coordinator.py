# -*- coding: utf-8 -*-
"""
MemoryCoordinator（第一版）
统一记忆写入入口，提供 L1 滚动窗口与摘要维护能力。
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from Agent.memory.session import get_session_pool, RedisSessionPool
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


L1_ATOMIC_APPEND = """
-- 阶段一: 原子推送 + 检测溢出
-- 溢出时返回全量列表供 Python 评分，未溢出返回空
local recent_key = KEYS[1]
local turn_json = ARGV[1]
local max_size = tonumber(ARGV[2])

redis.call('RPUSH', recent_key, turn_json)
local size = redis.call('LLEN', recent_key)
if size > max_size then
    return redis.call('LRANGE', recent_key, 0, -1)
end
return {}
"""

L1_ATOMIC_TRIM = """
-- 阶段二: 按 key 原子过滤淘汰项
-- KEYS[1] = recent_key
-- ARGV[1..N] = 要删除的 turn.key
-- 返回: 被淘汰的 turn JSON 数组
local recent_key = KEYS[1]
local remove = {}
for i = 1, #ARGV do
    remove[ARGV[i]] = true
end

local all = redis.call('LRANGE', recent_key, 0, -1)
local kept, popped = {}, {}

for i = 1, #all do
    local ok, turn = pcall(cjson.decode, all[i])
    if ok and turn['key'] and remove[turn['key']] then
        table.insert(popped, all[i])
    else
        table.insert(kept, all[i])
    end
end

redis.call('DEL', recent_key)
for i = 1, #kept do
    redis.call('RPUSH', recent_key, kept[i])
end
return popped
"""


class MemoryCoordinator:
    """
    第一版能力：
    1) 统一 append_turn 写入
    2) 维护 Redis L1 recent_turns（可配置轮数）
    3) 维护 Redis L1 session_summary（增量摘要）
    """

    def __init__(self):
        self.session_pool = get_session_pool()
        self._redis = self.session_pool.get_redis_client()
        self._l1_atomic_append = self._redis.register_script(L1_ATOMIC_APPEND) if self._redis else None
        self._l1_atomic_trim = self._redis.register_script(L1_ATOMIC_TRIM) if self._redis else None
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
            tool_interactions = extra_data.get('tool_interactions') if extra_data else None
            self.session_pool.add_conversation(session_id, role, content, user_id=user_id, tool_interactions=tool_interactions)
        except Exception as e:
            logger.warning(f"session_pool.add_conversation 失败: {e}")
            self._stats["turn_write_failures"] += 1

        await self._update_l1_memory(session_id, role, content)
        await self._post_process_turn(session_id=session_id, user_id=user_id, username=username, role=role, content=content)
        self._stats["turns_written"] += 1
        if user_id:
            self._maybe_trigger_merge(user_id)
        return True

    async def close_session(self, session_id: str, user_id: str) -> bool:
        """会话关闭入口 — 触发归档管线"""
        try:
            from Agent.memory.session import get_session_lifecycle
            lifecycle = get_session_lifecycle()
            return await lifecycle.on_session_close(session_id, user_id)
        except Exception as e:
            logger.warning(f"close_session 失败（不影响主流程）: {e}")
            return False

    def update_last_model_stats(self, model_name: str = None, tokens_in: int = None,
                                 tokens_out: int = None, latency_ms: int = None):
        """更新最近一次LLM调用的统计信息，供L3审计账本使用"""
        if model_name is not None:
            self._last_model_name = model_name
        if tokens_in is not None:
            self._last_tokens_in = tokens_in
        if tokens_out is not None:
            self._last_tokens_out = tokens_out
        if latency_ms is not None:
            self._last_latency_ms = latency_ms

    async def _update_l1_memory(self, session_id: str, role: str, content: str):
        """
        L1 两阶段智能淘汰：
        阶段一 (Lua 原子): RPUSH + 检测溢出 → 返回全量列表供评分
        阶段二 (Python): ImportanceScorer 评分 → 选最低分淘汰 → Lua 原子删除
        """
        if self._redis is None or self._l1_atomic_append is None or self._l1_atomic_trim is None:
            return

        import hashlib
        ts = datetime.now().isoformat()
        turn = {
            "key": hashlib.md5(f"{role}:{content[:100]}:{ts}".encode()).hexdigest()[:12],
            "role": role,
            "content": content,
            "timestamp": ts,
        }
        recent_key = self._recent_key(session_id)
        summary_key = self._summary_key(session_id)
        summary_meta_key = self._summary_meta_key(session_id)
        ttl = Config.REDIS_SESSION_TTL

        try:
            # 阶段一: 原子推送 + 检测溢出
            overflow_raw = self._l1_atomic_append(
                keys=[recent_key],
                args=[
                    json.dumps(turn, ensure_ascii=False),
                    memory_budget.l1_recent_limit,
                ],
            )
            if ttl:
                self._redis.expire(recent_key, ttl)

            if overflow_raw:
                # 阶段二: 评分淘汰
                scored = []
                for i, item in enumerate(overflow_raw):
                    try:
                        t = json.loads(item)
                        score = self._score_turn(t)
                        scored.append((t.get("key"), i, score))
                    except Exception:
                        scored.append((None, i, 0.0))

                scored.sort(key=lambda x: x[2])  # 低分在前
                drop_count = memory_budget.l1_rolling_drop_count
                remove_keys = [k for k, _, _ in scored[:drop_count] if k]

                if remove_keys:
                    popped_raw = self._l1_atomic_trim(
                        keys=[recent_key],
                        args=remove_keys,
                    )
                    if ttl:
                        self._redis.expire(recent_key, ttl)

                    popped_turns = []
                    for item in popped_raw:
                        try:
                            popped_turns.append(json.loads(item))
                        except Exception:
                            continue
                    if popped_turns:
                        inc_summary = await self._build_incremental_summary(popped_turns)
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

    def _score_turn(self, turn: Dict[str, Any]) -> float:
        """对单轮进行重要性评分"""
        try:
            from Agent.memory.importance_scorer import get_importance_scorer
            scorer = get_importance_scorer()
            if scorer:
                return scorer.score_conversation_turn(
                    turn.get('content', ''),
                    turn.get('role', 'user')
                ).composite
        except Exception:
            pass
        return 0.0

    async def _build_incremental_summary(self, turns: List[Dict[str, Any]]) -> str:
        """LLM 驱动的增量摘要，LLM 不可用时返回空字符串（系统本身依赖 LLM，无 LLM 时不会产生新对话）"""
        if not turns:
            return ""

        try:
            llm_summary = await self._summarize_turns_llm(turns)
            if llm_summary:
                return llm_summary[:memory_budget.l1_summary_max_chars]
        except Exception as e:
            logger.debug(f"LLM 摘要失败: {e}")

        return ""

    async def _summarize_turns_llm(self, turns: List[Dict[str, Any]]) -> str:
        """使用 LLM 生成语义摘要，捕获决策上下文和偏好变化"""
        from Agent.prompts.templates import L1_TURN_SUMMARY_PROMPT, L1_TURN_SUMMARY_SYSTEM

        # 构建对话文本
        lines = []
        for turn in turns:
            role = "用户" if turn.get("role") == "user" else "助手"
            content = (turn.get("content") or "").strip()
            if content:
                lines.append(f"{role}：{content}")
        conversation_text = "\n".join(lines)

        # 截断到预算内 — 保留尾部（popped_turns是旧轮次，尾部更接近当前对话）
        max_chars = memory_budget.summary_llm_max_chars
        if len(conversation_text) > max_chars:
            conversation_text = "..." + conversation_text[-(max_chars - 3):]

        prompt = L1_TURN_SUMMARY_PROMPT.format(content=conversation_text)

        try:
            import asyncio
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = self._get_summary_chatopenai()
            if llm is None:
                return ""

            messages = [SystemMessage(content=L1_TURN_SUMMARY_SYSTEM), HumanMessage(content=prompt)]
            response = await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=memory_budget.summary_llm_timeout
            )
            content = response.content.strip() if hasattr(response, 'content') else str(response).strip()
            if content and len(content) >= 3:
                logger.debug(f"LLM 摘要生成成功: {content[:60]}...")
                return content
            return ""
        except asyncio.TimeoutError:
            logger.debug(f"LLM 摘要超时 ({memory_budget.summary_llm_timeout}s)，降级正则")
            return ""
        except Exception as e:
            logger.debug(f"LLM 摘要调用失败: {e}")
            return ""

    def _get_summary_chatopenai(self):
        """获取摘要 LLM 客户端：配置了专用模型则新建，否则复用主模型"""
        from langchain_openai import ChatOpenAI
        from Agent.config import config as agent_config

        cfg = memory_budget
        if cfg.summary_llm_model:
            try:
                llm_config = agent_config.get_llm_config()
                llm = ChatOpenAI(
                    api_key=cfg.summary_llm_api_key or llm_config.api_key,
                    base_url=cfg.summary_llm_base_url or llm_config.base_url,
                    model=cfg.summary_llm_model,
                    temperature=0.3,  # 摘要任务低温度
                    max_tokens=200,
                    request_timeout=cfg.summary_llm_timeout,
                    max_retries=0,
                )
                logger.debug(f"使用摘要专用模型: {cfg.summary_llm_model}")
                return llm
            except Exception as e:
                logger.debug(f"摘要专用模型初始化失败，复用主模型: {e}")

        # 复用主模型
        try:
            from Agent.models.llm_model import get_llm_model
            main_llm = get_llm_model()
            return main_llm.llm if main_llm else None
        except Exception:
            return None

    def _merge_summary(self, existing: str, incoming: str) -> str:
        if not existing:
            return incoming
        if not incoming:
            return existing
        segments = [s.strip() for s in existing.split(" | ") if s.strip()]
        segments.append(incoming.strip())
        segments = segments[-5:]  # 保留最近5段
        merged = " | ".join(segments)
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
            meta = {
                'model': getattr(self, '_last_model_name', None),
                'tokens_in': getattr(self, '_last_tokens_in', None),
                'tokens_out': getattr(self, '_last_tokens_out', None),
                'latency_ms': getattr(self, '_last_latency_ms', None),
            }
            ok = self.l3_ledger.append_event(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                meta=meta,
            )
            if ok:
                self._stats["l3_writes"] += 1
            else:
                self._stats["l3_write_failures"] += 1
                logger.warning(f"L3审计写入失败: session={session_id}")

        if self.rag_enabled and user_id and content and self._should_index_to_rag(content):
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
                        # L2 更新后失效上下文缓存，使下一轮对话重新加载 L2 数据
                        self._invalidate_context_cache(session_id)
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

    def _plan_snapshot_key(self, session_id: str) -> str:
        return f"agent:memory:{session_id}:plan_snapshot"

    def update_l1_plan_snapshot(self, session_id: str, plan_data: Dict[str, Any]):
        """将 plan_data 同步到 L1 Redis，确保 session 过期后可恢复"""
        if self._redis is None or not plan_data:
            return
        try:
            key = self._plan_snapshot_key(session_id)
            self._redis.setex(key, Config.REDIS_SESSION_TTL,
                            json.dumps(plan_data, ensure_ascii=False, default=str))
            logger.debug(f"L1 plan_snapshot 已更新: session={session_id}")
        except Exception as e:
            logger.warning(f"L1 plan_snapshot 更新失败: {e}")

    def get_l1_plan_snapshot(self, session_id: str) -> Optional[Dict[str, Any]]:
        """从 L1 Redis 恢复 plan_data"""
        if self._redis is None:
            return None
        try:
            key = self._plan_snapshot_key(session_id)
            raw = self._redis.get(key)
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.debug(f"L1 plan_snapshot 读取失败: {e}")
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

    @staticmethod
    def _should_index_to_rag(content: str) -> bool:
        """RAG 质量门控：跳过低信号消息，减少向量库噪音"""
        if not content or not content.strip():
            return False
        text = content.strip()
        # 跳过过短消息
        if len(text) < 15:
            return False
        # 跳过纯确认词
        if text in ("好的", "谢谢", "收到", "明白了", "OK", "ok", "嗯", "好", "可以", "行"):
            return False
        # 跳过工具调用结果的纯 JSON（以 { 或 [ 开头且长度 < 200 的可能是工具结果片段）
        if text.startswith("{") and len(text) < 200:
            return False
        return True

    def _invalidate_context_cache(self, session_id: str):
        """L2 数据更新后失效上下文缓存"""
        try:
            from Agent.context.context_builder import get_context_builder
            builder = get_context_builder()
            builder.invalidate_cache(session_id)
            logger.debug(f"上下文缓存已失效: session={session_id}")
        except Exception as e:
            logger.debug(f"失效上下文缓存失败: {e}")

    async def run_maintenance(self, user_id: str) -> Dict[str, Any]:
        """
        定时维护任务：时间感知衰减 + 双阈值过期清理 + 过期关系清理

        由 app.py lifespan 定时调用（建议每 6 小时一次）。
        """
        result = {"decayed": 0, "expired_dual": 0, "stale_relations": {}, "global_orphans": 0}

        if not self.l2_enabled:
            return result

        try:
            result["decayed"] = self.l2_store.decay_preferences(
                user_id, decay_lambda=memory_budget.graph_decay_lambda
            )
        except Exception as e:
            logger.warning(f"时间感知衰减失败: {e}")

        try:
            result["expired_dual"] = self.l2_store.expire_by_dual_threshold(
                user_id,
                expire_days=memory_budget.merge_expire_days,
                min_importance=memory_budget.merge_min_importance,
            )
        except Exception as e:
            logger.warning(f"双阈值过期清理失败: {e}")

        try:
            result["stale_relations"] = self.l2_store.cleanup_stale_user_relations(
                user_id, max_age_days=30
            )
        except Exception as e:
            logger.warning(f"过期关系清理失败: {e}")

        try:
            result["global_orphans"] = self.l2_store.cleanup_global_orphan_preferences()
        except Exception as e:
            logger.warning(f"全局孤儿Preference回收失败: {e}")

        logger.info(f"维护任务完成: user={user_id}, {result}")
        return result

    def _maybe_trigger_merge(self, user_id: str):
        """
        计数触发合并检查: 写入量超过阈值时异步触发维护。

        在 append_turn 中调用，不阻塞用户对话。
        """
        self._stats["turns_written"] += 1  # (已在 append_turn 中递增，此处为保护)
        total_writes = (
            self._stats["turns_written"] +
            self._stats["l2_upserts"] +
            self._stats["rag_index_writes"]
        )
        if total_writes > 0 and total_writes % memory_budget.merge_count_threshold == 0:
            import asyncio
            asyncio.create_task(self.run_maintenance(user_id))
            logger.info(f"计数触发合并: user={user_id}, writes={total_writes}")

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
