# 2. Inject CSS Custom: Robotic Theme & Layout Full Edge
st.markdown("""
<style>
    /* Nhập font Cyberpunk / Sci-Fi */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&display=swap');

    /* Đổi màu tất cả chữ văn bản mặc định sang MÀU TRẮNG */
    html, body, [class*="css"], .stApp, p, span, label, div {
        color: #ffffff !important;
    }

    /* Bỏ hoàn toàn Padding khu vực Main Content để Map tràn viền */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }

    /* Tối ưu nền Sidebar dạng Dark Robotic */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e17 0%, #121929 100%);
        border-right: 2px solid #00f0ff;
        box-shadow: 5px 0px 15px rgba(0, 240, 255, 0.2);
    }

    /* Style Tiêu đề Sidebar */
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

    /* Nút bấm kiểu ROBOTIC CYBERPUNK */
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

    /* Container hiển thị thông số dạng HUD display */
    .hud-card {
        background: rgba(16, 26, 44, 0.85);
        border: 1px solid #00f0ff;
        border-left: 4px solid #7000ff;
        border-radius: 6px;
        padding: 12px;
        margin-top: 10px;
        box-shadow: inset 0 0 10px rgba(0, 240, 255, 0.1);
        font-family: 'Rajdhani', sans-serif;
    }

    .hud-label {
        color: #ffffff !important;
        font-size: 0.85rem;
        text-transform: uppercase;
    }

    .hud-value {
        color: #00f0ff !important;
        font-size: 1.3rem;
        font-weight: bold;
        font-family: 'Orbitron', sans-serif;
    }

    /* Divider phong cách Laser line */
    hr {
        border-color: #00f0ff !important;
        opacity: 0.3;
    }
</style>
""", unsafe_allow_html=True)
