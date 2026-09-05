import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from folium.plugins import LocateControl
from scipy.spatial.distance import cdist
import urllib.parse

st.set_page_config(layout="wide", page_title="Quản lý Tọa độ & Chỉ đường Google Maps")

# 1. Nạp và xử lý dữ liệu từ file Excel
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

# 2. Tính khoảng cách địa lý (Haversine - km)
def haversine_matrix(coords):
    rads = np.radians(coords)
    lats, lons = rads[:, 0], rads[:, 1]
    dlat = lats[:, None] - lats[None, :]
    dlon = lons[:, None] - lons[None, :]
    a = np.sin(dlat / 2.0)**2 + np.cos(lats[:, None]) * np.cos(lats[None, :]) * np.sin(dlon / 2.0)**2
    return 6371 * 2 * np.arcsin(np.sqrt(a))

# 3. Thuật toán tối ưu hóa tuyến đường (TSP)
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

# 4. Giao diện Sidebar
st.sidebar.title("Cấu hình chọn điểm")
all_objects = df['Tên đối tượng'].tolist()

selected_names = st.sidebar.multiselect(
    "Chọn các đối tượng cần đi qua (khoảng 10 điểm):",
    options=all_objects,
    default=all_objects[:10] if len(all_objects) >= 10 else all_objects[:2]
)

st.title("🗺️ Công cụ Tối ưu Route & Chỉ đường Google Maps")

if len(selected_names) < 2:
    st.warning("Vui lòng chọn ít nhất 2 đối tượng từ danh sách bên trái.")
else:
    selected_df = df[df['Tên đối tượng'].isin(selected_names)].reset_index(drop=True)
    path_indices, total_km = solve_tsp(selected_df)
    ordered_df = selected_df.iloc[path_indices].reset_index(drop=True)

    # Tạo URL Google Maps chỉ đường qua toàn bộ lộ trình
    origin = f"{ordered_df.iloc[0]['Latitude']},{ordered_df.iloc[0]['Longitude']}"
    destination = f"{ordered_df.iloc[-1]['Latitude']},{ordered_df.iloc[-1]['Longitude']}"
    
    waypoints = "|".join([f"{row['Latitude']},{row['Longitude']}" for _, row in ordered_df.iloc[1:-1].iterrows()])
    
    gmaps_full_route_url = f"https://www.google.com/maps/dir/?api=1&origin={origin}&destination={destination}"
    if waypoints:
        gmaps_full_route_url += f"&waypoints={urllib.parse.quote(waypoints)}"

    col1, col2 = st.columns([1, 2.8])
    
    with col1:
        st.metric(label="Tổng chiều dài tuyến đường", value=f"{total_km:.2f} km")
        
        # Nút bấm mở toàn bộ tuyến đường trên ứng dụng Google Maps
        st.link_button(
            "🚀 Mở chỉ đường toàn bộ lộ trình trên Google Maps", 
            gmaps_full_route_url, 
            type="primary",
            use_container_width=True
        )
        
        st.subheader("Thứ tự di chuyển:")
        for idx, row in ordered_df.iterrows():
            seq_num = idx + 1
            # Link Google Maps từng điểm lẻ từ vị trí hiện tại của thiết bị
            point_url = f"https://www.google.com/maps/dir/?api=1&destination={row['Latitude']},{row['Longitude']}"
            
            st.markdown(
                f"**{seq_num}. {row['Tên đối tượng']}**  \n"
                f"📍 `Lat: {row['Latitude']:.5f}, Lon: {row['Longitude']:.5f}`  \n"
                f"[👉 Chỉ đường đến điểm này trên Google Maps]({point_url})"
            )
            st.divider()

    with col2:
        center_lat = ordered_df['Latitude'].mean()
        center_lon = ordered_df['Longitude'].mean()
        
        # 1. Khởi tạo bản đồ với Google Maps làm nền
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=13,
            tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
            attr="Google Maps"
        )

        # 2. Thêm tùy chọn Google Maps Vệ tinh (Satellite) & Google Maps Lai (Hybrid)
        folium.TileLayer(
            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google Maps Satellite",
            name="Google Vệ tinh"
        ).add_to(m)

        folium.TileLayer(
            tiles="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
            attr="Google Maps Hybrid",
            name="Google Hybrid (Vệ tinh + Tên đường)"
        ).add_to(m)

        # 3. Tích hợp nút định vị GPS thiết bị/điện thoại hiện tại
        LocateControl(
            auto_start=False,
            flyTo=True,
            keepCurrentZoomLevel=True,
            strings={"title": "Định vị vị trí hiện tại của bạn"}
        ).add_to(m)

        folium.LayerControl().add_to(m)

        # 4. Vẽ tuyến đường kết nối
        route_coords = ordered_df[['Latitude', 'Longitude']].values.tolist()
        folium.PolyLine(route_coords, color="#1A73E8", weight=5, opacity=0.9).add_to(m)

        # 5. Đánh dấu các mốc điểm kèm nút bấm Chỉ đường trực tiếp
        for idx, row in ordered_df.iterrows():
            seq_num = idx + 1
            direct_gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={row['Latitude']},{row['Longitude']}"
            
            popup_html = f"""
            <div style="font-family: Arial; min-width: 160px;">
                <h4 style="margin: 0 0 5px 0;">{seq_num}. {row['Tên đối tượng']}</h4>
                <p style="margin: 0 0 10px 0; font-size: 12px; color: #555;">
                   <b>Tọa độ:</b> {row['Latitude']:.5f}, {row['Longitude']:.5f}
                </p>
                <a href="{direct_gmaps_url}" target="_blank" 
                   style="
                       display: inline-block;
                       background-color: #1a73e8;
                       color: white;
                       padding: 6px 12px;
                       text-decoration: none;
                       border-radius: 4px;
                       font-size: 12px;
                       font-weight: bold;
                   ">
                   🧭 Mở Google Maps Chỉ đường
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
                    box-shadow: 2px 2px 4px rgba(0,0,0,0.4);">
                    {seq_num}
                </div>
            '''
            
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"{seq_num}. {row['Tên đối tượng']} (Click để chỉ đường)",
                icon=folium.DivIcon(html=marker_icon_html)
            ).add_to(m)

        st_folium(m, width="100%", height=600)
