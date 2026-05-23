import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import FileManager
from src import config_loader


fm = FileManager()


def _resolve_output_file(selected_path: str, name: str) -> str:
    if name.startswith("../"):
        return os.path.join(selected_path, name.replace("../", ""))
    return os.path.join(selected_path, "results", name)


def _render_file_tab(selected_path: str, files: list[str], label: str, language: str) -> None:
    if not files:
        st.info(f"暂无 {label} 文件。")
        return

    selected = st.selectbox(f"选择 {label} 文件", files, key=f"{label}_select")
    path = _resolve_output_file(selected_path, selected)
    content = fm.read_file(path)
    if content.startswith("[读取错误") or content.startswith("[无法读取"):
        st.error(content)
        return

    if language == "markdown":
        st.markdown(content)
    elif language == "text":
        st.text_area("文件内容", content, height=420, key=f"{label}_content")
    else:
        st.code(content, language=language)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("打开文件夹", key=f"{label}_open_folder", use_container_width=True):
            if not fm.open_folder(os.path.dirname(path)):
                st.error("无法打开文件夹。")
    with c2:
        if st.button("默认应用打开", key=f"{label}_open_app", use_container_width=True):
            if not fm.open_with_default_app(path):
                st.error("无法用默认应用打开。")
    with c3:
        st.download_button(
            "下载文件",
            content,
            file_name=os.path.basename(path),
            key=f"{label}_download",
            use_container_width=True,
        )


def render_output_page() -> None:
    st.markdown("# 输出成果")
    st.caption("点击目录卡片可在应用内查看；也可以用按钮打开系统文件夹。")

    config = config_loader.load_config()
    output_dir = config_loader.resolve_path(config, "output_dir")
    dirs = fm.get_output_dirs(output_dir)

    if not dirs:
        st.info("暂无输出结果。请先在主页处理视频。")
        return

    st.markdown(f"共 {len(dirs)} 个输出目录。")
    list_col, detail_col = st.columns([1, 2])

    with list_col:
        for d in dirs:
            label = f"{'带图' if d['has_screenshots'] else '基础'} · {d['name'][:42]}"
            if st.button(label, key=f"select_{d['path']}", use_container_width=True):
                st.session_state["selected_output_dir"] = d["path"]
                st.rerun()

    selected_path = st.session_state.get("selected_output_dir")
    if not selected_path and dirs:
        selected_path = dirs[0]["path"]
        st.session_state["selected_output_dir"] = selected_path

    with detail_col:
        if not selected_path or not os.path.isdir(selected_path):
            st.warning("请选择一个有效的输出目录。")
            return

        st.markdown(f"## {os.path.basename(selected_path)}")
        st.code(selected_path, language="text")
        if st.button("打开该输出文件夹", type="primary", use_container_width=True):
            if not fm.open_folder(selected_path):
                st.error("无法打开输出文件夹。")

        files_info = fm.get_output_files(selected_path)
        tabs = st.tabs(["TXT", "Markdown", "HTML", "JSON", "截图"])

        with tabs[0]:
            _render_file_tab(selected_path, files_info.get("txt", []), "TXT", "text")
        with tabs[1]:
            _render_file_tab(selected_path, files_info.get("md", []), "Markdown", "markdown")
        with tabs[2]:
            html_files = files_info.get("html", [])
            if not html_files:
                st.info("暂无 HTML 文件。")
            else:
                selected_html = st.selectbox("选择 HTML 文件", html_files, key="html_select")
                html_path = _resolve_output_file(selected_path, selected_html)
                content = fm.read_file(html_path)
                st.components.v1.html(content, height=520, scrolling=True)
                if st.button("在浏览器中打开 HTML", use_container_width=True):
                    if not fm.open_in_browser(html_path):
                        st.error("无法打开 HTML。")
        with tabs[3]:
            _render_file_tab(selected_path, files_info.get("json", []), "JSON", "json")
        with tabs[4]:
            screenshots = fm.find_screenshot_files(selected_path)
            if not screenshots:
                st.info("该输出目录暂无截图。")
            else:
                st.success(f"共找到 {len(screenshots)} 张截图。")
                cols_per_row = 3
                for i in range(0, len(screenshots), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for col, ss in zip(cols, screenshots[i:i + cols_per_row]):
                        with col:
                            st.image(
                                ss["path"],
                                caption=ss.get("relative", ss["filename"]),
                                use_container_width=True,
                            )


render_output_page()
