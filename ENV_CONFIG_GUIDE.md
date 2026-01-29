# 🔒 环境变量安全配置指南

## ⚠️ 重要提醒

**你的 Google API Key 已被清理！**

如果你之前在 `backend/.env` 中配置了真实的 API Key：
```
LLM_API_KEY="AIzaSyC-CQz60ORyjcat8M1SpBQaIUlmMM2HhzY"
```

这个文件现在已经被**替换为安全的模板**，真实的 API Key 已被移除。

---

## 🎯 你现在需要做什么

### 步骤 1: 重新配置本地 API Key

**选项 A: 使用 Google Gemini（推荐）**

编辑 `backend/.env` 文件：

```bash
vim backend/.env
```

将第 14 行改为：
```bash
GEMINI_API_KEY="你的真实-Google-API-Key"
```

**选项 B: 使用其他提供商**

```bash
# OpenAI
OPENAI_API_KEY="你的-OpenAI-API-Key"

# Anthropic Claude
ANTHROPIC_API_KEY="你的-Claude-API-Key"
```

### 步骤 2: 重启本地服务

```bash
# 停止服务
docker-compose down

# 重新启动
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

### 步骤 3: 验证配置

```bash
# 检查环境变量是否正确加载
docker exec markpdfdown-backend env | grep API

# 测试 API 连接
curl http://localhost:18000/health
```

---

## 📋 完整的配置文件结构

### 当前配置层次（从高到低优先级）

```
1. docker-compose.yml (环境变量默认值)
   ↓
2. backend/.env (宿主机文件，被 volume 挂载)
   ↓
3. 容器内环境变量
```

### 工作原理

```yaml
# docker-compose.yml
environment:
  - LLM_API_KEY=${GEMINI_API_KEY}  # 从宿主机 .env 读取
  - LLM_MODEL=${LLM_MODEL:-gemini-3.0-flash-exp}  # 默认值
```

**优先级**：
1. 如果 `backend/.env` 中定义了 `GEMINI_API_KEY`，使用该值
2. 如果未定义，使用空字符串（会导致错误）
3. `LLM_MODEL` 有默认值，如果未定义会使用 `gemini-3.0-flash-exp`

---

## 🔐 安全配置最佳实践

### 本地开发环境

```bash
# 1. 创建配置文件
cp backend/.env.example backend/.env

# 2. 填写你的 API Key
vim backend/.env

# 3. 验证文件权限
ls -la backend/.env
# 应该显示：-rw-r--r-- (644) 或 -rw------- (600)

# 4. 测试服务
docker-compose up -d
```

### 服务器生产环境

```bash
# 1. 上传代码到服务器
scp -r * user@server:/opt/1panel/apps/markPDFdown/

# 2. 在服务器上创建配置
ssh user@server
cd /opt/1panel/apps/markPDFdown
cat > backend/.env << 'EOF'
LLM_PROVIDER="gemini"
LLM_MODEL="gemini-3.0-flash-exp"
GEMINI_API_KEY="你的生产环境API-Key"
LLM_CONCURRENCY=2
EOF

# 3. 设置文件权限（只有所有者可读）
chmod 600 backend/.env

# 4. 启动服务
docker-compose up -d --build
```

### 服务器更新后重新配置

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 配置不会受影响（.env 在 .gitignore 中）
# backend/.env 不会被覆盖

# 3. 重建容器（配置保留）
docker-compose down
docker-compose up -d --build
```

---

## 🧪 测试配置是否正确

### 检查环境变量

```bash
# 查看容器内的环境变量
docker exec markpdfdown-backend env | grep -E "API_KEY|MODEL|PROVIDER"

# 应该看到你配置的值
```

### 测试 API 连接

```bash
# 后端健康检查
curl http://localhost:18000/health

# 测试文件上传
curl -X POST http://localhost:18000/api/v1/upload \
  -F "file=@test.pdf"
```

---

## 🌍 支持的 LLM 提供商

### Google Gemini

```bash
# backend/.env 配置
GEMINI_API_KEY="AIzaSy..."  # 从 https://console.cloud.google.com/apis/credentials 获取
LLM_MODEL="gemini-3.0-flash-exp"
LLM_PROVIDER="gemini"
```

### OpenAI

```bash
OPENAI_API_KEY="sk-proj-..."  # 从 https://platform.openai.com/api-keys 获取
LLM_MODEL="gpt-4o"
LLM_PROVIDER="openai"
```

### Anthropic Claude

```bash
ANTHROPIC_API_KEY="sk-ant-..."  # 从 https://console.anthropic.com/ 获取
LLM_MODEL="claude-3-5-sonnet-20241022"
LLM_PROVIDER="anthropic"
```

### Ollama（本地模型）

```bash
# 不需要 API Key
LLM_MODEL="llava:latest"
OLLAMA_BASE_URL="http://localhost:11434"
```

---

## ⚙️ 配置选项说明

### 后端配置文件

| 变量名 | 说明 | 默认值 | 必填 |
|-------|------|--------|------|
| `LLM_PROVIDER` | LLM 提供商 | `gemini` | 否 |
| `LLM_MODEL` | 模型名称 | `gemini-3.0-flash-exp` | 否 |
| `LLM_CONCURRENCY` | 并发处理数 | `2` | 否 |
| `LLM_TEMPERATURE` | 温度参数 | `0.3` | 否 |
| `LLM_MAX_TOKENS` | 最大 token 数 | `8192` | 否 |
| `LLM_MAX_TASKS` | 最大任务数 | `20` | 否 |
| `GEMINI_API_KEY` | Gemini API Key | - | 使用 Gemini 时必填 |
| `OPENAI_API_KEY` | OpenAI API Key | - | 使用 OpenAI 时必填 |
| `ANTHROPIC_API_KEY` | Claude API Key | - | 使用 Claude 时必填 |
| `USE_CELERY` | 是否使用 Celery | `false` | 否 |

### 前端配置（通过 Web UI）

访问 `http://localhost:18080/settings` 可以在 Web 界面配置：

- API Key
- 模型名称
- API 基础 URL
- 并发数
- 最大任务数

配置会自动保存到 `backend/.env` 文件。

---

## 🔄 配置更新流程

### 本地更新配置

```bash
# 1. 编辑配置
vim backend/.env

# 2. 重启后端
docker-compose restart backend

# 3. 查看日志
docker-compose logs -f backend
```

### 服务器更新配置

```bash
# 1. SSH 登录服务器
ssh user@server

# 2. 进入项目目录
cd /opt/1panel/apps/markPDFdown

# 3. 编辑配置
vim backend/.env

# 4. 重启服务
docker-compose restart backend
```

### 撤销旧 API Key

如果使用了 Google API Key，建议定期（每 90 天）更换：

```bash
# 1. 访问 Google Cloud Console
# https://console.cloud.google.com/apis/credentials

# 2. 找到旧的 API Key，点击删除

# 3. 创建新的 API Key

# 4. 更新配置
vim backend/.env

# 5. 重启服务
docker-compose restart backend
```

---

## 🛡️ 安全检查清单

### 提交代码前

```bash
# 1. 检查是否有真实密钥
grep -r "AIzaSy" . --exclude-dir=node_modules --exclude-dir=.venv
grep -r "sk-" . --exclude-dir=node_modules --exclude-dir=.venv
grep -r "AKIA" . --exclude-dir=node_modules --exclude-dir=.venv

# 2. 检查 .env 文件状态
git status | grep ".env"
# 应该看不到 backend/.env（已在 .gitignore 中）

# 3. 确认 .env.example 是安全的
cat backend/.env.example | grep "your-api-key"
# 应该能看到（这是模板，是安全的）

# 4. 查看暂存区
git diff --cached
```

### 密钥泄露应急处理

**如果发现密钥已泄露到 GitHub**：

1. **立即撤销密钥**
   - Google: https://console.cloud.google.com/apis/credentials
   - OpenAI: https://platform.openai.com/api-keys
   - Anthropic: https://console.anthropic.com/

2. **生成新密钥**

3. **更新本地配置**
   ```bash
   vim backend/.env
   # 填入新的 API Key
   ```

4. **清理 Git 历史**（如果已提交）
   ```bash
   # 从所有历史记录中删除
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch backend/.env' \
     --prune-empty HEAD

   # 强制推送
   git push origin main --force
   ```

5. **通知团队**（如果是团队项目）
   - 告知密钥已撤销
   - 要求所有人更新配置
   - 监控 API 使用日志

---

## 📚 参考资源

### 获取 API Key

- **Google Gemini**: https://console.cloud.google.com/apis/credentials
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic Claude**: https://console.anthropic.com/
- **Ollama**: https://ollama.com/

### 密钥管理最佳实践

- ✅ 定期更换 API Key（建议每 90 天）
- ✅ 使用不同的密钥用于开发和生产
- ✅ 限制 API Key 的权限范围
- ✅ 监控 API 使用情况和费用
- ✅ 不在代码中硬编码密钥
- ✅ 使用环境变量管理密钥

---

## 💡 常见问题

### Q1: 更新代码后配置丢失了？

**A**: 不会！`backend/.env` 通过 volume 挂载到宿主机，重建容器不会丢失。

### Q2: 如何在不同的环境使用不同的配置？

**A**: 为每个环境创建不同的 `.env` 文件：
```bash
# 开发环境
cp backend/.env.example backend/.env.local

# 生产环境
cp backend/.env.example backend/.env
```

### Q3: .env.example 可以提交到 GitHub 吗？

**A**: 可以！`.env.example` 只包含占位符，不包含真实密钥，可以安全提交。

### Q4: 如何在 Docker Compose 中使用多个 .env 文件？

**A**:
```yaml
services:
  backend:
    env_file:
      - .env.common
      - .env.production
```

---

## 🎯 快速参考

### 本地配置（3 步）

```bash
# 1. 复制模板
cp backend/.env.example backend/.env

# 2. 填写 API Key
vim backend/.env

# 3. 重启服务
docker-compose restart backend
```

### 服务器配置（4 步）

```bash
# 1. SSH 登录
ssh user@server

# 2. 配置
cd /opt/1panel/apps/markPDFdown
cat > backend/.env << 'EOF'
GEMINI_API_KEY="your-key"
EOF

# 3. 设置权限
chmod 600 backend/.env

# 4. 重启
docker-compose restart backend
```

---

**你的 Google API Key 现在是安全的！** ✅

请按照上述步骤重新配置你的 API Key。
