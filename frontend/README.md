# 陕西非物质文化遗产展示平台 - 前端

<p align="center">
  <img src="https://raw.githubusercontent.com/Elaine-one/shaanxi-heritage-ai-platform/main/docs/frontend-banner.png" alt="陕西非遗展示平台" width="100%"/>
</p>

<div align="center">

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat&logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-red.svg)

</div>

---

## 项目概述

本项目是陕西非物质文化遗产展示平台的前端部分，采用原生 HTML、CSS 和 JavaScript 构建，提供了直观友好的用户界面，展示陕西省丰富的非物质文化遗产资源。

### 主要功能

#### 核心展示功能

- **非遗项目展示**: 以列表、详情和地图等多种形式展示非遗项目
- **详情页面**: 展示非遗项目的详细信息、图片和相关资料
- **地图页面**: 通过百度地图直观展示非遗项目的地理分布
- **多媒体展示**: 支持图片轮播、视频播放等多媒体内容展示
- **统计页面**: 非遗项目数据统计和可视化展示

#### 用户交互功能

- **收藏功能**: 支持用户收藏感兴趣的非遗项目，并在个人中心管理收藏
- **浏览历史**: 记录用户浏览历史，提供个性化推荐
- **分类筛选**: 按类别、级别、地区等多维度筛选非遗项目
- **搜索功能**: 支持关键词搜索，快速定位感兴趣的非遗项目
- **论坛系统**: 用户可以发表帖子、评论，分享非遗相关内容
- **创作功能**: 用户可以发布非遗相关创作内容，支持评论、点赞、分享

#### 内容管理功能

- **新闻资讯**: 展示非遗相关新闻资讯，支持分类浏览和搜索
- **政策法规**: 展示非遗相关政策法规，支持类型筛选和搜索
- **动态更新**: 实时更新最新的非遗项目信息和相关资讯
- **创作管理**: 用户创作内容的管理和展示

#### AI 智能功能

- **智能旅游规划**: 基于 AI 的个性化旅游路线规划
- **AI 对话助手**: 原生实现的 AI 聊天机器人，通过 SSE 流式返回响应
- **对话历史管理**: 完整的对话历史记录和智能摘要
- **AI 创作辅助**: 智能内容生成和优化建议

#### 技术特性

- **响应式设计**: 适配不同尺寸的设备，提供良好的移动端体验
- **用户系统**: 支持用户注册、登录，管理个人收藏和浏览历史
- **AI 对话助手**: 原生实现的 AI 聊天助手，通过 SSE 流式返回响应
- **性能优化**: 采用懒加载、图片压缩等技术提升页面加载速度
- **模块化设计**: 代码结构清晰，易于维护和扩展
- **安全性**: 完整的用户认证和授权机制

### 技术栈

| 类别 | 技术 |
|:---|:---|
| **页面结构** | HTML5 |
| **样式和布局** | CSS3 (Flexbox, Grid) |
| **交互逻辑** | JavaScript (ES6+) |
| **地图服务** | 百度地图 API |
| **HTTP 客户端** | Fetch API + SSE |
| **本地存储** | LocalStorage |
| **AI 对话** | 原生实现 + SSE 流式响应 |

---

## 项目结构

```
frontend/
├── css/
│   ├── agent/
│   │   ├── plan-editor.css
│   │   └── travel-planning.css
│   ├── base/
│   │   └── common.css
│   ├── components/
│   │   ├── advanced-lightbox.css
│   │   ├── modal.css
│   │   ├── notification.css
│   │   └── post-editor.css
│   └── pages/
│       ├── forum/
│       │   ├── forum.css
│       │   ├── forum-post.css
│       │   ├── forum-post-header.css
│       │   ├── forum-post-optimized.css
│       │   └── post-detail.css
│       ├── heritage/
│       │   ├── heritage-detail.css
│       │   ├── heritage-map.css
│       │   ├── heritage-map-overlay.css
│       │   └── heritage-statistics.css
│       ├── user/
│       │   ├── creation-center.css
│       │   ├── login.css
│       │   ├── profile.css
│       │   └── user-creation.css
│       ├── index.css
│       ├── news.css
│       ├── non-heritage-list.css
│       └── policy.css
│
├── js/
│   ├── agent/
│   │   ├── agent-core.js
│   │   ├── dialog-manager.js
│   │   ├── plan-editor.js
│   │   ├── plan-editor-api.js
│   │   ├── plan-editor-chat.js
│   │   ├── plan-editor-ui.js
│   │   ├── progress-manager.js
│   │   ├── result-renderer.js
│   │   ├── streaming-chat.js
│   │   └── travel-planning.js
│   ├── api/
│   │   ├── forum-api.js
│   │   ├── heritage-api.js
│   │   └── user-profile-api.js
│   ├── components/
│   │   ├── advanced-lightbox.js
│   │   ├── bg-image-handler.js
│   │   ├── floating-ai-assistant.js
│   │   ├── heritage-ui.js
│   │   ├── login-modal.js
│   │   ├── modal-manager.js
│   │   ├── notification-manager.js
│   │   └── post-editor.js
│   ├── core/
│   │   ├── api.js
│   │   ├── api-utils.js
│   │   ├── auth.js
│   │   └── auth-redirect.js
│   ├── lib/
│   │   └── LunarSolarConverter.js
│   ├── pages/
│   │   ├── forum/
│   │   │   ├── forum.js
│   │   │   ├── forum-post.js
│   │   │   └── post-detail.js
│   │   ├── heritage/
│   │   │   ├── heritage-detail.js
│   │   │   ├── heritage-filters.js
│   │   │   ├── heritage-map.js
│   │   │   ├── heritage-map-sidebar.js
│   │   │   └── heritage-map-toolbar.js
│   │   ├── user/
│   │   │   ├── creation-center.js
│   │   │   ├── forgot-password.js
│   │   │   ├── login.js
│   │   │   ├── profile.js
│   │   │   ├── register.js
│   │   │   ├── reset-password.js
│   │   │   └── user-creation.js
│   │   ├── index.js
│   │   ├── news.js
│   │   ├── non-heritage-list.js
│   │   └── policy.js
│   └── utils/
│       ├── avatar-cache.js
│       ├── browsing-history.js
│       ├── date-utils.js
│       ├── image-enhancer.js
│       └── utils.js
│
├── lib/
│   ├── dify_chatbot_embed.js
│   ├── maxkb_embed.js
│   └── third-party-embed.js
│
├── pages/
│   ├── creation-center.html
│   ├── forgot-password.html
│   ├── forum.html
│   ├── forum-post.html
│   ├── heritage-detail.html
│   ├── heritage-map.html
│   ├── login.html
│   ├── news.html
│   ├── non-heritage-list.html
│   ├── policy.html
│   ├── post-detail.html
│   ├── profile.html
│   ├── register.html
│   ├── reset-password.html
│   └── user-creation.html
│
├── index.html
└── README.md
```

---

## 页面说明

### 非遗列表页 (non-heritage-list.html)

展示所有非遗项目的列表，支持分类筛选和搜索。

- **筛选功能**: 按类别、级别、地区筛选
- **搜索功能**: 关键词搜索
- **分页功能**: 分页显示项目列表
- **收藏功能**: 用户登录后可收藏感兴趣的项目

### 非遗详情页 (heritage-detail.html)

展示单个非遗项目的详细信息。

- **基本信息**: 名称、类别、级别、地区等
- **详细描述**: 历史渊源、特征、价值等
- **图片展示**: 项目相关图片，支持轮播和放大
- **地理位置**: 显示项目所在地理位置
- **收藏功能**: 用户登录后可收藏/取消收藏项目
- **聊天咨询**: 可通过 AI 助手了解更多相关信息

### 地图页 (heritage-map.html)

在地图上展示非遗项目的地理分布。

- **地图标记**: 在地图上标记非遗项目位置
- **侧边栏列表**: 显示项目列表，支持筛选
- **信息窗口**: 点击标记显示项目简介
- **收藏功能**: 用户登录后可直接在地图上收藏项目

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
- **聊天历史**: 查看与 AI 助手的历史对话

---

## 收藏功能实现

收藏功能是本平台的核心功能之一，实现了以下特性：

- **多页面支持**: 在列表页、详情页、地图页和个人中心均可操作收藏
- **状态同步**: 用户在任一页面的收藏操作会同步到其他页面
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
- **js/pages/heritage/heritage-map-sidebar.js**: 地图页收藏功能
- **js/pages/user/profile.js**: 个人中心收藏管理

---

## 聊天助手功能

聊天助手功能基于原生 JavaScript 实现，通过 SSE 与后端 Agent 服务通信，提供实时智能问答服务。

### 聊天助手核心文件

- **js/agent/streaming-chat.js**: SSE 流式聊天管理器，支持不完整的 Markdown 处理
- **js/agent/progress-manager.js**: 进度监控管理器
- **js/components/floating-ai-assistant.js**: 浮层 AI 助手组件

### 第三方嵌入占位符

以下文件为第三方服务嵌入占位符，可根据需要启用：

- **lib/dify_chatbot_embed.js**: Dify 聊天机器人嵌入脚本
- **lib/maxkb_embed.js**: MaxKB 知识库嵌入脚本
- **lib/third-party-embed.js**: 其他第三方嵌入占位符

---

## 验证码功能

注册页面使用图形验证码进行人机验证，防止恶意注册。

- **后端**: `/api/auth/captcha/generate/` - 生成验证码
- **后端**: `/api/auth/captcha/verify/` - 验证验证码
- **前端**: `js/pages/user/register.js` - 验证码显示和刷新

---

## 通知系统

全局通知系统用于显示操作结果、错误提示等信息。

- **js/components/notification-manager.js**: 通知管理器
- **css/components/notification.css**: 通知样式

使用方式：`NotificationManager.success('操作成功！')` / `error()` / `warning()` / `info()`

---

## 模态框系统

统一模态框管理，支持确认框、提示框等。

- **js/components/modal-manager.js**: 模态框管理器
- **css/components/modal.css**: 模态框样式
- **js/components/login-modal.js**: 登录模态框组件

使用方式：`ModalManager.confirm('确定吗？')` / `alert('提示')` / `showLoginModal()`

---

## 高级图片查看器

全屏图片查看组件，支持缩放、旋转、下载等功能。

- **js/components/advanced-lightbox.js**: 高级图片查看器
- **css/components/advanced-lightbox.css**: 查看器样式

---

## 帖子编辑器

富文本帖子编辑器组件。

- **js/components/post-editor.js**: 帖子编辑器
- **css/components/post-editor.css**: 编辑器样式

---

## 头像缓存管理

用户头像缓存管理，提高加载性能。

- **js/utils/avatar-cache.js**: 头像缓存组件

---

## 图片增强

图片加载优化和增强功能。

- **js/utils/image-enhancer.js**: 图片增强组件
- **js/components/bg-image-handler.js**: 背景图片处理

---

## 浮层 AI 助手

页面浮层 AI 助手组件。

- **js/components/floating-ai-assistant.js**: 浮层 AI 助手

---

## 流式聊天

支持 SSE 流式响应，用于 AI 对话场景。

- **js/agent/streaming-chat.js**: `StreamingChatManager` 类
- **js/agent/progress-manager.js**: 进度管理器
- **js/agent/result-renderer.js**: 结果渲染器

---

## Agent 智能规划

AI 旅游规划 Agent，支持 SSE 流式进度推送。

- **js/agent/agent-core.js**: 规划核心功能
- **js/agent/dialog-manager.js**: 对话管理器
- **js/agent/plan-editor.js**: 规划编辑器
- **js/agent/plan-editor-api.js**: 规划编辑器 API
- **js/agent/plan-editor-chat.js**: 规划编辑器聊天
- **js/agent/plan-editor-ui.js**: 规划编辑器 UI
- **js/agent/travel-planning.js**: 旅游规划主入口（自动初始化为 `window.travelAgent`）

---

## 如何运行

### 本地开发

本地开发需要同时启动后端服务器和前端服务器。

#### 1. 启动后端服务器

```bash
cd backend
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
python manage.py runserver
```

后端服务器将在 `http://127.0.0.1:8000` 运行。

#### 2. 启动前端服务器

**方式一：使用 Python HTTP 服务器**

```bash
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

| 服务 | 地址 |
|:---|:---|
| 前端页面 | http://localhost:8080 |
| 后端 API | http://127.0.0.1:8000/api/ |
| 管理后台 | http://127.0.0.1:8000/admin/ |

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
start_nginx.bat
```

**Linux/Mac:**

```bash
chmod +x start_nginx.sh
./start_nginx.sh
```

#### 3. 访问应用

- 前端页面: http://localhost
- 后端 API: http://localhost/api/
- 管理后台: http://localhost/admin/

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

---

## API 调用

前端通过 Fetch API 与后端通信，API 请求封装在以下文件中：

- **js/core/api.js**: 统一 API 请求封装，自动注入 CSRF Token
- **js/api/heritage-api.js**: 非遗相关 API（列表、详情、收藏等）
- **js/api/forum-api.js**: 论坛相关 API（帖子、评论、点赞、关注等）
- **js/api/user-profile-api.js**: 用户资料 API（头像、资料更新等）

### 主要 API 模块

```javascript
// 非遗 API
heritageAPI.getAllItems(params)    // 获取非遗列表
heritageAPI.getItemDetail(id)      // 获取非遗详情
addFavorite(id) / removeFavorite(id)  // 收藏操作

// 论坛 API
forumAPI.getPosts(params)          // 获取帖子列表
forumAPI.createPost(data)         // 创建帖子
forumAPI.togglePostLike(id)       // 点赞帖子

// 用户 API
API.userProfile.getUserProfile()   // 获取用户资料
API.userProfile.uploadUserAvatar(file)  // 上传头像
```

---

## 日期时间工具

`js/utils/date-utils.js` 提供日期时间处理功能：

- `dateUtils.getFormattedDateTime()` - 格式化日期时间
- `dateUtils.getLunarDate()` - 获取农历日期
- `dateUtils.getSolarTerm()` - 获取节气
- `dateUtils.getFullDateTimeInfo()` - 获取完整日期信息

---

## 开发指南

### 添加新页面

1. 在 `pages/` 目录下创建新的 HTML 文件
2. 在 `css/pages/` 目录下创建对应的 CSS 文件
3. 在 `js/pages/` 目录下创建对应的 JavaScript 文件
4. 在 HTML 文件中引入必要的 CSS 和 JavaScript 文件

### 添加 AI 助手到新页面

1. 在 HTML 页面底部引入 AI 助手脚本

```html
<script src="../js/components/floating-ai-assistant.js"></script>
```

2. 根据需要初始化 AI 助手组件

---

## 重要说明

- 本项目使用原生 JavaScript，不依赖任何前端框架
- 收藏功能需要用户登录才能使用，未登录用户无法添加/移除收藏
- 地图功能需要百度地图 API 密钥，已通过后端 `/api/map/config/` 接口统一获取
- 确保后端 API 服务器已启动并正确配置跨域访问
- 聊天助手功能需要配置相应的 AI 服务接口

---

## 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，**禁止任何形式的使用、修改、分发或商业利用**。

- 本项目代码仅供学习和参考，不得用于任何实际项目
- 未经授权，禁止复制或引用本项目的任何代码
- 所有权利保留，侵权必究

---

## 联系方式

- **项目维护者**: elaine
- **邮箱**: onee20589@gmail.com
- **项目链接**: https://github.com/Elaine-one/shaanxi-heritage-ai-platform

---

<p align="center">
  <sub>Built with ❤️ for Shaanxi Intangible Cultural Heritage</sub>
</p>
