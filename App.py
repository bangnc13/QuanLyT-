import streamlit as st
import pandas as pd
import numpy as np
import folium
import requests
from streamlit_folium import st_folium

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

# 3. Thuật toán OSRM tính tuyến đường xe máy
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

# 4. Thuật toán TSP sắp xếp thứ tự điểm
def haversine_matrix(coords):
    rads = np.radians(coords)
    lats, lons = rads[:, 0], rads[:, 1]
    dlat = lats[:, None] - lats[None, :]
    dlon = lons[:, None] - lons[None, :]
    a = np.sin(dlat / 2.0)**2 + np.cos(lats[:, None]) * np.cos(lats[None, :]) * np.sin(dlon / 2.0)**2
    return 6371 * 2 * np.arcsin(np.sqrt(a))

def solve_tsp(selected_df):
    coords = selected_df[['Latitude', 'Longitude']].values
    dist_mat = haversine_matrix(coords)
    num_pts = len(coords)
    
    unvisited = set(range(num_pts))
    current = 0
    path = [current]
    unvisited.remove(current)
    
    while unvisited:
        next_pt = min(unvisited, key=lambda x: dist_mat[current][x])
        path.append(next_pt)
        unvisited.remove(next_pt)
        current = next_pt
        
    return path

# Session State
if 'is_routed' not in st.session_state:
    st.session_state['is_routed'] = False

# 5. Menu Sidebar Tối ưu
with st.sidebar:
    st.markdown("<h3 style='color: #27ae60; font-size: 18px; margin-bottom: 2px;'>⚡ TQG - Tuyến đường</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #2ab7ca; font-size: 11px; margin-bottom: 15px;'>Make by BangNC13</p>", unsafe_allow_html=True)

    all_objects = df['Tên đối tượng'].tolist()
    st.markdown("**LỌC DỮ LIỆU POP**")
    selected_names = st.multiselect(
        "Lọc dữ liệu POP",
        options=all_objects,
        default=all_objects[:5] if len(all_objects) >= 5 else all_objects,
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Nút Bấm Xanh dương khi kích hoạt
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
        st.session_state['is_routed'] = not st.session_state['is_routed']
        st.rerun()

# 6. Hiển thị Bản đồ & Tích hợp Nút Định vị Tốc độ cao
selected_df = df[df['Tên đối tượng'].isin(selected_names)].reset_index(drop=True)

center_lat = selected_df['Latitude'].mean() if len(selected_df) > 0 else 21.823
center_lon = selected_df['Longitude'].mean() if len(selected_df) > 0 else 105.216

m = folium.Map(
    location=[center_lat, center_lon], 
    zoom_start=13,
    zoom_control=False,
    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    attr="Google Maps Standard"
)

# Nút "📍 Tôi đang đứng" siêu nhẹ đặt nổi trên góc trái bản đồ
fast_gps_button_html = '''
<div style="position: fixed; top: 12px; left: 60px; z-index: 9999;">
    <button onclick="locateUserFast()" id="btn-fast-gps" style="
        background: #ff4d4f;
        color: white;
        border: none;
        padding: 8px 14px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
        display: flex;
        align-items: center;
        gap: 6px;
    ">
        📍 Tôi đang đứng
    </button>
</div>

<script>
    var userMarker = null;
    function locateUserFast() {
        var btn = document.getElementById('btn-fast-gps');
        btn.innerHTML = "⚡ Đang định vị...";
        
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                var lat = position.coords.latitude;
                var lon = position.coords.longitude;
                
                if (userMarker) {
                    map.removeLayer(userMarker);
                }
                
                // Marker icon vị trí xe máy xuất phát
                var gpsIcon = L.divIcon({
                    className: 'custom-div-icon',
                    html: "<div style='background-color:#e74c3c; color:white; border:2px solid white; border-radius:50%; width:30px; height:30px; text-align:center; line-height:26px; font-size:14px; font-weight:bold; box-shadow:0 2px 6px rgba(0,0,0,0.4);'>🛵</div>",
                    iconSize: [30, 30],
                    iconAnchor: [15, 15]
                });

                userMarker = L.marker([lat, lon], {icon: gpsIcon}).addTo(map)
                    .bindPopup("<b>Vị trí hiện tại của bạn</b>").openPopup();
                
                map.setView([lat, lon], 15);
                btn.innerHTML = "✅ Đã định vị";
                btn.style.background = "#27ae60";
            }, function(error) {
                alert("Không thể lấy định vị. Vui lòng bật GPS trên điện thoại.");
                btn.innerHTML = "📍 Tôi đang đứng";
            }, {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            });
        }
    }
</script>
'''
m.get_root().html.add_child(folium.Element(fast_gps_button_html))
m.get_root().html.add_child(folium.Element('<script>L.control.zoom({ position: "bottomright" }).addTo(map);</script>'))

# Render lộ trình khi bấm nút "Bấm"
if st.session_state['is_routed'] and len(selected_df) > 1:
    path_indices = solve_tsp(selected_df)
    ordered_df = selected_df.iloc[path_indices].reset_index(drop=True)

    raw_coords = ordered_df[['Latitude', 'Longitude']].values.tolist()
    osrm_route = get_osrm_route(raw_coords)

    folium.PolyLine(
        osrm_route, 
        color="#007bff", 
        weight=6, 
        opacity=0.85
    ).add_to(m)

    for idx, row in ordered_df.iterrows():
        seq_num = idx + 1
        marker_html = f'''
            <div style="font-family:sans-serif; font-size:10pt; color:white; background-color:#007bff; 
                        border:2px solid white; border-radius:50%; width:26px; height:26px; 
                        text-align:center; line-height:22px; font-weight:bold; box-shadow:0 2px 5px rgba(0,0,0,0.3);">
                {seq_num}
            </div>
        '''
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            tooltip=f"{seq_num}. {row['Tên đối tượng']}",
            icon=folium.DivIcon(html=marker_html)
        ).add_to(m)
else:
    for idx, row in selected_df.iterrows():
        marker_html = '''
            <div style="font-family:sans-serif; font-size:10pt; color:white; background-color:#27ae60; 
                        border:2px solid white; border-radius:50%; width:26px; height:26px; 
                        text-align:center; line-height:22px; font-weight:bold; box-shadow:0 2px 5px rgba(0,0,0,0.3);">
                📍
            </div>
        '''
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            tooltip=row['Tên đối tượng'],
            icon=folium.DivIcon(html=marker_html)
        ).add_to(m)

st_folium(m, width="100%", height=850, returned_objects=[])
