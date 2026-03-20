# -*- coding: utf-8 -*-
"""
MCP 工具适配器
将 MCP 工具适配到现有工具系统，支持大模型自主调用
"""

from typing import Dict, Any, List, Optional
from loguru import logger
from Agent.tools.base import BaseTool


class MCPToolAdapter(BaseTool):
    """
    MCP 工具适配器
    将 MCP Server 提供的工具适配为系统内部工具
    """
    
    def __init__(self, tool_info: Dict[str, Any], mcp_client):
        """
        初始化 MCP 工具适配器
        
        Args:
            tool_info: MCP 工具信息
            mcp_client: MCP 客户端实例
        """
        self._name = tool_info.get("name", "unknown")
        self._description = tool_info.get("description", "")
        self._input_schema = tool_info.get("inputSchema", {})
        self._mcp_client = mcp_client
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return self._input_schema
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行 MCP 工具调用
        
        Args:
            **kwargs: 工具参数
        
        Returns:
            Dict[str, Any]: 工具执行结果
        """
        try:
            result = await self._mcp_client.call_tool(self._name, kwargs)
            
            if result.get('success'):
                return result
            else:
                return {
                    'success': False,
                    'error': result.get('error', '工具调用失败')
                }
        except Exception as e:
            logger.error(f"MCP 工具 {self._name} 执行失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class MCPToolRegistry:
    """
    MCP 工具注册中心
    动态注册 MCP Server 提供的所有工具
    """
    
    def __init__(self):
        self._mcp_tools: Dict[str, MCPToolAdapter] = {}
        self._mcp_client = None
        self._initialized = False
        
        logger.info("MCP 工具注册中心初始化")
    
    async def initialize(self, mcp_client) -> bool:
        """
        初始化 MCP 工具注册
        
        Args:
            mcp_client: MCP 客户端实例
        
        Returns:
            bool: 是否初始化成功
        """
        if self._initialized:
            return True
        
        self._mcp_client = mcp_client
        
        tools = mcp_client.tools
        for tool_info in tools:
            tool_name = tool_info.get("name")
            if tool_name:
                adapter = MCPToolAdapter(tool_info, mcp_client)
                self._mcp_tools[tool_name] = adapter
                logger.info(f"注册 MCP 工具: {tool_name}")
        
        self._initialized = True
        logger.info(f"MCP 工具注册完成，共 {len(self._mcp_tools)} 个工具")
        
        return True
    
    def get_tool(self, name: str) -> Optional[MCPToolAdapter]:
        """获取 MCP 工具"""
        return self._mcp_tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有 MCP 工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "source": "mcp"
            }
            for tool in self._mcp_tools.values()
        ]
    
    def get_tool_names(self) -> List[str]:
        """获取所有 MCP 工具名称"""
        return list(self._mcp_tools.keys())
    
    def get_tools_for_react(self) -> str:
        """获取 ReAct 格式的工具描述"""
        descriptions = []
        
        for tool in self._mcp_tools.values():
            name = tool.name
            desc = tool.description
            schema = tool.parameters
            
            required = schema.get("required", [])
            properties = schema.get("properties", {})
            
            params_desc = []
            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                is_required = "*" if param_name in required else ""
                params_desc.append(f"  - {param_name}{is_required} ({param_type}): {param_desc}")
            
            descriptions.append(f"- {name}: {desc}\n  参数:\n" + "\n".join(params_desc))
        
        return "\n\n".join(descriptions)


_mcp_tool_registry: Optional[MCPToolRegistry] = None


async def get_mcp_tool_registry() -> MCPToolRegistry:
    """获取 MCP 工具注册中心单例"""
    global _mcp_tool_registry
    
    if _mcp_tool_registry is None:
        _mcp_tool_registry = MCPToolRegistry()
        
        from Agent.services.mcp_protocol_client import get_mcp_client
        mcp_client = await get_mcp_client()
        
        if mcp_client._initialized:
            await _mcp_tool_registry.initialize(mcp_client)
    
    return _mcp_tool_registry


async def init_mcp_tools() -> bool:
    """
    初始化 MCP 工具
    
    Returns:
        bool: 是否初始化成功
    """
    try:
        registry = await get_mcp_tool_registry()
        return registry._initialized
    except Exception as e:
        logger.error(f"初始化 MCP 工具失败: {e}")
        return False
