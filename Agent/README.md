# 🤖 智能旅游规划 Agent

<p align="center">
  <img src="https://raw.githubusercontent.com/Elaine-one/shaanxi-heritage-ai-platform/main/docs/agent-banner.png" alt="智能旅游规划 Agent" width="100%"/>
</p>

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-orange.svg)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-red.svg)

</div>

---

## 📖 项目概述

基于 **非遗文化** 的智能旅游规划服务，集成大语言模型和多种 API 服务，为用户提供个性化的文化旅游体验。

---

## ✨ 核心功能

| 功能 | 说明 |
|:---|:---|
| 🎯 **智能规划** | 基于 AI 大模型的旅游路线规划 |
| 🏛️ **非遗文化** | 专注非物质文化遗产景点推荐 |
| 🌤️ **天气集成** | 实时天气信息与出行建议 |
| 📍 **地理服务** | 百度地图/高德地图 MCP 集成 |
| 📊 **进度跟踪** | 实时规划进度监控 |
| 💬 **智能对话** | AI 助手支持信息查询和规划调整 |
| 🔄 **Redis 缓存** | 会话管理和缓存优化 |
| 🗄️ **MinIO 存储** | PDF 导出和媒体资源存储 |
| 📄 **多格式导出** | PDF / CSV / JSON 格式支持 |
| 🔌 **多厂商 LLM** | OpenAI / DashScope / DeepSeek / 智谱 GLM |

---

## 🏗️ 技术架构

### 核心技术栈

| 类别 | 技术 |
|:---|:---|
| **框架** | FastAPI + Pydantic |
| **AI 模型** | OpenAI, DashScope, DeepSeek, 智谱 GLM (多厂商) |
| **代理架构** | ReAct (Reasoning + Acting) |
| **上下文工程** | Context Builder / Compressor |
| **知识系统** | 知识图谱 + RAG 检索 |
| **工具协议** | MCP (Model Context Protocol) |
| **地图服务** | 百度地图 API / 高德地图 MCP |
| **天气服务** | Open-Meteo API |
| **PDF 生成** | ReportLab / PDFKit |
| **对象存储** | MinIO |
| **缓存系统** | Redis |

### ReAct Agent 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    ReAct Agent 核心                          │
│                                                              │
│   用户输入 → 上下文构建 → 知识图谱检索 → RAG增强              │
│                     ↓                                        │
│              提示词构建 → LLM推理 → 解析响应                  │
│                                    ↓                         │
│                            ┌─────────┴─────────┐            │
│                            ↓                   ↓            │
│                      Final Answer        Action调用           │
│                            ↓                   ↓            │
│                      返回用户             工具执行             │
│                                              ↓                │
│                                        Observation           │
│                                              ↓                │
│                                      继续推理循环            │
└─────────────────────────────────────────────────────────────┘
```

### 流式输出架构

```
前端 (Fetch API + SSE)
    ↓
Django Backend (StreamingHttpResponse 代理)
    ↓
FastAPI Agent Service (StreamingResponse)
    ↓
LLM (astream 流式调用)
    ↓
实时推送文本块
```

---

## 📂 项目结构

```
Agent/
├── agent/                  # 🤖 AI代理核心模块
│   ├── agent.py           # Agent主类
│   ├── langchain_agent.py # LangChain代理实现
│   ├── plan_editor.py     # 规划编辑器
│   └── travel_planner.py  # 旅游规划核心逻辑
│
├── api/                    # 🔌 FastAPI接口层
│   ├── export/            # 导出功能
│   │   ├── csv_exporter.py
│   │   ├── json_exporter.py
│   │   └── pdf_exporter.py
│   ├── app.py             # 主应用入口
│   ├── conversation_endpoints.py  # 对话接口
│   ├── edit_endpoints.py  # 编辑接口
│   ├── weather_endpoints.py   # 天气接口
│   └── admin_endpoints.py # 管理接口
│
├── common/                 # 🛠️ 公共模块
│   ├── exceptions.py      # 异常定义
│   └── result.py          # 结果封装
│
├── config/                 # ⚙️ 配置管理
│   └── settings.py
│
├── context/                # 📝 上下文管理
│   ├── cache_manager.py   # 缓存管理
│   ├── context_builder.py # 上下文构建
│   ├── context_compressor.py  # 上下文压缩
│   └── unified_context.py # 统一上下文
│
├── core/                   # ⚡ 核心功能
│   ├── concurrency.py     # 并发管理
│   ├── progress_manager.py # 进度管理
│   ├── resource_manager.py # 资源管理
│   ├── startup.py         # 启动管理
│   └── task_queue.py      # 任务队列
│
├── memory/                 # 🧠 记忆系统
│   ├── conversation_vector_service.py  # 对话向量服务
│   ├── heritage_query_service.py  # 非遗查询服务
│   ├── knowledge_graph.py  # 知识图谱
│   ├── rag_retriever.py   # RAG检索器
│   ├── redis_session.py   # Redis会话
│   ├── session.py         # 会话管理
│   ├── sqlite_store.py    # SQLite存储
│   ├── user_profile.py   # 用户画像
│   └── vector_store.py   # 向量存储
│
├── models/                 # 🤖 AI模型集成
│   ├── llm_factory.py    # LLM工厂
│   └── llm_model.py      # LLM模型封装
│
├── prompts/                # 📋 提示词管理
│   ├── langchain_prompt.py
│   ├── react.py           # ReAct提示词
│   └── templates.py       # 模板
│
├── safety/                 # 🔒 安全模块
│   └── safety_checker.py  # 安全检查
│
├── services/               # 📦 业务服务层
│   ├── amap_mcp_client.py  # 高德MCP客户端
│   ├── content_integrator.py  # 内容整合
│   ├── conversation_service.py  # 对话服务
│   ├── geocoding.py       # 地理编码
│   ├── heritage_analyzer.py  # 非遗分析
│   ├── mcp_client.py      # MCP客户端
│   ├── mcp_protocol_client.py  # MCP协议客户端
│   ├── minio_storage.py   # MinIO存储
│   ├── pdf_content_integrator.py  # PDF内容整合
│   ├── pdf_generator_optimized.py  # PDF生成器
│   ├── pdf_pdfkit.py      # PDFKit实现
│   ├── pdf_templates.py   # PDF模板
│   ├── user_history_service.py  # 用户历史服务
│   ├── weather.py         # 天气服务
│   └── weather_config.py  # 天气配置
│
├── tools/                  # 🔧 工具模块
│   ├── base.py            # 基础工具类
│   ├── context_manager.py # 上下文管理工具
│   ├── knowledge_graph_tools.py  # 知识图谱工具
│   ├── langchain_tools.py # LangChain工具
│   ├── langchain_wrappers.py  # LangChain封装
│   ├── mcp_tool_adapter.py  # MCP工具适配器
│   ├── mcp_tools.py       # MCP工具
│   └── plan_tools.py      # 规划工具
│
└── utils/                  # 🛠️ 工具函数
    ├── content_extractor.py
    ├── font_manager.py
    └── logger_config.py
```

---

## 🚀 快速开始

### 环境要求

| 组件 | 要求 |
|:---|:---|
| Python | 3.8+ |
| Redis | 用于会话管理 |
| MinIO | 用于文件存储 |

### 安装部署

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env

# 3. 编辑 .env 配置必要参数
LLM_PROVIDER=dashscope
LLM_API_KEY=your_api_key_here
LLM_MODEL=qwen-plus
BAIDU_MAP_AK=your_baidu_map_ak_here
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
MINIO_ENDPOINT=localhost:9000
```

### 启动服务

```bash
# 方式1: 使用 uvicorn 启动
python -m uvicorn Agent.api.app:app --host 0.0.0.0 --port 8001

# 方式2: 直接运行主模块
python -m Agent.api.app

# 方式3: 运行 main.py
python Agent/main.py
```

### 访问地址

| 服务 | 地址 |
|:---|:---|
| 📚 API 文档 | http://localhost:8001/docs |
| 🔍 健康检查 | http://localhost:8001/health |

---

## 🔧 多厂商 LLM 配置

| 厂商 | LLM_PROVIDER | 默认模型 | Base URL |
|:---|:---|:---|:---|
| 通义千问 (DashScope) | `dashscope` | qwen-plus | https://dashscope.aliyuncs.com/compatible-api/v1 |
| 智谱 GLM | `zhipu` | glm-4 | https://open.bigmodel.cn/api/paas/v4 |
| DeepSeek | `deepseek` | deepseek-chat | https://api.deepseek.com/v1 |
| OpenAI | `openai` | gpt-4o | https://api.openai.com/v1 |
| Moonshot | `moonshot` | moonshot-v1-8k | https://api.moonshot.cn/v1 |
| Ollama (本地) | `ollama` | llama2 | http://localhost:11434/v1 |

### 模型参数配置

```bash
LLM_TEMPERATURE=0.7      # 温度参数 (0-1)
LLM_MAX_TOKENS=4000      # 最大输出 token 数
```

---

## 🛠️ 工具系统

### 可用工具

| 工具名称 | 功能描述 | 主要参数 |
|:---|:---|:---|
| `heritage_search` | 查询非遗项目信息 | heritage_id, keywords, region, category |
| `weather_query` | 查询城市天气预报 | city, days |
| `travel_route_planning` | 生成旅游路线规划 | heritage_ids, travel_days, departure_location |
| `knowledge_base_qa` | 回答非遗知识性问题 | question, category |
| `plan_edit` | 修改已有旅游规划 | current_plan, edit_request |
| `geocoding_query` | 查询地点坐标 | location_name |
| `context_management` | 上下文管理工具 | operation, context_data |
| `knowledge_graph_query` | 知识图谱查询 | query_type, entities |

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

---

## 📡 API 文档

### 认证机制

本系统采用 Session 进行用户认证。所有核心功能接口都需要认证才能访问。

### 核心接口

| 接口 | 方法 | 描述 |
|:---|:---:|:---|
| `/health` | GET | 健康检查（无需认证） |
| `/api/travel-plan/create` | POST | 创建旅游规划 |
| `/api/travel-plan/progress/{plan_id}` | GET | 查询规划进度 |
| `/api/travel-plan/result/{plan_id}` | GET | 获取规划结果 |
| `/api/travel-plan/list` | GET | 获取规划列表 |
| `/api/agent/chat` | POST | AI 对话交互 |
| `/api/agent/start_edit_session` | POST | 开始编辑会话 |
| `/api/agent/edit_plan` | POST | 编辑规划 |

### 创建旅游规划

```http
POST /api/travel-plan/create
```

```json
{
  "heritage_ids": [1, 2, 3],
  "user_id": "test_user_001",
  "travel_days": 3,
  "departure_location": "西安市",
  "travel_mode": "自驾",
  "budget_range": "中等",
  "group_size": 2,
  "special_requirements": ["文化体验", "美食推荐"]
}
```

### AI 对话交互

```http
POST /api/agent/chat
```

```json
{
  "plan_id": "plan_xxx",
  "user_id": "test_user_001",
  "message": "我的预算是多少？",
  "context": {
    "current_day": 1,
    "current_location": "西安市"
  }
}
```

---

## 🖥️ 前端集成

### 基本请求示例

```javascript
const response = await fetch('/api/agent/api/travel-plan/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
        heritage_ids: [1, 2, 3],
        travel_days: 3,
        departure_location: "西安市"
    })
});
```

### JavaScript SDK

```javascript
// 初始化 Agent
const agent = new TravelPlanningAgent();

// 创建规划
agent.createTravelPlan({
    heritage_ids: [1, 2, 3],
    travel_days: 3,
    departure_location: "西安市"
});

// 监听进度更新
agent.onProgressUpdate = (progressData) => {
    console.log(`进度: ${progressData.progress}%`);
};

// 监听完成事件
agent.onPlanningCompleted = (result) => {
    console.log('规划完成:', result);
};
```

---

## ❓ 故障排除

| 问题 | 解决方案 |
|:---|:---|
| API 密钥错误 | 检查 `.env` 文件中的密钥配置 |
| 模块导入错误 | 确保所有依赖已正确安装 |
| Redis 连接失败 | 确认 Redis 服务已启动 |
| MinIO 上传失败 | 确认 MinIO 服务已启动，bucket 存在 |

### 日志查看

```bash
# 查看应用日志
tail -f logs/agent.log

# 查看错误日志
tail -f logs/error.log
```

### 调试模式

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

---

## 📄 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，**禁止任何形式的使用、修改、分发或商业利用**。

---

## 📬 联系方式

- **项目维护者**: elaine
- **邮箱**: onee20589@gmail.com
- **项目链接**: [GitHub Repository](https://github.com/Elaine-one/shaanxi-heritage-ai-platform)

---

<p align="center">
  <sub>Built with ❤️ for Shaanxi Intangible Cultural Heritage</sub>
</p>
