# 陕西非物质文化遗产展示平台

## 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，**禁止任何形式的使用、修改、分发或商业利用**。

* 本项目代码仅供学习和参考，不得用于任何实际项目
* 未经授权，禁止复制或引用本项目的任何代码
* 所有权利保留，侵权必究

## 项目概述

本项目是一个综合性的陕西非物质文化遗产展示平台，集成了现代化的Web展示、智能旅游规划和用户互动功能。项目通过AI技术赋能传统文化，为游客提供个性化的非遗文化体验和旅游规划服务。

### 核心价值
- **文化传承**：数字化展示陕西丰富的非物质文化遗产资源
- **智能体验**：基于AI的个性化旅游路线规划和内容生成
- **用户互动**：完整的用户系统和社区交流功能
- **技术融合**：传统非遗文化与现代AI技术的深度融合

### 项目特色
- 🎯 **智能规划**：基于阿里云大模型的AI旅游路线规划
- 🎨 **多媒体展示**：图片、视频、地图等多维度非遗展示
- 🤖 **AI助手**：智能聊天机器人提供实时咨询服务
- 📱 **响应式设计**：适配PC和移动设备的现代化界面
- 📄 **智能导出**：支持PDF、JSON、CSV等多种格式导出

## 项目结构

```
.
├── Agent/              # 智能旅游规划Agent系统
│   ├── api/           # FastAPI接口层
│   │   ├── export/        # 导出功能模块（PDF、CSV、JSON）
│   │   ├── app.py         # 主应用入口
│   │   ├── session_dependencies.py  # Django Session认证模块
│   │   ├── edit_endpoints.py   # 编辑相关接口
│   │   └── weather_endpoints.py   # 天气相关接口
│   ├── agent/         # AI代理核心模块
│   │   ├── react_agent.py      # ReAct代理实现
│   │   ├── plan_editor.py      # 规划编辑器和AI交互
│   │   └── travel_planner.py   # 旅游规划核心逻辑
│   ├── config/        # 配置管理
│   │   └── settings.py         # 配置文件
│   ├── memory/        # 内存管理和会话管理
│   │   └── session.py          # 会话池和上下文管理
│   ├── models/        # AI模型集成
│   │   ├── langchain/          # LangChain模型封装
│   │   │   └── llm.py          # 大语言模型接口
│   │   └── dashscope.py        # DashScope模型
│   ├── prompts/       # AI提示词管理
│   │   └── react.py            # ReAct代理提示词模板
│   ├── services/      # 业务服务层
│   │   ├── heritage_analyzer.py   # 非遗项目分析
│   │   ├── weather.py              # 天气服务
│   │   ├── weather_config.py       # 天气配置
│   │   ├── content_integrator.py   # 内容整合
│   │   ├── pdf_generator.py        # PDF生成器
│   │   └── pdf_content_integrator.py  # PDF内容整合
│   ├── tools/         # 工具模块
│   │   ├── base.py             # 基础工具类
│   │   ├── langchain_wrappers.py  # LangChain工具封装
│   │   └── schemas.py          # 数据模式定义
│   ├── utils/         # 工具模块
│   │   ├── logger_config.py    # 日志配置
│   │   ├── font_manager.py     # 字体管理
│   │   └── content_extractor.py  # 内容提取
│   ├── font_cache/    # 字体缓存目录
│   ├── logs/          # 日志目录
│   │   ├── agent.log           # Agent日志
│   │   └── error.log           # 错误日志
│   ├── .env           # 环境变量配置
│   ├── README.md      # Agent项目文档
│   └── main.py        # 主入口文件
├── backend/           # 后端API服务（Django）
│   ├── heritage_api/  # 主要API应用
│   │   ├── admin.py               # 管理后台配置
│   │   ├── agent_views.py         # Agent相关视图
│   │   ├── auth_views.py          # 认证相关视图
│   │   ├── forum_views.py         # 论坛相关视图
│   │   ├── plan_views.py          # 规划相关视图
│   │   ├── user_views.py          # 用户相关视图
│   │   ├── models.py              # 数据模型
│   │   ├── serializers.py         # 序列化器
│   │   ├── urls.py                # URL路由
│   │   └── management/            # 管理命令
│   │       └── commands/
│   │           └── import_heritage_data.py  # 数据导入命令
│   ├── heritage_project/ # Django项目配置
│   │   ├── settings.py            # 项目设置
│   │   ├── urls.py                # 主URL路由
│   │   ├── wsgi.py                # WSGI配置
│   │   └── celery.py              # Celery配置
│   ├── media/         # 媒体文件目录
│   │   └── heritage_images/       # 非遗项目图片
│   ├── logs/          # 日志目录
│   │   └── heritage.log           # 后端日志
│   ├── .env           # 环境变量配置
│   ├── manage.py      # Django管理脚本
│   ├── complete_database_schema.md  # 完整数据库结构文档
│   └── Agent_URL_加密使用指南.md  # Agent URL加密使用说明
├── frontend/          # 前端界面
│   ├── css/           # 样式文件
│   │   ├── common/              # 通用样式
│   │   ├── pages/               # 页面特定样式
│   │   ├── news.css             # 新闻页样式
│   │   └── policy.css           # 政策页样式
│   ├── js/            # JavaScript文件
│   │   ├── agent/               # AI智能规划相关脚本
│   │   │   ├── agent-core.js    # 规划核心功能
│   │   │   └── plan-editor.js   # AI对话式规划编辑器
│   │   ├── common/              # 通用脚本
│   │   ├── pages/               # 页面特定脚本
│   │   ├── news.js              # 新闻页脚本
│   │   └── policy.js            # 政策页脚本
│   ├── lib/           # 第三方库
│   │   ├── dify_chatbot_embed.js    # AI聊天助手嵌入脚本
│   │   ├── maxkb_embed.js           # 知识库嵌入脚本
│   │   └── third-party-embed.js    # 其他第三方嵌入脚本
│   ├── pages/         # HTML页面
│   │   ├── heritage-detail.html    # 详情页
│   │   ├── heritage-map.html       # 地图页
│   │   ├── login.html              # 登录页
│   │   ├── news.html               # 新闻页
│   │   ├── non-heritage-list.html  # 列表页
│   │   ├── policy.html             # 政策页
│   │   ├── profile.html            # 个人中心
│   │   └── register.html           # 注册页
│   ├── static/        # 静态资源
│   │   └── images/                # 图片资源
│   ├── index.html     # 首页
│   └── README.md      # 前端项目文档
├── FONT_MANAGER_UPDATE.md  # 字体管理器更新说明
├── .gitignore         # Git忽略文件配置
└── README.md          # 项目说明文档
```

## 主要功能模块

### 1. 非遗文化展示系统
**核心功能**：全面展示陕西非物质文化遗产的数字化平台

**具体功能**：
- **非遗项目展示**：
  - 分类浏览：按非遗类型、地区、年代等分类展示
  - 详情页面：包含项目介绍、历史渊源、传承人信息、图片视频资料
  - 地图定位：百度地图集成，显示非遗项目的地理位置分布
  - 搜索功能：支持关键词搜索和高级筛选

- **多媒体内容管理**：
  - 图片库：高清图片展示和浏览
  - 视频资料：非遗技艺展示视频播放
  - 文档资料：相关政策法规和研究成果展示

- **新闻资讯系统**：
  - 行业动态：非遗保护最新动态
  - 政策法规：相关法律法规和政策文件
  - 活动通知：非遗相关活动信息发布

### 2. 智能旅游规划系统
**核心功能**：基于AI的个性化非遗文化旅游路线规划

**具体功能**：
- **AI路线规划**：
  - 智能推荐：根据用户偏好推荐非遗景点
  - 多日规划：支持1-30天的旅游行程规划
  - 交通方式：自驾、公共交通等多种出行方式
  - 预算控制：根据预算范围优化行程安排

- **实时信息集成**：
  - 天气信息：实时天气预报和旅游建议
  - 景点信息：开放时间、门票价格、游客评价
  - 交通信息：实时路况和交通建议

- **智能导出功能**：
  - PDF报告：生成精美的旅游计划PDF文档
  - JSON数据：结构化数据导出，便于程序处理
  - CSV表格：表格化数据，方便数据分析

### 3. 用户互动系统
**核心功能**：完整的用户管理和社区交流平台

**具体功能**：
- **用户管理**：
  - 注册登录：完整的用户注册和登录流程
  - 个人中心：用户信息管理和偏好设置
  - 权限管理：不同用户角色的权限控制

- **内容互动**：
  - 收藏功能：用户可收藏感兴趣的非遗项目
  - 浏览历史：记录用户的浏览轨迹
  - 评论系统：用户可对非遗项目进行评论交流

- **社区功能**：
  - 论坛交流：非遗文化讨论和交流平台
  - 经验分享：用户旅游经验分享
  - 问答社区：非遗相关问题的问答系统

### 4. AI智能助手系统
**核心功能**：基于大模型的智能咨询和内容生成

**具体功能**：
- **智能咨询**：
  - 实时问答：关于非遗文化的智能问答
  - 旅游建议：个性化的旅游建议和路线优化
  - 内容解释：非遗项目背景和意义的智能解释

- **内容生成**：
  - 旅游文案：自动生成旅游计划的文字描述
  - 文化介绍：生成非遗项目的详细介绍内容
  - 报告生成：智能生成各类报告和文档

### 5. 管理后台系统
**核心功能**：全面的后台管理和数据分析

**具体功能**：
- **数据管理**：
  - 非遗项目管理：增删改查非遗项目信息
  - 用户管理：用户信息管理和权限设置
  - 内容审核：用户生成内容的审核管理

- **统计分析**：
  - 访问统计：用户访问行为数据分析
  - 热门分析：热门非遗项目和旅游路线分析
  - 用户画像：用户偏好和行为特征分析

- **系统配置**：
  - 参数设置：系统运行参数配置
  - 缓存管理：Redis缓存数据管理
  - 日志管理：系统运行日志查看和分析

## 技术架构

### 后端技术栈
- **Django 5.0+**: Web框架
- **Django REST Framework**: API框架
- **MySQL**: 数据库
- **Redis**: 缓存和任务队列
- **Gunicorn**: WSGI服务器

### 前端技术栈
- **HTML5/CSS3/JavaScript**: 前端基础技术
- **百度地图API**: 地理信息服务
- **Fetch API**: 前后端通信

### Agent系统技术栈
- **FastAPI**: 高性能API框架
- **阿里云大模型**: AI智能规划
- **Pydantic**: 数据验证
- **PDF生成**: 自定义PDF报告生成

### 部署架构
- **Nginx**: 反向代理和静态文件服务
- **Gunicorn**: Django应用服务器
- **前后端分离**: 现代化部署架构

## 快速开始

### 环境要求
- Python 3.9+
- MySQL 8.0+
- Node.js (可选)
- Redis (可选)

### 安装依赖
```bash
# 安装后端Python依赖
cd backend
pip install -r requirements.txt

# 安装Agent系统依赖
cd ../Agent
pip install -r requirements.txt
```

### 数据库设置
1. 创建MySQL数据库
2. 配置 `backend/.env` 文件中的数据库连接信息
3. 运行数据库迁移：
```bash
cd backend
python manage.py migrate
```

### 启动服务
```bash
# 启动后端服务
cd backend
python manage.py runserver

# 启动Agent服务
cd Agent
python api/app.py

# 或者使用uvicorn命令启动（推荐）
cd Agent
uvicorn api.app:app --host 0.0.0.0 --port 8001 --reload

# 启动前端界面
# 直接打开 frontend/index.html
```

## 文档目录

### 项目文档
- [complete_database_schema.md](backend/complete_database_schema.md) - 包含所有36个数据库表的完整创建命令和字段说明

### 数据库结构文档

完整的数据库表结构文档位于：
- [complete_database_schema.md](backend/complete_database_schema.md) - 包含所有36个数据库表的完整创建命令和字段说明

该文档包含：
- Django系统表（10个）：auth_group, auth_user等
- Heritage API业务表（26个）：heritage_api_heritage, heritage_api_userprofile等
- 每个表的完整SQL创建命令
- 详细的字段说明表格，包括字段类型、约束和索引信息

### API文档
- [Agent_URL_加密使用指南.md](backend/Agent_URL_加密使用指南.md) - Agent系统URL加密使用说明

## 核心功能说明

### 智能旅游规划Agent
- 基于阿里云大模型的智能路线规划
- 支持多种导出格式（PDF、JSON、CSV）
- 实时天气信息集成
- 个性化推荐算法

### 非遗数据管理
- 支持多种非遗类型分类
- 图片和多媒体资源管理
- 地理位置信息集成
- 全文搜索功能

### 用户系统
- 完整的用户注册登录流程
- 用户权限管理
- 个人收藏和历史记录
- 社区论坛功能

## 开发指南

### 代码结构说明
- `backend/heritage_api/` - 主要业务逻辑
- `backend/heritage_project/` - Django项目配置
- `Agent/` - 智能规划系统
- `backend/media/` - 媒体资源存储

### 环境配置
1. 复制 `.env.example` 为 `.env` 并配置相应参数
2. 配置数据库连接信息
3. 配置百度地图API密钥
4. 配置阿里云大模型API密钥（Agent系统）

#### 环境变量详细说明

##### Django基础配置
```bash
# Django配置
DJANGO_SECRET_KEY=django-insecure-[自动生成的密钥]  # Django加密密钥，开发环境可使用默认值
DJANGO_SETTINGS_MODULE=heritage_project.settings     # Django设置模块路径，无需修改
```

##### 数据库配置
```bash
# 数据库配置
DB_NAME=heritage_db      # 数据库名称
DB_USER=root            # 数据库用户名
DB_PASSWORD=your_password  # 数据库密码（需要修改）
DB_HOST=localhost       # 数据库主机地址
DB_PORT=3306           # 数据库端口
```

##### Redis配置（可选）
```bash
# Redis配置
REDIS_HOST=127.0.0.1   # Redis服务器地址
REDIS_PORT=6379        # Redis端口
REDIS_DB=0            # Redis数据库编号
REDIS_PASSWORD=your_redis_password  # Redis密码（需要修改）
```

##### API服务配置
```bash
# 百度地图API密钥（需要申请自己的密钥）
BAIDU_MAP_AK=your_baidu_map_ak

# 域名配置（用于CORS和CSRF设置）
DOMAIN_NAME=192.168.183.232  # 根据实际部署环境修改
```

##### 邮件服务配置（用于密码重置等功能）
```bash
# 邮件服务配置
EMAIL_HOST=smtp.163.com              # SMTP服务器地址
EMAIL_PORT=465                       # SMTP端口
EMAIL_HOST_USER=your_email@163.com  # 发件人邮箱（需要修改）
EMAIL_HOST_PASSWORD=your_auth_code  # 邮箱授权码（需要修改）
DEFAULT_FROM_EMAIL=your_email@163.com  # 默认发件人邮箱
FRONTEND_URL=http://192.168.183.232  # 前端应用地址
```

##### Agent服务配置
```bash
# Agent服务URL（已加密，用于旅游规划功能）
AGENT_SERVICE_URL=encrypted_agent_service_url  # 生产环境需要配置
```

#### 安全注意事项
1. **生产环境必须修改的配置**：
   - 数据库密码（DB_PASSWORD）
   - Redis密码（REDIS_PASSWORD）
   - 邮箱配置（EMAIL_HOST_USER, EMAIL_HOST_PASSWORD）
   - 百度地图API密钥（BAIDU_MAP_AK）
   - Django SECRET_KEY（生产环境应生成新的密钥）

2. **相对安全的配置**：
   - DJANGO_SECRET_KEY：开发环境默认值以"django-insecure-"开头，安全性较低但适合开发
   - DJANGO_SETTINGS_MODULE：仅为模块路径，无安全风险

3. **API密钥申请**：
   - 百度地图API密钥：前往[百度地图开放平台](https://lbsyun.baidu.com/)申请
   - 阿里云大模型API：前往[阿里云控制台](https://www.aliyun.com/)申请

### 常用命令
```bash
# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 导入非遗数据
python manage.py import_heritage_data

# 启动开发服务器
python manage.py runserver
```

## 实际应用场景

### 1. 文化旅游规划场景
**用户画像**：计划来陕西旅游的游客

**使用流程**：
1. 浏览非遗项目，了解陕西丰富的文化资源
2. 使用智能规划工具，选择感兴趣的非遗项目
3. 设置旅游天数、预算、出行方式等参数
4. AI生成个性化旅游路线，包含详细的行程安排
5. 导出PDF旅游计划，包含地图、天气、景点介绍

**效果展示**：
- 生成包含5-7天的陕西非遗文化深度游路线
- 智能推荐最佳游览顺序和交通方式
- 提供每个非遗项目的详细背景介绍
- 集成实时天气信息，优化行程安排

### 2. 文化学习研究场景
**用户画像**：文化研究者、学生、教育工作者

**使用流程**：
1. 通过分类浏览和搜索功能查找特定非遗项目
2. 查看详细的项目介绍、历史渊源和传承人信息
3. 使用AI助手进行深度咨询和内容解释
4. 收藏感兴趣的项目，建立个人研究资料库
5. 参与社区讨论，与其他研究者交流心得

**效果展示**：
- 提供完整的非遗项目数据库和资料库
- AI智能助手提供专业的内容解释和背景分析
- 支持多媒体内容的深度学习和研究
- 建立学术交流和资源共享平台

### 3. 文化机构管理场景
**用户画像**：文化管理部门、非遗保护机构

**使用流程**：
1. 通过后台管理系统管理非遗项目数据
2. 发布最新的非遗保护政策和活动信息
3. 分析用户访问数据，了解公众关注点
4. 管理用户生成内容，维护平台内容质量
5. 通过统计报表了解平台运营状况

**效果展示**：
- 实现非遗项目的数字化管理和展示
- 提供数据驱动的决策支持
- 建立与公众的互动沟通渠道
- 提升非遗文化的传播效果和影响力

### 4. 技术实现效果
**AI智能规划效果**：
- 路线规划准确率：基于真实地理位置和交通数据
- 个性化推荐：根据用户偏好和历史行为优化推荐
- 实时信息集成：天气、交通等实时数据动态调整
- 多格式导出：满足不同用户的使用需求

**用户体验效果**：
- 响应速度：前后端分离架构确保快速响应
- 界面友好：现代化UI设计，操作简单直观
- 多设备适配：PC和移动设备均可良好使用
- 内容丰富：涵盖陕西主要非遗项目的完整信息

## 项目特色亮点

### 技术创新
- **AI+传统文化**：将现代AI技术与传统非遗文化深度融合
- **智能内容生成**：基于大模型的自动内容创作和优化
- **实时数据集成**：多源数据实时整合，提供动态服务
- **多模态展示**：文字、图片、视频、地图等多种展示方式

### 用户体验
- **个性化服务**：根据用户特征提供定制化体验
- **智能交互**：自然语言交互，降低使用门槛
- **一站式服务**：从文化了解到旅游规划的全流程服务
- **多平台支持**：Web端和移动端均可使用

### 文化价值
- **数字化保护**：实现非遗文化的数字化保存和传播
- **教育功能**：提供丰富的学习资源和教育工具
- **社区建设**：建立非遗文化爱好者的交流社区
- **产业带动**：促进文化旅游和相关产业发展