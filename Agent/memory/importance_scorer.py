# -*- coding: utf-8 -*-
"""
记忆重要性评分器 — 三维简化模型

针对非遗+旅行规划场景优化：
- 决策密度 (0.40): 是否包含用户明确选择/决定
- 实体丰富度 (0.35): 非遗名、地名、路线关键词数量
- 信息密度 (0.25): 具体信息 vs 闲聊寒暄
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from loguru import logger


@dataclass
class MemoryScore:
    decision_density: float   # 决策密度 (0-1)
    entity_richness: float    # 实体丰富度 (0-1)
    info_density: float       # 信息密度 (0-1)

    @property
    def composite(self) -> float:
        return (
            0.40 * self.decision_density +
            0.35 * self.entity_richness +
            0.25 * self.info_density
        )


class ImportanceScorer:
    """记忆重要性评分器 — 三维模型"""

    # ── 决策关键词 ──
    DECISION_KEYWORDS = [
        '确定', '选', '就要', '定了', '按这个', '就这样', '可以',
        '决定', '选择', '改为', '换成', '增加', '减少', '取消',
        '确认', '同意', '没问题', '行', '好的', '就这样吧',
    ]

    # ── 非遗名模式 ──
    HERITAGE_PATTERN = re.compile(
        r'(皮影|秦腔|剪纸|泥塑|老腔|鼓乐|面花|刺绣|木版年画'
        r'|社火|碗碗腔|眉户|腰鼓|民歌|花鼓|非遗|文化遗产)'
    )

    # ── 地名模式 ──
    LOCATION_PATTERN = re.compile(
        r'(西安|咸阳|宝鸡|渭南|延安|汉中|安康|商洛|铜川|榆林'
        r'|华县|华阴|韩城|兴平|武功|乾县|礼泉|泾阳|三原|蓝田'
        r'|长安|临潼|鄠邑|周至|扶风|岐山|凤翔|陇县|千阳)'
    )

    # ── 规划关键词 ──
    PLAN_KEYWORDS = [
        '行程', '路线', '旅游', '出游', '天数', '预算', '出发',
        '自驾', '高铁', '飞机', '住宿', '酒店', '民宿',
    ]

    def score_conversation_turn(self, content: str, role: str = 'user',
                                 has_plan: bool = False) -> MemoryScore:
        """对单轮对话评分"""
        if not content:
            return MemoryScore(0.0, 0.0, 0.0)

        decision_density = self._calc_decision_density(content, has_plan)
        entity_richness = self._calc_entity_richness(content)
        info_density = self._calc_info_density(content)

        return MemoryScore(
            decision_density=min(decision_density, 1.0),
            entity_richness=min(entity_richness, 1.0),
            info_density=min(info_density, 1.0),
        )

    def score_session(self, turns: List[Dict],
                       summary: Optional[Dict] = None) -> float:
        """对整个会话评分 (0-1)，取各轮加权平均"""
        if not turns:
            return 0.0

        total = 0.0
        count = 0
        for turn in turns:
            content = turn.get('content', '')
            role = turn.get('role', 'user')
            score = self.score_conversation_turn(content, role)
            total += score.composite
            count += 1

        return total / max(count, 1)

    def apply_time_decay(self, score: float, days_since: int) -> float:
        """时间衰减: score *= decay_rate^(days_since / 30)"""
        from Agent.config.memory_budget import memory_budget
        rate = memory_budget.importance_decay_rate
        return score * (rate ** (days_since / 30.0))

    def should_retain(self, score: float, threshold: float = 0.15) -> bool:
        """判断记忆是否应保留"""
        return score >= threshold

    # ── 内部计算方法 ──

    def _calc_decision_density(self, content: str, has_plan: bool = False) -> float:
        """决策密度: 关键词匹配 + 规划数据存在 + 数字+量词"""
        score = 0.0

        # 显式决策词
        for kw in self.DECISION_KEYWORDS:
            if kw in content:
                score += 0.3
                break  # 一个决策词足够

        # 数字+量词（天数、预算、人数）
        if re.search(r'\d+[\s]*(?:天|人|元|块|万|小时|分钟|公里)', content):
            score += 0.2

        # 路线/行程关键词
        for kw in self.PLAN_KEYWORDS:
            if kw in content:
                score += 0.2
                break

        # 有规划数据
        if has_plan:
            score += 0.3

        return min(score, 1.0)

    def _calc_entity_richness(self, content: str) -> float:
        """实体丰富度: 非遗名 + 地名计数，归一化到 [0, 1]"""
        heritage_count = len(self.HERITAGE_PATTERN.findall(content))
        location_count = len(self.LOCATION_PATTERN.findall(content))

        raw = heritage_count * 0.15 + location_count * 0.1
        return min(raw, 1.0)

    def _calc_info_density(self, content: str) -> float:
        """信息密度: 实体字符占比"""
        if len(content) < 10:
            return 0.0

        # 非闲聊字符（中文字 + 数字）
        meaningful = len(re.findall(r'[一-鿿\d]', content))
        ratio = meaningful / max(len(content), 1)

        if ratio > 0.5:
            return 1.0
        elif ratio > 0.3:
            return 0.5
        return 0.2


_importance_scorer: Optional[ImportanceScorer] = None


def get_importance_scorer() -> ImportanceScorer:
    global _importance_scorer
    if _importance_scorer is None:
        _importance_scorer = ImportanceScorer()
    return _importance_scorer
