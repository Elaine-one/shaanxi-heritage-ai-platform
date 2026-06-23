# -*- coding: utf-8 -*-
"""
L3 SQLite 审计账本（骨架版）
记录对话事件与性能字段，默认只写不读。
"""

import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger


class L3SQLiteLedger:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = str(Path(__file__).parent.parent / "data" / "memory.db")
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn_instance: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        self._init_table()

    def _get_conn(self) -> sqlite3.Connection:
        """获取持久连接，首次创建时启用 WAL 模式"""
        if self._conn_instance is None:
            with self._lock:
                if self._conn_instance is None:
                    self._conn_instance = sqlite3.connect(self.db_path, check_same_thread=False)
                    self._conn_instance.execute("PRAGMA journal_mode=WAL")
        return self._conn_instance

    def _init_table(self):
        conn = self._get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id TEXT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model TEXT,
                tokens_in INTEGER,
                tokens_out INTEGER,
                latency_ms INTEGER,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_events_session ON conversation_events(session_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_conv_events_user ON conversation_events(user_id)")
        conn.commit()

    def append_event(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> bool:
        if not session_id or not role:
            return False
        meta = meta or {}
        try:
            with self._lock:
                conn = self._get_conn()
                conn.execute(
                    """
                    INSERT INTO conversation_events
                    (session_id, user_id, role, content, model, tokens_in, tokens_out, latency_ms, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        user_id,
                        role,
                        content,
                        meta.get("model"),
                        meta.get("tokens_in"),
                        meta.get("tokens_out"),
                        meta.get("latency_ms"),
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.warning(f"L3 账本写入失败: {e}")
            return False


_l3_ledger_instance: Optional[L3SQLiteLedger] = None


def get_l3_sqlite_ledger() -> L3SQLiteLedger:
    global _l3_ledger_instance
    if _l3_ledger_instance is None:
        _l3_ledger_instance = L3SQLiteLedger()
    return _l3_ledger_instance

