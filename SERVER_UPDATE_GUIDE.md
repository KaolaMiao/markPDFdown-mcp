# 服务器更新指南

本文档说明如何在服务器上更新 MarkPDFdown-MCP 项目。

## 📋 目录

1. [快速开始](#快速开始)
2. [更新方式对比](#更新方式对比)
3. [详细操作步骤](#详细操作步骤)
4. [常见场景](#常见场景)
5. [故障排查](#故障排查)
6. [自动化方案](#自动化方案)

---

## 🚀 快速开始

### 最简单的方式

```bash
# 1. SSH 登录服务器
ssh user@your-server

# 2. 进入项目目录
cd /opt/1panel/apps/markPDFdown

# 3. 拉取代码并重启
git pull origin main
docker-compose down
docker-compose up -d --build
```

**预计耗时**: 2-5 分钟

---

## 🔄 更新方式对比

| 方式 | 命令 | 耗时 | 停机时间 | 适用场景 |
|------|------|------|---------|---------|
| **完整更新** | `docker-compose up -d --build` | 2-5分钟 | 10-30秒 | 代码有改动，推荐 |
| **仅重启** | `docker-compose restart` | 5-10秒 | 5秒 | 只改配置，无代码改动 |
| **单独后端** | `docker-compose up -d --build backend` | 1-2分钟 | 5-10秒 | 只改了后端代码 |
| **单独前端** | `docker-compose up -d --build frontend` | 1-2分钟 | 5-10秒 | 只改了前端代码 |

---

## 📖 详细操作步骤

### 方式一：使用自动化脚本（推荐）

#### Linux 服务器

```bash
# 1. 上传 update.sh 到服务器
scp update.sh user@server:/opt/1panel/apps/markPDFdown/

# 2. 登录服务器
ssh user@server

# 3. 进入项目目录
cd /opt/1panel/apps/markPDFdown

# 4. 给脚本执行权限
chmod +x update.sh

# 5. 执行更新
./update.sh --full      # 完整更新
# 或
./update.sh --backend   # 只更新后端
# 或
./update.sh --fast      # 快速重启
```

#### Windows 服务器

```batch
# 1. 上传 update.bat 到服务器

# 2. 登录服务器（使用 PowerShell 或 CMD）

# 3. 进入项目目录
cd C:\path\to\markPDFdown-mcp

# 4. 执行更新
update.bat --full      # 完整更新
```

---

### 方式二：手动更新

#### 步骤 1: 备份数据（重要！）

```bash
# 创建备份目录
mkdir -p backup_$(date +%Y%m%d_%H%M%S)

# 备份数据库
cp backend/tasks.db backup_$(date +%Y%m%d_%H%M%S)/

# 备份环境配置
cp backend/.env backup_$(date +%Y%m%d_%H%M%S)/
```

#### 步骤 2: 拉取最新代码

```bash
# 查看当前版本
git describe --tags --abbrev=0

# 拉取最新代码
git fetch origin
git log HEAD..origin/main --oneline  # 查看有什么更新

# 更新代码
git pull origin main
```

#### 步骤 3: 停止服务

```bash
# 停止并删除容器
docker-compose down

# 确认容器已停止
docker-compose ps
```

#### 步骤 4: 重新构建并启动

**完整更新**（推荐）:
```bash
docker-compose up -d --build
```

**只更新后端**:
```bash
docker-compose up -d --build backend
```

**只更新前端**:
```bash
docker-compose up -d --build frontend
```

#### 步骤 5: 验证服务

```bash
# 查看服务状态
docker-compose ps

# 查看后端日志
docker-compose logs --tail=50 backend

# 检查健康状态
curl http://localhost:18000/health

# 访问前端
curl -I http://localhost:18080
```

---

## 🎯 常见场景

### 场景 1: 只修改了 README 文档

```bash
git pull origin main
# 无需重启，文档在代码仓库中
```

### 场景 2: 修改了后端 Python 代码

```bash
git pull origin main
docker-compose up -d --build backend
```

### 场景 3: 修改了前端 React 代码

```bash
git pull origin main
docker-compose up -d --build frontend
```

### 场景 4: 修改了 Docker 配置

```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

### 场景 5: 修改了环境变量

```bash
# 方式一：编辑 docker-compose.yml
vim docker-compose.yml
docker-compose up -d

# 方式二：修改 backend/.env（推荐）
vim backend/.env
docker-compose restart backend
```

### 场景 6: 版本升级（v1.0.0 → v1.0.1）

```bash
# 查看最新标签
git fetch origin --tags
git tag -l "v1.*"

# 拉取特定版本
git fetch origin tag v1.0.1
git checkout v1.0.1

# 更新并重启
docker-compose down
docker-compose up -d --build
```

---

## ⚠️ 故障排查

### 问题 1: 拉取代码失败

**错误信息**:
```
fatal: refusing to merge unrelated histories
```

**解决方法**:
```bash
# 备份当前分支
git branch backup-branch

# 强制重置到远程
git fetch origin
git reset --hard origin/main

# 重新部署
docker-compose down
docker-compose up -d --build
```

### 问题 2: 构建失败

**错误信息**:
```
ERROR [backend] failed to solve
```

**解决方法**:
```bash
# 清理 Docker 缓存
docker system prune -a

# 强制重新构建
docker-compose build --no-cache backend
docker-compose up -d
```

### 问题 3: 容器启动失败

**检查步骤**:
```bash
# 1. 查看容器状态
docker-compose ps

# 2. 查看详细日志
docker-compose logs backend
docker-compose logs frontend

# 3. 检查端口占用
netstat -tuln | grep 18000
netstat -tuln | grep 18080

# 4. 检查磁盘空间
df -h
```

### 问题 4: 数据丢失

**恢复备份**:
```bash
# 找到最新的备份目录
ls -lt backup_* | head -1

# 恢复数据库
cp backup_20250129_120000/tasks.db backend/tasks.db

# 重启服务
docker-compose restart backend
```

### 问题 5: 网站无法访问

**检查清单**:
```bash
# 1. 容器是否运行
docker-compose ps

# 2. 端口是否监听
netstat -tuln | grep 18080

# 3. 防火墙是否放行
sudo ufw status
sudo ufw allow 18080/tcp

# 4. Nginx 配置（如果使用了反向代理）
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🤖 自动化方案

### 方案 1: 定时自动更新

创建定时任务（每天凌晨 3 点自动更新）：

```bash
# 编辑 crontab
crontab -e

# 添加以下行
0 3 * * * cd /opt/1panel/apps/markPDFdown && ./update.sh --fast >> /var/log/markpdfdown-update.log 2>&1
```

### 方案 2: Git Webhook 自动更新

使用 Docker 镜像配置 Webhook：

```bash
# 安装 webhook
docker pull almir/webhook

# 创建 webhook 配置
cat > webhook.json <<EOF
[
  {
    "id": "update-markpdfdown",
    "execute-command": "/opt/1panel/apps/markPDFdown/update.sh",
    "command-working-directory": "/opt/1panel/apps/markPDFdown",
    "trigger-rule": {
      "match": {
        "type": "payload",
        "regex": "{\"ref\": \"refs/heads/main\"}",
        "parameter": {
          "source": "payload"
        }
      }
    }
  }
]
EOF

# 启动 webhook
docker run -d -p 9000:9000 \
  -v /opt/1panel/apps/markPDFdown:/opt/1panel/apps/markPDFdown \
  -v $(pwd)/webhook.json:/etc/webhook.json \
  almir/webhook
```

在 GitHub 设置 Webhook：
- URL: `http://your-server:9000/hooks/update-markpdfdown`
- Content type: `application/json`

### 方案 3: CI/CD 自动部署

使用 GitHub Actions：

```yaml
# .github/workflows/deploy.yml
name: Deploy to Server

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/1panel/apps/markPDFdown
            git pull origin main
            docker-compose down
            docker-compose up -d --build
```

---

## 📊 更新前后检查清单

### 更新前

- [ ] 备份重要数据（tasks.db、.env）
- [ ] 查看当前版本：`git describe --tags`
- [ ] 查看即将更新：`git log HEAD..origin/main`
- [ ] 确认服务器磁盘空间充足（> 2GB）

### 更新后

- [ ] 检查容器状态：`docker-compose ps`
- [ ] 检查后端日志：`docker-compose logs backend`
- [ ] 检查健康状态：`curl http://localhost:18000/health`
- [ ] 访问前端：http://your-server:18080
- [ ] 测试上传文件功能
- [ ] 检查数据库连接正常

---

## 💡 最佳实践

### 1. 定期备份

```bash
# 每天自动备份数据库
0 2 * * * cp /opt/1panel/apps/markPDFdown/backend/tasks.db /backup/tasks_$(date +\%Y\%m\%d).db
```

### 2. 保留最近 7 天的备份

```bash
# 清理旧备份
find /backup -name "tasks_*.db" -mtime +7 -delete
```

### 3. 更新前通知用户

```bash
# 在网站首页添加维护公告
echo "系统正在更新，请稍后访问..." > frontend/public/maintenance.html
```

### 4. 使用健康检查端点

```bash
# 更新前检查服务状态
curl http://localhost:18000/health

# 更新后等待服务就绪
while ! curl -f http://localhost:18000/health; do
    echo "等待服务启动..."
    sleep 5
done
```

---

## 🔗 相关链接

- [Docker Compose 文档](https://docs.docker.com/compose/)
- [Docker 更新镜像最佳实践](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions 部署文档](https://docs.github.com/en/actions/deployment)

---

**需要帮助？**

如果遇到问题，请提供：
1. 错误信息完整日志
2. `docker-compose ps` 输出
3. `docker-compose logs backend` 输出
4. 服务器系统版本：`cat /etc/os-release`
