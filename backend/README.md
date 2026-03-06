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
| `/api/auth/register/` | POST | 用户注册（邮箱注册） |
| `/api/auth/login/` | POST | 用户登录（邮箱登录） |
| `/api/auth/logout/` | POST | 用户登出 |
| `/api/auth/user/` | GET | 获取当前用户信息 |
| `/api/auth/csrf/` | GET | 获取CSRF Token |
| `/api/auth/captcha/generate/` | GET | 生成图形验证码 |
| `/api/auth/captcha/verify/` | POST | 验证验证码 |
| `/api/auth/request-password-reset/` | POST | 请求密码重置（发送邮件） |
| `/api/auth/reset-password/` | POST | 重置密码 |
| `/api/auth/security-status/` | GET | 获取安全状态 |

### 非遗接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/items/` | GET | 获取非遗列表（支持分页、筛选、搜索） |
| `/api/items/{id}/` | GET | 获取非遗详情 |
| `/api/items/categories/` | GET | 获取所有类别列表 |
| `/api/items/regions/` | GET | 获取所有地区列表 |
| `/api/items/levels/` | GET | 获取所有级别列表 |

### 收藏接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/favorites/` | GET | 获取用户收藏列表（支持排序） |
| `/api/favorites/add/` | POST | 添加收藏（body: `heritage_id`） |
| `/api/favorites/remove/` | POST | 移除收藏（body: `heritage_id`） |
| `/api/favorites/check/` | GET | 检查收藏状态（参数: `heritage_id`） |

### 浏览历史接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/history/` | GET | 获取浏览历史列表 |
| `/api/history/add/` | POST | 添加浏览记录（body: `heritage_id`） |
| `/api/history/clear/` | DELETE | 清除所有浏览历史 |
| `/api/history/remove/` | DELETE | 删除特定浏览记录（body: `heritage_id`） |

### 用户接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/profile/` | GET/PATCH | 用户资料（GET获取，PATCH更新） |
| `/api/profile/me/` | GET | 获取当前用户详细信息（含头像） |
| `/api/profile/update_profile/` | PUT/PATCH | 更新用户资料 |
| `/api/profile/upload-avatar/` | POST | 上传用户头像 |
| `/api/profile/clear-avatar/` | POST | 清除用户头像 |
| `/api/analytics/` | GET | 获取用户创作分析数据 |
| `/api/export-data/` | POST | 导出用户数据（ZIP格式） |
| `/api/delete-account/` | POST | 删除用户账户 |
| `/api/clear-avatar/` | POST | 清除头像（备用接口） |
| `/api/user/stats/` | GET | 获取用户统计数据 |

### 资讯政策接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/news/` | GET | 新闻列表（支持搜索、标签筛选） |
| `/api/news/{id}/` | GET | 新闻详情（自动增加浏览量） |
| `/api/news/sources/` | GET | 获取所有新闻来源 |
| `/api/news/search_suggestions/` | GET | 获取搜索建议 |
| `/api/news/tags/` | GET | 获取所有新闻标签 |
| `/api/policies/` | GET | 政策列表（支持搜索、类型筛选） |
| `/api/policies/{id}/` | GET | 政策详情（自动增加浏览量） |
| `/api/policies/types/` | GET | 获取所有政策类型 |
| `/api/policies/authorities/` | GET | 获取所有发布机构 |
| `/api/policies/search_suggestions/` | GET | 获取搜索建议 |

### 创作中心接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/creations/` | GET/POST | 创作列表/创建创作 |
| `/api/creations/{id}/` | GET/PUT/DELETE | 创作详情/更新/删除 |
| `/api/creation-likes/` | GET/POST | 点赞列表/点赞创作 |
| `/api/creation-comments/` | GET/POST | 评论列表/发表评论 |
| `/api/creation-history/` | GET | 创作浏览历史 |
| `/api/creation-favorites/` | GET/POST | 创作收藏列表/收藏创作 |

### 论坛接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/forum/` | GET | 论坛API根视图（列出所有端点） |
| `/api/forum/posts/` | GET/POST | 帖子列表/创建帖子 |
| `/api/forum/posts/{id}/` | GET/PUT/DELETE | 帖子详情/更新/删除 |
| `/api/forum/posts/{id}/like/` | POST | 切换帖子点赞状态 |
| `/api/forum/posts/{id}/favorite/` | POST | 切换帖子收藏状态 |
| `/api/forum/posts/{id}/pin/` | POST | 切换帖子置顶状态（管理员） |
| `/api/forum/posts/{id}/feature/` | POST | 切换帖子精华状态（管理员） |
| `/api/forum/posts/{id}/report/` | POST | 举报帖子 |
| `/api/forum/posts/{id}/view/` | POST | 增加帖子浏览量 |
| `/api/forum/posts/{post_id}/comments/` | GET/POST | 评论列表/发表评论 |
| `/api/forum/comments/{id}/like/` | POST | 切换评论点赞状态 |
| `/api/forum/comments/{id}/report/` | POST | 举报评论 |
| `/api/forum/comments/{id}/delete/` | DELETE | 删除评论 |
| `/api/forum/tags/` | GET | 标签列表 |
| `/api/forum/users/{id}/follow/` | POST | 切换用户关注状态 |
| `/api/forum/users/{id}/follow-status/` | GET | 检查用户关注状态 |
| `/api/forum/users/{id}/posts/` | GET | 获取用户帖子列表 |
| `/api/forum/users/search/` | GET | 搜索用户 |
| `/api/forum/users/active/` | GET | 获取活跃用户列表 |
| `/api/forum/users/stats/` | GET | 获取用户统计排行榜 |
| `/api/forum/my/favorites/` | GET | 我的收藏帖子 |
| `/api/forum/my/notifications/` | GET | 我的通知 |
| `/api/forum/my/following/` | GET | 我的关注列表 |
| `/api/forum/my/followers/` | GET | 我的粉丝列表 |
| `/api/forum/upload/image/` | POST | 上传图片 |

### Agent代理接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/agent/{path}` | ALL | 代理转发到Agent服务（支持SSE流式响应） |
| `/api/agent-service-url/` | GET | 获取Agent服务地址 |

### 地图配置接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/map/config/` | GET | 获取百度地图API配置 |

### 旅游规划接口

| 接口 | 方法 | 描述 |
|-----|------|------|
| `/api/travel-plan/export/` | GET | 导出旅游规划 |

## 数据模型

### 核心模型

#### Heritage (非遗项目)

```python
class Heritage(models.Model):
    name = models.CharField(max_length=100, unique=True)           # 项目名称
    pinyin_name = models.CharField(max_length=200, blank=True)     # 拼音名称
    category = models.CharField(max_length=50)                     # 类别
    region = models.CharField(max_length=50)                       # 地区
    level = models.CharField(max_length=50, default='未知级别')    # 级别
    batch = models.CharField(max_length=50, blank=True)            # 批次
    description = models.TextField()                               # 描述
    history = models.TextField(blank=True)                         # 历史渊源
    features = models.TextField(blank=True)                        # 基本内容/特征
    value = models.TextField(blank=True)                           # 重要价值
    status = models.TextField(blank=True)                          # 存续状况
    protection_measures = models.TextField(blank=True)             # 保护措施
    inheritors = models.TextField(blank=True)                      # 传承人
    related_works = models.TextField(blank=True)                   # 相关制品
    latitude = models.FloatField(null=True)                        # 纬度
    longitude = models.FloatField(null=True)                       # 经度
    main_image_url = models.URLField(max_length=500, blank=True)   # 主图片URL
    gallery_image_urls = models.JSONField(default=list)            # 图库图片URL列表
```

#### UserFavorite (用户收藏)

```python
class UserFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)       # 用户
    heritage = models.ForeignKey(Heritage, on_delete=models.CASCADE)  # 非遗项目
    created_at = models.DateTimeField(auto_now_add=True)           # 收藏时间
    
    class Meta:
        unique_together = ('user', 'heritage')  # 每个用户对每个项目只能收藏一次
```

#### UserHistory (浏览历史)

```python
class UserHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)       # 用户
    heritage = models.ForeignKey(Heritage, on_delete=models.CASCADE)  # 非遗项目
    visit_time = models.DateTimeField(auto_now_add=True)           # 浏览时间
    
    class Meta:
        unique_together = ('user', 'heritage')
```

#### News (新闻资讯)

```python
class News(models.Model):
    title = models.CharField(max_length=200)                       # 标题
    summary = models.TextField(max_length=500, blank=True)         # 摘要
    content = models.TextField()                                   # 内容
    author = models.CharField(max_length=100, blank=True)          # 作者
    source = models.CharField(max_length=200, blank=True)          # 来源
    source_url = models.URLField(max_length=500, blank=True)       # 来源链接
    image_url = models.URLField(max_length=500, blank=True)        # 配图链接
    publish_date = models.DateTimeField()                          # 发布时间
    view_count = models.PositiveIntegerField(default=0)            # 浏览次数
    tags = models.CharField(max_length=200, blank=True)            # 标签（逗号分隔）
    is_active = models.BooleanField(default=True)                  # 是否启用
```

#### Policy (政策法规)

```python
class Policy(models.Model):
    POLICY_TYPE_CHOICES = [
        ('law', '法律法规'),
        ('regulation', '部门规章'),
        ('notice', '通知公告'),
        ('standard', '标准规范'),
        ('guidance', '指导意见'),
        ('plan', '规划计划'),
        ('other', '其他'),
    ]
    
    title = models.CharField(max_length=200)                       # 标题
    summary = models.TextField(max_length=500, blank=True)         # 摘要
    content = models.TextField()                                   # 内容
    policy_number = models.CharField(max_length=100, blank=True)   # 政策编号
    issuing_authority = models.CharField(max_length=100)           # 发布机构
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)  # 政策类型
    publish_date = models.DateField()                              # 发布日期
    effective_date = models.DateField(blank=True, null=True)       # 生效日期
    source_url = models.URLField(max_length=500, blank=True)       # 来源链接
    attachment_url = models.URLField(max_length=500, blank=True)   # 附件链接
    tags = models.CharField(max_length=200, blank=True)            # 标签
    view_count = models.PositiveIntegerField(default=0)            # 浏览量
    is_active = models.BooleanField(default=True)                  # 是否激活
```

### 用户模型

#### UserProfile (用户资料)

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='user_avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    display_name = models.CharField(max_length=100, blank=True)
    
    # 信号：创建User时自动创建关联的UserProfile
```

### 创作中心模型

#### UserCreation (用户创作)

```python
class UserCreation(models.Model):
    CREATION_TYPE_CHOICES = [
        ('video', '视频创作'),
        ('photo', '图片创作'),
        ('article', '文章创作'),
        ('music', '音乐创作'),
    ]
    
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('reviewing', '审核中'),
        ('rejected', '已拒绝'),
        ('archived', '已归档'),
    ]
    
    title = models.CharField(max_length=100)                        # 创作标题
    description = models.TextField()                                # 创作描述
    type = models.CharField(max_length=20, choices=CREATION_TYPE_CHOICES)  # 创作类型
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')  # 状态
    media_file = models.FileField(upload_to='user_creations/%Y/%m/%d/', blank=True)  # 媒体文件
    thumbnail = models.ImageField(upload_to='creation_thumbnails/%Y/%m/%d/', blank=True)  # 缩略图
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creations')  # 作者
    heritage = models.ForeignKey(Heritage, on_delete=models.SET_NULL, blank=True, null=True)  # 关联非遗项目
    view_count = models.PositiveIntegerField(default=0)             # 浏览数
    like_count = models.PositiveIntegerField(default=0)             # 点赞数
    comment_count = models.PositiveIntegerField(default=0)          # 评论数
    share_count = models.PositiveIntegerField(default=0)            # 分享数
    tags = models.JSONField(default=list, blank=True)               # 标签
    is_featured = models.BooleanField(default=False)                # 是否精选
    is_public = models.BooleanField(default=True)                   # 是否公开
    published_at = models.DateTimeField(blank=True, null=True)      # 发布时间
```

#### CreationLike (创作点赞)

```python
class CreationLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creation_likes')
    creation = models.ForeignKey(UserCreation, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'creation')
```

#### CreationComment (创作评论)

```python
class CreationComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creation_comments')
    creation = models.ForeignKey(UserCreation, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    content = models.TextField()
    is_active = models.BooleanField(default=True)
    like_count = models.PositiveIntegerField(default=0)
```

#### CreationFavorite (创作收藏)

```python
class CreationFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creation_favorites')
    creation = models.ForeignKey(UserCreation, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'creation')
```

### 论坛模型

#### ForumPost (论坛帖子)

```python
class ForumPost(models.Model):
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('hidden', '已隐藏'),
        ('deleted', '已删除'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')
    is_pinned = models.BooleanField(default=False)                  # 是否置顶
    is_featured = models.BooleanField(default=False)                # 是否精华
    is_locked = models.BooleanField(default=False)                  # 是否锁定
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    favorite_count = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField('ForumTag', blank=True, related_name='posts')
    last_reply_at = models.DateTimeField(null=True, blank=True)
```

#### ForumComment (论坛评论)

```python
class ForumComment(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_comments')
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    like_count = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
```

#### ForumTag (论坛标签)

```python
class ForumTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')
    post_count = models.PositiveIntegerField(default=0)
```

#### ForumPostLike (帖子点赞)

```python
class ForumPostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
```

#### ForumPostFavorite (帖子收藏)

```python
class ForumPostFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_favorites')
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'post')
```

#### ForumUserFollow (用户关注)

```python
class ForumUserFollow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
```

#### ForumUserStats (用户统计)

```python
class ForumUserStats(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='forum_stats')
    post_count = models.PositiveIntegerField(default=0)             # 帖子数
    comment_count = models.PositiveIntegerField(default=0)          # 评论数
    like_received = models.PositiveIntegerField(default=0)          # 收到的点赞数
    followers_count = models.PositiveIntegerField(default=0)        # 粉丝数
    following_count = models.PositiveIntegerField(default=0)        # 关注数
    experience = models.PositiveIntegerField(default=0)             # 经验值
    last_active_at = models.DateTimeField(null=True, blank=True)    # 最后活跃时间
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

## Redis缓存

Redis工具类封装在 `heritage_api/redis_utils.py` 中，提供以下功能：

- **验证码缓存**: `set_captcha()`, `get_captcha()`, `delete_captcha()`
- **频率限制**: `check_rate_limit(endpoint, ip, max_requests, window)`
- **登录安全**: `incr_login_attempts()`, `is_login_locked()`, `reset_login_attempts()`
- **浏览量统计**: `incr_view_count()`, `get_view_count()`, `get_all_view_counts()`

## Celery异步任务

```bash
celery -A heritage_project worker -l info
celery -A heritage_project beat -l info
```

## 中间件

### IP白名单中间件

限制管理后台访问权限，默认只允许 `127.0.0.1` 和 `localhost` 访问 `/admin/`。

配置方式：在 `settings.py` 的 `MIDDLEWARE` 中添加 `'heritage_project.middleware.IPWhitelistMiddleware'`。

## 开发指南

### 添加新的API接口

1. 在 `api/` 目录下创建视图
2. 在 `serializers/` 目录下创建序列化器
3. 在 `urls.py` 中注册路由

### 添加新的数据模型

1. 在 `models.py` 或单独的模型文件中定义
2. 创建迁移文件: `python manage.py makemigrations`
3. 执行迁移: `python manage.py migrate`

## 版本更新日志

### v1.2.0 (2026-03-04)

#### 数据库优化
- **清理废弃表**: 删除 5 个未使用的数据库表
  - `HeritageImage` - 非遗图片表（Heritage模型已用JSON字段存储图片）
  - `CreationTag` - 创作标签表（UserCreation已用JSON字段存储标签）
  - `CreationShare` - 创作分享表（API中未使用）
  - `CreationReport` - 创作举报表（API中未使用）
  - `ForumAnnouncement` - 论坛公告表（未在URL中注册）


#### API文档优化
- **中文化API文档**: 更新所有ViewSet的docstring为中文
  - 非遗相关接口
  - 用户相关接口
  - 认证相关接口
  - 论坛相关接口
  - 资讯政策接口

### v1.1.0 (2025-12-XX)

#### 初始版本
- 完成基础功能开发
- 用户认证系统
- 非遗数据管理
- 论坛系统
- Agent服务代理

## 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，禁止任何形式的使用、修改、分发或商业利用。
## 联系方式

- 项目维护者: elaine
- 邮箱: onee20589@gmail.com
- 项目链接: https://github.com/Elaine-one/shaanxi-heritage-ai-platform