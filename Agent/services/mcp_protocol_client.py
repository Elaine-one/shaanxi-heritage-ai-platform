# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) 客户端
连接地图 MCP Server，实现大模型自主调用工具
支持高德地图和百度地图
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any, List, Optional
from loguru import logger


class MCPClient:
    """
    MCP 客户端
    通过 stdio 与 MCP Server 通信，支持大模型自主调用工具
    """
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.tools: List[Dict[str, Any]] = []
        self._request_id = 0
        self._initialized = False
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._reader_task: Optional[asyncio.Task] = None
        self._provider: str = "amap"
        
        logger.info("MCP 客户端初始化")
    
    async def connect_to_map_provider(self, provider: str = None) -> bool:
        """
        连接地图 MCP Server（根据配置选择高德或百度）
        
        Args:
            provider: 地图提供商 amap/baidu，不传则从配置读取
        
        Returns:
            bool: 连接是否成功
        """
        from Agent.config.settings import Config
        
        if provider is None:
            provider = Config.MAP_PROVIDER
        
        self._provider = provider
        
        if provider == "amap":
            return await self.connect_to_amap()
        else:
            return await self.connect_to_baidu_maps(Config.BAIDU_MAP_AK)
    
    async def connect_to_amap(self) -> bool:
        """
        连接高德地图 MCP Server
        
        Returns:
            bool: 连接是否成功
        """
        try:
            from Agent.config.settings import Config
            
            if not Config.AMAP_API_KEY:
                logger.warning("高德地图 API Key 未配置")
                return False
            
            logger.info("使用高德地图 HTTP API 客户端")
            from Agent.services.amap_mcp_client import get_amap_client
            client = get_amap_client()
            self.tools = self._get_amap_tools()
            self._initialized = True
            self._provider = "amap"
            logger.info(f"高德地图 HTTP API 客户端初始化完成，可用工具: {len(self.tools)} 个")
            return True
            
        except Exception as e:
            logger.error(f"连接高德 MCP Server 失败: {e}")
            return False
    
    def _get_amap_tools(self) -> List[Dict[str, Any]]:
        """获取高德地图工具列表（用于HTTP API模式）"""
        return [
            {
                "name": "maps_geo",
                "description": "地理编码：将地址转换为经纬度坐标",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "address": {"type": "string", "description": "待解析的地址"},
                        "city": {"type": "string", "description": "城市名称"}
                    },
                    "required": ["address"]
                }
            },
            {
                "name": "maps_regeocode",
                "description": "逆地理编码：将经纬度坐标转换为地址",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "经纬度坐标，格式：经度,纬度"}
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "maps_direction_driving",
                "description": "驾车路径规划：计算两点之间的驾车路线",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "起点坐标，格式：经度,纬度"},
                        "destination": {"type": "string", "description": "终点坐标，格式：经度,纬度"},
                        "strategy": {"type": "integer", "description": "策略：0-速度优先，1-费用优先，2-距离优先"}
                    },
                    "required": ["origin", "destination"]
                }
            },
            {
                "name": "maps_direction_walking",
                "description": "步行路径规划：计算两点之间的步行路线",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "起点坐标，格式：经度,纬度"},
                        "destination": {"type": "string", "description": "终点坐标，格式：经度,纬度"}
                    },
                    "required": ["origin", "destination"]
                }
            },
            {
                "name": "maps_direction_riding",
                "description": "骑行路径规划：计算两点之间的骑行路线",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "起点坐标，格式：经度,纬度"},
                        "destination": {"type": "string", "description": "终点坐标，格式：经度,纬度"}
                    },
                    "required": ["origin", "destination"]
                }
            },
            {
                "name": "maps_direction_transit",
                "description": "公交路径规划：计算两点之间的公交路线",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {"type": "string", "description": "起点坐标，格式：经度,纬度"},
                        "destination": {"type": "string", "description": "终点坐标，格式：经度,纬度"},
                        "city": {"type": "string", "description": "起点城市"},
                        "cityd": {"type": "string", "description": "终点城市（跨城时必填）"}
                    },
                    "required": ["origin", "destination", "city"]
                }
            },
            {
                "name": "maps_distance",
                "description": "距离测量：计算两点之间的距离",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origins": {"type": "string", "description": "起点坐标，格式：经度,纬度"},
                        "destination": {"type": "string", "description": "终点坐标，格式：经度,纬度"},
                        "type": {"type": "string", "description": "类型：1-驾车，3-步行"}
                    },
                    "required": ["origins", "destination"]
                }
            },
            {
                "name": "maps_text_search",
                "description": "POI关键词搜索：搜索指定区域内的兴趣点",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "keywords": {"type": "string", "description": "搜索关键词"},
                        "city": {"type": "string", "description": "城市名称"},
                        "citylimit": {"type": "boolean", "description": "是否限制城市内"}
                    },
                    "required": ["keywords"]
                }
            },
            {
                "name": "maps_around_search",
                "description": "POI周边搜索：搜索指定位置周边的兴趣点",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "keywords": {"type": "string", "description": "搜索关键词"},
                        "location": {"type": "string", "description": "中心点坐标，格式：经度,纬度"},
                        "radius": {"type": "integer", "description": "搜索半径(米)"},
                        "offset": {"type": "integer", "description": "返回结果数量"}
                    },
                    "required": ["keywords", "location"]
                }
            },
            {
                "name": "maps_weather",
                "description": "天气查询：查询指定城市的天气信息",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市名称或adcode"},
                        "extensions": {"type": "string", "description": "base-实况天气，all-预报天气"}
                    },
                    "required": ["city"]
                }
            },
            {
                "name": "maps_ip_location",
                "description": "IP定位：根据IP地址定位",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "ip": {"type": "string", "description": "IP地址，不传则定位当前请求IP"}
                    },
                    "required": []
                }
            }
        ]
    
    async def connect_to_baidu_maps(self, api_key: str) -> bool:
        """
        连接百度地图 MCP Server
        
        Args:
            api_key: 百度地图 API Key
        
        Returns:
            bool: 连接是否成功
        """
        try:
            import os
            env = os.environ.copy()
            env["BAIDU_MAPS_API_KEY"] = api_key
            
            try:
                import mcp_server_baidu_maps
                command = [sys.executable, "-m", "mcp_server_baidu_maps"]
                logger.info("使用已安装的 mcp-server-baidu-maps")
            except ImportError:
                command = [sys.executable, "-m", "pip", "install", "mcp-server-baidu-maps", "-q"]
                subprocess.run(command, check=True)
                command = [sys.executable, "-m", "mcp_server_baidu_maps"]
                logger.info("已安装 mcp-server-baidu-maps")
            
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1
            )
            
            self._reader_task = asyncio.create_task(self._read_responses())
            
            init_result = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "shaanxi-heritage-agent",
                    "version": "1.0.0"
                }
            })
            
            logger.info(f"MCP initialize 响应: {init_result}")
            
            if init_result.get("status") == "success":
                self._send_notification("notifications/initialized", {})
                
                tools_result = await self._send_request("tools/list", {})
                
                if tools_result.get("status") == "success":
                    result = tools_result.get("result", {})
                    self.tools = result.get("tools", []) if isinstance(result, dict) else []
                    self._initialized = True
                    logger.info(f"MCP 连接成功，可用工具: {len(self.tools)} 个")
                    return True
                else:
                    logger.error(f"MCP tools/list 失败: {tools_result.get('error')}")
            else:
                logger.error(f"MCP initialize 失败: {init_result.get('error')}")
            
            return False
            
        except Exception as e:
            logger.error(f"连接 MCP Server 失败: {e}")
            return False
    
    async def _read_responses(self):
        """异步读取 MCP Server 响应"""
        loop = asyncio.get_event_loop()
        
        while self.process and self.process.poll() is None:
            try:
                line = await loop.run_in_executor(None, self.process.stdout.readline)
                if not line:
                    await asyncio.sleep(0.1)
                    continue
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    response = json.loads(line)
                    
                    if "id" in response:
                        response_id = response["id"]
                        for req_id in list(self._pending_requests.keys()):
                            if str(req_id) == str(response_id):
                                future = self._pending_requests.pop(req_id)
                                if not future.done():
                                    future.set_result(response)
                                break
                except json.JSONDecodeError:
                    logger.warning(f"无法解析 MCP 响应: {line[:100]}")
                    
            except Exception as e:
                logger.error(f"读取 MCP 响应错误: {e}")
                await asyncio.sleep(0.1)
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """发送 MCP 请求"""
        if not self.process or self.process.poll() is not None:
            return {"status": "error", "error": "MCP Server 未运行"}
        
        self._request_id += 1
        request_id = self._request_id
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            request_str = json.dumps(request) + "\n"
            self.process.stdin.write(request_str)
            self.process.stdin.flush()
            
            try:
                response = await asyncio.wait_for(future, timeout=60.0)
                return {
                    "status": "success",
                    "result": response.get("result"),
                    "error": response.get("error")
                }
            except asyncio.TimeoutError:
                self._pending_requests.pop(request_id, None)
                logger.error(f"MCP 请求超时: {method}")
                return {"status": "error", "error": "请求超时"}
                
        except Exception as e:
            self._pending_requests.pop(request_id, None)
            return {"status": "error", "error": str(e)}
    
    def _send_notification(self, method: str, params: Dict[str, Any]):
        """发送 MCP 通知（不需要响应）"""
        if not self.process or self.process.poll() is not None:
            return
        
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        
        try:
            notification_str = json.dumps(notification) + "\n"
            self.process.stdin.write(notification_str)
            self.process.stdin.flush()
        except Exception as e:
            logger.error(f"发送 MCP 通知失败: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            Dict: 工具执行结果
        """
        if not self._initialized:
            return {"success": False, "error": "MCP 未初始化"}
        
        if self._provider == "amap" and self.process is None:
            return await self._call_amap_http_tool(tool_name, arguments)
        
        result = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        if result.get("status") == "success":
            tool_result = result.get("result", {})
            content = tool_result.get("content", [])
            
            if content and isinstance(content, list):
                text_content = ""
                for item in content:
                    if item.get("type") == "text":
                        text_content += item.get("text", "")
                
                try:
                    return json.loads(text_content)
                except json.JSONDecodeError:
                    return {"success": True, "data": text_content}
            
            return {"success": True, "data": tool_result}
        
        return {"success": False, "error": result.get("error", "调用失败")}
    
    async def _call_amap_http_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用高德 HTTP API 工具
        """
        try:
            from Agent.services.amap_mcp_client import get_amap_client
            client = get_amap_client()
            
            tool_method_map = {
                'maps_geo': client.maps_geo,
                'maps_regeocode': client.maps_regeocode,
                'maps_direction_driving': client.maps_direction_driving,
                'maps_direction_walking': client.maps_direction_walking,
                'maps_direction_riding': client.maps_direction_riding,
                'maps_direction_transit': client.maps_direction_transit,
                'maps_distance': client.maps_distance,
                'maps_text_search': client.maps_text_search,
                'maps_around_search': client.maps_around_search,
                'maps_weather': client.maps_weather,
                'maps_ip_location': client.maps_ip_location,
            }
            
            if tool_name in tool_method_map:
                method = tool_method_map[tool_name]
                result = await method(**arguments)
                return result
            else:
                return {"success": False, "error": f"未知工具: {tool_name}"}
                
        except Exception as e:
            logger.error(f"调用高德 HTTP API 工具失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        获取供 LLM 使用的工具列表
        
        Returns:
            List: 工具列表，格式兼容 OpenAI function calling
        """
        llm_tools = []
        
        for tool in self.tools:
            llm_tools.append({
                "type": "function",
                "function": {
                    "name": tool.get("name"),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("inputSchema", {})
                }
            })
        
        return llm_tools
    
    def get_tool_descriptions(self) -> str:
        """
        获取工具描述文本，用于 ReAct 提示词
        
        Returns:
            str: 工具描述文本
        """
        descriptions = []
        
        for tool in self.tools:
            name = tool.get("name", "")
            desc = tool.get("description", "")
            schema = tool.get("inputSchema", {})
            
            required = schema.get("required", [])
            properties = schema.get("properties", {})
            
            params_desc = []
            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                is_required = param_name in required
                req_mark = "*" if is_required else ""
                params_desc.append(f"    {param_name}{req_mark} ({param_type}): {param_desc}")
            
            descriptions.append(f"- {name}: {desc}\n  参数:\n" + "\n".join(params_desc))
        
        return "\n\n".join(descriptions)
    
    async def close(self):
        """关闭 MCP 连接"""
        self._initialized = False
        
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await asyncio.wait_for(self._reader_task, timeout=2.0)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                pass
            self._reader_task = None
        
        if self.process:
            try:
                self.process.stdin.close()
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=2)
            except Exception as e:
                logger.warning(f"终止 MCP 进程时出错: {e}")
                try:
                    self.process.kill()
                except:
                    pass
            
            self.process = None
        
        self._pending_requests.clear()
        logger.info("MCP 连接已关闭")


_mcp_client: Optional[MCPClient] = None


async def get_mcp_client() -> MCPClient:
    """
    获取 MCP 客户端单例
    
    Returns:
        MCPClient: MCP 客户端实例
    """
    global _mcp_client
    
    if _mcp_client is None:
        
        _mcp_client = MCPClient()
        
        success = await _mcp_client.connect_to_map_provider()
        if not success:
            logger.warning("MCP 连接失败，将使用降级方案")
    
    return _mcp_client


async def init_mcp_client() -> bool:
    """
    初始化 MCP 客户端
    
    Returns:
        bool: 是否初始化成功
    """
    try:
        client = await get_mcp_client()
        return client._initialized
    except Exception as e:
        logger.error(f"初始化 MCP 客户端失败: {e}")
        return False
