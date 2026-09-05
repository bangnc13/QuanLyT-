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
        padding: 12px 24px !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        clip-path: polygon(10% 0, 100% 0, 90% 100%, 0 100%);
        transition: all 0.3s ease-in-out !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.4) !important;
    }

    div.stButton > button:hover {
        transform: scale(1.03) translateY(-2px) !important;
        box-shadow: 0 0 25px rgba(0, 240, 255, 0.8), 0 0 10px rgba(112, 0, 255, 0.8) !important;
        color: #ffffff !important;
    }

    .hud-card {
        background: rgba(51, 20, 0, 0.85) !important;
        border: 1px solid #ff6600 !important;
        border-left: 4px solid #00f0ff !important;
        border-radius: 6px;
        padding: 12px;
        margin-top: 10px;
        box-shadow: inset 0 0 10px rgba(255, 102, 0, 0.2);
        font-family: 'Rajdhani', sans-serif;
    }

    .hud-label { color: #ffffff !important; font-size: 0.85rem; text-transform: uppercase; }
    .hud-value { color: #00f0ff !important; font-size: 1.3rem; font-weight: bold; font-family: 'Orbitron', sans-serif; }
    hr { border-color: #ff6600 !important; opacity: 0.5; }

    [data-baseweb="select"] > div { background-color: #1f0c00 !important; border: 1px solid #ff6600 !important; color: #00f0ff !important; }
    [data-baseweb="select"] div[role="button"], [data-baseweb="select"] input, [data-baseweb="select"] input::placeholder { color: #00f0ff !important; -webkit-text-fill-color: #00f0ff !important; }
    span[data-baseweb="tag"] { background-color: rgba(0, 240, 255, 0.2) !important; border: 1px solid #00f0ff !important; }
    span[data-baseweb="tag"] * { color: #00f0ff !important; font-weight: bold !important; }
    ul[role="listbox"] { background-color: #1f0c00 !important; border: 1px solid #00f0ff !important; }
    li[role="option"] span, li[role="option"] div { color: #00f0ff !important; }
    li[role="option"]:hover { background-color: rgba(0, 240, 255, 0.2) !important; }
</style>
""", unsafe_allow_html=True)

# 3. Hàm phụ trợ
def haversine(lat1, lon1, lat2, lon2):
    r = 6371000
    phi1, phi2 = radians(lat1
