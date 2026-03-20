# 🖥️ Django 后端服务

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![Django REST Framework](https://img.shields.io/badge/DRF-3.14-orange.svg)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-red.svg)

</div>

---

## 📖 项目概述

陕西非遗文化智能旅游平台的后端服务，提供用户认证、非遗数据管理、论坛系统、Agent 服务代理等核心功能。

基于 **Django 4.2** + **Django REST Framework** 构建的后端 API 服务，为前端提供数据接口和业务逻辑支持。

---

## ✨ 核心功能

| 功能 | 说明 |
|:---|:---|
| 🔐 **用户认证** | 邮箱注册、登录、密码重置、验证码 |
| 🏛️ **非遗管理** | 非遗项目 CRUD、收藏、浏览历史 |
| 🗺️ **地图服务** | 百度地图 API 配置、地理编码 |
| 💬 **论坛系统** | 帖子、评论、点赞、收藏、标签 |
| 🎨 **创作中心** | 用户创作内容管理 |
| 📰 **资讯政策** | 新闻资讯、政策法规展示 |
| 🤖 **Agent 代理** | 反向代理 AI 规划服务 |

---

## 🏗️ 技术架构

### 技术栈

| 类别 | 技术 |
|:---|:---|
| **框架** | Django 4.2 + DRF 3.14 |
| **数据库** | MySQL 8.0 |
| **缓存** | Redis |
| **异步任务** | Celery + django-celery-beat |
| **跨域处理** | django-cors-headers |
| **HTTP 客户端** | httpx (Agent 代理) |

---

## 📂 项目结构

```
backend/
├── heritage_project/           # ⚙️ Django项目配置
│   ├── settings.py            # 开发环境配置
│   ├── settings_production.py # 生产环境配置
│   ├── urls.py                # 主路由配置
│   ├── middleware.py          # 自定义中间件
│   ├── celery.py              # Celery配置
│   ├── wsgi.py                # WSGI入口
│   └── asgi.py                # ASGI入口
│
├── heritage_api/               # 📦 核心应用
│   ├── api/                   # 🔌 API视图层
│   │   ├── auth.py           # 认证接口
│   │   ├── heritage.py       # 非遗接口
│   │   ├── user.py           # 用户接口
│   │   ├── history.py        # 历史记录接口
│   │   ├── forum.py          # 论坛接口
│   │   ├── map.py            # 地图接口
│   │   └── agent.py          # Agent代理接口
│   │
│   ├── serializers/          # 📋 序列化器
│   │   ├── heritage.py
│   │   ├── user.py
│   │   └── forum.py
│   │
│   ├── services/             # 🔧 业务服务
│   │   └── search.py         # 搜索服务
│   │
│   ├── models.py             # 💾 核心数据模型
│   ├── user_models.py        # 用户相关模型
│   ├── forum_models.py       # 论坛相关模型
│   ├── creation_models.py    # 创作中心模型
│   ├── urls.py               # API路由
│   ├── forum_urls.py         # 论坛路由
│   ├── redis_utils.py        # Redis工具
│   ├── date_utils.py         # 日期工具
│   ├── map_config.py         # 地图配置
│   ├── tasks.py              # Celery异步任务
│   └── utils.py              # 通用工具
│
├── static/                    # 📁 静态文件
├── .env.example               # 环境变量示例
├── requirements.txt           # Python依赖
├── manage.py                  # Django管理脚本
└── README.md                 # 项目文档
```

---

## 🚀 快速开始

### 环境要求

| 组件 | 版本 | 用途 |
|:---|:---|:---|
| Python | 3.8+ | 后端运行环境 |
| MySQL | 8.0+ | 数据存储 |
| Redis | 6.0+ | 缓存与会话 |

### 安装部署

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env

# 3. 编辑 .env 配置必要参数
DJANGO_SECRET_KEY=your_secret_key_here
DB_NAME=heritage_db
DB_USER=root
DB_PASSWORD=your_password
REDIS_HOST=127.0.0.1
BAIDU_MAP_AK=your_baidu_map_ak
AGENT_SERVICE_URL=http://localhost:8001
```

### 数据库初始化

```bash
# 创建数据库迁移
python manage.py makemigrations

# 执行迁移
python manage.py migrate

# 导入非遗数据
python manage.py import_heritage_data
```

### 启动服务

```bash
# 开发环境
python manage.py runserver 0.0.0.0:8000

# 生产环境 (使用 gunicorn)
gunicorn heritage_project.wsgi:application --bind 0.0.0.0:8000
```

---

## 📡 API 文档

### 认证接口

| 接口 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/auth/register/` | POST | 用户注册（邮箱注册） |
| `/api/auth/login/` | POST | 用户登录（邮箱登录） |
| `/api/auth/logout/` | POST | 用户登出 |
| `/api/auth/user/` | GET | 获取当前用户信息 |
| `/api/auth/csrf/` | GET | 获取 CSRF Token |
| `/api/auth/captcha/generate/` | GET | 生成图形验证码 |
| `/api/auth/captcha/verify/` | POST | 验证验证码 |
| `/api/auth/request-password-reset/` | POST | 请求密码重置 |
| `/api/auth/reset-password/` | POST | 重置密码 |
| `/api/auth/security-status/` | GET | 获取安全状态 |

### 非遗接口

| 接口 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/items/` | GET | 获取非遗列表（支持分页、筛选、搜索） |
| `/api/items/{id}/` | GET | 获取非遗详情 |
| `/api/items/categories/` | GET | 获取所有类别列表 |
| `/api/items/regions/` | GET | 获取所有地区列表 |
| `/api/items/levels/` | GET | 获取所有级别列表 |

### 收藏 & 历史接口

| 接口 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/favorites/` | GET | 获取用户收藏列表 |
| `/api/favorites/add/` | POST | 添加收藏 |
| `/api/favorites/remove/` | POST | 移除收藏 |
| `/api/favorites/check/` | GET | 检查收藏状态 |
| `/api/history/` | GET | 获取浏览历史列表 |
| `/api/history/add/` | POST | 添加浏览记录 |
| `/api/history/clear/` | DELETE | 清除所有浏览历史 |

### 用户接口

| 接口 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/profile/` | GET/PATCH | 用户资料 |
| `/api/profile/me/` | GET | 获取当前用户详细信息 |
| `/api/profile/upload-avatar/` | POST | 上传用户头像 |
| `/api/analytics/` | GET | 获取用户创作分析数据 |
| `/api/export-data/` | POST | 导出用户数据 |
| `/api/user/stats/` | GET | 获取用户统计数据 |

### 资讯政策接口

| 接口 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/news/` | GET | 新闻列表 |
| `/api/news/{id}/` | GET | 新闻详情 |
| `/api/policies/` | GET | 政策列表 |
| `/api/policies/{id}/` | GET | 政策详情 |

### 创作中心接口

| 接口 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/creations/` | GET/POST | 创作列表/创建创作 |
| `/api/creations/{id}/` | GET/PUT/DELETE | 创作详情/更新/删除 |
| `/api/creation-likes/` | GET/POST | 点赞列表/点赞创作 |
| `/api/creation-comments/` | GET/POST | 评论列表/发表评论 |

### 论坛接口

| 接口 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/forum/posts/` | GET/POST | 帖子列表/创建帖子 |
| `/api/forum/posts/{id}/` | GET/PUT/DELETE | 帖子详情/更新/删除 |
| `/api/forum/posts/{id}/like/` | POST | 切换帖子点赞状态 |
| `/api/forum/posts/{id}/favorite/` | POST | 切换帖子收藏状态 |
| `/api/forum/tags/` | GET | 标签列表 |
| `/api/forum/users/{id}/follow/` | POST | 切换用户关注状态 |

### Agent 代理接口

| 接口 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/agent/{path}` | ALL | 代理转发到 Agent 服务 |
| `/api/agent-service-url/` | GET | 获取 Agent 服务地址 |
| `/api/map/config/` | GET | 获取百度地图 API 配置 |

---

## 💾 数据模型

### 核心模型

| 模型 | 说明 |
|:---|:---|
| `Heritage` | 非遗项目 |
| `UserFavorite` | 用户收藏 |
| `UserHistory` | 浏览历史 |
| `News` | 新闻资讯 |
| `Policy` | 政策法规 |

### 用户 & 创作模型

| 模型 | 说明 |
|:---|:---|
| `UserProfile` | 用户资料 |
| `UserCreation` | 用户创作 |
| `CreationLike` | 创作点赞 |
| `CreationComment` | 创作评论 |
| `CreationFavorite` | 创作收藏 |

### 论坛模型

| 模型 | 说明 |
|:---|:---|
| `ForumPost` | 论坛帖子 |
| `ForumComment` | 论坛评论 |
| `ForumTag` | 论坛标签 |
| `ForumPostLike` | 帖子点赞 |
| `ForumPostFavorite` | 帖子收藏 |
| `ForumUserFollow` | 用户关注 |
| `ForumUserStats` | 用户统计 |

---

## 🔧 高级配置

### Agent 服务代理

后端通过反向代理将 `/api/agent/` 路径的请求转发到 Agent 服务：

```python
# 请求流程
前端 → Django后端(/api/agent/*) → Agent服务(localhost:8001)
```

### Redis 缓存

Redis 工具类封装提供以下功能：

| 功能 | 方法 |
|:---|:---|
| 验证码缓存 | `set_captcha()`, `get_captcha()` |
| 频率限制 | `check_rate_limit()` |
| 登录安全 | `incr_login_attempts()`, `is_login_locked()` |
| 浏览量统计 | `incr_view_count()`, `get_view_count()` |

### Celery 异步任务

```bash
celery -A heritage_project worker -l info
celery -A heritage_project beat -l info
```

---

## 🛠️ 开发指南

### 添加新的 API 接口

1. 在 `api/` 目录下创建视图
2. 在 `serializers/` 目录下创建序列化器
3. 在 `urls.py` 中注册路由

### 添加新的数据模型

1. 在 `models.py` 或单独的模型文件中定义
2. 创建迁移文件: `python manage.py makemigrations`
3. 执行迁移: `python manage.py migrate`

---

## 📄 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，禁止任何形式的使用、修改、分发或商业利用。

---

## 📬 联系方式

- **项目维护者**: elaine
- **邮箱**: onee20589@gmail.com
- **项目链接**: [GitHub Repository](https://github.com/Elaine-one/shaanxi-heritage-ai-platform)

---

<p align="center">
  <sub>Built with ❤️ for Shaanxi Intangible Cultural Heritage</sub>
</p>
