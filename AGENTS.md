# MarkPDFdown-MCP 开发流程手册

> 🤖 **给 AI 助手和人类初学者的完整开发指南**
>
> 本文档提供详细的功能开发流程，确保每个功能分支的开发、测试和提交都符合最佳实践。

---

## 📚 目录

1. [项目概述](#项目概述)
2. [技术栈](#技术栈)
3. [开发环境配置](#开发环境配置)
4. [通用开发流程](#通用开发流程)
5. [功能分支详细规划](#功能分支详细规划)
6. [代码提交规范](#代码提交规范)
7. [测试标准](#测试标准)
8. [完成与合并条件](#完成与合并条件)
9. [常见问题](#常见问题)

---

## 项目概述

### 项目结构

```
markPDFdown-mcp/
├── backend/                 # FastAPI 后端服务
│   ├── src/
│   │   ├── api/            # API 路由和配置
│   │   ├── db/             # 数据库模型
│   │   ├── worker/         # 异步任务处理
│   │   └── mcp_server.py   # MCP 服务器
│   ├── tests/              # 后端测试
│   └── pyproject.toml      # Python 依赖
│
├── frontend/               # React 前端应用
│   ├── src/
│   │   ├── components/     # React 组件
│   │   ├── pages/          # 页面组件
│   │   └── services/       # API 客户端
│   └── package.json        # Node.js 依赖
│
├── markpdfdown_core/       # 核心转换库
│   └── src/markpdfdown/
│       └── core/           # PDF 转换核心逻辑
│
└── desktop_study/          # 参考项目（学习用）
```

### 开发原则

1. **小步快跑**：每个功能分成多个小提交
2. **测试优先**：先写测试，确保功能正常
3. **参考学习**：从 `desktop_study` 项目复制成熟实现
4. **本地验证**：本地测试通过后再提交
5. **分支隔离**：每个功能独立分支开发

---

## 技术栈

### 后端技术栈

```yaml
框架: FastAPI 0.109+
数据库: SQLite + SQLAlchemy 2.0 (async)
异步处理: asyncio + BackgroundTasks
LLM 接口: LiteLLM 1.18+
PDF 处理: PyMuPDF (fitz)
测试框架: pytest + pytest-asyncio
包管理: uv
```

### 前端技术栈

```yaml
框架: React 19 + TypeScript
构建工具: Vite 7
UI 组件: Ant Design 6
状态管理: React Hooks
HTTP 客户端: Fetch API
测试框架: Vitest + Testing Library
包管理: npm
```

### 通信模式

```yaml
API 风格: RESTful
实时通信: Server-Sent Events (SSE)
数据格式: JSON
文件上传: multipart/form-data
```

---

## 开发环境配置

### ⚠️ 重要提示

**不要使用 Docker 进行本地开发！** 直接在本地启动服务。

### 后端环境配置

```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖（使用 uv）
uv sync

# 3. 创建环境配置文件
cp .env.example .env

# 4. 编辑 .env 文件
# 至少配置以下变量：
API_KEY=your-api-key-here
MODEL_NAME=gemini-2.0-flash-exp
API_BASE=
CONCURRENCY=2
MAX_TASKS=20
TEMPERATURE=0.3
MAX_TOKENS=8192

# 5. 启动开发服务器
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**验证后端启动成功**：
- 访问 http://localhost:8000/docs 看到 Swagger UI
- 访问 http://localhost:8000/health 返回 `{"status": "ok"}`

### 前端环境配置

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

**验证前端启动成功**：
- 访问 http://localhost:5173 看到前端界面
- 控制台无错误信息

### 常用开发命令

```bash
# === 后端 ===
cd backend

# 启动开发服务器
uv run uvicorn src.api.main:app --reload --port 8000

# 运行所有测试
uv run pytest

# 运行单个测试文件
uv run pytest tests/unit/test_worker.py

# 运行测试并生成覆盖率报告
uv run pytest --cov=src --cov-report=html

# 代码格式化
uv run ruff format .

# 代码检查
uv run ruff check .

# === 前端 ===
cd frontend

# 启动开发服务器
npm run dev

# 运行测试
npm run test

# 代码检查
npm run lint

# 构建生产版本
npm run build
```

---

## 通用开发流程

### 📋 标准开发流程（7步骤）

```
步骤 1: 创建功能分支
    ↓
步骤 2: 研究参考实现（desktop_study）
    ↓
步骤 3: 实现功能（分小块，多次提交）
    ↓
步骤 4: 本地测试
    ↓
步骤 5: 代码提交（使用 smart-commit 技能）
    ↓
步骤 6: 完整验证
    ↓
步骤 7: 创建 PR 或合并分支
```

### 步骤 1: 创建功能分支

```bash
# 确保在 main 分支且代码最新
git checkout main
git pull origin main

# 创建功能分支（命名规范：feature/功能名）
git checkout -b feature/realtime-progress
```

**分支命名规范**：
- `feature/realtime-progress` - 实时进度
- `feature/dual-preview` - 双屏预览
- `feature/batch-processing` - 批量处理
- `feature/multi-provider` - 多提供商
- `feature/page-range` - 页码范围
- `feature/i18n` - 多语言支持

### 步骤 2: 研究参考实现

在 `desktop_study/` 目录中查找相关实现：

```bash
# 方法 1: 使用 grep 搜索关键词
cd desktop_study
grep -r "SSE\|EventSource" src/
grep -r "进度\|progress" src/

# 方法 2: 查找相关文件名
find . -name "*progress*" -o -name "*event*"

# 方法 3: 使用 Claude Code 的 Task tool
"在 desktop_study 中查找实时进度推送的实现"
```

**研究要点**：
- 理解核心逻辑
- 找出关键代码文件
- 确定技术方案
- 适配到当前项目

### 步骤 3: 实现功能（分小块）

**重要**：每个小功能点单独提交，不要攒到最后！

**示例：实时进度功能分解**
```
提交 1: 添加后端 SSE 端点基础结构
提交 2: 实现进度事件生成逻辑
提交 3: 前端创建 SSE 连接 Hook
提交 4: 前端进度条组件集成
提交 5: 错误处理和重连逻辑
提交 6: 添加单元测试
```

### 步骤 4: 本地测试

**每次修改后必须测试**：

```bash
# 后端测试
cd backend
uv run pytest

# 前端测试
cd frontend
npm run test

# 手动功能测试
# 1. 启动后端和前端
# 2. 打开浏览器访问 http://localhost:5173
# 3. 测试新功能是否正常工作
```

### 步骤 5: 代码提交

使用 `smart-commit` 技能自动提交：

```
"帮我提交代码"
```

**技能会自动**：
- 分析修改内容
- 询问修改类型
- 生成规范的提交信息
- 执行 git pull → add → commit → push

### 步骤 6: 完整验证

**整个功能开发完成后**：

```bash
# 运行完整测试套件
cd backend
uv run pytest --cov=src

# 确认输出类似：
# ========== 45 passed in 12.34s ==========
# coverage: 87%

# 只有看到测试通过的输出，才能说"测试通过"
```

**手动验证清单**：
- [ ] 所有单元测试通过
- [ ] 手动测试核心功能
- [ ] 测试边界情况（错误、断网、大文件等）
- [ ] 确认没有性能问题
- [ ] 代码符合项目规范

### 步骤 7: 创建 PR 或合并

使用 `finishing-a-development-branch` 技能：

```
"功能开发完成，帮我处理分支"
```

**选择选项**：
1. **选项 1**: 本地合并到 main（适合小功能）
2. **选项 2**: 创建 PR（推荐，适合重要功能）

---

## 功能分支详细规划

### 📊 功能实现进度总览

#### ✅ 已完成功能

- ✅ **功能 0.1**: 原子文件操作（数据安全）
- ✅ **功能 0.2**: Token 统计和追踪
- ✅ **功能 0.3**: 数据库模式扩展
- ✅ **功能 1.1**: SSE 实时进度推送（后端）
- ✅ **功能 1.2**: 实时页面预览（前端 + 后端）
- ✅ **功能 1.3**: 单页重新生成
- ✅ **功能 1.4**: 前端进度条 UI 组件
- ✅ **功能 2.1**: 双屏预览（PDF + Markdown）
- ✅ **功能 3**: 批量处理（支持多文件上传和并发转换）
- ✅ **功能 3.1**: 任务删除功能（带状态检查和安全验证）
- ✅ **功能 4.1**: 多提供商支持（OpenAI/Claude/Gemini）
- ✅ **文档完善**: 专业 API 文档（API.md）和开发指南更新

#### 🚧 开发中功能

- 🚧 **功能 2.2**: 同步滚动优化

#### 📋 计划中功能

- 📋 **功能 5**: 页码范围选择
- 📋 **功能 6**: 多语言支持 (i18n)

---

### 功能 0: 核心基础设施 ✅ (已完成)

#### 实现内容

**任务 0.1: 原子文件操作** ✅
- 所有文件写入使用临时文件 + `os.replace()`
- 防止进程崩溃时的数据损坏
- 覆盖范围：单页 markdown、最终合并文件、重新生成文件

**文件位置**:
- `backend/src/worker/smart_worker.py:126-131` - 单页保存
- `backend/src/worker/tasks.py:74-77` - 最终文件保存
- `backend/src/worker/tasks.py:158-165, 216-219` - 重新生成文件保存

**任务 0.2: Token 统计和追踪** ✅
- 完整的 token 使用统计（input_tokens, output_tokens, total_tokens）
- 主流程和重新生成流程都正确更新
- 数据一致性保证（input + output = total）

**文件位置**:
- `backend/src/worker/smart_worker.py:94-109` - Token 累积逻辑
- `backend/src/worker/tasks.py:82-84` - 主流程更新
- `backend/src/worker/tasks.py:241-248` - 重新生成更新

**任务 0.3: 数据库模式扩展** ✅
- 新增字段：started_at, completed_at, input_tokens, output_tokens, total_tokens
- 提供数据库迁移脚本
- 向后兼容，所有字段可空

**文件位置**:
- `backend/src/db/models.py` - 扩展任务模型
- `backend/scripts/migrate_add_token_stats.py` - 迁移脚本

#### 完成条件

- [x] 所有文件操作都是原子的
- [x] Token 统计数据一致性
- [x] 数据库迁移脚本提供
- [x] 向后兼容
- [x] 通过代码审查（评分 A-）

---

### 功能 1.1-1.3: 实时预览和单页重新生成 ✅ (已完成)

**目标**: 实时查看转换进度和结果，支持单页重新生成

#### 技术方案

```yaml
后端:
  - SSE 事件管理器（线程安全队列）
  - 页面内容获取端点（图片 + Markdown）
  - 单页重新生成端点
  - 流式处理架构

前端:
  - 页面预览组件（MarkdownPreview.tsx）
  - PDF 查看器组件（PDFViewer.tsx）
  - 双栏对比页面（Preview.tsx）
  - API 客户端扩展
```

#### 实现的任务

**任务 1.1.1: SSE 事件管理器** ✅
- 创建 `backend/src/api/sse_manager.py`
- 线程安全的队列管理
- 心跳机制（30s 超时）
- 自动清理断开连接的客户端
- 队列溢出保护（最多 100 条事件）

**任务 1.1.2: 页面预览端点** ✅
- `GET /api/v1/tasks/{task_id}/pages/{page_num}` - 获取页面渲染图片
- `GET /api/v1/tasks/{task_id}/pages/{page_num}/content` - 获取页面 Markdown
- 支持流式预览（每页完成后立即可查看）
- 完善的输入验证（page_num: 1-10000）

**文件位置**:
- `backend/src/api/routes.py:211-253` - 页面图片端点
- `backend/src/api/routes.py:256-328` - 页面内容端点

**任务 1.1.3: 单页重新生成** ✅
- `POST /api/v1/tasks/{task_id}/pages/{page_num}/regenerate`
- 使用 `_convert_one()` 方法处理单页图片
- 自动合并所有页面为最终 markdown
- Token 统计正确累加

**文件位置**:
- `backend/src/api/routes.py:331-396` - 重新生成端点
- `backend/src/worker/tasks.py:101-255` - 重新生成逻辑

**关键修复**:
- 修复竞态条件：改用 `_convert_one()` 而非 `process_file()`
- 原子文件操作：所有写入都使用 `os.replace()`
- 严格文件匹配：`page_[0-9][0-9][0-9][0-9].md` 模式
- Token 统计一致性：同步更新三个字段

**任务 1.1.4: 流式处理架构** ✅
- 每转换完一页立即保存 `page_XXXX.md`
- 支持实时预览，无需等待全部完成
- 最后合并所有页面为最终文件
- 并发控制通过 Semaphore 实现

**文件位置**:
- `backend/src/worker/smart_worker.py:82-156` - 流式处理逻辑

**任务 1.2.1: 前端预览组件** ✅
- `MarkdownPreview.tsx` - Markdown 渲染组件
- `PDFViewer.tsx` - PDF 查看器组件
- `Preview.tsx` - 双栏对比页面

**文件位置**:
- `frontend/src/components/MarkdownPreview.tsx`
- `frontend/src/components/PDFViewer.tsx`
- `frontend/src/pages/Preview.tsx`

**任务 1.2.2: API 客户端扩展** ✅
- `getPageImage()` - 获取页面图片
- `getPageContent()` - 获取页面 Markdown
- `regeneratePage()` - 重新生成页面

**文件位置**:
- `frontend/src/services/api.ts`

#### 完成条件

- [x] SSE 事件管理器实现
- [x] 页面预览端点正常工作
- [x] 单页重新生成功能正常
- [x] 流式处理架构实现
- [x] 前端预览组件实现
- [x] 所有文件操作原子化
- [x] Token 统计数据一致
- [x] 完善的错误处理和日志
- [x] 通过代码审查（评分 A-）

#### 测试验证

```bash
# 测试页面预览
curl http://localhost:8000/api/v1/tasks/{task_id}/pages/1

# 测试单页重新生成
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/pages/1/regenerate

# 手动测试
1. 上传 PDF 文件
2. 转换过程中访问 /preview/{task_id}
3. 查看实时预览效果
4. 测试单页重新生成功能
```

#### 参考文件

无参考实现，全新开发。

---

### 功能 1: 实时进度 (SSE)

**目标**: 用户上传 PDF 后，实时看到转换进度（百分比、当前页码）

#### 技术方案

```yaml
后端:
  - 使用 Server-Sent Events (SSE) 推送进度
  - 在 SmartWorker 中添加进度回调
  - 创建 /api/v1/events 端点

前端:
  - 使用 EventSource API 连接 SSE
  - 创建 useTaskProgress Hook
  - 进度条组件实时更新
```

#### 开发任务分解

**任务 1.1: 后端 SSE 端点** (预计 2-3 次提交)

```python
# backend/src/api/routes.py
from fastapi.responses import StreamingResponse

@app.get("/api/v1/events")
async def task_events():
    """SSE 端点，推送任务进度"""
    async def event_generator():
        # SSE 实现逻辑
        yield "data: {\"progress\": 10, \"page\": 1}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**测试**：
```bash
# 测试 SSE 端点
curl -N http://localhost:8000/api/v1/events
```

**任务 1.2: 进度事件生成** (预计 2-3 次提交)

```python
# backend/src/worker/smart_worker.py
class SmartWorker:
    async def convert_to_images(self, progress_callback=None):
        """添加进度回调参数"""
        for i, page in enumerate(pdf_file):
            # 转换页面
            # 调用进度回调
            if progress_callback:
                await progress_callback({
                    "current": i + 1,
                    "total": total_pages,
                    "progress": (i + 1) / total_pages * 100
                })
```

**任务 1.3: 前端 SSE Hook** (预计 2-3 次提交)

```typescript
// frontend/src/hooks/useTaskProgress.ts
export function useTaskProgress(taskId: string) {
  const [progress, setProgress] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);

  useEffect(() => {
    const eventSource = new EventSource(
      `http://localhost:8000/api/v1/events?task_id=${taskId}`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.progress);
      setCurrentPage(data.page);
    };

    return () => eventSource.close();
  }, [taskId]);

  return { progress, currentPage };
}
```

**任务 1.4: 进度条 UI** (预计 1-2 次提交)

```tsx
// frontend/src/components/ProgressBar.tsx
export function ProgressBar({ progress, currentPage, totalPages }) {
  return (
    <div>
      <Progress percent={progress} />
      <span>{currentPage} / {totalPages}</span>
    </div>
  );
}
```

**任务 1.5: 错误处理和重连** (预计 1-2 次提交)

```typescript
// 添加断线重连逻辑
eventSource.onerror = () => {
  eventSource.close();
  // 延迟重连
  setTimeout(() => {
    const newSource = new EventSource(...);
  }, 3000);
};
```

**任务 1.6: 单元测试** (预计 2-3 次提交)

```python
# backend/tests/test_sse.py
async def test_sse_endpoint():
    """测试 SSE 端点"""
    async with httpx.AsyncClient() as client:
        response = await client.get("/api/v1/events")
        assert response.status_code == 200
```

#### 完成条件

- [x] 后端 SSE 端点正常工作
- [x] 进度实时更新到前端
- [x ] 进度条显示正确百分比
- [x] 连接断开后自动重连
- [x] 所有单元测试通过
- [x] 手动测试：上传 PDF，看到进度实时更新

#### 参考文件

```bash
# desktop_study 中查找
desktop_study/src/services/ProgressService.ts
desktop_study/src/hooks/useProgress.ts
```

---

### 功能 2: 双屏预览 ✅ (部分完成)

**目标**: 左侧显示 PDF 原文，右侧显示 Markdown 转换结果

**完成状态**:
- ✅ 后端页面图片端点已实现
- ✅ 前端双栏布局已实现
- ✅ PDF 查看器组件已实现
- ✅ Markdown 渲染组件已实现
- 🚧 同步滚动待优化
- 🚧 响应式布局待完善

#### 技术方案

```yaml
后端:
  - 添加 /api/v1/pages/{task_id}/{page_num} 端点
  - 返回指定页面的图片

前端:
  - 使用 React-PDF 或 iframe 显示 PDF
  - 使用 Split 画布组件实现左右分栏
  - 同步滚动和页面切换
```

#### 开发任务分解

**任务 2.1: 后端页面图片端点** (2-3 次提交)

```python
# backend/src/api/routes.py
@app.get("/api/v1/pages/{task_id}/{page_num}")
async def get_page_image(task_id: str, page_num: int):
    """获取指定页面的渲染图片"""
    image_path = f"backend/files/tasks/{task_id}/page_{page_num}.png"
    return FileResponse(image_path)
```

**任务 2.2: 前端分栏布局** (1-2 次提交)

```tsx
// frontend/src/components/SplitView.tsx
import { SplitPane } from 'react-split-pane';

export function SplitView({ pdfUrl, markdown }) {
  return (
    <SplitPane split="vertical" defaultSize="50%">
      <PDFViewer url={pdfUrl} />
      <MarkdownViewer content={markdown} />
    </SplitPane>
  );
}
```

**任务 2.3: PDF 查看器** (2-3 次提交)

```tsx
// frontend/src/components/PDFViewer.tsx
export function PDFViewer({ url }) {
  return (
    <iframe
      src={url}
      style={{ width: '100%', height: '100vh' }}
    />
  );
}
```

**任务 2.4: 同步滚动** (2-3 次提交)

```tsx
// 实现左右联动滚动
const handleScrollLeft = () => {
  // 计算滚动比例，同步右侧
};

const handleScrollRight = () => {
  // 计算滚动比例，同步左侧
};
```

**任务 2.5: 页码切换** (1-2 次提交)

```tsx
// 添加页面导航
export function PageNavigation({ currentPage, totalPages, onPageChange }) {
  return (
    <div>
      <Button onClick={() => onPageChange(currentPage - 1)}>上一页</Button>
      <span>{currentPage} / {totalPages}</span>
      <Button onClick={() => onPageChange(currentPage + 1)}>下一页</Button>
    </div>
  );
}
```

#### 完成条件

- [x] 左右分栏显示正确
- [x] PDF 加载正常
- [x] Markdown 渲染正确
- [x] 同步滚动流畅
- [x] 页面切换正常
- [x] 响应式布局（移动端适配）

---

### 功能 3: 批量处理 ✅ (已完成)

**目标**: 支持一次上传多个 PDF 文件，并发转换，并提供任务管理功能

#### 实现内容

**任务 3.1: 批量上传端点** ✅
- `POST /api/v1/upload/batch` - 批量上传多个 PDF 文件
- 支持最多 10 个文件同时上传
- 文件大小限制：每个文件最大 50MB
- 防止 DOS 攻击的安全验证

**文件位置**:
- `backend/src/api/routes.py:155-218` - 批量上传端点
- `backend/src/api/routes.py:20-22` - 安全限制常量

**任务 3.2: 并发控制** ✅
- 使用全局 `asyncio.Semaphore` 控制并发任务数
- 可配置的并发限制（通过 `MAX_CONCURRENT_TASKS` 环境变量）
- 自动清理旧任务机制

**文件位置**:
- `backend/src/worker/tasks.py:27-38` - 全局信号量定义
- `backend/src/worker/tasks.py:47-72` - 并发处理逻辑

**任务 3.3: 删除任务功能** ✅
- `DELETE /api/v1/tasks/{task_id}` - 删除指定任务
- 状态检查：防止删除正在处理的任务（HTTP 409）
- 级联删除：数据库记录和文件系统目录
- 完善的错误处理

**文件位置**:
- `backend/src/api/routes.py:247-275` - 删除端点

**任务 3.4: 前端批量上传** ✅
- `BatchUploadScheduler` 类：智能批量上传调度器
- 100ms 防抖优化：自动合并连续上传
- 单文件/批量模式自动切换
- 拖拽上传支持

**文件位置**:
- `frontend/src/components/UploadZone.tsx:12-79` - 批量上传调度器

**任务 3.5: 前端任务管理** ✅
- 任务列表显示每个文件的状态
- 删除确认对话框（防止误操作）
- 实时进度更新（SSE 集成）
- 视觉状态指示器（图标 + Tooltip）
- 改进的表格布局和样式

**文件位置**:
- `frontend/src/components/TaskTable.tsx` - 任务表格组件
- `frontend/src/services/api.ts:49-58` - 批量和删除 API 方法

**任务 3.6: API 客户端扩展** ✅
- `ApiClient.uploadFiles()` - 批量上传方法
- `ApiClient.deleteTask()` - 删除任务方法
- 完整的 TypeScript 类型定义

**文件位置**:
- `frontend/src/services/api.ts` - API 客户端

#### 关键特性

**安全性**:
- ✅ 文件数量限制（最多 10 个）
- ✅ 文件大小限制（每个 50MB）
- ✅ 防止删除正在处理的任务
- ✅ 文件类型验证（仅 PDF）

**用户体验**:
- ✅ 智能防抖（100ms）
- ✅ 单文件/批量模式自动切换
- ✅ 删除确认对话框
- ✅ 实时进度显示
- ✅ 视觉状态指示器

**性能优化**:
- ✅ 批量上传减少 HTTP 开销
- ✅ 并发处理提高吞吐量
- ✅ 信号量控制资源使用
- ✅ 自动清理旧任务

#### 完成条件

- [x] 支持一次选择多个 PDF（最多 10 个）
- [x] 并发处理提高效率（可配置并发数）
- [x] 每个任务状态独立显示
- [x] 删除任务功能（带状态检查）
- [x] 错误隔离（单个失败不影响其他）
- [x] 安全限制（文件数量和大小）
- [x] 代码审查通过（评分 9/10）

#### 代码审查结果

**最终评分**: 9/10 (优秀)

**关键修复**:
1. 防止删除正在处理的任务（HTTP 409 Conflict）
2. 添加批量上传安全限制（文件数量和大小）
3. 改进错误日志记录（使用 logger 而非 print）

**测试验证**:
```bash
# 测试批量上传
curl -X POST http://localhost:8000/api/v1/upload/batch \
  -F "files=@test1.pdf" \
  -F "files=@test2.pdf"

# 测试删除任务（应返回 409 如果正在处理）
curl -X DELETE http://localhost:8000/api/v1/tasks/{task_id}

# 测试文件数量限制（应返回 400）
curl -X POST http://localhost:8000/api/v1/upload/batch \
  -F "files=@test1.pdf" \
  -F "files=@test2.pdf" \
  ... (11 个文件)
```

#### 参考实现
无参考实现，全新开发。结合了 FastAPI 批量上传最佳实践和 React Ant Design 组件库模式。

---

## 功能 4: 多提供商支持 ✅ (部分完成)

**目标**: 支持切换不同的 LLM 提供商（OpenAI、Claude、Ollama）

#### 技术方案

```yaml
后端:
  - 修改 /api/v1/upload 支持多文件
  - 使用 asyncio 并发处理
  - 添加批量任务状态追踪

前端:
  - 支持拖拽多文件
  - 显示每个文件的任务状态
  - 批量下载功能
```

#### 开发任务分解

**任务 3.1: 后端多文件上传** (2-3 次提交)

```python
# backend/src/api/routes.py
from fastapi import UploadFile, List

@app.post("/api/v1/upload/batch")
async def upload_batch(files: List[UploadFile]):
    """批量上传 PDF"""
    tasks = []
    for file in files:
        task_id = await create_task(file)
        tasks.append(task_id)
    return {"task_ids": tasks}
```

**任务 3.2: 并发处理逻辑** (2-3 次提交)

```python
# backend/src/worker/smart_worker.py
async def process_batch(task_ids: List[str]):
    """并发处理多个任务"""
    semaphore = asyncio.Semaphore(CONCURRENCY)
    tasks = [process_task(task_id, semaphore) for task_id in task_ids]
    await asyncio.gather(*tasks)
```

**任务 3.3: 批量任务状态** (1-2 次提交)

```python
# backend/src/db/models.py
class BatchTask(Base):
    """批量任务模型"""
    id: str
    task_ids: List[str]
    status: str  # pending, processing, completed
    created_at: datetime
```

**任务 3.4: 前端多文件上传** (2-3 次提交)

```tsx
// frontend/src/components/FileUpload.tsx
export function FileUpload({ onUpload }) {
  return (
    <Upload
      multiple
      accept=".pdf"
      beforeUpload={handleUpload}
    >
      <Button icon={<UploadOutlined />}>点击或拖拽上传</Button>
    </Upload>
  );
}
```

**任务 3.5: 批量任务列表** (2-3 次提交)

```tsx
// frontend/src/components/BatchTaskList.tsx
export function BatchTaskList({ tasks }) {
  return (
    <Table
      dataSource={tasks}
      columns={[
        { title: '文件名', dataIndex: 'filename' },
        { title: '状态', dataIndex: 'status' },
        { title: '进度', dataIndex: 'progress' },
        { title: '操作', render: (_, record) => (
          <Button onClick={() => download(record.id)}>下载</Button>
        )}
      ]}
    />
  );
}
```

**任务 3.6: 批量下载** (1-2 次提交)

```tsx
// 打包下载所有文件
export async function downloadAll(taskIds: string[]) {
  const files = await Promise.all(
    taskIds.map(id => fetch(`/api/v1/tasks/${id}/download`))
  );
  // 使用 JSZip 打包
  const zip = new JSZip();
  // ... 添加文件到 zip
  zip.generateAsync({ type: 'blob' }).then(blob => {
    saveAs(blob, 'batch-results.zip');
  });
}
```

#### 完成条件

- [x] 支持一次选择多个 PDF
- [x] 并发处理提高效率
- [x] 每个任务状态独立显示
- [x] 批量下载所有结果
- [x] 错误隔离（单个失败不影响其他）

---

### 功能 4: 多提供商支持 ✅ (部分完成)

**目标**: 支持切换不同的 LLM 提供商（OpenAI、Claude、Ollama）

**完成状态**:
- ✅ 后端提供商配置已实现
- ✅ 动态切换逻辑已实现
- ✅ 前端设置页面已实现
- ✅ 模型名称自动格式化
- 🚧 模型列表动态获取待完善
- 🚧 配置验证待加强

#### 技术方案

```yaml
后端:
  - 使用 LiteLLM 统一接口
  - 添加提供商配置管理
  - 模型名称自动格式化

前端:
  - 设置页面添加提供商选择
  - 动态显示模型列表
  - 保存提供商配置
```

#### 开发任务分解

**任务 4.1: 提供商配置模型** (1-2 次提交)

```python
# backend/src/api/models.py
class ProviderConfig(BaseModel):
    """LLM 提供商配置"""
    provider: Literal['openai', 'anthropic', 'gemini', 'ollama']
    api_key: str
    api_base: Optional[str]
    model_name: str
```

**任务 4.2: 动态切换逻辑** (2-3 次提交)

```python
# backend/src/worker/smart_worker.py
def get_model_name(provider: str, model: str) -> str:
    """根据提供商格式化模型名称"""
    if provider == 'gemini' and not model.startswith('gemini/'):
        return f'gemini/{model}'
    if provider == 'openai' and not model.startswith('gpt-'):
        return model
    return model
```

**任务 4.3: 前端提供商选择** (2-3 次提交)

```tsx
// frontend/src/pages/Settings.tsx
export function Settings() {
  return (
    <Form>
      <Form.Item label="提供商">
        <Select onChange={handleProviderChange}>
          <Option value="gemini">Google Gemini</Option>
          <Option value="openai">OpenAI</Option>
          <Option value="anthropic">Anthropic Claude</Option>
          <Option value="ollama">Ollama (本地)</Option>
        </Select>
      </Form.Item>

      <Form.Item label="模型">
        <Select>
          {models.map(model => (
            <Option key={model.name} value={model.name}>
              {model.display_name}
            </Option>
          ))}
        </Select>
      </Form.Item>
    </Form>
  );
}
```

**任务 4.4: 模型列表获取** (1-2 次提交)

```python
# backend/src/api/routes.py
@app.get("/api/v1/models")
async def list_models(provider: str):
    """获取支持的模型列表"""
    models = {
        'gemini': ['gemini-2.0-flash-exp', 'gemini-pro-vision'],
        'openai': ['gpt-4o', 'gpt-4o-mini'],
        'anthropic': ['claude-3-5-sonnet-20241022'],
        'ollama': ['llava', 'llama3.2-vision']
    }
    return {'models': models.get(provider, [])}
```

#### 完成条件

- [x] 支持至少 3 个提供商
- [x] 模型名称正确格式化
- [x] 配置动态切换
- [x] API Key 安全存储
- [x] 测试每个提供商的转换效果

---

### 功能 5: 页码范围

**目标**: 支持只转换 PDF 的指定页面（如 1-10 页，或第 3, 5, 7 页）

#### 技术方案

```yaml
后端:
  - 添加 page_range 参数
  - 支持多种格式：1-10, 3,5,7, 1-3,5-7
  - 解析页码范围逻辑

前端:
  - 上传时添加页码范围输入
  - 预览时显示选中的页面
```

#### 开发任务分解

**任务 5.1: 页码范围解析** (2-3 次提交)

```python
# backend/src/utils/page_range.py
def parse_page_range(range_str: str, total_pages: int) -> List[int]:
    """
    解析页码范围
    支持格式：
    - "1-10" → [1,2,3,4,5,6,7,8,9,10]
    - "1,3,5" → [1,3,5]
    - "1-3,5-7" → [1,2,3,5,6,7]
    """
    pages = []
    for part in range_str.split(','):
        if '-' in part:
            start, end = part.split('-')
            pages.extend(range(int(start), int(end) + 1))
        else:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= total_pages]
```

**任务 5.2: 上传接口修改** (1-2 次提交)

```python
# backend/src/api/routes.py
@app.post("/api/v1/upload")
async def upload_file(
    file: UploadFile,
    page_range: Optional[str] = None
):
    """上传 PDF，可选指定页码范围"""
    task_id = await create_task(file)
    if page_range:
        await update_task_config(task_id, {'page_range': page_range})
    return {'task_id': task_id}
```

**任务 5.3: Worker 逻辑修改** (2-3 次提交)

```python
# backend/src/worker/smart_worker.py
async def convert_to_images(self, page_range: Optional[List[int]] = None):
    """支持指定页码范围"""
    if page_range:
        # 只转换指定页面
        for page_num in page_range:
            page = self.pdf_file[page_num - 1]
            # 渲染页面
    else:
        # 转换所有页面
        for page in self.pdf_file:
            # 渲染页面
```

**任务 5.4: 前端页码输入** (2-3 次提交)

```tsx
// frontend/src/components/PageRangeInput.tsx
export function PageRangeInput({ value, onChange }) {
  return (
    <div>
      <label>页码范围（可选）</label>
      <Input
        placeholder="例如：1-10 或 1,3,5"
        value={value}
        onChange={e => onChange(e.target.value)}
      />
      <small>留空则转换全部页面</small>
    </div>
  );
}
```

**任务 5.5: 页码范围验证** (1-2 次提交)

```tsx
// 前端验证
function validatePageRange(range: string, totalPages: number) {
  try {
    const pages = parsePageRange(range);
    return pages.every(p => p >= 1 && p <= totalPages);
  } catch {
    return false;
  }
}
```

#### 完成条件

- [x] 支持多种页码范围格式
- [x] 页码范围验证正确
- [x] 只转换指定页面
- [x] 前端提示清晰
- [x] 错误处理完善

---

### 功能 6: 多语言 (i18n)

**目标**: 支持中英文界面切换

#### 技术方案

```yaml
后端:
  - API 错误消息支持多语言
  - 根据 Accept-Language 头返回

前端:
  - 使用 react-i18next
  - 提取所有文本到语言文件
  - 语言切换组件
```

#### 开发任务分解

**任务 6.1: 前端 i18n 配置** (1-2 次提交)

```bash
cd frontend
npm install react-i18next i18next
```

```typescript
// frontend/src/i18n/config.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import zh from './locales/zh.json';

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    zh: { translation: zh }
  },
  lng: 'zh',
  fallbackLng: 'en'
});
```

**任务 6.2: 语言文件** (2-3 次提交)

```json
// frontend/src/i18n/locales/zh.json
{
  "upload": {
    "title": "上传 PDF",
    "drag": "拖拽文件到此处",
    "select": "选择文件"
  },
  "settings": {
    "title": "设置",
    "apiKey": "API Key",
    "model": "模型"
  }
}
```

```json
// frontend/src/i18n/locales/en.json
{
  "upload": {
    "title": "Upload PDF",
    "drag": "Drag files here",
    "select": "Select Files"
  },
  "settings": {
    "title": "Settings",
    "apiKey": "API Key",
    "model": "Model"
  }
}
```

**任务 6.3: 组件中使用** (多次提交，逐步替换)

```tsx
// frontend/src/pages/Home.tsx
import { useTranslation } from 'react-i18next';

export function Home() {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('upload.title')}</h1>
      <p>{t('upload.drag')}</p>
    </div>
  );
}
```

**任务 6.4: 语言切换组件** (1-2 次提交)

```tsx
// frontend/src/components/LanguageSwitcher.tsx
export function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <Select value={i18n.language} onChange={changeLanguage}>
      <Option value="zh">中文</Option>
      <Option value="en">English</Option>
    </Select>
  );
}
```

**任务 6.5: 后端多语言** (2-3 次提交)

```python
# backend/src/api/i18n.py
from fastapi import Header

MESSAGES = {
    'zh': {
        'task_not_found': '任务不存在',
        'invalid_file': '文件格式错误'
    },
    'en': {
        'task_not_found': 'Task not found',
        'invalid_file': 'Invalid file format'
    }
}

def get_message(key: str, lang: str = 'zh') -> str:
    return MESSAGES.get(lang, MESSAGES['zh']).get(key, key)

# 在路由中使用
@app.get("/api/v1/tasks/{task_id}")
async def get_task(
    task_id: str,
    accept_language: str = Header(default='zh')
):
    lang = accept_language.split(',')[0].split('-')[0]
    task = await get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=get_message('task_not_found', lang)
        )
    return task
```

#### 完成条件

- [x] 所有界面文本支持中英文
- [x] 语言切换即时生效
- [x] 后端错误消息多语言
- [x] 语言偏好持久化（localStorage）
- [x] 默认语言为中文

---

## 代码提交规范

### 提交信息格式

使用 **Conventional Commits** 规范：

```
<type>(<scope>): <subject>

<body>
```

### Type 类型

```yaml
feat:     新功能
fix:      Bug 修复
docs:     文档更新
style:    代码格式（不影响功能）
refactor: 重构（不是新功能也不是修复）
test:     添加测试
chore:    构建/工具链配置
```

### Scope 范围

```yaml
backend:  后端修改
frontend: 前端修改
api:      API 路由
worker:   任务处理
db:       数据库
docs:     文档
deploy:   部署配置
```

### 提交示例

```bash
# 新功能
feat(backend): 添加 SSE 事件端点

feat(frontend): 实现进度监听 Hook

# Bug 修复
fix(worker): 修复并发处理时的死锁问题

fix(frontend): 修复进度条显示异常

# 文档
docs: 更新 API 使用说明

# 重构
refactor(backend): 优化任务队列逻辑

# 测试
test(backend): 添加 SSE 端点单元测试
```

### 使用 smart-commit 技能

```
"帮我提交代码"
```

技能会自动：
1. 分析修改类型
2. 生成规范的提交信息
3. 执行完整的提交流程

---

## 测试标准

### 后端测试

#### 单元测试

```python
# backend/tests/unit/test_worker.py
import pytest
from src.worker.smart_worker import SmartWorker

@pytest.mark.asyncio
async def test_convert_to_images():
    """测试 PDF 转图片"""
    worker = SmartWorker(file_path="test.pdf")
    images = await worker.convert_to_images()
    assert len(images) > 0
    assert all(img.endswith('.png') for img in images)

@pytest.mark.asyncio
async def test_page_range_parsing():
    """测试页码范围解析"""
    from src.utils.page_range import parse_page_range

    pages = parse_page_range("1-3,5", 10)
    assert pages == [1, 2, 3, 5]

    pages = parse_page_range("1,3,5", 10)
    assert pages == [1, 3, 5]
```

#### 集成测试

```python
# backend/tests/integration/test_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_upload_and_convert():
    """测试完整上传转换流程"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 上传文件
        with open("test.pdf", "rb") as f:
            response = await client.post("/api/v1/upload", files={"file": f})
        assert response.status_code == 200
        task_id = response.json()["task_id"]

        # 查询状态
        response = await client.get(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 200
```

#### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行单个测试文件
uv run pytest tests/unit/test_worker.py

# 运行特定测试
uv run pytest tests/unit/test_worker.py::test_convert_to_images

# 生成覆盖率报告
uv run pytest --cov=src --cov-report=html

# 查看覆盖率
open backend/htmlcov/index.html
```

#### 测试覆盖率要求

- **核心逻辑**: 覆盖率 ≥ 80%
- **API 端点**: 覆盖率 ≥ 70%
- **工具函数**: 覆盖率 ≥ 90%

### 前端测试

#### 组件测试

```typescript
// frontend/src/components/__tests__/ProgressBar.test.tsx
import { render, screen } from '@testing-library/react';
import { ProgressBar } from '../ProgressBar';

describe('ProgressBar', () => {
  it('显示正确的进度百分比', () => {
    render(<ProgressBar progress={50} currentPage={5} totalPages={10} />);
    expect(screen.getByText('5 / 10')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '50');
  });

  it('处理 100% 进度', () => {
    render(<ProgressBar progress={100} currentPage={10} totalPages={10} />);
    expect(screen.getByText('完成')).toBeInTheDocument();
  });
});
```

#### Hook 测试

```typescript
// frontend/src/hooks/__tests__/useTaskProgress.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useTaskProgress } from '../useTaskProgress';

describe('useTaskProgress', () => {
  it('接收进度更新', async () => {
    const { result } = renderHook(() => useTaskProgress('task-123'));

    await waitFor(() => {
      expect(result.current.progress).toBe(50);
    });
  });
});
```

#### 运行测试

```bash
cd frontend

# 运行所有测试
npm run test

# 运行特定测试文件
npm run test -- ProgressBar.test.tsx

# 监听模式（修改文件自动重测）
npm run test -- --watch

# 生成覆盖率报告
npm run test -- --coverage
```

### 手动测试清单

每次功能完成后，必须进行手动测试：

```yaml
基础功能:
  - [ ] 上传 PDF 文件成功
  - [ ] 任务状态正确更新
  - [ ] 转换完成后可下载结果

边界情况:
  - [ ] 上传非 PDF 文件提示错误
  - [ ] 网络断开时正确处理
  - [ ] 大文件（>50MB）正常处理
  - [ ] 并发上传多个文件

性能测试:
  - [ ] 响应时间 < 2s
  - [ ] 内存占用合理
  - [ ] CPU 使用率正常

兼容性:
  - [ ] Chrome 浏览器正常
  - [ ] Firefox 浏览器正常
  - [ ] Safari 浏览器正常
  - [ ] 移动端浏览器可用
```

---

## 完成与合并条件

### ✅ 功能完成标准

每个功能分支必须满足以下条件才能合并：

#### 1. 代码质量

- [x] 代码通过所有测试（pytest + vitest）
- [x] 测试覆盖率达标（≥ 70%）
- [x] 无 lint 错误（ruff + eslint）
- [x] 代码符合项目规范

#### 2. 功能完整性

- [x] 实现所有计划的功能点
- [x] 错误处理完善
- [x] 边界情况考虑
- [x] 用户体验良好

#### 3. 文档

- [x] API 文档更新（如新增端点）
- [x] README.md 更新（如需要）
- [x] 代码注释充分

#### 4. 测试验证

- [x] 单元测试通过
- [x] 集成测试通过
- [x] 手动测试通过
- [x] 性能测试通过

#### 5. 代码审查

- [x] 自我审查通过
- [x] 无安全漏洞
- [x] 无敏感信息泄露
- [x] 依赖库无已知漏洞

### 🎯 合并流程

#### 方案 A: 创建 Pull Request（推荐）

```bash
# 使用 finishing-a-development-branch 技能
"功能开发完成，帮我处理分支"

→ 选择选项 2: Push and create PR
```

**PR 标题示例**：
```
feat: 添加 SSE 实时进度推送功能
```

**PR 描述模板**：
```markdown
## 功能描述
- 后端实现 /api/v1/events SSE 端点
- 前端实现 useTaskProgress Hook
- 支持实时显示转换进度

## 主要变更
- 添加后端 SSE 事件生成逻辑
- 前端进度条组件实时更新
- 实现断线重连机制

## 测试情况
- [x] 单元测试通过（45 个测试）
- [x] 手动测试通过
- [x] 测试覆盖率：85%

## 截图
（添加功能截图）

## 检查清单
- [x] 代码符合规范
- [x] 测试充分
- [x] 文档完整
- [x] 无安全漏洞
```

#### 方案 B: 本地合并（小功能）

```bash
# 使用 finishing-a-development-branch 技能
→ 选择选项 1: Merge locally

# 流程：
git checkout main
git pull origin main
git merge feature/xxx
git push origin main
git branch -d feature/xxx
```

---

## 常见问题

### Q1: 如何在本地测试后端 API？

```bash
# 启动后端
cd backend
uv run uvicorn src.api.main:app --reload --port 8000

# 访问 API 文档
open http://localhost:8000/docs

# 使用 curl 测试
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@test.pdf"

# 查看响应
curl http://localhost:8000/api/v1/tasks/{task_id}
```

### Q2: 如何调试前端问题？

```bash
# 启动前端开发服务器
cd frontend
npm run dev

# 打开浏览器开发者工具
# 1. 打开 http://localhost:5173
# 2. 按 F12 打开 DevTools
# 3. 查看 Console 标签的错误信息
# 4. 查看 Network 标签的 API 请求

# 在代码中添加 console.log
console.log('Debug info:', data);
```

### Q3: 测试失败了怎么办？

```bash
# 1. 查看详细错误信息
uv run pytest -v

# 2. 运行特定测试并进入调试模式
uv run pytest tests/unit/test_worker.py::test_func -s

# 3. 在代码中添加断点
import pdb; pdb.set_trace()

# 4. 查看测试覆盖率
uv run pytest --cov=src --cov-report=term-missing
```

### Q4: Git 冲突如何解决？

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 如果有冲突，查看冲突文件
git status

# 3. 手动解决冲突（编辑文件）
# 搜索 <<<<<<< 标记

# 4. 标记冲突已解决
git add <resolved-file>

# 5. 继续合并
git commit

# 6. 推送
git push origin main
```

### Q5: 如何参考 desktop_study 项目？

```bash
# 1. 查找相关文件
cd desktop_study
find . -name "*progress*" -o -name "*sse*"

# 2. 搜索关键词
grep -r "EventSource" src/

# 3. 对比查看文件
diff desktop_study/src/service.ts backend/src/service.ts

# 4. 使用 Claude Code Task tool
"在 desktop_study 中查找实时进度推送的实现路径"
```

### Q6: 如何确保代码符合规范？

```bash
# 后端代码检查
cd backend
uv run ruff check .          # 检查代码规范
uv run ruff format .         # 自动格式化

# 前端代码检查
cd frontend
npm run lint                 # 检查代码规范

# 运行所有检查
uv run pytest && npm run test
```

### Q7: 依赖库如何更新？

```bash
# 后端依赖更新
cd backend
uv sync                      # 同步依赖
uv add <package-name>        # 添加新包

# 前端依赖更新
cd frontend
npm install                  # 安装依赖
npm install <package-name>   # 添加新包
npm update                   # 更新依赖
```

### Q8: 如何回滚到之前的版本？

```bash
# 查看提交历史
git log --oneline -10

# 回滚到指定提交（保留工作区修改）
git reset <commit-hash> --soft

# 回滚到指定提交（丢弃所有修改）
git reset --hard <commit-hash>

# 撤销最近一次提交（保留修改）
git reset --soft HEAD~1

# 撤销最近一次提交（丢弃修改）
git reset --hard HEAD~1
```

---

## 附录

### A. 快速参考卡片

```bash
# === 开发环境 ===
cd backend && uv run uvicorn src.api.main:app --reload --port 8000
cd frontend && npm run dev

# === 测试 ===
cd backend && uv run pytest
cd frontend && npm run test

# === Git 操作 ===
git checkout -b feature/xxx
"帮我提交代码"
"功能开发完成，帮我处理分支"

# === 代码检查 ===
cd backend && uv run ruff format .
cd frontend && npm run lint
```

### B. 分支命名规范

```yaml
功能分支: feature/功能名
  - feature/realtime-progress
  - feature/dual-preview
  - feature/batch-processing

修复分支: fix/问题描述
  - fix/upload-error
  - fix/memory-leak

文档分支: docs/文档内容
  - docs/api-guide
  - docs/update-readme
```

### C. 提交类型速查

```yaml
feat:  新功能
fix:   Bug 修复
docs:  文档更新
style: 代码格式
refactor: 重构
test:  测试
chore: 配置/工具
```

### D. 技术栈版本

```yaml
后端:
  Python: 3.10+
  FastAPI: 0.109+
  SQLAlchemy: 2.0+
  LiteLLM: 1.18+

前端:
  React: 19+
  TypeScript: 5.9+
  Vite: 7+
  Ant Design: 6+
```

---

## 🎓 学习资源

### 项目相关

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [React 官方文档](https://react.dev/)
- [Ant Design 组件库](https://ant.design/)
- [LiteLLM 文档](https://docs.litellm.ai/)

### 参考项目

- `desktop_study/` - 本项目的参考实现

### Git 和 GitHub

- [Git 官方文档](https://git-scm.com/doc)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)

---

**最后更新**: 2025-01-30
**维护者**: KaolaMiao
**反馈**: [GitHub Issues](https://github.com/KaolaMiao/markPDFdown-mcp/issues)

---

## 📝 更新日志

### 2025-01-30 - 功能模块状态更新

**新增功能**:
- ✅ 功能 0: 核心基础设施（原子文件操作、Token 统计、数据库扩展）
- ✅ 功能 1.1-1.3: 实时预览和单页重新生成
- ✅ 功能 2.1: 双屏预览（部分完成）
- ✅ 功能 4.1: 多提供商支持（部分完成）

**代码审查**:
- 评分从 B- 提升到 **A- (95/100)**
- 修复了所有关键安全问题
- 通过完整代码审查

**关键修复**:
- 修复 `regenerate_single_page` 的严重竞态条件
- 所有文件操作使用原子写入（100% 覆盖）
- Token 统计数据一致性保证
- 严格的输入验证和文件模式匹配

**提交记录**:
- `a0908c3` fix(tasks): 修复最终审核发现的关键问题
- `0d12b05` feat(backend): 添加实时预览和单页重新生成功能
- `123245d` Merge branch 'feature/realtime-preview'

**文档更新**:
- 添加功能实现进度总览
- 添加已完成功能的详细说明
- 更新进行中和计划中功能状态
