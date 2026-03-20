# 更新日志

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
- ✅ **移除冗余会话存储**: 删除 PlanEditor 中的 active_sessions，统一使用 SessionPool
- ✅ **优化会话上下文提取**: 改进 _extract_core_info 方法，支持从 plan['basic_info'] 获取用户信息
- ✅ **完善会话管理API**: 更新所有会话相关方法的调用，确保使用统一的 SessionPool 接口

## v1.1.1 (2025-10-15)

- ✅ **修复用户信息传递问题**: AI现在能够正确获取用户的出发地、交通方式、人数、预算等完整信息
- ✅ **修复天气日期计算**: 优化天气服务中的日期计算逻辑，确保天气查询使用正确的日期
- ✅ **增强AI上下文管理**: 改进session.py中的信息提取机制，支持从plan['basic_info']获取用户信息
- ✅ **完善PDF导出功能**: 修复PDF导出模块的导入问题，确保导出功能正常工作
- ✅ **优化ReAct代理提示词**: 在AI提示词中添加当前日期变量，提高天气查询的准确性
- ✅ **改进规划编辑器**: 增强plan_editor.py的_build_plan_summary方法，更好地整合用户信息到AI上下文中

## v1.0.0 (2025-08-31)
- ✅ 完成基础架构搭建
- ✅ 集成阿里云大模型
- ✅ 实现非遗项目分析
- ✅ 添加天气服务集成
- ✅ 完成API接口开发
- ✅ 实现细节条和结果展示
- ✅ 添加完整的测试覆盖