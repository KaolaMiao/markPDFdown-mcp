# MarkPDFdown-MCP API 文档

> **版本**: v1.0.0
> **基础路径**: `/api/v1`
> **协议**: HTTP/HTTPS
> **数据格式**: JSON

---

## 📚 目录

1. [概述](#概述)
2. [认证](#认证)
3. [通用响应格式](#通用响应格式)
4. [任务管理](#任务管理)
5. [文件上传](#文件上传)
6. [批量操作](#批量操作)
7. [实时进度](#实时进度)
8. [页面预览](#页面预览)
9. [设置管理](#设置管理)
10. [错误码](#错误码)
11. [速率限制](#速率限制)

---

## 概述

MarkPDFdown-MCP API 提供完整的 PDF 到 Markdown 转换服务，支持单文件和批量处理、实时进度追踪、页面预览等功能。

### 基础 URL

```
开发环境: http://localhost:8000/api/v1
生产环境: https://your-domain.com/api/v1
```

### 特性

- ✅ RESTful API 设计
- ✅ 支持批量文件处理
- ✅ Server-Sent Events (SSE) 实时进度
- ✅ 单页重新生成
- ✅ 并发控制
- ✅ 任务状态管理

---

## 认证

当前版本**不需要认证**。未来版本将添加 API Key 或 OAuth 支持。

---

## 通用响应格式

### 成功响应

```json
{
  "id": "task-id",
  "file_name": "document.pdf",
  "status": "processing",
  "created_at": "2025-01-30T12:00:00Z"
}
```

### 错误响应

```json
{
  "detail": "错误描述信息"
}
```

---

## 任务管理

### 获取任务列表

**端点**: `GET /tasks`

**描述**: 获取所有任务列表，支持分页

**查询参数**:

| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|--------|------|
| `skip` | integer | 否 | 0 | 跳过的任务数 |
| `limit` | integer | 否 | 20 | 返回的任务数（最大 100） |

**响应示例**:

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "file_name": "document.pdf",
    "status": "completed",
    "created_at": "2025-01-30T12:00:00Z",
    "total_pages": 10,
    "input_tokens": 1500,
    "output_tokens": 3000,
    "total_tokens": 4500
  }
]
```

**状态值**:
- `pending` - 等待处理
- `processing` - 正在处理
- `completed` - 处理完成
- `failed` - 处理失败

---

### 获取任务详情

**端点**: `GET /tasks/{task_id}`

**描述**: 获取指定任务的详细信息

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `task_id` | string | 任务 ID |

**响应示例**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "document.pdf",
  "status": "completed",
  "created_at": "2025-01-30T12:00:00Z",
  "started_at": "2025-01-30T12:00:05Z",
  "completed_at": "2025-01-30T12:02:30Z",
  "total_pages": 10,
  "input_tokens": 1500,
  "output_tokens": 3000,
  "total_tokens": 4500,
  "error": null
}
```

---

### 删除任务

**端点**: `DELETE /tasks/{task_id}`

**描述**: 删除指定任务及其相关文件

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `task_id` | string | 任务 ID |

**成功响应**: `204 No Content`

**错误响应**:

| 状态码 | 描述 |
|--------|------|
| `404` | 任务不存在 |
| `409` | 任务正在处理中，无法删除 |

**示例**:

```bash
curl -X DELETE http://localhost:8000/api/v1/tasks/{task_id}
```

---

### 下载任务结果

**端点**: `GET /tasks/{task_id}/download`

**描述**: 下载转换后的 Markdown 文件

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `task_id` | string | 任务 ID |

**成功响应**: Markdown 文件 (`text/markdown`)

**文件名**: `{original_filename}.md` 或 `{task_id}.md`

**示例**:

```bash
curl -O http://localhost:8000/api/v1/tasks/{task_id}/download
```

---

## 文件上传

### 上传单个文件

**端点**: `POST /upload`

**描述**: 上传单个 PDF 文件进行转换

**请求类型**: `multipart/form-data`

**请求参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `file` | File | 是 | PDF 文件（最大 50MB） |

**响应示例**:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "document.pdf",
  "status": "pending",
  "created_at": "2025-01-30T12:00:00Z"
}
```

**错误响应**:

| 状态码 | 描述 |
|--------|------|
| `400` | 文件格式错误（非 PDF） |
| `413` | 文件过大（超过 50MB） |

**示例 (cURL)**:

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@document.pdf"
```

**示例 (JavaScript)**:

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/v1/upload', {
  method: 'POST',
  body: formData
});

const task = await response.json();
console.log('Task ID:', task.id);
```

---

## 批量操作

### 批量上传文件

**端点**: `POST /upload/batch`

**描述**: 批量上传多个 PDF 文件进行转换

**请求类型**: `multipart/form-data`

**请求参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `files` | File[] | 是 | PDF 文件数组（最多 10 个，每个最大 50MB） |

**响应示例**:

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "file_name": "document1.pdf",
    "status": "pending",
    "created_at": "2025-01-30T12:00:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "file_name": "document2.pdf",
    "status": "pending",
    "created_at": "2025-01-30T12:00:01Z"
  }
]
```

**错误响应**:

| 状态码 | 描述 |
|--------|------|
| `400` | 文件数量超过限制（最多 10 个） |
| `400` | 文件大小超过限制（每个最大 50MB） |
| `400` | 无有效的 PDF 文件 |

**示例 (cURL)**:

```bash
curl -X POST http://localhost:8000/api/v1/upload/batch \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf" \
  -F "files=@document3.pdf"
```

**示例 (JavaScript)**:

```javascript
const formData = new FormData();
files.forEach(file => {
  formData.append('files', file);
});

const response = await fetch('/api/v1/upload/batch', {
  method: 'POST',
  body: formData
});

const tasks = await response.json();
console.log('Created tasks:', tasks.length);
```

---

## 实时进度

### SSE 进度事件

**端点**: `GET /events`

**描述**: 通过 Server-Sent Events (SSE) 订阅任务进度更新

**查询参数**:

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `task_id` | string | 是 | 要监听的任务 ID |

**响应类型**: `text/event-stream`

**事件格式**:

```json
data: {"task_id":"550e8400-e29b-41d4-a716-446655440000","current_page":5,"total_pages":10,"progress":50,"status":"processing","timestamp":1738255200}
```

**字段说明**:

| 字段 | 类型 | 描述 |
|------|------|------|
| `task_id` | string | 任务 ID |
| `current_page` | integer | 当前处理页码 |
| `total_pages` | integer | 总页数 |
| `progress` | number | 进度百分比（0-100） |
| `status` | string | 任务状态 |
| `timestamp` | integer | Unix 时间戳 |

**示例 (JavaScript)**:

```javascript
const eventSource = new EventSource(
  `/api/v1/events?task_id=${taskId}`
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data.progress);
  console.log('Page:', data.current_page, '/', data.total_pages);

  if (data.status === 'completed' || data.status === 'failed') {
    eventSource.close();
  }
};

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  eventSource.close();
};
```

**自动重连**:

EventSource API 会自动重连。建议实现指数退避策略：

```javascript
let retryCount = 0;
const maxRetries = 5;

eventSource.onerror = () => {
  if (retryCount >= maxRetries) {
    eventSource.close();
    return;
  }

  const delay = Math.min(1000 * Math.pow(2, retryCount), 30000);
  setTimeout(() => {
    retryCount++;
    // 重新连接
  }, delay);
};
```

---

## 页面预览

### 获取页面图片

**端点**: `GET /tasks/{task_id}/pages/{page_num}`

**描述**: 获取指定页面的渲染图片

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `task_id` | string | 任务 ID |
| `page_num` | integer | 页码（从 1 开始，1-10000） |

**响应**: PNG 图片 (`image/png`)

**示例**:

```bash
curl -O http://localhost:8000/api/v1/tasks/{task_id}/pages/1
```

---

### 获取页面内容

**端点**: `GET /tasks/{task_id}/pages/{page_num}/content`

**描述**: 获取指定页面的 Markdown 内容

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `task_id` | string | 任务 ID |
| `page_num` | integer | 页码（从 1 开始，1-10000） |

**响应示例**:

```markdown
# 页面标题

页面内容...
```

**示例**:

```bash
curl http://localhost:8000/api/v1/tasks/{task_id}/pages/1/content
```

---

### 重新生成页面

**端点**: `POST /tasks/{task_id}/pages/{page_num}/regenerate`

**描述**: 重新生成指定页面（仅当转换结果不理想时使用）

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| `task_id` | string | 任务 ID |
| `page_num` | integer | 页码（从 1 开始） |

**响应示例**:

```json
{
  "success": true,
  "message": "Page regenerated successfully",
  "page_num": 1
}
```

**错误响应**:

| 状态码 | 描述 |
|--------|------|
| `404` | 任务或页面不存在 |
| `409` | 任务正在处理中 |

**示例**:

```bash
curl -X POST http://localhost:8000/api/v1/tasks/{task_id}/pages/1/regenerate
```

---

## 设置管理

### 获取设置

**端点**: `GET /settings`

**描述**: 获取当前系统配置

**响应示例**:

```json
{
  "provider": "gemini",
  "apiKey": "sk-...",
  "baseUrl": null,
  "model": "gemini-2.0-flash-exp",
  "temperature": 0.3,
  "maxTokens": 8192,
  "concurrency": 2,
  "maxTasks": 20,
  "retryTimes": 3
}
```

---

### 更新设置

**端点**: `PUT /settings`

**描述**: 更新系统配置

**请求体**:

```json
{
  "provider": "openai",
  "apiKey": "sk-new-key",
  "model": "gpt-4o",
  "temperature": 0.5,
  "maxTokens": 4096,
  "concurrency": 3
}
```

**响应示例**:

```json
{
  "provider": "openai",
  "apiKey": "sk-new-key",
  "baseUrl": null,
  "model": "gpt-4o",
  "temperature": 0.5,
  "maxTokens": 4096,
  "concurrency": 3,
  "maxTasks": 20,
  "retryTimes": 3
}
```

**字段说明**:

| 字段 | 类型 | 描述 |
|------|------|------|
| `provider` | string | LLM 提供商（`gemini`, `openai`, `anthropic`, `ollama`） |
| `apiKey` | string | API 密钥 |
| `baseUrl` | string? | 自定义 API 基础 URL（可选） |
| `model` | string | 模型名称 |
| `temperature` | number | 温度参数（0.0-1.0） |
| `maxTokens` | integer | 最大 token 数 |
| `concurrency` | integer | 并发任务数（1-10） |
| `maxTasks` | integer | 保留的最大任务数 |
| `retryTimes` | integer | 失败重试次数 |

---

## 错误码

### HTTP 状态码

| 状态码 | 名称 | 描述 |
|--------|------|------|
| `200` | OK | 请求成功 |
| `204` | No Content | 删除成功 |
| `400` | Bad Request | 请求参数错误 |
| `404` | Not Found | 资源不存在 |
| `409` | Conflict | 资源状态冲突 |
| `413` | Payload Too Large | 文件过大 |
| `500` | Internal Server Error | 服务器内部错误 |

### 错误响应示例

```json
{
  "detail": "Task not found"
}
```

```json
{
  "detail": "Maximum 10 files allowed per batch. Got 15 files."
}
```

```json
{
  "detail": "Cannot delete task while it is processing. Please wait for completion."
}
```

---

## 速率限制

### 批量上传限制

- **文件数量**: 最多 10 个文件/批次
- **文件大小**: 每个文件最大 50MB
- **总大小**: 约 500MB/批次

### 并发处理限制

- **默认并发数**: 2 个任务同时处理
- **可配置范围**: 1-10 个任务
- **信号量控制**: 自动管理资源使用

### 任务保留限制

- **最大任务数**: 20 个（自动清理旧任务）
- **清理策略**: 保留最近的 N 个任务

---

## 数据模型

### Task 对象

```typescript
interface Task {
  id: string;                    // 任务 ID (UUID)
  file_name: string;             // 原始文件名
  status: TaskStatus;            // 任务状态
  created_at: string;            // 创建时间 (ISO 8601)
  started_at?: string;           // 开始时间
  completed_at?: string;         // 完成时间
  total_pages?: number;          // 总页数
  input_tokens?: number;         // 输入 token 数
  output_tokens?: number;        // 输出 token 数
  total_tokens?: number;         // 总 token 数
  result?: string;               // 结果文件路径
  error?: string;                // 错误信息
}

type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';
```

### Settings 对象

```typescript
interface Settings {
  provider: 'gemini' | 'openai' | 'anthropic' | 'ollama';
  apiKey: string;
  baseUrl?: string;
  model: string;
  temperature: number;
  maxTokens: number;
  concurrency: number;
  maxTasks: number;
  retryTimes: number;
}
```

### ProgressEvent 对象

```typescript
interface ProgressEvent {
  task_id: string;
  current_page: number;
  total_pages: number;
  progress: number;              // 0-100
  status: TaskStatus;
  timestamp: number;             // Unix timestamp
}
```

---

## 使用示例

### 完整工作流程

```javascript
// 1. 上传文件
const formData = new FormData();
formData.append('file', pdfFile);

const uploadResponse = await fetch('/api/v1/upload', {
  method: 'POST',
  body: formData
});
const task = await uploadResponse.json();

// 2. 订阅进度
const eventSource = new EventSource(
  `/api/v1/events?task_id=${task.id}`
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.progress}%`);
  console.log(`Page: ${data.current_page}/${data.total_pages}`);

  if (data.status === 'completed') {
    eventSource.close();
    downloadResult(task.id);
  }
};

// 3. 下载结果
async function downloadResult(taskId) {
  const response = await fetch(`/api/v1/tasks/${taskId}/download`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'result.md';
  a.click();
}
```

### 批量处理

```javascript
// 1. 批量上传
const formData = new FormData();
files.slice(0, 10).forEach(file => {  // 最多 10 个文件
  formData.append('files', file);
});

const response = await fetch('/api/v1/upload/batch', {
  method: 'POST',
  body: formData
});
const tasks = await response.json();

// 2. 监听所有任务进度
tasks.forEach(task => {
  const eventSource = new EventSource(
    `/api/v1/events?task_id=${task.id}`
  );

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateTaskProgress(task.id, data);
  };
});

// 3. 批量下载
async function downloadAllResults(tasks) {
  for (const task of tasks) {
    if (task.status === 'completed') {
      await downloadResult(task.id);
    }
  }
}
```

---

## 最佳实践

### 1. 错误处理

```javascript
try {
  const response = await fetch('/api/v1/upload', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  const task = await response.json();
} catch (error) {
  console.error('Upload failed:', error.message);
}
```

### 2. 进度显示

```javascript
function ProgressBar({ taskId }) {
  const [progress, setProgress] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  useEffect(() => {
    const eventSource = new EventSource(
      `/api/v1/events?task_id=${taskId}`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.progress);
      setCurrentPage(data.current_page);
      setTotalPages(data.total_pages);
    };

    return () => eventSource.close();
  }, [taskId]);

  return (
    <div>
      <progress value={progress} max={100} />
      <span>{currentPage} / {totalPages}</span>
    </div>
  );
}
```

### 3. 任务轮询（SSE 失败时的备用方案）

```javascript
async function pollTaskStatus(taskId) {
  while (true) {
    const response = await fetch(`/api/v1/tasks/${taskId}`);
    const task = await response.json();

    if (task.status === 'completed' || task.status === 'failed') {
      return task;
    }

    await new Promise(resolve => setTimeout(resolve, 2000));
  }
}
```

---

## 附录

### A. 状态转换图

```
pending → processing → completed
                    ↘ failed
```

### B. Token 统计

```javascript
// Token 使用统计
{
  "input_tokens": 1500,    // 输入 token 数
  "output_tokens": 3000,   // 输出 token 数
  "total_tokens": 4500     // 总 token 数
}

// 计算公式
total_tokens = input_tokens + output_tokens
```

### C. 支持的模型

| 提供商 | 模型名称 | 前缀 |
|--------|----------|------|
| Google Gemini | `gemini-2.0-flash-exp` | `gemini/` |
| OpenAI | `gpt-4o`, `gpt-4o-mini` | 无 |
| Anthropic | `claude-3-5-sonnet` | 无 |
| Ollama | `llava`, `llama3.2-vision` | 无 |

---

## 更新日志

### v1.0.0 (2025-01-30)

**新增**:
- ✅ 批量上传功能（最多 10 个文件）
- ✅ 任务删除功能（带状态检查）
- ✅ 并发控制（可配置）
- ✅ SSE 实时进度推送
- ✅ 单页重新生成
- ✅ 页面预览（图片 + Markdown）

**安全改进**:
- ✅ 文件大小限制（50MB）
- ✅ 文件数量限制（10 个）
- ✅ 防止删除正在处理的任务
- ✅ 完善的错误处理

---

**文档版本**: v1.0.0
**最后更新**: 2025-01-30
**维护者**: KaolaMiao

---

## 相关资源

- [项目仓库](https://github.com/KaolaMiao/markPDFdown-mcp)
- [开发文档](./AGENTS.md)
- [CLAUDE.md](./CLAUDE.md)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SSE 规范](https://html.spec.whatwg.org/multipage/server-sent-events.html)
