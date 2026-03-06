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
│   ├── pages/               # 页面特定样式
│   │   ├── creation-center.css  # 创作中心样式
│   │   ├── heritage-detail.css  # 详情页样式
│   │   ├── heritage-map.css     # 地图页样式
│   │   ├── heritage-map-overlay.css  # 地图覆盖层样式
│   │   ├── heritage-statistics.css  # 统计页面样式
│   │   ├── index.css            # 首页样式
│   │   ├── login.css            # 登录页样式
│   │   ├── non-heritage-list.css  # 列表页样式
│   │   ├── profile.css            # 个人中心样式
│   │   └── user-creation.css     # 用户创作样式
│   ├── common.css           # 通用样式
│   ├── forum.css            # 论坛样式
│   ├── forum-post.css       # 论坛帖子样式
│   ├── forum-post-header.css # 论坛帖子头部样式
│   ├── news.css             # 新闻页样式
│   ├── policy.css           # 政策页样式
│   └── post-detail.css      # 帖子详情样式
├── js/                 # JavaScript 文件
│   ├── agent/             # AI智能体相关脚本
│   │   ├── agent-core.js        # 规划核心功能
│   │   ├── dialog-manager.js    # 对话管理器
│   │   ├── plan-editor.js       # AI规划编辑器
│   │   ├── progress-manager.js  # 进度管理器
│   │   ├── result-renderer.js   # 结果渲染器
│   │   └── travel-planning.js   # 旅游规划主脚本
│   ├── api/                 # API相关脚本
│   │   ├── forum-api.js         # 论坛API
│   │   └── user-profile-api.js  # 用户资料API
│   ├── common/           # 通用脚本
│   │   ├── api.js               # 统一API请求封装
│   │   ├── api-utils.js         # API工具函数
│   │   ├── auth.js              # 认证相关
│   │   ├── bg-image-handler.js  # 背景图片处理
│   │   ├── browsing-history.js  # 浏览历史
│   │   ├── date-utils.js        # 日期时间工具
│   │   ├── heritage-api.js      # 非遗API
│   │   ├── heritage-ui.js       # UI工具函数
│   │   ├── tracker.js           # 埋点追踪
│   │   └── utils.js             # 工具函数
│   ├── lib/               # 工具库
│   │   └── LunarSolarConverter.js  # 农历阳历转换
│   ├── modules/          # 模块脚本
│   │   ├── profile-favorites.js  # 个人中心收藏模块
│   │   ├── profile-history.js    # 个人中心历史模块
│   │   ├── profile-settings.js   # 个人中心设置模块
│   │   └── profile-utils.js      # 个人中心工具函数
│   ├── pages/           # 页面特定脚本
│   │   ├── creation-center.js   # 创作中心脚本
│   │   ├── forgot-password.js   # 忘记密码脚本
│   │   ├── forum.js             # 论坛脚本
│   │   ├── forum-post.js        # 论坛帖子脚本
│   │   ├── heritage-detail.js   # 详情页脚本
│   │   ├── heritage-filters.js  # 筛选功能脚本
│   │   ├── heritage-map.js      # 地图页脚本
│   │   ├── heritage-map-sidebar.js # 地图侧边栏脚本
│   │   ├── index.js             # 首页脚本
│   │   ├── login.js             # 登录脚本
│   │   ├── non-heritage-list.js # 列表页脚本
│   │   ├── post-detail.js       # 帖子详情脚本
│   │   ├── profile.js           # 个人中心脚本
│   │   ├── register.js          # 注册脚本
│   │   ├── reset-password.js    # 密码重置脚本
│   │   └── user-creation.js     # 用户创作脚本
│   ├── news.js             # 新闻页脚本
│   └── policy.js           # 政策页脚本
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

- **js/common/heritage-api.js**: 封装了收藏相关的 API 调用
  - `addFavorite()`: 添加收藏
  - `removeFavorite()`: 移除收藏
  - `checkFavoriteStatus()`: 检查收藏状态
  - `getUserFavorites()`: 获取用户收藏列表
  - `updateFavoriteButtonsState()`: 更新所有收藏按钮状态
  - `heritageEvents`: 收藏状态事件总线

- **js/pages/heritage-detail.js**: 详情页收藏功能
  - `toggleFavorite()`: 切换收藏状态
  - `checkFavoriteStatus()`: 检查收藏状态
  - `updateFavoriteButton()`: 更新收藏按钮样式

- **js/pages/heritage-map-sidebar.js**: 地图页收藏功能
  - `toggleCollection()`: 切换收藏状态
  - `updateCollectionButtonsState()`: 更新所有收藏按钮状态
  - `loadCollectionsFromStorage()`: 从本地存储加载收藏
  - `saveCollectionsToStorage()`: 保存收藏到本地存储
  - `updateCollectionCount()`: 更新收藏计数

- **js/pages/profile.js**: 个人中心收藏管理
  - `fetchUserFavorites()`: 获取用户收藏列表
  - `renderFavorites()`: 渲染收藏列表
  - `removeFavorite()`: 移除收藏
  - `sortFavorites()`: 排序收藏列表

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

前端通过 Fetch API 与后端通信，API请求统一封装在 `js/common/api.js` 文件中：

```javascript
// 统一API请求函数
async function apiRequest(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    // CSRF Token自动注入
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes((options.method || 'GET').toUpperCase())) {
        const csrfToken = window.getCookie('csrftoken');
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
    }
    
    const url = `/api${endpoint}`;
    
    const response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include'  // 携带Session Cookie
    });
    
    return response.json();
}
```

非遗相关API封装在 `js/common/heritage-api.js` 文件中：

```javascript
// 获取非遗项目列表
const heritageAPI = {
    getAllItems: async (params = {}) => {
        let allItems = [];
        let currentPage = params.page || 1;
        // 分页获取所有数据
        // ...
    },
    
    getDetail: async (id) => {
        return apiRequest(`/heritage/items/${id}/`);
    }
};

// 收藏功能
async function toggleFavorite(heritageId) {
    return apiRequest(`/favorites/toggle/${heritageId}/`, {
        method: 'POST'
    });
}

// 检查收藏状态
async function checkFavoriteStatus(heritageId) {
    return apiRequest(`/favorites/status/${heritageId}/`);
}
```

## 日期时间工具

前端包含日期时间工具 `js/common/date-utils.js`，用于处理和格式化日期时间，包括：

- 格式化日期时间
- 显示农历日期（使用 `js/lib/LunarSolarConverter.js` 库）
- 显示节气信息

```javascript
// 日期时间格式选项
const DATE_FORMAT_OPTIONS = {
    FULL: { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long', hour: '2-digit', minute: '2-digit' },
    DATE_ONLY: { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' },
    TIME_ONLY: { hour: '2-digit', minute: '2-digit' }
};

// 获取格式化的日期时间字符串
function getFormattedDateTime(options = DATE_FORMAT_OPTIONS.FULL) {
    const now = new Date();
    return now.toLocaleDateString('zh-CN', options);
}

// 获取农历日期（使用LunarSolarConverter库）
function getLunarDate() {
    const now = new Date();
    const converter = new LunarSolarConverter();
    const lunar = converter.Lunar(now);
    return `农历 ${lunar.monthStr}${lunar.dayStr}`;
}
```

## 开发指南

### 添加新页面

1. 在 `pages/` 目录下创建新的 HTML 文件
2. 在 `css/pages/` 目录下创建对应的 CSS 文件
3. 在 `js/pages/` 目录下创建对应的 JavaScript 文件
4. 在 HTML 文件中引入必要的 CSS 和 JavaScript 文件

### 修改现有功能

1. 确定需要修改的功能所在的文件
2. 修改相应的 HTML、CSS 或 JavaScript 代码
3. 在浏览器中测试修改效果

### 添加聊天助手到新页面

1. 在HTML页面底部引入聊天助手脚本
   ```html
   <script src="../lib/dify_chatbot_embed.js"></script>
   ```
2. 根据需要配置聊天助手参数

## 最新更新记录

### v1.3.0 (2026-03-06)

#### 创作者中心全面优化
- 🎨 创作者中心UI/UX全面升级，采用现代化设计语言
- 🎨 新增渐变色彩系统和视觉层次优化
- 🎨 优化卡片布局、间距和阴影效果
- 🎨 添加流畅的交互动画和过渡效果
- 🎨 完善响应式设计，适配多种屏幕尺寸

#### 关注功能完善
- � 修复关注按钮在本人帖子上的显示问题
- 🔄 统一用户ID字段命名规范（id vs userId）
- � 修复用户创作中心关注API端点错误
- 🔄 实现论坛与用户创作中心关注状态同步
- � 修复重复关注/取消关注的问题

#### 代码质量提升
- ✅ 完善错误处理和用户反馈提示
- ✅ 提升代码可维护性和一致性

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