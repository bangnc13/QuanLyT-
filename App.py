import streamlit as st
import pandas as pd
import numpy as np
import folium
import requests
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# 1. Cấu hình trang & Styling
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
        
        /* Custom Button Styling */
        div.stButton > button {
            width: 100%;
            border-radius: 6px;
            font-weight: bold;
            border: none;
            padding: 10px 16px;
            margin-top: 5px;
            transition: all 0.3s ease;
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

# 3. Hàm tính lộ trình đường bộ thực tế qua OSRM (Xe máy/Ô tô)
def get_osrm_route(coords_list):
    # Format: lon,lat;lon,lat...
    loc_str = ";".join([f"{lon},{lat}" for lat, lon in coords_list])
    url = f"http://router.project-osrm.org/route/v1/driving/{loc_str}?overview=full&geometries=geojson"
    
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if data.get("code") == "Ok":
            route_geometry = data["routes"][0]["geometry"]["coordinates"]
            # Chuyển lon,lat sang lat,lon cho Folium
            return [[lat, lon] for lon, lat in route_geometry]
    except Exception:
        pass
    return coords_list # Fallback nếu nghẽn mạng

# 4. Thuật toán TSP xuất phát từ điểm 0
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

# Khởi tạo Session State
if 'my_location' not in st.session_state:
    st.session_state['my_location'] = None
if 'is_routed' not in st.session_state:
    st.session_state['is_routed'] = False

# 5. Menu Sidebar
with st.sidebar:
    st.markdown("<h3 style='color: #27ae60; font-size: 18px; margin-bottom: 2px;'>⚡ TQG - Tuyến đường</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #2ab7ca; font-size: 11px; margin-bottom: 15px;'>Make by BangNC13</p>", unsafe_allow_html=True)
    
    # Nút 1: Tôi đang đứng
    if st.button("📍 Tôi đang đứng", type="primary"):
        loc = get_geolocation()
        if loc and 'coords' in loc:
            st.session_state['my_location'] = {
                'Tên đối tượng': '📍 Vị trí hiện tại của tôi',
                'Latitude': loc['coords']['latitude'],
                'Longitude': loc['coords']['longitude']
            }
            st.session_state['is_routed'] = False # Reset lộ trình khi lấy lại GPS
            st.success("Đã xác định vị trí hiện tại!")
        else:
            st.warning("Vui lòng cho phép truy cập GPS trên thiết bị.")

    st.markdown("<hr style='margin: 10px 0; border: none; border-top: 1px solid #dcdfe6;'>", unsafe_allow_html=True)

    all_objects = df['Tên đối tượng'].tolist()
    st.markdown("**LỌC DỮ LIỆU POP**")
    selected_names = st.multiselect(
        "Lọc dữ liệu POP",
        options=all_objects,
        default=all_objects[:5] if len(all_objects) >= 5 else all_objects,
        label_visibility="collapsed"
    )

    # Đổi màu nút "Bấm" sang Xanh dương khi đã click
    btn_type = "primary" if st.session_state['is_routed'] else "secondary"
    
    # CSS tùy biến màu xanh dương cho nút "Bấm" khi kích hoạt
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
    
    if st.button("Bấm", type=btn_type):
        if not st.session_state['my_location']:
            st.error("Vui lòng bấm '📍 Tôi đang đứng' trước để lấy mốc xuất phát!")
        else:
            st.session_state['is_routed'] = True
            st.rerun()

# 6. Render Map
selected_df = df[df['Tên đối tượng'].isin(selected_names)].reset_index(drop=True)

# Khởi tạo danh sách điểm
if st.session_state['my_location']:
    start_row = pd.DataFrame([st.session_state['my_location']])
    full_df = pd.concat([start_row, selected_df], ignore_index=True)
else:
    full_df = selected_df.copy()

if len(full_df) > 0:
    center_lat = full_df['Latitude'].iloc[0]
    center_lon = full_df['Longitude'].iloc[0]
else:
    center_lat, center_lon = 21.823, 105.216

m = folium.Map(
    location=[center_lat, center_lon], 
    zoom_start=13,
    zoom_control=False,
    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google Maps Standard"
)

# Thêm nút Zoom góc dưới phải
m.get_root().html.add_child(folium.Element('<script>L.control.zoom({ position: "bottomright" }).addTo(map);</script>'))

# TRƯỜNG HỢP 1: ĐÃ BẤM NÚT "BẤM" (Tối ưu tuyến đường xe máy)
if st.session_state['is_routed'] and st.session_state['my_location']:
    path_indices = solve_tsp_from_start(full_df)
    ordered_df = full_df.iloc[path_indices].reset_index(drop=True)

    # Lấy tọa độ đường bộ giao thông thực tế cho xe máy
    raw_coords = ordered_df[['Latitude', 'Longitude']].values.tolist()
    osrm_route = get_osrm_route(raw_coords)

    # Vẽ đường di chuyển xanh dương nổi bật
    folium.PolyLine(
        osrm_route, 
        color="#007bff", 
        weight=6, 
        opacity=0.85,
        tooltip="Lộ trình di chuyển xe máy tối ưu"
    ).add_to(m)

    # Hiển thị Marker thứ tự lộ trình (1, 2, 3...)
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

# TRƯỜNG HỢP 2: CHƯA BẤM "BẤM" (Chỉ hiển thị các điểm và vị trí đứng)
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
