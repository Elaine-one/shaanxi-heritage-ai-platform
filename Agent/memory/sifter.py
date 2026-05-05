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

如果消息不包含任何旅行偏好信息，返回空数组 []。
只返回 JSON 数组，不要包含其他文字。"""

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
            response = await asyncio.wait_for(llm._call_model(prompt), timeout=15)
            if response and response.get('success'):
                answer = response.get('content', '').strip().lower()
                return 'true' in answer
        except Exception as e:
            logger.debug(f"LLM判断偏好失败，降级为关键词: {e}")
        return self.should_persist(role, content)

    def extract_preferences(self, content: str) -> List[Dict[str, Any]]:
        if not content:
            return []
        prefs: List[Dict[str, Any]] = []
        max_chars = memory_budget.sifter_pref_value_max_chars
        conf = memory_budget.sifter_confidence_default
        conf_low = memory_budget.sifter_confidence_low
        keywords = memory_budget.sifter_hot_keywords

        budget_kws = [k for k in keywords if k in ("预算",)]
        travel_kws = [k for k in keywords if k in ("自驾", "公交", "步行", "高铁")]
        region_kws = [k for k in keywords if k in ("西安", "咸阳", "宝鸡")]
        interest_kws = [k for k in keywords if k in ("喜欢", "偏好")]
        heritage_kws = [k for k in keywords if k in ("非遗", "皮影", "剪纸", "刺绣", "泥塑", "社火", "秦腔")]

        if any(k in content for k in budget_kws):
            prefs.append({"type": "budget", "value": content[:max_chars], "confidence": conf})
        if any(k in content for k in travel_kws):
            prefs.append({"type": "travel_mode", "value": content[:max_chars], "confidence": conf})
        if any(k in content for k in region_kws):
            prefs.append({"type": "region_interest", "value": content[:max_chars], "confidence": conf_low})
        if any(k in content for k in interest_kws):
            prefs.append({"type": "interest", "value": content[:max_chars], "confidence": conf_low})
        if any(k in content for k in heritage_kws):
            matched_name = next((k for k in heritage_kws if k in content), None)
            prefs.append({"type": "heritage_interest", "value": {"heritage_name": matched_name or content[:max_chars]}, "confidence": conf_low})
        return prefs

    async def extract_preferences_async(self, content: str) -> List[Dict[str, Any]]:
        if not content:
            return []
        llm = self._get_llm_model()
        if not llm:
            return self.extract_preferences(content)
        try:
            prompt = f"{SIFTER_SYSTEM_PROMPT}\n\n{SIFTER_USER_PROMPT.format(content=content)}"
            response = await asyncio.wait_for(llm._call_model(prompt), timeout=20)
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
