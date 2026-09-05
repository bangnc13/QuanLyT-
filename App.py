import streamlit as st
import pandas as pd
import requests
import folium
import streamlit.components.v1 as components
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation

# 1. Cấu hình trang Full-Width
st.set_page_config(
    page_title="Hệ Thống Tối Ưu Lộ Trình - Robotic UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject CSS Custom
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

    /* TRONG SUỐT THANH HEADER TÊN CÙNG */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        background: transparent !important;
    }

    header[data-testid="stHeader"] * {
        color: #ffffff !important;
        fill: #ffffff !important;
    }

    /* ================= TRONG SUỐT KHU VỰC BẢN ĐỒ VÀ PHẦN DƯỚI BẢN ĐỒ ================= */
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
        font-size: 1.3rem;
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

    /* ẨN NÚT ZOOM (+/-) VÀ MENU LAYER CONTROL BẢN ĐỒ */
    .leaflet-control-zoom,
    .leaflet-control-layers {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Hàm nạp dữ liệu
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(subset=['Latitude', 'Longitude'])
        return df
    except Exception:
        return pd.DataFrame()

# 4. THUẬT TOÁN TỐI ƯU LỘ TRÌNH VÒNG KÍN (ROUND-TRIP: BẮT ĐẦU = KẾT THÚC)
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
    
    st.markdown("<div class='hud-label'>📡 Trạng thái định vị GPS:</div>", unsafe_allow_html=True)
    loc_data = get_geolocation()
    
    if loc_data and 'coords' in loc_data:
        lat = loc_data['coords']['latitude']
        lon = loc_data['coords']['longitude']
        st.session_state.current_loc = (lat, lon)
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

m = folium.Map(
    location=map_center, 
    zoom_start=14, 
    tiles=None,
    zoom_control=False
)

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

if st.session_state.current_loc:
    folium.Marker(
        location=st.session_state.current_loc,
        popup="<b>Vị trí xuất phát & Kết thúc (GPS CORE)</b>",
        tooltip="GPS ORIGIN & END",
        icon=folium.Icon(color='red', icon='crosshairs', prefix='fa')
    ).add_to(m)

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

st_folium(m, use_container_width=True, height=1000)

# TỰ ĐỘNG ẨN SIDEBAR KHI CHẠM/CLICK VÀO BẢN ĐỒ
components.html("""
<script>
    const parentDoc = window.parent.document;
    
    function attachMapClickListener() {
        const iframes = parentDoc.querySelectorAll('iframe');
        iframes.forEach(iframe => {
            try {
                iframe.contentWindow.document.addEventListener('click', function() {
                    const collapseBtn = parentDoc.querySelector('[data-testid="stSidebarCollapseButton"] button');
                    if (collapseBtn) {
                        collapseBtn.click();
                    }
                });
            } catch (e) {
                // Bỏ qua lỗi cross-origin đối với iframe bên thứ ba
            }
        });
    }

    setTimeout(attachMapClickListener, 1500);
</script>
""", height=0, width=0)
