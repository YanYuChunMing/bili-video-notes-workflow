import os
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.secret_store import (
    SECRET_DEEPSEEK_API_KEY,
    SecretStoreError,
    delete_secret,
    get_status,
    save_secret,
)
from src import config_loader

try:
    import tomllib as tomli_reader
except ImportError:
    import tomli as tomli_reader

try:
    import tomli_w

    HAS_TOML_WRITER = True
except ImportError:
    HAS_TOML_WRITER = False


def _env_contains_legacy_key(project_root: str) -> bool:
    env_path = Path(project_root) / ".env"
    if not env_path.exists():
        return False
    try:
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith("DEEPSEEK_API_KEY=") and line.split("=", 1)[1].strip():
                return True
    except Exception:
        return False
    return False


def save_config_toml(config_path: str, config: dict) -> bool:
    if not HAS_TOML_WRITER:
        st.error("缺少 tomli_w，无法保存配置。请运行: pip install tomli-w")
        return False

    deepseek = dict(config.get("deepseek", {}))
    deepseek.pop("api_key", None)
    sections_to_save = {
        "project": config.get("project", {}),
        "whisper": config.get("whisper", {}),
        "deepseek": deepseek,
        "screenshot": config.get("screenshot", {}),
    }

    existing_tasks = []
    if os.path.exists(config_path):
        try:
            with open(config_path, "rb") as f:
                existing = tomli_reader.load(f)
            existing_tasks = existing.get("tasks", [])
        except Exception:
            pass

    full_config = {**sections_to_save, "tasks": existing_tasks}

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            tomli_w.dump(full_config, f)
        return True
    except Exception as exc:
        st.error(f"保存 config.toml 失败: {exc}")
        return False


def _render_secret_status() -> None:
    status = get_status(SECRET_DEEPSEEK_API_KEY)
    if st.session_state.get("deepseek_api_key"):
        st.success("当前会话已输入 API Key。")
    elif status.available:
        st.success(f"本地数据库已保存 API Key。存储: {status.db_path}")
    else:
        st.info("未配置 API Key。AI 标点、摘要、思维导图会跳过。")


def render_api_page() -> None:
    st.markdown("# API 设置")
    st.caption("API Key 只保存到本机加密数据库，不写入 .env 或 config.toml，也不会在页面展示任何片段。")

    config = config_loader.load_config()
    project_root = config_loader.get_project_root()
    config_path = os.path.join(project_root, "config.toml")

    if _env_contains_legacy_key(project_root):
        st.warning("检测到旧 .env 中存在 API Key。新版不会读取它；建议你删除旧 Key 或在平台轮换。")

    st.markdown("## DeepSeek API Key")
    _render_secret_status()

    api_key = st.text_input(
        "输入或更新 API Key",
        value="",
        type="password",
        placeholder="sk-...",
        help="留空不会改变本地数据库中的 API Key。",
        key="api_key_input",
    )
    passphrase = st.text_input(
        "Docker/Linux 加密口令",
        value="",
        type="password",
        placeholder="Windows 本机可留空；Docker/Linux 保存时需要",
        key="api_passphrase",
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("保存 API Key 到本机数据库", type="primary", use_container_width=True):
            if not api_key:
                st.error("API Key 为空，未保存。")
            else:
                try:
                    save_secret(
                        SECRET_DEEPSEEK_API_KEY,
                        api_key,
                        passphrase=passphrase or None,
                    )
                    st.session_state["deepseek_api_key"] = api_key
                    if passphrase:
                        st.session_state["secret_passphrase"] = passphrase
                    st.success("API Key 已加密保存到本机数据库。")
                except SecretStoreError as exc:
                    st.error(str(exc))
    with c2:
        if st.button("删除本机 API Key", use_container_width=True):
            delete_secret(SECRET_DEEPSEEK_API_KEY)
            st.session_state.pop("deepseek_api_key", None)
            st.success("本机 API Key 已删除。")

    st.markdown("## 基础设置")
    deepseek = config.get("deepseek", {})
    whisper = config.get("whisper", {})
    screenshot = config.get("screenshot", {})

    col1, col2 = st.columns(2)
    with col1:
        base_url = st.text_input(
            "API Base URL",
            value=deepseek.get("base_url", "https://api.deepseek.com"),
            key="api_base_url",
        )
        model = st.text_input(
            "DeepSeek 模型名称",
            value=deepseek.get("model", "deepseek-chat"),
            key="api_model",
        )
    with col2:
        max_chunk = st.number_input(
            "最大分块（分钟）",
            min_value=1,
            max_value=60,
            value=int(deepseek.get("max_chunk_minutes", 12)),
            key="api_max_chunk",
        )
        max_retries = st.number_input(
            "最大重试次数",
            min_value=0,
            max_value=10,
            value=int(deepseek.get("max_retries", 3)),
            key="api_max_retries",
        )

    st.markdown("## Whisper 默认设置")
    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        whisper_model = st.text_input(
            "模型名称或本地路径",
            value=whisper.get("model", "medium"),
            key="api_whisper_model",
        )
    with col_w2:
        whisper_lang = st.selectbox(
            "默认语言",
            ["Chinese", "English", "Japanese", "Korean", "auto"],
            index=["Chinese", "English", "Japanese", "Korean", "auto"].index(
                whisper.get("language", "Chinese")
            )
            if whisper.get("language", "Chinese") in ["Chinese", "English", "Japanese", "Korean", "auto"]
            else 0,
            key="api_whisper_lang",
        )
    with col_w3:
        whisper_device = st.selectbox(
            "计算设备",
            ["cuda", "cpu"],
            index=0 if whisper.get("device", "cuda") == "cuda" else 1,
            key="api_whisper_device",
        )

    st.markdown("## 截图设置")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        screenshot_enabled = st.checkbox(
            "默认启用截图",
            value=bool(screenshot.get("enabled", False)),
            key="screenshot_enabled",
        )
    with col_s2:
        min_interval = st.number_input(
            "最小截图间隔（秒）",
            min_value=1,
            max_value=60,
            value=int(screenshot.get("min_interval_seconds", 3)),
            key="screenshot_min_interval",
        )
    with col_s3:
        diff_threshold = st.slider(
            "相似度去重阈值",
            min_value=0.5,
            max_value=0.99,
            value=float(screenshot.get("difference_threshold", 0.85)),
            step=0.01,
            key="screenshot_diff_threshold",
        )

    if st.button("保存普通设置", type="primary", use_container_width=True):
        updated = dict(config)
        updated["deepseek"] = {
            "model": model,
            "base_url": base_url,
            "max_chunk_minutes": max_chunk,
            "max_retries": max_retries,
            "retry_delay_seconds": deepseek.get("retry_delay_seconds", 5),
        }
        updated["whisper"] = {
            **whisper,
            "model": whisper_model,
            "language": whisper_lang,
            "device": whisper_device,
        }
        updated["screenshot"] = {
            **screenshot,
            "enabled": screenshot_enabled,
            "min_interval_seconds": min_interval,
            "difference_threshold": diff_threshold,
        }
        if save_config_toml(config_path, updated):
            st.success("普通设置已保存到 config.toml。API Key 未写入配置文件。")

    display_config = config_loader.load_config()
    display_config.get("deepseek", {}).pop("api_key", None)
    st.markdown("## 当前普通配置")
    st.json(display_config)


render_api_page()
