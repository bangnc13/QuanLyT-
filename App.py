import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# 1. Cấu hình trang Full-Width
st.set_page_config(
    page_title="Hệ Thống Tối Ưu Lộ Trình - Robotic UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject CSS Custom: Theme Nền Cam Robotic & Layout Full Edge
st.markdown("""
<style>
    /* Nhập font Cyberpunk / Sci-Fi */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&display=swap');

    /* Bỏ hoàn toàn Padding khu vực Main Content */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }

    /* Đổi nền chính toàn ứng dụng sang màu Cam Tối / Cam Cyberpunk */
    .stApp {
        background-color: #1a0a00 !important;
    }

    /* Ép tất cả văn bản thường thành màu TRẮNG */
    html, body, [class*="css"], .stMarkdown, p, span, label, div {
        color: #ffffff !important;
    }

    /* Tối ưu nền Sidebar dạng Dark Orange Robotic Gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #331400 0%, #1f0c00 100%) !important;
        border-right: 2px solid #ff6600 !important;
        box-shadow: 5px 0px 15px rgba(255, 102, 0, 0.4) !important;
    }

    /* Style Tiêu đề Sidebar - Giữ màu Cyan Neon nổi bật trên nền cam */
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

    /* Nút bấm kiểu ROBOTIC CYBERPUNK - Giữ nguyên Gradient Neon */
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

    /* Container hiển thị thông số dạng HUD display - Nền Cam Đen */
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

    /* Nhãn chữ thường - Màu TRẮNG */
    .hud-label {
        color: #ffffff !important;
        font-size: 0.85rem;
        text-transform: uppercase;
    }

    /* Giá trị thông số - Giữ màu Cyan Neon */
    .hud-value {
        color: #00f0ff !important;
        font-size: 1.3rem;
        font-weight: bold;
        font-family: 'Orbitron', sans-serif;
    }

    /* Divider phong cách Laser line Cam Neon */
    hr {
        border-color: #ff6600 !important;
        opacity: 0.5;
    }
</style>
""", unsafe_allow_html=True)

# 3. Hàm nạp dữ liệu
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(subset=['Latitude', 'Longitude'])
        return df
    except Exception as e:
        st.error(f"Lỗi đọc file: {e}")
        return pd.DataFrame()

# 4. OSRM Route Optimization
def get_optimized_route(origin, points_list):
    coords_str = f"{origin[1]},{origin[0]}"
    for pt in points_list:
        coords_str += f";{pt['Longitude']},{pt['Latitude']}"

    url = f"http://router.project-osrm.org/trip/v1/driving/{coords_str}?overview=full&geometries=geojson&source=first&roundtrip=false"
    
    try:
        res = requests.get(url, timeout=10).json()
        if res.get('code') == 'Ok':
            trip = res['trips'][0]
            waypoints = res['waypoints']
            
            route_coords = [(lat, lon) for lon, lat in trip['geometry']['coordinates']]
            
            ordered_points = []
            for wp in waypoints:
                idx = wp['waypoint_index']
                if idx == 0:
                    continue
                
                pt_info = points_list[idx - 1]
                ordered_points.append({
                    'Name': pt_info['Tên đối tượng'],
                    'Latitude': pt_info['Latitude'],
                    'Longitude': pt_info['Longitude'],
                    'Order': len(ordered_points) + 1
                })
            
            ordered_points.sort(key=lambda x: x['Order'])
            return route_coords, ordered_points, trip['distance'] / 1000.0, trip['duration'] / 60.0
    except Exception as e:
        st.error(f"Lỗi kết nối OSRM API: {e}")
        
    return None, [], 0, 0

# Khởi tạo dữ liệu
df = load_data('QuanLyTĐ.xlsx')

if df.empty:
    st.warning("⚠️ Không tìm thấy dữ liệu từ QuanLyTĐ.xlsx. Đang sử dụng dữ liệu giả lập mẫu.")
    df = pd.DataFrame({
        'Tên đối tượng': ['Điểm A', 'Điểm B', 'Điểm C'],
        'Latitude': [21.0285, 21.0350, 21.0200],
        'Longitude': [105.8542, 105.8400, 105.8600]
    })

if 'current_loc' not in st.session_state:
    st.session_state.current_loc = None
if 'route_coords' not in st.session_state:
    st.session_state.route_coords = None
if 'ordered_points' not in st.session_state:
    st.session_state.ordered_points = []
if 'route_summary' not in st.session_state:
    st.session_state.route_summary = None

# ================= SIDEBAR (ROBOTIC CONTROL CENTER) =================
with st.sidebar:
    st.markdown("<h2 class='robot-title'>🤖 Make By BangNC13</h2>", unsafe_allow_html=True)
    st.caption("")
    
    # 1. Chọn điểm
    options = df['Tên đối tượng'].tolist()
    selected_names = st.multiselect(
        "🎯 Danh sách tập điểm target:",
        options=options,
        help="Chọn các mục tiêu cần quét lộ trình"
    )
    
    st.divider()
    
    # 2. Định vị GPS
    st.markdown("<div class='hud-label'>📡 Trạng thái định vị GPS:</div>", unsafe_allow_html=True)
    loc_data = get_geolocation()
    
    if loc_data and 'coords' in loc_data:
        lat = loc_data['coords']['latitude']
        lon = loc_data['coords']['longitude']
        st.session_state.current_loc = (lat, lon)
        st.markdown(f"""
        <div class='hud-card'>
            <div class='hud-label'>Tọa độ hiện tại</div>
            <div class='hud-value'>{lat:.4f}, {lon:.4f}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Bật GPS thiết bị để xác định điểm gốc.")

    st.divider()

    # 3. Nút kích hoạt lộ trình
    if st.button("⚡ Bấm xem lộ trình ⚡", use_container_width=True):
        if not st.session_state.current_loc:
            st.error("Chưa có tín hiệu GPS!")
        elif not selected_names:
            st.error("Chưa chọn mục tiêu!")
        else:
            selected_df = df[df['Tên đối tượng'].isin(selected_names)]
            points_list = selected_df.to_dict('records')
            
            with st.spinner("🤖 Đang tính toán ma trận khoảng cách..."):
                route_coords, ordered_points, dist_km, dur_min = get_optimized_route(
                    st.session_state.current_loc, points_list
                )
                
                if route_coords:
                    st.session_state.route_coords = route_coords
                    st.session_state.ordered_points = ordered_points
                    st.session_state.route_summary = {
                        'distance': dist_km,
                        'duration': dur_min
                    }

    # Hiển thị HUD kết quả
    if st.session_state.route_summary:
        st.divider()
        st.markdown(f"""
        <div class='hud-card'>
            <div class='hud-label'>Tổng quãng đường</div>
            <div class='hud-value'>{st.session_state.route_summary['distance']:.2f} KM</div>
            <div class='hud-label' style='margin-top:8px;'>Thời gian di chuyển</div>
            <div class='hud-value'>{st.session_state.route_summary['duration']:.0f} PHÚT</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><b style='color:#ffffff;'>📍 Lộ trình thực thi:</b>", unsafe_allow_html=True)
        for pt in st.session_state.ordered_points:
            st.markdown(f"<span style='color:#00f0ff;'>[{pt['Order']}]</span> <span style='color:#ffffff;'>{pt['Name']}</span>", unsafe_allow_html=True)

# ================= HIỂN THỊ BẢN ĐỒ FULL CẠNH VIỀN (MAIN CONTENT) =================
if st.session_state.current_loc:
    map_center = st.session_state.current_loc
else:
    map_center = [df['Latitude'].mean(), df['Longitude'].mean()]

m = folium.Map(location=map_center, zoom_start=15, tiles=None)

# Google Maps Tile Layers
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google Maps',
    name='Google Street',
    overlay=False
).add_to(m)

folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satellite',
    name='Google Satellite',
    overlay=False
).add_to(m)

# 1. Đánh dấu GPS xuất phát
if st.session_state.current_loc:
    folium.Marker(
        location=st.session_state.current_loc,
        popup="<b style='color:#000000;'>Vị trí xuất phát (GPS CORE)</b>",
        tooltip="GPS ORIGIN",
        icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')
    ).add_to(m)

# 2. Điểm ghé thăm Cyber Matrix Marker
if st.session_state.ordered_points:
    for pt in st.session_state.ordered_points:
        folium.Marker(
            location=(pt['Latitude'], pt['Longitude']),
            popup=f"<b style='color:#000000;'>Điểm {pt['Order']}: {pt['Name']}</b>",
            tooltip=f"TARGET [{pt['Order']}]: {pt['Name']}",
            icon=folium.DivIcon(
                html=f"""<div style="
                    background: linear-gradient(135deg, #00f0ff 0%, #7000ff 100%);
                    color: white;
                    border-radius: 50%;
                    width: 32px;
                    height: 32px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-weight: 900;
                    font-family: 'Orbitron', sans-serif;
                    border: 2px solid #ffffff;
                    box-shadow: 0 0 12px rgba(0, 240, 255, 0.9);
                ">{pt['Order']}</div>"""
            )
        ).add_to(m)

# 3. Polyline Cyber Neon
if st.session_state.route_coords:
    folium.PolyLine(
        st.session_state.route_coords,
        color="#00F0FF",
        weight=6,
        opacity=0.9,
        tooltip="Cyber Route Trajectory"
    ).add_to(m)

folium.LayerControl().add_to(m)

# Render Map 100% VH
st_folium(m, width="100%", height=920)
