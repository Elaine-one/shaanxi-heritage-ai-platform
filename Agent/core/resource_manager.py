# -*- coding: utf-8 -*-
"""
资源管理器
统一管理所有资源的生命周期
"""

import asyncio
from typing import Dict, Any, Set
from datetime import datetime, timedelta
from loguru import logger


class ResourceManager:
    """统一资源管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._resources: Dict[str, Any] = {}
        self._cleanup_tasks: Set[asyncio.Task] = set()
        self._shutdown_event = asyncio.Event()
        
        self._initialized = True
    
    def register(self, name: str, resource: Any, cleanup_func: callable = None):
        """注册资源"""
        self._resources[name] = {
            'resource': resource,
            'cleanup_func': cleanup_func,
            'registered_at': datetime.now()
        }
    
    async def cleanup_all(self):
        """清理所有资源（仅在关闭时调用）"""
        logger.info("开始清理资源...")
        
        try:
            from Agent.memory.session import get_session_pool
            session_pool = get_session_pool()
            session_pool.cleanup_expired_sessions(max_age_hours=12)
        except Exception as e:
            logger.warning(f"会话清理失败: {e}")
        
        try:
            from Agent.agent.travel_planner import get_travel_planner
            planner = get_travel_planner()
            planner.cleanup_old_progress(hours=1)
        except Exception as e:
            logger.warning(f"规划进度清理失败: {e}")
        
        try:
            from Agent.api.app import progress_callbacks
            cutoff = datetime.now() - timedelta(hours=1)
            expired = [
                k for k, v in progress_callbacks.items()
                if v.get('start_time') and datetime.fromisoformat(v['start_time']) < cutoff
            ]
            for k in expired:
                del progress_callbacks[k]
        except Exception as e:
            logger.warning(f"进度缓存清理失败: {e}")
        
        logger.info("资源清理完成")
    
    async def start_scheduler(self, interval: int = 300):
        """启动定时清理（静默运行，不输出日志）"""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=interval
                )
            except asyncio.TimeoutError:
                pass
            except Exception:
                await asyncio.sleep(60)
    
    async def shutdown(self):
        """优雅关闭"""
        logger.info("开始优雅关闭...")
        
        self._shutdown_event.set()
        
        for task in self._cleanup_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        await self.cleanup_all()
        
        for name, resource_info in self._resources.items():
            cleanup_func = resource_info.get('cleanup_func')
            if cleanup_func:
                try:
                    if asyncio.iscoroutinefunction(cleanup_func):
                        await cleanup_func()
                    else:
                        cleanup_func()
                except Exception as e:
                    logger.error(f"清理资源 {name} 失败: {e}")
        
        try:
            from Agent.services.weather import get_weather_service
            weather_service = get_weather_service()
            if weather_service:
                await weather_service.close()
        except Exception as e:
            logger.warning(f"关闭天气服务失败: {e}")
        
        try:
            from Agent.services.mcp_client import get_mcp_client
            mcp_client = get_mcp_client()
            if mcp_client:
                await mcp_client.close()
        except Exception as e:
            logger.warning(f"关闭MCP客户端失败: {e}")
        
        try:
            from Agent.services.mcp_protocol_client import get_mcp_client as get_protocol_client
            protocol_client = await get_protocol_client()
            if protocol_client and protocol_client._initialized:
                await protocol_client.close()
        except Exception as e:
            logger.warning(f"关闭MCP协议客户端失败: {e}")
        
        try:
            from Agent.memory.knowledge_graph import get_knowledge_graph
            kg = get_knowledge_graph()
            if kg:
                kg.close()
        except Exception as e:
            logger.warning(f"关闭知识图谱失败: {e}")
        
        logger.info("优雅关闭完成")


_resource_manager = None


def get_resource_manager() -> ResourceManager:
    """获取资源管理器单例"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager
