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
    """
    将设置保存到 .env 文件（增量更新模式）

    策略：
    1. 读取现有的 .env 文件
    2. 只更新 LLM 相关的配置项
    3. 保留其他配置（如 USE_CELERY、其他自定义配置）
    """
    # 读取现有配置
    existing_lines = []
    if ENV_FILE_PATH.exists():
        with open(ENV_FILE_PATH, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()

    # 需要更新的 LLM 配置项
    llm_keys = {
        "LLM_PROVIDER",
        "LLM_MODEL",
        "LLM_CONCURRENCY",
        "LLM_TEMPERATURE",
        "LLM_MAX_TOKENS",
        "LLM_MAX_TASKS",
        "LLM_API_KEY",
        "LLM_BASE_URL",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "OPENAI_API_BASE",
    }

    # 跟踪已更新的配置
    updated_keys = set()

    # 构建新的文件内容
    new_lines = []
    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            # 保留空行和注释
            new_lines.append(line)
            continue

        # 解析键值对
        if "=" in stripped:
            key, _, _ = stripped.partition("=")
            key = key.strip()

            if key in llm_keys:
                # 更新 LLM 配置项
                updated_keys.add(key)
                new_value = _get_env_value(settings, key)
                if new_value is not None:
                    new_lines.append(f"{new_value}\n")
                else:
                    # 如果值不存在，跳过这一行（删除）
                    continue
            else:
                # 保留非 LLM 配置项
                new_lines.append(line)

    # 添加缺失的 LLM 配置项
    for key in llm_keys:
        if key not in updated_keys:
            new_value = _get_env_value(settings, key)
            if new_value is not None:
                new_lines.append(f"{new_value}\n")

    # 写入文件
    with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

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


def _get_env_value(settings: Settings, key: str) -> Optional[str]:
    """根据配置键生成环境变量值"""
    if key == "LLM_PROVIDER":
        return f'LLM_PROVIDER="{settings.provider}"'
    elif key == "LLM_MODEL":
        return f'LLM_MODEL="{settings.model}"'
    elif key == "LLM_CONCURRENCY":
        return f"LLM_CONCURRENCY={settings.concurrency}"
    elif key == "LLM_TEMPERATURE":
        return f"LLM_TEMPERATURE={settings.temperature}"
    elif key == "LLM_MAX_TOKENS":
        return f"LLM_MAX_TOKENS={settings.max_tokens}"
    elif key == "LLM_MAX_TASKS":
        return f"LLM_MAX_TASKS={settings.maxTasks}"
    elif key == "LLM_API_KEY":
        if settings.apiKey:
            return f'LLM_API_KEY="{settings.apiKey}"'
        return None
    elif key == "LLM_BASE_URL":
        if settings.baseUrl:
            return f'LLM_BASE_URL="{settings.baseUrl}"'
        return None
    elif key == "OPENAI_API_BASE":
        if settings.baseUrl:
            return f'OPENAI_API_BASE="{settings.baseUrl}"'
        return None
    elif key == "OPENAI_API_KEY":
        if settings.apiKey and (settings.provider == "openai" or settings.model.startswith("gpt")):
            return f'OPENAI_API_KEY="{settings.apiKey}"'
        return None
    elif key == "ANTHROPIC_API_KEY":
        if settings.apiKey and (settings.provider == "anthropic" or settings.model.startswith("claude")):
            return f'ANTHROPIC_API_KEY="{settings.apiKey}"'
        return None
    elif key == "GEMINI_API_KEY":
        if settings.apiKey and (settings.provider == "gemini" or settings.model.startswith("gemini")):
            return f'GEMINI_API_KEY="{settings.apiKey}"'
        return None

    return None


# 全局设置实例（启动时从 .env 加载）
current_settings = load_settings_from_env()
