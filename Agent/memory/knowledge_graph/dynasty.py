# -*- coding: utf-8 -*-
"""
朝代 Mixin — 朝代节点创建 / 关键词匹配 / ORIGINATED_IN 关系 / 批量同步
从 heritage.history 文本中识别非遗起源朝代并写入知识图谱
"""

import re
from typing import Dict, Any, List, Optional, Set
from loguru import logger


class DynastyMixin:
    """朝代实体与匹配器的写操作"""

    driver: object = None

    # ──────────────────────────────
    # 标准朝代表
    # ──────────────────────────────

    DYNASTY_TABLE: Dict[str, tuple] = {
        '上古': (None, -2071, None),
        '夏': (-2070, -1600, None),
        '商': (-1600, -1046, '殷'),
        '西周': (-1046, -771, '镐京'),
        '东周': (-770, -256, '洛邑'),
        '秦': (-221, -206, '咸阳'),
        '西汉': (-206, 25, '长安'),
        '东汉': (25, 220, '洛阳'),
        '三国': (220, 280, None),
        '晋': (265, 420, None),
        '南北朝': (420, 589, None),
        '隋': (581, 618, '大兴'),
        '唐': (618, 907, '长安'),
        '五代十国': (907, 960, None),
        '宋': (960, 1279, '开封/临安'),
        '元': (1271, 1368, '大都'),
        '明': (1368, 1644, '北京'),
        '清': (1644, 1912, '北京'),
        '民国': (1912, 1949, '南京'),
        '当代': (1949, None, '北京'),
    }

    # ──────────────────────────────
    # 别名映射（历史文本中常见的变体 → 标准名）
    # ──────────────────────────────

    DYNASTY_ALIASES: Dict[str, str] = {
        # 唐
        '唐代': '唐', '唐朝': '唐', '盛唐': '唐', '中唐': '唐',
        '晚唐': '唐', '初唐': '唐', '大唐': '唐',
        # 清
        '清代': '清', '清朝': '清', '清光绪年间': '清',
        '清乾隆年间': '清', '清同治年间': '清', '清康熙年间': '清',
        '清末': '清', '晚清': '清', '清初': '清',
        # 明
        '明代': '明', '明朝': '明', '明嘉靖年间': '明',
        '明万历年间': '明', '明末': '明', '明末清初': '明',
        '明正德': '明',
        # 宋
        '宋代': '宋', '宋朝': '宋', '北宋': '宋', '南宋': '宋',
        # 元
        '元代': '元', '元朝': '元', '元灭金': '元',
        # 秦
        '秦代': '秦', '秦朝': '秦', '秦汉时期': '秦', '秦汉': '秦',
        '先秦时期': '东周', '先秦': '东周',
        # 汉
        '汉代': '东汉', '汉朝': '东汉', '西汉时期': '西汉',
        '汉武帝': '西汉',
        # 隋
        '隋代': '隋', '隋朝': '隋', '隋唐': '隋',
        # 周
        '周代': '东周', '商周时期': '西周', '商周': '西周',
        '西周时期': '西周', '东周时期': '东周',
        # 南北朝
        '南北朝时期': '南北朝',
        # 民国
        '民国时期': '民国', '近现代以来': '当代',
        # 当代
        '现代': '当代', '新中国成立后': '当代', '改革开放后': '当代',
        # 上古
        '远古时期': '上古', '上古时期': '上古', '原始社会': '上古',
        '新石器时代': '上古', '旧石器时代': '上古',
    }

    # ──────────────────────────────
    # 直接关键词匹配（在 history 文本中搜索这些词直接得到朝代）
    # ──────────────────────────────

    # 按匹配优先级排列的正则 → 朝代名
    # 注意：必须足够精确避免误匹配（如 "元" 匹配到 "万元"、"公元"）
    DIRECT_PATTERNS: List[tuple] = [
        # 必须带朝代/时期/年间标识的
        (r'秦汉(?:时期)?', '秦'),
        (r'秦(?:朝|代|时期|代)', '秦'),
        (r'西汉(?:时期)?', '西汉'),
        (r'东汉(?:时期)?', '东汉'),
        (r'隋(?:朝|代)', '隋'),
        (r'唐代', '唐'),
        (r'唐朝', '唐'),
        (r'宋代', '宋'),
        (r'宋朝', '宋'),
        (r'北宋', '宋'),
        (r'南宋', '宋'),
        (r'元代', '元'),
        (r'元朝', '元'),
        (r'明代', '明'),
        (r'明朝', '明'),
        (r'清代', '清'),
        (r'清朝', '清'),
        (r'周(?:朝|代)', '东周'),
        (r'西周', '西周'),
        (r'东周', '东周'),
        (r'商(?:朝|代|周)', '商'),
        (r'民国(?:时期)?', '民国'),
        # 当代
        (r'当代|新中国成立|改革开放后', '当代'),
        # 上古
        (r'远古|上古时期|原始社会|旧石器|新石器', '上古'),
        # 年号匹配（常见于陕西非遗文本）
        (r'光绪', '清'),
        (r'乾隆', '清'),
        (r'同治', '清'),
        (r'康熙', '清'),
        (r'万历', '明'),
        (r'嘉靖', '明'),
    ]

    # 复合朝代模式 → 多朝代集合（如 "唐宋" → 唐+宋）
    MULTI_DYNASTY_PATTERNS: List[tuple] = [
        (r'隋唐(?:时期)?', {'隋', '唐'}),
        (r'唐宋(?:时期)?', {'唐', '宋'}),
        (r'宋元(?:时期)?', {'宋', '元'}),
        (r'明清(?:时期)?', {'明', '清'}),
        (r'金元(?:时期)?', {'宋', '元'}),
        (r'夏商周', {'夏', '商', '西周'}),
    ]

    # ──────────────────────────────
    # 节点
    # ──────────────────────────────

    def create_dynasty_node(self, name: str, start_year: int = None,
                            end_year: int = None, capital: str = '') -> bool:
        """创建朝代节点（MERGE 保证幂等）"""
        if name not in self.DYNASTY_TABLE:
            logger.warning(f"未知朝代 '{name}'，跳过节点创建")
            return False
        return self._merge_node('Dynasty', 'name',
                                name=name, start_year=start_year,
                                end_year=end_year, capital=capital)

    # ──────────────────────────────
    # 关系
    # ──────────────────────────────

    def create_originated_in_relation(self, heritage_id: int,
                                      dynasty_name: str) -> bool:
        """创建 Heritage -[ORIGINATED_IN]-> Dynasty 关系"""
        return self._merge_relation('Heritage', heritage_id,
                                    'ORIGINATED_IN', 'Dynasty', dynasty_name)

    # ──────────────────────────────
    # 匹配逻辑
    # ──────────────────────────────

    @classmethod
    def match_dynasties_from_text(cls, history_text: str) -> Set[str]:
        """从 history 文本中识别起源朝代（纯规则，不含 LLM）

        Args:
            history_text: 非遗项目的 history 字段

        Returns:
            标准朝代名集合（一个非遗可能起源多个朝代）
        """
        if not history_text or not history_text.strip():
            return set()

        matched: Set[str] = set()

        # 第一轮：直接正则匹配
        for pattern, dynasty in cls.DIRECT_PATTERNS:
            if re.search(pattern, history_text):
                matched.add(dynasty)

        # 第二轮：复合朝代模式（如 "唐宋" → 唐+宋）
        for pattern, dynasties in cls.MULTI_DYNASTY_PATTERNS:
            if re.search(pattern, history_text):
                matched.update(dynasties)

        # 第三轮：别名表匹配（处理变体）
        for alias, standard in cls.DYNASTY_ALIASES.items():
            if alias in history_text:
                matched.add(standard)

        # 去重：移除被更精确朝代覆盖的泛称
        # 如同时有 "秦" 和 "上古"，去掉 "上古"
        if len(matched) > 1:
            specific_dynasties = matched - {'上古'}
            if specific_dynasties:
                matched = specific_dynasties

        return matched

    # ──────────────────────────────
    # 批量同步
    # ──────────────────────────────

    def sync_dynasties_from_heritage_list(self, heritage_list: List[Dict]) -> Dict[str, int]:
        """从 heritage 列表同步朝代到知识图谱，返回统计信息"""
        dynasty_node_count = 0
        relation_count = 0
        heritage_with_dynasty = 0

        # 先确保所有标准朝代节点存在
        for name, (start, end, capital) in self.DYNASTY_TABLE.items():
            if self.create_dynasty_node(name, start, end, capital or ''):
                dynasty_node_count += 1

        # 逐条匹配并创建关系
        for heritage in heritage_list:
            hid = heritage.get('id')
            history = heritage.get('history', '')
            if not history:
                continue

            dynasties = self.match_dynasties_from_text(history)
            if dynasties:
                heritage_with_dynasty += 1
                for d in dynasties:
                    if self.create_originated_in_relation(hid, d):
                        relation_count += 1

        logger.info(
            f"朝代同步完成: "
            f"{dynasty_node_count} 个 Dynasty 节点, "
            f"{heritage_with_dynasty} 个 Heritage 匹配到朝代, "
            f"{relation_count} 条 ORIGINATED_IN 关系"
        )
        return {
            'dynasty_nodes': dynasty_node_count,
            'heritage_matched': heritage_with_dynasty,
            'originated_in_relations': relation_count,
        }

    # ──────────────────────────────
    # LLM 复核（供外部脚本/工具调用）
    # ──────────────────────────────

    @staticmethod
    def build_llm_verify_prompt(history_text: str, rule_matched: Set[str]) -> str:
        """构建 LLM 复核 prompt"""
        matched_str = ', '.join(sorted(rule_matched)) if rule_matched else '（无）'
        return f"""你是陕西非遗历史文化专家。请复核以下非遗项目的起源朝代识别结果。

【历史渊源文本】
{history_text[:2000]}

【规则匹配到的朝代】
{matched_str}

请完成以下任务，仅返回 JSON：
1. confirm: 确认正确的朝代列表（使用标准朝代名：上古/夏/商/西周/东周/秦/西汉/东汉/三国/晋/南北朝/隋/唐/五代十国/宋/元/明/清/民国/当代）
2. remove: 需要删除的误匹配朝代列表
3. add: 规则遗漏的朝代列表
4. reason: 简短说明修正理由（50字以内）

返回格式：{{"confirm": ["唐", "宋"], "remove": [], "add": ["秦"], "reason": "..."}}"""  # noqa: E501
