import base64
from pathlib import Path

import streamlit as st

from app import PipelineRunner
from app.health_checks import run_health_checks
from app.runtime_config import inject_runtime_secrets
from src import config_loader, link_parser
from src.utils import load_json


BRAND_NAME = "烟雨春明"
PROJECT_ROOT = Path(config_loader.get_project_root())
TCX_IMAGE = PROJECT_ROOT / "docs" / "learning_screenshot_strategy" / "TCX.jpg"


def _asset_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _read_text_preview(path: Path) -> tuple[str, str]:
    if not path.exists():
        return "", f"文件不存在：{path}"
    try:
        return path.read_text(encoding="utf-8"), ""
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="gbk"), ""
        except Exception as exc:
            return "", f"读取失败：{exc}"
    except Exception as exc:
        return "", f"读取失败：{exc}"


def _parse_pasted_urls(text: str) -> list[str]:
    runner = PipelineRunner()
    try:
        return runner.parse_url_text(text)
    finally:
        runner.cleanup()


def _parse_links_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    return link_parser.parse_links_file(str(path))


def _recent_stats(config: dict) -> dict:
    output_dir = Path(config_loader.resolve_path(config, "output_dir"))
    processed = load_json(str(PROJECT_ROOT / "processed.json"), [])
    failed = load_json(str(PROJECT_ROOT / "failed.json"), [])
    output_count = len([p for p in output_dir.iterdir() if p.is_dir()]) if output_dir.is_dir() else 0
    return {"processed": processed, "failed": failed, "output_count": output_count}


def inject_global_styles() -> None:
    image_uri = _asset_data_uri(TCX_IMAGE)
    theme = st.session_state.get("ym_theme", "day")
    is_night = theme == "night"
    text = "#f0ffee" if is_night else "#142d20"
    muted = "rgba(235,255,231,.76)" if is_night else "#526f5d"
    panel = "rgba(8,31,25,.80)" if is_night else "rgba(255,255,248,.82)"
    panel_strong = "rgba(13,48,38,.90)" if is_night else "rgba(255,255,250,.94)"
    bg = (
        f"radial-gradient(circle at 12% 8%, rgba(242,207,100,.16), transparent 30%), "
        f"linear-gradient(145deg, rgba(5,24,19,.98), rgba(9,46,36,.96)), url('{image_uri}')"
        if is_night
        else f"radial-gradient(circle at 10% 8%, rgba(255,226,148,.42), transparent 30%), "
        f"linear-gradient(145deg, rgba(253,255,246,.96), rgba(226,249,217,.88)), url('{image_uri}')"
    )
    st.markdown(
        f"""
<style>
:root {{
  --ym-text:{text};
  --ym-muted:{muted};
  --ym-panel:{panel};
  --ym-panel-strong:{panel_strong};
  --ym-line:rgba(121,215,99,.28);
  --ym-green:#79d763;
  --ym-gold:#f2cf64;
  --ym-coral:#ff7353;
}}
.stApp {{
  color:var(--ym-text);
  background:{bg};
  background-size:auto, auto, min(48vw, 620px);
  background-position:center, center, right 2rem top 6rem;
  background-repeat:no-repeat;
  background-attachment:fixed;
}}
.block-container {{ max-width:1180px; padding-top:1.3rem; padding-bottom:4rem; }}
[data-testid="stSidebar"] {{
  background:{"linear-gradient(180deg,#071c17,#0c3529)" if is_night else "linear-gradient(180deg,#fbfff2,#e8f9dc)"};
  border-right:1px solid var(--ym-line);
}}
[data-testid="stSidebar"] * {{ color:var(--ym-text) !important; }}
[data-testid="stSidebar"] a {{
  margin:.25rem .45rem;
  border-radius:16px;
  border:1px solid transparent;
}}
[data-testid="stSidebar"] a:hover, [data-testid="stSidebar"] a[aria-current="page"] {{
  background:linear-gradient(135deg,rgba(121,215,99,.22),rgba(242,207,100,.16));
  border-color:rgba(121,215,99,.48);
}}
.ym-topbar {{ display:flex; justify-content:space-between; align-items:center; gap:1rem; margin-bottom:1rem; }}
.ym-brand {{
  display:inline-flex; align-items:center; gap:.75rem; padding:.62rem .9rem; border-radius:999px;
  border:1px solid var(--ym-line); background:var(--ym-panel); backdrop-filter:blur(18px);
  box-shadow:0 22px 70px rgba(20,77,39,.18);
}}
.ym-mark {{
  width:42px; height:42px; border-radius:16px; display:grid; place-items:center; color:#17351d; font-weight:900;
  background:conic-gradient(from 40deg,#d7ff7e,#74dc6d,#f5cf63,#d7ff7e);
  box-shadow:inset 0 0 0 2px rgba(255,255,255,.78),0 12px 28px rgba(80,147,52,.28);
}}
.ym-brand small {{ color:var(--ym-muted); display:block; }}
.ym-theme-link {{
  display:block; width:112px; height:58px; border-radius:999px; position:relative; text-decoration:none !important;
}}
.ym-theme-anchor {{
  display:block;
  width:112px; height:58px; border-radius:999px; position:relative; pointer-events:none;
  background:linear-gradient(145deg, {"#061712,#174734" if is_night else "#f8e57e,#7fd86b"});
  box-shadow:inset 0 5px 12px rgba(255,255,255,.28), inset 0 -10px 18px rgba(0,0,0,.20), 0 18px 42px rgba(36,99,45,.24);
}}
.ym-theme-anchor::after {{
  content:""; position:absolute; top:8px; left:{"58px" if is_night else "8px"}; width:42px; height:42px; border-radius:50%;
  background:{"linear-gradient(145deg,#e9f5ff,#9fb8c8)" if is_night else "linear-gradient(145deg,#fff7c8,#ffb84f)"};
  box-shadow:0 6px 14px rgba(0,0,0,.26), inset 0 2px 5px rgba(255,255,255,.75);
}}
.ym-hero,.ym-panel,.ym-card {{
  border:1px solid var(--ym-line); background:var(--ym-panel); box-shadow:0 28px 80px rgba(20,77,39,.18); backdrop-filter:blur(18px);
}}
.ym-hero {{ position:relative; min-height:285px; padding:clamp(1.4rem,4vw,2.7rem); border-radius:28px; overflow:hidden; }}
.ym-hero::after {{
  content:""; position:absolute; inset:0; background:url("{image_uri}") right -1rem center / min(43vw,540px) no-repeat;
  opacity:{"0.16" if is_night else "0.28"}; pointer-events:none;
}}
.ym-hero-content {{ position:relative; z-index:1; max-width:640px; }}
.ym-hero h1 {{ margin:0 0 .8rem; color:var(--ym-text); font-size:clamp(2.2rem,5vw,4.4rem); }}
.ym-hero p,.ym-section-title p,.ym-muted {{ color:var(--ym-muted); }}
.ym-chips {{ display:flex; flex-wrap:wrap; gap:.65rem; margin-top:1rem; }}
.ym-chip,.ym-badge {{
  display:inline-flex; align-items:center; gap:.45rem; padding:.46rem .78rem; border-radius:999px;
  border:1px solid rgba(121,215,99,.34); background:var(--ym-panel-strong); color:var(--ym-text); font-weight:800;
}}
.ym-chip::before {{ content:""; width:9px; height:9px; border-radius:50%; background:var(--ym-green); box-shadow:0 0 0 5px rgba(121,215,99,.13); }}
.ym-stats {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.85rem; margin:1rem 0; }}
.ym-card {{ border-radius:20px; padding:1rem; }}
.ym-card b {{ display:block; color:var(--ym-green); font-size:1.75rem; }}
.ym-panel {{ border-radius:24px; padding:1.25rem; margin-top:1rem; }}
.ym-list {{ display:grid; gap:.75rem; }}
.ym-list-item {{
  display:grid; grid-template-columns:auto 1fr auto; gap:.8rem; align-items:center; padding:.86rem .95rem; border-radius:18px;
  background:var(--ym-panel-strong); border:1px solid rgba(121,215,99,.22);
}}
.ym-dot {{ width:12px; height:12px; border-radius:50%; background:var(--ym-coral); box-shadow:0 0 0 7px rgba(255,115,83,.14); }}
.ym-dot.ok {{ background:var(--ym-green); box-shadow:0 0 0 7px rgba(121,215,99,.14); }}
.ym-file-preview {{ margin-top:.75rem; padding:.9rem; border-radius:18px; background:var(--ym-panel-strong); border:1px solid rgba(121,215,99,.26); }}
.stButton > button,.stDownloadButton > button {{
  min-height:2.95rem; border:0 !important; border-radius:18px !important; color:#132719 !important;
  background:linear-gradient(145deg,#fff6ba 0%,#9bec79 47%,#4fbd6a 100%) !important;
  box-shadow:inset 0 2px 0 rgba(255,255,255,.65), inset 0 -5px 0 rgba(18,78,42,.24), 0 16px 34px rgba(44,130,58,.24) !important;
  font-weight:900 !important;
}}
textarea,input {{
  border-radius:18px !important; color:var(--ym-text) !important; border:1px solid rgba(121,215,99,.34) !important;
  background:var(--ym-panel-strong) !important;
}}
.stRadio [role="radiogroup"] {{
  display:inline-flex; gap:.35rem; padding:.35rem; border-radius:999px; border:1px solid rgba(121,215,99,.34);
  background:var(--ym-panel-strong);
}}
.stRadio label {{ min-height:2.35rem; padding:.35rem .65rem; border-radius:999px; color:var(--ym-text) !important; }}
.stRadio label:has(input:checked) {{ background:linear-gradient(145deg,rgba(255,246,186,.9),rgba(121,215,99,.42)); color:#132719 !important; }}
@media(max-width:760px) {{
  .ym-stats {{ grid-template-columns:1fr; }}
  .ym-list-item {{ grid-template-columns:auto 1fr; }}
  .ym-list-item .ym-badge {{ grid-column:2; width:fit-content; }}
}}
</style>
""",
        unsafe_allow_html=True,
    )


def render_theme_controller() -> None:
    if "ym_theme" not in st.session_state:
        st.session_state["ym_theme"] = "day"
    query_theme = st.query_params.get("theme", "")
    if query_theme in ("day", "night"):
        st.session_state["ym_theme"] = query_theme
    mode = st.session_state["ym_theme"]
    next_mode = "night" if mode == "day" else "day"
    st.markdown(
        f'<a class="ym-theme-link" href="?theme={next_mode}" aria-label="切换昼夜模式">'
        f'<span class="ym-theme-anchor {mode}"></span></a>',
        unsafe_allow_html=True,
    )


def render_topbar() -> None:
    left, right = st.columns([1, 0.18], vertical_alignment="center")
    with left:
        st.markdown(
            f"""
<div class="ym-topbar">
  <div class="ym-brand">
    <div class="ym-mark">明</div>
    <div><strong>{BRAND_NAME}</strong><small>B站视频笔记工作流</small></div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
    with right:
        render_theme_controller()


def render_hero(config: dict, mode: str) -> None:
    whisper = config.get("whisper", {})
    mode_text = "带图模式" if mode == "with_images" else "基础模式"
    st.markdown(
        f"""
<section class="ym-hero">
  <div class="ym-hero-content">
    <h1>B站视频笔记工作流</h1>
    <p>把 B站视频链接整理成结构化学习笔记。基础模式适合快速转写；带图模式会下载视频并生成截图与图文笔记。</p>
    <div class="ym-chips">
      <span class="ym-chip">{mode_text}</span>
      <span class="ym-chip">Whisper：{whisper.get("model", "medium")} / {whisper.get("language", "Chinese")}</span>
    </div>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )


def render_stats(config: dict, mode: str) -> None:
    stats = _recent_stats(config)
    st.markdown(
        f"""
<div class="ym-stats">
  <div class="ym-card"><b>{len(stats["processed"])}</b><span>历史成功</span></div>
  <div class="ym-card"><b>{len(stats["failed"])}</b><span>历史失败</span></div>
  <div class="ym-card"><b>{stats["output_count"]}</b><span>输出目录</span></div>
  <div class="ym-card"><b>{mode}</b><span>当前流程</span></div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_health_panel(config: dict) -> None:
    checks = run_health_checks(inject_runtime_secrets(config))
    items = []
    for check in checks:
        dot = "ym-dot ok" if check.ok else "ym-dot"
        check_note = "命令检测" if check.check_type == "command" else "配置检测"
        items.append(
            f"""
<div class="ym-list-item">
  <span class="{dot}"></span>
  <span><strong>{check.name}</strong><br><span class="ym-muted">{check_note}：{check.detail}</span></span>
  <span class="ym-badge">{check.status}</span>
</div>
"""
        )
    st.markdown(
        f"""
<div class="ym-panel">
  <div class="ym-section-title"><h2>系统状态</h2><p>DeepSeek 只显示本地密钥配置状态，不代表联网验证成功。</p></div>
  <div class="ym-list">{''.join(items)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_txt_preview(path: Path, urls: list[str]) -> None:
    content, error = _read_text_preview(path)
    if error:
        st.error(error)
        return
    st.markdown('<div class="ym-file-preview">', unsafe_allow_html=True)
    st.caption(f"文件路径：{path}")
    st.code(content or "文件为空", language="text")
    st.markdown("</div>", unsafe_allow_html=True)
    if urls:
        st.success(f"识别到 {len(urls)} 个视频链接")
        with st.expander("查看解析出的链接"):
            for url in urls:
                st.write(url)
    else:
        st.warning("没有识别到有效的 B站视频链接。")


def render_workbench(config: dict, mode: str) -> None:
    mode_label = "带图模式" if mode == "with_images" else "基础模式"
    links_file = PROJECT_ROOT / ("links_with_images.txt" if mode == "with_images" else "links.txt")

    st.markdown(
        f"""
<div class="ym-panel">
  <div class="ym-section-title"><h2>开始处理</h2><p>当前：{mode_label}。文件加载将读取 {links_file.name}。</p></div>
</div>
""",
        unsafe_allow_html=True,
    )

    mode_choice = st.radio(
        "处理模式",
        ["基础模式", "带图模式"],
        index=1 if mode == "with_images" else 0,
        horizontal=True,
        key="ym_mode_choice",
    )
    selected_mode = "with_images" if mode_choice == "带图模式" else "basic"
    if selected_mode != mode:
        st.session_state["ym_mode"] = selected_mode
        st.rerun()

    input_method = st.radio(
        "链接输入方式",
        ["粘贴链接", f"从 {links_file.name} 加载"],
        horizontal=True,
        key=f"ym_input_method_{mode}",
    )

    urls: list[str] = []
    if input_method == "粘贴链接":
        text = st.text_area(
            "B站视频链接",
            height=156,
            placeholder="https://www.bilibili.com/video/BV1xx411c7mD\n每行一个链接，支持批量处理",
            key=f"ym_url_text_{mode}",
        )
        if text.strip():
            urls = _parse_pasted_urls(text)
            if urls:
                st.success(f"已识别 {len(urls)} 个视频链接")
            else:
                st.warning("没有识别到有效的 B站视频链接。")
    else:
        urls = _parse_links_file(links_file)
        render_txt_preview(links_file, urls)

    if not inject_runtime_secrets(config).get("deepseek", {}).get("api_key", ""):
        st.warning("未配置 DeepSeek API Key，AI 标点、摘要和思维导图会跳过。")

    if st.button("开始处理", type="primary", disabled=not urls, use_container_width=True):
        runner = PipelineRunner()
        progress = st.progress(0, text="准备开始")
        result_box = st.container()
        try:
            for idx, url in enumerate(urls, start=1):
                progress.progress((idx - 1) / len(urls), text=f"正在处理 {idx}/{len(urls)}")
                with st.spinner(f"正在处理第 {idx}/{len(urls)} 个视频：{mode_label}"):
                    result = runner.run_single(url, config, mode=mode)
                with result_box:
                    if result["success"]:
                        st.success(f"处理完成：{result.get('title') or url}")
                        if result.get("output_dir"):
                            st.code(result["output_dir"], language="text")
                    else:
                        st.error(f"处理失败：{url}")
                    if result.get("logs"):
                        with st.expander("处理日志"):
                            st.text("\n".join(result["logs"]))
                progress.progress(idx / len(urls), text=f"已完成 {idx}/{len(urls)}")
            st.success("全部任务处理完成。")
        finally:
            runner.cleanup()


def render_history_panel(config: dict) -> None:
    processed = _recent_stats(config)["processed"][-5:][::-1]
    if not processed:
        st.markdown('<div class="ym-panel"><h2>处理历史</h2><p class="ym-muted">暂无历史记录。</p></div>', unsafe_allow_html=True)
        return
    items = []
    for item in processed:
        title = item.get("title", "未命名视频")
        mode = item.get("mode", "unknown")
        when = item.get("processed_at", "")[:16]
        items.append(
            f'<div class="ym-list-item"><span class="ym-dot ok"></span><span><strong>{title}</strong><br><span class="ym-muted">{when}</span></span><span class="ym-badge">{mode}</span></div>'
        )
    st.markdown(f'<div class="ym-panel"><h2>处理历史</h2><div class="ym-list">{"".join(items)}</div></div>', unsafe_allow_html=True)


def render_dashboard() -> None:
    config = config_loader.load_config()
    if "ym_mode" not in st.session_state:
        st.session_state["ym_mode"] = "basic"
    mode = st.session_state["ym_mode"]

    inject_global_styles()
    render_topbar()
    render_hero(config, mode)
    render_stats(config, mode)
    render_workbench(config, mode)

    left, right = st.columns([1, 1])
    with left:
        render_health_panel(config)
    with right:
        render_history_panel(config)
