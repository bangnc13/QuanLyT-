import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# Cấu hình trang
st.set_page_config(
    page_title="Công cụ Quản lý & Tối ưu Lộ trình Tập điểm",
    page_icon="🗺️",
    layout="wide"
)

st.title("Tối ưu quãng đường thu cước TQG")

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

# 2. Hàm tối ưu hóa thứ tự ghé thăm và vẽ tuyến đường đi qua TẤT CẢ các điểm (OSRM Trip API)
def get_optimized_route(origin, points_list):
    """
    origin: (lat, lon)
    points_list: list các dict [{'Name': ..., 'lat': ..., 'lon': ...}]
    """
    # Ghép tọa độ: Điểm xuất phát (origin) ở đầu tiên
    coords_str = f"{origin[1]},{origin[0]}"
    for pt in points_list:
        coords_str += f";{pt['Longitude']},{pt['Latitude']}"

    # Gọi OSRM Trip API với tham số source=first (giữ điểm xuất phát cố định ở vị trí 0)
    url = f"http://router.project-osrm.org/trip/v1/driving/{coords_str}?overview=full&geometries=geojson&source=first&roundtrip=false"
    
    try:
        res = requests.get(url, timeout=10).json()
        if res.get('code') == 'Ok':
            trip = res['trips'][0]
            waypoints = res['waypoints']
            
            # Lấy danh sách tọa độ tuyến đường
            route_coords = [(lat, lon) for lon, lat in trip['geometry']['coordinates']]
            
            # Sắp xếp lại thứ tự tập điểm theo kết quả tối ưu từ OSRM
            ordered_points = []
            for wp in waypoints:
                idx = wp['waypoint_index']
                if idx == 0:
                    continue # Điểm 0 là vị trí xuất phát
                
                pt_info = points_list[idx - 1]
                ordered_points.append({
                    'Name': pt_info['Tên đối tượng'],
                    'Latitude': pt_info['Latitude'],
                    'Longitude': pt_info['Longitude'],
                    'Order': len(ordered_points) + 1
                })
            
            # Sắp xếp lại theo đúng thứ tự ghé thăm 1, 2, 3...
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

# Khởi tạo trạng thái dữ liệu trong Session State
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
    
    # 1. Danh sách chọn tập điểm
    options = df['Tên đối tượng'].tolist()
    selected_names = st.multiselect(
        "Chọn danh sách tập điểm cần ghé thăm:",
        options=options,
        help="Chọn nhiều điểm để hệ thống tự động sắp xếp thứ tự đi tối ưu nhất"
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
        st.info("Hãy cấp quyền 'Vị trí' (Location) cho trình duyệt.")

    st.divider()

    # 3. Nút "Bấm" tính toán lộ trình
    if st.button("🚀 Bấm", type="primary", use_container_width=True):
        if not st.session_state.current_loc:
            st.error("Chưa nhận diện được vị trí GPS hiện tại!")
        elif not selected_names:
            st.error("Vui lòng chọn ít nhất 1 tập điểm trong danh sách!")
        else:
            selected_df = df[df['Tên đối tượng'].isin(selected_names)]
            points_list = selected_df.to_dict('records')
            
            with st.spinner("Đang tính toán tuyến đường tối ưu qua tất cả các điểm..."):
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

    # Hiển thị thông tin tổng quan và danh sách thứ tự đi
    if st.session_state.route_summary:
        st.divider()
        st.markdown(f"**Tổng quãng đường:** `{st.session_state.route_summary['distance']:.2f} km`")
        st.markdown(f"**Thời gian dự kiến:** `{st.session_state.route_summary['duration']:.0f} phút`")
        
        st.subheader("📌 Thứ tự ghé thăm tối ưu:")
        for pt in st.session_state.ordered_points:
            st.write(f"**{pt['Order']}.** {pt['Name']}")

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
    name='Google Maps (Đường phố)',
    overlay=False,
    control=True
).add_to(m)

# Layer Google Maps Vệ Tinh
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satellite',
    name='Google Maps (Vệ tinh)',
    overlay=False,
    control=True
).add_to(m)

# 1. Đánh dấu vị trí xuất phát GPS (Màu đỏ)
if st.session_state.current_loc:
    folium.Marker(
        location=st.session_state.current_loc,
        popup="<b>Vị trí xuất phát (GPS)</b>",
        tooltip="Xuất phát",
        icon=folium.Icon(color='red', icon='play', prefix='fa')
    ).add_to(m)

# 2. Đánh dấu các tập điểm được chọn theo thứ tự đã sắp xếp (Màu xanh lá có số thứ tự)
if st.session_state.ordered_points:
    for pt in st.session_state.ordered_points:
        folium.Marker(
            location=(pt['Latitude'], pt['Longitude']),
            popup=f"<b>Điểm {pt['Order']}: {pt['Name']}</b>",
            tooltip=f"Điểm {pt['Order']}: {pt['Name']}",
            icon=folium.DivIcon(
                html=f"""<div style="
                    background-color: #28a745;
                    color: white;
                    border-radius: 50%;
                    width: 28px;
                    height: 28px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-weight: bold;
                    border: 2px solid white;
                    box-shadow: 0px 2px 5px rgba(0,0,0,0.4);
                ">{pt['Order']}</div>"""
            )
        ).add_to(m)

# 3. Vẽ tuyến đường di chuyển liên tục tối ưu (Màu xanh lam)
if st.session_state.route_coords:
    folium.PolyLine(
        st.session_state.route_coords,
        color="#0066FF",
        weight=6,
        opacity=0.85,
        tooltip="Lộ trình di chuyển xe máy"
    ).add_to(m)

folium.LayerControl().add_to(m)

# Render bản đồ lên Web
st_folium(m, width="100%", height=680)
