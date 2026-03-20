# -*- coding: utf-8 -*-
"""
Agent 提示模板
使用结构化JSON输出，支持JSON和Markdown混合格式
"""

from langchain_core.prompts import PromptTemplate


REACT_PROMPT_TEMPLATE = PromptTemplate(
    template="""{system_prompt}

# 工具列表

{tool_descriptions}

# 输出格式（必须严格遵守）

你需要根据情况选择以下两种输出格式之一：

## 格式一：调用工具（纯JSON）

当需要查询数据时，输出以下JSON格式：
```json
{{
    "thought": "分析问题和下一步行动",
    "action": "工具名称",
    "action_input": {{
        "参数名": "参数值"
    }}
}}
```

## 格式二：最终回答（Markdown内容）

当可以回答用户时，直接输出Markdown格式的内容，不需要JSON包装。
使用Markdown标题、列表、表格等格式组织内容。

# 执行规则

1. 简单问题（打招呼、常识问题）直接输出Markdown回答
2. 需要查询数据时，输出JSON调用工具
3. 每次只调用一个工具
4. 收到工具结果后，继续处理或输出Markdown回答
5. 不要重复调用同一工具
6. 最终回答必须使用Markdown格式，内容丰富、结构清晰
7. **专注于用户当前问题，不要被规划摘要带偏**

# 正确示例

示例1 - 调用工具（JSON格式）：
```json
{{
    "thought": "用户需要查询${city}的经纬度，调用maps_geo工具",
    "action": "maps_geo",
    "action_input": {{
        "address": "${city}"
    }}
}}
```

示例2 - 最终回答（Markdown格式，直接输出，不用JSON包装）：
## ${city}经纬度信息

${city}的经纬度坐标为：
- **纬度**：${latitude}
- **经度**：${longitude}

### 地理位置
${city}位于${region}，是${province}省会...

# 错误示例（禁止）

❌ 用户问"经纬度"时调用 heritage_search
❌ 最终回答使用JSON包装
❌ 调用工具时不使用JSON格式
❌ 使用单引号代替双引号（JSON中）
❌ action_input 使用字符串而非对象

{context}

# 用户问题

{question}

请根据情况选择合适的输出格式：""",
    input_variables=["system_prompt", "tool_descriptions", "context", "question"]
)


AI_SUGGESTIONS_PROMPT = PromptTemplate(
    template="""基于以下信息，为用户提供旅游建议：

出发地: {departure_location}
旅行天数: {travel_days}天
人数: {people_count}人
预算: {budget_range}
交通方式: {travel_mode}
非遗项目: {heritage_names}
特殊要求: {special_requirements}
当前日期: {current_date}

【重要时间说明】
- 今天是 {current_date}
- 出发日期默认为明天（用户计划出行，不是今天立即出发）
- 行程第1天 = 明天，第2天 = 后天，以此类推

请提供：
1. 行程安排建议（使用明天作为出发日期）
2. 注意事项
3. 文化体验推荐
4. 美食推荐

要求简洁实用，突出非遗文化特色。特别注意用户的特殊要求，在建议中予以体现。""",
    input_variables=["departure_location", "travel_days", "people_count", "budget_range", "travel_mode", "heritage_names", "special_requirements", "current_date"]
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


def get_react_prompt(system_prompt: str, tool_descriptions: str, context: str, question: str) -> str:
    return REACT_PROMPT_TEMPLATE.format(
        system_prompt=system_prompt,
        tool_descriptions=tool_descriptions,
        context=context,
        question=question
    )


def get_ai_suggestions_prompt(departure_location: str, travel_days: int, people_count: int,
                              budget_range: str, travel_mode: str, heritage_names: str, 
                              special_requirements: str = "无", current_date: str = None) -> str:
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
        special_requirements=special_requirements,
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
