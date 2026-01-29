# 手动部署项目的服务器更新指南

## 📋 你的部署情况

- **部署方式**: 手动上传文件
- **服务器**: Linux
- **容器**: Docker + Docker Compose
- **本地配置**: 服务器上单独修改了 `backend/.env` 等文件
- **数据持久化**: 已配置 volume 挂载 ✅

---

## 🔍 当前部署结构

```
/opt/1panel/apps/markPDFdown/          # 你的项目目录
├── backend/
│   ├── files/                        # ✅ 转换产物（宿主机）
│   ├── tasks.db                      # ✅ 数据库（宿主机）
│   └── .env                          # ✅ 环境配置（宿主机，服务器上修改的）
├── frontend/
├── docker-compose.yml
└── markpdfdown_core/
```

**关键点**：
- ✅ `files/`、`tasks.db`、`.env` 在宿主机上
- ✅ 重建容器**不会**丢失这些文件
- ⚠️ 但 Git 拉取时**可能**覆盖这些文件

---

## 🚀 安全更新方案

### 方案一：保护本地配置后初始化 Git（推荐）

#### 第一步：检查是否已经是 Git 仓库

```bash
cd /opt/1panel/apps/markPDFdown
ls -la | grep .git
```

**如果看到 `.git` 目录**：已经是 Git 仓库，跳到"方案二"

**如果没有 `.git` 目录**：执行以下操作

#### 第二步：初始化 Git 仓库并配置 .gitignore

```bash
# 1. 创建 .gitignore 文件
cat > .gitignore << 'EOF'
# 数据和运行时文件（必须在服务器上）
backend/files/
backend/tasks.db
backend/.env

# 构建缓存
frontend/dist/
frontend/node_modules/
backend/.venv/

# IDE 配置
.vscode/
.idea/

# 本地备份
backup_*/

# Docker 体积文件
*.tar.gz
EOF

# 2. 初始化 Git 仓库
git init

# 3. 添加远程仓库（选择一种方式）
# 方式A: 使用 HTTPS（每次推送需要输入密码）
git remote add origin https://github.com/KaolaMiao/markPDFdown-mcp.git

# 方式B: 使用 SSH（推荐，配置 SSH 密钥后免密）
git remote add origin git@github.com:KaolaMiao/markPDFdown-mcp.git
```

#### 第三步：提交现有代码

```bash
# 1. 添加所有代码（.gitignore 会排除本地文件）
git add .

# 2. 创建初始提交
git commit -m "feat: 初始化服务器部署版本

- Docker Compose 配置
- 前后端代码
- 本地配置文件通过 .gitignore 保护
"

# 3. 推送到 GitHub
git branch -M main
git push -u origin main
```

#### 第四步：验证配置是否被保护

```bash
# 检查 .gitignore 是否生效
git status

# 应该看到：
# On branch main
# Your branch is up to date with 'origin/main'.
# nothing to commit, working tree clean
```

**不应该看到**：
- backend/files/
- backend/tasks.db
- backend/.env

✅ 如果这样，说明配置正确！

---

### 方案二：已经是 Git 仓库的情况

#### 第一步：更新 .gitignore

```bash
cd /opt/1panel/apps/markPDFdown

# 编辑 .gitignore
vim .gitignore
```

确保包含以下内容：

```gitignore
# 数据和运行时文件（必须在服务器上）
backend/files/
backend/tasks.db
backend/.env

# 其他...
```

#### 第二步：移除已跟踪的本地文件（如果被误提交）

```bash
# 检查是否被跟踪
git ls-files | grep -E "files/|tasks.db|\.env"

# 如果有输出，说明被误提交了，需要移除
git rm --cached -r backend/files/
git rm --cached backend/tasks.db
git rm --cached backend/.env

# 提交移除操作
git commit -m "chore: 从版本控制中移除服务器本地文件"
git push origin main
```

#### 第三步：再次验证

```bash
git status
# 应该显示：nothing to commit, working tree clean
```

---

## 🔄 日常更新流程

### 场景 1: GitHub 上有新代码，更新服务器

```bash
# 1. 进入项目目录
cd /opt/1panel/apps/markPDFdown

# 2. 拉取最新代码
git fetch origin
git log HEAD..origin/main --oneline   # 查看有什么更新

# 3. 确认本地配置不会被覆盖
git status
# 应该看不到 backend/.env 等文件

# 4. 合并最新代码
git pull origin main
# 或者
git pull
```

#### 为什么安全？

因为 `.gitignore` 文件保护了这些文件：
- `backend/files/` - 已忽略，不会被拉取覆盖
- `backend/tasks.db` - 已忽略，不会被拉取覆盖
- `backend/.env` - 已忽略，不会被拉取覆盖

### 场景 2: 重建容器（代码有改动）

```bash
# 1. 拉取代码
git pull origin main

# 2. 停止容器
docker-compose down

# 3. 重建并启动
docker-compose up -d --build

# 4. 查看日志
docker-compose logs -f backend
# 按 Ctrl+C 退出
```

**你的配置文件是安全的！**
- `backend/.env` 在宿主机
- Docker volume 映射确保容器能看到这个文件
- 重建容器不会删除宿主机上的文件

### 场景 3: 只修改了 GitHub 上的配置文件

例如：`docker-compose.yml` 有更新

```bash
# 拉取代码
git pull origin main

# 重启服务（让新配置生效）
docker-compose down
docker-compose up -d
```

---

## ⚠️ 重要：配置文件管理

### 当前你的配置文件在服务器上

```bash
# 查看服务器上的配置
cat backend/.env
```

**可能的内容**：
```
API_KEY=your_api_key_here
API_BASE=http://p2m.384921.XYZ/api/v1
MODEL_NAME=gemini-3.0-flash-exp
CONCURRENCY=2
MAX_TASKS=20
```

### 更新配置文件的正确方式

**❌ 错误方式**：
```bash
# 直接在 GitHub 上修改 backend/.env
git pull
# 这样会覆盖服务器上的本地配置！
```

**✅ 正确方式**：
```bash
# 1. 在服务器上直接编辑
vim backend/.env

# 2. 重启后端让配置生效
docker-compose restart backend

# 3. 不提交 .env 到 Git
# .gitignore 已经忽略了这个文件
```

### 如何在本地和服务器上使用不同的配置？

**选项 1: 使用环境变量文件（推荐）**

在 `docker-compose.yml` 中已经配置：
```yaml
environment:
  - API_KEY=${API_KEY}
```

服务器上创建 `.env` 文件：
```bash
# 在项目根目录创建
cat > .env << 'EOF'
API_KEY=your_production_key
MODEL_NAME=gemini-3.0-flash-exp
EOF
```

更新 `docker-compose.yml`：
```yaml
environment:
  - API_KEY=${API_KEY}                    # 从 .env 文件读取
  - MODEL_NAME=${MODEL_NAME:-gemini-3.0-flash-exp}  # 默认值
```

**选项 2: 使用配置模板**

创建 `backend/.env.example`（提交到 Git）：
```bash
# 示例配置
API_KEY=your_api_key_here
MODEL_NAME=gemini-3.0-flash-exp
CONCURRENCY=2
MAX_TASKS=20
```

服务器上：
```bash
# 复制示例配置
cp backend/.env.example backend/.env

# 修改为实际值
vim backend/.env
```

---

## 🛠️ 使用自动化更新脚本

### 上传脚本到服务器

```bash
# 在你本地电脑上执行
scp update.sh user@your-server:/opt/1panel/apps/markPDFdown/
```

### 在服务器上使用

```bash
# 1. 登录服务器
ssh user@your-server

# 2. 进入项目目录
cd /opt/1panel/apps/markPDFdown

# 3. 给脚本执行权限
chmod +x update.sh

# 4. 执行更新
./update.sh --full
```

**脚本会自动**：
- ✅ 拉取最新代码
- ✅ 备份 `backend/.env` 和 `backend/tasks.db`
- ✅ 重建容器
- ✅ 健康检查
- ✅ 恢复配置（如果需要）

---

## 🔍 验证配置是否持久化

### 测试步骤

```bash
# 1. 修改配置
echo "TEST_CONFIG=123" >> backend/.env

# 2. 重启容器
docker-compose restart backend

# 3. 进入容器查看配置
docker exec -it markpdfdown-backend cat /app/backend/.env

# 应该能看到 TEST_CONFIG=123

# 4. 重建容器
docker-compose down
docker-compose up -d --build

# 5. 再次查看配置
docker exec -it markpdfdown-backend cat /app/backend/.env

# 配置仍然在！✓
```

---

## 📊 完整更新流程示例

### 示例场景：GitHub 上更新了后端代码

```bash
# === 在服务器上执行 ===

# 1. 进入项目目录
cd /opt/1panel/apps/markPDFdown

# 2. 查看当前状态
git status
# 输出: On branch main, nothing to commit

# 3. 查看有什么更新
git fetch origin
git log HEAD..origin/main --oneline
# 输出:
# a8762cf chore: 添加服务器更新工具
# d6bde1b docs: 重写 README 文档

# 4. 拉取代码
git pull origin main
# 输出:
# Updating a8762cf..d6bde1b
# Fast-forward
# README.md | 2 +-
# 1 file changed, 2 insertions(+), 1 deletion(-)

# 5. 检查本地文件是否还在
ls -la backend/.env backend/tasks.db
# 都还在！✓

# 6. 停止容器
docker-compose down

# 7. 重建并启动
docker-compose up -d --build

# 8. 查看日志
docker-compose logs -f backend
```

---

## 🆘 故障排查

### 问题 1: git pull 提示冲突

```bash
error: Your local changes to the following files would be overwritten by merge:
        backend/.env
```

**原因**: `.gitignore` 没配置好，文件被跟踪了

**解决**:
```bash
# 1. 取消合并
git merge --abort

# 2. 移除被跟踪的文件
git rm --cached backend/.env

# 3. 确保 .gitignore 包含这个文件
echo "backend/.env" >> .gitignore

# 4. 提交
git add .gitignore
git commit -m "chore: 忽略本地配置文件"

# 5. 再次拉取
git pull origin main
```

### 问题 2: 配置文件丢失了

```bash
# 检查备份
ls -la backup_*

# 恢复最近的备份
cp backup_20250129_120000/.env backend/.env
cp backup_20250129_120000/tasks.db backend/tasks.db

# 重启服务
docker-compose restart
```

### 问题 3: 容器启动失败

```bash
# 查看详细日志
docker-compose logs backend

# 检查配置文件是否存在
ls -la backend/.env

# 进入容器检查
docker run --rm -it \
  -v $(pwd)/backend:/app/backend \
  -w /app/backend \
  python:3.10-slim \
  bash
```

---

## 💡 最佳实践

### 1. 定期备份

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * cp /opt/1panel/apps/markPDFdown/backend/.env /backup/.env_$(date +\%Y\%m\%d)
0 2 * * * cp /opt/1panel/apps/markPDFdown/backend/tasks.db /backup/tasks.db_$(date +\%Y\%m\%d)
```

### 2. 记录配置变更

```bash
# 创建配置变更日志
vim CHANGELOG.config

# 示例：
# 2025-01-29: 修改 MAX_TASKS=20
# 2025-01-30: 更换 API_KEY
```

### 3. 使用环境变量管理

```bash
# 在服务器上创建配置文件
cat > /opt/markpdfdown-env.sh << 'EOF'
export MARKPDFDOWN_API_KEY="sk-xxxxx"
export MARKPDFDOWN_MODEL_NAME="gemini-3.0-flash-exp"
EOF

# 在 docker-compose.yml 中引用
# env_file:
#   - /opt/markpdfdown-env.sh
```

---

## 📝 快速参考卡片

```bash
# === 日常更新 ===
cd /opt/1panel/apps/markPDFdown
git pull origin main
docker-compose down
docker-compose up -d --build
docker-compose ps

# === 查看日志 ===
docker-compose logs -f backend   # 后端日志
docker-compose logs -f frontend  # 前端日志
docker-compose logs              # 所有日志

# === 修改配置 ===
vim backend/.env
docker-compose restart backend

# === 备份数据 ===
cp backend/.env backup/.env_$(date +%Y%m%d)
cp backend/tasks.db backup/tasks.db_$(date +%Y%m%d)

# === 检查健康 ===
curl http://localhost:18000/health
curl -I http://localhost:18080
```

---

## 🎯 总结

### ✅ 你的配置是安全的

- `.gitignore` 忽略了 `backend/.env`
- Docker volume 保证了数据持久化
- 拉取代码不会覆盖服务器上的本地文件

### ✅ 推荐的更新流程

```bash
git pull origin main          # 拉取代码
docker-compose down          # 停止容器
docker-compose up -d --build # 重建启动
docker-compose ps             # 检查状态
```

### ✅ 配置文件修改

```bash
# 在服务器上直接编辑
vim backend/.env

# 重启服务
docker-compose restart backend
```

---

**需要帮助？**

如果遇到问题，提供以下信息：
1. `git status` 输出
2. `git log HEAD..origin/main --oneline` 输出
3. `docker-compose ps` 输出
4. `docker-compose logs backend` 的最后 50 行
