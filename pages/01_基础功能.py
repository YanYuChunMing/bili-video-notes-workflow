import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import PipelineRunner
from src import config_loader


def render_basic_page():
    st.markdown("## 📝 基础功能")
    st.markdown("下载视频音频 → 语音转录 → AI标点补全 → AI摘要 → 思维导图")
    st.markdown("---")

    config = config_loader.load_config()

    st.markdown("### 🔗 视频链接输入")
    input_method = st.radio(
        "链接输入方式",
        ["粘贴链接", "从 links.txt 文件加载"],
        horizontal=True,
        key="basic_input_method",
    )

    urls = []
    if input_method == "粘贴链接":
        url_text = st.text_area(
            "请输入B站视频链接（每行一个，支持批量）",
            height=150,
            placeholder="https://www.bilibili.com/video/BV1xx411c7mD\nhttps://www.bilibili.com/video/BV1es411F7Xv",
            key="basic_url_text",
        )
        if url_text.strip():
            runner = PipelineRunner()
            urls = runner.parse_url_text(url_text)
            if urls:
                st.success(f"已识别 {len(urls)} 个视频链接")
                with st.expander("查看已识别链接"):
                    for u in urls:
                        st.markdown(f"- {u}")
            else:
                st.warning("未识别到有效的B站视频链接")
    else:
        project_root = config_loader.get_project_root()
        links_file = os.path.join(project_root, "links.txt")
        if os.path.exists(links_file):
            from src import link_parser
            urls = link_parser.parse_links_file(links_file)
            if urls:
                st.success(f"从 links.txt 加载了 {len(urls)} 个链接")
                with st.expander("查看链接列表"):
                    for u in urls:
                        st.markdown(f"- {u}")
            else:
                st.warning("links.txt 中未找到有效链接")
        else:
            st.error(f"links.txt 文件不存在: {links_file}")
            st.info("请在项目根目录创建 links.txt 文件，每行一个B站视频链接")

    st.markdown("---")

    ai_available = bool(config.get("deepseek", {}).get("api_key", ""))
    if not ai_available:
        st.warning("⚠️ 未配置 DeepSeek API Key，AI功能将跳过。仅执行语音转录。前往 **API设置** 页面配置。")

    st.markdown("### 🎛️ 处理选项")
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        whisper_model = st.selectbox(
            "Whisper 模型",
            ["tiny", "base", "small", "medium", "large-v2", "large-v3"],
            index=["tiny", "base", "small", "medium", "large-v2", "large-v3"].index(
                config.get("whisper", {}).get("model", "medium")
            ),
            key="basic_whisper_model",
        )
    with col_opt2:
        language = st.selectbox(
            "语言",
            ["Chinese", "English", "Japanese", "Korean", "auto"],
            index=["Chinese", "English", "Japanese", "Korean", "auto"].index(
                config.get("whisper", {}).get("language", "Chinese")
            ),
            key="basic_language",
        )

    st.markdown("---")

    if st.button("🚀 开始处理", type="primary", use_container_width=True, disabled=not urls):
        config["whisper"]["model"] = whisper_model
        config["whisper"]["language"] = language

        runner = PipelineRunner()
        progress_container = st.container()

        for idx, url in enumerate(urls):
            with progress_container:
                st.markdown(f"### 🔄 处理进度: {idx + 1}/{len(urls)}")
                st.markdown(f"**链接**: {url}")

            with st.spinner(f"正在处理第 {idx + 1}/{len(urls)} 个视频（基础模式）... 这可能需要几分钟"):
                result = runner.run_single(url, config, mode="basic")

            with progress_container:
                if result["success"]:
                    st.success(f"✅ 处理完成: {result['title']}")
                    st.markdown(f"输出目录: `{result['output_dir']}`")
                else:
                    st.error(f"❌ 处理失败: {url}")

                if result.get("logs"):
                    with st.expander("📋 处理日志"):
                        for log_line in result["logs"]:
                            st.text(log_line)

            if idx < len(urls) - 1:
                st.divider()

        st.success(f"🎉 全部处理完成！成功处理 {len(urls)} 个视频")
        st.info("前往 **输出成果** 页面查看生成的文件")

        runner.cleanup()

    st.markdown("---")
    st.markdown("### 💡 使用提示")
    st.info(
        "- 基础模式仅下载音频，速度快，适合快速获取文字笔记\n"
        "- 如需视频截图，请使用 **带图功能** 页面\n"
        "- 已处理过的链接会自动跳过，无需担心重复处理\n"
        "- 处理时间取决于视频长度和Whisper模型大小"
    )


if __name__ == "__main__":
    render_basic_page()
else:
    render_basic_page()
