# 陕西非物质文化遗产展示平台 - 前端

## 项目概述

本项目是陕西非物质文化遗产展示平台的前端部分，采用原生 HTML、CSS 和 JavaScript 构建，提供了直观友好的用户界面，展示陕西省丰富的非物质文化遗产资源。

## 主要功能

### 核心展示功能
- **非遗项目展示**：以列表、详情和地图等多种形式展示非遗项目
- **详情页面**：展示非遗项目的详细信息、图片和相关资料
- **地图页面**：通过百度地图直观展示非遗项目的地理分布
- **多媒体展示**：支持图片轮播、视频播放等多媒体内容展示
- **统计页面**：非遗项目数据统计和可视化展示

### 用户交互功能
- **收藏功能**：支持用户收藏感兴趣的非遗项目，并在个人中心管理收藏
- **浏览历史**：记录用户浏览历史，提供个性化推荐
- **分类筛选**：按类别、级别、地区等多维度筛选非遗项目
- **搜索功能**：支持关键词搜索，快速定位感兴趣的非遗项目
- **论坛系统**：用户可以发表帖子、评论，分享非遗相关内容
- **创作功能**：用户可以发布非遗相关创作内容，支持评论、点赞、分享

### 内容管理功能
- **新闻资讯**：展示非遗相关新闻资讯，支持分类浏览和搜索
- **政策法规**：展示非遗相关政策法规，支持类型筛选和搜索
- **动态更新**：实时更新最新的非遗项目信息和相关资讯
- **创作管理**：用户创作内容的管理和展示

### AI智能功能
- **智能旅游规划**：基于AI的个性化旅游路线规划
- **AI对话助手**：智能聊天机器人提供实时咨询服务
- **对话历史管理**：完整的对话历史记录和智能摘要
- **AI创作辅助**：智能内容生成和优化建议

### 技术特性
- **响应式设计**：适配不同尺寸的设备，提供良好的移动端体验
- **用户系统**：支持用户注册、登录，管理个人收藏和浏览历史
- **智能聊天助手**：集成AI聊天功能，为用户提供非遗知识问答服务
- **性能优化**：采用懒加载、图片压缩等技术提升页面加载速度
- **模块化设计**：代码结构清晰，易于维护和扩展
- **安全性**：完整的用户认证和授权机制

## 技术栈

- **HTML5**: 页面结构
- **CSS3**: 样式和布局，包括 Flexbox 和 Grid 布局
- **JavaScript (ES6+)**: 交互逻辑和数据处理
- **百度地图 API**: 地图展示和地理信息处理
- **Fetch API**: 与后端 API 通信
- **LocalStorage**: 本地数据存储，包括用户收藏和设置
- **AI聊天组件**: 集成第三方AI聊天服务

## 项目结构

```
frontend/
├── css/                # 样式文件
│   ├── agent/               # Agent相关样式
│   │   ├── plan-editor.css     # 规划编辑器样式
│   │   └── travel-planning.css  # 旅游规划样式
│   ├── base/                # 基础样式
│   │   └── common.css          # 通用样式
│   ├── components/          # 组件样式
│   │   ├── modal.css           # 模态框样式
│   │   └── notification.css    # 通知样式
│   └── pages/               # 页面特定样式
│       ├── forum/              # 论坛相关样式
│       │   ├── forum.css          # 论坛样式
│       │   ├── forum-post.css     # 论坛帖子样式
│       │   ├── forum-post-header.css # 论坛帖子头部样式
│       │   ├── forum-post-optimized.css # 论坛帖子优化样式
│       │   └── post-detail.css    # 帖子详情样式
│       ├── heritage/           # 非遗相关样式
│       │   ├── heritage-detail.css  # 详情页样式
│       │   ├── heritage-map.css     # 地图页样式
│       │   └── heritage-map-overlay.css  # 地图覆盖层样式
│       ├── user/               # 用户相关样式
│       │   ├── creation-center.css  # 创作中心样式
│       │   ├── login.css            # 登录页样式
│       │   ├── profile.css          # 个人中心样式
│       │   └── user-creation.css    # 用户创作样式
│       ├── index.css            # 首页样式
│       ├── news.css             # 新闻页样式
│       ├── non-heritage-list.css  # 列表页样式
│       └── policy.css           # 政策页样式
├── js/                 # JavaScript 文件
│   ├── agent/             # AI智能体相关脚本
│   │   ├── agent-core.js        # 规划核心功能
│   │   ├── dialog-manager.js    # 对话管理器
│   │   ├── plan-editor.js       # AI规划编辑器
│   │   ├── progress-manager.js  # 进度管理器
│   │   ├── result-renderer.js   # 结果渲染器
│   │   ├── streaming-chat.js    # 流式聊天
│   │   └── travel-planning.js   # 旅游规划主脚本
│   ├── api/                 # API相关脚本
│   │   ├── forum-api.js         # 论坛API
│   │   ├── heritage-api.js      # 非遗API
│   │   └── user-profile-api.js  # 用户资料API
│   ├── components/        # 可复用组件
│   │   ├── avatar-cache.js      # 头像缓存组件
│   │   ├── bg-image-handler.js  # 背景图片处理
│   │   ├── heritage-ui.js       # 非遗UI工具函数
│   │   ├── login-modal.js       # 登录模态框组件
│   │   ├── modal-manager.js     # 模态框管理器
│   │   └── notification-manager.js  # 通知管理
│   ├── core/              # 核心脚本
│   │   ├── api.js               # 统一API请求封装
│   │   ├── api-utils.js         # API工具函数
│   │   ├── auth.js              # 认证相关
│   │   └── auth-redirect.js     # 认证重定向
│   ├── lib/               # 工具库
│   │   └── LunarSolarConverter.js  # 农历阳历转换
│   ├── modules/          # 模块脚本
│   │   ├── profile-favorites.js  # 个人中心收藏模块
│   │   ├── profile-history.js    # 个人中心历史模块
│   │   ├── profile-settings.js   # 个人中心设置模块
│   │   └── profile-utils.js      # 个人中心工具函数
│   ├── pages/           # 页面特定脚本
│   │   ├── forum/              # 论坛相关脚本
│   │   │   ├── forum.js           # 论坛脚本
│   │   │   ├── forum-post.js      # 论坛帖子脚本
│   │   │   └── post-detail.js     # 帖子详情脚本
│   │   ├── heritage/           # 非遗相关脚本
│   │   │   ├── heritage-detail.js # 详情页脚本
│   │   │   ├── heritage-filters.js # 筛选功能脚本
│   │   │   ├── heritage-map.js    # 地图页脚本
│   │   │   ├── heritage-map-sidebar.js # 地图侧边栏脚本
│   │   │   └── heritage-map-toolbar.js # 地图工具栏脚本
│   │   ├── user/               # 用户相关脚本
│   │   │   ├── creation-center.js # 创作中心脚本
│   │   │   ├── forgot-password.js # 忘记密码脚本
│   │   │   ├── login.js           # 登录脚本
│   │   │   ├── profile.js         # 个人中心脚本
│   │   │   ├── register.js        # 注册脚本
│   │   │   ├── reset-password.js  # 密码重置脚本
│   │   │   └── user-creation.js   # 用户创作脚本
│   │   ├── index.js             # 首页脚本
│   │   ├── news.js              # 新闻页脚本
│   │   ├── non-heritage-list.js # 列表页脚本
│   │   └── policy.js            # 政策页脚本
│   └── utils/            # 工具函数
│       ├── date-utils.js        # 日期时间工具
│       └── utils.js             # 通用工具函数
├── lib/                # 第三方库
│   ├── dify_chatbot_embed.js  # AI聊天助手嵌入脚本
│   ├── maxkb_embed.js         # 知识库嵌入脚本
│   └── third-party-embed.js   # 其他第三方嵌入脚本
├── pages/              # HTML 页面
│   ├── creation-center.html    # 创作中心
│   ├── forgot-password.html    # 忘记密码
│   ├── forum.html              # 论坛首页
│   ├── forum-post.html         # 论坛帖子
│   ├── heritage-detail.html    # 详情页
│   ├── heritage-map.html       # 地图页
│   ├── login.html              # 登录页
│   ├── news.html               # 新闻页
│   ├── non-heritage-list.html  # 列表页
│   ├── policy.html             # 政策页
│   ├── post-detail.html        # 帖子详情
│   ├── profile.html            # 个人中心
│   ├── register.html           # 注册页
│   ├── reset-password.html     # 密码重置
│   └── user-creation.html      # 用户创作
├── index.html          # 首页
└── README.md           # 前端项目文档
```

## 页面说明

### 非遗列表页 (non-heritage-list.html)

展示所有非遗项目的列表，支持分类筛选和搜索。

- **筛选功能**: 按类别、级别、地区筛选
- **搜索功能**: 关键词搜索
- **分页功能**: 分页显示项目列表
- **收藏功能**: 用户可以收藏感兴趣的项目

### 非遗详情页 (heritage-detail.html)

展示单个非遗项目的详细信息。

- **基本信息**: 名称、类别、级别、地区等
- **详细描述**: 历史渊源、特征、价值等
- **图片展示**: 项目相关图片，支持轮播和放大
- **地理位置**: 显示项目所在地理位置
- **收藏功能**: 用户可以收藏/取消收藏项目
- **聊天咨询**: 可通过AI助手了解更多相关信息

### 地图页 (heritage-map.html)

在地图上展示非遗项目的地理分布。

- **地图标记**: 在地图上标记非遗项目位置
- **侧边栏列表**: 显示项目列表，支持筛选
- **信息窗口**: 点击标记显示项目简介
- **收藏功能**: 用户可以直接在地图上收藏项目

### 新闻资讯页 (news.html)

展示非遗相关新闻资讯。

- **新闻列表**: 展示最新的非遗相关新闻
- **分类筛选**: 按新闻类型和来源筛选
- **搜索功能**: 支持关键词搜索新闻
- **详情查看**: 点击查看新闻详细内容
- **分页加载**: 支持分页和无限滚动加载

### 政策法规页 (policy.html)

展示非遗相关政策法规。

- **政策列表**: 展示相关政策法规文件
- **类型筛选**: 按政策类型（法律法规、部门规章等）筛选
- **机构筛选**: 按发布机构筛选
- **搜索功能**: 支持关键词搜索政策
- **详情查看**: 查看政策详细内容和附件
- **时间排序**: 按发布时间或生效时间排序

### 个人中心 (profile.html)

用户个人信息和收藏管理。

- **用户信息**: 显示用户基本信息
- **收藏列表**: 管理用户收藏的非遗项目
- **浏览历史**: 查看用户浏览历史记录
- **收藏操作**: 支持批量取消收藏、排序等
- **导出功能**: 可将收藏导出为旅游计划
- **聊天历史**: 查看与AI助手的历史对话

## 收藏功能实现

收藏功能是本平台的核心功能之一，实现了以下特性：

- **多页面支持**: 在列表页、详情页、地图页和个人中心均可操作收藏
- **状态同步**: 用户在任一页面的收藏操作会同步到其他页面
- **本地存储**: 使用 localStorage 临时存储收藏数据，提高用户体验
- **后端同步**: 登录用户的收藏会同步到后端数据库
- **视觉反馈**: 收藏按钮状态变化提供直观的视觉反馈

### 收藏功能相关文件

- **js/api/heritage-api.js**: 封装了收藏相关的 API 调用
  - `addFavorite(heritageId)`: 添加收藏（POST `/favorites/add/`）
  - `removeFavorite(heritageId)`: 移除收藏（POST `/favorites/remove/`）
  - `checkFavoriteStatus(heritageId)`: 检查收藏状态（GET `/favorites/check/`）
  - `getUserFavorites(sort)`: 获取用户收藏列表（GET `/favorites/`）
  - `heritageEvents`: 收藏状态事件总线

- **js/pages/heritage/heritage-detail.js**: 详情页收藏功能
  - 集成收藏API，支持添加/移除收藏
  - 实时更新收藏按钮状态
  - 显示收藏状态视觉反馈

- **js/pages/heritage/heritage-map-sidebar.js**: 地图页收藏功能
  - 地图标记点的收藏操作
  - 侧边栏列表的收藏状态同步
  - 本地存储与后端数据同步

- **js/pages/user/profile.js**: 个人中心收藏管理
  - 展示用户收藏列表
  - 支持批量取消收藏
  - 支持按时间/名称排序

- **js/modules/profile-favorites.js**: 个人中心收藏功能模块
  - 提供收藏列表的管理和操作功能

## 聊天助手功能

聊天助手功能通过集成第三方AI服务，为用户提供非遗知识问答服务。

### 聊天助手相关文件

- **lib/dify_chatbot_embed.js**: AI聊天助手嵌入脚本
- **lib/maxkb_embed.js**: 知识库嵌入脚本
- **lib/third-party-embed.js**: 其他第三方嵌入脚本

### 使用方法

在HTML页面中引入聊天助手脚本：

```html
<!-- 在页面底部引入聊天助手脚本 -->
<script src="../lib/dify_chatbot_embed.js"></script>
<script src="../lib/maxkb_embed.js"></script>
```

## 验证码功能

注册页面使用图形验证码进行人机验证，防止恶意注册。

- **后端**: `/api/auth/captcha/generate/` - 生成验证码
- **后端**: `/api/auth/captcha/verify/` - 验证验证码
- **前端**: `js/pages/user/register.js` - 验证码显示和刷新

## 通知系统

全局通知系统用于显示操作结果、错误提示等信息。

- **js/components/notification-manager.js**: 通知管理器
- **css/components/notification.css**: 通知样式

使用方式：`NotificationManager.success('操作成功！')` / `error()` / `warning()` / `info()`

## 模态框系统

统一模态框管理，支持确认框、提示框等。

- **js/components/modal-manager.js**: 模态框管理器
- **css/components/modal.css**: 模态框样式
- **js/components/login-modal.js**: 登录模态框组件

使用方式：`ModalManager.confirm('确定吗？')` / `alert('提示')` / `showLoginModal()`

## 流式聊天

支持SSE流式响应，用于AI对话场景。

- **js/agent/streaming-chat.js**: `StreamingChatManager` 类
- **js/agent/progress-manager.js**: 进度管理器
- **js/agent/result-renderer.js**: 结果渲染器

## Agent智能规划

AI旅游规划Agent，支持SSE流式进度推送。

- **js/agent/agent-core.js**: 规划核心功能
- **js/agent/dialog-manager.js**: 对话管理器
- **js/agent/plan-editor.js**: 规划编辑器
- **js/agent/travel-planning.js**: 旅游规划主入口（自动初始化为 `window.travelAgent`）

## 如何运行

### 本地开发

本地开发需要同时启动后端服务器和前端服务器。

#### 1. 启动后端服务器

```bash
# 进入后端目录
cd backend

# 激活虚拟环境（如果使用）
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 启动 Django 开发服务器
python manage.py runserver
```

后端服务器将在 `http://127.0.0.1:8000` 运行。

#### 2. 启动前端服务器

**方式一：使用 Python HTTP 服务器**
```bash
# 在项目根目录运行
python -m http.server 8080
```

**方式二：使用 VS Code 的 Live Server 插件**
- 安装 Live Server 插件
- 右键点击 `index.html`，选择 "Open with Live Server"

#### 3. 配置 CORS（仅开发环境）

如果前端和后端不在同一端口，需要在后端配置 CORS。后端已安装 `django-cors-headers`，确保在 `backend/heritage_project/settings.py` 中配置：

```python
CORS_ALLOW_ALL_ORIGINS = True  # 仅开发环境使用
```

#### 4. 访问应用

- 前端页面: http://localhost:8080
- 后端 API:  http://127.0.0.1:8000/api/
- 管理后台:  http://127.0.0.1:8000/admin/

### 生产环境部署（推荐）

生产环境推荐使用 Nginx 作为前端服务器，代理后端 API 请求。

#### 1. 安装 Nginx

**Windows:**
- 下载 nginx for Windows: http://nginx.org/en/download.html
- 解压到指定目录（例如：C:\nginx）
- 将 C:\nginx 添加到系统 PATH 环境变量

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx

# macOS
brew install nginx
```

#### 2. 启动服务

**Windows:**
```bash
# 在项目根目录运行
start_nginx.bat
```

**Linux/Mac:**
```bash
# 在项目根目录运行
chmod +x start_nginx.sh
./start_nginx.sh
```

#### 3. 访问应用

启动成功后，访问以下地址：
- 前端页面: http://localhost
- 后端 API:  http://localhost/api/
- 管理后台:  http://localhost/admin/

#### 4. 管理命令

**Windows:**
- 停止服务: `stop_nginx.bat`
- 重启服务: `restart_nginx.bat`

**Linux/Mac:**
- 停止服务: `./stop_nginx.sh`
- 重启服务: `./restart_nginx.sh`

#### 5. 配置说明

Nginx 配置文件位于项目根目录的 `nginx.conf`，主要配置包括：
- 前端静态文件服务（`/`）
- 后端 API 代理（`/api/`）
- Agent 服务代理（`/api/agent/`）
- 管理后台代理（`/admin/`）
- 静态文件代理（`/static/`）
- 媒体文件代理（`/media/`）

详细配置说明请查看 `nginx.conf` 文件中的注释。

#### 6. HTTPS 配置（生产环境）

生产环境建议启用 HTTPS，配置方法请参考 `nginx.conf` 文件中的 HTTPS 配置示例。

## API 调用

前端通过 Fetch API 与后端通信，API请求封装在以下文件中：

- **js/core/api.js**: 统一API请求封装，自动注入CSRF Token
- **js/api/heritage-api.js**: 非遗相关API（列表、详情、收藏等）
- **js/api/forum-api.js**: 论坛相关API（帖子、评论、点赞、关注等）
- **js/api/user-profile-api.js**: 用户资料API（头像、资料更新等）

### 主要API模块

```javascript
// 非遗API
heritageAPI.getAllItems(params)    // 获取非遗列表
heritageAPI.getItemDetail(id)      // 获取非遗详情
addFavorite(id) / removeFavorite(id)  // 收藏操作

// 论坛API
forumAPI.getPosts(params)          // 获取帖子列表
forumAPI.createPost(data)          // 创建帖子
forumAPI.togglePostLike(id)        // 点赞帖子

// 用户API
API.userProfile.getUserProfile()   // 获取用户资料
API.userProfile.uploadUserAvatar(file)  // 上传头像
```

## 日期时间工具

`js/utils/date-utils.js` 提供日期时间处理功能：

- `dateUtils.getFormattedDateTime()` - 格式化日期时间
- `dateUtils.getLunarDate()` - 获取农历日期
- `dateUtils.getSolarTerm()` - 获取节气
- `dateUtils.getFullDateTimeInfo()` - 获取完整日期信息

## 开发指南

### 添加新页面

1. 在 `pages/` 目录下创建新的 HTML 文件
2. 在 `css/pages/` 目录下创建对应的 CSS 文件
3. 在 `js/pages/` 目录下创建对应的 JavaScript 文件
4. 在 HTML 文件中引入必要的 CSS 和 JavaScript 文件


### 添加聊天助手到新页面

1. 在HTML页面底部引入聊天助手脚本
   ```html
   <script src="../lib/dify_chatbot_embed.js"></script>
   ```
2. 根据需要配置聊天助手参数

## 最新更新记录

### v1.3.0 (2026-03-11)

#### 全面UI更新
- 🎨 论坛页面UI全面优化，提升视觉体验和交互流畅度
- 🎨 创作者中心UI/UX全面升级，采用现代化设计语言
- 🎨 新闻页面UI优化，改善信息展示和阅读体验
- 🎨 政策页面UI优化，提升内容可读性
- 🎨 遗产详情页面UI优化，增强视觉吸引力
- 🎨 非遗产列表页面UI优化，改善浏览体验
- 🎨 遗产地图页面UI优化，提升交互体验
- 🎨 个人中心页面UI优化，完善用户信息展示
- 🎨 新增渐变色彩系统和视觉层次优化
- 🎨 优化卡片布局、间距和阴影效果
- 🎨 添加流畅的交互动画和过渡效果
- 🎨 完善响应式设计，适配多种屏幕尺寸
- 🎨 统一页面风格和交互体验
- 🎨 优化表单和按钮样式
- 🎨 新增通用CSS组件库
- 🎨 新增高级图片查看器
- 🎨 新增头像缓存管理
- 🎨 新增图片增强功能
- 🎨 新增帖子编辑器组件
- 🎨 新增遗产地图工具栏组件

### v1.2.5 (2026-03-01)

#### 架构优化
- 🏗️ 重构Agent交互模块，采用类封装设计模式
- 🏗️ 优化模块化架构，分离agent/common/pages/modules目录
- 🏗️ 统一API请求封装，自动注入CSRF Token

#### 功能增强
- 🆕 完善SSE流式进度监控机制
- 🆕 新增ProgressManager进度管理器
- 🆕 新增ResultRenderer结果渲染器
- 🆕 新增DialogManager对话管理器
- 🆕 优化PlanEditor规划编辑器交互

#### 技术改进
- 📈 改进EventSource错误处理与重连机制
- 📈 优化内存管理，防止组件销毁时内存泄漏
- 📈 增强请求防抖与状态保护
- 📈 完善日志输出，便于调试

### v1.2.0 (2025-10-21)

#### Bug修复
- ✅ 修复了logo.png文件路径问题
- ✅ 修复了forum-post.html页面中静态资源引用路径错误
- ✅ 优化了静态文件的组织结构

#### 功能增强
- 🆕 新增论坛系统前端页面
- 🆕 增强了收藏功能的用户体验
- 🆕 优化了地图页面的交互逻辑
- 🆕 改进了搜索功能的响应速度

#### 技术改进
- 📈 优化了静态资源加载性能
- 📈 改进了移动端适配效果
- 📈 增强了代码的可维护性
- 📈 完善了错误处理机制

## 重要说明

- 本项目使用原生 JavaScript，不依赖任何前端框架
- 收藏功能需要用户登录才能完全使用，未登录用户的收藏仅保存在本地
- 地图功能需要百度地图 API 密钥，请在 `heritage-map.js` 中配置
- 确保后端 API 服务器已启动并正确配置跨域访问
- 聊天助手功能需要配置相应的AI服务接口

## 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，**禁止任何形式的使用、修改、分发或商业利用**。

* 本项目代码仅供学习和参考，不得用于任何实际项目
* 未经授权，禁止复制或引用本项目的任何代码
* 所有权利保留，侵权必究

## 联系方式

- 项目维护者: elaine
- 邮箱: onee20589@gmail.com
- 项目链接: https://github.com/Elaine-one/shaanxi-heritage-ai-platform