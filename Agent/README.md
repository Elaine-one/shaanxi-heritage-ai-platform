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
| 🧠 **知识图谱** | Neo4j 图数据库，331 节点/704 关系，覆盖人-时-地-艺四维度 |
| 📜 **传承人谱系** | 168 位传承人节点 + 师承关系链 |
| ⏳ **朝代时间轴** | 20 个朝代节点，32 项非遗 100% 匹配 |
| 🗺️ **地理层级** | 省→市→区县三级 Region 树，40 个区域节点 |
| 🌤️ **天气集成** | 实时天气信息与出行建议 |
| 📍 **地理服务** | 高德地图 MCP 集成 |
| 📊 **进度跟踪** | 实时规划进度监控 |
| 💬 **智能对话** | AI 助手支持信息查询和规划调整 |
| 🔄 **Redis 缓存** | 会话管理和缓存优化 |
| 🗄️ **MinIO 存储** | PDF 导出和媒体资源存储 |
| 📄 **多格式导出** | PDF / JSON 格式支持 |
| 🔌 **多厂商 LLM** | OpenAI / DashScope / DeepSeek / 智谱 GLM |

---

## 🏗️ 技术架构

### 核心技术栈

| 类别 | 技术 |
|:---|:---|
| **框架** | FastAPI + Pydantic |
| **AI 模型** | OpenAI, DashScope, DeepSeek, 智谱 GLM (多厂商) |
| **代理架构** | LangGraph ReAct (Reasoning + Acting) |
| **上下文工程** | Context Builder + Working Memory Assembler |
| **知识系统** | Neo4j 知识图谱 + ChromaDB 向量存储 + RAG 检索 |
| **图谱架构** | Mixin 模式（Base/Heritage/Inheritor/Dynasty/Query/Admin）|
| **记忆体系** | 四层记忆：L1 会话 → L2 图存储 → L3 账本 → RAG 向量 |
| **工具协议** | MCP (Model Context Protocol) |
| **地图服务** | 高德地图 MCP |
| **天气服务** | Open-Meteo API |
| **PDF 生成** | ReportLab / PDFKit |
| **对象存储** | MinIO |
| **缓存系统** | Redis |

### LangGraph ReAct Agent 工作流程

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
Nginx (直连 Agent，无 Django 中转)
    ↓
FastAPI Agent Service (StreamingResponse)
    ↓
LLM (astream 流式调用)
    ↓
实时推送文本块
```

### 知识图谱架构

```
┌──────────────────────────────────────────────────────────────────┐
│                     Neo4j 知识图谱 (331 节点 / 704 关系)            │
│                                                                   │
│  ┌──────────┐  ORIGINATED_IN  ┌──────────┐  HAS_INHERITOR  ┌───────────┐
│  │ Dynasty  │ ◄────────────── │ Heritage │ ───────────────→ │ Inheritor │
│  │  (20)    │                 │   (32)   │                  │   (168)   │
│  └──────────┘                 └────┬─────┘                  └─────┬─────┘
│                                    │                              │
│       ┌───────────────────┬────────┼────────┬─────────────┐      │
│       ▼                   ▼        ▼        ▼             ▼      │
│  ┌─────────┐    ┌──────────┐  ┌────────┐  ┌─────────┐  STUDIED_UNDER
│  │ Category │    │  Region  │  │ Level  │  │  Batch  │    (24)
│  │  (17)   │    │   (40)   │  │  (4)   │  │  (17)   │
│  └─────────┘    └────┬─────┘  └────────┘  └─────────┘
│                      │
│                 PART_OF (37)
│              省 → 市 → 区县 三级树
│
│  关系类型: BELONGS_TO | LOCATED_AT | HAS_LEVEL | IN_BATCH |
│            ORIGINATED_IN | HAS_INHERITOR | STUDIED_UNDER |
│            PART_OF | NEAR | AT_LOCATION
│
│  查询工具: heritage_search | heritage_timeline_query |
│            nearby_heritage_query | related_heritage_query |
│            nearby_region_query | heritage_route_hint |
│            user_heritage_recommend
└──────────────────────────────────────────────────────────────────┘
```

### 记忆系统分层架构

```
┌────────────────────────────────────────────────────┐
│                Memory Coordinator                   │
│          统一调度 + Token 预算控制                    │
│          L1 写入使用 Redis Lua 脚本原子化             │
├────────────────────────────────────────────────────┤
│                                                    │
│  L1 工作记忆 (Redis)                                │
│  ├── 滚动窗口 (默认 20 轮，可配置)                   │
│  ├── 增量摘要 (LLM 驱动，分段保留最近 5 段)          │
│  ├── plan_snapshot (规划数据快照)                    │
│  └── 写入: Lua 原子 RPUSH + LLEN + LTRIM            │
│                                                    │
│  L2 图存储 (Neo4j)                                  │
│  ├── 非遗知识: Heritage/Category/Region/Dynasty     │
│  ├── 用户偏好: User→Preference→Heritage/Category    │
│  ├── 用户兴趣: User→Region (非KG地区标记pending)    │
│  └── 定时维护: 衰减 + 双阈值过期 + 全局孤儿回收     │
│                                                    │
│  L3 审计账本 (SQLite)                               │
│  ├── 对话事件记录 (WAL 模式 + 持久连接)              │
│  └── 写入: 线程锁保护                                │
│                                                    │
│  RAG 检索增强 (ChromaDB, 5 个集合)                  │
│  ├── conversations     — 对话轮次向量               │
│  ├── heritage_knowledge — 非遗知识向量              │
│  ├── attractions       — 景点信息向量               │
│  ├── session_archives  — 会话归档向量               │
│  ├── user_preferences  — 偏好向量 (独立集合)         │
│  └── 双轨检索: ChromaDB 语义 + Neo4j 图遍历         │
│                                                    │
│  辅助模块:                                          │
│  ├── Sifter: LLM + 关键词双重偏好提取               │
│  ├── PreferenceVectorizer: 结构化偏好→向量          │
│  ├── ImportanceScorer: 三维记忆重要性评分            │
│  ├── TaskBuffer: ReAct 任务缓冲 (环形队列)           │
│  └── WorkingMemoryAssembler: 预算感知上下文组装     │
└────────────────────────────────────────────────────┘
```

---

## 📂 项目结构

```
Agent/
├── agent/                  # 🤖 AI代理核心模块
│   ├── agent.py           # Agent主类
│   ├── langchain_agent.py # LangGraph ReAct代理实现
│   ├── plan_editor.py     # 规划编辑器
│   └── travel_planner.py  # 旅游规划核心逻辑
│
├── api/                    # 🔌 FastAPI接口层
│   ├── app.py             # 应用骨架（lifespan + CORS + 异常处理器）
│   ├── travel_endpoints.py  # 旅游规划路由（6 条）
│   ├── edit_endpoints.py    # AI 编辑与对话路由（9 条）
│   ├── cache.py             # 共享进度缓存
│   ├── error_models.py      # 统一错误响应模型
│   └── session_dependencies.py  # Session 认证依赖
│
├── common/                 # 🛠️ 公共模块（预留）
│
├── config/                 # ⚙️ 配置管理
│   ├── settings.py        # 全局设置
│   └── memory_budget.py   # 记忆预算配置
│
├── context/                # 📝 上下文管理
│   ├── cache_manager.py   # 分层缓存管理 (L1 内存 + L2 Redis)
│   ├── context_builder.py # 上下文构建器
│   ├── unified_context.py # 统一上下文模型
│   └── working_memory_assembler.py  # 工作记忆组装
│
├── core/                   # ⚡ 核心功能
│   ├── resource_manager.py # 资源管理
│   └── startup.py         # 启动管理 + 数据同步
│
├── memory/                 # 🧠 记忆系统
│   ├── coordinator.py     # 记忆协调器（四层记忆统一调度）
│   ├── sifter.py          # 记忆筛选器（智能过滤 + 优先级排序）
│   ├── l2_graph_store.py  # L2 图存储（用户偏好图谱）
│   ├── l3_sqlite_ledger.py  # L3 账本存储（长期事实 + 审计）
│   ├── vector_store.py    # ChromaDB 向量存储
│   ├── rag_retriever.py   # RAG 混合检索（向量 + BM25）
│   ├── heritage_query_service.py  # 非遗查询服务
│   ├── importance_scorer.py   # 重要性评分
│   ├── task_buffer.py     # 任务队列缓冲
│   ├── preference_vectorizer.py  # 偏好向量化
│   ├── knowledge_graph/   # 🔗 知识图谱（Mixin 架构）
│   │   ├── __init__.py    # KnowledgeGraph 主类
│   │   ├── _base.py       # 基础 Mixin（连接/NERGE/SET）
│   │   ├── heritage.py    # HeritageMixin（非遗/区域/层级/Location）
│   │   ├── inheritor.py   # InheritorMixin（传承人/师承关系）
│   │   ├── dynasty.py     # DynastyMixin（朝代匹配/ORIGINATED_IN）
│   │   ├── queries.py     # QueryMixin（时间轴/层级/关联查询）
│   │   └── admin.py       # AdminMixin（统计/索引/清理）
│   └── session/           # 💬 会话模块
│       ├── __init__.py    # 统一导出
│       ├── pool.py        # SessionPool 会话池
│       ├── redis_pool.py  # Redis 分布式会话池
│       ├── context.py     # 会话上下文
│       ├── lifecycle.py   # 会话生命周期
│       ├── archiver.py    # 会话归档
│       └── index.py       # 会话索引
│
├── models/                 # 🤖 AI模型集成
│   ├── llm_factory.py    # LLM工厂（多厂商切换）
│   └── llm_model.py      # LLM模型封装
│
├── prompts/                # 📋 提示词管理
│   ├── react.py           # ReAct提示词
│   └── templates.py       # 通用模板
│
├── safety/                 # 🔒 安全模块
│   └── safety_checker.py  # 安全检查
│
├── services/               # 📦 业务服务层
│   ├── amap_mcp_service.py  # 高德MCP服务
│   ├── content_integrator.py  # 内容整合
│   ├── conversation_service.py  # 对话服务
│   ├── user_history_service.py  # 用户历史服务
│   ├── pdf_content_integrator.py  # PDF生成
│   ├── minio_storage.py   # MinIO存储
│   └── weather.py         # 天气服务
│
├── tools/                  # 🔧 工具模块（10 个注册工具 + 15 MCP 工具）
│   ├── base.py            # 基础工具类 + ToolRegistry
│   ├── knowledge_graph_tools.py  # 图谱工具（6个）
│   │   # NearbyHeritage / RelatedHeritage / NearbyRegion /
│   │   # RouteHint / UserRecommend / HeritageTimeline
│   ├── langchain_tools.py # LangChain工具 + MCP 集成（24 个工具）
│   └── plan_tools.py      # 规划工具（PlanQuery / RoutePreview）
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
| Neo4j | 用于知识图谱 |
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
AMAP_API_KEY=your_amap_api_key
MAP_PROVIDER=amap
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
LLM_MAX_TOKENS=4096      # 最大输出 token 数
```

---

## 🛠️ 工具系统

ToolRegistry 注册 10 个工具，供 ReAct Agent 调用。

### 知识图谱工具（6 个）

| 工具名称 | 查询维度 | 功能描述 |
|:---|:---|:---|
| `heritage_search` | 综合 | 非遗项目混合查询（图谱 + 向量），支持 ID/关键词/地域/类别 |
| `nearby_heritage_query` | 地理 | 邻近非遗查询（Haversine 距离 <100km） |
| `related_heritage_query` | 分类+地理 | 关联非遗查询（同类/同地区） |
| `nearby_region_query` | 地理 | 邻近地区查询 |
| `heritage_route_hint` | 地理 | 路线规划建议 + 顺访推荐 |
| `heritage_timeline_query` | 时间 | 朝代时间轴查询，支持按朝代/项目 ID/完整时间轴 |

### 规划工具（2 个）

| 工具名称 | 功能描述 |
|:---|:---|
| `plan_query` | 查询当前规划状态 |
| `route_preview` | 路线预览 |

### 通用工具（1 个）

| 工具名称 | 功能描述 |
|:---|:---|
| `plan_edit` | 修改已有旅游规划（含上下文 + Session 同步） |

### 个性化推荐

| 工具名称 | 查询维度 | 功能描述 |
|:---|:---|:---|
| `user_heritage_recommend` | 用户偏好 | 基于偏好图谱四级推理推荐非遗项目 |

---

## 📡 API 文档

### 认证机制

本系统采用 Session 进行用户认证。所有核心功能接口都需要认证才能访问。

### 核心接口

| 接口 | 方法 | 描述 |
|:---|:---:|:---|
| `/health` | GET | 健康检查（无需认证） |
| `/api/agent/travel-plan/create` | POST | 创建旅游规划 |
| `/api/agent/travel-plan/progress/{plan_id}` | GET | 查询规划进度（轮询） |
| `/api/agent/travel-plan/progress-stream/{plan_id}` | GET | 规划进度流（SSE） |
| `/api/agent/travel-plan/result/{plan_id}` | GET | 获取规划结果 |
| `/api/agent/travel-plan/cancel/{plan_id}` | POST | 取消规划 |
| `/api/agent/travel-plan/export/{plan_id}` | POST | 导出规划（PDF/JSON） |
| `/api/agent/chat-stream` | POST | AI 流式对话（SSE） |
| `/api/agent/start_edit_session` | POST | 开始编辑会话 |
| `/api/agent/export_pdf` | POST | 异步导出 PDF（返回 task_id） |
| `/api/agent/export_plan_pdf` | POST | 同步导出 PDF（直返文件） |

### 创建旅游规划

```http
POST /api/agent/travel-plan/create
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

### AI 流式对话

```http
POST /api/agent/chat-stream
```

```json
{
  "session_id": "session_xxx",
  "message": "我的预算是多少？"
}
```

响应为 SSE 流式（`text/event-stream`），逐 token 推送 `status`/`thinking`/`content`/`done` 事件。

---

## 🖥️ 前端集成

### 基本请求示例

```javascript
const response = await fetch('/api/agent/travel-plan/create', {
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

### 前端调用示例

```javascript
// 前端 PlanEditorAPI 封装了完整的编辑会话流程
// 详见 frontend/js/agent/plan-editor-api.js

// 创建规划
const response = await fetch('/api/agent/travel-plan/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
        heritage_ids: [1, 2, 3],
        travel_days: 3,
        departure_location: "西安市"
    })
});

// 开始编辑会话 → 流式对话 → 导出 PDF
// 前端通过 PlanEditorAPI 管理完整流程
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
