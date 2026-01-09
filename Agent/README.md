# 智能旅游规划Agent

基于非遗文化的智能旅游规划服务，集成阿里云大模型和多种API服务，为用户提供个性化的文化旅游体验。

## 项目概述

本项目是一个智能旅游规划系统，专注于非物质文化遗产的文化旅游体验。系统通过AI技术分析用户需求，结合天气、地理位置等信息，生成个性化的旅游规划方案。

### 核心功能

- 🎯 **智能规划**: 基于AI大模型的旅游路线规划
- 🏛️ **非遗文化**: 专注非物质文化遗产景点推荐
- 🌤️ **天气集成**: 实时天气信息与出行建议，准确的日期计算
- 📍 **地理服务**: 百度地图API集成，精准位置服务
- 📊 **进度跟踪**: 实时规划进度监控
- 📱 **前端界面**: 现代化Web界面，支持进度条和结果展示
- 💬 **智能对话**: AI助手支持用户信息查询和规划调整
- 📄 **多格式导出**: 支持PDF、CSV、JSON等多种格式导出规划方案

## 技术架构

### 核心技术栈

- **后端框架**: FastAPI - 高性能异步Web框架
- **AI模型**: 阿里云通义千问 (DashScope API) - 大语言模型
- **代理架构**: ReAct (Reasoning + Acting) - 智能决策代理
- **地图服务**: 百度地图API - 地理位置和路线规划
- **天气服务**: 实时天气API - 天气预报和出行建议
- **前端**: 原生JavaScript + HTML5 - 响应式Web界面
- **PDF生成**: ReportLab - 专业PDF文档生成
- **异步处理**: Python asyncio - 高效后台任务处理

### AI代理架构

系统采用ReAct代理架构，实现智能的推理和行动能力：

1. **推理阶段 (Reasoning)**: AI分析用户需求，理解上下文
2. **行动阶段 (Acting)**: 根据推理结果执行相应操作
3. **观察阶段 (Observing)**: 观察行动结果，更新上下文
4. **迭代优化**: 循环执行上述步骤，直到获得最佳结果

### 数据流架构

```
用户输入 → 前端界面 → API接口 → 业务逻辑层
                                      ↓
                            ┌─────────┴─────────┐
                            ↓                   ↓
                      AI代理层              数据服务层
                            ↓                   ↓
                      大语言模型调用        天气/地图API
                            ↓                   ↓
                            └─────────┬─────────┘
                                      ↓
                              规划生成与优化
                                      ↓
                              结果返回与展示
```

### 后端架构

```
Agent/
├── api/                    # FastAPI接口层
│   ├── export/             # 导出功能模块
│   │   ├── csv_exporter.py    # CSV导出
│   │   ├── json_exporter.py   # JSON导出
│   │   └── pdf_exporter.py    # PDF导出
│   ├── app.py              # 主应用入口
│   ├── session_dependencies.py  # Django Session认证模块
│   ├── edit_endpoints.py   # 编辑相关接口
│   └── weather_endpoints.py   # 天气相关接口
├── agent/                  # AI代理核心模块
│   ├── react_agent.py      # ReAct代理实现
│   ├── plan_editor.py      # 规划编辑器和AI交互
│   └── travel_planner.py   # 旅游规划核心逻辑
├── config/                 # 配置管理
│   └── settings.py         # 配置文件
├── memory/                 # 内存管理和会话管理
│   └── session.py          # 会话池和上下文管理
├── models/                 # AI模型集成
│   ├── langchain/          # LangChain模型封装
│   │   └── llm.py          # 大语言模型接口
│   └── dashscope.py        # DashScope模型
├── prompts/                # AI提示词管理
│   └── react.py            # ReAct代理提示词模板
├── services/               # 业务服务层
│   ├── heritage_analyzer.py   # 非遗项目分析
│   ├── weather.py              # 天气服务
│   ├── weather_config.py       # 天气配置
│   ├── content_integrator.py   # 内容整合
│   ├── pdf_generator.py        # PDF生成器
│   └── pdf_content_integrator.py  # PDF内容整合
├── tools/                  # 工具模块
│   ├── base.py             # 基础工具类
│   ├── langchain_wrappers.py  # LangChain工具封装
│   └── schemas.py          # 数据模式定义
├── utils/                  # 工具模块
│   ├── logger_config.py    # 日志配置
│   ├── font_manager.py     # 字体管理
│   └── content_extractor.py  # 内容提取
├── font_cache/             # 字体缓存目录
├── logs/                   # 日志目录
│   ├── agent.log           # Agent日志
│   └── error.log           # 错误日志
├── .env                    # 环境变量配置
├── README.md               # 项目文档
└── main.py                 # 主入口文件
```

## 快速开始

### 环境要求

- Python 3.8+
- Node.js (可选，用于前端开发)

### 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt
```

### 配置API密钥

编辑 `Agent/.env` 文件，填入你的API密钥：
```bash
# 阿里云API配置
DASHSCOPE_API_KEY=your_dashscope_api_key

# 百度地图API配置
BAIDU_MAP_AK=your_baidu_map_ak

# 天气API配置（可选）
WEATHER_API_KEY=your_weather_api_key
```

### 启动服务

本系统包含两个服务：

1. **Django后端服务** (端口8000) - 用户认证和前端界面
2. **FastAPI Agent服务** (端口8001) - AI规划和编辑功能

#### 启动Django后端服务

```bash
# 进入backend目录
cd backend

# 启动Django开发服务器
python manage.py runserver 0.0.0.0:8000
```

#### 启动FastAPI Agent服务

```bash
# 在项目根目录启动Agent服务
python -m uvicorn Agent.api.app:app --host 0.0.0.0 --port 8001 --reload

# 或者直接运行
python Agent/main.py
```

服务启动后，访问：
- Django后端: http://localhost:8000
- Agent API文档: http://localhost:8001/docs
- Agent健康检查: http://localhost:8001/health
- 前端界面: http://localhost:8000

## API文档

 ### 认证机制

本系统采用Django Session进行用户认证。所有核心功能接口都需要认证才能访问。认证通过Django后端的session机制实现，前端通过cookie自动携带session信息。

#### 认证流程

1. **用户登录**: 调用Django后端登录接口（http://localhost:8000），后端创建session并设置cookie
2. **自动认证**: 前端后续请求自动携带session cookie
3. **Session验证**: FastAPI服务端通过Django API验证用户身份，支持跨端口session共享

#### 前端集成示例

前端需要在请求中包含credentials以发送cookie：

```javascript
// 发起需要认证的请求到Agent服务
const response = await fetch('http://localhost:8001/api/travel-plan/create', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    credentials: 'include',  // 重要：包含cookie以支持session认证
    body: JSON.stringify({
        heritage_ids: [1, 2, 3],
        travel_days: 3,
        departure_location: '西安市'
    })
});
```

#### 跨端口Session认证说明

由于Django后端（端口8000）和Agent服务（端口8001）运行在不同端口，系统采用以下方式实现跨端口session认证：

1. **前端登录**: 用户在Django后端登录，获得session cookie
2. **Cookie自动携带**: 浏览器在同源请求中自动携带session cookie
3. **API验证**: Agent服务通过调用Django API验证session有效性
4. **用户信息获取**: 验证成功后从Django API获取用户信息

这种设计确保了：
- 用户只需在Django后端登录一次
- Agent服务可以安全地验证用户身份
- 前端无需手动管理token
- 支持跨端口部署

### 核心接口

以下接口都需要有效的Django session：

#### 1. 健康检查（无需认证）
```http
GET /health
```

响应示例：
```json
{
  "status": "healthy",
  "timestamp": "2025-08-31T21:42:01.676494",
  "components": {
    "agent": "ok",
    "planner": "ok",
    "api": "ok"
  }
}
```

#### 2. 创建旅游规划（需要认证）
```http
POST /api/travel-plan/create
```

请求体：
```json
{
  "heritage_ids": [1, 2, 3],
  "user_id": "test_user_001",
  "travel_days": 3,
  "departure_location": "西安市",
  "travel_mode": "自驾",
  "budget_range": "中等",
  "group_size": 2,
  "special_requirements": ["文化体验", "美食推荐"],
  "contact_info": {
    "phone": "13800138000",
    "email": "test@example.com"
  }
}
```

响应示例：
```json
{
  "success": true,
  "plan_id": "plan_4623b1a0_20250831_214244",
  "message": "旅游规划任务已启动，请使用plan_id查询进度",
  "data": {
    "plan_id": "plan_4623b1a0_20250831_214244",
    "estimated_time": "2-5分钟",
    "heritage_count": 3,
    "travel_days": 3
  }
}
```

#### 3. 查询规划进度（需要认证）
```http
GET /api/travel-plan/progress/{plan_id}
```

响应示例：
```json
{
  "plan_id": "plan_4623b1a0_20250831_214244",
  "status": "processing",
  "progress": 60,
  "current_step": "生成AI建议",
  "steps": [
    "分析非遗项目",
    "获取天气信息",
    "生成AI建议",
    "优化路线规划",
    "生成完整方案",
    "完成规划"
  ],
  "start_time": "2025-08-31T21:42:44.123456"
}
```

#### 4. 获取规划结果（需要认证）
```http
GET /api/travel-plan/result/{plan_id}
```

响应示例：
```json
{
  "success": true,
  "plan_id": "plan_4623b1a0_20250831_214244",
  "message": "规划获取成功",
  "data": {
    "title": "西安非遗文化3日游",
    "total_days": 3,
    "itinerary": [
      {
        "day": 1,
        "items": [
          {
            "name": "兵马俑",
            "type": "景点",
            "time": "09:00-12:00",
            "description": "世界文化遗产，秦始皇陵兵马俑"
          }
        ]
      }
    ]
  }
}
```

#### 5. 获取规划列表
```http
GET /api/travel-plan/list
```

#### 6. AI对话交互（需要认证）
```http
POST /api/agent/chat
```

请求体：
```json
{
  "plan_id": "plan_4623b1a0_20250831_214244",
  "user_id": "test_user_001",
  "message": "我的预算是多少？",
  "context": {
    "current_day": 1,
    "current_location": "西安市"
  }
}
```

响应示例：
```json
{
  "success": true,
  "response": "根据您的规划，您的预算范围是中等，适合3天的非遗文化深度游。建议您在住宿和餐饮方面合理安排，确保有足够的资金体验当地特色文化。",
  "plan_id": "plan_4623b1a0_20250831_214244",
  "timestamp": "2025-01-09T10:30:00"
}
```

## AI对话功能

### 功能特性

AI对话功能基于ReAct（Reasoning + Acting）代理架构，为用户提供智能的旅游规划咨询服务：

- **用户信息查询**: AI可以回答关于用户出发地、交通方式、人数、预算等信息
- **规划内容解释**: 详细解释规划中的景点、路线、时间安排等
- **天气信息查询**: 提供准确的天气预报和出行建议
- **个性化建议**: 根据用户偏好提供定制化的旅游建议
- **规划调整**: 支持用户对规划进行修改和优化

### 对话上下文

AI代理维护完整的对话上下文，包括：
- 用户基本信息（出发地、交通方式、人数、预算等）
- 规划内容（景点、路线、时间安排）
- 天气信息（实时天气、未来预报）
- 对话历史（用户提问和AI回答）

### 使用示例

```javascript
// 前端调用AI对话
const chatData = {
    plan_id: currentPlanId,
    user_id: currentUserId,
    message: "我的出发地是哪里？"
};

fetch('/api/agent/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(chatData)
})
.then(response => response.json())
.then(data => {
    console.log('AI回复:', data.response);
});
```

## 前端集成

### 前端集成

前端通过Django后端的session机制进行认证，无需手动管理token。只需确保在请求中包含credentials即可。

#### 基本请求示例

```javascript
// 发起需要认证的请求
const response = await fetch('http://localhost:8000/api/travel-plan/create', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    credentials: 'include',  // 重要：包含cookie以支持session认证
    body: JSON.stringify({
        heritage_ids: [1, 2, 3],
        travel_days: 3,
        departure_location: "西安市"
    })
});

const data = await response.json();
console.log(data);
```

#### 检查认证状态

```javascript
// 检查用户是否已登录
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/user/', {
            method: 'GET',
            credentials: 'include'
        });
        
        if (response.ok) {
            const userData = await response.json();
            console.log('用户已登录:', userData);
            return true;
        } else {
            console.log('用户未登录');
            return false;
        }
    } catch (error) {
        console.error('检查认证状态失败:', error);
        return false;
    }
}

// 使用示例
checkAuthStatus().then(isLoggedIn => {
    if (isLoggedIn) {
        console.log('可以访问受保护接口');
    } else {
        console.log('需要登录');
        window.location.href = '/login.html';
    }
});
```

### JavaScript SDK

项目提供了完整的前端JavaScript SDK，位于 `frontend/js/agent/travel-planning.js`。

#### 基本使用

```javascript
// 初始化Agent
const agent = new TravelPlanningAgent();

// 创建规划
const planData = {
    heritage_ids: [1, 2, 3],
    travel_days: 3,
    departure_location: "西安市",
    // ... 其他参数
};

agent.createTravelPlan(planData);
```

#### 进度监控

SDK自动处理进度监控，并提供回调函数：

```javascript
// 监听进度更新
agent.onProgressUpdate = (progressData) => {
    console.log(`进度: ${progressData.progress}%`);
    console.log(`当前步骤: ${progressData.current_step}`);
};

// 监听完成事件
agent.onPlanningCompleted = (result) => {
    console.log('规划完成:', result);
};
```

## 开发指南

### 添加新的非遗项目

编辑 `data/heritage_data.json` 文件：

```json
{
  "heritage_items": [
    {
      "id": 4,
      "name": "新的非遗项目",
      "category": "传统技艺",
      "location": "城市名",
      "description": "项目描述",
      "coordinates": {
        "latitude": 34.2619,
        "longitude": 108.9419
      }
    }
  ]
}
```

### 扩展AI模型

在 `models/` 目录下添加新的模型文件：

```python
# models/new_model.py
class NewModel:
    def __init__(self):
        # 初始化模型
        pass
    
    async def generate_suggestion(self, prompt: str) -> str:
        # 实现模型调用逻辑
        pass
```

### 添加新的API接口

在 `api/app.py` 中添加新的路由：

```python
@app.get("/api/new-endpoint")
async def new_endpoint():
    """
    新的API接口
    """
    return {"message": "Hello from new endpoint"}
```

## 关键修复与优化

### 用户信息传递问题

**问题描述**: AI代理无法获取用户的完整信息（出发地、交通方式、人数、预算等），导致无法回答用户关于自身信息的问题。

**根本原因**: 
- 用户信息在 `travel_planner.py` 中存储在 `plan['basic_info']` 字段
- 但 `plan_editor.py` 的 `_build_plan_summary` 方法尝试直接从 `plan` 对象获取
- 导致信息提取失败，AI上下文中缺少用户信息

**解决方案**:
1. 修改 `plan_editor.py` 的 `_build_plan_summary` 方法
2. 优先从 `plan['basic_info']` 获取用户信息
3. 保持向后兼容性，支持旧的数据结构

**关键代码**:
```python
# 从basic_info中获取用户信息
basic_info = plan.get('basic_info', {})

departure_location = basic_info.get('departure', plan.get('departure_location', '未指定'))
travel_mode = basic_info.get('travel_mode', plan.get('travel_mode', '未指定'))
group_size = basic_info.get('group_size', plan.get('group_size'))
budget_range = basic_info.get('budget_range', plan.get('budget_range', '未指定'))
```

### 天气日期计算问题

**问题描述**: AI在回答天气问题时使用错误的日期，导致天气信息不准确。

**根本原因**: 
- AI提示词中缺少当前日期信息
- AI无法确定应该查询哪一天的天气

**解决方案**:
1. 在 `prompts/react.py` 的 `REACT_AGENT_PROMPT` 中添加 `{current_date}` 变量
2. 在 `react_agent.py` 中动态注入当前日期
3. 在提示词中明确要求使用当前日期作为基准

**关键代码**:
```python
# 在提示词中添加日期变量
REACT_AGENT_PROMPT = PromptTemplate(
    template="""...在回答天气问题时，必须使用当前日期{current_date}作为基准...""",
    input_variables=["current_date", "tools", "tool_names", "format_instructions"]
)

# 动态注入当前日期
prompt = REACT_AGENT_PROMPT.partial(
    current_date=datetime.now().strftime("%Y-%m-%d"),
    tools=tools,
    tool_names=tool_names,
    format_instructions=format_instructions
)
```

### PDF导出功能问题

**问题描述**: PDF导出功能无法正常工作，出现模块导入错误。

**根本原因**: `plan_editor.py` 中的 `get_plan_editor` 函数未在 `__init__.py` 中导出。

**解决方案**: 在 `Agent/agent/__init__.py` 中添加 `get_plan_editor` 的导出。

**关键代码**:
```python
from .plan_editor import (
    PlanEditor,
    PlanSummary,
    get_plan_editor  # 添加此行
)
```

## 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `utils/config.py` 中的密钥配置
   - 确保密钥有效且有足够的配额

2. **模块导入错误**
   - 检查Python路径设置
   - 确保所有依赖已正确安装

3. **进度查询404错误**
   - 确保规划ID正确
   - 检查后台任务是否正常启动

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error.log
```

## 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，**禁止任何形式的使用、修改、分发或商业利用**。

* 本项目代码仅供学习和参考，不得用于任何实际项目
* 未经授权，禁止复制或引用本项目的任何代码
* 所有权利保留，侵权必究

## 联系方式

- 项目维护者: elaine
- 邮箱: onee20589@gmail.com
- 项目链接: https://github.com/Elaine-one/shaanxi-heritage-ai-platform

## 更新日志

### v1.4.0（2026-01-09）

#### 🔐 认证系统升级
- ✅ 引入基于 Django Session 的用户认证机制，替代原有的 JWT 方案  
- ✅ 新增 `session_dependencies.py` 模块，提供 FastAPI 兼容的 Session 验证依赖  
- ✅ 为所有核心接口添加 Session 认证保护，确保仅授权用户可访问  
- ✅ 配置 `settings.py` 中的 Session 参数（密钥、存储、过期策略等）  
- ✅ 支持前后端共享 Session 存储（如 Redis 或数据库）实现身份验证  
- ✅ 更新 `README.md`，补充认证集成说明与前端对接示例  

#### 🧠 Agent 架构重构
- ✅ 大规模重构 Agent 模块，优化整体代码结构与职责划分  
- ✅ 新增 `plan_editor.py`：独立规划编辑器，负责 AI 交互与行程动态编辑  
- ✅ 新增 `react_agent.py`：实现 ReAct（Reasoning + Acting）智能代理，支持推理与决策  
- ✅ 重构 `travel_planner.py`：解耦核心旅游规划逻辑，提升可读性与可维护性  
- ✅ 统一将 Agent 相关模块迁移至 `agent/` 目录，改善项目组织结构  

#### 📤 功能增强 
- ✅ 完善 API 接口：扩展编辑操作与天气查询相关接口，提升前后端协作效率  

### v1.2.0 (2025-10-21)

- ✅ **会话管理架构重构**: 将 SessionPool 从 agent/ 移动到 memory/ 目录，统一会话管理
- ✅ **移除冗余会话存储**: 删除 PlanEditor 中的 active_sessions，统一使用 SessionPool
- ✅ **优化会话上下文提取**: 改进 _extract_core_info 方法，支持从 plan['basic_info'] 获取用户信息
- ✅ **修复配置加载路径**: 修复环境变量加载路径问题，确保正确从 Agent/.env 加载配置
- ✅ **完善会话管理API**: 更新所有会话相关方法的调用，确保使用统一的 SessionPool 接口
- ✅ **增强代码可维护性**: 统一会话管理入口点，减少代码重复和潜在的一致性问题

### v1.1.1 (2025-06-15)

- ✅ **修复用户信息传递问题**: AI现在能够正确获取用户的出发地、交通方式、人数、预算等完整信息
- ✅ **修复天气日期计算**: 优化天气服务中的日期计算逻辑，确保天气查询使用正确的日期
- ✅ **增强AI上下文管理**: 改进session.py中的信息提取机制，支持从plan['basic_info']获取用户信息
- ✅ **完善PDF导出功能**: 修复PDF导出模块的导入问题，确保导出功能正常工作
- ✅ **优化ReAct代理提示词**: 在AI提示词中添加当前日期变量，提高天气查询的准确性
- ✅ **改进规划编辑器**: 增强plan_editor.py的_build_plan_summary方法，更好地整合用户信息到AI上下文中

### v1.0.0 (2025-04-10)

- ✅ 完成基础架构搭建
- ✅ 集成阿里云大模型
- ✅ 实现非遗项目分析
- ✅ 添加天气服务集成
- ✅ 完成API接口开发
- ✅ 实现前端进度条和结果展示
- ✅ 添加完整的测试覆盖

---

**感谢使用智能旅游规划Agent！** 🎉