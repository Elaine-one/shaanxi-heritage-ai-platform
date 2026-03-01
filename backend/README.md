# Django 后端服务

陕西非遗文化智能旅游平台的后端服务，提供用户认证、非遗数据管理、论坛系统、Agent服务代理等核心功能。

## 项目概述

基于 Django 4.2 + Django REST Framework 构建的后端API服务，为前端提供数据接口和业务逻辑支持。

### 核心功能

- 🔐 **用户认证**: 邮箱注册、登录、密码重置、验证码
- 🏛️ **非遗管理**: 非遗项目CRUD、收藏、浏览历史
- 🗺️ **地图服务**: 百度地图API配置、地理编码
- 💬 **论坛系统**: 帖子、评论、点赞、收藏、标签
- 🎨 **创作中心**: 用户创作内容管理
- 📰 **资讯政策**: 新闻资讯、政策法规展示
- 🤖 **Agent代理**: 反向代理AI规划服务

## 技术架构

### 技术栈

- **框架**: Django 4.2 + Django REST Framework 3.14
- **数据库**: MySQL 8.0
- **缓存**: Redis
- **异步任务**: Celery + django-celery-beat
- **跨域处理**: django-cors-headers
- **HTTP客户端**: httpx (Agent代理)

### 项目结构

```
backend/
├── heritage_project/           # Django项目配置
│   ├── settings.py             # 开发环境配置
│   ├── settings_production.py  # 生产环境配置
│   ├── urls.py                 # 主路由配置
│   ├── middleware.py           # 自定义中间件
│   ├── celery.py               # Celery配置
│   ├── wsgi.py                 # WSGI入口
│   └── asgi.py                 # ASGI入口
├── heritage_api/               # 核心应用
│   ├── api/                    # API视图层
│   │   ├── auth.py             # 认证接口
│   │   ├── heritage.py         # 非遗接口
│   │   ├── user.py             # 用户接口
│   │   ├── history.py          # 历史记录接口
│   │   ├── forum.py            # 论坛接口
│   │   ├── map.py              # 地图接口
│   │   └── agent.py            # Agent代理接口
│   ├── serializers/            # 序列化器
│   │   ├── heritage.py
│   │   ├── user.py
│   │   └── forum.py
│   ├── services/               # 业务服务层
│   │   └── search.py           # 搜索服务
│   ├── management/             # 管理命令
│   │   └── commands/
│   │       └── import_heritage_data.py
│   ├── migrations/             # 数据库迁移
│   ├── models.py               # 核心数据模型
│   ├── user_models.py          # 用户相关模型
│   ├── forum_models.py         # 论坛相关模型
│   ├── creation_models.py      # 创作中心模型
│   ├── urls.py                 # API路由
│   ├── forum_urls.py           # 论坛路由
│   ├── redis_utils.py          # Redis工具
│   └── utils.py                # 通用工具
├── static/                     # 静态文件
├── .env.example                # 环境变量示例
├── requirements.txt            # Python依赖
├── manage.py                   # Django管理脚本
└── README.md                   # 项目文档
```

## 快速开始

### 环境要求

- Python 3.8+
- MySQL 8.0+
- Redis 6.0+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要参数：

```bash
# Django配置
DJANGO_SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# 数据库配置
DB_NAME=heritage_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# 百度地图API
BAIDU_MAP_AK=your_baidu_map_ak

# Agent服务地址
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

# 生产环境 (使用gunicorn)
gunicorn heritage_project.wsgi:application --bind 0.0.0.0:8000
```

## API文档

### 认证接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/auth/register/` | POST | 用户注册 |
| `/api/auth/login/` | POST | 用户登录 |
| `/api/auth/logout/` | POST | 用户登出 |
| `/api/auth/user/` | GET | 获取用户信息 |
| `/api/auth/csrf/` | GET | 获取CSRF Token |
| `/api/auth/captcha/generate/` | GET | 生成验证码 |
| `/api/auth/captcha/verify/` | POST | 验证验证码 |
| `/api/auth/request-password-reset/` | POST | 请求密码重置 |
| `/api/auth/reset-password/` | POST | 重置密码 |

### 非遗接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/items/` | GET | 获取非遗列表 |
| `/api/items/{id}/` | GET | 获取非遗详情 |
| `/api/items/categories/` | GET | 获取类别列表 |
| `/api/items/regions/` | GET | 获取地区列表 |
| `/api/items/levels/` | GET | 获取级别列表 |
| `/api/items/search_suggestions/` | GET | 搜索建议 |
| `/api/favorites/` | GET/POST | 收藏列表/添加收藏 |

### 用户接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/profile/` | GET/PATCH | 用户资料 |
| `/api/history/` | GET | 浏览历史 |
| `/api/analytics/` | GET | 用户分析数据 |
| `/api/user/stats/` | GET | 用户统计 |

### 论坛接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/forum/posts/` | GET/POST | 帖子列表/创建帖子 |
| `/api/forum/posts/{id}/` | GET/PUT/DELETE | 帖子详情/更新/删除 |
| `/api/forum/comments/` | GET/POST | 评论列表/发表评论 |
| `/api/forum/tags/` | GET | 标签列表 |

### Agent代理接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/agent/{path}` | ALL | 代理转发到Agent服务 |
| `/api/agent-service-url/` | GET | 获取Agent服务地址 |

### 资讯政策接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/news/` | GET | 新闻列表 |
| `/api/policies/` | GET | 政策列表 |

## 数据模型

### 核心模型

#### Heritage (非遗项目)

```python
class Heritage(models.Model):
    name = models.CharField(max_length=100, unique=True)      # 项目名称
    category = models.CharField(max_length=50)                # 类别
    region = models.CharField(max_length=50)                  # 地区
    level = models.CharField(max_length=50)                   # 级别
    description = models.TextField()                          # 描述
    history = models.TextField(blank=True)                    # 历史渊源
    latitude = models.FloatField(null=True)                   # 纬度
    longitude = models.FloatField(null=True)                  # 经度
    inheritors = models.TextField(blank=True)                 # 传承人
```

#### User (用户扩展)

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='user_avatars/')
    bio = models.TextField(max_length=500)
    display_name = models.CharField(max_length=100)
```

#### ForumPost (论坛帖子)

```python
class ForumPost(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES)
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField('ForumTag')
```

## Agent服务代理

后端通过反向代理将 `/api/agent/` 路径的请求转发到Agent服务：

```python
# 请求流程
前端 → Django后端(/api/agent/*) → Agent服务(localhost:8001)

# 支持的代理功能
- 普通HTTP请求代理
- SSE流式响应代理 (进度推送)
- Session认证透传
```

### 代理配置

```bash
# .env
AGENT_SERVICE_URL=http://localhost:8001
```

## Redis缓存

### 使用场景

- 用户Session存储
- 验证码缓存
- 请求频率限制
- 热门数据缓存

### 缓存策略

```python
# 验证码缓存 (5分钟)
cache.set(f'captcha:{session_key}', code, 300)

# 频率限制 (滑动窗口)
redis_client.check_rate_limit('register', ip, 10, 60)  # 10次/分钟
```

## Celery异步任务

### 配置

```python
# heritage_project/celery.py
app = Celery('heritage_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
```

### 启动Worker

```bash
celery -A heritage_project worker -l info
celery -A heritage_project beat -l info
```

## 中间件

### IP白名单中间件

```python
# heritage_project/middleware.py
class IPWhitelistMiddleware:
    """IP访问控制中间件"""
```

## 开发指南

### 添加新的API接口

1. 在 `api/` 目录下创建视图
2. 在 `serializers/` 目录下创建序列化器
3. 在 `urls.py` 中注册路由

```python
# api/custom.py
from rest_framework.views import APIView
from rest_framework.response import Response

class CustomView(APIView):
    def get(self, request):
        return Response({'message': 'Hello'})

# urls.py
path('custom/', CustomView.as_view(), name='custom'),
```

### 添加新的数据模型

1. 在 `models.py` 或单独的模型文件中定义
2. 创建迁移文件: `python manage.py makemigrations`
3. 执行迁移: `python manage.py migrate`

## 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，禁止任何形式的使用、修改、分发或商业利用。
## 联系方式

- 项目维护者: elaine
- 邮箱: onee20589@gmail.com
- 项目链接: https://github.com/Elaine-one/shaanxi-heritage-ai-platform