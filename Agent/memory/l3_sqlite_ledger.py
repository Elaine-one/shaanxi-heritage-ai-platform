# -*- coding: utf-8 -*-
"""
L3 SQLite 审计账本（骨架版）
记录对话事件与性能字段，默认只写不读。
"""

import os
import sqlite3
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
        self._init_table()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_table(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_events_session ON conversation_events(session_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_events_user ON conversation_events(user_id)")
        conn.commit()
        conn.close()

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
        conn = None
        try:
            conn = self._conn()
            cur = conn.cursor()
            cur.execute(
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
        finally:
            if conn:
                conn.close()


_l3_ledger_instance: Optional[L3SQLiteLedger] = None


def get_l3_sqlite_ledger() -> L3SQLiteLedger:
    global _l3_ledger_instance
    if _l3_ledger_instance is None:
        _l3_ledger_instance = L3SQLiteLedger()
    return _l3_ledger_instance

