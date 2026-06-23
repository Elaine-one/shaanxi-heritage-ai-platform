# -*- coding: utf-8 -*-
"""
LangGraph Agent 封装
使用 langgraph.prebuilt.create_react_agent 实现 ReAct Agent
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional, Dict, Any, List

from loguru import logger

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from Agent.prompts import REACT_SYSTEM_PROMPT
from Agent.config.memory_budget import memory_budget

try:
    from langgraph.errors import GraphRecursionError
except ImportError:
    GraphRecursionError = None


class LangChainAgentExecutor:
    """
    LangGraph ReAct Agent 封装

    LangChain agents.create_agent 自动管理:
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
            base_max_tokens = llm_config.max_tokens or memory_budget.output_budget_max
            
            self._llm = ChatOpenAI(
                api_key=llm_config.api_key,
                base_url=llm_config.base_url,
                model=llm_config.model,
                temperature=llm_config.temperature or 0.7,
                max_tokens=base_max_tokens,
                request_timeout=600,
                max_retries=1,
                streaming=True,
            )
            
            logger.info(f"LangChain LLM 初始化完成（流式模式）: {llm_config.model}")
        
        return self._llm
    
    async def initialize(self, context: 'UnifiedContext' = None) -> bool:
        """初始化 Agent（包含 MCP 工具）"""
        if self._initialized:
            return True
        
        from Agent.tools.langchain_tools import get_langchain_tools_manager
        
        manager = get_langchain_tools_manager()
        
        manager.initialize()
        
        mcp_success = await manager.initialize_mcp()
        
        self._tools = await manager.get_all_tools()
        
        if not self._tools:
            logger.error("没有可用的 LangChain 工具")
            return False
        
        self._agent = create_react_agent(
            model=self.llm,
            tools=self._tools,
            prompt=REACT_SYSTEM_PROMPT,
        )
        
        self._initialized = True
        mcp_status = "已集成" if mcp_success else "未集成"
        logger.info(f"LangGraph Agent 初始化完成，工具数量: {len(self._tools)} (MCP工具{mcp_status})")
        return True
    
    async def run_stream(
        self,
        user_input: str,
        context: 'UnifiedContext'
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流式运行 Agent - 使用 messages 模式实现逐 token 流式输出"""
        from Agent.context.unified_context import set_current_context, clear_current_context
        from langchain_core.messages import AIMessageChunk, ToolMessage
        
        set_current_context(context)
        
        try:
            if not await self.initialize(context):
                yield {"type": "content", "content": "抱歉，系统初始化失败，请稍后重试。"}
                return
            
            input_budget = self._determine_input_budget(user_input, context)
            output_budget = self._determine_output_budget(user_input, context)
            if not memory_budget.token_budget_enforced:
                input_budget = memory_budget.model_context_window - output_budget
            messages = self._build_messages(user_input, context, input_budget=input_budget)
            llm_for_request = self.llm.bind(max_tokens=output_budget)
            runtime_agent = create_react_agent(
                model=llm_for_request,
                tools=self._tools,
                prompt=REACT_SYSTEM_PROMPT,
            )
            
            logger.info(f"🚀 LangGraph Agent 开始处理: {user_input[:50]}...")
            logger.info(f"🎯 本轮预算: input<={input_budget}, output<={output_budget} tokens")
            logger.info("=" * 60)
            
            try:
                step_count = 0
                final_content = ""
                usage_metadata = {}
                first_token_time = None
                import time as _time
                stream_start = _time.monotonic()
                
                has_seen_tools = False
                just_got_tool_result = False
                tool_interactions = []  # 收集本轮所有工具交互，供跨轮次记忆
                pending_tool_calls = []  # 当前待处理的 tool_call
                suppressed_reasoning = []  # 收集被抑制的推理文本，合并为单行日志

                async for event in runtime_agent.astream(
                    {"messages": messages},
                    {"recursion_limit": self.MAX_ITERATIONS},
                    stream_mode="messages"
                ):
                    if not event:
                        continue

                    if isinstance(event, tuple):
                        chunk = event[0]
                    elif isinstance(event, list):
                        chunk = event[0] if event else None
                    else:
                        chunk = event
                    if chunk is None:
                        continue
                    
                    if isinstance(chunk, AIMessageChunk):
                        if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                            usage_metadata = chunk.usage_metadata
                        
                        has_tool_calls = hasattr(chunk, 'tool_calls') and chunk.tool_calls
                        
                        if has_tool_calls:
                            # 冲刷之前积累的抑制推理文本
                            if suppressed_reasoning:
                                total = ''.join(suppressed_reasoning)
                                logger.debug(f"抑制工具调用前的推理文本: {len(total)} chars")
                                suppressed_reasoning = []
                            has_seen_tools = True
                            just_got_tool_result = False
                            step_count += 1
                            for tc in chunk.tool_calls:
                                tool_name = tc.get('name', 'unknown')
                                display_name = self._get_tool_display_name(tool_name)
                                logger.info(f"📌 步骤 {step_count}: 调用工具 [{display_name}] ({tool_name})")
                                logger.info(f"   参数: {tc.get('args', {})}")
                                pending_tool_calls.append({
                                    'name': tool_name,
                                    'args': tc.get('args', {}),
                                    'id': tc.get('id', ''),
                                })
                        elif chunk.content:
                            if not has_seen_tools or just_got_tool_result:
                                if first_token_time is None:
                                    first_token_time = _time.monotonic()
                                # 冲刷之前积累的抑制推理文本
                                if suppressed_reasoning:
                                    total = ''.join(suppressed_reasoning)
                                    logger.debug(f"抑制工具调用前的推理文本: {len(total)} chars")
                                    suppressed_reasoning = []
                                yield {"type": "content", "content": chunk.content}
                                final_content += chunk.content
                            else:
                                suppressed_reasoning.append(chunk.content)
                    
                    elif isinstance(chunk, ToolMessage):
                        just_got_tool_result = True
                        step_count += 1
                        content_preview = chunk.content[:200] if len(chunk.content) > 200 else chunk.content
                        logger.info(f"📋 步骤 {step_count}: 工具返回结果")
                        logger.info(f"   {content_preview}")
                        # 将待处理的 tool_call 与结果配对，存入 tool_interactions
                        for tc in pending_tool_calls:
                            tool_interactions.append({
                                'tool_name': tc['name'],
                                'tool_args': tc['args'],
                                'tool_call_id': tc['id'],
                                'result': chunk.content,
                            })
                        pending_tool_calls = []
                
                stream_end = _time.monotonic()
                total_latency_ms = int((stream_end - stream_start) * 1000)
                first_token_ms = int((first_token_time - stream_start) * 1000) if first_token_time else 0
                
                prompt_tokens = usage_metadata.get('input_tokens', 0) if usage_metadata else 0
                completion_tokens = usage_metadata.get('output_tokens', 0) if usage_metadata else 0
                total_tokens = usage_metadata.get('total_tokens', 0) if usage_metadata else 0
                
                logger.info("=" * 60)
                logger.info(f"📊 Agent 执行完成，共 {step_count} 步，输出 {len(final_content)} 字符")
                if usage_metadata:
                    logger.info(
                        f"📊 Token 用量: input={prompt_tokens}, output={completion_tokens}, "
                        f"total={total_tokens}"
                    )
                else:
                    est_input = self._estimate_tokens(str(messages))
                    est_output = self._estimate_tokens(final_content)
                    logger.info(
                        f"📊 Token 估算: input≈{est_input}, output≈{est_output} (LLM未返回usage)"
                    )
                logger.info(
                    f"📊 延迟: 首token={first_token_ms}ms, 总耗时={total_latency_ms}ms"
                )
                
                if not final_content:
                    yield {"type": "content", "content": "抱歉，我无法处理您的请求，请尝试换一种方式提问。"}

                if suppressed_reasoning:
                    total = ''.join(suppressed_reasoning)
                    logger.debug(f"抑制工具调用前的推理文本: {len(total)} chars")

                if tool_interactions:
                    yield {"type": "tool_interactions", "interactions": tool_interactions}

                yield {"type": "done"}
                    
            except Exception as e:
                is_recursion = (
                    (GraphRecursionError is not None and isinstance(e, GraphRecursionError))
                    or "Recursion limit" in str(e)
                )
                if is_recursion:
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
            'maps_direction_driving': '驾车路线查询',
            'maps_direction_transit': '公共交通查询',
            'maps_direction_riding': '骑行路线查询',
            'maps_direction_walking': '步行路线查询',
            'maps_weather': '天气查询',
            'maps_around_search': '周边搜索',
            'maps_geo': '地理编码',
            'maps_regeocode': '逆地理编码',
            'maps_distance': '距离测量',
            'maps_text_search': 'POI搜索',
            'maps_ip_location': 'IP定位',
            'heritage_search': '非遗项目查询',
            'plan_query': '规划查询',
            'plan_edit': '规划编辑',
            'nearby_heritage_query': '邻近非遗查询',
            'related_heritage_query': '相关非遗查询',
            'user_heritage_recommend': '个性化推荐',
            'nearby_region_query': '周边地区查询',
            'heritage_route_hint': '路线提示',
        }
        return tool_names.get(tool_name, tool_name)
    
    def _build_messages(self, user_input: str, context: 'UnifiedContext', input_budget: int) -> List:
        """
        构建 Agent 消息列表 — 委托给 WorkingMemoryAssembler

        WorkingMemoryAssembler 是唯一的上下文截断/压缩决策点，
        替代了之前散布在 _build_messages、_enforce_input_budget、
        _compress_conversation_history 中的7个独立截断点。
        """
        from Agent.context.working_memory_assembler import get_working_memory_assembler

        assembler = get_working_memory_assembler()
        output_budget = self._determine_output_budget(user_input, context)

        result = assembler.assemble(
            user_input=user_input,
            context=context,
            input_budget=input_budget,
            output_budget=output_budget,
        )

        # 更新 context 中的意图（由 Assembler 检测）
        context.detected_intent = result.intent

        return result.messages

    def _determine_input_budget(self, user_input: str, context: 'UnifiedContext') -> int:
        """
        动态输入预算上限。
        - 简短问候: 小上下文，降低延迟与成本
        - 一般问答: 中等上下文
        - 规划/路线/修改: 大上下文（上限20K）
        """
        text = (user_input or "").strip()
        if not text:
            return max(memory_budget.input_budget_min, 3000)

        normalized = text.lower()
        short_greetings = {"你好", "您好", "hi", "hello", "在吗", "哈喽"}
        if normalized in short_greetings or len(text) <= 6:
            return max(memory_budget.input_budget_min, 3500)

        intent = getattr(context, "detected_intent", None)
        intent_value = getattr(intent, "value", "")

        # 复杂任务保留高预算
        if intent_value in {"route_query", "plan_related", "modification"}:
            return memory_budget.input_budget_max

        # 中等复杂度问答
        if intent_value in {"weather_query", "heritage_query"}:
            return min(memory_budget.input_budget_max, 12000)

        # 根据历史轮次弹性扩容
        history_len = len(getattr(context, "conversation_history", []) or [])
        if history_len >= 12:
            return min(memory_budget.input_budget_max, 16000)
        if history_len >= 6:
            return min(memory_budget.input_budget_max, 12000)

        # 文本较长时提供更多上下文预算
        if len(text) > 120:
            return min(memory_budget.input_budget_max, 14000)

        return min(memory_budget.input_budget_max, max(memory_budget.input_budget_min, 9000))

    def _determine_output_budget(self, user_input: str, context: 'UnifiedContext') -> int:
        """
        动态确定本轮输出预算上限。
        注意：这是“上限”而非“目标输出长度”。
        """
        text = (user_input or "").strip()
        if not text:
            return 800

        short_greetings = {"你好", "您好", "hi", "hello", "在吗", "哈喽"}
        if text.lower() in short_greetings or len(text) <= 6:
            return 600

        intent = getattr(context, "detected_intent", None)
        if intent and getattr(intent, "value", "") in {"route_query", "plan_related", "modification"}:
            return min(memory_budget.output_budget_max, 8000)
        if intent and getattr(intent, "value", "") in {"weather_query", "heritage_query"}:
            return min(memory_budget.output_budget_max, 5000)

        if len(text) > 120:
            return min(memory_budget.output_budget_max, 6500)

        return max(memory_budget.output_budget_min, memory_budget.output_budget_default)

    def _estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        chinese_chars = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return chinese_chars + max(1, other_chars // 4)

    
    def get_tool_names(self) -> List[str]:
        return [t.name for t in self._tools]
    
    def get_tools_info(self) -> List[Dict[str, Any]]:
        return [{"name": t.name, "description": t.description} for t in self._tools]


_executor_instance: Optional[LangChainAgentExecutor] = None


def get_langchain_agent_executor() -> LangChainAgentExecutor:
    """获取 LangChainAgentExecutor 单例"""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = LangChainAgentExecutor()
    return _executor_instance
