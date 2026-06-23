# -*- coding: utf-8 -*-
"""
会话归档器 — SessionArchiver
Session Close 时触发，生成结构化会话归档：
1. LLM 生成会话摘要
2. 提取关键实体/决策
3. 存储归档 (ChromaDB 向量)
4. 更新用户画像 (L2)
5. 增强知识图谱 (L2)
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger

from Agent.config.memory_budget import memory_budget


class SessionArchive:
    """会话归档数据结构"""

    def __init__(
        self,
        session_id: str,
        user_id: str,
        summary: Dict[str, Any],
        statistics: Dict[str, Any],
        timestamp: str = None,
    ):
        self.session_id = session_id
        self.user_id = user_id
        self.summary = summary
        self.statistics = statistics
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "statistics": self.statistics,
        }


class SessionArchiver:
    """会话归档器 — 编排完整归档管线"""

    def __init__(self):
        self._memory_coordinator = None
        self._vector_store = None
        self._l2_store = None

    @property
    def memory_coordinator(self):
        if self._memory_coordinator is None:
            from Agent.memory.coordinator import get_memory_coordinator
            self._memory_coordinator = get_memory_coordinator()
        return self._memory_coordinator

    @property
    def vector_store(self):
        if self._vector_store is None:
            try:
                from Agent.memory.vector_store import get_vector_store
                self._vector_store = get_vector_store()
            except Exception:
                pass
        return self._vector_store

    @property
    def l2_store(self):
        if self._l2_store is None:
            try:
                from Agent.memory.l2_graph_store import get_l2_graph_store
                self._l2_store = get_l2_graph_store()
            except Exception:
                pass
        return self._l2_store

    async def archive_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """归档主入口 — 编排完整归档管线"""
        try:
            l1_snapshot = self.memory_coordinator.get_l1_snapshot(session_id)
            recent_turns = l1_snapshot.get("recent_turns", [])
            existing_summary = l1_snapshot.get("summary", "")

            if not recent_turns:
                logger.debug(f"归档跳过: session={session_id} 无对话数据")
                return None

            total_turns = len(recent_turns)

            summary = await self._generate_session_summary(recent_turns, existing_summary)
            entities = self._extract_session_entities(recent_turns, summary)
            statistics = self._compute_statistics(recent_turns)

            archive = SessionArchive(
                session_id=session_id,
                user_id=user_id,
                summary={
                    "topic": summary.get("topic", ""),
                    "key_decisions": summary.get("key_decisions", []),
                    "heritage_entities": entities,
                    "regions": summary.get("regions", []),
                    "plan_generated": summary.get("plan_generated", False),
                },
                statistics=statistics,
            )

            doc_id = f"archive_{session_id}"
            archive_text = self._archive_to_text(archive)
            self._index_archive_embedding(doc_id, archive_text, archive.to_dict())

            l2_ok = await self._enrich_l2_graph(user_id, entities, statistics)
            if l2_ok or not entities:
                self._cleanup_l1_data(session_id)
            else:
                logger.warning(f"L2增强失败，保留L1数据以防丢失: session={session_id}")

            logger.info(
                f"会话归档完成: session={session_id}, "
                f"turns={total_turns}, entities={len(entities)}"
            )
            return archive.to_dict()

        except Exception as e:
            logger.warning(f"会话归档失败（不影响主流程）: session={session_id}, error={e}")
            return None

    async def _generate_session_summary(
        self, turns: List[Dict[str, Any]], existing_summary: str = ""
    ) -> Dict[str, Any]:
        """LLM 生成结构化会话摘要"""
        conversation_text = self._turns_to_text(turns)
        if not conversation_text:
            return {}

        prompt = self._build_archive_summary_prompt(conversation_text, existing_summary)

        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage
            from Agent.config import config as agent_config

            llm_config = agent_config.get_llm_config()
            summary_model = memory_budget.summary_llm_model or llm_config.model
            summary_api_key = memory_budget.summary_llm_api_key or llm_config.api_key
            summary_base_url = memory_budget.summary_llm_base_url or llm_config.base_url

            llm = ChatOpenAI(
                api_key=summary_api_key,
                base_url=summary_base_url,
                model=summary_model,
                temperature=0.3,
                max_tokens=400,
                request_timeout=15,
                max_retries=0,
            )

            system_prompt = (
                "你是一个会话摘要助手。请从多轮对话中提取以下结构化信息，"
                "以 JSON 格式返回，不要包含其他文字。"
            )
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]

            import asyncio
            response = await asyncio.wait_for(llm.ainvoke(messages), timeout=15)
            content = response.content.strip() if hasattr(response, 'content') else ""

            try:
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                result = json.loads(content.strip())
                return result if isinstance(result, dict) else {}
            except (json.JSONDecodeError, IndexError):
                return {"topic": content[:200]} if content else {}

        except Exception as e:
            logger.debug(f"LLM 归档摘要生成失败: {e}")
            return {}

    def _build_archive_summary_prompt(self, conversation_text: str, existing_summary: str = "") -> str:
        existing_part = f"\n\n已有摘要：{existing_summary}" if existing_summary else ""
        return (
            f"从以下对话片段中提取结构化信息，返回 JSON 格式：\n\n"
            f"对话：\n{conversation_text}\n{existing_part}\n\n"
            f'返回格式：{{"topic": "主题(50字内)", '
            f'"key_decisions": ["决策1", "决策2"], '
            f'"regions": ["地区1"], '
            f'"plan_generated": true/false, '
            f'"user_satisfaction": "positive/neutral/negative"}}'
        )

    def _turns_to_text(self, turns: List[Dict[str, Any]], max_chars: int = None) -> str:
        max_chars = max_chars or getattr(memory_budget, 'summary_llm_max_chars', 4000)
        if len(turns) <= 4:
            lines = []
            for turn in turns:
                role = "用户" if turn.get("role") == "user" else "助手"
                content = (turn.get("content") or "").strip()
                if content:
                    lines.append(f"{role}：{content}")
            return "\n".join(lines)

        lines = []
        first = turns[0]
        role = "用户" if first.get("role") == "user" else "助手"
        content = (first.get("content") or "").strip()
        if content:
            lines.append(f"{role}：{content}")
            total = len(lines[-1])
        else:
            total = 0

        recent_lines = []
        for turn in reversed(turns[1:]):
            role = "用户" if turn.get("role") == "user" else "助手"
            content = (turn.get("content") or "").strip()
            if content:
                line = f"{role}：{content}"
                if total + len(line) > max_chars:
                    break
                total += len(line)
                recent_lines.append(line)
        return "\n".join(lines + list(reversed(recent_lines)))

    def _extract_session_entities(
        self, turns: List[Dict[str, Any]], summary: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """从对话和摘要中提取非遗实体"""
        entities = []
        seen_names = set()

        heritage_pattern = re.compile(
            r'(皮影|秦腔|剪纸|泥塑|老腔|鼓乐|面花|刺绣|木版年画|社火|碗碗腔|眉户|腰鼓|民歌|花鼓)'
        )

        for turn in turns:
            content = (turn.get("content") or "").strip()
            matches = heritage_pattern.findall(content)
            for name in matches:
                if name not in seen_names:
                    seen_names.add(name)
                    entities.append({"name": name, "category": "", "source": "dialogue"})

        for decision in summary.get("key_decisions", []):
            matches = heritage_pattern.findall(str(decision))
            for name in matches:
                if name not in seen_names:
                    seen_names.add(name)
                    entities.append({"name": name, "category": "", "source": "decision"})

        return entities[:10]

    def _compute_statistics(self, turns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算会话统计"""
        total_turns = len(turns)
        user_turns = sum(1 for t in turns if t.get("role") == "user")
        assistant_turns = sum(1 for t in turns if t.get("role") == "assistant")

        tools_called = []
        tool_pattern = re.compile(r'(heritage_search|maps_direction|maps_weather|route_preview|plan_edit|plan_query)')
        for turn in turns:
            if turn.get("role") == "assistant":
                content = turn.get("content", "") or ""
                matches = tool_pattern.findall(content)
                tools_called.extend(matches)

        return {
            "total_turns": total_turns,
            "user_turns": user_turns,
            "assistant_turns": assistant_turns,
            "tools_called": list(set(tools_called)),
            "user_satisfaction": "neutral",
        }

    def _archive_to_text(self, archive: SessionArchive) -> str:
        """将归档文档转为可索引的文本"""
        parts = [
            f"主题: {archive.summary.get('topic', '')}",
        ]
        for decision in archive.summary.get("key_decisions", []):
            parts.append(f"决策: {decision}")
        for entity in archive.summary.get("heritage_entities", []):
            name = entity.get("name", "") if isinstance(entity, dict) else str(entity)
            parts.append(f"非遗: {name}")
        for region in archive.summary.get("regions", []):
            parts.append(f"地区: {region}")
        return "\n".join(parts)

    def _index_archive_embedding(
        self, doc_id: str, content: str, metadata: Dict[str, Any]
    ):
        """向量索引到 ChromaDB session_archives 集合"""
        if not self.vector_store:
            logger.debug("VectorStore 不可用，跳过归档向量索引")
            return

        try:
            collection = self.vector_store.collections.get("session_archives")
            if collection is None:
                logger.debug("session_archives 集合未初始化，跳过")
                return

            embedding = self.vector_store.embedding_model.encode_single(content)
            meta = {
                "session_id": metadata.get("session_id", ""),
                "user_id": metadata.get("user_id", ""),
                "timestamp": metadata.get("timestamp", ""),
                "topic": metadata.get("summary", {}).get("topic", "")[:200],
            }

            collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[meta],
            )
            logger.debug(f"归档向量索引完成: {doc_id}")
        except Exception as e:
            logger.warning(f"归档向量索引失败: {e}")

    async def _enrich_l2_graph(
        self, user_id: str, entities: List[Dict[str, Any]], statistics: Dict[str, Any]
    ) -> bool:
        """增强 L2 知识图谱：用户→非遗 PREFERS 关联

        Returns:
            bool: True 表示 L2 增强成功或无实体需要处理，False 表示失败
        """
        if not self.l2_store or not entities:
            return True

        if not self.l2_store.is_available():
            logger.warning("L2 图谱不可用，跳过归档增强")
            return False

        success_count = 0
        fail_count = 0
        for entity in entities:
            name = entity.get("name", "")
            if not name:
                continue
            try:
                from Agent.memory.coordinator import get_memory_coordinator
                coordinator = get_memory_coordinator()
                resolved_id = coordinator._resolve_heritage_by_name(name)
                if resolved_id:
                    ok = self.l2_store.link_user_heritage(
                        user_id, resolved_id,
                        rel_type="PREFERS",
                        confidence=0.5,
                        source="session_archive",
                    )
                    if ok:
                        success_count += 1
                    else:
                        fail_count += 1
            except Exception as e:
                fail_count += 1
                logger.debug(f"归档→L2图谱关联失败(name={name}): {e}")

        if fail_count > 0 and success_count == 0:
            logger.warning(f"L2 增强全部失败: entities={len(entities)}")
            return False
        return True

    def _cleanup_l1_data(self, session_id: str):
        """清理 L1 Redis 临时数据"""
        try:
            redis_client = self.memory_coordinator._redis
            if redis_client:
                recent_key = self.memory_coordinator._recent_key(session_id)
                summary_key = self.memory_coordinator._summary_key(session_id)
                summary_meta_key = self.memory_coordinator._summary_meta_key(session_id)
                redis_client.delete(recent_key, summary_key, summary_meta_key)
                logger.debug(f"L1 数据已清理: session={session_id}")
        except Exception as e:
            logger.debug(f"L1 清理失败: {e}")
