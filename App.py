import streamlit as st
import pandas as pd
import numpy as np
import folium
import requests
from streamlit_folium import st_folium

# 1. Cấu hình trang & Styling Giao diện
st.set_page_config(layout="wide", page_title="TQG - Tuyến đường", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; }
        .block-container { padding: 0rem !important; }
        
        [data-testid="stSidebarCollapseButton"] {
            background-color: #ffffff !important;
            border: 1px solid #dcdfe6 !important;
            border-radius: 4px !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
            color: #333333 !important;
            z-index: 999999 !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #f0f2f5 !important;
            border-right: 1px solid #dcdfe6 !important;
            min-width: 300px !important;
            max-width: 340px !important;
            padding-top: 1rem;
        }
        
        div.stButton > button {
            width: 100%;
            border-radius: 6px;
            font-weight: bold;
            border: none;
            padding: 10px 16px;
            margin-top: 5px;
        }
    </style>
""", unsafe_allow_html=True)

# 2. Nạp dữ liệu Excel
@st.cache_data
def load_data():
    df = pd.read_excel('QuanLyTĐ.xlsx', sheet_name='TĐ')
    df = df.dropna(subset=['Latitude', 'Longitude']).reset_index(drop=True)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"[SYSTEM ERROR]: Không thể nạp dữ liệu. Chi tiết: {e}")
    st.stop()

# 3. Thuật toán OSRM tính tuyến đường xe máy (đường bộ thực tế)
def get_osrm_route(coords_list):
    loc_str = ";".join([f"{lon},{lat}" for lat, lon in coords_list])
    url = f"http://router.project-osrm.org/route/v1/driving/{loc_str}?overview=full&geometries=geojson"
    try:
        res = requests.get(url, timeout=3)
        data = res.json()
        if data.get("code") == "Ok":
            route_geometry = data["routes"][0]["geometry"]["coordinates"]
            return [[lat, lon] for lon, lat in route_geometry]
    except Exception:
        pass
    return coords_list

# 4. Thuật toán TSP sắp xếp thứ tự các điểm dừng
def haversine_matrix(coords):
    rads = np.radians(coords)
    lats, lons = rads[:, 0], rads[:, 1]
    dlat = lats[:, None] - lats[None, :]
    dlon = lons[:, None] - lons[None, :]
    a = np.sin(dlat / 2.0)**2 + np.cos(lats[:, None]) * np.cos(lats[None, :]) * np.sin(dlon / 2.0)**2
    return 6371 * 2 * np.arcsin(np.sqrt(a))

def solve_tsp_from_start(selected_df):
    coords = selected_df[['Latitude', 'Longitude']].values
    dist_mat = haversine_matrix(coords)
    num_pts = len(coords)
    
    unvisited = set(range(1, num_pts))
    current = 0
    path = [current]
    
    while unvisited:
        next_pt = min(unvisited, key=lambda x: dist_mat[current][x])
        path.append(next_pt)
        unvisited.remove(next_pt)
        current = next_pt
        
    return path

# Khởi tạo Session States
if 'user_lat' not in st.session_state:
    st.session_state['user_lat'] = None
if 'user_lon' not in st.session_state:
    st.session_state['user_lon'] = None
if 'is_routed' not in st.session_state:
    st.session_state['is_routed'] = False

# Đọc tọa độ từ tham số URL nếu JS đã lấy xong
query_params = st.query_params
if "lat" in query_params and "lon" in query_params:
    try:
        st.session_state['user_lat'] = float(query_params["lat"])
        st.session_state['user_lon'] = float(query_params["lon"])
    except:
        pass

# 5. Thanh Menu Sidebar Bên Trái
with st.sidebar:
    st.markdown("<h3 style='color: #27ae60; font-size: 18px; margin-bottom: 2px;'>⚡ TQG - Tuyến đường</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #2ab7ca; font-size: 11px; margin-bottom: 15px;'>Make by BangNC13</p>", unsafe_allow_html=True)
    
    # Nút "📍 Tôi đang đứng" nằm trong Sidebar
    st.components.v1.html("""
        <button id="gps_btn" style="
            width: 100%;
            background-color: #ff4d4f;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px;
            font-weight: bold;
            font-size: 14px;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        ">📍 Tôi đang đứng</button>

        <script>
            document.getElementById('gps_btn').onclick = function() {
                var btn = this;
                btn.innerHTML = "⚡ Đang lấy GPS...";
                btn.style.backgroundColor = "#e63946";
                
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(function(position) {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        const url = new URL(window.parent.location.href);
                        url.searchParams.set('lat', lat);
                        url.searchParams.set('lon', lon);
                        window.parent.location.href = url.href;
                    }, function(error) {
                        alert("Vui lòng bật quyền truy cập GPS/Vị trí trên trình duyệt điện thoại.");
                        btn.innerHTML = "📍 Tôi đang đứng";
                        btn.style.backgroundColor = "#ff4d4f";
                    }, {
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 0
                    });
                } else {
                    alert("Trình duyệt không hỗ trợ Geolocation.");
                }
            };
        </script>
    """, height=50)

    if st.session_state['user_lat'] is not None:
        st.caption("✅ Đã xác định vị trí hiện tại")

    st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #dcdfe6;'>", unsafe_allow_html=True)

    # Lọc dữ liệu POP
    all_objects = df['Tên đối tượng'].tolist()
    st.markdown("**LỌC DỮ LIỆU POP**")
    selected_names = st.multiselect(
        "Lọc dữ liệu POP",
        options=all_objects,
        default=all_objects[:5] if len(all_objects) >= 5 else all_objects,
        label_visibility="collapsed"
    )

    # Đổi màu nút "Bấm" sang xanh dương khi kích hoạt
    if st.session_state['is_routed']:
        st.markdown("""
            <style>
                div.stButton > button[kind="primary"] {
                    background-color: #007bff !important;
                    color: white !important;
                    box-shadow: 0 0 10px rgba(0,123,255,0.5);
                }
            </style>
        """, unsafe_allow_html=True)
    
    btn_type = "primary" if st.session_state['is_routed'] else "secondary"
    if st.button("Bấm", type=btn_type):
        if st.session_state['user_lat'] is None:
            st.error("Vui lòng bấm '📍 Tôi đang đứng' trước!")
        else:
            st.session_state['is_routed'] = True
            st.rerun()

# 6. Render Bản đồ
selected_df = df[df['Tên đối tượng'].isin(selected_names)].reset_index(drop=True)

# Tích hợp điểm xuất phát
if st.session_state['user_lat'] is not None:
    my_loc_row = pd.DataFrame([{
        'Tên đối tượng': '📍 Vị trí hiện tại của tôi',
        'Latitude': st.session_state['user_lat'],
        'Longitude': st.session_state['user_lon']
    }])
    full_df = pd.concat([my_loc_row, selected_df], ignore_index=True)
else:
    full_df = selected_df.copy()

center_lat = full_df['Latitude'].iloc[0] if len(full_df) > 0 else 21.823
center_lon = full_df['Longitude'].iloc[0] if len(full_df) > 0 else 105.216

m = folium.Map(
    location=[center_lat, center_lon], 
    zoom_start=13,
    zoom_control=False,
    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google Maps Standard"
)

m.get_root().html.add_child(folium.Element('<script>L.control.zoom({ position: "bottomright" }).addTo(map);</script>'))

# Nếu đã bấm "Bấm" -> Vẽ đường xe máy nối các điểm
if st.session_state['is_routed'] and st.session_state['user_lat'] is not None:
    path_indices = solve_tsp_from_start(full_df)
    ordered_df = full_df.iloc[path_indices].reset_index(drop=True)

    raw_coords = ordered_df[['Latitude', 'Longitude']].values.tolist()
    osrm_route = get_osrm_route(raw_coords)

    # Đường Polyline màu xanh dương
    folium.PolyLine(
        osrm_route, 
        color="#007bff", 
        weight=6, 
        opacity=0.85
    ).add_to(m)

    for idx, row in ordered_df.iterrows():
        seq_num = idx + 1
        is_my_loc = (row['Tên đối tượng'] == '📍 Vị trí hiện tại của tôi')
        bg_color = "#e74c3c" if is_my_loc else "#007bff"
        
        marker_html = f'''
            <div style="font-family:sans-serif; font-size:10pt; color:white; background-color:{bg_color}; 
                        border:2px solid white; border-radius:50%; width:26px; height:26px; 
                        text-align:center; line-height:22px; font-weight:bold; box-shadow:0 2px 5px rgba(0,0,0,0.3);">
                {seq_num if not is_my_loc else "🛵"}
            </div>
        '''
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            tooltip=f"{seq_num}. {row['Tên đối tượng']}",
            icon=folium.DivIcon(html=marker_html)
        ).add_to(m)

# Chưa bấm "Bấm" -> Chỉ hiển thị các vị trí
else:
    for idx, row in full_df.iterrows():
        is_my_loc = (row['Tên đối tượng'] == '📍 Vị trí hiện tại của tôi')
        bg_color = "#e74c3c" if is_my_loc else "#27ae60"
        icon_str = "🛵" if is_my_loc else "📍"
        
        marker_html = f'''
            <div style="font-family:sans-serif; font-size:10pt; color:white; background-color:{bg_color}; 
                        border:2px solid white; border-radius:50%; width:26px; height:26px; 
                        text-align:center; line-height:22px; font-weight:bold; box-shadow:0 2px 5px rgba(0,0,0,0.3);">
                {icon_str}
            </div>
        '''
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            tooltip=row['Tên đối tượng'],
            icon=folium.DivIcon(html=marker_html)
        ).add_to(m)

st_folium(m, width="100%", height=850, returned_objects=[])
