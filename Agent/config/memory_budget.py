# -*- coding: utf-8 -*-
"""
记忆与上下文预算配置
集中管理所有记忆系统参数，避免在业务代码中硬编码。
所有参数均可通过环境变量覆盖，环境变量名即下方 _get_int/_get_bool/_get_str_list 的第一个参数。
"""

import os
from dataclasses import dataclass, field


def _get_int(name: str, default: int) -> int:
    """读取整数环境变量，缺失或非法时返回 default"""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_bool(name: str, default: bool) -> bool:
    """读取布尔环境变量，"1/true/yes/on" 视为 True"""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_str_list(name: str, default: str) -> tuple:
    """读取逗号分隔的字符串列表环境变量，返回 tuple"""
    value = os.getenv(name)
    if value is None:
        raw = default
    else:
        raw = value
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass
class MemoryBudgetConfig:
    """
    记忆与上下文预算配置

    所有字段均通过环境变量覆盖，环境变量名即 _get_* 的第一个参数。
    默认值经过生产验证，一般无需修改；如需调优请优先调整 INPUT_BUDGET / OUTPUT_BUDGET_DEFAULT。
    """

    # ── LLM 上下文窗口 ──────────────────────────────────
    # 模型上下文窗口大小（tokens），决定输入+输出的理论上限
    # 切换模型时务必同步修改此值，否则预算计算会失真
    # 环境变量: MODEL_CONTEXT_WINDOW  默认: 128000
    # 常见模型: qwen-plus=131072, glm-4=128000, gpt-4o=128000,
    #          deepseek-chat=128000, moonshot-v1-8k=8192
    model_context_window: int = _get_int("MODEL_CONTEXT_WINDOW", 128000)

    # ── 输入预算 ─────────────────────────────────────────
    # 发送给 LLM 的 prompt 总 token 上限（含 system + history + rag + tools）
    # 环境变量: INPUT_BUDGET  默认: 20000
    # 20K 分配建议: system/guardrails≈2000, L2长期记忆≈6000,
    #              L1摘要≈2000, L1最近原文≈6000, RAG+Tools≈4000
    input_budget: int = _get_int("INPUT_BUDGET", 20000)

    # 输入预算下限，低于此值时强制提升（防止上下文过短导致回答质量差）
    # 环境变量: INPUT_BUDGET_MIN  默认: 3000
    input_budget_min: int = _get_int("INPUT_BUDGET_MIN", 3000)

    # 输入预算上限，动态预算计算结果不会超过此值
    # 环境变量: INPUT_BUDGET_MAX  默认: 20000
    input_budget_max: int = _get_int("INPUT_BUDGET_MAX", 20000)

    # ── 输出预算 ─────────────────────────────────────────
    # 默认输出 token 数，用于一般规划类对话
    # 环境变量: OUTPUT_BUDGET_DEFAULT  默认: 6000
    # 实际输出预算由 _determine_output_budget 按意图动态调整
    output_budget_default: int = _get_int("OUTPUT_BUDGET_DEFAULT", 6000)

    # 输出预算下限，短问答/闲聊场景使用
    # 环境变量: OUTPUT_BUDGET_MIN  默认: 400
    output_budget_min: int = _get_int("OUTPUT_BUDGET_MIN", 400)

    # 输出预算上限，复杂路线/多约束场景使用
    # 环境变量: OUTPUT_BUDGET_MAX  默认: 8000
    output_budget_max: int = _get_int("OUTPUT_BUDGET_MAX", 8000)

    # ── 压缩与裁剪 ──────────────────────────────────────
    # 上下文压缩器的 token 预算，超预算时触发分层压缩
    # 环境变量: CONTEXT_COMPRESSION_BUDGET  默认: 12000
    # 应小于 INPUT_BUDGET，为 system prompt 和 RAG 留空间
    compression_token_budget: int = _get_int("CONTEXT_COMPRESSION_BUDGET", 12000)

    # RAG 向量检索返回的最少文档数
    # 环境变量: RAG_TOP_K_MIN  默认: 1
    rag_top_k_min: int = _get_int("RAG_TOP_K_MIN", 1)

    # RAG 向量检索返回的最多文档数
    # 环境变量: RAG_TOP_K_MAX  默认: 3
    # 实际 top_k 由 _get_rag_top_k 根据输入预算动态计算
    rag_top_k_max: int = _get_int("RAG_TOP_K_MAX", 3)

    # RAG 注入上下文时的单次最大字符数（超出截断）
    # 环境变量: RAG_CONTEXT_MAX_CHARS  默认: 1800
    rag_context_max_chars: int = _get_int("RAG_CONTEXT_MAX_CHARS", 1800)

    # 工具返回结果的最大字符数（超出截断并附加原始长度提示）
    # 环境变量: TOOL_RESULT_MAX_CHARS  默认: 2000
    tool_result_max_chars: int = _get_int("TOOL_RESULT_MAX_CHARS", 2000)

    # ── L1 滚动窗口（Redis 感知层）──────────────────────
    # L1 最近对话保留轮数，超出后触发滚动丢弃
    # 环境变量: MEMORY_L1_RECENT_LIMIT  默认: 10
    # 值越大上下文越完整，但 token 消耗越高
    l1_recent_limit: int = _get_int("MEMORY_L1_RECENT_LIMIT", 10)

    # 每次滚动丢弃的最旧轮数（触发滚动时一次丢弃几轮）
    # 环境变量: MEMORY_L1_ROLLING_DROP_COUNT  默认: 2
    l1_rolling_drop_count: int = _get_int("MEMORY_L1_ROLLING_DROP_COUNT", 2)

    # L1 session_summary 增量摘要合并后的最大字符数
    # 环境变量: MEMORY_L1_SUMMARY_MAX_CHARS  默认: 800
    l1_summary_max_chars: int = _get_int("MEMORY_L1_SUMMARY_MAX_CHARS", 800)

    # L1 单轮对话摘要的最大字符数（用于 _build_incremental_summary 截断）
    # 环境变量: MEMORY_L1_TURN_SUMMARY_MAX_CHARS  默认: 25
    l1_turn_summary_max_chars: int = _get_int("MEMORY_L1_TURN_SUMMARY_MAX_CHARS", 25)

    # ── L2/L3/Sifter 开关 ───────────────────────────────
    # MemoryCoordinator 总开关，关闭后 agent 直接写 session_pool，不经 coordinator
    # 环境变量: MEMORY_COORDINATOR_ENABLED  默认: true
    memory_coordinator_enabled: bool = _get_bool("MEMORY_COORDINATOR_ENABLED", True)

    # Token 预算强制执行开关，关闭后不裁剪输入/不限制输出
    # 环境变量: TOKEN_BUDGET_ENFORCED  默认: true
    # 关闭后输入可能超预算，仅用于调试或紧急回滚
    token_budget_enforced: bool = _get_bool("TOKEN_BUDGET_ENFORCED", True)

    # L2 图记忆（Neo4j）开关，关闭后 coordinator 跳过 L2 写入
    # 环境变量: GRAPH_MEMORY_ENABLED  默认: true
    # Neo4j 不可用时 coordinator 会自动禁用，无需手动关闭
    l2_memory_enabled: bool = _get_bool("GRAPH_MEMORY_ENABLED", True)

    # L3 审计账本（SQLite）开关，关闭后 coordinator 跳过 L3 写入
    # 环境变量: L3_LEDGER_ENABLED  默认: true
    l3_ledger_enabled: bool = _get_bool("L3_LEDGER_ENABLED", True)

    # Sifter 对话沉淀筛选器开关，关闭后 coordinator 跳过偏好提取
    # 环境变量: SIFTER_ENABLED  默认: true
    sifter_enabled: bool = _get_bool("SIFTER_ENABLED", True)

    # ── Sifter 关键词 ───────────────────────────────────
    # 触发长期记忆沉淀的热词列表（逗号分隔）
    # 环境变量: MEMORY_SIFTER_KEYWORDS
    # 默认: 预算,自驾,公交,步行,高铁,西安,咸阳,宝鸡,喜欢,偏好
    sifter_hot_keywords: tuple = _get_str_list(
        "MEMORY_SIFTER_KEYWORDS",
        "预算,自驾,公交,步行,高铁,西安,咸阳,宝鸡,喜欢,偏好,非遗,皮影,剪纸,刺绣,泥塑,社火,秦腔"
    )

    # Sifter 默认置信度（整数除以100，如45→0.45）
    # 用于 budget/travel_mode 等强信号偏好类型
    # 环境变量: MEMORY_SIFTER_CONFIDENCE  默认: 45 → 0.45
    sifter_confidence_default: float = float(
        _get_int("MEMORY_SIFTER_CONFIDENCE", 45) / 100.0
    )

    # Sifter 低置信度（整数除以100，如35→0.35）
    # 用于 region_interest/interest 等弱信号偏好类型
    # 环境变量: MEMORY_SIFTER_CONFIDENCE_LOW  默认: 35 → 0.35
    sifter_confidence_low: float = float(
        _get_int("MEMORY_SIFTER_CONFIDENCE_LOW", 35) / 100.0
    )

    # Sifter 提取的偏好值最大字符数（超出截断）
    # 环境变量: MEMORY_SIFTER_PREF_VALUE_MAX_CHARS  默认: 40
    sifter_pref_value_max_chars: int = _get_int("MEMORY_SIFTER_PREF_VALUE_MAX_CHARS", 40)

    # 对话历史最大轮数（超过后裁剪最旧记录）
    # 环境变量: CONVERSATION_HISTORY_MAX_TURNS  默认: 20
    conversation_history_max_turns: int = _get_int("CONVERSATION_HISTORY_MAX_TURNS", 20)

    # 对话压缩触发阈值（轮数达到此值时触发上下文压缩）
    # 应小于 conversation_history_max_turns
    # 环境变量: CONVERSATION_COMPRESS_THRESHOLD  默认: 15
    conversation_compress_threshold: int = _get_int("CONVERSATION_COMPRESS_THRESHOLD", 15)


memory_budget = MemoryBudgetConfig()

from loguru import logger
logger.info(
    f"📋 记忆预算配置: "
    f"input={memory_budget.input_budget}/{memory_budget.input_budget_min}-{memory_budget.input_budget_max}, "
    f"output={memory_budget.output_budget_default}/{memory_budget.output_budget_min}-{memory_budget.output_budget_max}, "
    f"compression={memory_budget.compression_token_budget}, "
    f"L1_window={memory_budget.l1_recent_limit}, "
    f"coordinator={memory_budget.memory_coordinator_enabled}, "
    f"budget_enforced={memory_budget.token_budget_enforced}, "
    f"L2={memory_budget.l2_memory_enabled}, L3={memory_budget.l3_ledger_enabled}, "
    f"sifter={memory_budget.sifter_enabled}"
)
