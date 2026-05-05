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

请严格遵循以下规则：
1. 如果用户明确指定了天数（如"改成X天"、"X天假期"、"延长到X天"），必须将 travel_days 修改为指定值
2. 如果用户指定了人数、出发地、预算等参数，必须相应修改
3. 返回完整的JSON格式规划数据

【重要】
- 严格按照用户的修改要求执行，不要省略任何参数的修改
- 如果用户说"改成7天"，travel_days 必须改为 7

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


PDF_CONTENT_PROMPT = """你是一位资深陕西非遗文化旅游规划师，正在为用户撰写一份**可直接打印使用**的专业旅行攻略文档。

# 基本信息
- **目的地**：{destination}
- **出发地**：{start_location}
- **行程天数**：{travel_days}天
- **出行日期**：{travel_dates}
- **出行方式**：{travel_mode}
- **人数**：{group_size}人
- **预算**：{budget_range}
- **天气**：{weather_summary}

# 用户需求（对话历史摘要）
{formatted_history}

# 行程骨架
{slim_itinerary_json}

# 非遗项目素材
{heritage_context_str}

# 系统建议
{sys_recs}

# 路线信息
{route_summary}

---

# 输出要求

## 一、文档结构（严格按此顺序输出7个板块）

### 板块1：行程概览
用一段话总结行程亮点，然后输出概览表格：

| 项目 | 内容 |
|-----|------|
| 目的地 | {destination} |
| 行程天数 | {travel_days}天 |
| 出行方式 | {travel_mode} |
| 预算级别 | {budget_range} |
| 出行人数 | {group_size}人 |
| 总路程 | 约{route_summary} |

然后输出 **三大亮点**，每条用 `> 🌟` 开头，如：
> 🌟 亮点一：在户县农民画院亲手绘制农民画，感受黄土高原的色彩表达

### 板块2：行前准备清单
输出分类准备表格，带勾选列：

| 类别 | 物品 | 备注 | 勾选 |
|-----|------|------|------|
| 证件 | 身份证 | 必带 | □ |
| 证件 | 学生证/老年证 | 景区优惠 | □ |
| 衣物 | ... | 根据天气 | □ |
| 电子 | 充电宝 | 必带 | □ |
| 药品 | ... | ... | □ |

### 板块3：出行方式对比
输出交通方式对比表格：

| 方式 | 预计耗时 | 预估费用 | 舒适度 | 推荐指数 |
|-----|---------|---------|--------|---------|
| 自驾 | X小时 | ¥XXX | ★★★★ | ★★★★★ |
| 高铁+公交 | X小时 | ¥XXX | ★★★ | ★★★ |
| ... | ... | ... | ... | ... |

用 `> 💡` 标注推荐方案，如：
> 💡 推荐自驾出行，景点间距离较远，自驾灵活性最高

### 板块4：费用预算明细
输出分类预算表格：

| 费用项目 | 明细 | 预估金额(元/人) |
|---------|------|----------------|
| 交通费 | 高铁往返+市内交通 | ¥XXX |
| 住宿费 | X晚经济型酒店 | ¥XXX |
| 餐饮费 | X天三餐 | ¥XXX |
| 门票费 | X个景点 | ¥XXX |
| 体验费 | 非遗手工体验 | ¥XXX |
| 其他 | 纪念品+备用金 | ¥XXX |
| **合计** | | **¥XXX** |

### 板块5：每日行程（核心板块，每天一节）

每天的标题格式：`### 第X天（{day_dates_str}）：主题名`

每天**必须**按以下顺序输出5个部分：

**（1）当日天气**（用 `> 💡` 引用块）
> 💡 今日天气：晴，15~28°C，适宜户外活动

**（2）今日行程安排表格**

| 时间 | 项目 | 地点 | 时长 | 体验类型 |
|-----|------|------|------|---------|
| 08:00-09:00 | 早餐 | XX餐厅 | 1h | 餐饮 |
| 09:00-11:30 | 非遗项目名 | 具体地址 | 2.5h | 非遗体验 |
| 11:30-13:00 | 午餐 | XX餐馆 | 1.5h | 餐饮 |
| ... | ... | ... | ... | ... |

**（3）三餐推荐表格**

| 餐次 | 推荐餐厅/小吃 | 招牌菜 | 人均(元) | 地址 |
|-----|-------------|--------|---------|------|
| 早餐 | 具体店名 | 具体菜名 | ¥XX | 具体地址 |
| 午餐 | 具体店名 | 具体菜名 | ¥XX | 具体地址 |
| 晚餐 | 具体店名 | 具体菜名 | ¥XX | 具体地址 |

**（4）项目详情**（每个非遗项目一个小节，用 `#### 项目名` 标题）
每个项目必须包含：
- **体验方式**：具体怎么参与（如"在传承人指导下绘制农民画"）
- **最佳时段**：几点去体验最好
- **预计费用**：门票/体验费具体金额
- **附近寻味**：步行可达的特色小吃
- **摄影建议**：最佳拍摄位置和角度
- 用 `> ⚠️` 标注注意事项

**（5）当日贴士**（用 `> 💡` 引用块）
> 💡 今日贴士：XX项目下午2点有传承人现场演示，建议提前到达

### 板块6：住宿推荐
输出住宿推荐表格：

| 推荐类型 | 酒店名称 | 参考价格 | 位置 | 推荐理由 |
|---------|---------|---------|------|---------|
| 经济型 | 具体酒店名 | ¥XX/晚 | 具体区域 | 理由 |
| 舒适型 | 具体酒店名 | ¥XX/晚 | 具体区域 | 理由 |
| 特色民宿 | 具体民宿名 | ¥XX/晚 | 具体区域 | 理由 |

### 板块7：实用贴士
分为4个子部分：

**紧急联系信息**（表格）：
| 类型 | 电话 |
|-----|------|
| 报警 | 110 |
| 急救 | 120 |
| 旅游投诉 | 12345 |
| 陕西省文旅厅 | 029-XXXXXXX |

**当地文化禁忌**（用 `> ⚠️` 引用块）：
> ⚠️ 参观寺庙时请勿大声喧哗，拍照前请征得同意

**备选方案**（用 `> 💡` 引用块）：
> 💡 若遇雨天，可将XX户外项目替换为XX室内体验

**通用建议**（列表）：
- 具体建议1
- 具体建议2

---

## 二、格式规范

1. 使用Markdown格式输出
2. 表格必须对齐，列名严格按上述格式
3. 引用块标记含义：
   - `> 💡` = 实用贴士（绿色信息卡）
   - `> ⚠️` = 注意事项（橙色警示卡）
   - `> 🌟` = 行程亮点（红色高亮卡）
4. 每日行程标题必须用 `### 第X天（日期）：主题` 格式
5. 项目详情标题必须用 `#### 项目名` 格式

## 三、内容质量要求（必须严格遵守）

1. **禁止抽象描述**：不得出现"文化底蕴深厚"、"历史悠久"、"场景化复原"、"独具特色"、"别具一格"等空洞词汇
2. **必须具体可操作**：
   - 餐厅推荐必须写具体店名（如"老孙家泡馍"而非"当地特色餐馆"）
   - 费用必须写具体数字（如"门票¥50/人"而非"门票约几十元"）
   - 地址必须写具体位置（如"碑林区南大街XX号"而非"市中心附近"）
   - 时间必须写具体时段（如"09:00-11:30"而非"上午"）
3. **每个非遗项目**必须包含：体验方式、最佳时段、预计费用、附近寻味、摄影建议
4. **三餐推荐**必须写真实存在的当地特色餐厅/小吃，不得编造
5. **住宿推荐**必须写真实存在的酒店/民宿类型，价格合理
6. **紧急联系**必须包含真实可用的电话号码

## 四、禁止事项

- 禁止输出emoji符号（如📢🎒🚗💰📜🍽️📍💡等），用文字标记代替
- 禁止输出纯文字大段落（超过3行），必须用表格或列表组织
- 禁止在表格中使用换行符
- 禁止输出"详见上文"、"同上"等引用
- 禁止输出空表格（每个表格至少2行数据）"""


def get_pdf_content_prompt(
    destination: str,
    start_location: str,
    travel_days: int,
    travel_dates: str,
    travel_mode: str,
    group_size: int,
    budget_range: str,
    weather_summary: str,
    formatted_history: str,
    slim_itinerary_json: str,
    heritage_context_str: str,
    sys_recs: str,
    day_dates_str: str,
    route_summary: str = ""
) -> str:
    return PDF_CONTENT_PROMPT.format(
        destination=destination,
        start_location=start_location,
        travel_days=travel_days,
        travel_dates=travel_dates,
        travel_mode=travel_mode,
        group_size=group_size,
        budget_range=budget_range,
        weather_summary=weather_summary,
        formatted_history=formatted_history,
        slim_itinerary_json=slim_itinerary_json,
        heritage_context_str=heritage_context_str,
        sys_recs=sys_recs,
        day_dates_str=day_dates_str,
        route_summary=route_summary
    )
