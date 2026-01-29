# 🔒 安全修复操作清单

## ⚠️ 发现的问题

### 1. backend/.env 包含真实的 API Key
```
LLM_API_KEY="AIzaSyC-CQz60ORyjcat8M1SpBQaIUlmMM2HhzY"
```
**状态**: ✅ 幸运，文件未被提交到 GitHub（已通过 .gitignore 保护）

### 2. docker-compose.yml 有硬编码的 URL
```yaml
API_BASE=http://p2m.384921.XYZ/api/v1
```
**状态**: ⚠️ 虽然不是密钥，但应该使用环境变量

---

## ✅ 立即执行的安全修复

### 第一步：清理 backend/.env 中的真实密钥

```bash
# 备份当前配置
cp backend/.env backend/.env.backup

# 编辑文件，移除真实 API Key
vim backend/.env
```

**将第 10 行改为**：
```bash
# 原来的：LLM_API_KEY="AIzaSyC-CQz60ORyjcat8M1SpBQaIUlmMM2HhzY"
# 改为：
LLM_API_KEY="your-api-key-here"
```

### 第二步：创建安全的配置模板

```bash
# 创建 .env.example 文件
cat > backend/.env.example << 'EOF'
# MarkPDFdown Server LLM Configuration
# 这是配置模板，复制此文件为 .env 并填入真实值

# LLM 提供商配置
LLM_PROVIDER="gemini"
LLM_MODEL="gemini-3.0-flash-exp"
LLM_CONCURRENCY=2
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=8192
LLM_MAX_TASKS=20

# API 密钥（根据提供商选择一个填写）
# Google Gemini
GEMINI_API_KEY="your-gemini-api-key-here"

# OpenAI
OPENAI_API_KEY="your-openai-api-key-here"

# Anthropic Claude
ANTHROPIC_API_KEY="your-anthropic-api-key-here"

# API 基础 URL（如果使用代理或自定义端点）
LLM_BASE_URL=""
OPENAI_API_BASE=""

# Docker 配置
USE_CELERY=false
EOF
```

### 第三步：更新 docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: markpdfdown-backend
    restart: always
    environment:
      # 从宿主机的 .env 文件读取（推荐）
      # 或从项目根目录的 .env 读取
      - LLM_PROVIDER=${LLM_PROVIDER:-gemini}
      - LLM_MODEL=${LLM_MODEL:-gemini-3.0-flash-exp}
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_CONCURRENCY=${LLM_CONCURRENCY:-2}
      - LLM_TEMPERATURE=${LLM_TEMPERATURE:-0.3}
      - LLM_MAX_TOKENS=${LLM_MAX_TOKENS:-8192}
      - LLM_MAX_TASKS=${LLM_MAX_TASKS:-20}
      - USE_CELERY=${USE_CELERY:-false}
      - PYTHONPATH=/app/backend:/app/markpdfdown_core/src
    volumes:
      - ./backend/files:/app/backend/files
      - ./backend/tasks.db:/app/backend/tasks.db
      - ./backend/.env:/app/backend/.env
    ports:
      - "127.0.0.1:18000:8000"

  frontend:
    build:
      context: ./frontend
    container_name: markpdfdown-frontend
    restart: always
    ports:
      - "127.0.0.1:18080:80"
    depends_on:
      - backend
```

---

## 📝 .env.example 最佳实践

### 应该包含的内容

✅ **包含**：
- 配置项名称
- 说明文字和注释
- 默认值（如果安全）
- 示例值（用占位符）

❌ **不包含**：
- 真实的 API Key
- 真实的密码
- 真实的 URL
- 任何敏感信息

### 格式示例

```bash
# 好的示例
DATABASE_URL="postgresql://user:password@localhost/db"
export DEFAULT_TIMEOUT=30

# 不好的示例
DATABASE_URL="postgresql://admin:supersecretpass@localhost/production"
export STRIPE_SECRET_KEY="sk_live_51ABC..."
```

---

## 🔒 密钥管理最佳实践

### 开发环境

```bash
# 使用 .env 文件
cat > .env << 'EOF'
API_KEY="dev-key-12345"
DATABASE_URL="postgresql://localhost:5432/dev"
EOF

# 确保 .env 在 .gitignore 中
echo ".env" >> .gitignore
```

### 生产环境

```bash
# 在服务器上手动创建 .env
cat > backend/.env << 'EOF'
LLM_API_KEY="${PROD_API_KEY}"
DATABASE_URL="${PROD_DATABASE_URL}"
EOF

# 设置权限（只有所有者可读）
chmod 600 backend/.env
```

### CI/CD 环境

```yaml
# GitHub Actions
env:
  API_KEY: ${{ secrets.API_KEY }}
  DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

---

## 🛡️ 检查清单

### 提交前检查

```bash
# 1. 检查是否有真实密钥
grep -r "sk-" . --exclude-dir=node_modules --exclude-dir=.venv
grep -r "AIza" . --exclude-dir=node_modules --exclude-dir=.venv
grep -r "AKIA" . --exclude-dir=node_modules --exclude-dir=.venv
grep -r "ya29" . --exclude-dir=node_modules --exclude-dir=.venv

# 2. 检查 .env 文件
git ls-files | grep "\.env"

# 3. 检查 .gitignore
grep "\.env" .gitignore

# 4. 查看暂存区
git status
```

### 工具辅助

```bash
# 使用 git-secrets 检查
# 安装：brew install git-secrets

# 扫描整个仓库
git secrets --scan

# 注册敏感模式
git secrets --register 'AIza[0-9A-Za-z\\-_]{35}'
git secrets --register 'sk-[a-zA-Z0-9]{32,}'
```

---

## 🚨 如果密钥已经泄露

### Google API Key

1. **立即撤销密钥**
   - 访问：https://console.cloud.google.com/apis/credentials
   - 找到对应的 API Key
   - 点击删除或撤销

2. **创建新密钥**
   - 创建新的 API Key
   - 更新服务器上的配置

3. **清理历史记录**（如果已提交）
   ```bash
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch backend/.env' \
     --prune-empty HEAD
   git push origin main --force
   ```

### GitHub 密钥

1. 访问：https://github.com/settings/tokens
2. 撤销泄露的 token
3. 生成新的 token
4. 更新本地配置

---

## 📚 参考资源

- [OWASP 密钥管理最佳实践](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Git 忽略敏感文件](https://help.github.com/en/github/using-git/ignoring-files)
- [Docker 环境变量](https://docs.docker.com/engine/reference/commandline/daemon/)
- [12-Factor App 密钥管理](https://12factor.net/config)

---

**重要提醒**：
- ✅ 定期更换 API Key（建议每 90 天）
- ✅ 使用不同的密钥用于开发和生产
- ✅ 限制 API Key 的权限范围
- ✅ 监控 API 使用情况，发现异常立即撤销
