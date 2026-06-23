# -*- coding: utf-8 -*-
"""
会话生命周期管理 — SessionLifecycle
提供会话打开/关闭的钩子，编排归档和跨会话检索
"""

from typing import Any, Dict, List, Optional

from loguru import logger


class SessionLifecycle:
    """会话生命周期管理器"""

    def __init__(self):
        self._archiver = None
        self._index = None

    @property
    def archiver(self):
        if self._archiver is None:
            try:
                from .archiver import SessionArchiver
                self._archiver = SessionArchiver()
            except Exception as e:
                logger.warning(f"SessionArchiver 初始化失败: {e}")
        return self._archiver

    @property
    def index(self):
        if self._index is None:
            try:
                from .index import SessionIndex
                self._index = SessionIndex()
            except Exception as e:
                logger.warning(f"SessionIndex 初始化失败: {e}")
        return self._index

    async def on_session_open(
        self, user_id: str, query: str = ""
    ) -> Dict[str, Any]:
        """会话打开钩子 — 检索相关历史会话上下文"""
        result = {"cross_session_context": "", "recent_sessions": []}

        if not user_id:
            return result

        try:
            if self.index:
                recent = self.index.get_recent_sessions(user_id, limit=3)
                result["recent_sessions"] = recent

                if query:
                    ctx = self._get_cross_session_context(user_id, query)
                    result["cross_session_context"] = ctx
        except Exception as e:
            logger.debug(f"on_session_open 失败（不影响主流程）: {e}")

        return result

    async def on_session_close(self, session_id: str, user_id: str) -> bool:
        """会话关闭钩子 — 触发归档管线，异步执行不阻塞主流程"""
        if not session_id or not user_id:
            return False

        try:
            if self.archiver:
                result = await self.archiver.archive_session(session_id, user_id)
                if result:
                    logger.info(f"会话归档成功: session={session_id}")
                    return True
                logger.debug(f"会话归档返回空: session={session_id}")
                return False
        except Exception as e:
            logger.warning(f"会话关闭钩子失败（不影响主流程）: {e}")

        return False

    async def close_and_archive(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """完整的会话关闭流程：归档 + 清理"""
        result = {"archived": False, "archive": None}

        if not session_id or not user_id:
            return result

        try:
            archive = None
            if self.archiver:
                archive = await self.archiver.archive_session(session_id, user_id)

            if archive:
                result["archived"] = True
                result["archive"] = archive

            return result
        except Exception as e:
            logger.warning(f"close_and_archive 失败: {e}")
            return result

    def _get_cross_session_context(
        self, user_id: str, query: str, top_k: int = 2
    ) -> str:
        """检索相关历史会话上下文"""
        try:
            if not self.index:
                return ""

            similar = self.index.search_similar_sessions(
                query=query,
                user_id=user_id,
                top_k=top_k,
            )
            if not similar:
                return ""

            parts = ["\n# 历史会话"]
            for i, session in enumerate(similar, 1):
                topic = session.get("topic", "未知主题")
                decisions = session.get("key_decisions", [])
                regions = session.get("regions", [])
                ts = session.get("timestamp", "")

                line = f"- 会话{i}: {topic}"
                if regions:
                    line += f" (涉及: {', '.join(regions[:3])})"
                if decisions:
                    line += f" — {', '.join(decisions[:2])}"
                parts.append(line)

            return "\n".join(parts)

        except Exception as e:
            logger.debug(f"跨会话上下文检索失败: {e}")
            return ""


_session_lifecycle: Optional[SessionLifecycle] = None


def get_session_lifecycle() -> SessionLifecycle:
    """获取会话生命周期管理器单例"""
    global _session_lifecycle
    if _session_lifecycle is None:
        _session_lifecycle = SessionLifecycle()
    return _session_lifecycle
