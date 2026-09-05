import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from math import radians, cos, sin, asin, sqrt

# 1. Cấu hình trang Full-Width
st.set_page_config(
    page_title="Hệ Thống Tối Ưu Lộ Trình - Realtime UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject CSS Custom
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&display=swap');

    .block-container { padding: 0rem !important; max-width: 100% !important; }
    .stApp { background-color: #1a0a00 !important; }
    html, body, .stMarkdown, p, label { color: #ffffff !important; }

    /* Custom nút ẩn/hiện menu sidebar màu Xanh Neon & Bo tròn */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarExpandButton"] button,
    button[data-testid="baseButton-headerNoPadding"] {
        background-color: #1a0a00 !important;
        border: 2px solid #00f0ff !important;
        border-radius: 50% !important;
        color: #00f0ff !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.6) !important;
        transition: all 0.3s ease-in-out !important;
        width: 40px !important;
        height: 40px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    [data-testid="stSidebarCollapseButton"]:hover,
    [data-testid="stSidebarExpandButton"] button:hover,
    button[data-testid="baseButton-headerNoPadding"]:hover {
        background-color: #00f0ff !important;
        color: #000000 !important;
        box-shadow: 0 0 20px rgba(0, 240, 255, 1) !important;
        transform: scale(1.1) !important;
    }

    /* Đổi màu icon bên trong nút menu sang Xanh Neon */
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebarExpandButton"] svg,
    button[data-testid="baseButton-headerNoPadding"] svg {
        fill: #00f0ff !important;
        color: #00f0ff !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #331400 0%, #1f0c00 100%) !important;
        border-right: 2px solid #ff6600 !important;
        box-shadow: 5px 0px 15px rgba(255, 102, 0, 0.4) !important;
    }

    .robot-title {
        font-family: 'Orbitron', sans-serif;
        color: #00f0ff !important;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.7);
        margin-top: 15px;
        margin-bottom: 20px;
    }

    div.stButton > button {
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        color: #000000 !important;
        background: linear-gradient(135deg, #00f0ff 0%, #7000ff 100%) !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 12px 24px !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        clip-path: polygon(10% 0, 100% 0, 90% 100%, 0 100%);
        transition: all 0.3s ease-in-out !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.4) !important;
    }

    div.stButton > button:hover {
        transform: scale(1.03) translateY(-2px) !important;
        box-shadow: 0 0 25px rgba(0, 240, 255, 0.8), 0 0 10px rgba(112, 0, 255, 0.8) !important;
        color: #ffffff !important;
    }

    .hud-card {
        background: rgba(51, 20, 0, 0.85) !important;
        border: 1px solid #ff6600 !important;
        border-left: 4px solid #00f0ff !important;
        border-radius: 6px;
        padding: 12px;
        margin-top: 10px;
        box-shadow: inset 0 0 10px rgba(255, 102, 0, 0.2);
        font-family: 'Rajdhani', sans-serif;
    }

    .hud-label { color: #ffffff !important; font-size: 0.85rem; text-transform: uppercase; }
    .hud-value { color: #00f0ff !important; font-size: 1.3rem; font-weight: bold; font-family: 'Orbitron', sans-serif; }
    hr { border-color: #ff6600 !important; opacity: 0.5; }

    [data-baseweb="select"] > div { background-color: #1f0c00 !important; border: 1px solid #ff6600 !important; color: #00f0ff !important; }
    [data-baseweb="select"] div[role="button"], [data-baseweb="select"] input, [data-baseweb="select"] input::placeholder { color: #00f0ff !important; -webkit-text-fill-color: #00f0ff !important; }
    span[data-baseweb="tag"] { background-color: rgba(0, 240, 255, 0.2) !important; border: 1px solid #00f0ff !important; }
    span[data-baseweb="tag"] * { color: #00f0ff !important; font-weight: bold !important; }
    ul[role="listbox"] { background-color: #1f0c00 !important; border: 1px solid #00f0ff !important; }
    li[role="option"] span, li[role="option"] div { color: #00f0ff !important; }
    li[role="option"]:hover { background-color: rgba(0, 240, 255, 0.2) !important; }
</style>
""", unsafe_allow_html=True)

# 3. Hàm phụ trợ
def haversine(lat1, lon1, lat2, lon2):
    r = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return 2 * r * asin(sqrt(a))

@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(subset=['Latitude', 'Longitude'])
        return df
    except Exception:
        return pd.DataFrame()

# 4. Thuật toán OSRM Round-trip
def get_optimized_route_roundtrip(origin, points_list):
    all_points = [{'Name': 'GPS ORIGIN', 'Latitude': origin[0], 'Longitude': origin[1]}] + points_list
    coords_str = ";".join([f"{pt['Longitude']},{pt['Latitude']}" for pt in all_points])
    table_url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=duration,distance"
    
    try:
        res = requests.get(table_url, timeout=10).json()
        if res.get('code') != 'Ok':
            return None, [], 0, 0
            
        durations = res['durations']
        unvisited = list(range(1, len(all_points)))
        current_idx = 0
        ordered_indices = []
        
        while unvisited:
            next_idx = min(unvisited, key=lambda x: durations[current_idx][x])
            ordered_indices.append(next_idx)
            unvisited.remove(next_idx)
            current_idx = next_idx

        ordered_points = []
        route_coords_str = f"{origin[1]},{origin[0]}"
        
        for order, idx in enumerate(ordered_indices, 1):
            pt = all_points[idx]
            ordered_points.append({
                'Name': pt['Tên đối tượng'],
                'Latitude': pt['Latitude'],
                'Longitude': pt['Longitude'],
                'Order': order
            })
            route_coords_str += f";{pt['Longitude']},{pt['Latitude']}"

        route_coords_str += f";{origin[1]},{origin[0]}"

        route_url = f"http://router.project-osrm.org/route/v1/driving/{route_coords_str}?overview=full&geometries=geojson"
        route_res = requests.get(route_url, timeout=10).json()
        
        if route_res.get('code') == 'Ok':
            route_data = route_res['routes'][0]
            route_coords = [(lat, lon) for lon, lat in route_data['geometry']['coordinates']]
            dist_km = route_data['distance'] / 1000.0
            dur_min = route_data['duration'] / 60.0
            return route_coords, ordered_points, dist_km, dur_min

    except Exception as e:
        st.error(f"Lỗi tính toán lộ trình: {e}")
        
    return None, [], 0, 0

# Khởi tạo dữ liệu
df = load_data('QuanLyTĐ.xlsx')
if df.empty:
    df = pd.DataFrame({
        'Tên đối tượng': ['Điểm A', 'Điểm B', 'Điểm C'],
        'Latitude': [21.0285, 21.0350, 21.0200],
        'Longitude': [105.8542, 105.8400, 105.8600]
    })

if 'current_loc' not in st.session_state:
    st.session_state.current_loc = None
if 'route_coords' not in st.session_state:
    st.session_state.route_coords = None
if 'ordered_points' not in st.session_state:
    st.session_state.ordered_points = []
if 'route_summary' not in st.session_state:
    st.session_state.route_summary = None
if 'selected_targets' not in st.session_state:
    st.session_state.selected_targets = []

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("<h2 class='robot-title'>🤖 Make By BangNC13</h2>", unsafe_allow_html=True)
    
    options = df['Tên đối tượng'].tolist()
    selected_names = st.multiselect(
        "🎯 Chọn danh sách tập điểm cần đi (Tối đa 15):",
        options=options,
        max_selections=15,
        placeholder="Choose options"
    )
    st.session_state.selected_targets = selected_names
    
    st.divider()
    
    st.markdown("<div class='hud-label'>📡 Trạng thái định vị GPS:</div>", unsafe_allow_html=True)
    
    loc_data = get_geolocation()
    if loc_data and 'coords' in loc_data:
        new_lat = loc_data['coords']['latitude']
        new_lon = loc_data['coords']['longitude']
        
        if st.session_state.current_loc is None or haversine(st.session_state.current_loc[0], st.session_state.current_loc[1], new_lat, new_lon) > 20:
            st.session_state.current_loc = (new_lat, new_lon)
            if st.session_state.selected_targets and st.session_state.route_coords:
                selected_df = df[df['Tên đối tượng'].isin(st.session_state.selected_targets)]
                points_list = selected_df.to_dict('records')
                route_coords, ordered_points, dist_km, dur_min = get_optimized_route_roundtrip(st.session_state.current_loc, points_list)
                if route_coords:
                    st.session_state.route_coords = route_coords
                    st.session_state.ordered_points = ordered_points
                    st.session_state.route_summary = {'distance': dist_km, 'duration': dur_min}
                st.rerun()

    if st.session_state.current_loc:
        lat, lon = st.session_state.current_loc
        st.markdown(f"""
        <div class='hud-card'>
            <div class='hud-label'>Tọa độ hiện tại</div>
            <div class='hud-value'>{lat:.4f}, {lon:.4f}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Bật GPS thiết bị để xác định điểm gốc.")

    st.divider()

    if st.button("⚡ Bấm xem lộ trình ⚡", use_container_width=True):
        if not st.session_state.current_loc:
            st.error("Chưa có tín hiệu GPS!")
        elif not selected_names:
            st.error("Chưa chọn mục tiêu!")
        else:
            selected_df = df[df['Tên đối tượng'].isin(selected_names)]
            points_list = selected_df.to_dict('records')
            
            with st.spinner("🤖 Đang tối ưu hóa lộ trình vòng kín..."):
                route_coords, ordered_points, dist_km, dur_min = get_optimized_route_roundtrip(
                    st.session_state.current_loc, points_list
                )
                
                if route_coords:
                    st.session_state.route_coords = route_coords
                    st.session_state.ordered_points = ordered_points
                    st.session_state.route_summary = {
                        'distance': dist_km,
                        'duration': dur_min
                    }
                    st.rerun()

    if st.session_state.route_summary:
        st.divider()
        st.markdown(f"""
        <div class='hud-card'>
            <div class='hud-label'>Tổng quãng đường (Vòng kín)</div>
            <div class='hud-value'>{st.session_state.route_summary['distance']:.2f} KM</div>
            <div class='hud-label' style='margin-top:8px;'>Thời gian di chuyển</div>
            <div class='hud-value'>{st.session_state.route_summary['duration']:.0f} PHÚT</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><b style='color:#ffffff;'>📍 Lộ trình thực thi:</b>", unsafe_allow_html=True)
        st.markdown("<span style='color:#00f0ff;'>[0] Vị trí xuất phát (GPS CORE)</span>", unsafe_allow_html=True)
        for pt in st.session_state.ordered_points:
            st.markdown(f"<span style='color:#00f0ff;'>[{pt['Order']}]</span> <span style='color:#ffffff;'>{pt['Name']}</span>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:#00f0ff;'>[{len(st.session_state.ordered_points)+1}]</span> <span style='color:#ffffff;'>Quay về vị trí xuất phát</span>", unsafe_allow_html=True)

# ================= MAIN CONTENT MAP =================
if st.session_state.current_loc:
    map_center = st.session_state.current_loc
else:
    map_center = [df['Latitude'].mean(), df['Longitude'].mean()]

m = folium.Map(location=map_center, zoom_start=15, tiles=None)

folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google Maps',
    name='Google Street',
    overlay=False
).add_to(m)

folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satellite',
    name='Google Satellite',
    overlay=False
).add_to(m)

# Các điểm Target
if st.session_state.ordered_points:
    for pt in st.session_state.ordered_points:
        folium.Marker(
            location=(pt['Latitude'], pt['Longitude']),
            popup=f"<b>Điểm {pt['Order']}: {pt['Name']}</b>",
            tooltip=f"TARGET [{pt['Order']}]: {pt['Name']}",
            icon=folium.DivIcon(
                html=f"""<div style="
                    background: linear-gradient(135deg, #00f0ff 0%, #7000ff 100%);
                    color: white; border-radius: 50%; width: 30px; height: 30px;
                    display: flex; justify-content: center; align-items: center;
                    font-weight: 900; font-family: 'Orbitron', sans-serif;
                    border: 2px solid #ffffff; box-shadow: 0 0 10px rgba(0, 240, 255, 0.9);
                ">{pt['Order']}</div>"""
            )
        ).add_to(m)

# Tuyến đường đã tối ưu
if st.session_state.route_coords:
    folium.PolyLine(
        st.session_state.route_coords,
        color="#00F0FF",
        weight=5,
        opacity=0.9,
        tooltip="Cyber Round-Trip Route"
    ).add_to(m)

folium.LayerControl().add_to(m)

# INJECT JAVASCRIPT & CSS REALTIME MARKER VÀ NÚT TỌA ĐỘ GPS
js_realtime_tracker = """
<script>
    setTimeout(function() {
        var map_element = document.querySelector('.leaflet-container');
        if (!map_element) return;
        var map = map_element._leaflet_map;
        
        // 1. Tạo Icon Marker chuẩn Google Maps Blue Dot
        var googleDotIcon = L.divIcon({
            className: 'gmaps-marker',
            html: '<div class="gmaps-pulse"></div><div class="gmaps-dot"></div>',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });

        var userMarker = null;
        var currentLatLng = null;

        // 2. Hàm định vị vị trí người dùng
        function updateLocation(centerMap) {
            if ("geolocation" in navigator) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    var lat = position.coords.latitude;
                    var lng = position.coords.longitude;
                    currentLatLng = new L.LatLng(lat, lng);

                    if (!userMarker) {
                        userMarker = L.marker(currentLatLng, {icon: googleDotIcon, zIndexOffset: 1000}).addTo(map);
                        userMarker.bindTooltip("Vị trí của bạn (Realtime)", {permanent: false, direction: 'top'});
                    } else {
                        userMarker.setLatLng(currentLatLng);
                    }

                    if (centerMap) {
                        map.flyTo(currentLatLng, 16, { animate: true, duration: 1.5 });
                    }
                }, function(error) {
                    console.error("Lỗi GPS: ", error);
                }, { enableHighAccuracy: true, maximumAge: 1000, timeout: 5000 });
            }
        }

        // Tự động lấy vị trí ban đầu
        updateLocation(false);

        // Theo dõi di chuyển liên tục
        if ("geolocation" in navigator) {
            navigator.geolocation.watchPosition(function(position) {
                var lat = position.coords.latitude;
                var lng = position.coords.longitude;
                currentLatLng = new L.LatLng(lat, lng);

                if (!userMarker) {
                    userMarker = L.marker(currentLatLng, {icon: googleDotIcon, zIndexOffset: 1000}).addTo(map);
                    userMarker.bindTooltip("Vị trí của bạn (Realtime)", {permanent: false, direction: 'top'});
                } else {
                    userMarker.setLatLng(currentLatLng);
                }
            }, null, { enableHighAccuracy: true, maximumAge: 1000, timeout: 5000 });
        }

        # 3. Tạo nút bấm biểu tượng Tọa độ (GPS Control)
        var gpsControl = L.control({position: 'topright'});
        gpsControl.onAdd = function (map) {
            var div = L.DomUtil.create('div', 'leaflet-bar leaflet-control custom-gps-btn');
            div.innerHTML = '<button title="Định vị vị trí hiện tại" style="background-color: #1a0a00; border: 2px solid #00f0ff; border-radius: 50%; width: 44px; height: 44px; cursor: pointer; display: flex; justify-content: center; align-items: center; box-shadow: 0 0 15px rgba(0,240,255,0.6); transition: all 0.3s ease;">' +
                            '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#00f0ff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">' +
                            '<crosshair x1="12" y1="2" x2="12" y2="6"></crosshair>' +
                            '<circle cx="12" cy="12" r="7"></circle>' +
                            '<line x1="12" y1="2" x2="12" y2="5"></line>' +
                            '<line x1="12" y1="19" x2="12" y2="22"></line>' +
                            '<line x1="2" y1="12" x2="5" y2="12"></line>' +
                            '<line x1="19" y1="12" x2="22" y2="12"></line>' +
                            '</svg></button>';
            
            div.onclick = function() {
                updateLocation(true);
            };
            return div;
        };
        gpsControl.addTo(map);

    }, 1000);
</script>

<style>
.gmaps-marker {
    position: relative;
    width: 24px;
    height: 24px;
}

.gmaps-dot {
    width: 16px;
    height: 16px;
    background-color: #4285F4;
    border: 3px solid #FFFFFF;
    border-radius: 50%;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    z-index: 2;
}

.gmaps-pulse {
    width: 40px;
    height: 40px;
    background-color: rgba(66, 133, 244, 0.35);
    border-radius: 50%;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    animation: gmaps-ripple 2s infinite ease-out;
    z-index: 1;
}

@keyframes gmaps-ripple {
    0% {
        width: 16px;
        height: 16px;
        opacity: 0.8;
    }
    100% {
        width: 50px;
        height: 50px;
        opacity: 0;
    }
}

.custom-gps-btn button:hover {
    background-color: #00f0ff !important;
    transform: scale(1.1);
    box-shadow: 0 0 25px rgba(0, 240, 255, 1) !important;
}

.custom-gps-btn button:hover svg {
    stroke: #000000 !important;
}
</style>
"""

# Render Map
map_data = st_folium(m, width="100%", height=850)

# Inject đoạn mã HTML/JS
st.components.v1.html(js_realtime_tracker, height=0)
