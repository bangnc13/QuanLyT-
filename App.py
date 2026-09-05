import streamlit as st
import pandas as pd
import requests
import folium
import streamlit.components.v1 as components

# 1. Cấu hình trang
st.set_page_config(
    page_title="Hệ Thống Tối Ưu Lộ Trình - Ultra Responsive UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject CSS Custom UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&display=swap');

    .block-container { padding: 0rem !important; max-width: 100% !important; }
    .stApp { background-color: #1a0a00 !important; }
    html, body, .stMarkdown, p, label { color: #ffffff !important; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #331400 0%, #1f0c00 100%) !important;
        border-right: 2px solid #ff6600 !important;
        box-shadow: 5px 0px 15px rgba(255, 102, 0, 0.4) !important;
    }

    header[data-testid="stHeader"] { background-color: transparent !important; }
    header[data-testid="stHeader"] * { color: #ffffff !important; fill: #ffffff !important; }
    iframe { background-color: transparent !important; }
    
    .robot-title {
        font-family: 'Orbitron', sans-serif;
        color: #00f0ff !important;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.7);
        margin-top: 15px; margin-bottom: 20px;
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

    .hud-card {
        background: rgba(51, 20, 0, 0.85) !important;
        border: 1px solid #ff6600 !important;
        border-left: 4px solid #00f0ff !important;
        border-radius: 6px;
        padding: 12px; margin-top: 10px;
        box-shadow: inset 0 0 10px rgba(255, 102, 0, 0.2);
        font-family: 'Rajdhani', sans-serif;
    }

    .hud-label { color: #ffffff !important; font-size: 0.85rem; text-transform: uppercase; }
    .hud-value { color: #00f0ff !important; font-size: 1.3rem; font-weight: bold; font-family: 'Orbitron', sans-serif; }

    /* MULTISELECT UI FIX */
    [data-baseweb="select"] > div { background-color: #1f0c00 !important; border: 1px solid #ff6600 !important; color: #00f0ff !important; }
    [data-baseweb="select"] div[role="button"], [data-baseweb="select"] input, [data-baseweb="select"] input::placeholder { color: #00f0ff !important; -webkit-text-fill-color: #00f0ff !important; }
    span[data-baseweb="tag"] { background-color: rgba(0, 240, 255, 0.2) !important; border: 1px solid #00f0ff !important; }
    span[data-baseweb="tag"] * { color: #00f0ff !important; font-weight: bold !important; }

    /* NÚT TOGGLE SIDEBAR NEON */
    [data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarExpandButton"] button {
        background-color: #1f0c00 !important;
        border: 2px solid #00f0ff !important;
        border-radius: 50% !important;
        color: #00f0ff !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.6) !important;
        width: 40px !important; height: 40px !important;
    }

    .leaflet-control-zoom, .leaflet-control-layers { display: none !important; }
</style>
""", unsafe_allow_html=True)

# 3. Nạp dữ liệu
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        return df.dropna(subset=['Latitude', 'Longitude'])
    except Exception:
        return pd.DataFrame()

# 4. Thuật toán tối ưu đường đi
def get_optimized_route_roundtrip(origin, points_list):
    all_points = [{'Name': 'GPS ORIGIN', 'Latitude': origin[0], 'Longitude': origin[1]}] + points_list
    coords_str = ";".join([f"{pt['Longitude']},{pt['Latitude']}" for pt in all_points])
    table_url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=duration,distance"
    
    try:
        res = requests.get(table_url, timeout=10).json()
        if res.get('code') != 'Ok': return None, [], 0, 0
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
            ordered_points.append({'Name': pt['Tên đối tượng'], 'Latitude': pt['Latitude'], 'Longitude': pt['Longitude'], 'Order': order})
            route_coords_str += f";{pt['Longitude']},{pt['Latitude']}"
        route_coords_str += f";{origin[1]},{origin[0]}"

        route_url = f"http://router.project-osrm.org/route/v1/driving/{route_coords_str}?overview=full&geometries=geojson"
        route_res = requests.get(route_url, timeout=10).json()
        
        if route_res.get('code') == 'Ok':
            route_data = route_res['routes'][0]
            route_coords = [(lat, lon) for lon, lat in route_data['geometry']['coordinates']]
            return route_coords, ordered_points, route_data['distance']/1000.0, route_data['duration']/60.0
    except Exception:
        pass
    return None, [], 0, 0

df = load_data('QuanLyTĐ.xlsx')
if df.empty:
    df = pd.DataFrame({'Tên đối tượng': ['Điểm A', 'Điểm B'], 'Latitude': [21.0285, 21.0350], 'Longitude': [105.8542, 105.8400]})

if 'current_loc' not in st.session_state: st.session_state.current_loc = (21.0285, 105.8542)
if 'route_coords' not in st.session_state: st.session_state.route_coords = None
if 'ordered_points' not in st.session_state: st.session_state.ordered_points = []
if 'route_summary' not in st.session_state: st.session_state.route_summary = None

realtime_lat = st.query_params.get("lat")
realtime_lon = st.query_params.get("lon")
if realtime_lat and realtime_lon:
    try: st.session_state.current_loc = (float(realtime_lat), float(realtime_lon))
    except ValueError: pass

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("<h2 class='robot-title'>🤖 Make By BangNC13</h2>", unsafe_allow_html=True)
    selected_names = st.multiselect("🎯 Chọn danh sách tập điểm cần đi:", options=df['Tên đối tượng'].tolist(), max_selections=15)
    
    st.divider()
    lat, lon = st.session_state.current_loc
    st.markdown(f"""
    <div class='hud-card'>
        <div class='hud-label'>Tọa độ Khởi tạo / GPS</div>
        <div class='hud-value'>{lat:.5f}, {lon:.5f}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⚡ Bấm xem lộ trình ⚡", use_container_width=True):
        if selected_names:
            selected_df = df[df['Tên đối tượng'].isin(selected_names)]
            route_coords, ordered_points, dist_km, dur_min = get_optimized_route_roundtrip(st.session_state.current_loc, selected_df.to_dict('records'))
            if route_coords:
                st.session_state.route_coords = route_coords
                st.session_state.ordered_points = ordered_points
                st.session_state.route_summary = {'distance': dist_km, 'duration': dur_min}

    if st.session_state.route_summary:
        st.divider()
        st.markdown(f"""
        <div class='hud-card'>
            <div class='hud-label'>Quãng đường vòng kín</div>
            <div class='hud-value'>{st.session_state.route_summary['distance']:.2f} KM</div>
            <div class='hud-label' style='margin-top:6px;'>Thời gian ước tính</div>
            <div class='hud-value'>{st.session_state.route_summary['duration']:.0f} PHÚT</div>
        </div>
        """, unsafe_allow_html=True)

# ================= MAIN MAP =================
m = folium.Map(location=st.session_state.current_loc, zoom_start=17, tiles=None, zoom_control=False)

folium.TileLayer('https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', attr='Google Maps', name='Google Street').add_to(m)
folium.TileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr='Google Satellite', name='Google Satellite').add_to(m)

# Marker Mũi Tên Động (Interactive Dynamic Marker)
arrow_html = """
<div id="live-user-marker" style="width: 50px; height: 50px; display: flex; justify-content: center; align-items: center; transition: transform 0.05s linear;">
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" style="filter: drop-shadow(0px 0px 10px #00f0ff);">
        <path d="M12 2L4.5 20.29 5.21 21 12 18 18.79 21 19.5 20.29 12 2Z" fill="#00F0FF" stroke="#FFFFFF" stroke-width="1.5"/>
    </svg>
</div>
"""
folium.Marker(
    location=st.session_state.current_loc,
    icon=folium.DivIcon(icon_size=(50,50), icon_anchor=(25,25), html=arrow_html)
).add_to(m)

if st.session_state.ordered_points:
    for pt in st.session_state.ordered_points:
        folium.Marker(
            location=(pt['Latitude'], pt['Longitude']),
            icon=folium.DivIcon(html=f"""<div style="background:#00f0ff; color:#000; border-radius:50%; width:28px; height:28px; display:flex; justify-content:center; align-items:center; font-weight:bold; border:2px solid #fff;">{pt['Order']}</div>""")
        ).add_to(m)

if st.session_state.route_coords:
    folium.PolyLine(st.session_state.route_coords, color="#00F0FF", weight=5, opacity=0.85).add_to(m)

from streamlit_folium import st_folium
st_folium(m, use_container_width=True, height=1000)

# 5. ENGINE JAVASCRIPT ĐỒNG BỘ CLIENT (REALTIME HIGH FREQUENCY GPS & COMPASS)
components.html("""
<script>
    // A. Thu gọn Sidebar khi chạm vào bản đồ
    window.addEventListener('message', function(e) {
        if (e.data && e.data.type === 'CLOSE_SIDEBAR') {
            const pDoc = window.parent.document;
            const sb = pDoc.querySelector('[data-testid="stSidebar"]');
            if (sb && sb.getAttribute('aria-expanded') === 'true') {
                const btn = pDoc.querySelector('[data-testid="stSidebarCollapseButton"] button');
                if (btn) btn.click();
            }
        }
    });

    const pDoc = window.parent.document;
    
    // B. Bộ Lọc Smooth Motion (Low-Pass Filter)
    let currentHeading = 0;
    let targetHeading = 0;

    function smoothRotate() {
        let diff = targetHeading - currentHeading;
        while (diff < -180) diff += 360;
        while (diff > 180) diff -= 360;

        // Nội suy mượt theo thời gian
        currentHeading += diff * 0.2; 

        const arrow = pDoc.querySelector('#live-user-marker');
        if (arrow) {
            arrow.style.transform = `rotate(${currentHeading}deg)`;
        }
        requestAnimationFrame(smoothRotate);
    }
    requestAnimationFrame(smoothRotate);

    // C. Bắt La Bàn Độ Nhạy Cao
    function handleCompass(event) {
        let heading = null;
        if (event.webkitCompassHeading) {
            heading = event.webkitCompassHeading; // iOS
        } else if (event.alpha !== null) {
            heading = 360 - event.alpha; // Android
        }
        if (heading !== null) {
            targetHeading = heading;
        }
    }

    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
        DeviceOrientationEvent.requestPermission().then(r => {
            if (r === 'granted') window.addEventListener('deviceorientation', handleCompass, true);
        });
    } else {
        window.addEventListener('deviceorientationabsolute', handleCompass, true);
        window.addEventListener('deviceorientation', handleCompass, true);
    }

    // D. Realtime GPS Tracking (Cập nhật vị trí tức thì trên Canvas)
    if ("geolocation" in navigator) {
        navigator.geolocation.watchPosition(
            (pos) => {
                const lat = pos.coords.latitude;
                const lon = pos.coords.longitude;
                
                // Đồng bộ mượt với leaflet instance nếu có
                const mapEl = pDoc.querySelector('.folium-map');
                if (mapEl && mapEl._leaflet_id) {
                    // Cập nhật vị trí marker không cần reload Streamlit
                }
            },
            (err) => console.error(err),
            { enableHighAccuracy: true, maximumAge: 0, timeout: 3000 }
        );
    }
</script>
""", height=0, width=0)
