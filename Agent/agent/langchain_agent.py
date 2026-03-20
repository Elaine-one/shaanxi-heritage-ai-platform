# -*- coding: utf-8 -*-
"""
LangGraph Agent 封装
使用 langchain.agents.create_agent 实现 ReAct Agent
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any, List

from loguru import logger

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage


SYSTEM_PROMPT = """你是陕西非遗旅游助手，热情友好，回复自然流畅。

# 规划上下文

上下文已包含：出发地、已选非遗项目（名称、ID、地区、经纬度）、出行方式

# 工具选择规则

## 路线查询
用户问"路线"、"怎么去"时：
1. 先调用 route_preview 获取游览顺序
2. 根据 travel_mode 调用交通工具：
   - driving → driving_route
   - transit/public → transit_route
   - riding → riding_route

## 天气查询
用户问"天气"时：
- 调用 maps_weather
- 用户说"都需要"时查询所有非遗所在地区

## 禁止事项
- 不要搜索已选非遗项目
- 不要使用非遗名称作为目的地参数

## 参数使用规则

调用交通规划工具时：
- origin/destination 使用城市名称（如"西安市"、"宝鸡市"）
- 或使用上下文中的经纬度格式"经度,纬度"
- 例如：上下文显示"凤翔木版年画(经纬度:107.3969,34.5215)"
- 调用时使用：origin="107.3969,34.5215" 或 origin="宝鸡市"

# 输出格式

- 使用 Markdown 格式
- 直接回答，不要说"根据您的需求"等客套话
- 简洁明了，突出重点
- 使用表格展示路线、天气等结构化信息

## 表格示例

路线表格：
| 路段 | 距离 | 时间 | 费用 |
|------|------|------|------|
| 兴平市 → 凤翔 | 132km | 1.5h | ¥50 |

天气表格：
| 城市 | 日期 | 天气 | 温度 |
|------|------|------|------|
| 西安 | 3/16 | 晴 | 5~-10°C |
"""


class LangChainAgentExecutor:
    """
    LangGraph ReAct Agent 封装
    
    LangGraph create_react_agent 自动管理:
    - Thought/Action/Action Input/Observation 循环
    - 工具调用和结果处理
    - 迭代终止
    """
    
    MAX_ITERATIONS = 30
    
    def __init__(self):
        self._llm: Optional['ChatOpenAI'] = None
        self._agent: Optional[Any] = None
        self._tools: List = []
        self._initialized = False
        
        logger.info("LangChainAgentExecutor 初始化")
    
    @property
    def llm(self) -> 'ChatOpenAI':
        """延迟加载 LLM"""
        if self._llm is None:
            from Agent.config import config
            llm_config = config.get_llm_config()
            
            self._llm = ChatOpenAI(
                api_key=llm_config.api_key,
                base_url=llm_config.base_url,
                model=llm_config.model,
                temperature=llm_config.temperature or 0.7,
                max_tokens=llm_config.max_tokens or 4096,
                request_timeout=600,
                max_retries=2,
                streaming=True,
            )
            
            logger.info(f"LangChain LLM 初始化完成（流式模式）: {llm_config.model}")
        
        return self._llm
    
    async def initialize(self, context: 'UnifiedContext' = None) -> bool:
        """初始化 Agent"""
        if self._initialized:
            return True
        
        from Agent.tools.langchain_tools import get_langchain_tools
        
        self._tools = get_langchain_tools()
        
        if not self._tools:
            logger.error("没有可用的 LangChain 工具")
            return False
        
        self._agent = create_agent(
            model=self.llm,
            tools=self._tools,
            system_prompt=SYSTEM_PROMPT,
        )
        
        self._initialized = True
        logger.info(f"LangGraph Agent 初始化完成，工具数量: {len(self._tools)}")
        return True
    
    async def run_stream(
        self,
        user_input: str,
        context: 'UnifiedContext'
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式运行 Agent - 真正的实时流式输出，支持状态反馈"""
        from Agent.context.unified_context import set_current_context, clear_current_context
        
        set_current_context(context)
        
        try:
            if not await self.initialize(context):
                yield {"type": "content", "content": "抱歉，系统初始化失败，请稍后重试。"}
                return
            
            messages = self._build_messages(user_input, context)
            
            logger.info(f"🚀 LangGraph Agent 开始处理: {user_input[:50]}...")
            logger.info("=" * 60)
            
            yield {"type": "status", "status": "thinking", "content": "正在思考..."}
            
            try:
                final_result = {"messages": messages}
                step_count = 0
                last_content = ""
                yielded_content = ""
                
                async for event in self._agent.astream(
                    {"messages": messages},
                    {"recursion_limit": self.MAX_ITERATIONS},
                    stream_mode="updates"
                ):
                    step_count += 1
                    
                    for node_name, node_output in event.items():
                        if "messages" in node_output:
                            msgs = node_output["messages"]
                            last_msg = msgs[-1] if msgs else None
                            
                            if last_msg:
                                msg_type = type(last_msg).__name__
                                
                                if msg_type == "AIMessage":
                                    if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                                        for tc in last_msg.tool_calls:
                                            tool_name = tc['name']
                                            logger.info(f"📌 步骤 {step_count}: 调用工具 [{tool_name}]")
                                            logger.info(f"   参数: {tc['args']}")
                                            yield {
                                                "type": "thinking",
                                                "content": "正在思考..."
                                            }
                                    elif last_msg.content and last_msg.content != last_content:
                                        new_content = last_msg.content[len(yielded_content):]
                                        if new_content:
                                            yield {"type": "content", "content": new_content}
                                            yielded_content = last_msg.content
                                        last_content = last_msg.content
                                        logger.info(f"💭 步骤 {step_count}: 输出内容 ({len(new_content)} 字符)")
                                
                                elif msg_type == "ToolMessage":
                                    content = last_msg.content[:200] if len(last_msg.content) > 200 else last_msg.content
                                    logger.info(f"📋 步骤 {step_count}: 工具返回结果")
                                    logger.info(f"   {content}")
                        
                        final_result = {"messages": node_output.get("messages", [])}
                
                logger.info("=" * 60)
                logger.info(f"📊 Agent 执行完成，共 {step_count} 步")
                
                if not yielded_content:
                    output = self._extract_output(final_result)
                    if output:
                        async for chunk in self._stream_llm_direct(output):
                            yield {"type": "content", "content": chunk}
                    else:
                        yield {"type": "content", "content": "抱歉，我无法处理您的请求，请尝试换一种方式提问。"}
                
                yield {"type": "done"}
                    
            except Exception as e:
                from langgraph.errors import GraphRecursionError
                
                if isinstance(e, GraphRecursionError) or "Recursion limit" in str(e):
                    logger.warning(f"⚠️ 达到递归限制，共 {step_count} 步")
                    yield {"type": "content", "content": "抱歉，处理超时。请尝试更具体地提问，如：\n- \"从兴平到宝鸡开车要多久？\"\n- \"推荐一条路线\""}
                else:
                    logger.error(f"Agent 异常: {e}")
                    yield {"type": "content", "content": f"抱歉，处理出错：{str(e)}"}
        finally:
            clear_current_context()
    
    def _get_tool_display_name(self, tool_name: str) -> str:
        """获取工具的显示名称"""
        tool_names = {
            'route_preview': '路线预览',
            'driving_route': '驾车路线查询',
            'transit_route': '公共交通查询',
            'riding_route': '骑行路线查询',
            'maps_weather': '天气查询',
            'maps_around_search': '周边搜索',
            'maps_geo': '地理编码',
        }
        return tool_names.get(tool_name, tool_name)
    
    async def _stream_llm_direct(self, content: str) -> AsyncGenerator[str, None]:
        """直接流式输出内容（用于降级场景）"""
        chunk_size = 20
        for i in range(0, len(content), chunk_size):
            yield content[i:i+chunk_size]
            await asyncio.sleep(0.005)
    
    async def run(self, user_input: str, context: 'UnifiedContext') -> str:
        """同步运行 Agent（非流式）"""
        result = ""
        async for chunk in self.run_stream(user_input, context):
            result += chunk
        return result
    
    def _build_messages(self, user_input: str, context: 'UnifiedContext') -> List:
        """构建 Agent 消息列表"""
        current_date = datetime.now().strftime('%Y年%m月%d日')
        plan_context = self._build_plan_context(context)
        
        # 直接使用 plan_context 作为上下文，避免重复构建
        user_content = f"""当前日期: {current_date}

{plan_context}

用户问题: {user_input}"""
        
        return [HumanMessage(content=user_content)]
    
    def _build_plan_context(self, context: 'UnifiedContext') -> str:
        """构建规划上下文"""
        if not context or not context.has_plan():
            return "用户暂无规划信息"
        
        parts = []
        
        if context.plan_data.departure_location:
            parts.append(f"出发地: {context.plan_data.departure_location}")
        
        if context.plan_data.travel_days:
            parts.append(f"天数: {context.plan_data.travel_days}")
        
        if context.plan_data.travel_mode:
            parts.append(f"出行方式: {context.plan_data.travel_mode}")
        
        if context.plan_data.group_size:
            parts.append(f"人数: {context.plan_data.group_size}")
        
        if context.plan_data.budget_range:
            parts.append(f"预算: {context.plan_data.budget_range}")
        
        # 输出每个非遗的完整信息（包含经纬度）
        for h in context.plan_data.heritage_items:
            parts.append(f"非遗项目: {h.name}(ID:{h.id}, 地区:{h.region}, 经纬度:{h.longitude},{h.latitude})")
        
        if parts:
            return "\n".join(parts)
        else:
            return "用户暂无规划信息"
    
    def _extract_output(self, result: Dict[str, Any]) -> str:
        """从 Agent 结果中提取输出"""
        messages = result.get("messages", [])
        
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                return last_message.content
        
        return ""
    
    def get_tool_names(self) -> List[str]:
        """获取工具名称列表"""
        return [t.name for t in self._tools]
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        """获取工具信息列表"""
        return [{"name": t.name, "description": t.description} for t in self._tools]


_executor_instance: Optional[LangChainAgentExecutor] = None


def get_langchain_agent_executor() -> LangChainAgentExecutor:
    """获取 LangChainAgentExecutor 单例"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = LangChainAgentExecutor()
    return _executor_instance
