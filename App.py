import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

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
        df = df.dropna(subset=['Latitude', 'Longitude'])
        return df
    except Exception as e:
        st.error(f"Không thể đọc file {file_path}: {e}")
        return pd.DataFrame()

# 2. Hàm lấy lộ trình từ OSRM API (đường đi xe máy / ô tô)
def get_osrm_route(origin, destination):
    url = f"http://router.project-osrm.org/route/v1/driving/{origin[1]},{origin[0]};{destination[1]},{destination[0]}?overview=full&geometries=geojson"
    try:
        res = requests.get(url, timeout=5).json()
        if res.get('code') == 'Ok':
            coords = res['routes'][0]['geometry']['coordinates']
            return [(lat, lon) for lon, lat in coords]
    except Exception as e:
        st.error(f"Lỗi khi tính toán lộ trình: {e}")
    return [origin, destination]

# Đọc file Excel
df = load_data('QuanLyTĐ.xlsx')

if df.empty:
    st.warning("Không tìm thấy dữ liệu tập điểm hợp lệ từ QuanLyTĐ.xlsx.")
    st.stop()

# Khởi tạo trạng thái dữ liệu trong Session State
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
    
    # 2. Lấy vị trí GPS chính xác từ thiết bị
    st.subheader("📍 Định vị GPS")
    loc_data = get_geolocation()
    
    if loc_data and 'coords' in loc_data:
        lat = loc_data['coords']['latitude']
        lon = loc_data['coords']['longitude']
        st.session_state.current_loc = (lat, lon)
        st.success(f"GPS thiết bị: {lat:.5f}, {lon:.5f}")
    else:
        st.info("Vui lòng cấp quyền truy cập Vị trí (Location) trên điện thoại / trình duyệt.")

    st.divider()

    # 3. Nút "Bấm" tính toán lộ trình
    if st.button("🚀 Bấm", type="primary", use_container_width=True):
        if not st.session_state.current_loc:
            st.error("Chưa nhận diện được vị trí GPS! Hãy kiểm tra quyền vị trí trên thiết bị.")
        elif not selected_names:
            st.error("Vui lòng chọn ít nhất 1 tập điểm trong danh sách!")
        else:
            selected_df = df[df['Tên đối tượng'].isin(selected_names)]
            st.session_state.selected_points_data = selected_df.to_dict('records')
            
            dest = (selected_df.iloc[0]['Latitude'], selected_df.iloc[0]['Longitude'])
            with st.spinner("Đang tìm lộ trình di chuyển tối ưu..."):
                st.session_state.route_coords = get_osrm_route(st.session_state.current_loc, dest)
            st.success("Đã tìm xong lộ trình!")

# ================= HIỂN THỊ BẢN ĐỒ (MAIN CONTENT) =================
if st.session_state.current_loc:
    map_center = st.session_state.current_loc
else:
    map_center = [df['Latitude'].mean(), df['Longitude'].mean()]

m = folium.Map(location=map_center, zoom_start=15)

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

# Đánh dấu vị trí hiện tại GPS (Màu đỏ)
if st.session_state.current_loc:
    folium.Marker(
        location=st.session_state.current_loc,
        popup="<b>Vị trí GPS của bạn</b>",
        tooltip="Vị trí thiết bị hiện tại",
        icon=folium.Icon(color='red', icon='user', prefix='fa')
    ).add_to(m)

# Đánh dấu các tập điểm được chọn (Màu xanh lá)
if st.session_state.selected_points_data:
    for pt in st.session_state.selected_points_data:
        folium.Marker(
            location=(pt['Latitude'], pt['Longitude']),
            popup=f"<b>{pt['Tên đối tượng']}</b>",
            tooltip=pt['Tên đối tượng'],
            icon=folium.Icon(color='green', icon='flag')
        ).add_to(m)

# Vẽ tuyến đường di chuyển xe máy (Màu xanh lam)
if st.session_state.route_coords:
    folium.PolyLine(
        st.session_state.route_coords,
        color="#0066FF",
        weight=6,
        opacity=0.8,
        tooltip="Lộ trình di chuyển xe máy"
    ).add_to(m)

folium.LayerControl().add_to(m)

# Render bản đồ lên giao diện Web
st_folium(m, width="100%", height=650)
