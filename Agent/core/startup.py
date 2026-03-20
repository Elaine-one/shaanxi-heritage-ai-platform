# -*- coding: utf-8 -*-
"""
启动初始化模块
负责服务启动时的并行初始化、数据同步、健康检查等
"""

import json
import hashlib
import aiohttp
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
from loguru import logger


class StartupManager:
    """
    启动管理器
    负责并行初始化各个组件，优化启动速度
    """
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sync_status_file = self.data_dir / "sync_status.json"
        self.sync_status = self._load_sync_status()
    
    def _load_sync_status(self) -> Dict[str, Any]:
        """加载同步状态"""
        try:
            if self.sync_status_file.exists():
                with open(self.sync_status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"加载同步状态失败: {e}")
        return {
            'last_sync': None,
            'heritage_count': 0,
            'data_hash': None
        }
    
    def _save_sync_status(self):
        """保存同步状态"""
        try:
            with open(self.sync_status_file, 'w', encoding='utf-8') as f:
                json.dump(self.sync_status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存同步状态失败: {e}")
    
    def _compute_data_hash(self, heritage_list: List[Dict]) -> str:
        """计算数据哈希值，用于检测变化"""
        if not heritage_list:
            return ""
        
        data_str = json.dumps(
            [(h.get('id'), h.get('name'), h.get('updated_at', '')) for h in heritage_list],
            sort_keys=True
        )
        return hashlib.md5(data_str.encode()).hexdigest()
    
    async def initialize_all(self) -> Dict[str, Any]:
        """并行初始化所有组件"""
        logger.info("开始并行初始化...")
        start_time = datetime.now()
        
        results = {}
        
        try:
            result = await self._init_llm()
            results['llm'] = {'success': True, 'result': result}
            logger.info("✓ llm 初始化完成")
        except Exception as e:
            results['llm'] = {'success': False, 'error': str(e)}
            logger.error(f"✗ llm 初始化失败: {e}")
        
        try:
            result = await self._init_knowledge_graph()
            results['knowledge_graph'] = {'success': True, 'result': result}
            logger.info("✓ knowledge_graph 初始化完成")
        except Exception as e:
            results['knowledge_graph'] = {'success': False, 'error': str(e)}
            logger.error(f"✗ knowledge_graph 初始化失败: {e}")
        
        try:
            result = await self._init_vector_store()
            results['vector_store'] = {'success': True, 'result': result}
            logger.info("✓ vector_store 初始化完成")
        except Exception as e:
            results['vector_store'] = {'success': False, 'error': str(e)}
            logger.error(f"✗ vector_store 初始化失败: {e}")
        
        try:
            result = await self._init_session_pool()
            results['session_pool'] = {'success': True, 'result': result}
            logger.info("✓ session_pool 初始化完成")
        except Exception as e:
            results['session_pool'] = {'success': False, 'error': str(e)}
            logger.error(f"✗ session_pool 初始化失败: {e}")
        
        try:
            result = await self._init_mcp_client()
            results['mcp_client'] = {'success': True, 'result': result}
            logger.info("✓ mcp_client 初始化完成")
        except Exception as e:
            results['mcp_client'] = {'success': False, 'error': str(e)}
            logger.error(f"✗ mcp_client 初始化失败: {e}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"并行初始化完成，耗时 {elapsed:.2f}s")
        
        return results
    
    async def _init_llm(self) -> Dict[str, Any]:
        """初始化 LLM"""
        from Agent.models.llm_factory import get_llm
        
        llm = get_llm()
        
        return {
            'provider': getattr(llm, 'model_name', 'unknown'),
            'initialized': True
        }
    
    async def _init_knowledge_graph(self) -> Dict[str, Any]:
        """初始化知识图谱连接"""
        from Agent.memory.knowledge_graph import get_knowledge_graph
        
        kg = get_knowledge_graph()
        if kg and kg.is_connected():
            return {
                'connected': True
            }
        return {
            'connected': False
        }
    
    async def _init_vector_store(self) -> Dict[str, Any]:
        """初始化向量数据库"""
        from Agent.memory.vector_store import get_vector_store
        
        vs = get_vector_store()
        if vs:
            stats = vs.get_collection_stats()
            return {
                'available': True,
                'stats': stats
            }
        return {
            'available': False,
            'stats': {}
        }
    
    async def _init_session_pool(self) -> Dict[str, Any]:
        """初始化会话池"""
        from Agent.memory.session import get_session_pool
        
        sp = get_session_pool()
        return {
            'initialized': True
        }
    
    async def _init_mcp_client(self) -> Dict[str, Any]:
        """初始化 MCP 客户端"""
        try:
            from Agent.services.mcp_protocol_client import init_mcp_client, get_mcp_client
            
            success = await init_mcp_client()
            if success:
                client = await get_mcp_client()
                tools_count = len(client.tools) if client._initialized else 0
            else:
                tools_count = 0
            
            return {
                'initialized': success,
                'tools_count': tools_count
            }
        except Exception as e:
            logger.warning(f"MCP 客户端初始化失败: {e}")
            return {
                'initialized': False,
                'tools_count': 0,
                'error': str(e)
            }
    
    async def auto_sync_heritage_data(self, force: bool = False) -> Dict[str, Any]:
        """自动同步非遗数据到知识图谱和向量数据库"""
        from Agent.config.settings import config
        
        if not config.HERITAGE_DATA_SYNC_ENABLED:
            logger.info("数据同步已禁用，跳过同步（HERITAGE_DATA_SYNC_ENABLED=false）")
            return {
                'success': True,
                'skipped': True,
                'reason': '数据同步已禁用'
            }
        
        logger.info("开始自动同步非遗数据...")
        start_time = datetime.now()
        
        try:
            heritage_list = await self._fetch_heritage_from_mysql()
            
            if not heritage_list:
                return {
                    'success': False,
                    'error': '未获取到非遗数据'
                }
            
            current_hash = self._compute_data_hash(heritage_list)
            stored_hash = self.sync_status.get('data_hash')
            
            kg_empty = await self._check_knowledge_graph_empty()
            
            if not force and current_hash == stored_hash and not kg_empty:
                logger.info("数据无变化，跳过同步")
                return {
                    'success': True,
                    'skipped': True,
                    'reason': '数据无变化'
                }
            
            if kg_empty:
                logger.info("知识图谱为空，强制同步")
            
            logger.info(f"检测到数据变化，开始同步 {len(heritage_list)} 条数据...")
            
            kg_result = await self._sync_to_knowledge_graph(heritage_list)
            vs_result = await self._sync_to_vector_store(heritage_list)
            
            self.sync_status = {
                'last_sync': datetime.now().isoformat(),
                'heritage_count': len(heritage_list),
                'data_hash': current_hash
            }
            self._save_sync_status()
            
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"同步完成，耗时 {elapsed:.2f}s")
            
            return {
                'success': True,
                'heritage_count': len(heritage_list),
                'knowledge_graph': kg_result,
                'vector_store': vs_result,
                'elapsed_seconds': elapsed
            }
            
        except Exception as e:
            logger.error(f"自动同步失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _check_knowledge_graph_empty(self) -> bool:
        """检查知识图谱是否为空"""
        from Agent.memory.knowledge_graph import get_knowledge_graph
        
        kg = get_knowledge_graph()
        if not kg or not kg.is_connected():
            return True
        
        try:
            count = kg.get_heritage_count()
            return count == 0
        except:
            return True
    
    async def _fetch_heritage_from_mysql(self) -> List[Dict]:
        """从 MySQL API 获取非遗数据（完整分页获取）"""
        from Agent.config.settings import config
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{config.BACKEND_API_URL}/items/"
                
                all_items = []
                page = 1
                page_size = 100
                total_count = None
                
                while True:
                    params = {
                        'page': page,
                        'page_size': page_size
                    }
                    
                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status != 200:
                            logger.error(f"获取非遗数据失败: {response.status}")
                            break
                        
                        data = await response.json()
                        
                        if isinstance(data, dict) and 'results' in data:
                            items = data['results']
                            if total_count is None:
                                total_count = data.get('count', 0)
                                logger.info(f"数据库共有 {total_count} 条非遗数据")
                            
                            all_items.extend(items)
                            logger.info(f"第 {page} 页获取了 {len(items)} 条数据，累计 {len(all_items)}/{total_count or '?'} 条")
                            
                            next_url = data.get('next')
                            if next_url is None:
                                logger.info("已获取所有页面（无下一页）")
                                break
                            
                            if total_count and len(all_items) >= total_count:
                                logger.info(f"已获取全部数据: {len(all_items)}/{total_count}")
                                break
                            
                        elif isinstance(data, list):
                            items = data
                            all_items.extend(items)
                            if len(items) < page_size:
                                break
                        else:
                            logger.warning(f"未知的响应格式: {type(data)}")
                            break
                        
                        page += 1
                
                logger.info(f"从数据库获取了 {len(all_items)} 条非遗数据")
                return all_items
                
        except Exception as e:
            logger.error(f"获取非遗数据失败: {e}")
            return []
    
    async def _sync_to_knowledge_graph(self, heritage_list: List[Dict]) -> Dict[str, int]:
        """同步到知识图谱"""
        from Agent.memory.knowledge_graph import get_knowledge_graph
        
        kg = get_knowledge_graph()
        if not kg or not kg.is_connected():
            return {'success': False, 'error': '知识图谱未连接'}
        
        categories = set()
        regions = set()
        levels = set()
        batches = set()
        
        for heritage in heritage_list:
            if heritage.get('category'):
                categories.add(heritage['category'])
            if heritage.get('region'):
                regions.add(heritage['region'])
            if heritage.get('level'):
                levels.add(heritage['level'])
            if heritage.get('batch'):
                batches.add(heritage['batch'])
        
        for category in categories:
            kg.create_category_node(category, '')
        for region in regions:
            kg.create_region_node(region, '陕西', '')
        for level in levels:
            kg.create_level_node(level, 0)
        for batch in batches:
            kg.create_batch_node(batch)
        
        heritage_count = 0
        for heritage in heritage_list:
            if kg.create_heritage_node(heritage):
                heritage_count += 1
                kg.build_heritage_relations(
                    heritage_id=heritage['id'],
                    category=heritage.get('category', ''),
                    region=heritage.get('region', ''),
                    level=heritage.get('level', ''),
                    batch=heritage.get('batch', ''),
                    latitude=heritage.get('latitude'),
                    longitude=heritage.get('longitude'),
                    name=heritage.get('name', '')
                )
        
        near_count = kg.build_near_relations(max_distance_km=100)
        
        return {
            'success': True,
            'heritage_count': heritage_count,
            'category_count': len(categories),
            'region_count': len(regions),
            'near_relation_count': near_count
        }
    
    async def _sync_to_vector_store(self, heritage_list: List[Dict]) -> Dict[str, int]:
        """同步到向量数据库"""
        from Agent.memory.vector_store import get_vector_store
        
        vs = get_vector_store()
        if not vs:
            return {'success': False, 'error': '向量数据库不可用'}
        
        vector_count = 0
        for heritage in heritage_list:
            content = self._build_heritage_content(heritage)
            if vs.add_heritage_knowledge(
                heritage_id=heritage['id'],
                name=heritage.get('name', ''),
                content=content,
                metadata={
                    'category': heritage.get('category', ''),
                    'region': heritage.get('region', ''),
                    'level': heritage.get('level', ''),
                    'batch': heritage.get('batch', '')
                }
            ):
                vector_count += 1
        
        return {
            'success': True,
            'vector_count': vector_count
        }
    
    def _build_heritage_content(self, heritage: Dict) -> str:
        """构建非遗内容用于向量化"""
        parts = []
        
        if heritage.get('name'):
            parts.append(f"名称：{heritage['name']}")
        if heritage.get('category'):
            parts.append(f"类别：{heritage['category']}")
        if heritage.get('region'):
            parts.append(f"地区：{heritage['region']}")
        if heritage.get('level'):
            parts.append(f"级别：{heritage['level']}")
        if heritage.get('batch'):
            parts.append(f"批次：{heritage['batch']}")
        if heritage.get('description'):
            parts.append(f"描述：{heritage['description']}")
        if heritage.get('history'):
            parts.append(f"历史渊源：{heritage['history']}")
        if heritage.get('features'):
            parts.append(f"基本特征：{heritage['features']}")
        if heritage.get('value'):
            parts.append(f"重要价值：{heritage['value']}")
        if heritage.get('inheritors'):
            parts.append(f"传承人：{heritage['inheritors']}")
        
        return '\n'.join(parts)
    
    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        return self.sync_status.copy()


_startup_manager_instance = None


def get_startup_manager() -> StartupManager:
    """获取启动管理器单例"""
    global _startup_manager_instance
    if _startup_manager_instance is None:
        _startup_manager_instance = StartupManager()
    return _startup_manager_instance
