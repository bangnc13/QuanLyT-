import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl
from scipy.spatial.distance import cdist
import urllib.parse

# 1. Cấu hình trang full màn hình
st.set_page_config(layout="wide", page_title="Quản lý Tọa độ & Chỉ đường Google Maps", initial_sidebar_state="collapsed")

# CSS tùy chỉnh để tối ưu hóa không gian hiển thị tràn viền
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; padding-bottom: 0rem; padding-left: 1rem; padding-right: 1rem; }
        div[data-testid="stSidebarCollapseButton"] { background-color: #1a73e8; color: white; }
    </style>
""", unsafe_allow_html=True)

# 2. Nạp và xử lý dữ liệu từ file Excel
@st.cache_data
def load_data():
    df = pd.read_excel('QuanLyTĐ.xlsx', sheet_name='TĐ')
    df = df.dropna(subset=['Latitude', 'Longitude']).reset_index(drop=True)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Không thể đọc file QuanLyTĐ.xlsx. Lỗi: {e}")
    st.stop()

# 3. Tính khoảng cách địa lý (Haversine - km)
def haversine_matrix(coords):
    rads = np.radians(coords)
    lats, lons = rads[:, 0], rads[:, 1]
    dlat = lats[:, None] - lats[None, :]
    dlon = lons[:, None] - lons[None, :]
    a = np.sin(dlat / 2.0)**2 + np.cos(lats[:, None]) * np.cos(lats[None, :]) * np.sin(dlon / 2.0)**2
    return 6371 * 2 * np.arcsin(np.sqrt(a))

# 4. Thuật toán tối ưu hóa tuyến đường (TSP)
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

# 5. Sidebar điều hướng
st.sidebar.title("⚙️ Thống kê & Cấu hình")
all_objects = df['Tên đối tượng'].tolist()

selected_names = st.sidebar.multiselect(
    "Chọn danh sách đối tượng (khoảng 10 điểm):",
    options=all_objects,
    default=all_objects[:10] if len(all_objects) >= 10 else all_objects[:2]
)

if len(selected_names) < 2:
    st.warning("Vui lòng chọn ít nhất 2 đối tượng từ Sidebar bên trái.")
else:
    selected_df = df[df['Tên đối tượng'].isin(selected_names)].reset_index(drop=True)
    path_indices, total_km = solve_tsp(selected_df)
    ordered_df = selected_df.iloc[path_indices].reset_index(drop=True)

    # Hiển thị thông số trên Sidebar
    st.sidebar.metric(label="Tổng chiều dài lộ trình", value=f"{total_km:.2f} km")
    
    # URL Google Maps lộ trình tổng
    origin = f"{ordered_df.iloc[0]['Latitude']},{ordered_df.iloc[0]['Longitude']}"
    destination = f"{ordered_df.iloc[-1]['Latitude']},{ordered_df.iloc[-1]['Longitude']}"
    waypoints = "|".join([f"{row['Latitude']},{row['Longitude']}" for _, row in ordered_df.iloc[1:-1].iterrows()])
    gmaps_full_route_url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}"
    if waypoints:
        gmaps_full_route_url += f"&waypoints={urllib.parse.quote(waypoints)}"

    st.sidebar.link_button(
        "🚀 Mở lộ trình trên Google Maps App", 
        gmaps_full_route_url, 
        type="primary",
        use_container_width=True
    )

    st.sidebar.subheader("Thứ tự di chuyển")
    for idx, row in ordered_df.iterrows():
        seq_num = idx + 1
        point_url = f"https://www.google.com/maps/dir/?api=1&destination={row['Latitude']},{row['Longitude']}"
        st.sidebar.markdown(f"**{seq_num}. {row['Tên đối tượng']}**  \n[🧭 Chỉ đường Google Maps]({point_url})")

    # 6. Khu vực Bản đồ Full màn hình
    center_lat = ordered_df['Latitude'].mean()
    center_lon = ordered_df['Longitude'].mean()

    # Khởi tạo bản đồ với Google Maps làm nền mặc định
    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=13,
        tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google Maps"
    )

    # Thêm lớp bản đồ Vệ tinh & Hybrid
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        attr="Google Maps Hybrid",
        name="Google Vệ tinh"
    ).add_to(m)

    # Nút Định vị GPS thiết bị đẹp mắt
    LocateControl(
        auto_start=False,
        flyTo=True,
        keepCurrentZoomLevel=True,
        strings={"title": "Vị trí GPS của bạn"},
        icon="fa-location-arrow",
        icon_element='<span class="fa fa-location-arrow" style="color: #1a73e8; font-size: 16px;"></span>'
    ).add_to(m)

    # Tính năng chỉ đường giao thông trực tiếp trên Map (Routing Machine)
    routing_script = """
    <link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css" />
    <script src="https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.js"></script>
    """
    m.get_root().header.add_child(folium.Element(routing_script))

    # Bảng điều khiển chuyển đổi lớp bản đồ
    folium.LayerControl().add_to(m)

    # Vẽ đường thẳng kết nối lộ trình
    route_coords = ordered_df[['Latitude', 'Longitude']].values.tolist()
    folium.PolyLine(route_coords, color="#1A73E8", weight=5, opacity=0.8, dash_array='8, 8').add_to(m)

    # Tạo Marker các mốc điểm
    for idx, row in ordered_df.iterrows():
        seq_num = idx + 1
        direct_gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={row['Latitude']},{row['Longitude']}"
        
        popup_html = f"""
        <div style="font-family: Arial; min-width: 180px;">
            <h4 style="margin: 0 0 5px 0; color: #1a73e8;">{seq_num}. {row['Tên đối tượng']}</h4>
            <p style="margin: 0 0 8px 0; font-size: 12px; color: #555;">
               <b>Tọa độ:</b> {row['Latitude']:.5f}, {row['Longitude']:.5f}
            </p>
            <a href="{direct_gmaps_url}" target="_blank" 
               style="
                   display: block;
                   text-align: center;
                   background-color: #1a73e8;
                   color: white;
                   padding: 6px 10px;
                   text-decoration: none;
                   border-radius: 4px;
                   font-size: 12px;
                   font-weight: bold;
               ">
               🧭 Chỉ đường bằng App Google Maps
            </a>
        </div>
        """
        
        marker_icon_html = f'''
            <div style="
                font-size: 11pt; 
                color: white; 
                background-color: #EA4335; 
                border: 2px solid white;
                border-radius: 50%; 
                width: 28px; 
                height: 28px; 
                text-align: center; 
                line-height: 24px; 
                font-weight: bold;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.4);">
                {seq_num}
            </div>
        '''
        
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{seq_num}. {row['Tên đối tượng']}",
            icon=folium.DivIcon(html=marker_icon_html)
        ).add_to(m)

    # Hiển thị Map full màn hình
    st_folium(m, width="100%", height=780, returned_objects=[])
