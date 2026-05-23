import os
import tomllib


DEFAULT_CONFIG = {
    "project": {
        "name": "bili-video-notes-workflow",
        "output_dir": "outputs",
        "log_dir": "logs",
        "temp_dir": "temp",
        "download_dir": "downloads",
    },
    "whisper": {
        "model": "medium",
        "language": "Chinese",
        "device": "cuda",
        "compute_type": "auto",
    },
    "deepseek": {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "max_chunk_minutes": 12,
        "max_retries": 3,
        "retry_delay_seconds": 5,
        "api_key": "",
    },
    "screenshot": {
        "enabled": False,
        "strategy": "learning",
        "min_interval_seconds": 3,
        "max_avg_per_minute": 6,
        "max_images_per_unit": 2,
        "prefer_after_action_seconds": 1.5,
        "difference_threshold": 0.85,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: str = "config.toml") -> dict:
    config = DEFAULT_CONFIG.copy()

    if os.path.exists(config_path):
        try:
            with open(config_path, "rb") as f:
                user_config = tomllib.load(f)
            config = _deep_merge(config, user_config)
        except Exception as e:
            print(f"[WARN] 读取 config.toml 失败: {e}，使用默认配置")

    # API Key is intentionally not loaded from .env or config.toml.
    # Runtime code injects it from the local encrypted secret database.
    config.setdefault("deepseek", {})
    config["deepseek"]["api_key"] = ""
    return config


def get_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_path(config: dict, key: str) -> str:
    project_root = get_project_root()
    relative = config["project"].get(key, key)
    if os.path.isabs(relative):
        return relative
    return os.path.join(project_root, relative)


def get_tasks(config: dict) -> list:
    return config.get("tasks", [])


def get_task_by_name(config: dict, name: str) -> dict | None:
    for task in get_tasks(config):
        if task.get("name") == name:
            return task
    return None
