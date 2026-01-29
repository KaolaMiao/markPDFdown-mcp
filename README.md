# MarkPDFdown 🚀

MarkPDFdown 是一个利用 **Gemini 3.0 Flash** 等多模态大模型，将 PDF 转换为高质量 Markdown 格式的开源系统。它能够精准识别复杂布局、表格、数学公式和图片。

## ✨ 主要功能

- **高精度转换**: 识别多栏布局、表格内容及 LaTeX 数学公式。
- **任务管理**: 完整的任务记录、状态监控及产物预览。
- **本地 & 远程协作**:
  - **Docker 一键部署**: 专为服务器面板（1Panel、宝塔）优化。
  - **MCP 协议支持**: 将你的转换服务器连接到 Claude Desktop 或 Cursor，实现 AI 驱动的文档处理流水线。
- **自动清理**: 智能硬盘保护，自动保留最近 N 条任务（如最近 20 条），防止服务器存储爆炸。

## 🚀 未来开发计划

本项目参考了 [MarkPDFdown Desktop](https://github.com/markpdfdown/markpdfdown-desktop) 的优秀设计，持续优化用户体验和功能完整性。

### Phase 1: 前端体验升级 🎨

**目标**: 提供媲美桌面版的用户界面和交互体验

- **任务管理优化**
  - [ ] 引入 Ant Design `Tag` 和 `Progress` 组件，美化任务状态显示
  - [ ] 添加任务操作入口：Preview（预览）、Retry（重试）、Delete（删除）
  - [ ] 实现任务列表的虚拟滚动，支持大量任务高效展示

- **实时进度反馈** ⭐ 核心功能
  - [ ] 实现 **SSE (Server-Sent Events)** 机制
  - [ ] 后端 `/api/v1/events` 端点推送 `task:progress` 和 `task:status` 事件
  - [ ] 前端 `useTaskEvents` Hook 自动更新任务状态，无需手动刷新
  - [ ] 实时显示当前处理页码和转换进度

- **双屏预览页面** (`/preview/:id`)
  - [ ] **左侧**: PDF 源文件图片预览（支持懒加载、缩放、旋转）
  - [ ] **右侧**: Markdown 渲染结果（支持语法高亮、LaTeX 公式）
  - [ ] **交互**: 可拖拽的分隔条调整左右宽度（使用 Ant Design `<Splitter>` 组件）
  - [ ] **导航**: 底部页码导航栏，支持快速跳转和逐页对比

### Phase 2: 后端架构增强 🔧

**目标**: 提升性能、可扩展性和稳定性

- **实时通信**
  - [ ] 实现基于 `asyncio` 的 SSE 事件流推送
  - [ ] 支持多客户端并发连接和断线重连

- **API 优化**
  - [ ] 分页 API: `GET /tasks/{id}/pages/{page}` - 避免一次性加载超大 JSON
  - [ ] 批量操作 API: 批量删除、批量重试
  - [ ] 文件流式传输: 支持大文件的流式上传和下载

- **任务管理**
  - [ ] 支持页码范围选择（如 "1-5, 8, 10-12"）
  - [ ] 任务优先级队列
  - [ ] 失败重试机制（指数退避策略）

### Phase 3: 高级功能 ✨

**参考桌面版的功能设计**

- **多提供商支持**
  - [ ] OpenAI、Anthropic Claude、Google Gemini、Ollama（本地模型）
  - [ ] 统一的 LLM 接口抽象（参考桌面版 `ILLMClient` 接口设计）
  - [ ] 动态切换模型和提供商

- **文件处理增强**
  - [ ] 图片文件支持（PNG、JPG）
  - [ ] Office 文档支持（Word、PPT）
  - [ ] 文件分割功能（按页码范围拆分 PDF）

- **多语言支持** (i18n)
  - [ ] 英文、简体中文、日语、俄语、阿拉伯语、波斯语
  - [ ] 使用 `react-i18next` 实现国际化

- **数据持久化升级**
  - [ ] 从 SQLite 迁移到 PostgreSQL（支持高并发）
  - [ ] 任务详情表：记录每页的转换状态和内容
  - [ ] 提供商和模型管理：动态配置 LLM 服务

### Phase 4: 企业级特性 🏢

**面向生产环境的增强**

- **安全与认证**
  - [ ] JWT 用户认证
  - [ ] API Key 管理
  - [ ] 文件访问权限控制

- **监控与日志**
  - [ ] 集成 Prometheus + Grafana 监控
  - [ ] 结构化日志（JSON 格式）
  - [ ] 任务执行统计和性能分析

- **可观测性**
  - [ ] 健康检查端点（`/health`）
  - [ ] OpenAPI/Swagger 文档
  - [ ] 错误追踪（Sentry 集成）

- **部署优化**
  - [ ] Kubernetes Helm Charts
  - [ ] 水平扩展支持（多实例负载均衡）
  - [ ] Redis 队列（替代 Celery，简化部署）

### 技术债务清理 🧹

- [ ] 完善单元测试覆盖率（目标：80%+）
- [ ] 集成测试和端到端测试
- [ ] 代码质量：ESLint、Ruff、Pre-commit hooks
- [ ] 文档完善：API 文档、部署指南、贡献指南

---

## 🛠️ 快速部署 (服务器端)

我们推荐使用 Docker Compose 在服务器上部署。

1. **上传代码**: 将项目上传至 `/opt/1panel/apps/markPDFdown`。
2. **初始化**:
   ```bash
   mkdir -p /opt/1panel/apps/markPDFdown/backend/files
   touch /opt/1panel/apps/markPDFdown/backend/tasks.db
   ```
3. **域名配置**: 建议使用 1Panel/宝塔 的“反向代理”将 `p2m.384921.XYZ` 指向容器端口 `18080`。

详细步骤请参阅：[**DEPLOY.md**](DEPLOY.md)

## 🤖 AI 助手集成 (MCP 服务)

让 AI 助手直接读取并转换你的本地 PDF：

1. **修改本地配置**:
   在 Claude Desktop 配置文件中添加：
   ```json
   {
     "mcpServers": {
       "markpdfdown": {
         "command": "uv",
         "args": ["run", "python", "src/mcp_server.py"],
         "cwd": "D:\\MyTools\\markPDFdown-mcp\\backend",
         "env": {
           "API_BASE": "http://p2m.384921.XYZ/api/v1"
         }
       }
     }
   }
   ```

2. **对话使用**:
   > "Claude，帮我把桌面上的合同.pdf 转换成 Markdown 内容。"

详细指南：[**mcp_install_guide.md**](mcp_install_guide.md)

## 📄 开源协议

本项目采用 **Apache License 2.0** 开源协议。

Copyright 2025 KaolaMiao

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

本项目是基于 [MarkPDFdown](https://github.com/markpdfdown) 项目（Apache-2.0）的衍生云端版本，
遵循原项目的开源协议要求，继续使用 Apache-2.0 协议。

## 🙏 致谢

### 原创项目

本项目基于以下优秀的开源项目进行开发：

- **[MarkPDFdown/markpdfdown](https://github.com/markpdfdown/markpdfdown)** - 核心转换逻辑库
  - 感谢原作者提供的基于多模态 LLM 的 PDF 转 Markdown 核心算法

- **[MarkPDFdown/markpdfdown-desktop](https://github.com/markpdfdown/markpdfdown-desktop)** - 桌面应用程序
  - 本项目的云端版本参考了桌面版的架构设计
  - 桌面版提供了优秀的用户体验设计，为后端 API 设计提供了参考

### 架构设计学习

桌面版采用了优秀的 **Clean Architecture（整洁架构）** 设计模式，本项目计划逐步借鉴其架构思想：

**核心架构层次**：
- **Domain Layer（领域层）**: 纯业务逻辑和接口定义，无外部依赖
  - 仓库接口（`TaskRepository`, `ProviderRepository`）
  - LLM 客户端接口（`ILLMClient`）
  - 分割器接口（`ISplitter`）
  - 页码范围解析器（`PageRangeParser`）

- **Application Layer（应用层）**: 应用业务逻辑和编排
  - Worker 协调器（`WorkerOrchestrator`）
  - 模型服务（`ModelService`）
  - 三个核心 Worker：
    - `SplitterWorker` - 文件分割（PDF → 图片）
    - `ConverterWorker` - 页面转换（图片 → Markdown）
    - `MergerWorker` - 结果合并（多页 → 完整文档）

- **Infrastructure Layer（基础设施层）**: 外部依赖实现
  - 数据库（Prisma + SQLite）
  - LLM 适配器（OpenAI、Claude、Gemini、Ollama）
  - 文件分割器（PDF Splitter、Image Splitter）
  - 文件服务（`FileService`）

- **Shared Layer（共享层）**: 跨层关注点
  - 事件总线（`EventBus`）用于 Worker 间通信

**关键技术亮点**：
- ✨ **优雅的依赖注入**: 使用依赖倒置原则，高层不依赖低层
- ✨ **事件驱动架构**: Worker 通过 EventBus 通信，解耦合
- ✨ **优雅关闭**: Worker 支持信号处理和资源清理
- ✨ **TypeScript 严格模式**: 类型安全，减少运行时错误
- ✨ **完整的测试覆盖**: 单元测试、集成测试、E2E 测试

同时感谢以下开源技术栈的支持：

- **FastAPI** - 现代化的 Python Web 框架
- **React + Ant Design** - 前端用户界面
- **LiteLLM** - 统一的 LLM 接口
- **MCP (Model Context Protocol)** - AI 助手集成协议

---

## 📞 联系方式

- 问题反馈：[GitHub Issues](https://github.com/KaolaMiao/markPDFdown-mcp/issues)
- 功能建议：[GitHub Discussions](https://github.com/KaolaMiao/markPDFdown-mcp/discussions)
