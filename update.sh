#!/bin/bash
# 服务器更新脚本
# 使用方法：./update.sh [选项]
# 选项：
#   --full     完整更新（重建所有镜像）
#   --backend 只更新后端
#   --frontend 只更新前端
#   --fast    快速更新（不重建，仅重启）

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示使用说明
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --full     完整更新（重建所有镜像）- 推荐"
    echo "  --backend  只更新后端服务"
    echo "  --frontend 只更新前端服务"
    echo "  --fast     快速更新（不重建，仅重启）"
    echo "  --help     显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --full       # 完整更新所有服务"
    echo "  $0 --backend    # 只更新后端"
    echo "  $0 --fast       # 快速重启（无代码更新）"
}

# 默认选项
UPDATE_MODE="full"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            UPDATE_MODE="full"
            shift
            ;;
        --backend)
            UPDATE_MODE="backend"
            shift
            ;;
        --frontend)
            UPDATE_MODE="frontend"
            shift
            ;;
        --fast)
            UPDATE_MODE="fast"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            error "未知选项: $1"
            show_usage
            exit 1
            ;;
    esac
done

# 检查是否在项目目录
if [ ! -f "docker-compose.yml" ]; then
    error "未找到 docker-compose.yml，请在项目根目录执行此脚本"
    exit 1
fi

info "========================================="
info "  MarkPDFdown-MCP 服务器更新工具"
info "========================================="
info ""
info "更新模式: $UPDATE_MODE"
info ""

# 1. 检查 Git 状态
info "步骤 1/5: 检查 Git 状态..."
if [ ! -d ".git" ]; then
    error "不是 Git 仓库"
    exit 1
fi

# 显示当前版本
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "未发布")
info "当前版本: $CURRENT_VERSION"
info ""

# 2. 拉取最新代码
info "步骤 2/5: 拉取最新代码..."
git fetch origin
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" == "$REMOTE" ]; then
    success "代码已是最新版本"
    if [ "$UPDATE_MODE" == "fast" ]; then
        info "继续执行快速重启..."
    else
        info "如需强制重建，请使用: $0 --full"
        exit 0
    fi
else
    git pull origin main
    success "代码已更新"
fi
info ""

# 3. 备份数据（可选）
info "步骤 3/5: 备份重要数据..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 备份数据库
if [ -f "backend/tasks.db" ]; then
    cp backend/tasks.db $BACKUP_DIR/
    info "已备份数据库到: $BACKUP_DIR/tasks.db"
fi

# 备份环境配置
if [ -f "backend/.env" ]; then
    cp backend/.env $BACKUP_DIR/
    info "已备份配置到: $BACKUP_DIR/.env"
fi

success "备份完成"
info ""

# 4. 停止服务
info "步骤 4/5: 停止服务..."
docker-compose down
success "服务已停止"
info ""

# 5. 根据模式更新
info "步骤 5/5: 更新服务..."

case $UPDATE_MODE in
    full)
        info "执行完整更新（重建所有镜像）..."
        docker-compose up -d --build
        ;;

    backend)
        info "只更新后端服务..."
        docker-compose up -d --build backend
        ;;

    frontend)
        info "只更新前端服务..."
        docker-compose up -d --build frontend
        ;;

    fast)
        info "快速重启（不重建镜像）..."
        docker-compose up -d
        ;;
esac

success "服务已启动"
info ""

# 等待服务启动
info "等待服务启动..."
sleep 5

# 检查服务状态
info "检查服务状态..."
docker-compose ps

# 检查后端健康
info ""
info "检查后端健康..."
if curl -f http://localhost:18000/health &>/dev/null; then
    success "后端服务正常 ✓"
else
    error "后端服务异常 ✗"
    info "查看日志: docker-compose logs backend"
    exit 1
fi

# 检查前端
info "检查前端服务..."
if curl -f http://localhost:18080 &>/dev/null; then
    success "前端服务正常 ✓"
else
    warning "前端服务可能异常，请手动检查"
fi

info ""
success "========================================="
success "  更新完成！"
success "========================================="
info ""
info "查看日志:"
info "  docker-compose logs -f backend"
info "  docker-compose logs -f frontend"
info ""
info "查看服务状态:"
info "  docker-compose ps"
info ""
info "如有问题，回滚备份:"
info "  cp $BACKUP_DIR/tasks.db backend/tasks.db"
info "  docker-compose restart"
