import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import urllib.parse

# 1. Cấu hình trang & CSS Giao diện Clean Light
st.set_page_config(layout="wide", page_title="TQG - XÁC ĐỊNH VỊ TRÍ DỨT CÁP", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        /* Base App Styling */
        .stApp {
            background-color: #f8f9fa;
            color: #212529;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        .block-container {
            padding: 0.5rem 0.5rem 0rem 0.5rem !important;
        }
        header {visibility: hidden;}

        /* Nút toggle Sidebar mặc định của Streamlit */
        button[data-testid="baseButton-header"] {
            background-color: #ffffff !important;
            border: 1px solid #dcdfe6 !important;
            border-radius: 6px !important;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
            position: fixed !important;
            top: 10px !important;
            left: 10px !important;
            z-index: 999999 !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #f4f6f8;
            border-right: 1px solid #e1e4e8;
            padding-top: 1rem;
        }

        .card-title {
            font-size: 11px;
            font-weight: 700;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }

        /* Nút bấm Custom */
        .btn-danger {
            width: 100%;
            background-color: #ff4d4f;
            color: white;
            border: none;
            padding: 8px;
            border-radius: 4px;
            font-weight: 600;
            cursor: pointer;
        }

        .btn-secondary {
            width: 100%;
            background-color: #e0e0e0;
            color: #333;
            border: none;
            padding: 8px;
            border-radius: 4px;
            font-weight: 600;
            cursor: pointer;
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

# 4. Thanh Menu bên cạnh (Sidebar) Ban đầu
with st.sidebar:
    st.markdown("""
        <div style="margin-bottom: 12px;">
            <div style="color: #27ae60; font-size: 16px; font-weight: bold;">⚡ TQG-XÁC ĐỊNH VỊ TRÍ DỨT CÁP</div>
            <div style="color: #2ab7ca; font-size: 11px; font-weight: 500;">Make by BangNC13</div>
        </div>
    """, unsafe_allow_html=True)
    
    all_objects = df['Tên đối tượng'].tolist()
    
    # Lọc dữ liệu POP
    st.markdown('<div class="card-title">LỌC DỮ LIỆU POP</div>', unsafe_allow_html=True)
    selected_names = st.multiselect(
        "Chọn danh sách tập điểm:",
        options=all_objects,
        default=all_objects[:10] if len(all_objects) >= 10 else all_objects[:2],
        label_visibility="collapsed"
    )
    
    st.markdown("<hr style='margin: 12px 0; border: none; border-top: 1px solid #e1e4e8;'>", unsafe_allow_html=True)
    
    # Thông tin đo OTDR
    st.markdown('<div class="card-title">📍 THÔNG TIN ĐO (OTDR)</div>', unsafe_allow_html=True)
    
    st.caption("Điểm đo (Đang đứng)")
    start_node_name = st.selectbox("Start Node", options=selected_names if selected_names else all_objects, label_visibility="collapsed")
    
    st.caption("Hướng đo (Xuôi ngọn / Về ODF)")
    end_node_name = st.selectbox("End Node", options=selected_names if selected_names else all_objects, index=min(1, len(selected_names)-1), label_visibility="collapsed")
    
    st.caption("Chiều dài đo được (Mét)")
    measure_dist = st.number_input("Dist", value=170.00, step=10.0, format="%.2f", label_visibility="collapsed")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<button class="btn-danger">📌 Xác định</button>', unsafe_allow_html=True)
    with col2:
        st.markdown('<button class="btn-secondary">🗑️ Xóa</button>', unsafe_allow_html=True)

# 5. Hiển thị Bản đồ
if len(selected_names) < 2:
    st.warning("Vui lòng chọn ít nhất 2 điểm dừng trong Menu bên cạnh.")
else:
    selected_df = df[df['Tên đối tượng'].isin(selected_names)].reset_index(drop=True)
    path_indices, total_km = solve_tsp(selected_df)
    ordered_df = selected_df.iloc[path_indices].reset_index(drop=True)

    center_lat = ordered_df['Latitude'].mean()
    center_lon = ordered_df['Longitude'].mean()

    m = folium.Map(
        location=[center_lat, center_lon], 
        zoom_start=13,
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

    # Nút bấm góc trên trái (GPS của tôi & Chỉ đường) - Thắt chặt lề trái 60px để không che nút Hamburger Menu
    first_target_lat = ordered_df.iloc[0]['Latitude']
    first_target_lon = ordered_df.iloc[0]['Longitude']
    direct_gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={first_target_lat},{first_target_lon}"

    top_buttons_html = f'''
    <div style="
        position: fixed; 
        top: 12px; 
        left: 60px; 
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
            font-size: 13px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 6px;
        ">
            <span style="color: #ff4d4f;">🎯</span> GPS của tôi
        </button>
        
        <a href="{direct_gmaps_url}" target="_blank" style="
            background: #00b894;
            color: #ffffff;
            border: none;
            padding: 7px 12px;
            border-radius: 4px;
            font-size: 13px;
            font-weight: bold;
            text-decoration: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 6px;
        ">
            🛣️ Chỉ đường tới điểm sự cố
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
                    alert("Không thể truy cập GPS vị trí của bạn.");
                }});
            }}
        }}
    </script>
    '''
    m.get_root().html.add_child(folium.Element(top_buttons_html))

    # Vẽ tuyến đường
    route_coords = ordered_df[['Latitude', 'Longitude']].values.tolist()
    folium.PolyLine(
        route_coords, 
        color="#3867d6", 
        weight=5, 
        opacity=0.8
    ).add_to(m)

    # Marker điểm dừng
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

    # Hiển thị bản đồ tràn màn hình
    st_folium(m, width="100%", height=850, returned_objects=[])
