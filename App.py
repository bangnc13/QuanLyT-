import streamlit as st
import pandas as pd
import requests
import folium
import streamlit.components.v1 as components
from streamlit_folium import st_folium

# ================= 1. CẤU HÌNH TRANG =================
st.set_page_config(
    page_title="Hệ Thống Tối Ưu Lộ Trình - Robotic UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= 2. INJECT CSS CUSTOM UI =================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&display=swap');

    .block-container {
        padding: 0rem !important;
        max-width: 100% !important;
    }

    .stApp {
        background-color: #1a0a00 !important;
    }

    html, body, .stMarkdown, p, label {
        color: #ffffff !important;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #331400 0%, #1f0c00 100%) !important;
        border-right: 2px solid #ff6600 !important;
        box-shadow: 5px 0px 15px rgba(255, 102, 0, 0.4) !important;
    }

    header[data-testid="stHeader"] {
        background-color: transparent !important;
        background: transparent !important;
        z-index: 1 !important;
    }

    header[data-testid="stHeader"] * {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    /* ẨN FOOTER STREAMLIT */
    footer {
        visibility: hidden !important;
        height: 0px !important;
    }

    iframe {
        background-color: transparent !important;
    }
    
    [data-element-container="true"] {
        background-color: transparent !important;
    }

    .stMainBlockContainer, [data-testid="stMainBlockContainer"] {
        background-color: transparent !important;
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

    .hud-label {
        color: #ffffff !important;
        font-size: 0.85rem;
        text-transform: uppercase;
    }

    .hud-value {
        color: #00f0ff !important;
        font-size: 1.1rem;
        font-weight: bold;
        font-family: 'Orbitron', sans-serif;
    }

    hr {
        border-color: #ff6600 !important;
        opacity: 0.5;
    }

    /* MULTISELECT UI FIX */
    [data-baseweb="select"] > div {
        background-color: #1f0c00 !important;
        border: 1px solid #ff6600 !important;
        color: #00f0ff !important;
    }

    [data-baseweb="select"] div[role="button"],
    [data-baseweb="select"] input,
    [data-baseweb="select"] input::placeholder {
        color: #00f0ff !important;
        -webkit-text-fill-color: #00f0ff !important;
    }

    span[data-baseweb="tag"] {
        background-color: rgba(0, 240, 255, 0.2) !important;
        border: 1px solid #00f0ff !important;
    }

    span[data-baseweb="tag"] * {
        color: #00f0ff !important;
        font-weight: bold !important;
    }

    ul[role="listbox"] {
        background-color: #1f0c00 !important;
        border: 1px solid #00f0ff !important;
    }

    li[role="option"] span, li[role="option"] div {
        color: #00f0ff !important;
    }

    li[role="option"]:hover {
        background-color: rgba(0, 240, 255, 0.2) !important;
    }

    /* NÚT COLLAPSE/EXPAND SIDEBAR NEON XANH */
    [data-testid="stSidebarCollapseButton"] button,
    [data-testid="stSidebarExpandButton"] button {
        background-color: #1f0c00 !important;
        border: 2px solid #00f0ff !important;
        border-radius: 50% !important;
        color: #00f0ff !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.6), inset 0 0 5px rgba(0, 240, 255, 0.4) !important;
        transition: all 0.3s ease-in-out !important;
        width: 40px !important;
        height: 40px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    [data-testid="stSidebarCollapseButton"] button svg,
    [data-testid="stSidebarExpandButton"] button svg {
        fill: #00f0ff !important;
        color: #00f0ff !important;
    }

    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="stSidebarExpandButton"] button:hover {
        background-color: #00f0ff !important;
        box-shadow: 0 0 20px #00f0ff, 0 0 35px #00f0ff !important;
        transform: scale(1.1) !important;
    }

    [data-testid="stSidebarCollapseButton"] button:hover svg,
    [data-testid="stSidebarExpandButton"] button:hover svg {
        fill: #000000 !important;
        color: #000000 !important;
    }

    /* ẨN NÚT ZOOM (+/-) */
    .leaflet-control-zoom {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ================= 3. HÀM NẠP DỮ LIỆU EXCEL =================
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(subset=['Latitude', 'Longitude'])
        return df
    except Exception:
        return pd.DataFrame()

# ================= 4. THUẬT TOÁN TỐI ƯU LỘ TRÌNH VÒNG KÍN =================
def get_optimized_route_roundtrip(origin, points_list):
    all_points = [{'Name': 'GPS ORIGIN', 'Latitude': origin[0], 'Longitude': origin[1]}] + points_list
    
    coords_str = ";".join([f"{pt['Longitude']},{pt['Latitude']}" for pt in all_points])
    table_url = f"http://router.project-osrm.org/table/v1/driving/{coords_str}?annotations=duration,distance"
    
    try:
        res = requests.get(table_url, timeout=5).json()
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
        route_res = requests.get(route_url, timeout=5).json()
        
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

# Bắt tọa độ ban đầu từ URL nếu có
realtime_lat = st.query_params.get("lat")
realtime_lon = st.query_params.get("lon")
if realtime_lat and realtime_lon:
    try:
        st.session_state.current_loc = (float(realtime_lat), float(realtime_lon))
    except ValueError:
        pass

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
    
    st.divider()
    
    st.markdown("<div class='hud-label'>📡 Trạng thái định vị GPS REALTIME:</div>", unsafe_allow_html=True)
    
    # Hiển thị HUD dynamic realtime qua HTML container để JS cập nhật trực tiếp
    st.markdown("""
    <div class='hud-card'>
        <div class='hud-label'>Tọa độ Realtime</div>
        <div class='hud-value' id='hud-gps-display'>Đang tìm tín hiệu...</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.button("⚡ Bấm xem lộ trình ⚡", use_container_width=True):
        if not st.session_state.current_loc:
            st.error("Chưa nhận diện được GPS!")
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
map_center = st.session_state.current_loc if st.session_state.current_loc else [df['Latitude'].mean(), df['Longitude'].mean()]

m = folium.Map(
    location=map_center, 
    zoom_start=16, 
    tiles=None,
    zoom_control=False
)

# LAYER 1: Google Street
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    attr='Google Maps',
    name='Google Street (Đường phố)',
    overlay=False,
    control=True,
    show=True
).add_to(m)

# LAYER 2: Google Satellite
folium.TileLayer(
    tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    attr='Google Satellite',
    name='Google Satellite (Vệ tinh)',
    overlay=False,
    control=True,
    show=False
).add_to(m)

folium.LayerControl(position='topright').add_to(m)

# MarkerGPS động siêu tốc xử lý thuần bằng Leaflet JS
gps_marker_js = folium.Element("""
<script>
    var userGpsMarker = null;
    var userMapInstance = null;

    function getLeafletMap() {
        for (var key in window) {
            if (key.startsWith('map_') && window[key] instanceof L.Map) {
                return window[key];
            }
        }
        return null;
    }

    function updateGpsMarkerDirectly(lat, lon) {
        if (!userMapInstance) {
            userMapInstance = getLeafletMap();
        }
        if (!userMapInstance) return;

        var iconHtml = `
            <div id="user-heading-arrow" style="
                width: 42px; 
                height: 42px; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                transition: transform 0.1s linear; 
                transform-origin: center center;
            ">
                <svg width="42" height="42" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style="filter: drop-shadow(0px 0px 8px #00f0ff);">
                    <path d="M12 2L4.5 20.29 5.21 21 12 18 18.79 21 19.5 20.29 12 2Z" fill="#00F0FF" stroke="#FFFFFF" stroke-width="1.5" stroke-linejoin="round"/>
                </svg>
            </div>
        `;

        var customIcon = L.divIcon({
            html: iconHtml,
            iconSize: [42, 42],
            iconAnchor: [21, 21],
            className: ''
        });

        if (userGpsMarker) {
            userGpsMarker.setLatLng([lat, lon]);
        } else {
            userGpsMarker = L.marker([lat, lon], {icon: customIcon}).addTo(userMapInstance);
            userMapInstance.setView([lat, lon], 16);
        }
    }
</script>
""")
m.get_root().html.add_child(gps_marker_js)

if st.session_state.ordered_points:
    for pt in st.session_state.ordered_points:
        folium.Marker(
            location=(pt['Latitude'], pt['Longitude']),
            popup=f"<b>Điểm {pt['Order']}: {pt['Name']}</b>",
            tooltip=f"TARGET [{pt['Order']}]: {pt['Name']}",
            icon=folium.DivIcon(
                html=f"""<div style="
                    background: linear-gradient(135deg, #00f0ff 0%, #7000ff 100%);
                    color: white;
                    border-radius: 50%;
                    width: 30px;
                    height: 30px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-weight: 900;
                    font-family: 'Orbitron', sans-serif;
                    border: 2px solid #ffffff;
                    box-shadow: 0 0 10px rgba(0, 240, 255, 0.9);
                ">{pt['Order']}</div>"""
            )
        ).add_to(m)

if st.session_state.route_coords:
    folium.PolyLine(
        st.session_state.route_coords,
        color="#00F0FF",
        weight=5,
        opacity=0.9,
        tooltip="Cyber Round-Trip Route"
    ).add_to(m)

# FLOATING ACTION BUTTON GPS
gps_button_element = folium.Element("""
<style>
    .leaflet-gps-fab {
        position: fixed !important;
        top: 25px !important;
        left: 25px !important;
        z-index: 999999 !important;
        width: 48px;
        height: 48px;
        background: rgba(31, 12, 0, 0.95);
        border: 2px solid #00f0ff;
        border-radius: 50%;
        color: #00f0ff;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.7), inset 0 0 10px rgba(0, 240, 255, 0.3);
        transition: all 0.2s ease;
    }
    .leaflet-gps-fab:hover {
        transform: scale(1.15);
        background: #00f0ff;
        color: #000000;
        box-shadow: 0 0 25px #00f0ff;
    }
</style>

<div class="leaflet-gps-fab" id="map-gps-btn" title="Cập nhật vị trí Tức Thời">
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3"></circle>
        <path d="M12 2v3m0 14v3M2 12h3m14 0h3"></path>
    </svg>
</div>

<script>
    (function initGpsBtnPure() {
        var gpsBtn = document.getElementById('map-gps-btn');
        if (gpsBtn) {
            gpsBtn.onclick = function(e) {
                e.stopPropagation();
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            var lat = position.coords.latitude;
                            var lon = position.coords.longitude;
                            
                            // Cập nhật ngay lập tức không thông qua Streamlit Reload
                            if (typeof updateGpsMarkerDirectly === 'function') {
                                updateGpsMarkerDirectly(lat, lon);
                            }
                            
                            window.parent.postMessage({
                                type: 'INSTANT_GPS_SET',
                                lat: lat,
                                lon: lon
                            }, '*');
                        },
                        function(error) {
                            alert("Hãy bật GPS định vị trên điện thoại!");
                        },
                        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
                    );
                }
            };
        } else {
            setTimeout(initGpsBtnPure, 50);
        }
    })();
</script>
""")
m.get_root().html.add_child(gps_button_element)

# Đóng sidebar khi bấm bản đồ
map_click_js = folium.Element("""
<script>
    document.addEventListener('DOMContentLoaded', function() {
        var mapContainer = document.querySelector('.folium-map');
        if (mapContainer) {
            mapContainer.addEventListener('click', function() {
                try {
                    window.parent.postMessage({type: 'CLOSE_STREAMLIT_SIDEBAR'}, '*');
                } catch(e) {}
            });
            mapContainer.addEventListener('touchstart', function() {
                try {
                    window.parent.postMessage({type: 'CLOSE_STREAMLIT_SIDEBAR'}, '*');
                } catch(e) {}
            });
        }
    });
</script>
""")
m.get_root().html.add_child(map_click_js)

st_folium(m, use_container_width=True, height=1000)

# ================= 5. ENGINE ĐỊNH VỊ PURE JAVASCRIPT TRỰC TIẾP DOWNTIME 0MS =================
components.html("""
<script>
    window.addEventListener('message', function(event) {
        if (!event.data) return;

        if (event.data.type === 'CLOSE_STREAMLIT_SIDEBAR') {
            const parentDoc = window.parent.document;
            const sidebar = parentDoc.querySelector('[data-testid="stSidebar"]');
            if (sidebar && sidebar.getAttribute('aria-expanded') === 'true') {
                const collapseBtn = parentDoc.querySelector('[data-testid="stSidebarCollapseButton"] button');
                if (collapseBtn) collapseBtn.click();
            }
        }

        if (event.data.type === 'INSTANT_GPS_SET') {
            const lat = event.data.lat;
            const lon = event.data.lon;
            const parentDoc = window.parent.document;
            
            // 1. Cập nhật giao diện HUD bên Sidebar ngay lập tức (Không load lại trang)
            const hudElem = parentDoc.querySelector('#hud-gps-display');
            if (hudElem) {
                hudElem.innerText = lat.toFixed(5) + ', ' + lon.toFixed(5);
            }

            // 2. Cập nhật tham số ngầm cho URL mà không trigger Streamlit reload
            const currentUrl = new URL(parentDoc.location.href);
            currentUrl.searchParams.set('lat', lat);
            currentUrl.searchParams.set('lon', lon);
            parentDoc.history.replaceState({}, '', currentUrl);
        }
    });

    // LA BÀN REALTIME 60FPS
    function handleOrientation(event) {
        let heading = null;
        if (event.webkitCompassHeading) {
            heading = event.webkitCompassHeading;
        } else if (event.alpha !== null) {
            heading = 360 - event.alpha;
        }

        if (heading !== null) {
            const parentDoc = window.parent.document;
            const arrowIcons = parentDoc.querySelectorAll('#user-heading-arrow');
            arrowIcons.forEach(icon => {
                icon.style.transform = `rotate(${heading}deg)`;
            });
        }
    }

    if (window.DeviceOrientationEvent) {
        if (typeof DeviceOrientationEvent.requestPermission === 'function') {
            DeviceOrientationEvent.requestPermission().then(res => {
                if (res === 'granted') {
                    window.addEventListener('deviceorientation', handleOrientation, true);
                }
            });
        } else {
            window.addEventListener('deviceorientationabsolute', handleOrientation, true);
            window.addEventListener('deviceorientation', handleOrientation, true);
        }
    }

    // CONTINUOUS GPS TRACKER - CẬP NHẬT TỨC THÌ LÊN MÀN HÌNH BẢN ĐỒ
    if ("geolocation" in navigator) {
        navigator.geolocation.watchPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                
                // Đẩy vị trí trực tiếp lên bản đồ Leaflet trong Iframe
                const iframeMap = window.parent.document.querySelector('iframe[src*="folium"]');
                if (iframeMap && iframeMap.contentWindow && typeof iframeMap.contentWindow.updateGpsMarkerDirectly === 'function') {
                    iframeMap.contentWindow.updateGpsMarkerDirectly(lat, lon);
                }

                // Cập nhật text HUD
                const hudElem = window.parent.document.querySelector('#hud-gps-display');
                if (hudElem) {
                    hudElem.innerText = lat.toFixed(5) + ', ' + lon.toFixed(5);
                }

                // Cập nhật ngầm URL State
                const currentUrl = new URL(window.parent.location.href);
                currentUrl.searchParams.set('lat', lat);
                currentUrl.searchParams.set('lon', lon);
                window.parent.history.replaceState({}, '', currentUrl);
            },
            (err) => {},
            {
                enableHighAccuracy: true,
                maximumAge: 1000,
                timeout: 5000
            }
        );
    }
</script>
""", height=0, width=0)
