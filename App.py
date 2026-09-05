import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# 1. Cấu hình trang Full-Width
st.set_page_config(
    page_title="Hệ Thống Tối Ưu Lộ Trình - Robotic UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS Tối ưu giao diện - An toàn, không vỡ layout
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&display=swap');

    /* Ẩn Header, Footer mặc định của Streamlit */
    header, footer, [data-testid="stHeader"] {
        display: none !important;
    }

    /* Đổi màu nền toàn ứng dụng */
    .stApp {
        background-color: #120700 !important;
    }

    /* Loại bỏ hoàn toàn Margin/Padding của Main Container để bản đồ tràn sát cạnh */
    .main .block-container {
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }

    /* Ép văn bản hiển thị rõ màu TRẮNG */
    p, span, label, h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }

    /* Tối ưu Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2b1100 0%, #170900 100%) !important;
        border-right: 2px solid #ff6600 !important;
        box-shadow: 4px 0px 15px rgba(255, 102, 0, 0.3) !important;
    }

    /* Khắc phục lỗi đường kẻ ngang st.divider() bị kéo dài / vỡ layout */
    [data-testid="stSidebar"] hr {
        border: none !important;
        border-top: 1px solid #ff6600 !important;
        opacity: 0.4 !important;
        margin: 12px 0 !important;
        width: 100% !important;
    }

    /* Style Tiêu đề Sidebar */
    .robot-title {
        font-family: 'Orbitron', sans-serif;
        color: #00f0ff !important;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.6);
        margin-top: 10px;
        margin-bottom: 15px;
        font-size: 1.3rem;
    }

    /* Nút bấm Robotic Cyberpunk */
    div.stButton > button {
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        color: #000000 !important;
        background: linear-gradient(135deg, #00f0ff 0%, #7000ff 100%) !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 10px 20px !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        transition: all 0.3s ease-in-out !important;
        box-shadow: 0 0 12px rgba(0, 240, 255, 0.4) !important;
    }

    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 0.8) !important;
        color: #ffffff !important;
    }

    /* Card hiển thị chỉ số HUD */
    .hud-card {
        background: rgba(43, 17, 0, 0.8) !important;
        border: 1px solid #ff6600 !important;
        border-left: 4px solid #00f0ff !important;
        border-radius: 4px;
        padding: 10px;
        margin-top: 8px;
        font-family: 'Rajdhani', sans-serif;
    }

    .hud-label {
        color: #d0d0d0 !important;
        font-size: 0.8rem;
        text-transform: uppercase;
    }

    .hud-value {
        color: #00f0ff !important;
        font-size: 1.2rem;
        font-weight: bold;
        font-family: 'Orbitron', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# 3. Đọc dữ liệu từ file Excel
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(subset=['Latitude', 'Longitude'])
        return df
    except Exception as e:
        return pd.DataFrame()

# 4. Hàm lấy đường đi từ OSRM
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
    except Exception:
        pass
        
    return None, [], 0, 0

# Khởi tạo dữ liệu
df = load_data('QuanLyTĐ.xlsx')

if df.empty:
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

# Lấy chiều cao thực tế của màn hình trình duyệt (mặc định 900 nếu chưa bắt được)
window_height = streamlit_js_eval(js_expressions='window.innerHeight', key='viewport_height')
map_height = window_height if window_height and window_height > 200 else 900

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("<h3 class='robot-title'>🤖 MAKE BY BANGNC13</h3>", unsafe_allow_html=True)
    
    # Select target points
    options = df['Tên đối tượng'].tolist()
    selected_names = st.multiselect(
        "🎯 Danh sách tập điểm target:",
        options=options,
        help="Chọn các điểm mục tiêu cần di chuyển"
    )
    
    st.divider()
    
    # Định vị GPS
    st.markdown("<div class='hud-label'>📡 Trạng thái định vị GPS:</div>", unsafe_allow_html=True)
    loc_data = get_geolocation()
    
    if loc_data and 'coords' in loc_data:
        lat = loc_data['coords']['latitude']
        lon = loc_data['coords']['longitude']
        st.session_state.current_loc = (lat, lon)
        st.markdown(f"""
        <div class='hud-card'>
            <div class='hud-label'>Tọa độ GPS hiện tại</div>
            <div class='hud-value'>{lat:.4f}, {lon:.4f}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Đang quét tín hiệu GPS...")

    st.divider()

    # Nút bấm hành động
    if st.button("⚡ TỐI ƯU LỘ TRÌNH ⚡", use_container_width=True):
        if not st.session_state.current_loc:
            st.error("Chưa xác định được GPS xuất phát!")
        elif not selected_names:
            st.error("Hãy chọn ít nhất 1 điểm mục tiêu!")
        else:
            selected_df = df[df['Tên đối tượng'].isin(selected_names)]
            points_list = selected_df.to_dict('records')
            
            with st.spinner("🤖 Đang tính toán lộ trình tối ưu..."):
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

    # Hiển thị kết quả tính toán
    if st.session_state.route_summary:
        st.divider()
        st.markdown(f"""
        <div class='hud-card'>
            <div class='hud-label'>Tổng khoảng cách</div>
            <div class='hud-value'>{st.session_state.route_summary['distance']:.2f} KM</div>
            <div class='hud-label' style='margin-top:6px;'>Thời gian dự kiến</div>
            <div class='hud-value'>{st.session_state.route_summary['duration']:.0f} PHÚT</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><b style='color:#ffffff;'>📍 Lộ trình di chuyển:</b>", unsafe_allow_html=True)
        for pt in st.session_state.ordered_points:
            st.markdown(f"<span style='color:#00f0ff;'>[{pt['Order']}]</span> {pt['Name']}", unsafe_allow_html=True)

# ================= MAIN BẢN ĐỒ FULL MÀN HÌNH =================
if st.session_state.current_loc:
    map_center = st.session_state.current_loc
else:
    map_center = [df['Latitude'].mean(), df['Longitude'].mean()]

m = folium.Map(location=map_center, zoom_start=14, tiles=None)

# Nền bản đồ Google
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

# Marker Vị trí GPS hiện tại
if st.session_state.current_loc:
    folium.Marker(
        location=st.session_state.current_loc,
        popup="<b>Vị trí hiện tại (GPS Origin)</b>",
        tooltip="GPS ORIGIN",
        icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')
    ).add_to(m)

# Marker các điểm đến (Cyber styling)
if st.session_state.ordered_points:
    for pt in st.session_state.ordered_points:
        folium.Marker(
            location=(pt['Latitude'], pt['Longitude']),
            popup=f"<b>Điểm {pt['Order']}: {pt['Name']}</b>",
            tooltip=f"[{pt['Order']}] {pt['Name']}",
            icon=folium.DivIcon(
                html=f"""<div style="
                    background: linear-gradient(135deg, #00f0ff 0%, #7000ff 100%);
                    color: white;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-weight: bold;
                    font-family: 'Orbitron', sans-serif;
                    border: 2px solid #ffffff;
                    box-shadow: 0 0 10px rgba(0, 240, 255, 0.8);
                ">{pt['Order']}</div>"""
            )
        ).add_to(m)

# Vẽ đường nối lộ trình Neon
if st.session_state.route_coords:
    folium.PolyLine(
        st.session_state.route_coords,
        color="#00F0FF",
        weight=5,
        opacity=0.9,
        tooltip="Cyber Route Line"
    ).add_to(m)

folium.LayerControl().add_to(m)

# Hiển thị bản đồ tràn full cạnh dưới chuẩn theo chiều cao màn hình
st_folium(m, use_container_width=True, height=map_height)
