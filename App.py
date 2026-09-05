import os
import json
import math
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# 1. Cấu hình trang Streamlit
st.set_page_config(
    page_title="TQG - Tối Ưu Lộ Trình Di Chuyển",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Dark Theme cho ứng dụng & Sidebar
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"], .main, .stApp {
            margin: 0 !important;
            padding: 0 !important;
            height: 100vh !important;
            overflow: hidden !important;
            background-color: #0E1117 !important;
            color: #E2E8F0 !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #1E293B !important;
            z-index: 999999 !important;
            border-right: 1px solid #334155 !important;
        }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem !important;
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
        }

        .sidebar-title {
            font-size: 1.2rem !important;
            font-weight: 800 !important;
            color: #38BDF8 !important;
            margin-bottom: 2px !important;
        }
        .sidebar-subtitle {
            font-size: 0.75rem !important;
            color: #94A3B8 !important;
            margin-bottom: 10px !important;
        }

        header[data-testid="stHeader"] {
            background: transparent !important;
            height: 0px !important;
            z-index: 999999 !important;
        }

        .main .block-container, 
        [data-testid="stMainBlockContainer"],
        [data-testid="stVerticalBlock"],
        [data-testid="stVerticalBlockBorderWrapper"] {
            padding: 0 !important;
            margin: 0 !important;
            gap: 0rem !important;
            max-width: 100vw !important;
            height: 100vh !important;
        }

        iframe {
            width: 100vw !important;
            height: 100vh !important;
            border: none !important;
            margin: 0 !important;
            padding: 0 !important;
            display: block !important;
        }
        
        div[data-baseweb="select"] > div {
            background-color: #0F172A !important;
            color: #F8FAFC !important;
            border-color: #334155 !important;
        }
        input {
            background-color: #0F172A !important;
            color: #F8FAFC !important;
        }
    </style>
""", unsafe_allow_html=True)

# Khởi tạo session state
if "selected_pops" not in st.session_state:
    st.session_state.selected_pops = []
if "user_gps" not in st.session_state:
    st.session_state.user_gps = None
if "calculated_route" not in st.session_state:
    st.session_state.calculated_route = []

# Nhận tọa độ GPS từ URL trình duyệt
query_params = st.query_params
if "user_lat" in query_params and "user_lon" in query_params:
    try:
        st.session_state.user_gps = (float(query_params["user_lat"]), float(query_params["user_lon"]))
    except Exception:
        pass

# Tính khoảng cách Haversine (km)
def haversine(coord1, coord2):
    R = 6371.0
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Thuật toán Nearest Neighbor tìm đường đi ngắn nhất
def calculate_optimal_route(start_gps, target_points):
    if not target_points:
        return []
    
    unvisited = target_points.copy()
    current_pos = start_gps
    route = []

    while unvisited:
        nearest_item = min(unvisited, key=lambda item: haversine(current_pos, item['coords']))
        route.append(nearest_item)
        current_pos = nearest_item['coords']
        unvisited.remove(nearest_item)

    return route

# Đọc file Excel đính kèm QuanLyTĐ.xlsx
@st.cache_data
def load_local_data():
    file_path = "QuanLyTĐ.xlsx"
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    return None

df = load_local_data()

st.sidebar.markdown('<div class="sidebar-title">⚡ TQG - Tuyến Đường</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-subtitle">Voice by BangNC13 - FPT Telecom System</div>', unsafe_allow_html=True)

if df is not None:
    # Trích xuất mã POP (lấy chuỗi trước dấu chấm, ví dụ: TQGM001 từ TQGM001.0001/FO)
    df['POP'] = df['Tên đối tượng'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
    pop_list = sorted(df['POP'].unique())

    selected_pops = st.sidebar.multiselect(
        "LỌC DỮ LIỆU POP", 
        options=pop_list, 
        default=st.session_state.selected_pops,
        key="pop_multiselect"
    )
    
    col_r1, col_r2 = st.sidebar.columns([1, 1])
    with col_r1:
        if st.button("🔄 Reset bộ lọc", use_container_width=True):
            st.session_state.selected_pops = []
            st.session_state.calculated_route = []
            st.rerun()

    # Lọc dữ liệu theo POP được chọn
    if selected_pops:
        filtered_df = df[df['POP'].isin(selected_pops)].copy()
    else:
        filtered_df = df.copy()

    # Danh sách tọa độ và marker
    target_points = []
    for _, row in filtered_df.iterrows():
        try:
            name = str(row['Tên đối tượng']).strip()
            lat = float(row['Latitude'])
            lon = float(row['Longitude'])
            target_points.append({"name": name, "coords": (lat, lon)})
        except Exception:
            continue

    st.sidebar.markdown("---")
    
    # Nút "Bấm" tính toán lộ trình tối ưu
    if st.sidebar.button("🚀 Bấm", type="primary", use_container_width=True):
        if not selected_pops:
            st.sidebar.warning("⚠️ Vui lòng chọn ít nhất 1 POP để tính lộ trình!")
        elif not target_points:
            st.sidebar.error("❌ Không tìm thấy tọa độ hợp lệ.")
        else:
            start_pos = st.session_state.user_gps if st.session_state.user_gps else target_points[0]['coords']
            st.session_state.calculated_route = calculate_optimal_route(start_pos, target_points)
            st.rerun()

    # Hiển thị kết quả lộ trình
    if st.session_state.calculated_route:
        st.sidebar.markdown("### 🚗 LỘ TRÌNH TỐI ƯU")
        for idx, step in enumerate(st.session_state.calculated_route, 1):
            st.sidebar.markdown(f"**{idx}.** `{step['name']}`")
        
        if st.session_state.user_gps:
            waypoints_str = "/".join([f"{item['coords'][0]},{item['coords'][1]}" for item in st.session_state.calculated_route])
            gmaps_url = f"https://www.google.com/maps/dir/{st.session_state.user_gps[0]},{st.session_state.user_gps[1]}/{waypoints_str}"
            st.sidebar.link_button("🗺️ Mở lộ trình trên Google Maps", gmaps_url, type="secondary", use_container_width=True)

    # Cấu hình bản đồ Leaflet
    map_center = [21.816, 105.208]
    if target_points:
        map_center = [target_points[0]['coords'][0], target_points[0]['coords'][1]]

    markers = [{"coords": pt["coords"], "popup": f"<b>Điểm:</b> {pt['name']}", "tooltip": pt["name"]} for pt in target_points]

    route_polyline = None
    if st.session_state.calculated_route:
        start_pt = list(st.session_state.user_gps) if st.session_state.user_gps else list(st.session_state.calculated_route[0]['coords'])
        r_coords = [start_pt] + [list(item['coords']) for item in st.session_state.calculated_route]
        route_polyline = {
            "coords": r_coords,
            "color": "#F59E0B",
            "weight": 4,
            "opacity": 0.9,
            "dashArray": "8, 8"
        }

    markers_json = json.dumps(markers)
    route_polyline_json = json.dumps(route_polyline)
    map_center_json = json.dumps(map_center)

    leaflet_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            html, body {{
                width: 100%; height: 100vh; margin: 0; padding: 0;
                overflow: hidden; background-color: #0E1117;
            }}
            #map {{
                width: 100%; height: 100vh; background: #0E1117;
            }}
            .leaflet-control-layers, .leaflet-bar {{
                background-color: #1E293B !important;
                border: 1px solid #334155 !important;
                color: #F8FAFC !important;
            }}
            .leaflet-control-layers-toggle {{
                filter: invert(1);
            }}
            .user-location-marker {{
                background-color: #3B82F6;
                border: 3px solid #FFFFFF;
                border-radius: 50%;
                width: 18px !important;
                height: 18px !important;
                margin-left: -9px !important;
                margin-top: -9px !important;
                box-shadow: 0 0 10px rgba(59, 130, 246, 0.9);
            }}
            .leaflet-control-locate {{
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 4px;
                width: 34px; height: 34px;
                line-height: 32px; text-align: center;
                cursor: pointer; font-size: 18px;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                var googleStreets = L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}', {{ maxZoom: 20, attribution: 'Google Maps' }});
                var googleSat = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}', {{ maxZoom: 20, attribution: 'Google Satellite' }});
                var googleHybrid = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}', {{ maxZoom: 20, attribution: 'Google Hybrid' }});

                var map = L.map('map', {{
                    zoomControl: true,
                    attributionControl: false,
                    layers: [googleStreets]
                }}).setView({map_center_json}, 14);

                var baseMaps = {{
                    "🗺️ Google Đường phố": googleStreets,
                    "🛰️ Google Vệ tinh": googleSat,
                    "🌐 Google Hybrid": googleHybrid
                }};
                L.control.layers(baseMaps, null, {{ position: 'topright' }}).addTo(map);

                // Hiển thị các Marker điểm từ file QuanLyTĐ.xlsx
                var markersData = {markers_json};
                markersData.forEach(function(item) {{
                    var circle = L.circleMarker(item.coords, {{
                        radius: 6, color: '#818CF8', fillColor: '#0F172A', fillOpacity: 0.9, weight: 2
                    }}).addTo(map);
                    if (item.popup) circle.bindPopup(item.popup);
                    if (item.tooltip) circle.bindTooltip(item.tooltip);
                }});

                // Vẽ lộ trình kết nối các điểm
                var routeData = {route_polyline_json};
                if (routeData && routeData.coords) {{
                    L.polyline(routeData.coords, {{
                        color: routeData.color,
                        weight: routeData.weight,
                        opacity: routeData.opacity,
                        dashArray: routeData.dashArray
                    }}).addTo(map);
                }}

                // Định vị vị trí GPS thiết bị
                var userMarker = null;
                var accuracyCircle = null;

                function sendGpsToStreamlit(lat, lon) {{
                    const url = new URL(window.parent.location.href);
                    if (url.searchParams.get('user_lat') !== lat.toString()) {{
                        url.searchParams.set('user_lat', lat);
                        url.searchParams.set('user_lon', lon);
                        window.parent.location.href = url.toString();
                    }}
                }}

                function updateLocation(pos) {{
                    var lat = pos.coords.latitude;
                    var lng = pos.coords.longitude;
                    var latlng = [lat, lng];
                    var radius = pos.coords.accuracy / 2;

                    sendGpsToStreamlit(lat, lng);

                    if (userMarker) {{
                        userMarker.setLatLng(latlng);
                        accuracyCircle.setLatLng(latlng).setRadius(radius);
                    }} else {{
                        var userIcon = L.divIcon({{ className: 'user-location-marker' }});
                        userMarker = L.marker(latlng, {{ icon: userIcon }}).addTo(map)
                            .bindPopup("<b>Vị trí hiện tại của bạn</b>");
                        accuracyCircle = L.circle(latlng, radius, {{
                            color: '#3B82F6', fillColor: '#3B82F6', fillOpacity: 0.15, weight: 1
                        }}).addTo(map);
                    }}
                }}

                function handleGPSError(err) {{
                    console.warn("GPS Warning/Error: " + err.message);
                }}

                if ("geolocation" in navigator) {{
                    navigator.geolocation.watchPosition(updateLocation, handleGPSError, {{
                        enableHighAccuracy: true,
                        maximumAge: 0,
                        timeout: 5000
                    }});
                }}

                var locateControl = L.Control.extend({{
                    options: {{ position: 'topleft' }},
                    onAdd: function (map) {{
                        var container = L.DomUtil.create('div', 'leaflet-control-locate');
                        container.innerHTML = '🎯';
                        container.title = "Định vị vị trí của tôi";
                        container.onclick = function() {{
                            if ("geolocation" in navigator) {{
                                navigator.geolocation.getCurrentPosition(function(pos) {{
                                    var latlng = [pos.coords.latitude, pos.coords.longitude];
                                    map.flyTo(latlng, 18);
                                    updateLocation(pos);
                                }}, handleGPSError, {{ enableHighAccuracy: true, timeout: 3000 }});
                            }}
                        }};
                        return container;
                    }}
                }});
                map.addControl(new locateControl());

                setTimeout(function() {{ map.invalidateSize(); }}, 200);
            }});
        </script>
    </body>
    </html>
    """

    components.html(leaflet_html, height=1000, scrolling=False)

else:
    st.error("❌ Không tìm thấy file `QuanLyTĐ.xlsx` trong thư mục làm việc.")
