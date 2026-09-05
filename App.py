import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# ---------------------------------------------------------
# CẤU HÌNH TRANG & CUSTOM DARK THEME CSS
# ---------------------------------------------------------
st.set_page_config(
    page_title="Công cụ Quản lý & Tối ưu Lộ trình Tập điểm",
    page_icon="🗺️",
    layout="wide"
)

# Custom CSS cho giao diện Dark Theme đồng bộ
st.markdown("""
    <style>
    /* Nền chính và font chữ */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    /* Cards / Expander / Containers */
    div[data-testid="stMetricValue"] {
        color: #58a6ff;
    }
    /* Button primary */
    .stButton>button {
        background-color: #238636;
        color: #ffffff;
        border: none;
        border-radius: 6px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        color: #ffffff;
    }
    /* Divider */
    hr {
        border-color: #30363d;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🗺️ Tối ưu quãng đường thu cước TQG")

# 1. Hàm nạp dữ liệu từ file Excel
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(subset=['Latitude', 'Longitude'])
        return df
    except Exception as e:
        st.error(f"Không thể đọc file {file_path}: {e}")
        return pd.DataFrame()

# 2. Hàm tối ưu hóa thứ tự ghé thăm (OSRM Trip API)
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
            distance_km = trip['distance'] / 1000.0
            duration_min = trip['duration'] / 60.0

            return route_coords, ordered_points, distance_km, duration_min
    except Exception as e:
        st.error(f"Lỗi khi tính toán lộ trình tối ưu: {e}")

    return None, [], 0, 0

# Đọc dữ liệu
df = load_data('QuanLyTĐ.xlsx')

if df.empty:
    st.warning("Không tìm thấy dữ liệu tập điểm hợp lệ từ QuanLyTĐ.xlsx.")
    st.stop()

# Khởi tạo Session State
if 'current_loc' not in st.session_state:
    st.session_state.current_loc = None

if 'route_coords' not in st.session_state:
    st.session_state.route_coords = None

if 'ordered_points' not in st.session_state:
    st.session_state.ordered_points = []

if 'route_summary' not in st.session_state:
    st.session_state.route_summary = None

# ================= TẠO BẢNG ĐIỀU KHIỂN (SIDEBAR) =================
with st.sidebar:
    st.header("📋 Make by BangNC13")

    options = df['Tên đối tượng'].tolist()
    selected_names = st.multiselect(
        "Chọn danh sách tập điểm cần ghé thăm:",
        options=options,
        help="Chọn nhiều điểm để hệ thống tự động sắp xếp thứ tự đi tối ưu nhất"
    )

    st.divider()

    st.subheader("📍 Định vị GPS")
    loc_data = get_geolocation()

    if loc_data and 'coords' in loc_data:
        lat = loc_data['coords']['latitude']
        lon = loc_data['coords']['longitude']
        st.session_state.current_loc = (lat, lon)
        st.success(f"GPS thiết bị: {lat:.5f}, {lon:.5f}")
    else:
        st.info("Hãy cấp quyền 'Vị trí' (Location) cho trình duyệt.")

    st.divider()

    if st.button("🚀 Bấm tính lộ trình", type="primary", use_container_width=True):
        if not st.session_state.current_loc:
            st.error("Chưa nhận diện được vị trí GPS hiện tại!")
        elif not selected_names:
            st.error("Vui lòng chọn ít nhất 1 tập điểm trong danh sách!")
        else:
            selected_df = df[df['Tên đối tượng'].isin(selected_names)]
            points_list = selected_df.to_dict('records')

            with st.spinner("Đang tính toán tuyến đường tối ưu..."):
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
                    st.success("Đã tối ưu hóa lộ trình thành công!")

    if st.session_state.route_summary:
        st.divider()
        st.markdown(f"**Tổng quãng đường:** `<span style='color:#58a6ff'>{st.session_state.route_summary['distance']:.2f} km</span>`", unsafe_allow_html=True)
        st.markdown(f"**Thời gian dự kiến:** `<span style='color:#58a6ff'>{st.session_state.route_summary['duration']:.0f} phút</span>`", unsafe_allow_html=True)

        st.subheader("📌 Thứ tự ghé thăm tối ưu:")
        for pt in st.session_state.ordered_points:
            st.write(f"**{pt['Order']}.** {pt['Name']}")

# ================= HIỂN THỊ BẢN ĐỒ (DARK MODE) =================
if st.session_state.current_loc:
    map_center = st.session_state.current_loc
else:
    map_center = [df['Latitude'].mean(), df['Longitude'].mean()]

# Khởi tạo bản đồ
m = folium.Map(location=map_center, zoom_start=14, tiles=None)

# 1. Layer CartoDB Dark Matter (Đêm / Tối chuẩn)
folium.TileLayer(
    tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    name='Dark Mode (Mặc định)',
    overlay=False,
    control=True
).add_to(m)

# 2. Layer Google Maps Vệ Tinh (Hợp với Dark Theme)
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satellite',
    name='Google Maps (Vệ tinh)',
    overlay=False,
    control=True
).add_to(m)

# 3. Layer Google Maps Đường Phố
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google Maps',
    name='Google Maps (Chuẩn)',
    overlay=False,
    control=True
).add_to(m)

# 1. Đánh dấu vị trí xuất phát GPS (Màu đỏ Neon)
if st.session_state.current_loc:
    folium.Marker(
        location=st.session_state.current_loc,
        popup="<b>Vị trí xuất phát (GPS)</b>",
        tooltip="Xuất phát",
        icon=folium.Icon(color='red', icon='play', prefix='fa')
    ).add_to(m)

# 2. Đánh dấu các tập điểm (Màu Xanh Lá Neon tương phản nền tối)
if st.session_state.ordered_points:
    for pt in st.session_state.ordered_points:
        folium.Marker(
            location=(pt['Latitude'], pt['Longitude']),
            popup=f"<b>Điểm {pt['Order']}: {pt['Name']}</b>",
            tooltip=f"Điểm {pt['Order']}: {pt['Name']}",
            icon=folium.DivIcon(
                html=f"""<div style="
                    background-color: #238636;
                    color: #ffffff;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-weight: bold;
                    font-size: 14px;
                    border: 2px solid #58a6ff;
                    box-shadow: 0px 0px 8px rgba(88, 166, 255, 0.8);
                ">{pt['Order']}</div>"""
            )
        ).add_to(m)

# 3. Vẽ đường đi (Màu Cyan / Xanh lam sáng rực rỡ trên nền tối)
if st.session_state.route_coords:
    folium.PolyLine(
        st.session_state.route_coords,
        color="#00D2FF",
        weight=5,
        opacity=0.9,
        tooltip="Lộ trình di chuyển"
    ).add_to(m)

folium.LayerControl().add_to(m)

# Render bản đồ lên Web
st_folium(m, width="100%", height=680)
