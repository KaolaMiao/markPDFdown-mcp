"""
Settings management with .env file persistence
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

# .env 文件路径（放在 backend 目录下）
ENV_FILE_PATH = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseModel):
    """LLM 配置设置"""
    provider: str = "openai"
    model: str = "gpt-4o"
    concurrency: int = 2
    temperature: float = 0.3
    max_tokens: int = 4096
    apiKey: Optional[str] = None
    baseUrl: Optional[str] = None
    maxTasks: int = 20  # 自动清理：保留最近的任务数量


def load_settings_from_env() -> Settings:
    """从环境变量和 .env 文件加载设置 (优先级: .env > ENV_VARS)"""
    # 1. 首先加载当前系统环境变量（作为基准/默认值）
    env_vars = os.environ.copy()
    
    # 2. 从 .env 文件加载 (如果存在，则覆盖环境变量，实现持久化修改生效)
    if ENV_FILE_PATH.exists():
        with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    value = value.strip().strip('"').strip("'")
                    env_vars[key.strip()] = value
    
    return Settings(
        provider=env_vars.get("LLM_PROVIDER", env_vars.get("provider", "openai")),
        model=env_vars.get("LLM_MODEL", env_vars.get("model", "gpt-4o")),
        concurrency=int(env_vars.get("LLM_CONCURRENCY", env_vars.get("concurrency", "2"))),
        temperature=float(env_vars.get("LLM_TEMPERATURE", "0.3")),
        max_tokens=int(env_vars.get("LLM_MAX_TOKENS", "4096")),
        maxTasks=int(env_vars.get("LLM_MAX_TASKS", env_vars.get("maxTasks", "20"))),
        apiKey=env_vars.get("LLM_API_KEY") or env_vars.get("OPENAI_API_KEY") or env_vars.get("apiKey"),
        baseUrl=env_vars.get("LLM_BASE_URL") or env_vars.get("OPENAI_API_BASE") or env_vars.get("baseUrl"),
    )


def save_settings_to_env(settings: Settings) -> None:
    """将设置保存到 .env 文件"""
    lines = []
    
    # 添加注释
    lines.append("# MarkPDFdown Server LLM Configuration")
    lines.append("# This file is auto-generated. You can also edit it manually.")
    lines.append("")
    
    # 保存设置
    lines.append(f'LLM_PROVIDER="{settings.provider}"')
    lines.append(f'LLM_MODEL="{settings.model}"')
    lines.append(f"LLM_CONCURRENCY={settings.concurrency}")
    lines.append(f"LLM_TEMPERATURE={settings.temperature}")
    lines.append(f"LLM_MAX_TOKENS={settings.max_tokens}")
    lines.append(f"LLM_MAX_TASKS={settings.maxTasks}")
    
    if settings.apiKey:
        lines.append(f'LLM_API_KEY="{settings.apiKey}"')
        # 同时设置 OpenAI 兼容的环境变量
        if settings.provider == "openai" or settings.model.startswith("gpt"):
            lines.append(f'OPENAI_API_KEY="{settings.apiKey}"')
        elif settings.provider == "anthropic" or settings.model.startswith("claude"):
            lines.append(f'ANTHROPIC_API_KEY="{settings.apiKey}"')
        elif settings.provider == "gemini" or settings.model.startswith("gemini"):
            lines.append(f'GEMINI_API_KEY="{settings.apiKey}"')
    
    if settings.baseUrl:
        lines.append(f'LLM_BASE_URL="{settings.baseUrl}"')
        lines.append(f'OPENAI_API_BASE="{settings.baseUrl}"')
    
    lines.append("")
    
    # 写入文件
    with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    # 同时设置当前进程的环境变量
    if settings.apiKey:
        os.environ["LLM_API_KEY"] = settings.apiKey
        if settings.provider == "openai" or settings.model.startswith("gpt"):
            os.environ["OPENAI_API_KEY"] = settings.apiKey
        elif settings.provider == "anthropic" or settings.model.startswith("claude"):
            os.environ["ANTHROPIC_API_KEY"] = settings.apiKey
        elif settings.provider == "gemini" or settings.model.startswith("gemini"):
            os.environ["GEMINI_API_KEY"] = settings.apiKey
    
    if settings.baseUrl:
        os.environ["LLM_BASE_URL"] = settings.baseUrl
        os.environ["OPENAI_API_BASE"] = settings.baseUrl


# 全局设置实例（启动时从 .env 加载）
current_settings = load_settings_from_env()
