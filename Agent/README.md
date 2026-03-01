# 智能旅游规划Agent

基于非遗文化的智能旅游规划服务，集成大语言模型和多种API服务，为用户提供个性化的文化旅游体验。

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
- 📝 **对话系统**: 完整的对话历史管理和智能摘要功能
- 🔄 **Redis缓存**: 会话管理和缓存优化，提升响应速度
- 🗄️ **MinIO存储**: PDF导出文件和媒体资源的对象存储
- 📊 **用户历史**: 完整的用户历史记录和行为分析
- 📄 **多格式导出**: 支持PDF、CSV、JSON等多种格式导出规划方案
- 🔌 **多厂商LLM**: 支持OpenAI、DashScope、DeepSeek、智谱GLM等多厂商切换

## 技术架构

### 核心技术栈

- **后端框架**: FastAPI - 高性能异步Web框架
- **AI模型**: 大语言模型 (支持多厂商切换) - OpenAI、DashScope、DeepSeek、智谱GLM等
- **代理架构**: ReAct (Reasoning + Acting) - 智能决策代理
- **地图服务**: 百度地图API - 地理位置和路线规划
- **天气服务**: Open-Meteo API - 免费天气预报服务
- **PDF生成**: ReportLab - 专业PDF文档生成
- **对象存储**: MinIO - 存储PDF导出文件和媒体资源
- **缓存系统**: Redis - 会话管理和缓存优化
- **异步处理**: Python asyncio - 高效后台任务处理
- **数据验证**: Pydantic - 数据模型验证
- **提示词管理**: 自定义提示词模板系统
- **AI框架**: LangChain 1.0 - 大语言模型应用框架

### AI代理架构

系统采用ReAct代理架构，实现智能的推理和行动能力：

1. **推理阶段 (Reasoning)**: AI分析用户需求，理解上下文
2. **行动阶段 (Acting)**: 根据推理结果执行相应操作
3. **观察阶段 (Observing)**: 观察行动结果，更新上下文
4. **迭代优化**: 循环执行上述步骤，直到获得最佳结果

### ReAct Agent 工作流程

```
用户输入 → 提示词构建 → LLM推理 → 解析响应
                                    ↓
                            ┌───────┴───────┐
                            ↓               ↓
                      Final Answer    Action调用
                            ↓               ↓
                      返回用户         工具执行
                                            ↓
                                      Observation
                                            ↓
                                      继续推理循环
```

### 数据流架构

```
用户输入 → 前端界面 → Django后端(反向代理) → FastAPI Agent服务
                                      ↓
                            ┌─────────┴─────────┐
                            ↓                   ↓
                      AI代理层              数据服务层
                            ↓                   ↓
                      大语言模型调用        天气/地图API/MinIO
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
│   ├── session_dependencies.py  # Session认证模块
│   ├── edit_endpoints.py   # 编辑相关接口
│   ├── weather_endpoints.py   # 天气相关接口
│   └── conversation_endpoints.py  # 对话相关接口
├── agent/                  # AI代理核心模块
│   ├── react_agent.py      # ReAct代理实现
│   ├── plan_editor.py      # 规划编辑器和AI交互
│   └── travel_planner.py   # 旅游规划核心逻辑
├── config/                 # 配置管理
│   └── settings.py         # 配置文件（支持多厂商LLM）
├── memory/                 # 内存管理和会话管理
│   ├── session.py          # 会话池和上下文管理
│   └── redis_session.py    # Redis会话管理
├── models/                 # AI模型集成
│   ├── langchain/          # LangChain模型封装
│   │   └── llm.py          # 大语言模型接口
│   ├── llm_model.py        # LLM模型封装（多厂商支持）
│   └── llm_factory.py      # LLM实例工厂
├── prompts/                # AI提示词管理
│   ├── react.py            # ReAct代理提示词模板
│   └── conversation_summary.py  # 对话摘要提示词模板
├── services/               # 业务服务层
│   ├── heritage_analyzer.py   # 非遗项目分析
│   ├── weather.py              # 天气服务
│   ├── weather_config.py       # 天气配置
│   ├── content_integrator.py   # 内容整合
│   ├── pdf_generator.py        # PDF生成器
│   ├── pdf_content_integrator.py  # PDF内容整合
│   ├── minio_storage.py       # MinIO存储服务
│   ├── conversation_service.py    # 对话服务
│   ├── geocoding.py           # 地理编码服务
│   └── user_history_service.py     # 用户历史记录服务
├── tools/                  # 工具模块
│   ├── base.py             # 基础工具类
│   ├── langchain_wrappers.py  # LangChain工具封装
│   └── schemas.py          # 数据模式定义
├── utils/                  # 工具模块
│   ├── logger_config.py    # 日志配置
│   ├── font_manager.py     # 字体管理
│   └── content_extractor.py  # 内容提取
├── data/                   # 数据文件
│   └── city_coords.json    # 城市坐标数据
├── font_cache/             # 字体缓存目录
├── logs/                   # 日志目录
│   ├── agent.log           # Agent日志
│   └── error.log           # 错误日志
├── .env                    # 环境变量配置
├── .env.example            # 环境变量示例
├── README.md               # 项目文档
├── requirements.txt        # Python依赖
├── main.py                 # 主入口文件
└── __init__.py             # 包初始化
```

## 快速开始

### 环境要求

- Python 3.8+
- Redis Server (用于会话管理)
- MinIO Server (用于文件存储)

### 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 为 `.env` 并填入配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要参数：

```bash
# LLM 提供商配置 (必填)
LLM_PROVIDER=dashscope
LLM_API_KEY=your_api_key_here
LLM_MODEL=qwen-plus

# 百度地图API配置 (必填)
BAIDU_MAP_AK=your_baidu_map_ak_here

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

### 启动Agent服务

```bash
# 方式1: 使用uvicorn启动
python -m uvicorn Agent.api.app:app --host 0.0.0.0 --port 8001

# 方式2: 直接运行主模块
python -m Agent.api.app

# 方式3: 运行main.py
python Agent/main.py
```

服务启动后，访问：
- Agent API文档: http://localhost:8001/docs
- Agent健康检查: http://localhost:8001/health

## 多厂商LLM配置

系统支持多种大语言模型厂商，通过环境变量灵活切换：

### 支持的厂商

| 厂商 | LLM_PROVIDER | 默认模型 | Base URL |
|------|-------------|---------|----------|
| DashScope (通义千问) | `dashscope` | qwen-plus | https://dashscope.aliyuncs.com/compatible-api/v1 |
| 智谱GLM | `zhipu` | glm-4 | https://open.bigmodel.cn/api/paas/v4 |
| DeepSeek | `deepseek` | deepseek-chat | https://api.deepseek.com/v1 |
| OpenAI | `openai` | gpt-4o | https://api.openai.com/v1 |
| Moonshot | `moonshot` | moonshot-v1-8k | https://api.moonshot.cn/v1 |
| Ollama (本地) | `ollama` | llama2 | http://localhost:11434/v1 |
| 自定义 | `custom` | - | 需配置LLM_BASE_URL |

### 配置示例

```bash
# DashScope (推荐)
LLM_PROVIDER=dashscope
LLM_API_KEY=sk-xxxxx
LLM_MODEL=qwen-plus

# 智谱GLM
LLM_PROVIDER=zhipu
LLM_API_KEY=xxxxx.xxxxx
LLM_MODEL=glm-4

# DeepSeek
LLM_PROVIDER=deepseek
LLM_API_KEY=sk-xxxxx
LLM_MODEL=deepseek-chat

# OpenAI
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxxxx
LLM_MODEL=gpt-4o

# 本地Ollama
LLM_PROVIDER=ollama
LLM_MODEL=llama2
LLM_BASE_URL=http://localhost:11434/v1
```

### 模型参数配置

```bash
LLM_TEMPERATURE=0.7      # 温度参数 (0-1)
LLM_MAX_TOKENS=4000      # 最大输出token数
```

## API文档

### 认证机制

本系统采用Session进行用户认证。所有核心功能接口都需要认证才能访问。

#### 认证流程

1. **用户登录**: 通过后端服务登录，获得session
2. **自动认证**: 前端后续请求自动携带session信息
3. **Session验证**: Agent服务端验证用户身份

#### 前端集成示例

```javascript
// 发起需要认证的请求到Agent服务
const response = await fetch('/api/agent/api/travel-plan/create', {
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

### 核心接口

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

#### 7. 开始编辑会话
```http
POST /api/agent/start_edit_session
```

请求体：
```json
{
  "plan_data": {
    "plan_id": "plan_xxx",
    "basic_info": {...},
    "heritage_items": [...],
    "itinerary": [...]
  }
}
```

#### 8. 编辑规划
```http
POST /api/agent/edit_plan
```

请求体：
```json
{
  "session_id": "edit_plan_xxx",
  "user_input": "我想增加一天的行程"
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
- **上下文记忆**: AI能够记住用户的规划信息，提供连贯的对话体验

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

fetch('/api/agent/api/agent/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(chatData)
})
.then(response => response.json())
.then(data => {
    console.log('AI回复:', data.response);
});
```

## 工具系统

### 可用工具

Agent提供以下工具供AI调用：

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|---------|
| `heritage_search` | 查询非遗项目信息 | heritage_id, keywords, region, category |
| `weather_query` | 查询城市天气预报 | city, days |
| `travel_route_planning` | 生成旅游路线规划 | heritage_ids, travel_days, departure_location |
| `knowledge_base_qa` | 回答非遗知识性问题 | question, category |
| `plan_edit` | 修改已有旅游规划 | current_plan, edit_request |
| `geocoding_query` | 查询地点坐标 | location_name |

### 工具调用示例

```python
# 非遗查询 - ID查询
heritage_search(heritage_id=17)

# 非遗查询 - 关键词搜索
heritage_search(keywords="皮影戏", region="西安")

# 天气查询
weather_query(city="西安", days=3)

# 路线规划
travel_route_planning(
    heritage_ids=[17, 20],
    travel_days=3,
    departure_location="西安",
    travel_mode="自驾"
)
```

## 前端集成

### 基本请求示例

```javascript
// 发起需要认证的请求
const response = await fetch('/api/agent/api/travel-plan/create', {
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
        pass
    
    async def generate_suggestion(self, prompt: str) -> str:
        # 实现模型调用逻辑
        pass
```

### 添加新的工具

在 `tools/base.py` 中注册新工具：

```python
@tool_registry.register("new_tool")
class NewTool(AsyncTool):
    @property
    def name(self) -> str:
        return "new_tool"
    
    @property
    def description(self) -> str:
        return "工具描述"
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        # 实现工具逻辑
        return {"result": "success"}
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

## 故障排除

### 常见问题

1. **API密钥错误**
   - 检查 `.env` 文件中的密钥配置
   - 确保密钥有效且有足够的配额

2. **模块导入错误**
   - 检查Python路径设置
   - 确保所有依赖已正确安装：`pip install -r requirements.txt`

3. **进度查询404错误**
   - 确保规划ID正确
   - 检查后台任务是否正常启动

4. **Redis连接失败**
   - 确认Redis服务已启动
   - 检查REDIS_HOST和REDIS_PORT配置

5. **MinIO上传失败**
   - 确认MinIO服务已启动
   - 检查bucket是否存在，如不存在需创建

### 日志查看

```bash
# 查看应用日志
tail -f logs/agent.log

# 查看错误日志
tail -f logs/error.log
```

### 调试模式

设置环境变量启用调试：

```bash
DEBUG=true
LOG_LEVEL=DEBUG
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

### v1.3.5（2026-03-01）

- 支持多厂商LLM切换（OpenAI、DashScope、DeepSeek、智谱GLM、Moonshot、Ollama）
- 新增LLM工厂模式，简化模型实例化流程
- 重构LLM模型层，统一使用LangChain ChatOpenAI接口
- 优化上下文传递格式，改进会话管理
- 优化日志系统，添加单例模式防止重复初始化
- 适配langchain1.0.0，修复与旧版本不兼容问题

### v1.3.2（2026-02-08）

#### 🔧 系统架构优化
- ✅ 优化后端文件结构，采用 `api/`, `serializers/`, `services/` 分层架构
- ✅ 移除 Agent URL 加密功能，简化服务间通信
- ✅ 完善 Agent 服务反向代理，前端通过 Django 统一访问 Agent API
- ✅ 移除前端 MinIO 依赖，所有文件存储通过后端/Agent服务处理

### v1.3.1（2026-01-11）

#### 🧠 对话历史智能优化

- ✅ 新增 `conversation_summary.py` 提示词模板，定义专业角色以保证提取准确性
- ✅ 在提示词中定义"对话历史分析专家"角色，确保摘要质量和信息密度
- ✅ 智能提取用户需求、已确定信息、关键决策点等核心内容
- ✅ 控制摘要长度在 200-500 字之间，确保信息密度高

#### 📄 PDF 生成升级
- ✅ 升级 PDF 生成流程，使用 LLM 智能摘要替代简单截取
- ✅ 确保 PDF 生成和聊天界面使用一致的对话历史处理方式

#### 🔧 技术优化与修复
- ✅ 修复 Pydantic v2 与 LangChain 工具的兼容性问题
- ✅ 修改 `schemas.py` 导入语句，使用 `pydantic.v1` 的 BaseModel
- ✅ 添加异常处理和降级机制，提升系统健壮性


### v1.3.0（2026-01-09）

#### 🔐 认证系统升级
- ✅ 引入基于 Django Session 的用户认证机制，替代原有的 JWT 方案  
- ✅ 新增 `session_dependencies.py` 模块，提供 FastAPI 兼容的 Session 验证依赖  
- ✅ 为所有核心接口添加 Session 认证保护，确保仅授权用户可访问  
- ✅ 配置 `settings.py` 中的 Session 参数（密钥、存储、过期策略等）  
- ✅ 支持前后端共享 Session 存储（如 Redis 或数据库）实现身份验证  
- ✅ 更新 `README.md`，补充认证集成说明与前端对接示例  

#### 🧠 Agent 架构重构
- ✅ 大规模重构 Agent 模块，优化整体代码结构与职责划分  

### v1.3.3（2026-02-28）

#### 🐛 Bug修复
- ✅ 修复了前端流式输出在后台停止的问题
- ✅ 修复了AI响应时输入框被禁用的问题
- ✅ 修复了AI响应内容被截断的问题
- ✅ 清理了代码中的版本标识注释（如"(交互体验优化版)"等）
- ✅ 修复了硬编码城市坐标的问题，改用地理编码服务
- ✅ 清理了特殊注释标签（如"【...】"、"[...]"、"//性能优化：..."等）

#### 🚀 功能增强
- 🆕 实现了基于requestAnimationFrame的流式输出优化
- ✨ 添加了页面可见性检测，后台时暂停流式输出
- 🆕 优化了ReAct Agent提示词模板，防止响应截断
- 🆕 重构了天气服务，移除模拟数据，创建天气评估专家工具
- 🆕 设计了基于SSE和AsyncGenerator的后端流式实现方案
- 🆕 使用zhdate库替换了错误的农历计算逻辑
- 🆕 支持指定日期的农历和节气计算
- 🆕 添加了zhdate依赖到requirements.txt

#### 📈 技术改进
- 📈 优化了前端流式输出的性能和用户体验
- 📈 改进了天气服务的准确性和可靠性
- 📈 增强了代码的可维护性和可读性
- 📈 完善了农历计算的准确性（支持1900-2100年）
- 📈 优化了代码注释，移除了不必要的标签和版本标识
- 📈 改进了地理编码服务的集成，避免硬编码坐标

#### 🧹 代码清理
- 🧹 系统性清理了多个文件中的版本标识注释
- 🧹 移除了硬编码的城市坐标数据
- 🧹 清理了特殊格式的注释标签
- 🧹 统一了代码风格和注释规范  
