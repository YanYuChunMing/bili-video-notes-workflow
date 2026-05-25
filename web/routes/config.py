import os
import json
import tomllib

from fastapi import APIRouter, HTTPException

from web.models import (
    ApiResponse, ConfigUpdateRequest,
    ConfigDisplay, WhisperConfig, DeepseekConfig, ScreenshotConfig, ProjectConfig,
)

router = APIRouter(prefix="/api/config", tags=["config"])


def _get_config_for_display(config: dict) -> ConfigDisplay:
    return ConfigDisplay(
        project=ProjectConfig(
            name=config["project"]["name"],
            output_dir=config["project"]["output_dir"],
            log_dir=config["project"]["log_dir"],
            temp_dir=config["project"]["temp_dir"],
            download_dir=config["project"]["download_dir"],
        ),
        whisper=WhisperConfig(
            model=config["whisper"]["model"],
            language=config["whisper"]["language"],
            device=config["whisper"]["device"],
            compute_type=config["whisper"].get("compute_type", "auto"),
        ),
        deepseek=DeepseekConfig(
            model=config["deepseek"]["model"],
            base_url=config["deepseek"]["base_url"],
            has_api_key=bool(config["deepseek"].get("api_key", "")),
            max_chunk_minutes=config["deepseek"].get("max_chunk_minutes", 12),
        ),
        screenshot=ScreenshotConfig(
            enabled=config["screenshot"].get("enabled", False),
            strategy=config["screenshot"].get("strategy", "learning"),
            min_interval_seconds=config["screenshot"].get("min_interval_seconds", 3),
            max_avg_per_minute=config["screenshot"].get("max_avg_per_minute", 6),
            max_images_per_unit=config["screenshot"].get("max_images_per_unit", 2),
            difference_threshold=config["screenshot"].get("difference_threshold", 0.85),
        ),
    )


@router.get("")
def get_config():
    from src import config_loader
    config = config_loader.load_config("config.toml")
    return ApiResponse(data=_get_config_for_display(config)).model_dump()


@router.put("", response_model=ApiResponse)
def update_config(req: ConfigUpdateRequest):
    from src import config_loader

    project_root = config_loader.get_project_root()
    config_path = os.path.join(project_root, "config.toml")
    env_path = os.path.join(project_root, ".env")

    if not os.path.exists(config_path):
        return ApiResponse(code=500, message="config.toml 不存在").model_dump()

    config = config_loader.load_config(config_path)

    if req.whisper_model is not None:
        config["whisper"]["model"] = req.whisper_model
    if req.whisper_language is not None:
        config["whisper"]["language"] = req.whisper_language
    if req.whisper_device is not None:
        config["whisper"]["device"] = req.whisper_device
    if req.whisper_compute_type is not None:
        config["whisper"]["compute_type"] = req.whisper_compute_type
    if req.deepseek_model is not None:
        config["deepseek"]["model"] = req.deepseek_model
    if req.deepseek_base_url is not None:
        config["deepseek"]["base_url"] = req.deepseek_base_url
    if req.screenshot_enabled is not None:
        config["screenshot"]["enabled"] = req.screenshot_enabled
    if req.screenshot_strategy is not None:
        config["screenshot"]["strategy"] = req.screenshot_strategy
    if req.screenshot_min_interval_seconds is not None:
        config["screenshot"]["min_interval_seconds"] = req.screenshot_min_interval_seconds
    if req.screenshot_max_avg_per_minute is not None:
        config["screenshot"]["max_avg_per_minute"] = req.screenshot_max_avg_per_minute
    if req.screenshot_difference_threshold is not None:
        config["screenshot"]["difference_threshold"] = req.screenshot_difference_threshold

    _write_toml_config(config_path, config)

    if req.deepseek_api_key is not None:
        _write_env_file(env_path, req.deepseek_api_key, req.deepseek_base_url)

    return ApiResponse(message="配置已更新").model_dump()


@router.get("/check", response_model=ApiResponse)
def check_api_key():
    from src import config_loader
    from openai import OpenAI

    config = config_loader.load_config("config.toml")
    api_key = config["deepseek"].get("api_key", "")

    if not api_key:
        return ApiResponse(code=400, message="未配置 API Key").model_dump()

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=config["deepseek"]["base_url"],
        )
        response = client.chat.completions.create(
            model=config["deepseek"]["model"],
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        return ApiResponse(data={"valid": True, "message": config["deepseek"]["model"]}).model_dump()
    except Exception as e:
        return ApiResponse(code=400, data={"valid": False, "message": str(e)}).model_dump()


def _write_toml_config(config_path: str, config: dict):
    lines = []
    lines.append("[project]")
    lines.append(f'name = "{config["project"]["name"]}"')
    lines.append(f'output_dir = "{config["project"]["output_dir"]}"')
    lines.append(f'log_dir = "{config["project"]["log_dir"]}"')
    lines.append(f'temp_dir = "{config["project"]["temp_dir"]}"')
    lines.append(f'download_dir = "{config["project"]["download_dir"]}"')
    lines.append("")
    lines.append("[whisper]")
    lines.append(f'model = "{config["whisper"]["model"]}"')
    lines.append(f'language = "{config["whisper"]["language"]}"')
    lines.append(f'device = "{config["whisper"]["device"]}"')
    if "compute_type" in config["whisper"]:
        lines.append(f'compute_type = "{config["whisper"]["compute_type"]}"')
    lines.append("")
    lines.append("[deepseek]")
    lines.append(f'model = "{config["deepseek"]["model"]}"')
    lines.append(f'base_url = "{config["deepseek"]["base_url"]}"')
    lines.append(f'max_chunk_minutes = {config["deepseek"].get("max_chunk_minutes", 12)}')
    lines.append(f'max_retries = {config["deepseek"].get("max_retries", 3)}')
    lines.append(f'retry_delay_seconds = {config["deepseek"].get("retry_delay_seconds", 5)}')
    lines.append("")
    lines.append("[screenshot]")
    ss = config["screenshot"]
    enabled_str = "true" if ss.get("enabled", False) else "false"
    lines.append(f"enabled = {enabled_str}")
    lines.append(f'strategy = "{ss.get("strategy", "learning")}"')
    lines.append(f'min_interval_seconds = {ss.get("min_interval_seconds", 3)}')
    lines.append(f'max_avg_per_minute = {ss.get("max_avg_per_minute", 6)}')
    lines.append(f'max_images_per_unit = {ss.get("max_images_per_unit", 2)}')
    lines.append(f'prefer_after_action_seconds = {ss.get("prefer_after_action_seconds", 1.5)}')
    lines.append(f'difference_threshold = {ss.get("difference_threshold", 0.85)}')

    with open(config_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _write_env_file(env_path: str, api_key: str, base_url: str = None):
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

    new_lines = []
    key_updated = False
    url_updated = False

    for line in lines:
        if line.startswith("DEEPSEEK_API_KEY="):
            new_lines.append(f"DEEPSEEK_API_KEY={api_key}")
            key_updated = True
        elif line.startswith("DEEPSEEK_BASE_URL=") and base_url:
            new_lines.append(f"DEEPSEEK_BASE_URL={base_url}")
            url_updated = True
        else:
            new_lines.append(line)

    if not key_updated:
        new_lines.append(f"DEEPSEEK_API_KEY={api_key}")
    if not url_updated:
        new_lines.append(f"DEEPSEEK_BASE_URL={base_url or 'https://api.deepseek.com'}")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")
