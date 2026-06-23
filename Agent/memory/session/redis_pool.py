# -*- coding: utf-8 -*-
"""
Redis 会话池 — RedisSessionPool
继承 SessionPool，将 L1 热数据持久化到 Redis，支持分布式部署
"""

import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import asdict
from loguru import logger

from .context import SessionContext
from .pool import SessionPool
from Agent.config.settings import Config

try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    Redis = None
    REDIS_AVAILABLE = False
    logger.warning("Redis库未安装，Redis会话存储不可用")


class RedisSessionPool(SessionPool):
    """基于 Redis 的会话池管理器，继承自 SessionPool"""

    def __init__(self, max_sessions: int = 100, cleanup_interval: int = 3600):
        self.max_sessions = max_sessions
        self.cleanup_interval = cleanup_interval
        self.redis_client: Optional[Redis] = None
        self.session_key_prefix = "agent:session:"
        self.session_index_key = "agent:session:index"

        self._user_history_service = None
        self._conversation_service = None

        self._init_redis()
        self._cleanup_task = None
        self._start_cleanup_task()

        logger.info(f"Redis会话池初始化完成，最大会话数: {max_sessions}")

    @property
    def user_history_service(self):
        if self._user_history_service is None:
            try:
                from Agent.services.user_history_service import get_user_history_service
                self._user_history_service = get_user_history_service()
            except Exception as e:
                logger.warning(f"用户历史服务加载失败: {str(e)}")
        return self._user_history_service

    @property
    def conversation_service(self):
        if self._conversation_service is None:
            try:
                from Agent.services.conversation_service import get_conversation_service
                self._conversation_service = get_conversation_service()
            except Exception as e:
                logger.warning(f"对话服务加载失败: {str(e)}")
        return self._conversation_service

    def _init_redis(self):
        """初始化 Redis 连接 — L1 热数据存储必要组件，不可降级"""
        try:
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                db=Config.REDIS_DB,
                password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            self.redis_client.ping()
            logger.info(f"Redis连接成功: {Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)} — L1 热数据存储不可用，系统无法正常工作")
            self.redis_client = None
            raise RuntimeError(f"Redis连接失败，L1热数据存储不可用: {str(e)}")

    def get_redis_client(self):
        return self.redis_client

    def _get_session_key(self, session_id: str) -> str:
        return f"{self.session_key_prefix}{session_id}"

    def _session_to_dict(self, session: SessionContext) -> Dict[str, Any]:
        data = asdict(session)
        for key in ['created_at', 'last_updated', 'last_activity']:
            if isinstance(data.get(key), datetime):
                data[key] = data[key].isoformat()
        return data

    def _dict_to_session(self, data: Dict[str, Any]) -> SessionContext:
        return SessionContext(**data)

    def _extract_core_info(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        basic_info = plan_data.get('basic_info', {})
        heritage_items = plan_data.get('heritage_items', [])

        selected_heritage_items = []
        location_coordinates = {}
        for item in heritage_items:
            if isinstance(item, int):
                selected_heritage_items.append({'id': item})
                continue
            if not isinstance(item, dict):
                continue
            entry = {
                'id': item.get('id'),
                'name': item.get('name', ''),
                'region': item.get('region', ''),
                'category': item.get('category', ''),
            }
            selected_heritage_items.append(entry)
            lat = item.get('latitude') or item.get('lat')
            lon = item.get('longitude') or item.get('lng')
            if lat and lon:
                location_coordinates[item.get('name', '')] = {
                    'latitude': lat,
                    'longitude': lon,
                }

        budget_constraints = {}
        budget_range = (
            basic_info.get('budget_range') or basic_info.get('budgetRange')
            or plan_data.get('budget_range')
        )
        if budget_range:
            budget_constraints['budget_range'] = budget_range
        budget = plan_data.get('budget')
        if budget:
            budget_constraints['budget'] = budget

        time_constraints = {}
        travel_days = (
            basic_info.get('travel_days') or basic_info.get('travelDays')
            or plan_data.get('travel_days')
        )
        if travel_days:
            time_constraints['travel_days'] = travel_days

        return {
            'departure_location': (
                basic_info.get('departure') or basic_info.get('departureLocation')
                or plan_data.get('departure') or plan_data.get('departure_location')
                or plan_data.get('departureLocation')
            ),
            'travel_mode': (
                basic_info.get('travel_mode') or basic_info.get('travelMode')
                or plan_data.get('travel_mode') or plan_data.get('travelMode')
            ),
            'group_size': (
                basic_info.get('group_size') or basic_info.get('groupSize')
                or plan_data.get('group_size') or plan_data.get('groupSize')
            ),
            'budget_range': budget_range,
            'travel_days': travel_days,
            'heritage_ids': [item.get('id') for item in selected_heritage_items if item.get('id')],
            'heritage_names': [item.get('name', '') for item in selected_heritage_items if item.get('name')],
            'special_requirements': (
                basic_info.get('special_requirements') or
                plan_data.get('special_requirements', [])
            ),
            'weather_info': plan_data.get('weather_info') or plan_data.get('weather'),
            'selected_heritage_items': selected_heritage_items,
            'location_coordinates': location_coordinates,
            'budget_constraints': budget_constraints,
            'time_constraints': time_constraints,
        }

    def _save_plan_snapshot(self, session_id: str, plan_data: Dict[str, Any]):
        if not self.redis_client or not plan_data:
            return
        try:
            basic_info = plan_data.get('basic_info', {})
            heritage_items = plan_data.get('heritage_items', [])

            snapshot = {
                'departure_location': (
                    basic_info.get('departure') or basic_info.get('departureLocation')
                    or plan_data.get('departure') or plan_data.get('departure_location', '')
                ),
                'travel_days': (
                    basic_info.get('travel_days') or basic_info.get('travelDays')
                    or plan_data.get('travel_days', 0)
                ),
                'travel_mode': (
                    basic_info.get('travel_mode') or basic_info.get('travelMode')
                    or plan_data.get('travel_mode', 'driving')
                ),
                'group_size': (
                    basic_info.get('group_size') or basic_info.get('groupSize')
                    or plan_data.get('group_size', 1)
                ),
                'budget_range': (
                    basic_info.get('budget_range') or basic_info.get('budgetRange')
                    or plan_data.get('budget_range', '')
                ),
                'special_requirements': list(
                    basic_info.get('special_requirements')
                    or plan_data.get('special_requirements', [])
                    or []
                ),
                'heritage_items': [
                    {
                        'id': item.get('id'),
                        'name': item.get('name', ''),
                        'region': item.get('region', ''),
                        'category': item.get('category', ''),
                        'level': item.get('level', ''),
                        'latitude': item.get('latitude') or item.get('lat'),
                        'longitude': item.get('longitude') or item.get('lng'),
                    }
                    for item in heritage_items if isinstance(item, dict) and item.get('id')
                ],
                'itinerary': plan_data.get('itinerary', []) or [],
            }

            key = f"agent:memory:{session_id}:plan_snapshot"
            self.redis_client.setex(
                key, Config.REDIS_SESSION_TTL,
                json.dumps(snapshot, ensure_ascii=False, default=str)
            )
            logger.debug(f"L1 plan_snapshot 已保存: session={session_id}")
        except Exception as e:
            logger.warning(f"L1 plan_snapshot 保存失败: {e}")

    async def create_session(self,
                           plan_id: str,
                           original_plan: Dict[str, Any],
                           user_id: Optional[str] = None,
                           username: Optional[str] = None) -> SessionContext:
        current_count = self.redis_client.zcard(self.session_index_key)
        if current_count >= self.max_sessions:
            await self._cleanup_oldest_sessions_redis(1)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_id = f"edit_{plan_id}_{timestamp}"

        core_info = self._extract_core_info(original_plan)

        session_context = SessionContext(
            session_id=session_id,
            plan_id=plan_id,
            user_id=user_id,
            username=username,
            current_plan=original_plan.copy(),
            original_plan=original_plan.copy(),
            **core_info
        )

        self._save_session_to_redis(session_context)

        if user_id:
            try:
                user_sessions_key = self.get_user_sessions_key(user_id)
                pipe = self.redis_client.pipeline()
                pipe.sadd(user_sessions_key, session_id)
                pipe.expire(user_sessions_key, Config.REDIS_SESSION_TTL + 3600)
                pipe.execute()
            except Exception as e:
                logger.warning(f"更新用户会话索引失败: {e}")

        if user_id and self.user_history_service:
            try:
                session_summary = {
                    "session_id": session_id,
                    "plan_id": plan_id,
                    "user_id": user_id,
                    "title": f"规划会话 {plan_id}",
                    "destination": core_info.get("departure_location", "未知"),
                    "created_at": session_context.created_at,
                    "last_activity": session_context.last_activity,
                    "message_count": 0,
                    "status": "active"
                }
                self.user_history_service.add_session_to_history(user_id, session_summary)
            except Exception as e:
                logger.warning(f"添加会话到用户历史失败: {str(e)}")

        if self.conversation_service:
            try:
                self.conversation_service.initialize_conversation_metadata(
                    session_id,
                    {
                        "plan_id": plan_id,
                        "user_id": user_id,
                        "created_at": session_context.created_at
                    }
                )
            except Exception as e:
                logger.warning(f"初始化对话元数据失败: {str(e)}")

        logger.info(f"创建新会话: {session_id}，当前会话数: {self.redis_client.zcard(self.session_index_key)}")
        return session_context

    def _save_session_to_redis(self, session: SessionContext):
        session_key = self._get_session_key(session.session_id)
        session_data = self._session_to_dict(session)

        pipe = self.redis_client.pipeline()
        pipe.setex(
            session_key,
            Config.REDIS_SESSION_TTL,
            json.dumps(session_data, ensure_ascii=False)
        )
        score = datetime.fromisoformat(session.last_activity).timestamp()
        pipe.zadd(self.session_index_key, {session.session_id: score})
        pipe.expire(self.session_index_key, Config.REDIS_SESSION_TTL + 3600)
        pipe.execute()

    def get_session(self, session_id: str) -> Optional[SessionContext]:
        session_key = self._get_session_key(session_id)
        session_data = self.redis_client.get(session_key)

        if not session_data:
            return None

        try:
            data = json.loads(session_data)
            session = self._dict_to_session(data)

            now_iso = datetime.now().isoformat()
            data['last_activity'] = now_iso
            score = datetime.fromisoformat(now_iso).timestamp()

            pipe = self.redis_client.pipeline()
            pipe.setex(
                session_key,
                Config.REDIS_SESSION_TTL,
                json.dumps(data, ensure_ascii=False)
            )
            pipe.zadd(self.session_index_key, {session_id: score})
            pipe.expire(self.session_index_key, Config.REDIS_SESSION_TTL + 3600)
            pipe.execute()

            session.last_activity = now_iso
            return session
        except Exception as e:
            logger.error(f"解析会话数据失败: {str(e)}")
            return None

    def update_session_context(self, session_id: str, session_context: SessionContext) -> bool:
        session_key = self._get_session_key(session_id)
        if not self.redis_client.exists(session_key):
            return False

        session_context.last_updated = datetime.now().isoformat()
        session_context.last_activity = datetime.now().isoformat()
        self._save_session_to_redis(session_context)
        return True

    def update_session(self, session_id: str, updated_plan: Dict[str, Any]) -> bool:
        session = self.get_session(session_id)
        if not session:
            return False

        session.current_plan = updated_plan.copy()
        session.last_updated = datetime.now().isoformat()
        session.edit_count += 1

        if 'travel_days' in updated_plan:
            session.travel_days = updated_plan['travel_days']
        if 'departure' in updated_plan or 'departure_location' in updated_plan:
            session.departure_location = updated_plan.get('departure') or updated_plan.get('departure_location', '')
        if 'travel_mode' in updated_plan:
            session.travel_mode = updated_plan['travel_mode']
        if 'group_size' in updated_plan:
            session.group_size = updated_plan['group_size']
        if 'budget_range' in updated_plan:
            session.budget_range = updated_plan['budget_range']

        core_info = self._extract_core_info(updated_plan)
        session.weather_info = core_info.get('weather_info')
        session.selected_heritage_items = core_info.get('selected_heritage_items', [])
        session.location_coordinates = core_info.get('location_coordinates', {})
        session.budget_constraints = core_info.get('budget_constraints', {})
        session.time_constraints = core_info.get('time_constraints', {})

        self._save_session_to_redis(session)
        self._save_plan_snapshot(session_id, updated_plan)

        logger.info(f"会话 {session_id} 已更新，travel_days={session.travel_days}, 编辑次数: {session.edit_count}")
        return True

    def remove_session(self, session_id: str) -> bool:
        session = self.get_session(session_id)
        session_key = self._get_session_key(session_id)
        plan_snapshot_key = f"agent:memory:{session_id}:plan_snapshot"

        pipe = self.redis_client.pipeline()
        pipe.delete(session_key)
        pipe.delete(plan_snapshot_key)
        pipe.zrem(self.session_index_key, session_id)
        if session and session.user_id:
            user_sessions_key = self.get_user_sessions_key(session.user_id)
            pipe.srem(user_sessions_key, session_id)
        result = pipe.execute()

        if result[0]:
            logger.info(f"会话 {session_id} 已移除")
            return True
        return False

    def update_session_user_id(self, session_id: str, user_id: str) -> bool:
        session_key = self._get_session_key(session_id)
        session_data = self.redis_client.get(session_key)
        if not session_data:
            return False
        data = json.loads(session_data)
        data['user_id'] = user_id
        data['last_activity'] = datetime.now().isoformat()
        pipe = self.redis_client.pipeline()
        pipe.setex(session_key, Config.REDIS_SESSION_TTL, json.dumps(data, ensure_ascii=False))
        user_sessions_key = self.get_user_sessions_key(user_id)
        pipe.sadd(user_sessions_key, session_id)
        pipe.expire(user_sessions_key, Config.REDIS_SESSION_TTL + 3600)
        pipe.execute()
        logger.info(f"会话 {session_id} 已绑定用户 {user_id}")
        return True

    def _ensure_session_exists(self, session_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        session_key = self._get_session_key(session_id)
        session_data = self.redis_client.get(session_key)
        if session_data:
            try:
                return json.loads(session_data)
            except Exception:
                logger.warning(f"会话数据损坏，重建空会话: {session_id}")

        now_iso = datetime.now().isoformat()
        data = {
            'session_id': session_id,
            'plan_id': session_id,
            'user_id': user_id,
            'departure_location': None,
            'travel_mode': None,
            'group_size': None,
            'budget_range': None,
            'travel_days': None,
            'heritage_ids': [],
            'heritage_names': [],
            'special_requirements': [],
            'current_plan': {},
            'original_plan': {},
            'itinerary_summary': None,
            'weather_info': None,
            'selected_heritage_items': [],
            'location_coordinates': {},
            'budget_constraints': {},
            'time_constraints': {},
            'conversation_history': [],
            'created_at': now_iso,
            'last_updated': now_iso,
            'last_activity': now_iso,
            'edit_count': 0,
        }
        score = datetime.fromisoformat(now_iso).timestamp()
        pipe = self.redis_client.pipeline()
        pipe.setex(session_key, Config.REDIS_SESSION_TTL, json.dumps(data, ensure_ascii=False))
        pipe.zadd(self.session_index_key, {session_id: score})
        pipe.expire(self.session_index_key, Config.REDIS_SESSION_TTL + 3600)
        if user_id:
            user_sessions_key = self.get_user_sessions_key(user_id)
            pipe.sadd(user_sessions_key, session_id)
            pipe.expire(user_sessions_key, Config.REDIS_SESSION_TTL + 3600)
        pipe.execute()
        logger.info(f"自动创建缺失会话: {session_id}, user_id={user_id}")
        return data

    def add_conversation(self, session_id: str, role: str, content: str, user_id: Optional[str] = None, tool_interactions: list = None):
        data = self._ensure_session_exists(session_id, user_id=user_id)
        if data is None:
            return

        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if tool_interactions:
            turn["tool_interactions"] = tool_interactions
        if data.get('conversation_history') is None:
            data['conversation_history'] = []
        data['conversation_history'].append(turn)
        data['last_activity'] = datetime.now().isoformat()
        session_key = self._get_session_key(session_id)
        self.redis_client.setex(session_key, Config.REDIS_SESSION_TTL, json.dumps(data, ensure_ascii=False))

        try:
            if self.conversation_service:
                self.conversation_service.append_message(
                    session_id=session_id,
                    role=role,
                    content=content,
                    message_type="text",
                    extra_data={"user_id": data.get('user_id')} if data.get('user_id') else None,
                    sync_session_history=False
                )
        except Exception as e:
            logger.warning(f"保存对话记录失败: {e}")

    def update_session_plan(self, session_id: str, new_plan: Dict[str, Any]) -> bool:
        return self.update_session(session_id, new_plan)

    def get_optimized_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.get_session(session_id)
        if not session:
            return None

        return {
            'session_id': session.session_id,
            'plan_id': session.plan_id,
            'weather_info': session.weather_info,
            'heritage_items': session.selected_heritage_items,
            'location': session.location_coordinates,
            'budget': session.budget_constraints,
            'time_constraints': session.time_constraints,
            'edit_count': session.edit_count,
            'last_updated': session.last_updated
        }

    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """清理过期会话索引

        Args:
            max_age_hours: 超过此时间的会话视为过期，从索引中移除
        """
        try:
            import time
            cutoff = time.time() - (max_age_hours * 3600)

            session_ids = self.redis_client.zrangebyscore(
                self.session_index_key, '-inf', cutoff
            )
            removed_count = 0

            for session_id in session_ids:
                session_key = self._get_session_key(session_id)
                self.redis_client.delete(session_key)
                self.redis_client.zrem(self.session_index_key, session_id)
                removed_count += 1

            if removed_count > 0:
                logger.info(f"清理了 {removed_count} 个过期会话 (max_age={max_age_hours}h)")
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")

    async def _cleanup_oldest_sessions_redis(self, count: int):
        try:
            oldest_sessions = self.redis_client.zrange(
                self.session_index_key, 0, count - 1
            )
            for session_id in oldest_sessions:
                self.remove_session(session_id)
                logger.info(f"清理最旧会话: {session_id}")
        except Exception as e:
            logger.error(f"清理最旧会话时发生错误: {str(e)}")

    def _cleanup_oldest_sessions(self, count: int):
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._cleanup_oldest_sessions_redis(count))
            else:
                loop.run_until_complete(self._cleanup_oldest_sessions_redis(count))
        except Exception as e:
            logger.error(f"清理最旧会话时发生错误: {str(e)}")

    def get_session_stats(self) -> Dict[str, Any]:
        try:
            total_sessions = self.redis_client.zcard(self.session_index_key)

            one_hour_ago = (datetime.now() - timedelta(hours=1)).timestamp()
            active_sessions = self.redis_client.zcount(
                self.session_index_key, one_hour_ago, '+inf'
            )

            total_edits = 0
            session_ids = self.redis_client.zrange(self.session_index_key, 0, -1)
            for session_id in session_ids:
                session = self.get_session(session_id)
                if session:
                    total_edits += session.edit_count

            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'max_sessions': self.max_sessions,
                'total_edits': total_edits,
                'average_edits_per_session': total_edits / max(total_sessions, 1),
                'storage_mode': 'redis'
            }
        except Exception as e:
            logger.error(f"获取会话统计信息失败: {str(e)}")
            return {
                'total_sessions': 0,
                'active_sessions': 0,
                'max_sessions': self.max_sessions,
                'total_edits': 0,
                'average_edits_per_session': 0,
                'storage_mode': 'redis',
                'error': str(e)
            }

    def health_check(self) -> Dict[str, Any]:
        try:
            self.redis_client.ping()
            info = self.redis_client.info()
            return {
                'status': 'healthy',
                'redis_version': info.get('redis_version'),
                'connected_clients': info.get('connected_clients'),
                'used_memory_human': info.get('used_memory_human'),
                'total_sessions': self.redis_client.zcard(self.session_index_key)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


# ── 全局 Redis 会话池单例 ──

_session_pool_instance = None


def get_redis_session_pool() -> SessionPool:
    """获取 Redis 会话池单例"""
    global _session_pool_instance
    if _session_pool_instance is None:
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis库未安装，L1热数据存储不可用。请安装 redis 包。")
        _session_pool_instance = RedisSessionPool()
        logger.info("使用Redis会话存储 (L1)")
    return _session_pool_instance


def reset_session_pool():
    """重置会话池实例（用于测试）"""
    global _session_pool_instance
    _session_pool_instance = None
