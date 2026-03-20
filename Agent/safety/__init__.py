# -*- coding: utf-8 -*-
"""
安全检测模块
基于规则的安全检测，替代LLM意图识别
"""

from Agent.safety.safety_checker import (
    SafetyChecker,
    SafetyResult,
    check_safety,
    get_safety_checker,
)

__all__ = [
    'SafetyChecker',
    'SafetyResult',
    'check_safety',
    'get_safety_checker',
]
