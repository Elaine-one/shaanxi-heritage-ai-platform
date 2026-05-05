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
                            has_seen_tools = True
                            just_got_tool_result = False
                            step_count += 1
                            for tc in chunk.tool_calls:
                                tool_name = tc.get('name', 'unknown')
                                display_name = self._get_tool_display_name(tool_name)
                                logger.info(f"📌 步骤 {step_count}: 调用工具 [{display_name}] ({tool_name})")
                                logger.info(f"   参数: {tc.get('args', {})}")
                        elif chunk.content:
                            if not has_seen_tools or just_got_tool_result:
                                if first_token_time is None:
                                    first_token_time = _time.monotonic()
                                yield {"type": "content", "content": chunk.content}
                                final_content += chunk.content
                            else:
                                logger.debug(f"抑制工具调用前的推理文本: {chunk.content[:80]}")
                    
                    elif isinstance(chunk, ToolMessage):
                        just_got_tool_result = True
                        step_count += 1
                        content_preview = chunk.content[:200] if len(chunk.content) > 200 else chunk.content
                        logger.info(f"📋 步骤 {step_count}: 工具返回结果")
                        logger.info(f"   {content_preview}")
                
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
            'maps_distance': '距离测量',
            'maps_text_search': 'POI搜索',
            'heritage_search': '非遗项目查询',
            'plan_query': '规划查询',
            'plan_edit': '规划编辑',
            'nearby_heritage_query': '邻近非遗查询',
            'related_heritage_query': '相关非遗查询',
        }
        return tool_names.get(tool_name, tool_name)
    
    def _build_messages(self, user_input: str, context: 'UnifiedContext', input_budget: int) -> List:
        """构建 Agent 消息列表"""
        current_date = datetime.now().strftime('%Y年%m月%d日')
        system_content = REACT_SYSTEM_PROMPT.format(current_date=current_date)

        plan_context = self._build_plan_context(context)
        if plan_context and plan_context != "用户暂无规划信息":
            system_content += "\n\n# 当前会话规划信息\n" + plan_context

        if context.user_id:
            try:
                from Agent.memory.l2_graph_store import get_l2_graph_store
                l2_store = get_l2_graph_store()
                if l2_store.is_available():
                    user_memory = l2_store.fetch_user_memory(context.user_id)
                    user_context = self._format_user_memory_for_prompt(user_memory)
                    if user_context:
                        system_content += "\n\n" + user_context

                    recommendations = l2_store.recommend_for_user(context.user_id, limit=3)
                    if recommendations:
                        rec_lines = ["【个性化推荐 - 基于用户历史偏好，仅供参考】"]
                        for rec in recommendations:
                            rec_lines.append(
                                f"- {rec['name']}({rec.get('category', '')}, "
                                f"{rec.get('region', '')}) [推荐理由: {rec.get('reason', '')}]"
                            )
                        system_content += "\n\n" + "\n".join(rec_lines)
            except Exception as e:
                logger.debug(f"获取用户偏好/推荐失败: {e}")

        session_summary = ""
        if getattr(context, "cached_data", None):
            session_summary = context.cached_data.get("session_summary", "")
        if session_summary:
            system_content += "\n\n# 历史摘要\n" + session_summary

        rag_context = self._get_rag_context(user_input, context, input_budget=input_budget)
        if rag_context:
            system_content += "\n\n" + rag_context

        messages = [SystemMessage(content=system_content)]

        history_len = len(context.conversation_history)
        from Agent.config.memory_budget import memory_budget
        if history_len > memory_budget.conversation_compress_threshold:
            compressed_context = self._compress_conversation_history(context)
            system_content += "\n\n# 对话历史摘要\n" + compressed_context
            messages[0] = SystemMessage(content=system_content)
        else:
            for turn in context.conversation_history[-10:-1]:
                if turn.role == "user":
                    messages.append(HumanMessage(content=turn.content))
                elif turn.role == "assistant":
                    messages.append(AIMessage(content=turn.content))

        user_content = f"""当前日期: {current_date}

用户问题: {user_input}"""

        messages.append(HumanMessage(content=user_content))
        messages = self._enforce_input_budget(messages, input_budget)

        self._log_messages_summary(messages, context.conversation_history, user_input)

        return messages

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

    def _enforce_input_budget(self, messages: List, budget: int) -> List:
        """
        输入预算控制：优先保留 system 与最后用户问题，裁剪历史消息。
        """
        if not messages:
            return messages

        if len(messages) <= 2:
            return messages

        fixed_first = messages[0]
        fixed_last = messages[-1]
        middle = messages[1:-1]

        fixed_tokens = self._estimate_tokens(getattr(fixed_first, "content", "")) + \
            self._estimate_tokens(getattr(fixed_last, "content", ""))

        remaining_budget = max(1500, budget - fixed_tokens)
        selected_reversed = []
        used = 0

        # 从最近历史开始保留，超预算则停止
        for msg in reversed(middle):
            token = self._estimate_tokens(getattr(msg, "content", ""))
            if used + token > remaining_budget:
                break
            selected_reversed.append(msg)
            used += token

        selected_middle = list(reversed(selected_reversed))
        trimmed = [fixed_first] + selected_middle + [fixed_last]

        total_tokens = sum(self._estimate_tokens(getattr(m, "content", "")) for m in trimmed)
        logger.info(
            f"🧮 输入预算控制: budget={budget}, fixed={fixed_tokens}, history_kept={len(selected_middle)}, total≈{total_tokens}"
        )
        return trimmed

    def _log_messages_summary(self, messages: List, conversation_history: list, user_input: str):
        """记录发送给 API 的消息摘要"""
        logger.info("=" * 60)
        logger.info("📤 即将发送给 API 的消息摘要:")
        logger.info(f"=" * 60)

        for i, msg in enumerate(messages):
            msg_type = type(msg).__name__
            content_preview = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            logger.info(f"  [{i}] {msg_type}: {content_preview}")

        logger.info(f"-" * 60)
        logger.info(f"📊 统计信息:")
        logger.info(f"  - SystemMessage 长度: {len(messages[0].content)} 字符")
        logger.info(f"  - 历史对话轮数: {len(conversation_history)} 轮")
        if conversation_history:
            history_chars = sum(len(t.content) for t in conversation_history)
            logger.info(f"  - 历史对话总长度: {history_chars} 字符")
        logger.info(f"  - 当前用户输入: {len(user_input)} 字符")
        logger.info(f"  - 消息总数: {len(messages)} 条")
        logger.info("=" * 60)

    def _get_rag_top_k(self, input_budget: int) -> int:
        """
        根据输入预算动态计算 RAG top_k。
        """
        min_k = memory_budget.rag_top_k_min
        max_k = max(min_k, memory_budget.rag_top_k_max)
        if input_budget >= 16000:
            return max_k
        if input_budget >= 10000:
            return min(max_k, min_k + 1)
        return min_k

    def _get_rag_context(self, user_input: str, context: 'UnifiedContext', input_budget: int) -> str:
        """获取RAG增强上下文"""
        try:
            from Agent.memory.rag_retriever import get_rag_retriever

            retriever = get_rag_retriever()
            top_k = self._get_rag_top_k(input_budget)
            rag_context = retriever.build_rag_prompt(
                query=user_input,
                user_id=context.user_id,
                top_k=top_k
            )
            if rag_context:
                if len(rag_context) > memory_budget.rag_context_max_chars:
                    rag_context = rag_context[:memory_budget.rag_context_max_chars] + "\n...（RAG内容已截断）"
                if context.cached_data is None:
                    context.cached_data = {}
                context.cached_data['rag_context'] = rag_context
                logger.info(
                    f"✅ RAG检索成功: top_k={top_k}, context_chars={len(rag_context)}"
                )
            return rag_context
        except Exception as e:
            logger.debug(f"RAG检索失败: {e}")
            return ""

    def _compress_conversation_history(self, context: 'UnifiedContext') -> str:
        """压缩对话历史上下文（不包含当前用户输入）"""
        try:
            from Agent.context.context_compressor import get_context_compressor

            compressor = get_context_compressor()

            history_dicts = []
            for turn in context.conversation_history[:-1]:
                history_dicts.append({
                    'role': turn.role,
                    'content': turn.content
                })

            context_dict = {
                'plan_data': context.plan_data.model_dump() if context.plan_data else {},
                'conversation_history': history_dicts,
                'cached_data': context.cached_data,
                'rag_context': context.cached_data.get('rag_context', '') if context.cached_data else '',
            }

            result = compressor.compress(
                context_dict,
                token_budget=memory_budget.compression_token_budget
            )

            logger.info(f"上下文压缩: {result.original_tokens} → {result.compressed_tokens} tokens, "
                       f"比例: {result.compression_ratio:.1%}, 保留: {result.preserved_sections}, "
                       f"移除: {result.removed_sections}")

            return result.content
        except Exception as e:
            logger.warning(f"上下文压缩失败，回退到简单截取: {e}")
            return ""
    
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

    def _format_user_memory_for_prompt(self, user_memory: Dict[str, Any]) -> str:
        if not user_memory:
            return ""

        preferences = user_memory.get("preferences", [])
        interested_regions = user_memory.get("interested_regions", [])
        preferred_heritages = user_memory.get("preferred_heritages", [])
        planned_heritages = user_memory.get("planned_heritages", [])
        exported_heritages = user_memory.get("exported_heritages", [])

        if not preferences and not interested_regions and not preferred_heritages and not planned_heritages:
            return ""

        lines = ["【用户长期偏好 - 作为参考，优先级低于本次规划】"]

        pref_map = {}
        for p in preferences:
            pref_map[p.get("type", "")] = p.get("value", "")

        budget_val = pref_map.get("budget")
        if budget_val:
            lines.append(f"- 偏好预算：{self._format_pref_value(budget_val)}")

        travel_val = pref_map.get("travel_mode")
        if travel_val:
            lines.append(f"- 偏好出行方式：{self._format_pref_value(travel_val)}")

        interest_val = pref_map.get("interest")
        if interest_val:
            lines.append(f"- 感兴趣的非遗类型：{self._format_pref_value(interest_val)}")

        group_val = pref_map.get("group_preference")
        if group_val:
            lines.append(f"- 团队偏好：{self._format_pref_value(group_val)}")

        if interested_regions:
            lines.append(f"- 感兴趣的地区：{', '.join(interested_regions[:5])}")

        if preferred_heritages:
            names = [h.get("name", "") for h in preferred_heritages[:5] if h.get("name")]
            if names:
                lines.append(f"- 对话中感兴趣的非遗：{', '.join(names)}")

        if planned_heritages:
            names = [h.get("name", "") for h in planned_heritages[:5] if h.get("name")]
            if names:
                lines.append(f"- 历史规划过的非遗：{', '.join(names)}")

        if exported_heritages:
            names = [h.get("name", "") for h in exported_heritages[:5] if h.get("name")]
            if names:
                lines.append(f"- 导出过路书的非遗：{', '.join(names)}")

        if len(lines) <= 1:
            return ""

        return '\n'.join(lines)

    @staticmethod
    def _format_pref_value(val) -> str:
        if isinstance(val, dict):
            if "amount" in val:
                return f"约{val['amount']}元"
            if "prefer" in val:
                return f"偏好{','.join(val['prefer'])}" if val.get("prefer") else ""
            if "exclude" in val:
                return f"避免{','.join(val['exclude'])}" if val.get("exclude") else ""
            if "regions" in val:
                return ','.join(val["regions"])
            if "category" in val:
                return val["category"] + (f"({val.get('detail', '')})" if val.get("detail") else "")
            if "group_type" in val:
                return val["group_type"] + (f"({val.get('notes', '')})" if val.get("notes") else "")
            return str(val)
        return str(val)
    
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
