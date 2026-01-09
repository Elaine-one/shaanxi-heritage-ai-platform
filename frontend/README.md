# 陕西非物质文化遗产展示平台 - 前端

## 项目概述

本项目是陕西非物质文化遗产展示平台的前端部分，采用原生 HTML、CSS 和 JavaScript 构建，提供了直观友好的用户界面，展示陕西省丰富的非物质文化遗产资源。

## 主要功能

### 核心展示功能
- **非遗项目展示**：以列表、详情和地图等多种形式展示非遗项目
- **详情页面**：展示非遗项目的详细信息、图片和相关资料
- **地图页面**：通过百度地图直观展示非遗项目的地理分布
- **多媒体展示**：支持图片轮播、视频播放等多媒体内容展示

### 用户交互功能
- **收藏功能**：支持用户收藏感兴趣的非遗项目，并在个人中心管理收藏
- **浏览历史**：记录用户浏览历史，提供个性化推荐
- **分类筛选**：按类别、级别、地区等多维度筛选非遗项目
- **搜索功能**：支持关键词搜索，快速定位感兴趣的非遗项目
- **论坛系统**：用户可以发表帖子、评论，分享非遗相关内容

### 内容管理功能
- **新闻资讯**：展示非遗相关新闻资讯，支持分类浏览和搜索
- **政策法规**：展示非遗相关政策法规，支持类型筛选和搜索
- **动态更新**：实时更新最新的非遗项目信息和相关资讯

### 技术特性
- **响应式设计**：适配不同尺寸的设备，提供良好的移动端体验
- **用户系统**：支持用户注册、登录，管理个人收藏和浏览历史
- **智能聊天助手**：集成AI聊天功能，为用户提供非遗知识问答服务
- **性能优化**：采用懒加载、图片压缩等技术提升页面加载速度

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
│   ├── common/           # 通用样式
│   │   ├── base.css        # 基础样式
│   │   ├── header.css      # 头部样式
│   │   └── footer.css      # 底部样式
│   ├── news.css            # 新闻页样式
│   ├── policy.css          # 政策页样式
│   └── pages/           # 页面特定样式
│       ├── heritage-detail.css    # 详情页样式
│       ├── heritage-map.css       # 地图页样式
│       ├── non-heritage-list.css  # 列表页样式
│       └── profile.css            # 个人中心样式
├── js/                 # JavaScript 文件
│   ├── agent/             # AI智能体相关脚本
│   │   └── plan-editor.js     # AI规划编辑器
│   ├── common/           # 通用脚本
│   │   ├── heritage-api.js   # API 封装
│   │   ├── date-utils.js     # 日期时间工具
│   │   └── auth.js           # 认证相关
│   ├── news.js             # 新闻页脚本
│   ├── policy.js           # 政策页脚本
│   └── pages/           # 页面特定脚本
│       ├── heritage-detail.js    # 详情页脚本
│       ├── heritage-map.js       # 地图页脚本
│       ├── heritage-map-sidebar.js # 地图侧边栏脚本
│       ├── non-heritage-list.js  # 列表页脚本
│       └── profile.js            # 个人中心脚本
├── lib/                # 第三方库
│   ├── dify_chatbot_embed.js  # AI聊天助手嵌入脚本
│   ├── maxkb_embed.js         # 知识库嵌入脚本
│   └── third-party-embed.js   # 其他第三方嵌入脚本
├── pages/              # HTML 页面
│   ├── heritage-detail.html    # 详情页
│   ├── heritage-map.html       # 地图页
│   ├── login.html              # 登录页
│   ├── news.html               # 新闻页
│   ├── non-heritage-list.html  # 列表页
│   ├── policy.html             # 政策页
│   ├── profile.html            # 个人中心
│   └── register.html           # 注册页
├── static/             # 静态资源
│   └── images/           # 图片资源
└── index.html          # 首页
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

1. 克隆仓库：
   ```bash
   git clone <repository_url>
   cd <repository_directory>/frontend
   ```

2. 使用简单的 HTTP 服务器：
   ```bash
   python -m http.server 8080
   ```
   或使用 VS Code 的 Live Server 插件

3. 在浏览器中访问：
   ```
   http://localhost:8080
   ```

### 配置后端 API

在 `js/common/heritage-api.js` 文件中配置后端 API 地址：

```javascript
const API_BASE_URL = 'http://localhost:8000/api';
```

## API 调用

前端通过 Fetch API 与后端通信，主要 API 调用封装在 `js/common/heritage-api.js` 文件中：

```javascript
// 获取非遗项目列表
async function getHeritageItems(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const response = await fetch(`${API_BASE_URL}/heritage/items/?${queryString}`);
    return await response.json();
}

// 获取非遗项目详情
async function getHeritageDetail(id) {
    const response = await fetch(`${API_BASE_URL}/heritage/items/${id}/`);
    return await response.json();
}

// 添加收藏
async function addFavorite(heritageId) {
    const response = await fetch(`${API_BASE_URL}/favorites/toggle/${heritageId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        credentials: 'include'
    });
    return await response.json();
}

// 发送聊天消息
async function sendChatMessage(message) {
    const response = await fetch(`${API_BASE_URL}/chat/message/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ message }),
        credentials: 'include'
    });
    return await response.json();
}
```

## 日期时间工具

前端包含日期时间工具 `js/common/date-utils.js`，用于处理和格式化日期时间，包括：

- 格式化日期时间
- 显示农历日期
- 显示节气信息

```javascript
// 获取格式化日期时间
async function getFormattedDate() {
    const response = await fetch(`${API_BASE_URL}/date/formatted/`);
    return await response.json();
}

// 更新页面上的日期时间显示
function updateDateTimeDisplay() {
    getFormattedDate().then(data => {
        document.getElementById('current-date').textContent = 
            `${data.year}年${data.month}月${data.day}日 ${data.weekday}`;
        document.getElementById('lunar-date').textContent = 
            `农历 ${data.lunar_date} ${data.solar_term || ''}`;
    });
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

### v1.2.0 (2025-10-21)

#### Bug修复
- ✅ 修复了favicon.ico文件404错误
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

## 开发规范

### 代码风格
- 使用2个空格进行缩进
- 变量和函数名使用驼峰命名法
- 常量使用大写字母和下划线
- 为所有函数添加注释说明

### 文件命名
- HTML文件使用小写字母和连字符
- CSS文件按功能模块命名
- JavaScript文件按页面或功能命名
- 图片文件使用描述性名称

## 故障排除

### 常见问题

**Q: 页面显示404错误**
A: 检查静态文件路径是否正确，确保favicon.ico和logo.png文件存在于正确位置

**Q: 地图无法显示**
A: 检查百度地图API密钥是否正确配置，网络连接是否正常

**Q: 收藏功能不工作**
A: 确认用户已登录，检查后端API是否正常运行

**Q: 聊天助手无法加载**
A: 检查AI服务配置是否正确，网络连接是否稳定

### 调试技巧
- 使用浏览器开发者工具检查网络请求
- 查看控制台错误信息
- 使用断点调试JavaScript代码
- 检查本地存储数据是否正确

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