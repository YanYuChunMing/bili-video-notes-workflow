import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import PipelineRunner
from src import config_loader


def render_with_images_page():
    st.markdown("## 🖼️ 带图功能")
    st.markdown("视频下载 → 语音转录 → 智能截图 → AI处理 → 图文整合笔记")
    st.markdown("---")

    config = config_loader.load_config()

    st.markdown("### 🔗 视频链接输入")
    input_method = st.radio(
        "链接输入方式",
        ["粘贴链接", "从 links_with_images.txt 文件加载"],
        horizontal=True,
        key="img_input_method",
    )

    urls = []
    if input_method == "粘贴链接":
        url_text = st.text_area(
            "请输入B站视频链接（每行一个，建议逐个处理以节省空间）",
            height=150,
            placeholder="https://www.bilibili.com/video/BV1xx411c7mD",
            key="img_url_text",
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
        links_file = os.path.join(project_root, "links_with_images.txt")
        if os.path.exists(links_file):
            from src import link_parser
            urls = link_parser.parse_links_file(links_file)
            if urls:
                st.success(f"从 links_with_images.txt 加载了 {len(urls)} 个链接")
                with st.expander("查看链接列表"):
                    for u in urls:
                        st.markdown(f"- {u}")
            else:
                st.warning("links_with_images.txt 中未找到有效链接")
        else:
            st.error(f"links_with_images.txt 文件不存在: {links_file}")
            st.info("请在项目根目录创建 links_with_images.txt 文件，每行一个B站视频链接")

    st.markdown("---")

    ai_available = bool(config.get("deepseek", {}).get("api_key", ""))
    if not ai_available:
        st.warning("⚠️ 未配置 DeepSeek API Key，AI功能将跳过。前往 **API设置** 页面配置。")

    st.markdown("### 🎛️ 处理选项")
    col1, col2, col3 = st.columns(3)
    with col1:
        whisper_model = st.selectbox(
            "Whisper 模型",
            ["tiny", "base", "small", "medium", "large-v2", "large-v3"],
            index=["tiny", "base", "small", "medium", "large-v2", "large-v3"].index(
                config.get("whisper", {}).get("model", "medium")
            ),
            key="img_whisper_model",
        )
    with col2:
        language = st.selectbox(
            "语言",
            ["Chinese", "English", "Japanese", "Korean", "auto"],
            index=["Chinese", "English", "Japanese", "Korean", "auto"].index(
                config.get("whisper", {}).get("language", "Chinese")
            ),
            key="img_language",
        )
    with col3:
        screenshot_enabled = st.checkbox(
            "启用智能截图",
            value=config.get("screenshot", {}).get("enabled", True),
            help="基于SSIM相似度去重的智能截图",
            key="img_screenshot_enabled",
        )

    with st.expander("📷 截图高级设置"):
        col_a, col_b = st.columns(2)
        with col_a:
            min_interval = st.number_input(
                "最小截图间隔(秒)",
                min_value=1,
                max_value=30,
                value=config.get("screenshot", {}).get("min_interval_seconds", 5),
                key="img_min_interval",
            )
        with col_b:
            diff_threshold = st.slider(
                "相似度去重阈值",
                min_value=0.5,
                max_value=0.99,
                value=config.get("screenshot", {}).get("difference_threshold", 0.85),
                step=0.01,
                key="img_diff_threshold",
            )

    st.markdown("---")

    st.markdown("⚠️ **注意**：带图模式需要下载完整视频，将消耗更多磁盘空间和下载时间。")

    if st.button("🚀 开始处理（带图模式）", type="primary", use_container_width=True, disabled=not urls):
        config["whisper"]["model"] = whisper_model
        config["whisper"]["language"] = language
        config["screenshot"]["enabled"] = screenshot_enabled
        config["screenshot"]["min_interval_seconds"] = min_interval
        config["screenshot"]["difference_threshold"] = diff_threshold

        runner = PipelineRunner()
        progress_container = st.container()

        for idx, url in enumerate(urls):
            with progress_container:
                st.markdown(f"### 🔄 处理进度: {idx + 1}/{len(urls)}")
                st.markdown(f"**链接**: {url}")

            with st.spinner(
                f"正在处理第 {idx + 1}/{len(urls)} 个视频（带图模式）... "
                "下载视频和转录可能需要较长时间"
            ):
                result = runner.run_single(url, config, mode="with_images")

            with progress_container:
                if result["success"]:
                    st.success(f"✅ 处理完成: {result['title']}")
                    st.markdown(f"输出目录: `{result['output_dir']}`")
                    if screenshot_enabled:
                        st.info("智能截图已生成，请前往 **输出成果** 页面查看")
                else:
                    st.error(f"❌ 处理失败: {url}")

                if result.get("logs"):
                    with st.expander("📋 处理日志"):
                        for log_line in result["logs"]:
                            st.text(log_line)

            if idx < len(urls) - 1:
                st.divider()

        st.success(f"🎉 全部处理完成！成功处理 {len(urls)} 个视频")
        st.info("前往 **输出成果** 页面查看生成的文件和截图")

        runner.cleanup()

    st.markdown("---")
    st.markdown("### 💡 使用提示")
    st.info(
        "- 带图模式下载完整视频（最高1080p），请确保有充足磁盘空间\n"
        "- 截图基于SSIM结构相似度算法智能去重，避免重复画面\n"
        "- 每个视频将被分成多个片段分别处理截图\n"
        "- 处理时间取决于视频长度和画质"
    )


if __name__ == "__main__":
    render_with_images_page()
else:
    render_with_images_page()
