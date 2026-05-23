import os
import sys

import streamlit as st


st.set_page_config(
    page_title="烟雨春明",
    page_icon="明",
    layout="wide",
    initial_sidebar_state="expanded",
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ui import render_dashboard


pages = [
    st.Page(render_dashboard, title="主页", icon="🏠", default=True),
    st.Page("pages/03_API设置.py", title="API设置", icon="🔐"),
    st.Page("pages/04_输出成果.py", title="输出成果", icon="📂"),
]

st.navigation(pages).run()
