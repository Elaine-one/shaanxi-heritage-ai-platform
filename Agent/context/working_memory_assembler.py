# -*- coding: utf-8 -*-
"""
工作记忆组装器 (Working Memory Assembler)

核心职责：唯一的上下文截断/压缩决策点
替代之前散布在 context_builder、langchain_agent._build_messages、
context_compressor、_enforce_input_budget 中的7个独立截断点。

设计原则：
1. 单一组装点 — 所有上下文组装逻辑集中在此
2. 预算感知 — 按 token 预算分配各部分空间，System 不无限膨胀
3. 渐进压缩 — 无断崖，从完整→关键句→摘要，逐级降质
4. 意图驱动 — 意图检测结果影响 prompt 构建和工具选择
5. 存储与组装分离 — 存储层只负责存取，组装层负责预算分配和优先级排序
"""

import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage, ToolMessage

from Agent.context.unified_context import (
    UnifiedContext, ConversationTurn, IntentType, PlanData, HeritageItem
)
from Agent.config.memory_budget import memory_budget


# ── 预算分配数据结构 ──────────────────────────────────────

@dataclass
class BudgetAllocation:
    """各部分的 token 预算分配"""
    system: int = 0          # System Prompt (REACT + 日期)
    intent_hint: int = 0     # 意图提示
    plan_context: int = 0    # 规划信息
    working_memory: int = 0  # 工作记忆（工具调用摘要+规划状态+下一步）
    l2_preferences: int = 0  # L2 用户偏好
    rag_context: int = 0     # RAG 检索
    session_summary: int = 0 # L1 会话摘要
    cross_session: int = 0   # 跨会话上下文
    guide_slot: int = 0      # 引导槽（图扩展推荐）
    conversation: int = 0    # 对话历史
    current_input: int = 0   # 当前用户输入

    @property
    def total(self) -> int:
        return sum([
            self.system, self.intent_hint, self.plan_context,
            self.working_memory,
            self.l2_preferences, self.rag_context, self.session_summary,
            self.cross_session, self.guide_slot,
            self.conversation, self.current_input
        ])


@dataclass
class AssembleResult:
    """组装结果"""
    messages: List[BaseMessage]
    intent: IntentType
    allocation: BudgetAllocation
    total_tokens: int = 0


# ── 核心组装器 ──────────────────────────────────────────────

class WorkingMemoryAssembler:
    """
    工作记忆组装器 — 唯一的上下文截断/压缩决策点

    替代之前的7个独立截断点:
    1. context_builder.py:99 的 source_turns[-10:]
    2. coordinator.py:166 的 25字/轮摘要
    3. session.py:69 的 20条硬上限
    4. langchain_agent.py:300 的 15轮断崖
    5. context_compressor.py:298 的 P3丢弃
    6. langchain_agent.py:305 的 [-10:-1]
    7. langchain_agent.py:393 的 System膨胀挤压
    """

    def __init__(self):
        self._rag_retriever = None
        self._l2_store = None

    # ── 延迟加载依赖 ──

    @property
    def rag_retriever(self):
        if self._rag_retriever is None:
            try:
                from Agent.memory.rag_retriever import RAGRetriever
                self._rag_retriever = RAGRetriever()
            except Exception as e:
                logger.warning(f"[WMA] RAG检索器初始化失败: {e}")
        return self._rag_retriever

    @property
    def l2_store(self):
        if self._l2_store is None:
            try:
                from Agent.memory.l2_graph_store import get_l2_graph_store
                self._l2_store = get_l2_graph_store()
            except Exception as e:
                logger.warning(f"[WMA] L2图存储初始化失败: {e}")
        return self._l2_store

    # ── 核心入口 ──

    def assemble(
        self,
        user_input: str,
        context: UnifiedContext,
        input_budget: int,
        output_budget: int,
    ) -> AssembleResult:
        """
        组装预算感知的 LLM Message 列表

        Args:
            user_input: 当前用户输入
            context: 统一上下文（由 context_builder 构建，包含完整数据）
            input_budget: 输入 token 预算
            output_budget: 输出 token 预算

        Returns:
            AssembleResult: 包含 messages、intent、allocation
        """
        # 1. 意图检测（上下文感知）
        intent = self._detect_intent(user_input, context)

        # 2. 预算分配
        allocation = self._allocate_budget(intent, input_budget, context, user_input)

        # 3. 各部分在预算内组装
        system_content = self._build_system_content(allocation.system)
        intent_hint = self._build_intent_hint(intent, allocation.intent_hint)
        plan_ctx = self._build_plan_context(context, allocation.plan_context)
        wm_ctx = self._build_working_memory(user_input, context, intent, allocation.working_memory)
        l2_ctx = self._build_l2_context(context, allocation.l2_preferences)
        rag_ctx = self._build_rag_context(user_input, context, allocation.rag_context)
        summary_ctx = self._build_summary_context(context, allocation.session_summary)
        cross_session_ctx = self._build_cross_session_context(context, user_input, allocation.cross_session)
        guide_ctx = self._build_guide_slot(context, allocation.guide_slot)

        # 合并所有 system 级内容
        full_system = self._merge_system_content(
            system_content, intent_hint, plan_ctx, wm_ctx, l2_ctx,
            rag_ctx, summary_ctx, cross_session_ctx, guide_ctx
        )

        # 4. 对话历史组装（渐进压缩，无断崖）
        history_messages = self._build_conversation_messages(
            context.conversation_history, allocation.conversation
        )

        # 5. 组装最终 Message 列表
        messages = [SystemMessage(content=full_system)]
        messages.extend(history_messages)
        messages.append(HumanMessage(content=user_input))

        # 6. 最终预算校验
        total_tokens = self._estimate_tokens_for_messages(messages)
        if total_tokens > input_budget and memory_budget.token_budget_enforced:
            messages = self._final_budget_trim(messages, input_budget)

        logger.info(
            f"[WMA] 组装完成: intent={intent.value}, "
            f"allocation={allocation}, "
            f"messages={len(messages)}, "
            f"tokens≈{total_tokens}"
        )

        return AssembleResult(
            messages=messages,
            intent=intent,
            allocation=allocation,
            total_tokens=total_tokens,
        )

    # ── 意图检测（上下文感知） ──

    def _detect_intent(self, user_input: str, context: UnifiedContext) -> IntentType:
        """
        上下文感知的意图检测

        改进点:
        1. 使用上下文信号（是否有规划、最近摘要内容）加权
        2. 扩充关键词列表（从5-7个扩展到15+个）
        3. 加权评分而非硬匹配
        """
        input_lower = user_input.lower()

        # 上下文信号
        has_plan = context.has_plan()
        recent_summary = context.cached_data.get('session_summary', '')

        intent_rules = {
            IntentType.PLAN_RELATED: {
                'keywords': [
                    '规划', '行程', '路线', '已选', '安排', '旅游', '出游',
                    '去玩', '攻略', '计划', '出发', '几天', '怎么安排',
                    '行程安排', '旅游规划', '出行'
                ],
                'context_signals': [has_plan, '规划' in recent_summary, '行程' in recent_summary],
                'weight': 1.3,
            },
            IntentType.ROUTE_QUERY: {
                'keywords': [
                    '路线', '怎么走', '距离', '多远', '顺序', '交通',
                    '开车', '坐车', '导航', '路线规划', '怎么去', '公交',
                    '自驾', '高铁', '火车', '飞机', '骑行', '步行'
                ],
                'context_signals': [has_plan],
                'weight': 1.2,
            },
            IntentType.MODIFICATION: {
                'keywords': [
                    '修改', '调整', '增加', '删除', '换', '改一下', '去掉',
                    '添加', '减少', '换成', '改成', '取消', '不要', '加上',
                    '假期', '休假', '天假', '延长', '缩短', '多加', '压缩',
                    '加一天', '减一天', '再多', '改成..天',
                ],
                'context_signals': [has_plan],
                'weight': 1.4,  # 有规划时修改意图权重最高
            },
            IntentType.WEATHER_QUERY: {
                'keywords': [
                    '天气', '气温', '下雨', '晴天', '温度', '天气预报',
                    '阴天', '下雪', '风力', '穿什么', '带伞'
                ],
                'context_signals': [],
                'weight': 1.0,
            },
            IntentType.HERITAGE_QUERY: {
                'keywords': [
                    '非遗', '项目介绍', '历史', '特色', '什么是', '介绍一下',
                    '皮影', '秦腔', '剪纸', '泥塑', '老腔', '鼓乐', '面花',
                    '刺绣', '木版年画', '社火', '碗碗腔', '眉户'
                ],
                'context_signals': [],
                'weight': 1.0,
            },
        }

        # 加权评分
        scores = {}
        for intent_type, rule in intent_rules.items():
            score = 0.0
            for kw in rule['keywords']:
                if kw in input_lower:
                    score += 1.0
            # 上下文信号加权
            for signal in rule.get('context_signals', []):
                if signal:
                    score *= rule.get('weight', 1.0)
            scores[intent_type] = score

        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
        return IntentType.GENERAL_QUERY

    # ── 预算分配 ──

    def _allocate_budget(
        self,
        intent: IntentType,
        total_budget: int,
        context: UnifiedContext,
        user_input: str,
    ) -> BudgetAllocation:
        """
        根据 intent 和上下文动态分配 token 预算

        核心原则：对话历史始终保证 >= 配置比例（默认60%）
        工作记忆占 5-8%，从 RAG 和对话历史中分配
        """
        # 当前用户输入的 token 估算
        input_tokens = self._estimate_tokens(user_input)

        # 固定部分
        system_tokens = 1500  # REACT_SYSTEM_PROMPT 约 1500 tokens
        intent_tokens = 100
        input_reserve = max(input_tokens, 200)  # 至少保留200 tokens 给当前输入

        # 可变部分的基础分配
        has_plan = context.has_plan()
        has_history = len(context.conversation_history) > 0
        plan_tokens = 1500 if has_plan else 0
        l2_tokens = 800 if self.l2_store else 0
        rag_tokens = 1000 if self.rag_retriever else 0
        summary_tokens = 500

        # 跨会话 & 引导槽
        cross_session_tokens = int(total_budget * getattr(memory_budget, 'wm_cross_session_ratio', 0.05))
        guide_tokens = int(total_budget * getattr(memory_budget, 'wm_semantic_memory_ratio', 0.05))

        # 工作记忆：有规划或对话历史时分配更多
        wm_ratio = getattr(memory_budget, 'wm_working_memory_ratio', 0.06)
        wm_tokens = int(total_budget * wm_ratio) if (has_plan or has_history) else 0

        # 固定+可变基础合计
        fixed_total = (
            system_tokens + intent_tokens + plan_tokens + wm_tokens +
            l2_tokens + rag_tokens + summary_tokens +
            cross_session_tokens + guide_tokens + input_reserve
        )

        # 对话历史保证 >= 配置比例（默认60%）
        min_conversation = int(total_budget * memory_budget.wm_conversation_ratio)
        conversation_tokens = max(min_conversation, total_budget - fixed_total)

        # 如果总预算不够，按优先级缩减可变部分
        if fixed_total + conversation_tokens > total_budget:
            # 依次缩减: guide → cross_session → RAG → L2 → 摘要 → 工作记忆 → 规划
            overflow = fixed_total + conversation_tokens - total_budget
            if overflow > 0 and guide_tokens > 0:
                cut = min(guide_tokens, overflow)
                guide_tokens -= cut
                overflow -= cut
            if overflow > 0 and cross_session_tokens > 0:
                cut = min(cross_session_tokens, overflow)
                cross_session_tokens -= cut
                overflow -= cut
            if overflow > 0 and rag_tokens > 0:
                cut = min(rag_tokens, overflow)
                rag_tokens -= cut
                overflow -= cut
            if overflow > 0 and l2_tokens > 0:
                cut = min(l2_tokens, overflow)
                l2_tokens -= cut
                overflow -= cut
            if overflow > 0 and summary_tokens > 0:
                cut = min(summary_tokens, overflow)
                summary_tokens -= cut
                overflow -= cut
            if overflow > 0 and wm_tokens > 200:
                cut = min(wm_tokens - 200, overflow)
                wm_tokens -= cut
                overflow -= cut
            if overflow > 0 and plan_tokens > 0:
                cut = min(plan_tokens, overflow)
                plan_tokens -= cut
                overflow -= cut
            if overflow > 0:
                conversation_tokens = max(
                    min_conversation,
                    conversation_tokens - overflow
                )

        return BudgetAllocation(
            system=system_tokens,
            intent_hint=intent_tokens,
            plan_context=plan_tokens,
            working_memory=wm_tokens,
            l2_preferences=l2_tokens,
            rag_context=rag_tokens,
            session_summary=summary_tokens,
            cross_session=cross_session_tokens,
            guide_slot=guide_tokens,
            conversation=conversation_tokens,
            current_input=input_reserve,
        )

    # ── 各部分组装 ──

    def _build_system_content(self, budget: int) -> str:
        """构建 System Prompt 基础内容"""
        from Agent.prompts.react import REACT_SYSTEM_PROMPT
        current_date = datetime.now().strftime("%Y年%m月%d日")
        content = REACT_SYSTEM_PROMPT.format(current_date=current_date)

        # 如果超出预算，截断到预算内
        if self._estimate_tokens(content) > budget:
            content = self._truncate_to_budget(content, budget)
        return content

    def _build_intent_hint(self, intent: IntentType, budget: int) -> str:
        """根据意图生成提示，注入 System Prompt"""
        hints = {
            IntentType.PLAN_RELATED: "【当前意图】用户正在咨询旅游规划，优先使用 plan_query 和 route_preview 工具。",
            IntentType.ROUTE_QUERY: "【当前意图】用户在询问路线/交通，优先使用 route_preview 和 maps_direction 工具。",
            IntentType.MODIFICATION: "【当前意图】用户想修改规划，使用 plan_edit 工具，先查询当前规划再修改。",
            IntentType.WEATHER_QUERY: "【当前意图】用户询问天气，使用 maps_weather 工具。",
            IntentType.HERITAGE_QUERY: "【当前意图】用户询问非遗项目，使用 heritage_search 和 related_heritage_query 工具。",
        }
        hint = hints.get(intent, "")
        if hint and self._estimate_tokens(hint) > budget:
            hint = self._truncate_to_budget(hint, budget)
        return hint

    def _build_plan_context(self, context: UnifiedContext, budget: int) -> str:
        """构建规划上下文"""
        if not context.has_plan():
            return ""

        plan = context.plan_data
        parts = ["\n# 当前规划信息"]

        if plan.departure_location:
            parts.append(f"- 出发地: {plan.departure_location}")
        if plan.travel_days:
            parts.append(f"- 旅行天数: {plan.travel_days}天")
        if plan.travel_mode:
            parts.append(f"- 出行方式: {plan.travel_mode}")
        if plan.group_size and plan.group_size > 1:
            parts.append(f"- 人数: {plan.group_size}人")
        if plan.budget_range:
            parts.append(f"- 预算: {plan.budget_range}")
        if plan.special_requirements:
            parts.append(f"- 特殊要求: {', '.join(plan.special_requirements)}")

        if plan.heritage_items:
            parts.append(f"\n## 已选非遗项目 ({len(plan.heritage_items)}个)")
            for h in plan.heritage_items:
                item_str = f"- [{h.id}] {h.name}"
                if h.region:
                    item_str += f" ({h.region})"
                if h.category:
                    item_str += f" [{h.category}]"
                if h.level:
                    item_str += f" {h.level}"
                if h.latitude and h.longitude:
                    item_str += f" 坐标:{h.longitude},{h.latitude}"
                parts.append(item_str)

        if plan.itinerary:
            parts.append(f"\n## 行程安排 ({len(plan.itinerary)}天)")
            for day in plan.itinerary[:5]:  # 最多展示5天
                day_num = day.get('day', '?')
                theme = day.get('theme', '')
                places = day.get('places', [])
                parts.append(f"- 第{day_num}天: {theme} ({', '.join(str(p) for p in places[:3])})")

        content = '\n'.join(parts)
        if self._estimate_tokens(content) > budget:
            content = self._truncate_to_budget(content, budget)
        return content

    def _build_working_memory(
        self, user_input: str, context: UnifiedContext, intent: IntentType, budget: int
    ) -> str:
        """
        构建工作记忆段落 — Session 内的工具调用摘要和规划状态。

        纯规则提取 + TaskMemBuffer 感知，每轮由 WMA 自动重建。
        包含三部分：当前规划、已完成操作（TaskMemBuffer优先）、当前状态。
        """
        if budget <= 200:
            return ""

        parts = ["\n# 工作记忆"]

        # ── 0. TaskMemBuffer 上下文（优先于正则推断） ──
        task_ctx = self._build_task_buffer_context(budget // 3)
        if task_ctx:
            parts.append(task_ctx)

        # ── 1. 当前规划状态（从 plan_data 读取） ──
        plan_section = self._build_wm_plan_state(context)
        if plan_section:
            parts.append(plan_section)

        # ── 2. 已完成的关键操作（从对话历史提取，TaskMemBuffer 不可用时使用） ──
        if not task_ctx:
            ops_section = self._build_wm_tool_operations(context)
            if ops_section:
                parts.append(ops_section)

        # ── 3. 当前状态推断 ──
        status = self._infer_wm_status(user_input, context, intent)
        if status:
            parts.append(status)

        if len(parts) <= 1:
            return ""

        content = '\n'.join(parts)
        if self._estimate_tokens(content) > budget:
            content = self._truncate_to_budget(content, budget)
        return content

    def _build_wm_plan_state(self, context: UnifiedContext) -> str:
        """从 plan_data 提取规划状态"""
        if not context.has_plan():
            return ""

        plan = context.plan_data
        lines = ["## 当前规划"]

        if plan.heritage_items:
            items = []
            for h in plan.heritage_items[:8]:
                item_str = f"[{h.id}]{h.name}"
                if h.region:
                    item_str += f"({h.region})"
                if h.category:
                    item_str += f"[{h.category}]"
                items.append(item_str)
            lines.append(f"- 非遗: {', '.join(items)}")

        details = []
        if plan.departure_location:
            details.append(f"出发: {plan.departure_location}")
        if plan.travel_days:
            details.append(f"{plan.travel_days}天")
        if plan.travel_mode:
            details.append(f"{plan.travel_mode}")
        if plan.group_size and plan.group_size > 1:
            details.append(f"{plan.group_size}人")
        if plan.budget_range:
            details.append(f"预算{plan.budget_range}")
        if details:
            lines.append(f"- {' | '.join(details)}")

        return '\n'.join(lines) if len(lines) > 1 else ""

    def _build_wm_tool_operations(self, context: UnifiedContext) -> str:
        """
        从对话历史提取工具调用摘要。

        策略：扫描助手回复中的关键模式，推断已调用的工具和关键结果。
        纯规则匹配，不调 LLM。
        """
        history = context.conversation_history
        if len(history) < 2:
            return ""

        # 只分析最近 20 条消息
        recent = history[-20:] if len(history) > 20 else history

        ops = {}  # tool_name → latest summary

        for turn in recent:
            if turn.role != "assistant":
                continue
            content = turn.content or ""

            # 检测非遗查询结果
            if self._looks_like_heritage_search(content):
                # 提取非遗名称列表
                names = re.findall(
                    r'(?:皮影|秦腔|剪纸|泥塑|老腔|鼓乐|面花|刺绣|木版年画'
                    r'|社火|碗碗腔|眉户|腰鼓|民歌|花鼓)',
                    content
                )
                count_match = re.search(r'(\d+)\s*(?:个|项|条)', content)
                count = count_match.group(1) if count_match else str(len(set(names)))
                ops["heritage_search"] = f"查询非遗 → {count}个结果"

            # 检测路线/距离查询结果
            if self._looks_like_direction(content):
                from_match = re.search(r'(?:从|由)(\S{2,8})(?:到|至|→)(\S{2,8})', content)
                dist_match = re.search(r'(\d+\.?\d*)\s*(?:公里|km)', content)
                time_match = re.search(r'(\d+\.?\d*)\s*(?:小时|h)', content)
                if from_match:
                    route = f"{from_match.group(1)}→{from_match.group(2)}"
                    detail = ""
                    if dist_match:
                        detail += f"{dist_match.group(1)}km"
                    if time_match:
                        detail += f" {time_match.group(1)}h" if detail else f"{time_match.group(1)}h"
                    ops["maps_direction"] = f"{route} → {detail}" if detail else route

            # 检测天气查询结果
            if self._looks_like_weather(content):
                temp_match = re.search(r'(\d+)[\-~～](\d+)\s*[°℃]', content)
                weather_match = re.search(r'(晴|阴|雨|雪|多云|风)', content)
                loc_match = re.search(r'(?:陕西)?(\S{2,4})(?:地区|市|县)?(?:未来|近)', content)
                detail = ""
                if weather_match:
                    detail += weather_match.group(1)
                if temp_match:
                    detail += f" {temp_match.group(1)}-{temp_match.group(2)}°C"
                loc = loc_match.group(1) if loc_match else ""
                ops["maps_weather"] = f"{loc} → {detail}" if detail else f"{loc}天气已查询"

            # 检测路线规划结果
            if self._looks_like_route_planning(content):
                day_count = len(re.findall(r'第\s*\d+\s*天', content))
                route_match = re.search(r'(?:推荐|规划|最优).*?(?:路线|行程)', content)
                ops["route_preview"] = f"路线规划 → {day_count}天行程" if day_count else "路线规划已完成"

        if not ops:
            return ""

        lines = ["## 已完成的操作"]
        for tool_name in ["heritage_search", "maps_direction", "maps_weather", "route_preview"]:
            if tool_name in ops:
                lines.append(f"- [{tool_name}] {ops[tool_name]}")

        return '\n'.join(lines) if len(lines) > 1 else ""

    @staticmethod
    def _looks_like_heritage_search(text: str) -> bool:
        return bool(re.search(r'(?:查询|找到|搜索|非遗|项目).*(?:结果|以下|如下|个)|(?:皮影|秦腔|剪纸|泥塑).*(?:是|位于|属于)', text))

    @staticmethod
    def _looks_like_direction(text: str) -> bool:
        return bool(re.search(r'(?:驾车|距离|公里|小时|路线|高速|国道)', text))

    @staticmethod
    def _looks_like_weather(text: str) -> bool:
        return bool(re.search(r'(?:天气|气温|温度|°C|℃|晴|阴|雨|雪)', text))

    @staticmethod
    def _looks_like_route_planning(text: str) -> bool:
        return bool(re.search(r'(?:第\s*\d+\s*天|行程安排|路线规划|行程规划|每日行程|推荐路线)', text))

    def _build_task_buffer_context(self, budget: int) -> str:
        """构建 TaskMemBuffer 上下文 — 直接读取 ReAct 步骤"""
        if budget <= 100:
            return ""
        try:
            from Agent.memory.task_buffer import get_task_mem_buffer
            buffer = get_task_mem_buffer()
            if not buffer.has_active_task():
                return ""
            ctx = buffer.get_task_context(max_chars=budget * 2)
            return ctx
        except Exception:
            return ""

    def _infer_wm_status(
        self, user_input: str, context: UnifiedContext, intent: IntentType
    ) -> str:
        """根据意图和历史推断当前工作状态，指导 Agent 下一步行动"""
        history_len = len(context.conversation_history)
        has_plan = context.has_plan()
        input_lower = user_input.lower().strip()

        # 简短确认词 → Agent 应继续推进而非重新排列
        confirm_words = {"确定", "好的", "可以", "行", "ok", "yes", "对", "是的", "没错", "就这样", "按这个"}
        if input_lower in confirm_words:
            if has_plan:
                return "## 当前状态\n- 用户已确认，应调用地图/路线工具实际规划，而非重新排列已有数据"
            return "## 当前状态\n- 用户已确认，继续当前任务"

        if intent == IntentType.MODIFICATION:
            return "## 当前状态\n- 用户想修改规划，应先调用 plan_query 查看当前规划，再用 plan_edit 修改"

        if intent == IntentType.ROUTE_QUERY:
            had_direction = any(
                self._looks_like_direction(t.content)
                for t in context.conversation_history[-6:]
                if t.role == "assistant"
            )
            if had_direction:
                return "## 当前状态\n- 路线已查询过，如用户无新要求可直接引用已有结果"
            return "## 当前状态\n- 用户询问路线，应调用 maps_direction 或 route_preview 工具"

        if intent == IntentType.PLAN_RELATED:
            if history_len > 8 and has_plan:
                return "## 当前状态\n- 规划进行中，注意利用已有查询结果，避免重复调用相同工具"
            return "## 当前状态\n- 用户咨询规划，先了解需求再调用工具"

        return ""

    def _build_l2_context(self, context: UnifiedContext, budget: int) -> str:
        """构建 L2 用户偏好上下文（优先读缓存，缓存未命中才查 Neo4j）"""
        if not context.user_id or budget <= 0:
            return ""

        try:
            user_memory = None

            # 优先从 context_builder 缓存读取（TTL 300s，避免每轮 5 次 Neo4j 查询）
            cached = context.cached_data.get('l2_user_memory')
            if cached:
                user_memory = cached
                logger.debug("[WMA] L2 缓存命中")
            elif self.l2_store:
                user_memory = self.l2_store.fetch_user_memory(context.user_id)
                logger.debug("[WMA] L2 Neo4j 查询（缓存未命中）")

            if not user_memory:
                return ""

            parts = ["\n# 用户偏好"]
            preferences = user_memory.get('preferences', [])
            if preferences:
                for pref in preferences[:5]:
                    ptype = pref.get('type', '')
                    pvalue = pref.get('value', '')
                    if not ptype or not pvalue:
                        continue
                    # value 可能是字符串或 dict（如 heritage_interest 类型）
                    if isinstance(pvalue, dict):
                        pvalue = pvalue.get('heritage_name', '') or pvalue.get('name', '') or str(pvalue)
                    if not isinstance(pvalue, str):
                        pvalue = str(pvalue)
                    parts.append(f"- {ptype}: {pvalue[:100]}")

            interested_regions = user_memory.get('interested_regions', [])
            if interested_regions:
                regions = ', '.join(str(r) for r in interested_regions[:3])
                parts.append(f"- 感兴趣地区: {regions}")

            content = '\n'.join(parts)
            if self._estimate_tokens(content) > budget:
                content = self._truncate_to_budget(content, budget)
            return content
        except Exception as e:
            logger.warning(f"[WMA] L2偏好构建失败: {e}")
            return ""

    def _build_rag_context(
        self, user_input: str, context: UnifiedContext, budget: int
    ) -> str:
        """构建 RAG 检索上下文"""
        if not self.rag_retriever or budget <= 0:
            return ""

        try:
            # 动态 top_k
            if budget >= 3000:
                top_k = memory_budget.rag_top_k_max
            elif budget >= 1500:
                top_k = max(memory_budget.rag_top_k_min, memory_budget.rag_top_k_max - 1)
            else:
                top_k = memory_budget.rag_top_k_min

            rag_prompt = self.rag_retriever.build_rag_prompt(
                query=user_input,
                user_id=context.user_id,
                top_k=top_k
            )

            if not rag_prompt:
                return ""

            content = f"\n# 相关知识\n{rag_prompt}"
            if self._estimate_tokens(content) > budget:
                content = self._truncate_to_budget(content, budget)
            return content
        except Exception as e:
            logger.warning(f"[WMA] RAG上下文构建失败: {e}")
            return ""

    def _build_summary_context(self, context: UnifiedContext, budget: int) -> str:
        """构建 L1 会话摘要上下文"""
        summary = context.cached_data.get('session_summary', '')
        if not summary or budget <= 0:
            return ""

        content = f"\n# 对话历史摘要\n{summary}"
        if self._estimate_tokens(content) > budget:
            content = self._truncate_to_budget(content, budget)
        return content

    def _build_cross_session_context(
        self, context: UnifiedContext, user_input: str, budget: int
    ) -> str:
        """构建跨会话上下文"""
        if not context.user_id or budget <= 200:
            return ""

        try:
            from Agent.memory.session import get_session_lifecycle
            lifecycle = get_session_lifecycle()
            ctx = lifecycle._get_cross_session_context(
                context.user_id, user_input
            )
            if ctx and self._estimate_tokens(ctx) <= budget:
                return ctx
            return ""
        except Exception as e:
            logger.debug(f"[WMA] 跨会话上下文构建失败: {e}")
            return ""

    def _build_guide_slot(self, context: UnifiedContext, budget: int) -> str:
        """构建引导槽 — 图扩展推荐的实体"""
        if not context.user_id or budget <= 200:
            return ""

        try:
            if not self.l2_store:
                return ""

            heritage_names = []
            for item in context.plan_data.heritage_items:
                if item.name:
                    heritage_names.append(item.name)

            if not heritage_names:
                prefs = context.cached_data.get('l2_user_memory', {})
                for pref in prefs.get('preferences', []):
                    if pref.get('type') == 'heritage_interest':
                        val = pref.get('value', '')
                        if isinstance(val, dict):
                            heritage_names.append(val.get('heritage_name', ''))
                        elif isinstance(val, str):
                            heritage_names.append(val)

            if not heritage_names:
                return ""

            from Agent.config.memory_budget import memory_budget
            boosts = []
            for name in heritage_names[:3]:
                if not name:
                    continue
                boost = self.l2_store.get_graph_expansion_boost(
                    context.user_id, name
                )
                if boost > 0:
                    boosts.append((name, boost))

            if not boosts:
                return ""

            boosts.sort(key=lambda x: -x[1])
            parts = ["\n# 关联推荐"]
            for name, boost in boosts[:3]:
                parts.append(f"- 基于「{name}」的图扩展推荐 (关联度: {boost:.2f})")

            content = '\n'.join(parts)
            if self._estimate_tokens(content) > budget:
                content = self._truncate_to_budget(content, budget)
            return content
        except Exception as e:
            logger.debug(f"[WMA] 引导槽构建失败: {e}")
            return ""

    # ── 对话历史组装（渐进压缩，无断崖） ──

    def _build_conversation_messages(
        self,
        history: List[ConversationTurn],
        budget: int,
    ) -> List[BaseMessage]:
        """
        渐进式对话历史组装 — 无断崖

        策略:
        - 最近5轮: 完整原文
        - 更早的轮次: 关键句提取 → 超短摘要 → 丢弃
        - 预算不足时从最旧开始丢弃
        """
        if not history:
            return []

        recent_count = getattr(memory_budget, 'wm_recent_full_turns', 5)
        recent = history[-recent_count:] if len(history) > recent_count else history
        older = history[:-recent_count] if len(history) > recent_count else []

        messages = []

        # 更早的轮次：渐进压缩
        if older:
            recent_tokens = sum(self._estimate_tokens(t.content) for t in recent)
            # 为每条最近消息预留 role 开销
            recent_tokens += len(recent) * 10
            older_budget = max(0, budget - recent_tokens)

            if older_budget > 200:  # 至少200 tokens 才值得压缩
                compressed = self._progressive_compress(older, older_budget)
                if compressed:
                    messages.append(SystemMessage(
                        content=f"# 更早的对话\n{compressed}"
                    ))

        # 最近几轮：原文
        for turn in recent:
            if turn.role == 'user':
                messages.append(HumanMessage(content=turn.content))
            elif turn.role == 'assistant':
                # 重建 tool_call → ToolMessage 对，让 LLM 知道之前已调用过哪些工具
                interactions = getattr(turn, 'tool_interactions', None) or []
                if interactions:
                    tool_calls_list = []
                    tool_messages_list = []
                    for ti in interactions:
                        tc_id = ti.get('tool_call_id', '')
                        tc_name = ti.get('tool_name', '')
                        tc_args = ti.get('tool_args', {})
                        if tc_id:
                            tool_calls_list.append({
                                'name': tc_name,
                                'args': tc_args,
                                'id': tc_id,
                            })
                            tool_messages_list.append(ToolMessage(
                                content=str(ti.get('result', ''))[:2000],
                                tool_call_id=tc_id,
                            ))
                    if tool_calls_list:
                        messages.append(AIMessage(
                            content=turn.content,
                            tool_calls=tool_calls_list,
                        ))
                        messages.extend(tool_messages_list)
                    else:
                        messages.append(AIMessage(content=turn.content))
                else:
                    messages.append(AIMessage(content=turn.content))

        return messages

    def _progressive_compress(self, turns: List[ConversationTurn], budget: int) -> str:
        """
        渐进压缩：关键句 → 超短摘要 → 丢弃

        从最近的旧轮次开始保留（信息价值更高）
        """
        result_parts = []
        remaining_budget = budget

        key_sentence_max = getattr(memory_budget, 'wm_key_sentence_max_chars', 200)
        ultra_short_max = getattr(memory_budget, 'wm_ultra_short_max_chars', 80)

        for turn in reversed(turns):  # 从最近的旧轮次开始
            if remaining_budget <= 0:
                break

            # 提取关键句
            key_sentences = self._extract_key_sentences(turn.content)
            if key_sentences:
                compressed = f"{turn.role}: {'。'.join(key_sentences)}"
            else:
                compressed = f"{turn.role}: {turn.content[:key_sentence_max]}"

            # 截断到 key_sentence_max
            if len(compressed) > key_sentence_max:
                compressed = compressed[:key_sentence_max] + "..."

            tokens = self._estimate_tokens(compressed)
            if tokens <= remaining_budget:
                result_parts.insert(0, compressed)
                remaining_budget -= tokens
            else:
                # 预算不够，尝试超短摘要
                ultra_short = f"{turn.role}: {turn.content[:ultra_short_max]}..."
                tokens = self._estimate_tokens(ultra_short)
                if tokens <= remaining_budget:
                    result_parts.insert(0, ultra_short)
                    remaining_budget -= tokens
                # 否则丢弃此轮

        return '\n'.join(result_parts)

    def _extract_key_sentences(self, text: str) -> List[str]:
        """
        从文本中提取包含关键信息的句子

        关键信息包括：地名、数字+单位、交通方式、非遗名称、决策词
        """
        if not text:
            return []

        # 按中文标点分句
        sentences = re.split(r'[。！？\n]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 3]

        key_sentences = []
        for s in sentences:
            is_key = False
            # 包含地名指示词
            if re.search(r'(?:去|到|从|在|出发|到达|前往)[^\s，。！？]{2,8}', s):
                is_key = True
            # 包含数字+单位
            if re.search(r'\d+[\s]*(?:天|人|元|块|万|小时|分钟|公里|米)', s):
                is_key = True
            # 包含交通方式
            if re.search(r'(?:自驾|公交|步行|骑行|高铁|飞机|火车|地铁)', s):
                is_key = True
            # 包含非遗/文化关键词
            if re.search(r'(?:皮影|秦腔|剪纸|泥塑|老腔|鼓乐|面花|刺绣|木版年画|社火|非遗)', s):
                is_key = True
            # 包含决策/变更词
            if re.search(r'(?:决定|选择|改为|换成|增加|减少|取消|确认|同意)', s):
                is_key = True

            if is_key:
                key_sentences.append(s)

        return key_sentences[:3]  # 每轮最多3个关键句

    # ── 合并 System 内容 ──

    def _merge_system_content(self, *parts: str) -> str:
        """合并所有 system 级内容"""
        non_empty = [p for p in parts if p]
        return '\n'.join(non_empty)

    # ── 最终预算校验 ──

    def _final_budget_trim(
        self, messages: List[BaseMessage], budget: int
    ) -> List[BaseMessage]:
        """
        最终预算校验：如果超出预算，从最旧的历史消息开始移除

        保留: 第一条(SystemMessage) 和 最后一条(HumanMessage)
        """
        if len(messages) <= 2:
            return messages

        fixed_first = messages[0]
        fixed_last = messages[-1]
        middle = messages[1:-1]

        fixed_tokens = (
            self._estimate_tokens(getattr(fixed_first, 'content', '')) +
            self._estimate_tokens(getattr(fixed_last, 'content', ''))
        )
        remaining = max(1000, budget - fixed_tokens)

        # 从最近的历史开始保留
        selected = []
        used = 0
        for msg in reversed(middle):
            tokens = self._estimate_tokens(getattr(msg, 'content', ''))
            if used + tokens > remaining:
                break
            selected.append(msg)
            used += tokens

        selected.reverse()
        return [fixed_first] + selected + [fixed_last]

    # ── 工具方法 ──

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """估算 token 数（中文1字≈1token，英文4字符≈1token）"""
        if not text:
            return 0
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        return chinese_chars + other_chars // 4

    def _estimate_tokens_for_messages(self, messages: List[BaseMessage]) -> int:
        """估算消息列表的总 token 数"""
        total = 0
        for msg in messages:
            total += self._estimate_tokens(getattr(msg, 'content', ''))
            total += 10  # role 开销
        return total

    def _truncate_to_budget(self, text: str, budget: int) -> str:
        """将文本截断到预算内"""
        if self._estimate_tokens(text) <= budget:
            return text
        # 粗略估算：1 token ≈ 1 中文字 或 4 英文字符
        # 保守截断
        max_chars = budget * 2  # 假设平均2字符/token
        if len(text) > max_chars:
            return text[:max_chars] + "\n...(内容已截断)"
        return text


# ── 全局单例 ──

_assembler: Optional[WorkingMemoryAssembler] = None


def get_working_memory_assembler() -> WorkingMemoryAssembler:
    """获取全局 WorkingMemoryAssembler 单例"""
    global _assembler
    if _assembler is None:
        _assembler = WorkingMemoryAssembler()
    return _assembler
