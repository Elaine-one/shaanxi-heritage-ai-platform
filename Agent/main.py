# -*- coding: utf-8 -*-
"""
Agent 模块入口

此文件保留用于向后兼容。
如需使用 Agent 功能，请从以下位置导入：
- Agent.agent.agent.Agent - Agent 主类
- Agent.agent.agent.get_agent - 获取 Agent 实例
- Agent.agent.travel_planner.TravelPlanner - 旅游规划器
"""

from Agent.agent.agent import Agent, get_agent
from Agent.agent.travel_planner import TravelPlanner, get_travel_planner

__all__ = [
    'Agent',
    'get_agent',
    'TravelPlanner',
    'get_travel_planner',
]
