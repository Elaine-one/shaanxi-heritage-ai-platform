# 🖥️ 陕西非遗管理后台（Vue3）

<div align="center">

![Vue](https://img.shields.io/badge/Vue-3.5.32-4FC08D?style=flat&logo=vue.js&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-8.0.10-646CFF?style=flat&logo=vite&logoColor=white)
![Element Plus](https://img.shields.io/badge/Element%20Plus-2.14.0-409EFF?style=flat&logo=element&logoColor=white)
![License](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-red.svg)

</div>

---

## 📖 项目概述

基于 **Vue 3.5** + **Vite 8.0** + **Element Plus 2.14** 构建的现代化管理后台前端，替代 Django Admin 界面，提供直观友好的管理操作界面。

---

## ✨ 核心功能

| 功能 | 说明 |
|:---|:---|
| 🔐 **管理员认证** | 用户名密码登录、Session + Cookie 认证、速率限制 |
| 📊 **仪表盘** | 统计数据展示、操作记录、快捷操作入口 |
| 👥 **用户管理** | 用户列表、创建用户、编辑信息、重置密码 |
| 🏛️ **非遗管理** | 非遗项目 CRUD、分类筛选、搜索 |
| 📰 **资讯政策** | 新闻资讯管理、政策法规管理 |
| 💬 **论坛管理** | 帖子管理、标签管理、公告管理、版规管理、举报处理 |
| 🎨 **创作管理** | 用户创作内容审核、状态管理 |
| 📝 **操作日志** | 管理操作记录、Django Admin 日志合并展示 |

---

## 🎨 UI 特性

| 特性 | 说明 |
|:---|:---|
| 🏮 **传统文化风格** | 朱砂红 + 金色主题，中国印章风格图标 |
| 📜 **滚动条美化** | 自定义滚动条样式，平滑滚动效果 |
| 🌙 **暗色侧边栏** | 护眼暗色导航，金色高亮 |
| 📱 **响应式布局** | 适配不同屏幕尺寸 |
| ⚡ **Element Plus** | 丰富的 UI 组件，开箱即用 |

---

## 🏗️ 技术架构

### 技术栈

| 类别 | 技术 |
|:---|:---|
| **框架** | Vue 3.5.32 |
| **构建工具** | Vite 8.0.10 |
| **UI 组件** | Element Plus 2.14.0 |
| **状态管理** | Pinia 3.0.4 |
| **路由** | Vue Router 4.6.4 |
| **HTTP 客户端** | Axios 1.16.0 |
| **样式** | SCSS + CSS Variables |
| **图标** | Element Plus Icons |

---

## 📂 项目结构

```
admin-frontend/
├── public/                     # 📁 静态资源
│   ├── favicon.svg            # 网站图标（印章风格）
│   └── icons.svg              # Element Plus 图标集合
│
├── src/
│   ├── api/                   # 🔌 API 接口封装
│   │   ├── admin.js           # 管理后台 API
│   │   ├── auth.js            # 认证 API
│   │   ├── heritage.js        # 非遗 API
│   │   ├── news.js            # 新闻 API
│   │   ├── policy.js          # 政策 API
│   │   ├── forum.js           # 论坛 API
│   │   ├── creation.js        # 创作 API
│   │   ├── user.js            # 用户 API
│   │   └── request.js         # Axios 实例配置
│   │
│   ├── layouts/               # 📐 布局组件
│   │   ├── AdminLayout.vue    # 主布局
│   │   ├── Header.vue         # 顶部导航
│   │   └── Sidebar.vue        # 侧边栏菜单
│   │
│   ├── router/                # 🛤️ 路由配置
│   │   └── index.js
│   │
│   ├── stores/                # 📦 状态管理
│   │   ├── app.js             # 应用状态
│   │   └── auth.js            # 认证状态
│   │
│   ├── styles/                # 🎨 全局样式
│   │   └── element-override.scss  # Element Plus 主题覆盖
│   │
│   ├── utils/                 # 🔧 工具函数
│   │   ├── csrf.js            # CSRF Token 处理
│   │   └── format.js          # 格式化工具
│   │
│   ├── views/                 # 📄 页面组件
│   │   ├── dashboard/
│   │   │   └── DashboardView.vue
│   │   ├── heritage/
│   │   │   ├── HeritageList.vue
│   │   │   └── HeritageDetail.vue
│   │   ├── news/
│   │   │   ├── NewsList.vue
│   │   │   └── NewsDetail.vue
│   │   ├── policy/
│   │   │   ├── PolicyList.vue
│   │   │   └── PolicyDetail.vue
│   │   ├── forum/
│   │   │   ├── PostList.vue
│   │   │   ├── TagList.vue
│   │   │   ├── AnnouncementList.vue
│   │   │   ├── RuleList.vue
│   │   │   └── ReportList.vue
│   │   ├── creation/
│   │   │   ├── CreationList.vue
│   │   │   └── CreationDetail.vue
│   │   ├── user/
│   │   │   ├── UserList.vue
│   │   │   └── UserDetail.vue
│   │   └── login/
│   │       └── LoginView.vue
│   │
│   ├── App.vue                # 根组件
│   └── main.js                # 入口文件
│
├── index.html                 # HTML 入口
├── vite.config.js             # Vite 配置
├── package.json               # 依赖配置
└── README.md                  # 项目文档
```

---

## 🚀 快速开始

### 环境要求

| 组件 | 版本 | 用途 |
|:---|:---|:---|
| Node.js | 18.0+ | 运行环境 |
| npm | 9.0+ | 包管理器 |

### 安装依赖

```bash
cd admin-frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
```

构建产物自动输出到 `../backend/admin_static/`

### 预览构建结果

```bash
npm run preview
```

---

## 📡 API 端点

### 认证接口

| 端点 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/admin/login/` | POST | 管理员登录（速率限制 5次/分钟/IP） |

### 统计 & 日志接口

| 端点 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/admin/stats/` | GET | 获取统计数据 |
| `/api/admin/operation-logs/` | GET | 操作记录列表（合并 Django LogEntry） |

### 用户管理接口

| 端点 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/admin/users/` | GET | 用户列表（支持搜索、筛选、分页） |
| `/api/admin/users/create/` | POST | 创建用户 |
| `/api/admin/users/{id}/` | GET/PATCH | 用户详情/更新 |
| `/api/admin/users/{id}/reset-password/` | POST | 重置用户密码 |

### 论坛管理接口

| 端点 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/admin/forum/posts/` | GET | 帖子列表（所有状态） |
| `/api/admin/forum/posts/{id}/` | GET/PATCH/DELETE | 帖子详情/状态变更/删除 |
| `/api/admin/forum/tags/` | GET/POST | 标签列表/创建 |
| `/api/admin/forum/tags/{id}/` | GET/PUT/DELETE | 标签详情/更新/删除 |
| `/api/admin/forum/announcements/` | GET/POST | 公告列表/创建 |
| `/api/admin/forum/rules/` | GET/POST | 版规列表/创建 |
| `/api/admin/forum/reports/` | GET | 举报列表 |
| `/api/admin/forum/reports/{id}/` | GET/PATCH | 举报详情/处理 |

### 创作管理接口

| 端点 | 方法 | 描述 |
|:---|:---:|:---|
| `/api/admin/creations/` | GET | 创作列表（支持类型、状态筛选） |
| `/api/admin/creations/{id}/` | GET/PATCH/DELETE | 创作详情/状态变更/删除 |

---

## 🔐 安全特性

| 特性 | 说明 |
|:---|:---|
| **CSRF 防护** | 自动获取并注入 CSRF Token |
| **登录速率限制** | 5次/分钟/IP，超限返回 429 |
| **权限分级** | 超级管理员 > 管理员 > 普通用户 |
| **is_staff 保护** | 仅超级管理员可修改用户的 is_staff 字段 |
| **操作日志** | 所有写操作自动记录到 AdminOperationLog |

---

## 📦 部署说明

### 开发环境

前端运行在 `localhost:3000`，通过 Vite proxy 代理请求到 Django 后端 `localhost:8000`。

### 生产环境

1. 执行 `npm run build` 构建前端
2. 构建产物自动输出到 `backend/admin_static/`
3. Django 通过静态文件配置提供服务
4. 访问 `http://your-domain/vue-admin/`

### Nginx 配置示例

```nginx
location /vue-admin/ {
    alias /path/to/backend/admin_static/;
    try_files $uri $uri/ /vue-admin/index.html;
}

location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## 📝 更新日志

### v1.0.0 (2026-05-12)

- ✨ 初始版本发布
- ✅ 完成所有核心管理功能
- 🎨 实现中国传统文化风格 UI
- 📝 添加操作日志记录（AdminOperationLog）
- 🐛 修复前端收藏功能分页数据解析问题
- 🧹 清理数据库中残留的 TravelPlan 幽灵表
- 🎨 美化滚动条样式，新增印章风格 favicon 图标

---

## 🔗 相关链接

- [Vue 3 文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [Vite 文档](https://vitejs.dev/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Vue Router 文档](https://router.vuejs.org/)

---

## 📄 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，**禁止任何形式的使用、修改、分发或商业利用**。

---

## 📬 联系方式

- **项目维护者**: elaine
- **邮箱**: onee20589@gmail.com
- **项目链接**: [GitHub Repository](https://github.com/Elaine-one/shaanxi-heritage-ai-platform)

---

<p align="center">
  <sub>Built with ❤️ for Shaanxi Intangible Cultural Heritage</sub>
</p>
