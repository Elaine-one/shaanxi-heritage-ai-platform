# 陕西非物质文化遗产智能旅游平台

<p align="center">
  <img src="https://github.com/user-attachments/assets/08d4fce6-b204-4947-839b-da6863727123" alt="陕西非遗智能旅游平台" width="100%"/>
</p>

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.134+-orange.svg)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-red.svg)
![GitHub Stars](https://img.shields.io/github/stars/Elaine-one/shaanxi-heritage-ai-platform?style=social)
![GitHub Forks](https://img.shields.io/github/forks/Elaine-one/shaanxi-heritage-ai-platform?style=social)

</div>

***

## 📖 项目简介

基于 **AI 大语言模型** 与 **LangGraph ReAct Agent** 技术，构建的陕西非物质文化遗产数字化展示与智能旅游规划平台。

### 🎯 核心价值

|      维度      | 价值              |
| :----------: | :-------------- |
| 🏛️ **文化传承** | 数字化保存与展示陕西非遗资源  |
|  🤖 **智能体验** | AI 驱动的个性化旅游规划服务 |
|  💬 **用户互动** | 社区化的文化交流与内容创作   |

***

## ✨ 功能特性

### 🏛️ 非遗文化展示

- 丰富的非遗项目数据库（名称、类别、级别、地区、批次、历史渊源、传承人等）
- 地图可视化地理分布（支持高德/百度地图切换）
- 非遗详情页与图库展示
- 非遗资讯与政策法规独立板块

### 🗺️ 智能旅游规划

- AI 驱动的个性化路线规划（基于真实道路距离优化，解决回头路问题）
- 支持简单模式（`skip_ai_suggestions`）与完整模式切换
- 基于天气、位置的非遗景点推荐（Open-Meteo 免费天气 API）
- 多格式规划方案导出（PDF / JSON），PDF 自动生成并上传 MinIO 对象存储

### 🤖 AI 智能助手

- 基于 **LangGraph ReAct Agent** 的智能对话，支持流式输出
- 安全检测层（`safety_checker`）过滤敏感输入
- 上下文记忆与知识图谱检索（Neo4j）
- RAG 增强检索（ChromaDB 向量数据库）
- MCP（Model Context Protocol）工具调用：高德地图、天气查询、周边搜索等
- 多厂商 LLM 切换（OpenAI / DashScope / DeepSeek / 智谱 GLM / Moonshot / Ollama）

### 👥 社区互动

- 论坛系统：帖子、评论、标签、公告、规则、举报
- 用户创作中心：作品发布、点赞、评论、收藏、浏览历史
- 收藏与浏览历史管理

### 🖥️ 管理后台

- 独立 `admin-frontend`（Vue3 + Vite + Element Plus）管理后台前端，开发端口 `3000`
- 自定义 Admin API（`/api/admin/*`）：用户管理、论坛管理、创作审核、操作日志等

***

## 🏗️ 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户层 (Frontend)                         │
│  ┌─────────────────────┐  ┌─────────────────────────────────┐  │
│  │ 用户前端             │  │ 管理后台前端 (admin-frontend)    │  │
│  │ HTML5 + CSS3 + JS   │  │ Vue3 + Vite                     │  │
│  └─────────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      网关层 (Nginx)                              │
│                    端口: 80 | 统一入口                            │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │ / 静态文件  │  │ /api/      │  │/api/agent/ │  │/vue-admin│ │
│  │ 前端 SPA   │  │ Django API │  │ Agent 直连  │  │ 管理后台  │ │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────────┘
      │                    │                    │
      ▼                    ▼                    ▼
┌──────────┐     ┌─────────────┐      ┌─────────────┐
│ Frontend │     │   Django    │      │   Agent     │
│  静态文件  │     │  端口: 8000  │      │  端口: 8001  │
└──────────┘     └──────┬──────┘      └──────┬──────┘
                        │                    │
                  ┌─────┼─────┐        ┌─────┼──────────────┐
                  ▼     ▼     ▼        ▼     ▼     ▼        ▼
            ┌──────┐ ┌──────┐    ┌────────┐ ┌──────┐ ┌──────────┐
            │MySQL │ │Redis │    │ Neo4j  │ │Redis │ │ ChromaDB │
            │ 数据  │ │Celery│    │知识图谱│ │ 会话  │ │ 向量数据库│
            └──────┘ │验证码│    └────────┘ └──────┘ └─────┬────┘
            ┌────────┐│限流锁│         ▲              ▲         │
            │ Django ││浏览量│         │              │         ▼
            │ Admin  │└──────┘         └──────────────┘  ┌──────────┐
            └────────┘        共享 Redis 实例            │ SQLite   │
                                                     │L3审计账本│
                                                     └──────────┘
```

### 技术栈全景

| 层级                 | 技术栈                                                                                           |
| :----------------- | :-------------------------------------------------------------------------------------------- |
| **Frontend**       | HTML5, CSS3, JavaScript, 高德地图 API / 百度地图 API, MaxKB, Dify                                     |
| **Admin Frontend** | Vue3 3.5, Vite 8, Element Plus 2.14, Pinia 3, Vue Router 4.6, axios 1.16, Sass 1.99 |
| **Backend**        | Django 4.2, DRF 3.16, MySQL 8.0, Redis 7.0, Celery, bleach, jieba                             |
| **Agent**          | FastAPI 0.134, Pydantic, LangGraph, LangChain, ChromaDB, sentence-transformers, OpenTelemetry |
| **AI**             | OpenAI, DashScope, DeepSeek, 智谱 GLM, Moonshot, Ollama (多厂商切换)                                 |

### Agent 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                 LangGraph ReAct Agent 核心                   │
│                                                              │
│   用户输入                                                   │
│     ↓                                                        │
│   安全检测 (safety_checker)                                  │
│     ↓                                                        │
│   上下文构建 (context_builder) ← 记忆协调器 (memory_coordinator)│
│     ↓                                    ↑                   │
│   意图检测                          L1 Redis 感知层          │
│     ↓                               L2 Neo4j 图记忆          │
│   LangGraph ReAct Agent             L3 SQLite 审计账本       │
│     ↓                                                        │
│   ├─→ RAG 检索 (ChromaDB)                                    │
│   ├─→ 知识图谱查询 (Neo4j)                                   │
│   ├─→ MCP 工具调用 (高德地图 / 天气 / 周边搜索)               │
│   ├─→ LLM 推理                                               │
│     ↓                                                        │
│   流式输出 / Final Answer                                    │
│     ↓                                                        │
│   返回用户                                                   │
└─────────────────────────────────────────────────────────────┘
```

***

## 📂 项目结构

```
shaanxi-heritage-ai-platform/
├── Agent/                    # 🤖 AI Agent 服务 (FastAPI)
│   ├── agent/                # Agent 核心 (LangGraph ReAct)
│   ├── api/                  # FastAPI 接口 & 路由
│   ├── config/               # 配置 (settings, memory_budget)
│   ├── context/              # 上下文工程
│   ├── core/                 # 启动 & 资源管理
│   ├── memory/               # 记忆系统 (Redis/Neo4j/SQLite)
│   ├── models/               # LLM 模型封装
│   ├── prompts/              # 提示词模板
│   ├── safety/               # 安全检测
│   ├── services/             # 业务服务 (天气/PDF/MinIO/地理编码)
│   ├── tools/                # 工具系统 (MCP/地图/RAG)
│   └── utils/                # 工具函数
│
├── backend/                  # 🖥️ Django 后端服务
│   ├── heritage_api/         # 核心应用
│   │   ├── api/              # API 视图层
│   │   ├── models.py         # 核心模型 (Heritage/News/Policy)
│   │   ├── user_models.py    # 用户模型
│   │   ├── forum_models.py   # 论坛模型
│   │   ├── creation_models.py# 创作模型
│   │   └── serializers/      # 序列化器
│   └── heritage_project/     # 项目配置
│
├── frontend/                 # 🎨 用户前端 (HTML5/CSS3/JS)
│   ├── pages/                # HTML 页面
│   ├── js/                   # JavaScript
│   │   ├── agent/            # Agent 交互
│   │   ├── api/              # API 封装
│   │   └── components/       # 可复用组件
│   ├── css/                  # 样式文件
│   └── lib/                  # 第三方嵌入 (MaxKB/Dify)
│
└── admin-frontend/           # 🛠️ 管理后台前端 (Vue3 + Vite)
    ├── src/
    ├── index.html
    ├── package.json
    └── vite.config.js
```

***

## 🚀 快速开始

### 环境要求

| 组件      | 版本     | 用途                |
| :------ | :----- | :---------------- |
| Python  | 3.8+   | 后端运行环境            |
| Node.js | 18+    | admin-frontend 构建 |
| MySQL   | 8.0+   | 数据存储              |
| Redis   | 6.0+   | 缓存与会话             |
| Neo4j   | 5.0+   | 知识图谱存储            |
| MinIO   | Latest | 对象存储              |

### 安装部署

```bash
# 1. 克隆项目
git clone https://github.com/Elaine-one/shaanxi-heritage-ai-platform.git
cd shaanxi-heritage-ai-platform

# 2. 安装后端依赖
pip install -r backend/requirements.txt
pip install -r Agent/requirements.txt

# 3. 配置环境变量
cp backend/.env.example backend/.env
cp Agent/.env.example Agent/.env

# 4. 初始化数据库
cd backend && python manage.py migrate

# 5. 启动服务
# 终端1: Django 后端
cd backend && python manage.py runserver

# 终端2: Agent 服务
python -m Agent.api.app

# 终端3: 管理后台前端 (开发模式，端口 3000)
cd admin-frontend && npm install && npm run dev

# 终端3 (备选): 管理后台前端构建生产包
# cd admin-frontend && npm install && npm run build
# 构建产物输出到 backend/admin_static/，通过 Django /vue-admin/ 访问
```

### 访问地址

| 服务          | 地址                           | 说明                    |
| :---------- | :--------------------------- | :-------------------- |
| 🌐 前端首页     | <http://localhost:8000>      | 主界面                   |
| 📡 API 文档   | <http://localhost:8000/api>  | RESTful API           |
| 🤖 Agent 文档 | <http://localhost:8001/docs> | FastAPI 文档            |
| 🛠️ 管理后台开发 | <http://localhost:3000>      | admin-frontend (开发模式) |
| 🛠️ 管理后台生产 | <http://localhost:8000/vue-admin/> | admin-frontend (生产模式) |

***

## 🔧 配置说明

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
REDIS_HOST=127.0.0.1
MINIO_ENDPOINT=localhost:9000

# 地图服务 (Agent)
AMAP_API_KEY=your_amap_api_key
MAP_PROVIDER=amap          # amap | baidu
```

### 多厂商 LLM 配置

| 厂商               | LLM\_PROVIDER | 默认模型           |
| :--------------- | :------------ | :------------- |
| 通义千问 (DashScope) | `dashscope`   | qwen-plus      |
| 智谱 GLM           | `zhipu`       | glm-4          |
| DeepSeek         | `deepseek`    | deepseek-chat  |
| OpenAI           | `openai`      | gpt-4o         |
| Moonshot         | `moonshot`    | moonshot-v1-8k |
| Ollama           | `ollama`      | llama3         |

> 记忆与上下文预算相关环境变量（`MODEL_CONTEXT_WINDOW`、`INPUT_BUDGET`、`OUTPUT_BUDGET_*`、`RAG_*`、`MEMORY_L1_*`、`GRAPH_MEMORY_ENABLED` 等）详见 `Agent/.env.example` 与 `Agent/config/memory_budget.py`。

***

## 📚 文档导航

| 文档                                        | 说明              |
| :---------------------------------------- | :-------------- |
| [📖 Agent 文档](Agent/README.md)            | Agent 系统详细文档    |
| [📖 Agent 更新日志](Agent/CHANGELOG.md)       | Agent 版本更新记录    |
| [🖥️ Backend 文档](backend/README.md)       | 后端服务详细文档        |
| [📋 Backend 更新日志](backend/CHANGELOG.md)   | Backend 版本更新记录  |
| [🎨 Frontend 文档](frontend/README.md)      | 前端服务详细文档        |
| [📋 Frontend 更新日志](frontend/CHANGELOG.md) | Frontend 版本更新记录 |
| [📋 项目规划](.trae/documents/)               | 开发规划与设计文档       |

***

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

***

## 📄 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，**禁止任何形式的使用、修改、分发或商业利用**。

- 本项目代码仅供学习和参考，不得用于任何实际项目
- 未经授权，禁止复制或引用本项目的任何代码
- 所有权利保留，侵权必究

***

## 📬 联系方式

- **项目维护者**: elaine
- **邮箱**: <onee20589@gmail.com>
- **项目链接**: [GitHub Repository](https://github.com/Elaine-one/shaanxi-heritage-ai-platform)

***

<p align="center">
  <sub>Built with ❤️ for Shaanxi Intangible Cultural Heritage</sub>
</p>
