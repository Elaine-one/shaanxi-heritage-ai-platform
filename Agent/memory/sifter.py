# -*- coding: utf-8 -*-
"""
Sifter: 对话沉淀筛选器
用于判断一轮对话是否值得进入长期记忆，并提取结构化偏好。
优先使用 LLM 提取结构化偏好，LLM 不可用时降级为关键词匹配。
"""

import json
import asyncio
from typing import Any, Dict, List, Optional
from loguru import logger

from Agent.config.memory_budget import memory_budget

SIFTER_SYSTEM_PROMPT = """你是一个旅行偏好提取器。从用户消息中提取旅行偏好，返回 JSON 数组。

支持的偏好类型：
- budget: 预算偏好，value 包含 amount(数字) 和 currency(货币)
- travel_mode: 出行方式偏好，value 包含 prefer(偏好列表) 和 exclude(排除列表)
- region_interest: 地区兴趣，value 包含 regions(地区名列表)
- interest: 兴趣偏好，value 包含 category(类别) 和 detail(描述)
- group_preference: 团队偏好，value 包含 group_type(如家庭/朋友/独自) 和 notes(备注)
- heritage_interest: 非遗项目兴趣，value 包含 heritage_name(项目名称) 和 heritage_id(项目ID整数，如已知)

每项必须包含：type, value(结构化对象), confidence(0-1浮点数), source(原文片段)

【示例输出】
[{"type":"budget","value":{"amount":5000,"currency":"CNY"},"confidence":0.8,"source":"预算5000"},
 {"type":"region_interest","value":{"regions":["西安","延安"]},"confidence":0.7,"source":"想去西安和延安"},
 {"type":"heritage_interest","value":{"heritage_name":"皮影戏"},"confidence":0.65,"source":"看看皮影戏"}]

【重要规则】
- 注意否定：如果用户说"不想要/不去/不喜欢/排除"某物，不要将其提取为正向偏好
- 仅返回 JSON 数组，禁止 markdown 代码块包裹
- 如果消息不包含任何旅行偏好信息，返回空数组 []"""

SIFTER_USER_PROMPT = """请从以下用户消息中提取旅行偏好：

用户消息：{content}"""


class Sifter:

    def __init__(self):
        self._llm_model = None

    def _get_llm_model(self):
        if self._llm_model is not None:
            return self._llm_model
        try:
            from Agent.agent import get_travel_planner
            planner = get_travel_planner()
            if planner and planner.llm_model:
                self._llm_model = planner.llm_model
                return self._llm_model
        except Exception as e:
            logger.debug(f"获取LLM模型失败: {e}")
        return None

    def should_persist(self, role: str, content: str) -> bool:
        if role != "user" or not content:
            return False
        return any(k in content for k in memory_budget.sifter_hot_keywords)

    async def should_persist_async(self, role: str, content: str) -> bool:
        if role != "user" or not content:
            return False
        llm = self._get_llm_model()
        if not llm:
            return self.should_persist(role, content)
        try:
            prompt = f"判断以下用户消息是否包含旅行偏好信息（预算/出行方式/地区/兴趣/团队等），只回答 true 或 false：\n{content}"
            response = await asyncio.wait_for(llm.call_model(prompt), timeout=15)
            if response and response.get('success'):
                answer = response.get('content', '').strip().lower()
                return 'true' in answer
        except Exception as e:
            logger.debug(f"LLM判断偏好失败，降级为关键词: {e}")
        return self.should_persist(role, content)

    # ── 可配置偏好提取规则 ──
    # 每条规则: (偏好类型, 关键词列表, 置信度)
    # 可通过环境变量 SIFTER_RULES_JSON 扩展
    @classmethod
    def _get_extraction_rules(cls):
        import os
        rules_json = os.getenv("SIFTER_RULES_JSON")
        if rules_json:
            try:
                import json
                return json.loads(rules_json)
            except Exception:
                pass
        # 默认规则集
        return [
            {"type": "budget", "keywords": ["预算", "花费", "费用", "价格", "省钱"], "confidence_key": "default"},
            {"type": "travel_mode", "keywords": ["自驾", "公交", "步行", "高铁", "飞机", "火车"], "confidence_key": "default"},
            {"type": "region_interest", "keywords": ["西安", "咸阳", "宝鸡", "渭南", "延安", "汉中"], "confidence_key": "low"},
            {"type": "interest", "keywords": ["喜欢", "偏好", "感兴趣", "热爱"], "confidence_key": "low"},
            {"type": "heritage_interest", "keywords": ["非遗", "皮影", "剪纸", "刺绣", "泥塑", "社火", "秦腔", "老腔", "鼓乐"], "confidence_key": "low"},
            {"type": "group_preference", "keywords": ["带孩子", "老人", "朋友", "情侣", "独自", "家庭"], "confidence_key": "low"},
            {"type": "pace", "keywords": ["深度", "打卡", "轻松", "紧凑", "自由行"], "confidence_key": "low"},
        ]

    def extract_preferences(self, content: str) -> List[Dict[str, Any]]:
        if not content:
            return []
        prefs: List[Dict[str, Any]] = []
        conf_default = memory_budget.sifter_confidence_default
        conf_low = memory_budget.sifter_confidence_low

        for rule in self._get_extraction_rules():
            keywords = rule.get("keywords", [])
            pref_type = rule.get("type", "")
            conf_key = rule.get("confidence_key", "default")
            confidence = conf_low if conf_key == "low" else conf_default

            if any(k in content for k in keywords):
                if pref_type == "heritage_interest":
                    matched_name = next((k for k in keywords if k in content), None)
                    prefs.append({
                        "type": pref_type,
                        "value": {"heritage_name": matched_name or content[:80]},
                        "confidence": min(confidence, 0.25),
                    })
                else:
                    matched_kw = next((k for k in keywords if k in content), "")
                    prefs.append({
                        "type": pref_type,
                        "value": matched_kw or content[:80],
                        "confidence": confidence,
                    })
        return prefs

    async def extract_preferences_async(self, content: str) -> List[Dict[str, Any]]:
        if not content:
            return []
        llm = self._get_llm_model()
        if not llm:
            return self.extract_preferences(content)
        try:
            prompt = f"{SIFTER_SYSTEM_PROMPT}\n\n{SIFTER_USER_PROMPT.format(content=content)}"
            response = await asyncio.wait_for(llm.call_model(prompt), timeout=20)
            if not response or not response.get('success'):
                return self.extract_preferences(content)

            raw = response.get('content', '').strip()
            json_str = raw
            if '```' in raw:
                start = raw.find('[')
                end = raw.rfind(']') + 1
                if start >= 0 and end > start:
                    json_str = raw[start:end]
            elif not raw.startswith('['):
                start = raw.find('[')
                end = raw.rfind(']') + 1
                if start >= 0 and end > start:
                    json_str = raw[start:end]

            prefs = json.loads(json_str)
            if isinstance(prefs, list):
                valid = [
                    p for p in prefs
                    if isinstance(p, dict) and 'type' in p and 'value' in p and 'confidence' in p
                ]
                if valid:
                    return valid
                logger.debug("LLM提取偏好格式不完整，降级为关键词")
        except (json.JSONDecodeError, asyncio.TimeoutError) as e:
            logger.debug(f"LLM偏好提取失败，降级为关键词: {e}")
        except Exception as e:
            logger.debug(f"LLM偏好提取异常，降级为关键词: {e}")
        return self.extract_preferences(content)


_sifter_instance: Optional[Sifter] = None


def get_sifter() -> Sifter:
    global _sifter_instance
    if _sifter_instance is None:
        _sifter_instance = Sifter()
    return _sifter_instance
