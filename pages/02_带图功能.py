import os
import sys

import streamlit as st


st.set_page_config(
    page_title="烟雨春明 - 工作台",
    page_icon="春",
    layout="wide",
    initial_sidebar_state="expanded",
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui import render_dashboard


render_dashboard()
