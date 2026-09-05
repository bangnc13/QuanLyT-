import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl
from scipy.spatial.distance import cdist
import urllib.parse

# 1. Cấu hình trang full view & Dark Theme Robotic
st.set_page_config(layout="wide", page_title="Robotic Route HUD", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        /* Dark Theme Style */
        .stApp {
            background-color: #0d1117;
            color: #58a6ff;
            font-family: 'Courier New', Courier, monospace;
        }
        .block-container {
            padding: 0.5rem 0.5rem 0rem 0.5rem !important;
        }
        header {visibility: hidden;}
        
        /* Tùy chỉnh Sidebar phong cách Robotic */
        section[data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #30363d;
        }
        section[data-testid="stSidebar"] * {
            color: #c9d1d9 !important;
            font-family: 'Courier New', Courier, monospace;
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

# 3. Thuật toán Haversine & TSP
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

# 4. Thanh Menu điều khiển chọn điểm
st.sidebar.title("⚙️ CONTROL PANEL")
all_objects = df['Tên đối tượng'].tolist()

selected_names = st.sidebar.multiselect(
    "SELECT NODES (Tối thiểu 2 điểm):",
    options=all_objects,
    default=all_objects[:10] if len(all_objects) >= 10 else all_objects[:2]
)

if len(selected_names) < 2:
    st.warning("[WARNING]: Vui lòng chọn ít nhất 2 đối tượng trên Menu bên cạnh.")
else:
    selected_df = df[df['Tên đối tượng'].isin(selected_names)].reset_index(drop=True)
    path_indices, total_km = solve_tsp(selected_df)
    ordered_df = selected_df.iloc[path_indices].reset_index(drop=True)

    # 5. Tạo URL Google Maps
    origin = f"{ordered_df.iloc[0]['Latitude']},{ordered_df.iloc[0]['Longitude']}"
    destination = f"{ordered_df.iloc[-1]['Latitude']},{ordered_df.iloc[-1]['Longitude']}"
    waypoints = "|".join([f"{row['Latitude']},{row['Longitude']}" for _, row in ordered_df.iloc[1:-1].iterrows()])
    gmaps_full_route_url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}"
    if waypoints:
        gmaps_full_route_url += f"&waypoints={urllib.parse.quote(waypoints)}"

    # 6. Khởi tạo Bản đồ Google Maps Hybrid
    center_lat = ordered_df['Latitude'].mean()
    center_lon = ordered_df['Longitude'].mean()

    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=13,
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Maps Hybrid"
    )

    # Nút Định vị GPS Cyberpunk
    LocateControl(
        auto_start=False,
        flyTo=True,
        keepCurrentZoomLevel=True,
        strings={"title": "TARGET GPS LOCK"},
        icon="fa-crosshairs",
        icon_element='<span class="fa fa-crosshairs" style="color: #00ffcc; font-size: 18px;"></span>'
    ).add_to(m)

    # 7. Bảng điều khiển HUD trên màn hình Bản đồ
    hud_html = f'''
    <div style="
        position: fixed; 
        top: 15px; 
        left: 60px; 
        z-index: 9999; 
        background: rgba(13, 17, 23, 0.9);
        border: 1px solid #30363d;
        border-left: 4px solid #00ffcc;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.2);
        border-radius: 4px;
        padding: 10px 15px;
        color: #e6edf3;
        font-family: monospace;
    ">
        <div style="font-size: 11px; color: #8b949e; letter-spacing: 1px;">SYS.ROUTE_NAV // ACTIVE</div>
        <div style="font-size: 18px; font-weight: bold; color: #00ffcc; margin: 2px 0 8px 0;">
            DIST: {total_km:.2f} KM <span style="font-size:12px; color:#8b949e;">({len(ordered_df)} NODES)</span>
        </div>
        <a href="{gmaps_full_route_url}" target="_blank" style="
            display: inline-block;
            background: linear-gradient(90deg, #1f6beb, #238636);
            color: #ffffff;
            padding: 6px 12px;
            text-decoration: none;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
            box-shadow: 0 0 8px rgba(35, 134, 54, 0.4);
        ">
            ⚡ OPEN FULL ROUTE (GMAPS)
        </a>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(hud_html))

    # 8. Vẽ đường nối Laser Neon
    route_coords = ordered_df[['Latitude', 'Longitude']].values.tolist()
    folium.PolyLine(
        route_coords, 
        color="#00ffcc", 
        weight=4, 
        opacity=0.9, 
        dash_array='6, 6'
    ).add_to(m)

    # 9. Marker điểm mốc Robotic HUD
    for idx, row in ordered_df.iterrows():
        seq_num = idx + 1
        direct_gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={row['Latitude']},{row['Longitude']}"
        
        popup_html = f"""
        <div style="
            font-family: monospace; 
            background-color: #0d1117; 
            color: #c9d1d9; 
            padding: 10px; 
            border-radius: 4px;
            border: 1px solid #30363d;
            min-width: 180px;
        ">
            <div style="font-size: 10px; color: #8b949e;">NODE #{seq_num:02d}</div>
            <div style="font-size: 14px; font-weight: bold; color: #58a6ff; margin-bottom: 5px;">
                {row['Tên đối tượng']}
            </div>
            <div style="font-size: 11px; color: #8b949e; margin-bottom: 10px;">
                LAT: {row['Latitude']:.5f}<br>LON: {row['Longitude']:.5f}
            </div>
            <a href="{direct_gmaps_url}" target="_blank" style="
                display: block;
                text-align: center;
                background-color: #238636;
                color: #ffffff;
                padding: 6px 8px;
                text-decoration: none;
                border-radius: 3px;
                font-size: 11px;
                font-weight: bold;
            ">
                🧭 NAVIGATE TO NODE
            </a>
        </div>
        """
        
        marker_icon_html = f'''
            <div style="
                font-family: monospace;
                font-size: 11pt; 
                color: #0d1117; 
                background-color: #00ffcc; 
                border: 2px solid #ffffff;
                border-radius: 3px; 
                width: 26px; 
                height: 26px; 
                text-align: center; 
                line-height: 22px; 
                font-weight: bold;
                box-shadow: 0 0 10px rgba(0, 255, 204, 0.8);">
                {seq_num}
            </div>
        '''
        
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"NODE #{seq_num:02d}: {row['Tên đối tượng']}",
            icon=folium.DivIcon(html=marker_icon_html)
        ).add_to(m)

    # Hiển thị bản đồ
    st_folium(m, width="100%", height=850, returned_objects=[])
