# -*- coding: utf-8 -*-
"""
Agent 提示模板
使用 LangChain 1.0 PromptTemplate 统一管理
"""

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from .react import REACT_SYSTEM_PROMPT


REACT_PROMPT_TEMPLATE = PromptTemplate(
    template="""{system_prompt}

工具详情:
{tool_descriptions}

可用工具列表: [{tool_names}]

=== 输出格式（严格遵守）===

Thought: 分析问题，决定是否需要调用工具
Action: 工具名称（如需调用）
Action Input: {{"参数名": "参数值"}}

或者直接回答:

Thought: 分析问题，已知信息足够
Final Answer: 你的完整回答

=== 规则 ===

1. 简单问题（打招呼、常识问题）直接 Final Answer
2. 需要查询数据时，调用工具
3. 每次只调用一个工具
4. 收到 Observation 后，必须给出 Final Answer 或调用下一个工具
5. 不要重复调用同一工具
6. 【重要】Final Answer 必须包含完整的回答内容，不要把详细信息放在 Thought 中

{context}

=== 开始 ===

Question: {question}
Thought: """,
    input_variables=["system_prompt", "tool_descriptions", "tool_names", "context", "question"]
)


TRAVEL_PLAN_PROMPT = PromptTemplate(
    template="""请为以下陕西非遗项目制定{travel_days}天旅游规划:

{heritage_info}

用户需求:
- 出发地: {start_location}
- 天数: {travel_days}
- 交通: {transport_preference}
- 预算: {budget_range}
- 当前日期: {current_date}

要求:
1. 每天安排1-2个主要非遗项目，穿插附近景点
2. 行程灵活，留有余地
3. 突出文化体验深度
4. 必须返回纯 JSON 格式，包含 itinerary, travel_tips, cultural_notes
5. 注意：使用当前日期{current_date}作为出发日期，不要使用过去的日期
""",
    input_variables=["heritage_info", "travel_days", "start_location", "transport_preference", "budget_range", "current_date"]
)


AI_SUGGESTIONS_PROMPT = PromptTemplate(
    template="""基于以下信息，为用户提供旅游建议：

出发地: {departure_location}
旅行天数: {travel_days}天
人数: {people_count}人
预算: {budget_range}
交通方式: {travel_mode}
非遗项目: {heritage_names}
当前日期: {current_date}

请提供：
1. 行程安排建议（注意：使用当前日期{current_date}作为出发日期，不要使用过去的日期）
2. 注意事项
3. 文化体验推荐
4. 美食推荐

要求简洁实用，突出非遗文化特色。""",
    input_variables=["departure_location", "travel_days", "people_count", "budget_range", "travel_mode", "heritage_names", "current_date"]
)


CONVERSATION_SUMMARY_PROMPT = PromptTemplate(
    template="""你是一位专业的**对话历史分析专家**，擅长从复杂的对话记录中提取关键信息并进行精准摘要。

【任务目标】
请对以下对话历史进行智能摘要，提取最重要的信息，以便为后续对话提供上下文支持。

【摘要要求】
1. **信息优先级**：
   - 用户的明确需求和偏好（如：想去的地方、感兴趣的非遗类型、时间安排等）
   - 已确定的重要信息（如：已查询的天气、已推荐的景点、已制定的行程等）
   - 关键的决策点或约束条件（如：预算限制、时间限制、特殊要求等）

2. **摘要格式**：
   - 使用简洁、清晰的语言
   - 按信息类型分类整理（用户需求、已确定信息、待解决问题等）
   - 避免冗余和无关信息
   - 保持客观，不添加主观评价

3. **长度控制**：
   - 摘要长度控制在 200-500 字之间
   - 确保信息密度高，每句话都有价值

4. **角色定位**：
   - 你是专业的信息提取专家
   - 你的摘要将被用于辅助后续的旅游规划决策

【对话历史】
{conversation_history}

请生成摘要：""",
    input_variables=["conversation_history"]
)


KNOWLEDGE_QA_PROMPT = PromptTemplate(
    template="""你是一个陕西非物质文化遗产专家。请根据你的知识回答以下问题：

问题类别：{category}
问题：{question}

请提供准确、详细的回答。如果涉及具体项目，请尽量包含历史背景、文化意义和特色亮点。

回答：""",
    input_variables=["category", "question"]
)


PLAN_EDIT_PROMPT = PromptTemplate(
    template="""你是一个专业的旅游规划师。请根据用户的要求修改旅游规划。

当前规划：
{current_plan}

用户修改要求：{edit_request}

请分析用户意图，修改规划并返回完整的JSON格式规划数据。确保修改后：
1. 行程安排合理
2. 路线逻辑清晰
3. 包含必要的非遗项目信息

如果用户要求不合理，请提供替代建议。

请只返回JSON数据，不要其他解释：""",
    input_variables=["current_plan", "edit_request"]
)


def get_react_prompt(system_prompt: str, tool_descriptions: str, tool_names: str, context: str, question: str) -> str:
    """
    获取 ReAct 提示词
    
    Args:
        system_prompt: 系统提示词
        tool_descriptions: 工具描述
        tool_names: 工具名称列表
        context: 上下文
        question: 用户问题
    
    Returns:
        str: 格式化后的提示词
    """
    return REACT_PROMPT_TEMPLATE.format(
        system_prompt=system_prompt,
        tool_descriptions=tool_descriptions,
        tool_names=tool_names,
        context=context,
        question=question
    )


def get_travel_plan_prompt(heritage_info: str, travel_days: int, start_location: str, 
                          transport_preference: str, budget_range: str, current_date: str = None) -> str:
    """
    获取旅游规划提示词
    """
    from datetime import datetime
    if current_date is None:
        current_date = datetime.now().strftime('%Y年%m月%d日')
    
    return TRAVEL_PLAN_PROMPT.format(
        heritage_info=heritage_info,
        travel_days=travel_days,
        start_location=start_location,
        transport_preference=transport_preference,
        budget_range=budget_range,
        current_date=current_date
    )


def get_ai_suggestions_prompt(departure_location: str, travel_days: int, people_count: int,
                              budget_range: str, travel_mode: str, heritage_names: str, current_date: str = None) -> str:
    """
    获取 AI 建议提示词
    """
    from datetime import datetime
    if current_date is None:
        current_date = datetime.now().strftime('%Y年%m月%d日')
    
    return AI_SUGGESTIONS_PROMPT.format(
        departure_location=departure_location,
        travel_days=travel_days,
        people_count=people_count,
        budget_range=budget_range,
        travel_mode=travel_mode,
        heritage_names=heritage_names,
        current_date=current_date
    )


def get_conversation_summary_prompt(conversation_history: str) -> str:
    """
    获取对话摘要提示词
    """
    return CONVERSATION_SUMMARY_PROMPT.format(conversation_history=conversation_history)


def get_knowledge_qa_prompt(category: str, question: str) -> str:
    """
    获取知识库问答提示词
    """
    return KNOWLEDGE_QA_PROMPT.format(category=category, question=question)


def get_plan_edit_prompt(current_plan: str, edit_request: str) -> str:
    """
    获取规划编辑提示词
    """
    return PLAN_EDIT_PROMPT.format(current_plan=current_plan, edit_request=edit_request)
