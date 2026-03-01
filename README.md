# 陕西非物质文化遗产智能旅游平台

> 基于 AI 技术的非物质文化遗产数字化展示与智能旅游规划平台

## 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，禁止任何形式的使用、修改、分发或商业利用。

---

## 项目愿景

将陕西丰富的非物质文化遗产资源与现代AI技术深度融合，构建"文化展示 + 智能规划 + 社区互动"三位一体的数字化平台，让传统文化以更智能、更便捷的方式触达用户。

### 核心价值主张

| 维度 | 价值 |
|-----|------|
| 文化传承 | 数字化保存与展示陕西非遗资源 |
| 智能体验 | AI驱动的个性化旅游规划服务 |
| 用户互动 | 社区化的文化交流与内容创作 |

---

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户层 (Frontend)                         │
│                    HTML5 + CSS3 + JavaScript                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      网关层 (Django Backend)                      │
│                    端口: 8000 | 统一入口                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ 用户认证    │  │ 数据API     │  │ Agent代理   │              │
│  │ Session     │  │ RESTful     │  │ 反向代理    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   MySQL     │      │   Redis     │      │Agent Service│
│   数据存储   │      │   缓存/会话  │      │  端口: 8001 │
└─────────────┘      └─────────────┘      └─────────────┘
                                                  │
                                                  ▼
                                         ┌─────────────┐
                                         │   MinIO     │
                                         │   对象存储   │
                                         └─────────────┘
```

### 三层服务架构

| 层级 | 服务 | 端口 | 职责 |
|-----|------|------|------|
| 展示层 | Frontend | - | 用户界面、交互逻辑 |
| 网关层 | Django Backend | 8000 | 认证、数据API、请求路由 |
| 智能层 | Agent Service | 8001 | AI规划、内容生成 |

### 数据流向

```
用户请求 → Django认证 → 业务处理
                    ↓
         ┌─────────┴─────────┐
         ↓                   ↓
    数据查询              Agent代理
    (MySQL/Redis)         (FastAPI)
                              ↓
                         LLM推理
                              ↓
                         工具调用
                              ↓
                         结果返回
```

---

## 技术选型

### 技术栈全景

```
┌────────────────────────────────────────────────────────────┐
│                        Frontend                             │
│  HTML5 | CSS3 | JavaScript | 百度地图API | Fetch API       │
└────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────────────────────────────────────┐
│                     Backend (Django)                        │
│  Django 4.2 | DRF 3.14 | MySQL 8.0 | Redis 7.0 | Celery   │
└────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────────────────────────────────────┐
│                     Agent (FastAPI)                         │
│  FastAPI | LangChain 1.0 | Pydantic | ReportLab | MinIO   │
└────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────────────────────────────────────┐
│                        AI Layer                             │
│  OpenAI | DashScope | DeepSeek | 智谱GLM | 多厂商支持       │
└────────────────────────────────────────────────────────────┘
```

### 核心技术决策

| 决策点 | 选择 | 理由 |
|-------|------|------|
| 后端框架 | Django | 成熟稳定、ORM强大、Admin内置 |
| Agent框架 | FastAPI | 异步高性能、原生OpenAPI文档 |
| AI框架 | LangChain | 工具链丰富、多模型支持 |
| 数据库 | MySQL | 事务支持、生态成熟 |
| 缓存 | Redis | 高性能、支持多种数据结构 |
| 对象存储 | MinIO | 开源、S3兼容、私有部署 |

---

## 核心模块设计

### 模块依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Module                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 展示模块  │  │ 规划模块  │  │ 社区模块  │  │ 用户模块  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend Module                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 认证服务  │  │ 数据服务  │  │ 代理服务  │  │ 缓存服务  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent Module                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ ReAct代理 │  │ 工具系统  │  │ 记忆系统  │  │ 导出系统  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Agent 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    ReAct Agent 核心                          │
│                                                              │
│   用户输入 → 推理(Reason) → 行动(Act) → 观察(Observe)        │
│                     ↑                           │            │
│                     └───────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  LLM模型    │      │  工具调用    │      │  上下文记忆  │
│ 多厂商支持   │      │ 非遗/天气等  │      │ Redis存储   │
└─────────────┘      └─────────────┘      └─────────────┘
```

### 工具系统

| 工具 | 功能 | 数据源 |
|-----|------|-------|
| heritage_search | 非遗项目查询 | MySQL |
| weather_query | 天气预报查询 | Open-Meteo API |
| travel_route_planning | 路线规划 | 百度地图API |
| knowledge_base_qa | 知识问答 | LLM |
| plan_edit | 规划修改 | 内存 |

---

## 项目结构

```
shaanxi-heritage-ai-platform/
├── Agent/                    # AI智能规划服务
│   ├── api/                  # FastAPI接口层
│   ├── agent/                # ReAct代理核心
│   ├── models/               # LLM模型封装
│   ├── tools/                # 工具系统
│   ├── services/             # 业务服务
│   ├── prompts/              # 提示词模板
│   └── config/               # 配置管理
│
├── backend/                  # Django后端服务
│   ├── heritage_api/         # 核心应用
│   │   ├── api/              # 视图层
│   │   ├── serializers/      # 序列化器
│   │   ├── services/         # 服务层
│   │   └── models.py         # 数据模型
│   └── heritage_project/     # 项目配置
│
├── frontend/                 # 前端界面
│   ├── pages/                # HTML页面
│   ├── js/                   # JavaScript
│   │   ├── agent/            # Agent交互
│   │   ├── common/           # 通用模块
│   │   └── pages/            # 页面脚本
│   └── css/                  # 样式文件
```

---

## 快速开始

### 环境要求

| 组件 | 版本 | 用途 |
|-----|------|------|
| Python | 3.8+ | 后端运行环境 |
| MySQL | 8.0+ | 数据存储 |
| Redis | 6.0+ | 缓存与会话 |
| MinIO | Latest | 对象存储 |

### 一键启动

```bash
# 1. 安装依赖
pip install -r backend/requirements.txt
pip install -r Agent/requirements.txt

# 2. 配置环境变量
cp backend/.env.example backend/.env
cp Agent/.env.example Agent/.env

# 3. 初始化数据库
cd backend && python manage.py migrate

# 4. 启动服务
# 终端1: Django后端
python manage.py runserver 0.0.0.0:8000

# 终端2: Agent服务
cd Agent && python -m uvicorn Agent.api.app:app --host 0.0.0.0 --port 8001
```

### 访问地址

| 服务 | 地址 | 说明 |
|-----|------|------|
| 前端首页 | http://localhost:8000 | 主界面 |
| API文档 | http://localhost:8000/api | RESTful API |
| Agent文档 | http://localhost:8001/docs | FastAPI文档 |

---

## 配置说明

### 必需配置项

```bash
# backend/.env
DJANGO_SECRET_KEY=your_secret_key
DB_PASSWORD=your_db_password
REDIS_HOST=127.0.0.1
BAIDU_MAP_AK=your_baidu_ak
AGENT_SERVICE_URL=http://localhost:8001

# Agent/.env
LLM_PROVIDER=dashscope
LLM_API_KEY=your_api_key
LLM_MODEL=qwen-plus
BAIDU_MAP_AK=your_baidu_ak
REDIS_HOST=127.0.0.1
MINIO_ENDPOINT=localhost:9000
```

### 多厂商LLM配置

```bash
# DashScope (通义千问)
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-plus

# 智谱GLM
LLM_PROVIDER=zhipu
LLM_MODEL=glm-4

# DeepSeek
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat

# OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
```

---

## 文档索引

### 架构文档
| 文档 | 说明 |
|-----|------|
| [Agent README](Agent/README.md) | Agent系统详细文档 |
| [Backend README](backend/README.md) | 后端服务详细文档 |
| [Frontend README](frontend/README.md) | 前端服务详细文档 |
| [数据库结构](backend/complete_database_schema.md) | 数据库表结构 |
---

## 联系方式

- 项目维护者: elaine
- 邮箱: onee20589@gmail.com
- 项目链接: https://github.com/Elaine-one/shaanxi-heritage-ai-platform
