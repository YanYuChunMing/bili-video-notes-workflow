import os
import sys
import streamlit as st
import base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import FileManager
from src import config_loader

fm = FileManager()


def render_output_page():
    st.markdown("## 📂 输出成果")
    st.markdown("浏览、查看和打开已处理的视频笔记结果")
    st.markdown("---")

    config = config_loader.load_config()
    output_dir = config_loader.resolve_path(config, "output_dir")

    st.markdown("### 📁 输出目录列表")

    dirs = fm.get_output_dirs(output_dir)

    if not dirs:
        st.info("暂无输出结果。请先使用 **基础功能** 或 **带图功能** 处理视频。")
        return

    st.markdown(f"共 **{len(dirs)}** 个输出目录")

    selected_dir = None
    col_dir_list, col_dir_preview = st.columns([1, 2])

    with col_dir_list:
        for d in dirs:
            mode_icon = "🖼️" if d["has_screenshots"] else "📝"
            file_count = len(d["files"])
            btn_label = f"{mode_icon} {d['name'][:50]}"
            if st.button(
                btn_label,
                key=f"dir_{d['name']}",
                use_container_width=True,
                help=f"修改时间: {d['modified']}\n文件数: {file_count}",
            ):
                st.session_state["selected_output_dir"] = d["path"]
                st.rerun()

    with col_dir_preview:
        selected_path = st.session_state.get("selected_output_dir", "")

        if selected_path and os.path.isdir(selected_path):
            dir_name = os.path.basename(selected_path)
            st.markdown(f"### 📋 {dir_name}")

            files_info = fm.get_output_files(selected_path)

            st.markdown("### 🎬 输出模式选择")

            output_mode = st.radio(
                "选择输出查看方式",
                [
                    "📂 模式一：打开文件所在文件夹",
                    "📄 模式二：应用内查看文件内容",
                ],
                horizontal=True,
                key="output_mode",
            )

            st.markdown("---")

            if output_mode.startswith("📂"):
                st.markdown("#### 📂 打开文件夹")
                st.info("点击下方按钮，将在系统文件管理器中打开对应文件夹")

                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    if st.button(
                        "📁 打开输出目录", use_container_width=True, type="primary",
                        key="open_output_dir",
                    ):
                        success = fm.open_folder(selected_path)
                        if success:
                            st.success(f"已打开文件夹: {selected_path}")
                        else:
                            st.error("无法打开文件夹")

                with col_f2:
                    results_path = os.path.join(selected_path, "results")
                    if os.path.isdir(results_path):
                        if st.button(
                            "📁 打开 results 子目录", use_container_width=True,
                            key="open_results_dir",
                        ):
                            success = fm.open_folder(results_path)
                            if success:
                                st.success(f"已打开文件夹: {results_path}")
                            else:
                                st.error("无法打开文件夹")

                st.markdown("##### 📂 所有子目录快捷打开")
                subdirs = [
                    d for d in os.listdir(selected_path)
                    if os.path.isdir(os.path.join(selected_path, d))
                ]
                if subdirs:
                    cols = st.columns(min(len(subdirs), 4))
                    for i, sd in enumerate(subdirs):
                        sd_path = os.path.join(selected_path, sd)
                        with cols[i % len(cols)]:
                            if st.button(f"📁 {sd[:30]}", key=f"subdir_{sd}", use_container_width=True):
                                fm.open_folder(sd_path)

            else:
                st.markdown("#### 📄 文件内容查看")

                tabs = st.tabs(["📝 TXT 文件", "📋 MD 文件", "🌐 HTML 文件", "📊 JSON 文件"])

                with tabs[0]:
                    txt_files = files_info.get("txt", [])
                    if txt_files:
                        selected_txt = st.selectbox(
                            "选择 TXT 文件", txt_files, key="txt_select"
                        )
                        if selected_txt:
                            txt_path = os.path.join(
                                selected_path, "results", selected_txt
                            )
                            if not os.path.exists(txt_path):
                                txt_path = os.path.join(
                                    selected_path,
                                    selected_txt.replace("../", ""),
                                )
                            content = fm.read_file(txt_path)
                            st.text_area(
                                "文件内容",
                                content,
                                height=400,
                                key="txt_content",
                            )

                            col_t1, col_t2, col_t3 = st.columns(3)
                            with col_t1:
                                if st.button(
                                    "📂 打开文件位置",
                                    key="txt_open_folder",
                                    use_container_width=True,
                                ):
                                    fm.open_folder(os.path.dirname(txt_path))
                            with col_t2:
                                if st.button(
                                    "📝 用默认应用打开",
                                    key="txt_open_app",
                                    use_container_width=True,
                                ):
                                    fm.open_with_default_app(txt_path)
                            with col_t3:
                                st.download_button(
                                    "⬇️ 下载文件",
                                    content,
                                    file_name=selected_txt,
                                    key="txt_download",
                                    use_container_width=True,
                                )
                    else:
                        st.info("暂无 TXT 文件")

                with tabs[1]:
                    md_files = files_info.get("md", [])
                    if md_files:
                        selected_md = st.selectbox(
                            "选择 MD 文件", md_files, key="md_select"
                        )
                        if selected_md:
                            md_path = os.path.join(
                                selected_path, "results", selected_md
                            )
                            if not os.path.exists(md_path):
                                md_path = os.path.join(
                                    selected_path,
                                    selected_md.replace("../", ""),
                                )
                            content = fm.read_file(md_path)
                            st.markdown(content)

                            col_m1, col_m2, col_m3 = st.columns(3)
                            with col_m1:
                                if st.button(
                                    "📂 打开文件位置",
                                    key="md_open_folder",
                                    use_container_width=True,
                                ):
                                    fm.open_folder(os.path.dirname(md_path))
                            with col_m2:
                                if st.button(
                                    "📝 用默认应用打开",
                                    key="md_open_app",
                                    use_container_width=True,
                                ):
                                    fm.open_with_default_app(md_path)
                            with col_m3:
                                st.download_button(
                                    "⬇️ 下载文件",
                                    content,
                                    file_name=selected_md,
                                    key="md_download",
                                    use_container_width=True,
                                )
                    else:
                        st.info("暂无 MD 文件")

                with tabs[2]:
                    html_files = files_info.get("html", [])
                    if html_files:
                        selected_html = st.selectbox(
                            "选择 HTML 文件", html_files, key="html_select"
                        )
                        if selected_html:
                            html_path = os.path.join(
                                selected_path, "results", selected_html
                            )
                            if not os.path.exists(html_path):
                                html_path = os.path.join(
                                    selected_path,
                                    selected_html.replace("../", ""),
                                )
                            content = fm.read_file(html_path)

                            st.markdown("##### 🌐 HTML 预览")
                            st.components.v1.html(content, height=500, scrolling=True)

                            col_h1, col_h2, col_h3 = st.columns(3)
                            with col_h1:
                                if st.button(
                                    "🌐 在浏览器中打开",
                                    key="html_open_browser",
                                    use_container_width=True,
                                ):
                                    success = fm.open_in_browser(html_path)
                                    if success:
                                        st.success("已在浏览器中打开")
                                    else:
                                        st.error("无法打开浏览器")
                            with col_h2:
                                if st.button(
                                    "📂 打开文件位置",
                                    key="html_open_folder",
                                    use_container_width=True,
                                ):
                                    fm.open_folder(os.path.dirname(html_path))
                            with col_h3:
                                st.download_button(
                                    "⬇️ 下载文件",
                                    content,
                                    file_name=selected_html,
                                    key="html_download",
                                    use_container_width=True,
                                )
                    else:
                        st.info("暂无 HTML 文件")

                with tabs[3]:
                    json_files = files_info.get("json", [])
                    if json_files:
                        selected_json = st.selectbox(
                            "选择 JSON 文件", json_files, key="json_select"
                        )
                        if selected_json:
                            json_path = os.path.join(
                                selected_path, "results", selected_json
                            )
                            if not os.path.exists(json_path):
                                json_path = os.path.join(
                                    selected_path,
                                    selected_json.replace("../", ""),
                                )
                            content = fm.read_file(json_path)
                            try:
                                import json
                                parsed = json.loads(content)
                                st.json(parsed)
                            except Exception:
                                st.code(content, language="json")

                            col_j1, col_j2 = st.columns(2)
                            with col_j1:
                                if st.button(
                                    "📂 打开文件位置",
                                    key="json_open_folder",
                                    use_container_width=True,
                                ):
                                    fm.open_folder(os.path.dirname(json_path))
                            with col_j2:
                                st.download_button(
                                    "⬇️ 下载文件",
                                    content,
                                    file_name=selected_json,
                                    key="json_download",
                                    use_container_width=True,
                                )
                    else:
                        st.info("暂无 JSON 文件")

            st.markdown("---")
            st.markdown("### 🖼️ 截图浏览")

            screenshots = fm.find_screenshot_files(selected_path)
            if screenshots:
                st.markdown(f"共 **{len(screenshots)}** 张截图")
                cols_per_row = 3
                for i in range(0, len(screenshots), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        idx = i + j
                        if idx < len(screenshots):
                            ss = screenshots[idx]
                            with cols[j]:
                                try:
                                    st.image(
                                        ss["path"],
                                        caption=f"{ss['segment']}/{ss['filename']}",
                                        use_container_width=True,
                                    )
                                except Exception:
                                    st.warning(f"无法加载: {ss['filename']}")
            else:
                st.info("该输出目录暂无截图")

        elif not selected_path and dirs:
            st.info("👈 请从左侧列表选择一个输出目录查看详情")

    st.markdown("---")

    st.markdown("### 🔮 预留扩展功能")
    st.markdown("以下功能将在后续版本中实现：")

    ext_col1, ext_col2, ext_col3 = st.columns(3)
    with ext_col1:
        st.markdown("##### 📝 TXT → DOCX")
        st.caption("将TXT文字稿转换为精美排版DOCX文档")
        st.button(
            "🔜 即将推出",
            disabled=True,
            key="ext_docx",
            use_container_width=True,
        )
    with ext_col2:
        st.markdown("##### 📋 MD 关联应用")
        st.caption("直接跳转至系统默认Markdown编辑器打开MD文件")
        st.button(
            "🔜 即将推出",
            disabled=True,
            key="ext_md",
            use_container_width=True,
        )
    with ext_col3:
        st.markdown("##### 🌐 HTML 浏览器")
        st.caption("直接在系统默认浏览器中打开HTML思维导图")
        st.button(
            "🔜 即将推出",
            disabled=True,
            key="ext_html",
            use_container_width=True,
        )


if __name__ == "__main__":
    render_output_page()
else:
    render_output_page()
