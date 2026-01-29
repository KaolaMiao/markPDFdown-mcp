# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

MarkPDFdown-MCP 是一个基于 MCP (Model Context Protocol) 的 PDF 转 Markdown 系统,采用 Monorepo 结构,包含三个主要模块:

- **markpdfdown_core**: Python 核心库,负责 PDF 解析、OCR 和转换逻辑
- **backend**: FastAPI 后端服务,提供 Web API 和任务调度
- **frontend**: React + Vite + Ant Design 前端界面

## 常用命令

### 后端开发

```bash
# 进入后端目录
cd backend

# 安装依赖 (使用 uv)
uv sync

# 运行开发服务器
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
uv run pytest

# 运行单个测试文件
uv run pytest tests/unit/test_models.py

# 运行测试并生成覆盖率报告
uv run pytest --cov=src --cov-report=html
```

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 构建生产版本
npm run build

# 运行测试
npm run test

# 代码检查
npm run lint
```

### Docker 部署

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 仅重新构建并启动后端
docker-compose up -d --build backend

# 仅重新构建并启动前端
docker-compose up -d --build frontend

# 查看后端日志
docker logs -f markpdfdown-backend

# 停止所有服务
docker-compose down
```

## 核心架构

### 架构模式

项目采用分层架构和依赖倒置原则:

1. **markpdfdown_core (领域层)**: 纯 Python 库,无 Web 框架依赖
   - `core/llm_client.py`: LiteLLM 集成,支持多模型提供商
   - `core/file_worker.py`: PDF/图片处理和转换逻辑
   - `config.py`: 配置管理

2. **backend (应用层)**: FastAPI Web 服务
   - `src/api/routes.py`: API 路由定义
   - `src/worker/smart_worker.py`: 异步任务处理器,使用流式管道
   - `src/db/models.py`: SQLAlchemy 数据模型
   - `src/mcp_server.py`: MCP 协议服务器实现

3. **frontend (表现层)**: React SPA
   - 使用 Ant Design 组件库
   - 通过 REST API 与后端通信

### 关键设计决策

#### 并发处理模式

后端支持两种任务执行模式,通过 `USE_CELERY` 环境变量控制:

- **Celery 模式** (`USE_CELERY=true`): 使用 Redis 作为消息队列,适合分布式部署
- **BackgroundTasks 模式** (`USE_CELERY=false`): 使用 FastAPI BackgroundTasks,适合单机部署

**当前生产环境默认使用 BackgroundTasks 模式**,无需额外依赖 Redis。

#### 流式处理架构

`SmartWorker` 使用生成器模式实现流式处理:

```python
# worker/smart_worker.py
# 1. PDF 转图片是流式的 (生成器逐页产生)
image_gen = worker.convert_to_images()

# 2. 图片转 Markdown 并发处理
for i, img_path in enumerate(image_gen):
    task = asyncio.create_task(_wrapped_convert(i, img_path))
    tasks.append(task)

# 3. 结果按索引排序,保证页面顺序
sorted_results = sorted(results, key=lambda x: x[0])
```

这种设计的优势:
- 立即开始转换,无需等待所有图片生成完成
- 内存占用低,逐页处理
- 并发控制通过 Semaphore 实现

#### 数据库设计

- 使用 SQLite + SQLAlchemy (async)
- 任务模型: `Task` (id, file_name, status, result_path, created_at)
- 状态枚举: `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`
- 自动清理: 保留最近 N 条任务 (通过 `maxTasks` 配置)

#### 文件存储策略

```
backend/files/
├── tasks/
│   ├── {task_id}/
│   │   ├── original.pdf      # 原始上传文件
│   │   ├── page_0.png        # 渲染的页面图片
│   │   ├── page_1.png
│   │   └── result.md         # 转换结果
```

每个任务使用独立目录,便于清理和隔离。

### MCP 协议集成

MCP 服务器 (`src/mcp_server.py`) 提供 4 个工具:

1. **convert_pdf**: 上传 PDF → 轮询状态 → 返回 Markdown 内容
2. **list_tasks**: 列出服务器上的任务
3. **get_task_content**: 获取指定任务的 Markdown 内容
4. **download_file**: 下载任务结果到本地文件

**关键配置**:
```json
{
  "mcpServers": {
    "markpdfdown": {
      "command": "uv",
      "args": ["run", "python", "src/mcp_server.py"],
      "cwd": "D:\\MyTools\\markPDFdown-mcp\\backend",
      "env": {
        "API_BASE": "http://your-server.com/api/v1"
      }
    }
  }
}
```

**注意**: MCP 服务器使用 `trust_env=False` 禁用系统代理,避免代理配置导致的 502 错误。

### 模型提供商支持

通过 LiteLLM 支持多种 LLM 提供商:

- **OpenAI**: `gpt-4o`, `gpt-4o-mini`
- **Anthropic**: `claude-3-5-sonnet`
- **Google Gemini**: `gemini-2.0-flash-exp` (需要添加 `gemini/` 前缀)
- **Ollama**: 本地模型

**模型名称格式处理** (`worker/smart_worker.py:18-30`):
```python
if model_name.startswith("gemini") and not model_name.startswith("gemini/"):
    model_name = f"gemini/{model_name}"
```

## 开发工作流

### 修改核心转换逻辑

1. 修改 `markpdfdown_core/src/` 中的代码
2. 后端会自动使用更新后的核心库 (PYTHONPATH 包含核心库路径)
3. 重启后端服务: `docker-compose restart backend`

### 添加新的 API 端点

1. 在 `backend/src/api/routes.py` 定义路由
2. 在 `backend/src/api/main.py` 注册路由 (通过 router 自动包含)
3. 更新前端服务 (`frontend/src/services/api.ts`) 以调用新端点

### 添加新的 LLM 提供商

1. 在 `markpdfdown_core/src/core/llm_client.py` 添加支持
2. 在 `backend/src/worker/smart_worker.py` 添加模型名称格式化规则
3. 更新环境变量映射逻辑

## 环境配置

### 后端环境变量

```bash
# API 配置
API_KEY=your-api-key
API_BASE=http://localhost:8000/api/v1

# 模型配置
MODEL_NAME=gemini-2.0-flash-exp
TEMPERATURE=0.3
MAX_TOKENS=8192
RETRY_TIMES=3

# 并发配置
CONCURRENCY=2  # 并发处理的页面数

# 任务管理
MAX_TASKS=20  # 保留最近 20 条任务

# 执行模式
USE_CELERY=false  # 生产环境使用 false
```

### 配置持久化

后端配置通过 `backend/src/api/settings.py` 模块管理:

- `load_settings_from_env()`: 从 `.env` 文件加载
- `save_settings_to_env()`: 保存到 `.env` 文件
- 前端通过 `/api/v1/settings` 端点管理配置

**注意**: `.env` 文件通过 Docker Volume 持久化,重启容器不会丢失配置。

## 测试策略

### 后端测试

- **单元测试**: `tests/unit/` - 测试模型、worker 逻辑
- **集成测试**: `tests/integration/` - 测试 API 端点
- **测试配置**: `tests/conftest.py` - 设置 PYTHONPATH

运行测试时,确保设置正确的 Python 路径:
```python
# conftest.py
sys.path.append(str(src_path))  # backend/src
sys.path.append(str(core_path))  # markpdfdown_core/src
```

### 前端测试

- 使用 Vitest + Testing Library
- 测试文件: `src/services/__tests__/`
- 运行: `npm run test`

## 故障排查

### 后端启动失败

```bash
# 检查日志
docker logs -f markpdfdown-backend

# 常见问题:
# 1. PYTHONPATH 错误 → 确保 docker-compose.yml 中环境变量正确
# 2. markpdfdown_core 未找到 → 确保 Docker 构建上下文为根目录
# 3. 数据库权限问题 → 检查 tasks.db 文件权限
```

### 前端无法连接后端

```bash
# 检查网络
docker ps  # 确认容器运行
docker network inspect markpdfdown-mcp_default

# 检查 nginx 配置 (frontend/nginx.conf)
# 确保反向代理正确配置: proxy_pass http://backend:8000
```

### 转换任务失败

```bash
# 查看 SmartWorker 日志
docker logs markpdfdown-backend | grep "Processing file"

# 常见原因:
# 1. API_KEY 无效 → 检查 .env 配置
# 2. 模型名称格式错误 → 检查是否添加 provider/ 前缀
# 3. 并发过高 → 降低 CONCURRENCY 值
# 4. 文件损坏 → 检查 PDF 是否能正常打开
```

## 重要文件路径

```
markPDFdown-mcp/
├── markpdfdown_core/src/          # 核心库源码
│   ├── markpdfdown/
│   │   ├── core/
│   │   │   ├── llm_client.py     # LLM 客户端
│   │   │   └── file_worker.py    # 文件处理
│   │   └── config.py             # 配置管理
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── main.py           # FastAPI 应用入口
│   │   │   ├── routes.py         # API 路由
│   │   │   └── settings.py       # 配置管理
│   │   ├── worker/
│   │   │   └── smart_worker.py   # 核心转换逻辑
│   │   ├── db/
│   │   │   ├── models.py         # SQLAlchemy 模型
│   │   │   └── database.py       # 数据库连接
│   │   └── mcp_server.py         # MCP 服务器
│   ├── Dockerfile                # 后端镜像构建
│   ├── files/                    # 文件存储 (持久化)
│   ├── tasks.db                  # SQLite 数据库 (持久化)
│   └── .env                      # 环境配置 (持久化)
├── frontend/
│   ├── src/
│   │   ├── services/api.ts       # API 客户端
│   │   └── App.tsx               # 应用入口
│   ├── Dockerfile                # 前端镜像构建
│   └── nginx.conf                # Nginx 配置
└── docker-compose.yml            # 服务编排
```

## 依赖关系

```
frontend → backend (REST API)
backend → markpdfdown_core (Python 导入)
```

**重要**: 后端的 Docker 构建上下文必须为项目根目录,以便访问 `markpdfdown_core`。

## 版本控制

- Python: 3.10+
- Node.js: 18+
- Docker: Compose v3.8+
