import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# Cấu hình trang
st.set_page_config(
    page_title="Công cụ Quản lý & Chỉ đường Tập điểm",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Quản lý Tập điểm & Chỉ đường Xe máy")

# 1. Hàm nạp dữ liệu từ file Excel
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        # Loại bỏ các dòng bị thiếu tọa độ
        df = df.dropna(subset=['Latitude', 'Longitude'])
        return df
    except Exception as e:
        st.error(f"Không thể đọc file {file_path}: {e}")
        return pd.DataFrame()

# 2. Hàm lấy vị trí hiện tại dựa trên IP
def get_current_location_by_ip():
    try:
        res = requests.get('https://ipinfo.io/json', timeout=5).json()
        if 'loc' in res:
            lat, lon = map(float, res['loc'].split(','))
            return lat, lon
    except Exception:
        pass
    return None

# 3. Hàm lấy lộ trình từ OSRM API (đường đi xe máy / ô tô)
def get_osrm_route(origin, destination):
    url = f"http://router.project-osrm.org/route/v1/driving/{origin[1]},{origin[0]};{destination[1]},{destination[0]}?overview=full&geometries=geojson"
    try:
        res = requests.get(url, timeout=5).json()
        if res.get('code') == 'Ok':
            coords = res['routes'][0]['geometry']['coordinates']
            # Chuyển đổi [lon, lat] từ OSRM thành [lat, lon] cho Folium
            return [(lat, lon) for lon, lat in coords]
    except Exception as e:
        st.error(f"Lỗi khi tính toán lộ trình: {e}")
    return [origin, destination]

# Đọc file Excel
df = load_data('QuanLyTĐ.xlsx')

if df.empty:
    st.warning("Không tìm thấy dữ liệu tập điểm hợp lệ từ QuanLyTĐ.xlsx.")
    st.stop()

# Khởi tạo trạng thái lưu dữ liệu
if 'current_loc' not in st.session_state:
    st.session_state.current_loc = None

if 'route_coords' not in st.session_state:
    st.session_state.route_coords = None

if 'selected_points_data' not in st.session_state:
    st.session_state.selected_points_data = []

# ================= TẠO BẢNG ĐIỀU KHIỂN (SIDEBAR) =================
with st.sidebar:
    st.header("📋 Bảng điều khiển")
    
    # 1. Danh sách chọn tập điểm
    options = df['Tên đối tượng'].tolist()
    selected_names = st.multiselect(
        "Chọn danh sách tập điểm cần đến:",
        options=options,
        help="Có thể gõ từ khóa để tìm nhanh"
    )
    
    st.divider()
    
    # 2. Nút bấm nhận vị trí hiện tại
    if st.button("📍 Lấy vị trí hiện tại", use_container_width=True):
        loc = get_current_location_by_ip()
        if loc:
            st.session_state.current_loc = loc
            st.success(f"Vị trí: {loc[0]:.5f}, {loc[1]:.5f}")
        else:
            default_lat = df['Latitude'].mean()
            default_lon = df['Longitude'].mean()
            st.session_state.current_loc = (default_lat, default_lon)
            st.warning("Không định vị được IP, sử dụng tọa độ trung tâm mặc định.")

    if st.session_state.current_loc:
        st.info(f"Vị trí xuất phát: {st.session_state.current_loc[0]:.5f}, {st.session_state.current_loc[1]:.5f}")

    st.divider()

    # 3. Nút "Bấm" tính toán lộ trình
    if st.button("🚀 Bấm", type="primary", use_container_width=True):
        if not st.session_state.current_loc:
            st.error("Vui lòng nhấn nút 'Lấy vị trí hiện tại' trước!")
        elif not selected_names:
            st.error("Vui lòng chọn ít nhất 1 tập điểm trong danh sách!")
        else:
            selected_df = df[df['Tên đối tượng'].isin(selected_names)]
            st.session_state.selected_points_data = selected_df.to_dict('records')
            
            dest = (selected_df.iloc[0]['Latitude'], selected_df.iloc[0]['Longitude'])
            with st.spinner("Đang vẽ lộ trình di chuyển..."):
                st.session_state.route_coords = get_osrm_route(st.session_state.current_loc, dest)
            st.success("Đã tìm xong lộ trình!")

# ================= HIỂN THỊ BẢN ĐỒ (MAIN CONTENT) =================
if st.session_state.current_loc:
    map_center = st.session_state.current_loc
else:
    map_center = [df['Latitude'].mean(), df['Longitude'].mean()]

m = folium.Map(location=map_center, zoom_start=14)

# Layer Google Maps Đường Phố
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google Maps',
    name='Google Maps',
    overlay=False,
    control=True
).add_to(m)

# Layer Google Maps Vệ Tinh
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satellite',
    name='Google Satellite',
    overlay=False,
    control=True
).add_to(m)

# Đánh dấu vị trí hiện tại (Đỏ)
if st.session_state.current_loc:
    folium.Marker(
        location=st.session_state.current_loc,
        popup="<b>Vị trí xuất phát</b>",
        tooltip="Vị trí của bạn",
        icon=folium.Icon(color='red', icon='user', prefix='fa')
    ).add_to(m)

# Đánh dấu tập điểm chọn (Xanh)
if st.session_state.selected_points_data:
    for pt in st.session_state.selected_points_data:
        folium.Marker(
            location=(pt['Latitude'], pt['Longitude']),
            popup=f"<b>{pt['Tên đối tượng']}</b>",
            tooltip=pt['Tên đối tượng'],
            icon=folium.Icon(color='green', icon='flag')
        ).add_to(m)

# Vẽ tuyến đường di chuyển (Xanh lam)
if st.session_state.route_coords:
    folium.PolyLine(
        st.session_state.route_coords,
        color="#0066FF",
        weight=6,
        opacity=0.8,
        tooltip="Lộ trình di chuyển xe máy"
    ).add_to(m)

folium.LayerControl().add_to(m)

# Render bản đồ lên Web
st_folium(m, width="100%", height=650)
