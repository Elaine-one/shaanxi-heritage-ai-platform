# 更新日志

所有重要的前端更新都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

***

## [Unreleased](https://github.com/Elaine-one/shaanxi-heritage-ai-platform/compare/v1.4.0...HEAD)

***

## [v1.4.0](https://github.com/Elaine-one/shaanxi-heritage-ai-platform/compare/v1.3.0...v1.4.0) (2026-03-19)

### AI 规划助手增强

- 🤖 AI 规划师小组件支持缩小/半展开/全展开多种状态
- 🤖 小组件支持连续切换，状态记忆功能
- 🤖 量化记录同步，实时同步规划进度和结果
- 🤖 优化小组件动画效果，流畅的状态过渡
- 🤖 增强错误处理和重连机制

### 交互体验优化

- 🎨 优化 AI 助手的展开/收起动画
- 🎨 改进小组件在移动端的触控体验
- 🎨 增强 SSE 连接状态的视觉反馈

***

## [v1.3.0](https://github.com/Elaine-one/shaanxi-heritage-ai-platform/compare/v1.2.5...v1.3.0) (2026-03-11)

### 全面UI更新

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

***

## [v1.2.5](https://github.com/Elaine-one/shaanxi-heritage-ai-platform/compare/v1.2.0...v1.2.5) (2026-03-01)

### 架构优化

- 🏗️ 重构Agent交互模块，采用类封装设计模式
- 🏗️ 优化模块化架构，分离agent/common/pages/modules目录
- 🏗️ 统一API请求封装，自动注入CSRF Token

### 功能增强

- 🆕 完善SSE流式进度监控机制
- 🆕 新增ProgressManager进度管理器
- 🆕 新增ResultRenderer结果渲染器
- 🆕 新增DialogManager对话管理器
- 🆕 优化PlanEditor规划编辑器交互

### 技术改进

- 📈 改进EventSource错误处理与重连机制
- 📈 优化内存管理，防止组件销毁时内存泄漏
- 📈 增强请求防抖与状态保护
- 📈 完善日志输出，便于调试

***

## [v1.2.0](https://github.com/Elaine-one/shaanxi-heritage-ai-platform/releases/tag/v1.2.0) (2025-10-21)

### Bug修复

- ✅ 修复了logo.png文件路径问题
- ✅ 修复了forum-post.html页面中静态资源引用路径错误
- ✅ 优化了静态文件的组织结构

### 功能增强

- 🆕 新增论坛系统前端页面
- 🆕 增强了收藏功能的用户体验
- 🆕 优化了地图页面的交互逻辑
- 🆕 改进了搜索功能的响应速度

### 技术改进

- 📈 优化了静态资源加载性能
- 📈 改进了移动端适配效果
- 📈 增强了代码的可维护性
- 📈 完善了错误处理机制

***

