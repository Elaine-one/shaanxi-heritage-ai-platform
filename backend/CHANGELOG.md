# 更新日志

所有重要的项目更新都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

---

## [v1.2.0] (2026-03-04)

### 数据库优化

- **清理废弃表**: 删除 5 个未使用的数据库表
  - `HeritageImage` - 非遗图片表（Heritage模型已用JSON字段存储图片）
  - `CreationTag` - 创作标签表（UserCreation已用JSON字段存储标签）
  - `CreationShare` - 创作分享表（API中未使用）
  - `CreationReport` - 创作举报表（API中未使用）
  - `ForumAnnouncement` - 论坛公告表（未在URL中注册）

### API文档优化

- **中文化API文档**: 更新所有ViewSet的docstring为中文
  - 非遗相关接口
  - 用户相关接口
  - 认证相关接口
  - 论坛相关接口
  - 资讯政策接口

---

## [v1.0.0] (2025-05-10)

### 初始版本

- 完成基础功能开发
- 用户认证系统
- 非遗数据管理
- 论坛系统

---

[Unreleased]: https://github.com/Elaine-one/shaanxi-heritage-ai-platform/compare/v1.2.0...HEAD
[v1.2.0]: https://github.com/Elaine-one/shaanxi-heritage-ai-platform/compare/v1.0.0...v1.2.0
[v1.0.0]: https://github.com/Elaine-one/shaanxi-heritage-ai-platform/releases/tag/v1.0.0
