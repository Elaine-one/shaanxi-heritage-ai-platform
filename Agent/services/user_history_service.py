#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户历史记录管理服务
维护用户会话历史索引和摘要
"""

import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from loguru import logger

from Agent.memory.session_provider import get_session_pool
from Agent.config.settings import Config


class UserHistoryService:
    """
    用户历史记录管理服务
    管理用户的会话历史、统计信息和偏好
    """

    def __init__(self):
        """初始化用户历史服务"""
        self.session_pool = get_session_pool()
        self._redis_client = self.session_pool.get_redis_client()
        self.minio_service = None

        try:
            from .minio_storage import get_minio_service
            self.minio_service = get_minio_service()
        except Exception as e:
            logger.warning(f"MinIO服务加载失败: {str(e)}")

    def _require_redis(self):
        if self._redis_client is None:
            raise RuntimeError("Redis 不可用，用户历史服务需要 Redis 支持")

    def _get_user_sessions_key(self, user_id: str) -> str:
        return self.session_pool.get_user_sessions_key(user_id)

    def _get_user_history_key(self, user_id: str) -> str:
        return f"agent:user:{user_id}:history:summary"

    def _get_user_stats_key(self, user_id: str) -> str:
        return f"agent:user:{user_id}:stats"

    def _get_user_favorites_key(self, user_id: str) -> str:
        return f"agent:user:{user_id}:favorites"

    def add_session_to_history(self,
                              user_id: str,
                              session_summary: Dict[str, Any]) -> bool:
        try:
            self._require_redis()
            redis_client = self._redis_client

            user_sessions_key = self._get_user_sessions_key(user_id)
            session_id = session_summary.get("session_id")

            redis_client.sadd(user_sessions_key, session_id)
            redis_client.expire(user_sessions_key, Config.REDIS_SESSION_TTL * 7)

            user_history_key = self._get_user_history_key(user_id)
            score = datetime.now().timestamp()

            summary_json = json.dumps(session_summary, ensure_ascii=False)
            redis_client.zadd(user_history_key, {summary_json: score})
            redis_client.expire(user_history_key, Config.REDIS_SESSION_TTL * 7)

            self._update_user_stats(user_id, session_summary)

            logger.info(f"会话已添加到用户历史: user={user_id}, session={session_id}")
            return True

        except Exception as e:
            logger.error(f"添加会话到历史失败: {str(e)}")
            return False

    def _update_user_stats(self, user_id: str, session_summary: Dict[str, Any]):
        try:
            self._require_redis()
            redis_client = self._redis_client
            stats_key = self._get_user_stats_key(user_id)

            stats_raw = redis_client.get(stats_key)
            stats = json.loads(stats_raw) if stats_raw else {
                "total_sessions": 0,
                "total_messages": 0,
                "total_exports": 0,
                "favorite_count": 0,
                "destinations": [],
                "first_session": None,
                "last_session": None
            }

            stats["total_sessions"] += 1
            stats["total_messages"] += session_summary.get("message_count", 0)
            stats["last_session"] = datetime.now().isoformat()

            if stats["first_session"] is None:
                stats["first_session"] = datetime.now().isoformat()

            destination = session_summary.get("destination")
            if destination and destination not in stats["destinations"]:
                stats["destinations"].append(destination)

            redis_client.setex(
                stats_key,
                Config.REDIS_SESSION_TTL * 30,
                json.dumps(stats, ensure_ascii=False)
            )

        except Exception as e:
            logger.error(f"更新用户统计失败: {str(e)}")

    def get_recent_sessions(self,
                           user_id: str,
                           limit: int = 10,
                           include_archived: bool = False) -> List[Dict[str, Any]]:
        try:
            self._require_redis()
            redis_client = self._redis_client
            user_history_key = self._get_user_history_key(user_id)

            results = redis_client.zrevrange(user_history_key, 0, limit - 1)

            sessions = []
            for result in results:
                try:
                    summary = json.loads(result)

                    session_id = summary.get("session_id")
                    session = self.session_pool.get_session(session_id)

                    if session:
                        summary["status"] = "active"
                        summary["current_plan"] = session.current_plan
                    else:
                        summary["status"] = "expired"

                    sessions.append(summary)

                except json.JSONDecodeError:
                    continue

            return sessions

        except Exception as e:
            logger.error(f"获取最近会话失败: {str(e)}")
            return []

    def get_session_stats(self, user_id: str) -> Dict[str, Any]:
        try:
            self._require_redis()
            redis_client = self._redis_client
            stats_key = self._get_user_stats_key(user_id)

            stats_raw = redis_client.get(stats_key)
            if stats_raw:
                stats = json.loads(stats_raw)
            else:
                stats = {
                    "total_sessions": 0,
                    "total_messages": 0,
                    "total_exports": 0,
                    "favorite_count": 0,
                    "destinations": [],
                    "first_session": None,
                    "last_session": None
                }

            user_sessions_key = self._get_user_sessions_key(user_id)
            active_sessions = redis_client.scard(user_sessions_key)
            stats["active_sessions"] = active_sessions

            return stats

        except Exception as e:
            logger.error(f"获取会话统计失败: {str(e)}")
            return {}

    def get_timeline(self,
                    user_id: str,
                    days: int = 30) -> List[Dict[str, Any]]:
        try:
            self._require_redis()
            redis_client = self._redis_client
            user_history_key = self._get_user_history_key(user_id)

            cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()

            results = redis_client.zrevrangebyscore(
                user_history_key,
                "+inf",
                cutoff_time,
                withscores=True
            )

            timeline = []
            for result, score in results:
                try:
                    summary = json.loads(result)
                    summary["timestamp"] = datetime.fromtimestamp(score).isoformat()
                    timeline.append(summary)
                except json.JSONDecodeError:
                    continue

            return timeline

        except Exception as e:
            logger.error(f"获取时间线失败: {str(e)}")
            return []

    def add_favorite(self, user_id: str, session_id: str) -> bool:
        try:
            self._require_redis()
            redis_client = self._redis_client
            favorites_key = self._get_user_favorites_key(user_id)

            redis_client.sadd(favorites_key, session_id)
            redis_client.expire(favorites_key, Config.REDIS_SESSION_TTL * 30)

            self._update_favorite_count(user_id, 1)

            logger.info(f"会话已收藏: user={user_id}, session={session_id}")
            return True

        except Exception as e:
            logger.error(f"收藏会话失败: {str(e)}")
            return False

    def remove_favorite(self, user_id: str, session_id: str) -> bool:
        try:
            self._require_redis()
            redis_client = self._redis_client
            favorites_key = self._get_user_favorites_key(user_id)

            redis_client.srem(favorites_key, session_id)

            self._update_favorite_count(user_id, -1)

            logger.info(f"会话已取消收藏: user={user_id}, session={session_id}")
            return True

        except Exception as e:
            logger.error(f"取消收藏失败: {str(e)}")
            return False

    def _update_favorite_count(self, user_id: str, delta: int):
        try:
            self._require_redis()
            redis_client = self._redis_client
            stats_key = self._get_user_stats_key(user_id)

            stats_raw = redis_client.get(stats_key)
            if stats_raw:
                stats = json.loads(stats_raw)
                stats["favorite_count"] = max(0, stats.get("favorite_count", 0) + delta)

                redis_client.setex(
                    stats_key,
                    Config.REDIS_SESSION_TTL * 30,
                    json.dumps(stats, ensure_ascii=False)
                )
        except Exception as e:
            logger.error(f"更新收藏数失败: {str(e)}")

    def get_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            self._require_redis()
            redis_client = self._redis_client
            favorites_key = self._get_user_favorites_key(user_id)

            session_ids = redis_client.smembers(favorites_key)
            favorites = []

            for session_id in session_ids:
                session = self.session_pool.get_session(session_id)
                if session:
                    favorites.append({
                        "session_id": session_id,
                        "plan_id": session.plan_id,
                        "destination": session.departure_location,
                        "created_at": session.created_at,
                        "last_activity": session.last_activity
                    })

            return favorites

        except Exception as e:
            logger.error(f"获取收藏列表失败: {str(e)}")
            return []

    def cleanup_old_sessions(self,
                            user_id: str,
                            days: int = 90) -> int:
        try:
            self._require_redis()
            redis_client = self._redis_client
            user_history_key = self._get_user_history_key(user_id)

            cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()

            removed = redis_client.zremrangebyscore(
                user_history_key,
                "-inf",
                cutoff_time
            )

            logger.info(f"已清理用户 {user_id} 的 {removed} 条旧会话记录")
            return removed

        except Exception as e:
            logger.error(f"清理旧会话失败: {str(e)}")
            return 0

    def get_user_storage_usage(self, user_id: str) -> Dict[str, Any]:
        try:
            stats = self.get_session_stats(user_id)

            estimated_usage = {
                "conversations_mb": stats.get("total_sessions", 0) * 0.5,
                "pdfs_mb": stats.get("total_exports", 0) * 2,
                "total_mb": 0,
                "total_gb": 0
            }
            estimated_usage["total_mb"] = (
                estimated_usage["conversations_mb"] +
                estimated_usage["pdfs_mb"]
            )
            estimated_usage["total_gb"] = round(estimated_usage["total_mb"] / 1024, 2)

            return {
                "user_id": user_id,
                "estimated_usage": estimated_usage,
                "stats": stats
            }

        except Exception as e:
            logger.error(f"获取存储使用情况失败: {str(e)}")
            return {}


_user_history_service_instance = None


def get_user_history_service() -> UserHistoryService:
    global _user_history_service_instance
    if _user_history_service_instance is None:
        _user_history_service_instance = UserHistoryService()
    return _user_history_service_instance


def reset_user_history_service():
    global _user_history_service_instance
    _user_history_service_instance = None
