# -*- coding: utf-8 -*-
"""
高德地图 MCP 服务
使用 langchain-mcp-adapters 连接高德 MCP Server 2.0
"""

import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger

_mcp_client = None
_mcp_tools: List[Any] = []


class AmapMCPService:
    """
    高德地图 MCP 服务封装
    使用 langchain-mcp-adapters 的 MultiServerMCPClient
    """
    
    MCP_CONNECT_TIMEOUT = 10
    
    def __init__(self):
        self._client = None
        self._tools: List[Any] = []
        self._initialized = False
        self._session = None
        
    async def initialize(self) -> bool:
        """
        初始化 MCP 客户端
        
        Returns:
            bool: 是否初始化成功
        """
        if self._initialized:
            return True
            
        try:
            from Agent.config.settings import Config
            
            if not Config.AMAP_API_KEY:
                logger.warning("AMAP_API_KEY 未配置，MCP 地图工具将不可用")
                return False
            
            from langchain_mcp_adapters.client import MultiServerMCPClient
            
            mcp_url = f"{Config.AMAP_MCP_URL}?key={Config.AMAP_API_KEY}"
            
            logger.info(f"正在连接高德 MCP Server: {Config.AMAP_MCP_URL}")
            
            self._client = MultiServerMCPClient(
                connections={
                    "amap-maps": {
                        "url": mcp_url,
                        "transport": "sse"
                    }
                }
            )
            
            try:
                tools = await asyncio.wait_for(
                    self._client.get_tools(),
                    timeout=self.MCP_CONNECT_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning(f"高德 MCP Server 连接超时（{self.MCP_CONNECT_TIMEOUT}秒），将使用本地工具")
                return False
            
            if not tools:
                logger.warning("高德 MCP Server 返回空工具列表")
                return False
            
            self._tools = tools
            self._initialized = True
            logger.info(f"高德 MCP Server 连接成功，可用工具: {len(self._tools)} 个")
            
            for tool in self._tools:
                tool_name = getattr(tool, 'name', str(tool))
                logger.info(f"  - {tool_name}")
            
            return True
            
        except ImportError as e:
            logger.warning(f"langchain-mcp-adapters 未安装: {e}")
            return False
        except Exception as e:
            logger.warning(f"连接高德 MCP Server 失败: {e}")
            return False
    
    def get_tools(self) -> List[Any]:
        """
        获取 MCP 工具列表
        
        Returns:
            List: LangChain 工具列表
        """
        return self._tools
    
    def get_tool_names(self) -> List[str]:
        """
        获取工具名称列表
        
        Returns:
            List[str]: 工具名称列表
        """
        return [getattr(t, 'name', str(t)) for t in self._tools]
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        """
        获取工具信息列表
        
        Returns:
            List[Dict]: 工具信息列表
        """
        result = []
        for tool in self._tools:
            info = {
                'name': getattr(tool, 'name', 'unknown'),
                'description': getattr(tool, 'description', ''),
            }
            if hasattr(tool, 'args_schema'):
                info['args_schema'] = tool.args_schema
            result.append(info)
        return result
    
    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._initialized
    
    async def close(self):
        """关闭连接"""
        if self._client:
            try:
                pass
            except Exception as e:
                logger.warning(f"关闭 MCP 客户端时出错: {e}")
            finally:
                self._client = None
                self._session = None
                self._initialized = False


_amap_mcp_service: Optional[AmapMCPService] = None


async def get_amap_mcp_service() -> AmapMCPService:
    """
    获取高德 MCP 服务单例
    
    Returns:
        AmapMCPService: MCP 服务实例
    """
    global _amap_mcp_service
    
    if _amap_mcp_service is None:
        _amap_mcp_service = AmapMCPService()
        await _amap_mcp_service.initialize()
    
    return _amap_mcp_service


async def get_mcp_tools() -> List[Any]:
    """
    获取 MCP 工具列表
    
    Returns:
        List: LangChain 工具列表
    """
    service = await get_amap_mcp_service()
    return service.get_tools()


async def init_amap_mcp() -> bool:
    """
    初始化高德 MCP 服务
    
    Returns:
        bool: 是否初始化成功
    """
    try:
        service = await get_amap_mcp_service()
        return service.is_initialized
    except Exception as e:
        logger.error(f"初始化高德 MCP 服务失败: {e}")
        return False
