# MarkPDFdown-MCP

> 基于 MCP 协议的云端 PDF 转 Markdown 服务，利用多模态大模型实现高精度文档转换

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-blue.svg)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

MarkPDFdown-MCP 是一个云端的 PDF 文档转换服务，通过多模态大模型（如 Gemini 3.0 Flash）将 PDF 文档转换为高质量的 Markdown 格式。项目提供 Web 界面和 MCP (Model Context Protocol) 服务，可独立部署或与 AI 助手（Claude Desktop、Cursor）集成。

## ✨ 核心特性

### 🎯 高精度转换
- 支持 PDF 文档转换为 Markdown
- 准确识别复杂布局、表格结构
- 保留 LaTeX 数学公式格式
- 图片和图表的智能识别

### 🌐 Web 服务
- **RESTful API**: 基于 FastAPI 的高性能接口
- **异步任务处理**: 支持大文件的并发转换
- **任务管理**: 完整的任务状态追踪和历史记录
- **自动清理**: 智能磁盘空间管理，可配置保留最近 N 条任务

### 🤖 AI 助手集成 (MCP)
- **MCP 协议支持**: 可连接到 Claude Desktop 或 Cursor
- **本地文件处理**: AI 助手可直接读取和转换本地 PDF 文件
- **无缝集成**: 在 AI 对话中直接调用转换服务

### 🐳 部署友好
- **Docker 一键部署**: 单条命令启动完整服务
- **服务器面板优化**: 兼容 1Panel、宝塔等面板
- **配置灵活**: 支持环境变量和 Web 界面配置

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

#### 前置要求
- Docker 20.10+
- Docker Compose 2.0+

#### 启动服务

```bash
# 克隆仓库
git clone https://github.com/KaolaMiao/markPDFdown-mcp.git
cd markPDFdown-mcp

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

服务启动后：
- 前端界面：http://localhost:18080
- 后端 API：http://localhost:18000
- 健康检查：http://localhost:18000/health

#### 配置 LLM 服务

访问 `http://localhost:18080`，在设置页面配置：
- **API Key**: 你的 LLM 服务密钥
- **Model**: 模型名称（如 `gemini-3.0-flash-exp`）
- **API Base**: LLM 服务地址（可选）

### 方式二：本地开发

#### 后端启动

```bash
cd backend

# 安装依赖（使用 uv）
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API_KEY 等配置

# 启动后端服务
uv run uvicorn src.api.main:app --reload --port 8000
```

#### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173 查看前端界面。

## 📚 使用指南

### Web 界面使用

1. **上传文件**: 拖拽 PDF 文件到上传区域
2. **选择模型**: 在设置中配置 LLM 模型
3. **开始转换**: 点击转换按钮
4. **下载结果**: 转换完成后下载 Markdown 文件

### MCP 协议集成

在 Claude Desktop 配置文件中添加：

```json
{
  "mcpServers": {
    "markpdfdown": {
      "command": "uv",
      "args": ["run", "python", "src/mcp_server.py"],
      "cwd": "/path/to/markPDFdown-mcp/backend",
      "env": {
        "API_BASE": "http://localhost:8000/api/v1"
      }
    }
  }
}
```

然后在对话中使用：
```
"请帮我把桌面上的 report.pdf 转换成 Markdown 格式"
```

### API 调用示例

```bash
# 上传 PDF
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@document.pdf"

# 查询任务状态
curl http://localhost:8000/api/v1/tasks/{task_id}

# 下载结果
curl http://localhost:8000/api/v1/tasks/{task_id}/download \
  -o output.md

# 列出所有任务
curl http://localhost:8000/api/v1/tasks?limit=10&skip=0
```

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI 0.109+ - 现代异步 Web 框架
- **数据库**: SQLite + SQLAlchemy 2.0 (async)
- **LLM 接口**: LiteLLM 1.18+ - 统一的多模型接口
- **PDF 处理**: PyMuPDF (fitz) - 高性能 PDF 解析
- **异步处理**: Python asyncio + BackgroundTasks

### 前端
- **框架**: React 19 + TypeScript
- **构建工具**: Vite 7
- **UI 组件**: Ant Design 6
- **状态管理**: React Hooks
- **HTTP 客户端**: Fetch API

### 部署
- **容器化**: Docker + Docker Compose
- **Web 服务器**: Nginx (前端)
- **进程管理**: Uvicorn (后端)

## 📁 项目结构

```
markPDFdown-mcp/
├── backend/                 # 后端服务
│   ├── src/
│   │   ├── api/            # FastAPI 路由和设置
│   │   ├── db/             # 数据库模型和连接
│   │   ├── worker/         # 异步任务处理器
│   │   └── mcp_server.py   # MCP 协议服务器
│   ├── tests/              # 后端测试
│   ├── Dockerfile          # 后端镜像构建
│   └── pyproject.toml      # Python 依赖配置
│
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── pages/          # 页面组件
│   │   └── services/       # API 客户端
│   ├── Dockerfile          # 前端镜像构建
│   └── package.json        # Node.js 依赖
│
├── markpdfdown_core/       # 核心转换库
│   └── src/markpdfdown/    # PDF 转换核心逻辑
│
├── docker-compose.yml      # 服务编排配置
├── CLAUDE.md              # Claude Code 开发指南
└── README.md              # 项目文档
```

## ⚙️ 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `API_KEY` | LLM 服务密钥 | - |
| `API_BASE` | LLM 服务地址 | - |
| `MODEL_NAME` | 模型名称 | `gemini-3.0-flash-exp` |
| `CONCURRENCY` | 并发处理数 | `2` |
| `MAX_TASKS` | 保留任务数 | `20` |
| `TEMPERATURE` | LLM 温度参数 | `0.3` |
| `MAX_TOKENS` | 最大 token 数 | `8192` |
| `USE_CELERY` | 是否使用 Celery | `false` |

### Web 界面配置

也可以在 Web 界面的设置页面修改上述配置，配置会持久化保存。

## 🔧 开发指南

### 运行测试

```bash
# 后端测试
cd backend
uv run pytest

# 前端测试
cd frontend
npm run test

# 测试覆盖率
npm run test:coverage
```

### 代码规范

```bash
# Python 代码检查
cd backend
uv run ruff check
uv run ruff format

# JavaScript 代码检查
cd frontend
npm run lint
```

详细的开发指南请参考 [CLAUDE.md](./CLAUDE.md)。

## 📖 API 文档

启动服务后，访问以下地址查看完整 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

主要端点：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/upload` | POST | 上传 PDF 文件 |
| `/api/v1/tasks` | GET | 获取任务列表 |
| `/api/v1/tasks/{id}` | GET | 获取任务详情 |
| `/api/v1/tasks/{id}/download` | GET | 下载转换结果 |
| `/api/v1/settings` | GET/POST | 获取/更新配置 |
| `/health` | GET | 健康检查 |

## 🗺️ 路线图

- [ ] **实时进度**: SSE 推送转换进度
- [ ] **双屏预览**: PDF 和 Markdown 并排预览
- [ ] **批量处理**: 支持多文件并发转换
- [ ] **多提供商**: OpenAI、Claude、Ollama 等
- [ ] **页码范围**: 支持指定页面转换
- [ ] **多语言**: 中英文界面支持

## ❓ 常见问题

### Q: 支持哪些 LLM 模型？

A: 通过 LiteLLM 支持，包括：
- Google Gemini: `gemini-3.0-flash-exp`, `gemini-pro-vision`
- OpenAI: `gpt-4o`, `gpt-4o-mini`
- Anthropic: `claude-3-5-sonnet`
- Ollama: `llava`, `llama3.2-vision`

### Q: 如何提高转换速度？

A: 可通过以下方式优化：
- 增加 `CONCURRENCY` 参数（并发处理页数）
- 使用更快的模型（如 Gemini Flash）
- 部署在性能更好的服务器

### Q: 转换失败怎么办？

A: 检查以下几点：
- API Key 是否正确
- 网络连接是否正常
- PDF 文件是否损坏
- 查看后端日志：`docker logs markpdfdown-backend`

### Q: 支持多大的 PDF 文件？

A: 理论上无限制，但建议：
- 单文件 < 100MB
- 页数 < 500 页
- 可通过分批上传大文件

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加某个功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

贡献指南请参考 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 📄 许可证

本项目采用 Apache License 2.0 开源协议。

Copyright 2025 KaolaMiao

本项目是基于 [MarkPDFdown](https://github.com/markpdfdown) 项目（Apache-2.0）的云端衍生版本。

## 🙏 致谢

感谢以下开源项目：

- **[MarkPDFdown/markpdfdown](https://github.com/markpdfdown/markpdfdown)** - 核心 PDF 转换算法
- **[MarkPDFdown/markpdfdown-desktop](https://github.com/markpdfdown/markpdfdown-desktop)** - 优秀的桌面版设计参考
- **FastAPI** - 现代化的 Python Web 框架
- **LiteLLM** - 统一的 LLM 接口
- **Ant Design** - 优秀的 React UI 组件库

## 📞 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/KaolaMiao/markPDFdown-mcp/issues)
- **功能建议**: [GitHub Discussions](https://github.com/KaolaMiao/markPDFdown-mcp/discussions)
- **邮箱**: (可选)

---

⭐ 如果这个项目对你有帮助，请给它一个 Star！
