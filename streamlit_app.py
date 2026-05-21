import os
import sys
import streamlit as st

st.set_page_config(
    page_title="B站视频笔记工作流",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import config_loader

config = config_loader.load_config()


def check_dependencies():
    issues = []
    import subprocess

    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            issues.append("ffmpeg 未安装或不可用")
    except FileNotFoundError:
        issues.append("ffmpeg 未安装")
    except Exception:
        issues.append("ffmpeg 检测失败")

    try:
        result = subprocess.run(
            ["yt-dlp", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            issues.append("yt-dlp 未安装或不可用")
    except FileNotFoundError:
        issues.append("yt-dlp 未安装")
    except Exception:
        issues.append("yt-dlp 检测失败")

    return issues


COLOR_PRIMARY = "#00A1D6"
COLOR_SUCCESS = "#00C853"
COLOR_WARNING = "#FF9800"
COLOR_ERROR = "#F44336"

st.markdown(
    f"""
<style>
    .main-header {{
        background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, #0D7B9E 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 2rem;
    }}
    .main-header h1 {{ color: white; font-size: 2.2rem; }}
    .main-header p {{ color: rgba(255,255,255,0.9); font-size: 1.1rem; }}
    .stat-card {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.8rem;
        color: white;
        text-align: center;
    }}
    .stat-card.success {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
    .stat-card.warning {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }}
    .stat-card.info {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
    .stat-card .number {{ font-size: 2.5rem; font-weight: bold; }}
    .dep-ok {{ color: {COLOR_SUCCESS}; }}
    .dep-fail {{ color: {COLOR_ERROR}; }}
    .stButton > button {{
        border-radius: 0.5rem;
        font-weight: 600;
        transition: all 0.2s;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    .footer {{
        text-align: center;
        padding: 1.5rem;
        color: #999;
        font-size: 0.85rem;
        border-top: 1px solid #eee;
        margin-top: 2rem;
    }}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-header">'
    "<h1>🎬 B站视频自动笔记生成工作流</h1>"
    "<p>将B站视频自动转化为结构化学习笔记，支持语音转录、AI摘要、思维导图与智能截图</p>"
    "</div>",
    unsafe_allow_html=True,
)

st.sidebar.markdown("## 🧭 功能导航")
st.sidebar.markdown("---")
st.sidebar.markdown("请在左侧页面菜单中选择功能模块：")
st.sidebar.markdown("")
st.sidebar.markdown("| 功能 | 说明 |")
st.sidebar.markdown("|------|------|")
st.sidebar.markdown("| 📝 **基础功能** | 音频下载 + 语音转录 + AI笔记 |")
st.sidebar.markdown("| 🖼️ **带图功能** | 视频下载 + 截图 + 图文笔记 |")
st.sidebar.markdown("| ⚙️ **API设置** | DeepSeek API 配置管理 |")
st.sidebar.markdown("| 📂 **输出成果** | 查看/打开处理结果文件 |")
st.sidebar.markdown("---")

deps = check_dependencies()
if deps:
    st.sidebar.error("⚠️ 系统依赖缺失")
    for d in deps:
        st.sidebar.warning(f"  • {d}")
else:
    st.sidebar.success("✅ 系统依赖已就绪")

api_key = config.get("deepseek", {}).get("api_key", "")
if api_key:
    masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    st.sidebar.success(f"🔑 API Key: {masked}")
else:
    st.sidebar.warning("⚠️ 未配置 DeepSeek API Key")
    st.sidebar.info("请前往 **API设置** 页面配置")

st.markdown("### 📊 项目概况")

col1, col2, col3, col4 = st.columns(4)

project_root = config_loader.get_project_root()
output_dir = config_loader.resolve_path(config, "output_dir")
processed_file = os.path.join(project_root, "processed.json")
failed_file = os.path.join(project_root, "failed.json")

from src.utils import load_json

processed = load_json(processed_file, [])
failed = load_json(failed_file, [])

output_count = 0
if os.path.isdir(output_dir):
    output_count = len(
        [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
    )

with col1:
    st.markdown(
        f'<div class="stat-card success"><div class="number">{len(processed)}</div>成功处理</div>',
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f'<div class="stat-card warning"><div class="number">{len(failed)}</div>处理失败</div>',
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f'<div class="stat-card info"><div class="number">{output_count}</div>输出目录</div>',
        unsafe_allow_html=True,
    )

with col4:
    whisper_model = config.get("whisper", {}).get("model", "medium")
    st.markdown(
        f'<div class="stat-card"><div class="number" style="font-size: 1.5rem;">{whisper_model}</div>Whisper 模型</div>',
        unsafe_allow_html=True,
    )

st.markdown("---")

st.markdown("### 🚀 快速开始")

tab1, tab2 = st.tabs(["📋 使用流程", "⚡ 快捷操作"])

with tab1:
    st.markdown("""
**三步开始使用：**

1. **配置 API Key** → 前往 **API设置** 页面，填入 DeepSeek API Key
2. **输入视频链接** → 在 **基础功能** 或 **带图功能** 页面输入 B站视频 URL
3. **查看输出成果** → 前往 **输出成果** 页面浏览生成的笔记文件

**两种处理模式：**
- 📝 **基础模式**：下载音频 → 语音转录 → AI标点补全 → AI摘要 → 思维导图
- 🖼️ **带图模式**：基础模式 + 视频下载 → 智能截图 → 图文整合笔记
""")

with tab2:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("📝 基础功能", use_container_width=True):
            st.switch_page("pages/01_基础功能.py")
    with c2:
        if st.button("🖼️ 带图功能", use_container_width=True):
            st.switch_page("pages/02_带图功能.py")
    with c3:
        if st.button("⚙️ API设置", use_container_width=True):
            st.switch_page("pages/03_API设置.py")
    with c4:
        if st.button("📂 输出成果", use_container_width=True):
            st.switch_page("pages/04_输出成果.py")

st.markdown("---")

st.markdown("### 📁 最近处理记录")

if processed:
    recent = processed[-5:][::-1]
    for item in recent:
        mode_badge = "🖼️ 带图" if item.get("mode") == "with_images" else "📝 基础"
        st.markdown(
            f"- {mode_badge} | **{item.get('title', '未知')}** "
            f"| {item.get('processed_at', '')[:16]} "
            f"| `{os.path.basename(item.get('output_dir', ''))}`"
        )
else:
    st.info("暂无处理记录，快去处理第一个视频吧！")

st.markdown(
    '<div class="footer">'
    "B站视频笔记工作流 v1.3.0 | Powered by Streamlit + Whisper + DeepSeek | "
    '<a href="https://github.com" target="_blank">GitHub</a>'
    "</div>",
    unsafe_allow_html=True,
)
