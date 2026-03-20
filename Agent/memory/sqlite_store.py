# -*- coding: utf-8 -*-
"""
SQLite 持久化存储模块
用于存储用户偏好、会话归档等长期记忆
"""

import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger


class SQLiteStore:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'memory.db')
        
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_tables()
        logger.info(f"SQLite 存储初始化完成，数据库路径: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                username TEXT,
                preferred_departure TEXT,
                preferred_travel_mode TEXT,
                preferred_budget_range TEXT,
                preferred_group_size INTEGER,
                interested_heritage_types TEXT,
                travel_history TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_memories (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                plan_id TEXT,
                departure_location TEXT,
                travel_mode TEXT,
                group_size INTEGER,
                budget_range TEXT,
                travel_days INTEGER,
                heritage_ids TEXT,
                heritage_names TEXT,
                itinerary_summary TEXT,
                current_plan TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_id TEXT,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_memories(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversation_user ON conversation_memories(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_user ON session_memories(user_id)')
        
        conn.commit()
        conn.close()
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM user_profiles WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def update_user_profile(self, user_id: str, profile: Dict[str, Any]):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        existing = self.get_user_profile(user_id)
        
        if existing:
            cursor.execute('''
                UPDATE user_profiles SET
                    username = COALESCE(?, username),
                    preferred_departure = COALESCE(?, preferred_departure),
                    preferred_travel_mode = COALESCE(?, preferred_travel_mode),
                    preferred_budget_range = COALESCE(?, preferred_budget_range),
                    preferred_group_size = COALESCE(?, preferred_group_size),
                    interested_heritage_types = COALESCE(?, interested_heritage_types),
                    travel_history = COALESCE(?, travel_history),
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                profile.get('username'),
                profile.get('preferred_departure'),
                profile.get('preferred_travel_mode'),
                profile.get('preferred_budget_range'),
                profile.get('preferred_group_size'),
                json.dumps(profile.get('interested_heritage_types', [])) if profile.get('interested_heritage_types') else None,
                json.dumps(profile.get('travel_history', [])) if profile.get('travel_history') else None,
                user_id
            ))
        else:
            cursor.execute('''
                INSERT INTO user_profiles (user_id, username, preferred_departure, preferred_travel_mode, 
                                           preferred_budget_range, preferred_group_size, interested_heritage_types,
                                           travel_history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                profile.get('username'),
                profile.get('preferred_departure'),
                profile.get('preferred_travel_mode'),
                profile.get('preferred_budget_range'),
                profile.get('preferred_group_size'),
                json.dumps(profile.get('interested_heritage_types', [])),
                json.dumps(profile.get('travel_history', []))
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"更新用户偏好: user_id={user_id}")
    
    def save_session_memory(self, session_id: str, user_id: str, plan_id: str, 
                           session_data: Dict[str, Any], expires_hours: int = 24):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        expires_at = datetime.now().timestamp() + expires_hours * 3600
        
        cursor.execute('''
            INSERT OR REPLACE INTO session_memories 
            (session_id, user_id, plan_id, departure_location, travel_mode, group_size,
             budget_range, travel_days, heritage_ids, heritage_names, itinerary_summary,
             current_plan, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            user_id,
            plan_id,
            session_data.get('departure_location'),
            session_data.get('travel_mode'),
            session_data.get('group_size'),
            session_data.get('budget_range'),
            session_data.get('travel_days'),
            json.dumps(session_data.get('heritage_ids', [])),
            json.dumps(session_data.get('heritage_names', [])),
            session_data.get('itinerary_summary'),
            json.dumps(session_data.get('current_plan', {})),
            expires_at
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"保存会话记忆: session_id={session_id}")
    
    def get_session_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM session_memories WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data = dict(row)
            data['heritage_ids'] = json.loads(data['heritage_ids']) if data['heritage_ids'] else []
            data['heritage_names'] = json.loads(data['heritage_names']) if data['heritage_names'] else []
            data['current_plan'] = json.loads(data['current_plan']) if data['current_plan'] else {}
            return data
        return None
    
    def save_conversation(self, session_id: str, user_id: str, role: str, content: str):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversation_memories (session_id, user_id, role, content)
            VALUES (?, ?, ?, ?)
        ''', (session_id, user_id, role, content))
        
        conn.commit()
        conn.close()
    
    def get_conversations(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role, content, created_at FROM conversation_memories 
            WHERE session_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (session_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in reversed(rows)]
    
    def cleanup_expired_sessions(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        current_time = datetime.now().timestamp()
        
        cursor.execute('DELETE FROM session_memories WHERE expires_at < ?', (current_time,))
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if deleted > 0:
            logger.info(f"清理过期会话: {deleted} 个")


_sqlite_store = None


def get_sqlite_store() -> SQLiteStore:
    global _sqlite_store
    if _sqlite_store is None:
        _sqlite_store = SQLiteStore()
    return _sqlite_store
