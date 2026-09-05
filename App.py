import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

# 1. Cấu hình trang & Sidebar mở mặc định
st.set_page_config(layout="wide", page_title="TQG - Tuyến đường", initial_sidebar_state="expanded")

# 2. Styling CSS Giao diện Clean Light
st.markdown("""
    <style>
        .stApp {
            background-color: #f8f9fa;
        }
        .block-container {
            padding: 0rem !important;
        }
        
        /* Đảm bảo nút đóng/mở Sidebar hiển thị rõ nét */
        [data-testid="stSidebarCollapseButton"] {
            background-color: #ffffff !important;
            border: 1px solid #dcdfe6 !important;
            border-radius: 4px !important;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
            color: #333333 !important;
            z-index: 999999 !important;
        }

        /* Định dạng Sidebar bên trái */
        section[data-testid="stSidebar"] {
            background-color: #f0f2f5 !important;
            border-right: 1px solid #dcdfe6 !important;
            min-width: 300px !important;
            max-width: 340px !important;
            padding-top: 1rem;
        }
        
        /* Styling Nút Bấm */
        div.stButton > button {
            width: 100%;
            background-color: #27ae60;
            color: white;
            border-radius: 6px;
            font-weight: bold;
            border: none;
            padding: 10px 16px;
            margin-top: 10px;
        }
        div.stButton > button:hover {
            background-color: #219150;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# 3. Nạp dữ liệu Excel
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

# 4. Thuật toán Haversine & TSP
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
    total_dist = 0.0
    
    while unvisited:
        next_pt = min(unvisited, key=lambda x: dist_mat[current][x])
        total_dist += dist_mat[current][next_pt]
        path.append(next_pt)
        unvisited.remove(next_pt)
        current = next_pt
        
    return path, total_dist

# 5. Thanh Menu Sidebar đã tối giản & Đổi tên
with st.sidebar:
    st.markdown("<h3 style='color: #27ae60; font-size: 18px; margin-bottom: 2px;'>⚡ TQG - Tuyến đường</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #2ab7ca; font-size: 11px; margin-bottom: 20px;'>Make by BangNC13</p>", unsafe_allow_html=True)
    
    all_objects = df['Tên đối tượng'].tolist()
    
    # Chỉ giữ lại Mục Lọc dữ liệu POP
    st.markdown("**LỌC DỮ LIỆU POP**")
    selected_names = st.multiselect(
        "Lọc dữ liệu POP",
        options=all_objects,
        default=all_objects[:10] if len(all_objects) >= 10 else all_objects[:2],
        label_visibility="collapsed"
    )
    
    # Thêm nút Bấm
    btn_click = st.button("Bấm")

# 6. Hiển thị Bản đồ bên phải
if len(selected_names) < 2:
    st.info("Vui lòng chọn từ 2 điểm trở lên trong Menu bên trái để hiển thị bản đồ.")
else:
    selected_df = df[df['Tên đối tượng'].isin(selected_names)].reset_index(drop=True)
    path_indices, total_km = solve_tsp(selected_df)
    ordered_df = selected_df.iloc[path_indices].reset_index(drop=True)

    center_lat = ordered_df['Latitude'].mean()
    center_lon = ordered_df['Longitude'].mean()

    # Tạo bản đồ Google Maps Standard
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=12,
        zoom_control=False,
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google Maps Standard"
    )

    # Đưa nút Zoom (+ -) xuống góc dưới bên phải
    m.get_root().html.add_child(folium.Element('''
        <script>
            L.control.zoom({ position: 'bottomright' }).addTo(map);
        </script>
    '''))

    # Nút bấm góc trên trái bản đồ
    first_target_lat = ordered_df.iloc[0]['Latitude']
    first_target_lon = ordered_df.iloc[0]['Longitude']
    direct_gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={first_target_lat},{first_target_lon}"

    map_overlay_buttons = f'''
    <div style="
        position: fixed; 
        top: 12px; 
        left: 65px; 
        z-index: 9999; 
        display: flex;
        flex-direction: column;
        gap: 6px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    ">
        <button onclick="locateUser()" style="
            background: #ffffff;
            color: #333333;
            border: 1px solid #cccccc;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 5px;
        ">
            <span style="color: #ff4d4f;">🎯</span> GPS của tôi
        </button>
        
        <a href="{direct_gmaps_url}" target="_blank" style="
            background: #00b894;
            color: #ffffff;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            text-decoration: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 5px;
        ">
            🛣️ Chỉ đường tới điểm
        </a>
    </div>

    <script>
        function locateUser() {{
            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(function(position) {{
                    var userLat = position.coords.latitude;
                    var userLon = position.coords.longitude;
                    map.setView([userLat, userLon], 15);
                    L.circleMarker([userLat, userLon], {{
                        radius: 8,
                        fillColor: "#00b894",
                        color: "#ffffff",
                        weight: 2,
                        fillOpacity: 0.9
                    }}).addTo(map).bindPopup("📍 Vị trí hiện tại của bạn").openPopup();
                }}, function() {{
                    alert("Không thể lấy dữ liệu GPS.");
                }});
            }}
        }}
    </script>
    '''
    m.get_root().html.add_child(folium.Element(map_overlay_buttons))

    # Vẽ đường tuyến nối các điểm
    route_coords = ordered_df[['Latitude', 'Longitude']].values.tolist()
    folium.PolyLine(
        route_coords, 
        color="#3867d6", 
        weight=5, 
        opacity=0.8
    ).add_to(m)

    # Đặt Marker các điểm mốc tròn màu xanh
    for idx, row in ordered_df.iterrows():
        seq_num = idx + 1
        marker_icon_html = f'''
            <div style="
                font-family: sans-serif;
                font-size: 10pt; 
                color: #ffffff; 
                background-color: #3867d6; 
                border: 2px solid #ffffff;
                border-radius: 50%; 
                width: 24px; 
                height: 24px; 
                text-align: center; 
                line-height: 20px; 
                font-weight: bold;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
                {seq_num}
            </div>
        '''
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            tooltip=f"{seq_num}. {row['Tên đối tượng']}",
            icon=folium.DivIcon(html=marker_icon_html)
        ).add_to(m)

    # Render bản đồ tràn khung
    st_folium(m, width="100%", height=850, returned_objects=[])
