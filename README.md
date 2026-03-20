# 陕西非物质文化遗产智能旅游平台

<p align="center">
  <img src="https://raw.githubusercontent.com/Elaine-one/shaanxi-heritage-ai-platform/main/docs/banner.png" alt="陕西非遗智能旅游平台" width="100%"/>
</p>

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-orange.svg)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-red.svg)
![GitHub Stars](https://img.shields.io/github/stars/Elaine-one/shaanxi-heritage-ai-platform?style=social)
![GitHub Forks](https://img.shields.io/github/forks/Elaine-one/shaanxi-heritage-ai-platform?style=social)

</div>

---

## 📖 项目简介

基于 **AI 大语言模型** 与 **Agent 智能代理** 技术，构建的陕西非物质文化遗产数字化展示与智能旅游规划平台。

### 🎯 核心价值

| 维度 | 价值 |
|:---:|:---|
| 🏛️ **文化传承** | 数字化保存与展示陕西非遗资源 |
| 🤖 **智能体验** | AI 驱动的个性化旅游规划服务 |
| 💬 **用户互动** | 社区化的文化交流与内容创作 |

---

## ✨ 功能特性

### 🗺️ 智能旅游规划

- AI 驱动的个性化路线规划
- 基于天气、位置的非遗景点推荐
- 多格式规划方案导出 (PDF/CSV/JSON)

### 🏛️ 非遗文化展示

- 丰富的非遗项目数据库
- 地图可视化地理分布
- 详细的历史渊源与传承人信息

### 💬 AI 智能助手

- 基于 ReAct Agent 的智能对话
- 上下文记忆与知识图谱检索
- 实时天气查询与出行建议

### 👥 社区互动

- 论坛帖子与评论系统
- 用户创作内容分享
- 收藏与浏览历史管理

---

## 🏗️ 系统架构

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

### 技术栈全景

| 层级 | 技术栈 |
|:---|:---|
| **Frontend** | HTML5, CSS3, JavaScript, 百度地图 API |
| **Backend** | Django 4.2, DRF 3.14, MySQL 8.0, Redis 7.0 |
| **Agent** | FastAPI, Pydantic, 上下文工程, 知识图谱, RAG, MCP |
| **AI** | OpenAI, DashScope, DeepSeek, 智谱 GLM (多厂商切换) |

### Agent 系统架构

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
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  LLM模型    │      │  工具调用    │      │  上下文记忆  │
│ 多厂商支持   │      │ MCP/非遗等  │      │ Redis/向量   │
└─────────────┘      └─────────────┘      └─────────────┘
```

---

## 📂 项目结构

```
shaanxi-heritage-ai-platform/
├── Agent/                    # 🤖 AI 智能规划服务
│   ├── agent/                # Agent 核心模块
│   ├── api/                  # FastAPI 接口层
│   ├── context/              # 上下文工程
│   ├── memory/               # 记忆系统
│   ├── tools/                # 工具系统
│   └── services/             # 业务服务
│
├── backend/                  # 🖥️ Django 后端服务
│   ├── heritage_api/         # 核心应用
│   │   ├── api/             # API 视图层
│   │   ├── models.py        # 数据模型
│   │   └── serializers/     # 序列化器
│   └── heritage_project/     # 项目配置
│
└── frontend/                 # 🎨 前端界面
    ├── pages/                # HTML 页面
    ├── js/                   # JavaScript
    │   ├── agent/            # Agent 交互
    │   ├── api/              # API 封装
    │   └── components/      # 可复用组件
    └── css/                  # 样式文件
```

---

## 🚀 快速开始

### 环境要求

| 组件 | 版本 | 用途 |
|:---|:---|:---|
| Python | 3.8+ | 后端运行环境 |
| MySQL | 8.0+ | 数据存储 |
| Redis | 6.0+ | 缓存与会话 |
| Neo4j | 5.0+ | 知识图谱存储 |
| MinIO | Latest | 对象存储 |

### 安装部署

```bash
# 1. 克隆项目
git clone https://github.com/Elaine-one/shaanxi-heritage-ai-platform.git
cd shaanxi-heritage-ai-platform

# 2. 安装依赖
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
```

### 访问地址

| 服务 | 地址 | 说明 |
|:---|:---|:---|
| 🌐 前端首页 | http://localhost:8000 | 主界面 |
| 📡 API 文档 | http://localhost:8000/api | RESTful API |
| 🤖 Agent 文档 | http://localhost:8001/docs | FastAPI 文档 |

---

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
```

### 多厂商 LLM 配置

| 厂商 | LLM_PROVIDER | 默认模型 |
|:---|:---|:---|
| 通义千问 (DashScope) | `dashscope` | qwen-plus |
| 智谱 GLM | `zhipu` | glm-4 |
| DeepSeek | `deepseek` | deepseek-chat |
| OpenAI | `openai` | gpt-4o |

---

## 📚 文档导航

| 文档 | 说明 |
|:---|:---|
| [📖 Agent 文档](Agent/README.md) | Agent 系统详细文档 |
| [📖 Agent 更新日志](Agent/CHANGELOG.md) | Agent 版本更新记录 |
| [🖥️ Backend 文档](backend/README.md) | 后端服务详细文档 |
| [📋 Backend 更新日志](backend/CHANGELOG.md) | Backend 版本更新记录 |
| [🎨 Frontend 文档](frontend/README.md) | 前端服务详细文档 |
| [📋 Frontend 更新日志](frontend/CHANGELOG.md) | Frontend 版本更新记录 |
| [📋 项目规划](.trae/documents/) | 开发规划与设计文档 |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📄 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，**禁止任何形式的使用、修改、分发或商业利用**。

- 本项目代码仅供学习和参考，不得用于任何实际项目
- 未经授权，禁止复制或引用本项目的任何代码
- 所有权利保留，侵权必究

---

## 📬 联系方式

- **项目维护者**: elaine
- **邮箱**: onee20589@gmail.com
- **项目链接**: [GitHub Repository](https://github.com/Elaine-one/shaanxi-heritage-ai-platform)

---

<p align="center">
  <sub>Built with ❤️ for Shaanxi Intangible Cultural Heritage</sub>
</p>
