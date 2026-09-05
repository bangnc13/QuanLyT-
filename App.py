import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from math import radians, cos, sin, asin, sqrt

# 1. Cấu hình trang Full-Width
st.set_page_config(
    page_title="Hệ Thống Tối Ưu Lộ Trình - Realtime UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject CSS Custom (Bo tròn viền NEON CAM cho nút Toggle Sidebar)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&display=swap');

    .block-container { padding: 0rem !important; max-width: 100% !important; }
    .stApp { background-color: #1a0a00 !important; }
    html, body, .stMarkdown, p, label { color: #ffffff !important; }

    /* ================= CSS NÚT ẨN/HIỆN MENU SIDEBAR (BO TRÒN VIỀN NEON CAM) ================= */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarExpandButton"] button,
    [data-testid="stSidebarExpandButton"],
    button[data-testid="baseButton-headerNoPadding"],
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] button {
        background-color: #1a0a00 !important;
        border: 2px solid #ff6600 !important;
        border-radius: 50% !important;
        color: #ff6600 !important;
        box-shadow: 0 0 12px rgba(255, 102, 0, 0.8) !important;
        transition: all 0.3s ease-in-out !important;
        width: 42px !important;
        height: 42px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
        margin: 5px !important;
    }

    /* Hiệu ứng Hover nút Menu */
    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="stSidebarCollapseButton"]:hover,
    [data-testid="stSidebarExpandButton"] button:hover,
    [data-testid="stSidebarExpandButton"]:hover,
    button[data-testid="baseButton-headerNoPadding"]:hover,
    [data-testid="collapsedControl"]:hover,
    [data-testid="collapsedControl"] button:hover {
        background-color: #ff6600 !important;
        color: #000000 !important;
        box-shadow: 0 0 25px rgba(255, 102, 0, 1) !important;
        transform: scale(1.1) !important;
    }

    /* Định dạng Icon bên trong nút Menu sang màu Cam */
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebarExpandButton"] svg,
    button[data-testid="baseButton-headerNoPadding"] svg,
    [data-testid="collapsedControl"] svg {
        fill: #ff6600 !important;
        color: #ff6600 !important;
        stroke: #ff6600 !important;
        transition: all 0.3s ease-in-out !important;
    }

    [data-testid="stSidebarCollapseButton"] button:hover svg,
    [data-testid="stSidebarExpandButton"] button:hover svg,
    button[data-testid="baseButton-headerNoPadding"]:hover svg,
    [data-testid="collapsedControl"]:hover svg,
    [data-testid="collapsedControl"] button:hover svg {
        fill: #000000 !important;
        color: #000000 !important;
        stroke: #000000 !important;
    }

    /* Giao diện Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #331400 0%, #1f0c00 100%) !important;
        border-right: 2px solid #ff6600 !important;
        box-shadow: 5px 0px 15px rgba(255, 102, 0, 0.4) !important;
    }

    .robot-title {
        font-family: 'Orbitron', sans-serif;
        color: #00f0ff !important;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.7);
        margin-top: 15px;
        margin-bottom: 20px;
    }

    div.stButton > button {
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        color: #000000 !important;
        background: linear-gradient(135deg, #00f0ff 0%, #7000ff 100%) !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 12px 2
