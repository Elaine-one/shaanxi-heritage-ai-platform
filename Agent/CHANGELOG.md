# 更新日志

## v1.7（2026-06-23）

#### 🔧 API 规整化与架构清理

**端点精简 (44 → 17, -61%)：**

- 🗑️ 清理 4 个桩端点（`apply_plan_changes`、`get_edit_history`、`get_available_operations`、`get_plan_summary`）
- 🗑️ 删除 4 个无调用方端点（`DELETE /api/travel-plan/{id}`、`GET /api/travel-plan/list`、`GET /api/agent/session_info`、`GET /api/agent/health`）
- 🗑️ 移除对话管理 HTTP 路由（保留 `services/conversation_service.py` 内部调用）
- 🗑️ 移除知识图谱管理 HTTP 路由（保留 `memory/` 层内部调用）
- 🗑️ 移除天气 HTTP 端点（保留 `services/weather.py` 内部调用）
- 🗑️ 删除 Django 侧死代码（`TravelPlanExportView`、`get_agent_service_url`、对应 URL 路由）

**FastAPI 路由重组：**

- ✅ 新增 `api/travel_endpoints.py`：`travel_router`（`prefix='/api/agent/travel-plan'`，`tags=['旅游规划']`），6 条路由
- ✅ 重构 `api/edit_endpoints.py`：`edit_router`（`tags=['AI 编辑与对话']`），9 条路由
- ✅ 新增 `api/cache.py`：共享 `progress_callbacks` TTLCache，解决 app.py 与路由模块的循环依赖
- ✅ 新增 `api/error_models.py`：统一错误响应 `{success, error: {code, message}, detail}`
- ✅ 精简 `api/app.py`（761→200 行）：仅保留 lifespan、CORS、全局异常处理器、根/健康端点、路由注册

**关键 Bug 修复：**

- 🐛 修复 `memory/coordinator.py` 循环导入导致 L1/L2/L3/RAG 全部静默降级（P0.1）
- 🐛 修复 SSE 序列化安全：`json.dumps(data, ensure_ascii=False, default=str)`（P0.2）
- 🐛 修复 4 处 HTTPException 被外层 `except Exception` 吞为 500（P1.1）

**Nginx 架构优化：**

- ✅ `/api/agent/` 从 Nginx→Django→Agent 两跳改为 Nginx→Agent 直连
- ✅ `/api/agent/` 统一聚合所有 Agent 路由（旅行规划 + 编辑对话），取消原 `/api/travel-plan/` 独立前缀
- ✅ 新增 `/vue-admin/` location（`alias backend/admin_static/`）
- ✅ 新增 `/health/agent` 独立健康检查

## v1.6.1（2026-06-22）

#### 🧠 记忆系统可靠性修复（12 项）

- ✅ 偏好向量迁至独立 ChromaDB 集合 `user_preferences`，根治对话检索污染
- ✅ L1 滚动窗口改为 Redis Lua 原子写入，消除并发竞态
- ✅ L3 SQLite 持久连接 + WAL 模式
- ✅ 归档流程 L1 清理前检查 L2 增强结果，防止对话数据丢失
- ✅ `_call_model` → `call_model` 公开化

## v1.6（2026-06-22）

#### 🔗 知识图谱架构重构 — Mixin 模块化

将单体 `knowledge_graph.py` 拆分为 Mixin 架构包 `knowledge_graph/`：

```
knowledge_graph/
├── __init__.py   # KnowledgeGraph 主类（6 个 Mixin 组合）
├── _base.py      # BaseMixin — 连接管理 / MERGE 节点 / MERGE 关系
├── heritage.py   # HeritageMixin — 非遗 / 区域 / 层级 / 位置 / NEAR / Region 树
├── inheritor.py  # InheritorMixin — 传承人 / HAS_INHERITOR / STUDIED_UNDER
├── dynasty.py    # DynastyMixin — 朝代匹配 / ORIGINATED_IN
├── queries.py    # QueryMixin — 时间轴 / 层级 / 关联查询
└── admin.py      # AdminMixin — 统计 / 索引 / 清理
```

- 新增长参数 `level`（省/地级市/区县）支持 Region 节点
- 所有节点写入自动添加 `updated_at = datetime()`
- get_stats() 改为动态统计所有标签/关系类型
- 新增 2 个关系类型：ORIGINATED_IN、PART_OF

#### 🧠 记忆系统扩展

- ✅ 新增 `importance_scorer.py`：记忆重要性评分
- ✅ 新增 `task_buffer.py`：任务队列缓冲
- ✅ 新增 `preference_vectorizer.py`：偏好向量化
- ✅ 新增 `working_memory_assembler.py`：工作记忆组装
- ✅ 会话模块重构为 `session/` 包（pool / redis_pool / context / lifecycle / archiver / index）

#### 📜 阶段一：传承人图谱（168 节点 / 156 HAS_INHERITOR / 24 STUDIED_UNDER）

- ✅ InheritorMixin 正则解析器：标准格式 `姓名(级别, 批次, 生年, 简介)`
- ✅ 集成到启动同步 `sync_inheritors_from_heritage_list()`
- ✅ LLM 二次查漏补缺：正则初筛 84 人，LLM 新发现 54 人
  - 处理顿号分隔名单、分代列举、斜线分隔、兜底名单等非标准格式
  - 受益记录：安塞腰鼓(+1)、宝鸡社火脸谱(+15)、东雷上锣鼓(+37)、陕西皮影戏(+1)

#### ⏳ 阶段二：时间轴 + 地理层级（20 Dynasty / 112 ORIGINATED_IN / 40 Region / 37 PART_OF）

- ✅ DynastyMixin：
  - 20 个标准朝代（DYNASTY_TABLE）+ 50+ 别名映射（DYNASTY_ALIASES）
  - 三轮匹配策略：30+ 正则模式 → 6 个复合模式 → 别名表
  - 32/32 非遗全部匹配到朝代（100% 覆盖率）
  - 修复"元"误匹配"万元"问题
- ✅ Region 层级树：10 市 → 27 区县的三级 PART_OF 树
  - `expand_region_tree()` 全量创建
  - `refine_heritage_region()` 将 23 条记录精确关联到区县
- ✅ HeritageTimelineTool 注册（支持按朝代/按项目/完整时间轴三种查询）

#### 📈 图谱指标

| 指标 | v1.5 | v1.6 |
|------|------|------|
| 节点类型 | 6 | **8** (+Inheritor, +Dynasty) |
| 关系类型 | 6 | **12** (+6) |
| 总节点 | ~200 | **331** |
| 总关系 | ~350 | **704** |
| 查询工具 | 5 | **10** (+5) |

## v1.5（2026-05-5）

#### 🧠 记忆系统架构重构

**新增核心模块：**

- ✅ 新增 `coordinator.py`：记忆协调器，统一管理四层记忆（内存/Redis/SQLite/Neo4j）
- ✅ 新增 `sifter.py`：记忆筛选器，实现智能上下文过滤与优先级排序
- ✅ 新增 `l2_graph_store.py`：L2 图存储层，强化关系记忆与知识图谱集成
- ✅ 新增 `l3_sqlite_ledger.py`：L3 账本存储，替代旧 SQLite 模块，支持审计追踪
- ✅ 新增 `session_provider.py`：会话提供者，统一会话管理接口
- ✅ 新增 `memory_budget.py`：记忆预算配置，控制 Token 消耗与上下文长度

**上下文系统优化：**

- ✅ 重构 `context_compressor.py`：优化 P0-P3 四级压缩策略
- ✅ 优化 `context_builder.py`：改进上下文构建流程，增强层间通信
- ✅ 改进 `unified_context.py`：扩展上下文模型，支持记忆预算控制

**会话管理重构：**

- ✅ 重构 `session.py`：优化会话状态管理，支持多存储后端切换
- ✅ 改进 `redis_session.py`：增强分布式会话支持

**模块清理：**

- 🗑️ 移除 `memory/sqlite_store.py`：被 `l3_sqlite_ledger.py` 替代
- 🗑️ 移除 `memory/user_profile.py`：功能整合至 L3 账本
- 🗑️ 移除 `memory/conversation_vector_service.py`：功能迁移至筛选器
- 🗑️ 移除 `tools/context_manager.py`：功能整合至协调器
- 🗑️ 移除 `api/export/` 目录：导出功能迁移
- 🗑️ 移除 `core/concurrency.py`、`progress_manager.py`、`task_queue.py`：功能整合

## v1.4（2026-03-19）

#### 🔌 MCP 工具统一封装

- ✅ 新增 MCP（Model Context Protocol）协议客户端，支持高德地图服务
- ✅ 新增 `amap_mcp_client.py`：高德地图 MCP Server 连接器
- ✅ 新增 `mcp_client.py`：MCP 客户端封装，提供路线规划、POI搜索、距离测量等工具
- ✅ 新增 `mcp_tools.py`：MCP 工具类定义（MCPRouteTool、MCPPOISearchTool、MCPTrafficTool、MCPGeocodingTool）
- ✅ 新增 `mcp_tool_adapter.py`：MCP 工具适配器，统一工具接口
- ✅ 新增 `mcp_protocol_client.py`：MCP 协议客户端，支持 stdio/SSE/streamable-http 多种连接方式

#### 🧠 ReAct 优化

- ✅ 优化推理提示词，提高工具选择准确性
- ✅ 增强上下文理解能力，支持复杂多轮对话
- ✅ 改进错误处理和降级策略

#### 💾 记忆模块优化

- ✅ 新增 `knowledge_graph.py`：Neo4j 知识图谱管理，支持非遗项目关联查询
- ✅ 新增 `rag_retriever.py`：RAG 检索增强生成，支持混合搜索
- ✅ 新增 `conversation_vector_service.py`：对话向量服务
- ✅ 优化 `session.py`：增强会话状态管理和上下文提取
- ✅ 优化 `user_profile.py`：完善用户偏好管理

#### 🎯 上下文系统优化

- ✅ 新增 `unified_context.py`：统一上下文模型
- ✅ 新增 `context_builder.py`：上下文构建器，支持意图检测
- ✅ 新增 `context_compressor.py`：上下文压缩器，支持 Token 预算控制
- ✅ 新增 `cache_manager.py`：分层缓存管理器（L1 内存 + L2 Redis）

#### 🔧 其他优化

- ✅ 新增 `safety_checker.py`：安全检测器，支持敏感词过滤和注入防护
- ✅ 新增 `concurrency.py`：并发控制模块
- ✅ 新增 `resource_manager.py`：资源管理器
- ✅ 新增 `progress_manager.py`：进度管理器

## v1.3.6（2026-03-04）

#### 🚀 LangChain 1.0 适配

- ✅ 使用 LangChain 1.0 原生 `astream()` 方法实现流式输出，替代自定义实现
- ✅ 利用 LangChain 1.0 新增的异步支持，增强流式返回到前端的性能
- ✅ 移除冗余的 LLM 包装器（models/langchain/ 目录），直接使用 LangChain ChatOpenAI
- ✅ 统一提示词管理，使用 LangChain PromptTemplate 替代字符串拼接
- ✅ 优化 LLM 模块结构，减少自定义包装层

#### 📊 系统验证

- ✅ 分析运行日志，确认系统运行状态正常
- ✅ 验证流式输出、工具调用、会话管理等功能正常
- ✅ 检查代码重复和逻辑问题

## v1.3.5（2026-03-01）

- 支持多厂商LLM切换（OpenAI、DashScope、DeepSeek、智谱GLM、Moonshot、Ollama）
- 新增LLM工厂模式，简化模型实例化流程
- 重构LLM模型层，统一使用LangChain ChatOpenAI接口
- 优化上下文传递格式，改进会话管理
- 优化日志系统，添加单例模式防止重复初始化
- 适配langchain1.0.0，修复与旧版本不兼容问题

## v1.3.3（2026-02-28）

#### 🐛 Bug修复

- ✅ 修复了前端流式输出在后台停止的问题
- ✅ 修复了AI响应时输入框被禁用的问题
- ✅ 修复了AI响应内容被截断的问题
- ✅ 修复了硬编码城市坐标的问题，改用地理编码服务

#### 🚀 功能增强

- 🆕 实现了基于requestAnimationFrame的流式输出优化
- ✨ 添加了页面可见性检测，后台时暂停流式输出
- 🆕 优化了ReAct Agent提示词模板，防止响应截断
- 🆕 重构了天气服务，移除模拟数据，创建天气评估专家工具
- 🆕 设计了基于SSE和AsyncGenerator的后端流式实现方案
- 🆕 支持指定日期的农历和节气计算

#### 📈 技术改进

- 📈 优化了前端流式输出的性能和用户体验
- 📈 改进了天气服务的准确性和可靠性
- 📈 增强了代码的可维护性和可读性
- 📈 完善了农历计算的准确性（支持1900-2100年）
- 📈 改进了地理编码服务的集成，避免硬编码坐标

## v1.3.2（2026-02-08）

#### 🔧 系统架构优化

- ✅ 优化后端文件结构，采用 `api/`, `serializers/`, `services/` 分层架构
- ✅ 移除 Agent URL 加密功能，简化服务间通信
- ✅ 完善 Agent 服务反向代理，前端通过 Django 统一访问 Agent API
- ✅ 移除前端 MinIO 依赖，所有文件存储通过后端/Agent服务处理

## v1.3.1（2026-01-11）

#### 🧠 对话历史智能优化

- ✅ 新增 `conversation_summary.py` 提示词模板，定义专业角色以保证提取准确性
- ✅ 在提示词中定义"对话历史分析专家"角色，确保摘要质量和信息密度
- ✅ 智能提取用户需求、已确定信息、关键决策点等核心内容
- ✅ 控制摘要长度在 200-500 字之间，确保信息密度高

#### 📄 PDF 生成升级

- ✅ 升级 PDF 生成流程，使用 LLM 智能摘要替代简单截取
- ✅ 确保 PDF 生成和聊天界面使用一致的对话历史处理方式

#### 🔧 技术优化与修复

- ✅ 修复 Pydantic v2 与 LangChain 工具的兼容性问题
- ✅ 修改 `schemas.py` 导入语句，使用 `pydantic.v1` 的 BaseModel
- ✅ 添加异常处理和降级机制，提升系统健壮性

## v1.3.0（2026-01-09）

#### 🔐 认证系统升级

- ✅ 引入基于 Django Session 的用户认证机制，替代原有的 JWT 方案
- ✅ 新增 `session_dependencies.py` 模块，提供 FastAPI 兼容的 Session 验证依赖
- ✅ 为所有核心接口添加 Session 认证保护，确保仅授权用户可访问
- ✅ 配置 `settings.py` 中的 Session 参数（密钥、存储、过期策略等）
- ✅ 支持前后端共享 Session 存储（如 Redis 或数据库）实现身份验证

#### 🧠 Agent 架构重构

- ✅ 大规模重构 Agent 模块，优化整体代码结构与职责划分

## v1.2.0 (2025-10-21)

- ✅ **会话管理架构重构**: 将 SessionPool 从 agent/ 移动到 memory/ 目录，统一会话管理
- ✅ **移除冗余会话存储**: 删除 PlanEditor 中的 active\_sessions，统一使用 SessionPool
- ✅ **优化会话上下文提取**: 改进 \_extract\_core\_info 方法，支持从 plan\['basic\_info'] 获取用户信息
- ✅ **完善会话管理API**: 更新所有会话相关方法的调用，确保使用统一的 SessionPool 接口

## v1.1.1 (2025-10-15)

- ✅ **修复用户信息传递问题**: AI现在能够正确获取用户的出发地、交通方式、人数、预算等完整信息
- ✅ **修复天气日期计算**: 优化天气服务中的日期计算逻辑，确保天气查询使用正确的日期
- ✅ **增强AI上下文管理**: 改进session.py中的信息提取机制，支持从plan\['basic\_info']获取用户信息
- ✅ **完善PDF导出功能**: 修复PDF导出模块的导入问题，确保导出功能正常工作
- ✅ **优化ReAct代理提示词**: 在AI提示词中添加当前日期变量，提高天气查询的准确性
- ✅ **改进规划编辑器**: 增强plan\_editor.py的\_build\_plan\_summary方法，更好地整合用户信息到AI上下文中

## v1.0.0 (2025-08-31)

- ✅ 完成基础架构搭建
- ✅ 集成阿里云大模型
- ✅ 实现非遗项目分析
- ✅ 添加天气服务集成
- ✅ 完成API接口开发
- ✅ 实现细节条和结果展示
- ✅ 添加完整的测试覆盖

