import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import config_loader

try:
    import tomllib as tomli_reader
except ImportError:
    try:
        import tomli as tomli_reader
    except ImportError:
        import toml as tomli_reader

try:
    import tomli_w
    HAS_TOML_WRITER = True
except ImportError:
    HAS_TOML_WRITER = False


def save_config_toml(config_path: str, config: dict):
    if not HAS_TOML_WRITER:
        st.error("缺少 tomli_w 库，无法保存配置。请运行: pip install tomli-w")
        return False

    sections_to_save = {
        "project": config.get("project", {}),
        "whisper": config.get("whisper", {}),
        "deepseek": config.get("deepseek", {}),
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
    except Exception as e:
        st.error(f"保存配置文件失败: {e}")
        return False


def save_env_file(env_path: str, api_key: str, base_url: str):
    content = f"""DEEPSEEK_API_KEY={api_key}
DEEPSEEK_BASE_URL={base_url}
"""
    try:
        os.makedirs(os.path.dirname(env_path) or ".", exist_ok=True)
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        st.error(f"保存 .env 文件失败: {e}")
        return False


def render_api_page():
    st.markdown("## ⚙️ API 设置")
    st.markdown("配置 DeepSeek API 参数，用于AI标点补全、摘要生成和思维导图")
    st.markdown("---")

    config = config_loader.load_config()
    deepseek = config.get("deepseek", {})
    project_root = config_loader.get_project_root()
    config_path = os.path.join(project_root, "config.toml")
    env_path = os.path.join(project_root, ".env")

    st.markdown("### 🔑 DeepSeek API Key")

    current_key = deepseek.get("api_key", "")
    if current_key:
        masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "***"
        st.success(f"当前 API Key: {masked}")

    api_key = st.text_input(
        "API Key",
        value="",
        type="password",
        placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        help="从 https://platform.deepseek.com/api_keys 获取",
        key="api_key_input",
    )

    st.markdown("### 🌐 基础设置")

    col1, col2 = st.columns(2)
    with col1:
        base_url = st.text_input(
            "API Base URL",
            value=deepseek.get("base_url", "https://api.deepseek.com"),
            help="API服务地址",
            key="api_base_url",
        )
        model = st.text_input(
            "模型名称",
            value=deepseek.get("model", "deepseek-chat"),
            help="DeepSeek 模型名称",
            key="api_model",
        )
    with col2:
        max_chunk = st.number_input(
            "最大分块(分钟)",
            min_value=1,
            max_value=60,
            value=deepseek.get("max_chunk_minutes", 12),
            help="长文本每块对应的音频分钟数",
            key="api_max_chunk",
        )
        max_retries = st.number_input(
            "最大重试次数",
            min_value=0,
            max_value=10,
            value=deepseek.get("max_retries", 3),
            key="api_max_retries",
        )

    st.markdown("### 🎤 Whisper 默认设置")

    whisper = config.get("whisper", {})
    col_w1, col_w2, col_w3 = st.columns(3)
    with col_w1:
        whisper_model = st.selectbox(
            "默认模型",
            ["tiny", "base", "small", "medium", "large-v2", "large-v3"],
            index=["tiny", "base", "small", "medium", "large-v2", "large-v3"].index(
                whisper.get("model", "medium")
            ),
            key="api_whisper_model",
        )
    with col_w2:
        whisper_lang = st.selectbox(
            "默认语言",
            ["Chinese", "English", "Japanese", "Korean", "auto"],
            index=["Chinese", "English", "Japanese", "Korean", "auto"].index(
                whisper.get("language", "Chinese")
            ),
            key="api_whisper_lang",
        )
    with col_w3:
        whisper_device = st.selectbox(
            "计算设备",
            ["cuda", "cpu"],
            index=0 if whisper.get("device", "cuda") == "cuda" else 1,
            key="api_whisper_device",
        )

    st.markdown("---")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            updated = config.copy()
            updated["deepseek"]["model"] = model
            updated["deepseek"]["base_url"] = base_url
            updated["deepseek"]["max_chunk_minutes"] = max_chunk
            updated["deepseek"]["max_retries"] = max_retries
            updated["whisper"]["model"] = whisper_model
            updated["whisper"]["language"] = whisper_lang
            updated["whisper"]["device"] = whisper_device

            if api_key:
                updated["deepseek"]["api_key"] = api_key

            toml_saved = save_config_toml(config_path, updated)

            env_key = api_key if api_key else current_key
            env_saved = save_env_file(env_path, env_key, base_url)

            if toml_saved and env_saved:
                st.success("✅ 配置已保存！")
                st.info("配置将在下次页面刷新后生效")
            elif toml_saved:
                st.success("✅ config.toml 已保存")
            elif env_saved:
                st.success("✅ .env 已保存")

    with col_btn2:
        if st.button("🔄 重新加载配置", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")
    st.markdown("### 📋 当前完整配置")

    current_full = config_loader.load_config()
    display_config = {
        "whisper": {k: v for k, v in current_full.get("whisper", {}).items()},
        "deepseek": {
            k: v for k, v in current_full.get("deepseek", {}).items()
            if k not in ("api_key",)
        },
        "screenshot": current_full.get("screenshot", {}),
    }
    display_config["deepseek"]["api_key"] = (
        "***已配置***" if current_full.get("deepseek", {}).get("api_key") else "未配置"
    )

    st.json(display_config)

    st.markdown("### 💡 关于 DeepSeek API")
    st.info(
        "- **获取方式**: 访问 [platform.deepseek.com](https://platform.deepseek.com) 注册并获取 API Key\n"
        "- **费用说明**: DeepSeek API 按 token 计费，价格实惠\n"
        "- **模型推荐**: deepseek-chat 适合大多数场景\n"
        "- **无API时**: 应用仍可执行语音转录，但会跳过AI标点补全、摘要和思维导图\n"
        "- **配置存储**: API Key 保存在项目根目录 .env 文件中，已加入 .gitignore"
    )


if __name__ == "__main__":
    render_api_page()
else:
    render_api_page()
