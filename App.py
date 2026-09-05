import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from scipy.spatial.distance import cdist

st.set_page_config(layout="wide", page_title="Quản lý Tọa độ & Tạo Tuyến đường")

# 1. Nạp và xử lý dữ liệu từ file Excel
@st.cache_data
def load_data():
    df = pd.read_excel('QuanLyTĐ.xlsx', sheet_name='TĐ')
    df = df.dropna(subset=['Latitude', 'Longitude']).reset_index(drop=True)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Không thể đọc file QuanLyTĐ.xlsx. Vui lòng kiểm tra lại file! Lỗi: {e}")
    st.stop()

# 2. Bảng tính khoảng cách địa lý (Haversine - km)
def haversine_matrix(coords):
    rads = np.radians(coords)
    lats, lons = rads[:, 0], rads[:, 1]
    dlat = lats[:, None] - lats[None, :]
    dlon = lons[:, None] - lons[None, :]
    a = np.sin(dlat / 2.0)**2 + np.cos(lats[:, None]) * np.cos(lats[None, :]) * np.sin(dlon / 2.0)**2
    return 6371 * 2 * np.arcsin(np.sqrt(a))

# 3. Thuật toán tìm đường đi ngắn nhất (Nearest Neighbor TSP)
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

st.title("🗺️ Công cụ Tạo Tuyến đường Tối ưu từ QuanLyTĐ.xlsx")

if len(selected_names) < 2:
    st.warning("Vui lòng chọn ít nhất 2 đối tượng từ danh sách bên trái để tạo quãng đường.")
else:
    selected_df = df[df['Tên đối tượng'].isin(selected_names)].reset_index(drop=True)
    path_indices, total_km = solve_tsp(selected_df)
    ordered_df = selected_df.iloc[path_indices].reset_index(drop=True)

    col1, col2 = st.columns([1, 2.8])
    
    with col1:
        st.metric(label="Tổng chiều dài tuyến đường", value=f"{total_km:.2f} km")
        st.subheader("Thứ tự di chuyển:")
        
        display_df = ordered_df.copy()
        display_df.index = display_df.index + 1
        st.dataframe(
            display_df[['Tên đối tượng', 'Latitude', 'Longitude']],
            use_container_width=True
        )

    with col2:
        center_lat = ordered_df['Latitude'].mean()
        center_lon = ordered_df['Longitude'].mean()
        
        # Khởi tạo bản đồ với nguồn nền CartoDB (tránh lỗi xám nền OSM)
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=13,
            tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            attr="CARTO / OpenStreetMap"
        )

        # Bổ sung lớp bản đồ Vệ tinh Esri
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri World Imagery",
            name="Bản đồ Vệ tinh"
        ).add_to(m)

        # Cho phép đổi lớp bản đồ ở góc trên bên phải
        folium.LayerControl().add_to(m)

        # Vẽ tuyến đường kết nối
        route_coords = ordered_df[['Latitude', 'Longitude']].values.tolist()
        folium.PolyLine(route_coords, color="blue", weight=4, opacity=0.8).add_to(m)

        # Đánh dấu từng điểm số thứ tự
        for idx, row in ordered_df.iterrows():
            seq_num = idx + 1
            marker_html = f'''
                <div style="
                    font-size: 11pt; 
                    color: white; 
                    background-color: #d9534f; 
                    border: 2px solid white;
                    border-radius: 50%; 
                    width: 26px; 
                    height: 26px; 
                    text-align: center; 
                    line-height: 22px; 
                    font-weight: bold;
                    box-shadow: 1px 1px 3px rgba(0,0,0,0.5);">
                    {seq_num}
                </div>
            '''
            
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=f"<b>Thứ tự {seq_num}:</b> {row['Tên đối tượng']}",
                tooltip=f"{seq_num}. {row['Tên đối tượng']}",
                icon=folium.DivIcon(html=marker_html)
            ).add_to(m)

        st_folium(m, width=900, height=600)
