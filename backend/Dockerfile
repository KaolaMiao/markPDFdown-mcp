# 使用官方 Python 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，包含 backend 和 core 库
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend:/app/markpdfdown_core/src

# 安装 uv 包管理器
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 复制依赖配置 (假设构建上下文是根目录)
COPY backend/pyproject.toml backend/uv.lock ./backend/

# 安装依赖
WORKDIR /app/backend
RUN uv sync --frozen --no-install-project

# 复制源代码
# 这里假设 docker context 是项目根目录
COPY backend/src ./src
COPY markpdfdown_core/src /app/markpdfdown_core/src

# 创建文件存储目录
RUN mkdir -p files/tasks files/uploads

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uv", "run", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
