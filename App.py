import os
import json
import math
import pandas as pd
import networkx as nx
import streamlit as st
import streamlit.components.v1 as components

# 1. Cấu hình trang Streamlit
st.set_page_config(
    page_title="TQG - Xác Định Vị Trí Đứt Cáp & Tối Ưu Lộ Trình",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Dark Mode & Giao diện Sidebar giống ảnh
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

        /* Sidebar Style */
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
            margin-bottom: 12px !important;
        }

        /* Style nút "Tôi đang đứng" màu đỏ giống ảnh */
        div.stButton > button[key="btn_my_location"] {
            background-color: #EF4444 !important;
            color: white !important;
            font-weight: bold !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 10px 0px !important;
            font-size: 0.95rem !important;
            box-shadow: 0 4px 6px -1px rgba(239, 68, 68, 0.4);
        }
        div.stButton > button[key="btn_my_location"]:hover {
            background-color: #DC2626 !important;
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

# Khởi tạo Session State
if "user_gps" not in st.session_state:
    st.session_state.user_gps = None
if "break_result" not in st.session_state:
    st.session_state.break_result = None
if "break_gps" not in st.session_state:
    st.session_state.break_gps = None
if "selected_pops" not in st.session_state:
    st.session_state.selected_pops = []

# Đọc GPS truyền từ JavaScript vào URL Parameters
query_params = st.query_params
if "user_lat" in query_params and "user_lon" in query_params:
    try:
        st.session_state.user_gps = (float(query_params["user_lat"]), float(query_params["user_lon"]))
    except Exception:
        pass

# Hàm tính khoảng cách Haversine (km) giữa 2 tọa độ GPS
def haversine(coord1, coord2):
    R = 6371.0
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Tối ưu hóa thứ tự di chuyển qua các điểm (Lộ trình ngắn nhất - Nearest Neighbor)
def calculate_optimal_route(start_gps, pop_locations):
    if not pop_locations:
        return []
    
    unvisited = pop_locations.copy()
    current_pos = start_gps
    route = []

    while unvisited:
        nearest_item = min(unvisited, key=lambda item: haversine(current_pos, item['coords']))
        route.append(nearest_item)
        current_pos = nearest_item['coords']
        unvisited.remove(nearest_item)

    return route

@st.cache_data
def load_server_data():
    possible_files = [
        "Danh-Sách-Đoạn-Cáp.xlsx", 
        "Danh_Sach_Doan_Cap.xlsx", 
        "data.xlsx", 
        "Danh-Sách-Đoạn-Cáp.xls"
    ]
    selected_file = None
    for f in possible_files:
        if os.path.exists(f):
            selected_file = f
            break

    if not selected_file:
        files = [f for f in os.listdir(".") if f.endswith(".xlsx") or f.endswith(".xls")]
        if files:
            selected_file = files[0]

    if selected_file:
        df = pd.read_excel(selected_file)
        return df, selected_file
    return None, None

df, file_name = load_server_data()

# Giao diện Sidebar
st.sidebar.markdown('<div class="sidebar-title">⚡ TQG - Tuyến Đường</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-subtitle">Voice by BangNC13 - FPT Telecom System</div>', unsafe_allow_html=True)

# Nút "📍 Tôi đang đứng" giống hệt giao diện trong ảnh
if st.sidebar.button("📍 Tôi đang đứng", key="btn_my_location", use_container_width=True):
    # Kích hoạt JavaScript để xin quyền truy cập vị trí thiết bị
    components.html("""
        <script>
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    const lat = position.coords.latitude;
                    const lon = position.coords.longitude;
                    const url = new URL(window.parent.location.href);
                    url.searchParams.set('user_lat', lat);
                    url.searchParams.set('user_lon', lon);
                    window.parent.location.href = url.toString();
                }, function(error) {
                    alert("Không thể lấy vị trí. Vui lòng bật GPS / Cho phép quyền truy cập vị trí trên trình duyệt!");
                }, { enableHighAccuracy: true });
            } else {
                alert("Trình duyệt không hỗ trợ Định vị GPS.");
            }
        </script>
    """, height=0)

if df is not None:
    df.columns = [str(col).strip() for col in df.columns]
    
    lat_col1 = next((c for c in df.columns if 'lat' in c.lower() and '1' in c.lower()), None)
    lon_col1 = next((c for c in df.columns if 'lng' in c.lower() or ('lon' in c.lower() and '1' in c.lower())), None)
    lat_col2 = next((c for c in df.columns if 'lat' in c.lower() and '2' in c.lower()), None)
    lon_col2 = next((c for c in df.columns if 'lng' in c.lower() or ('lon' in c.lower() and '2' in c.lower())), None)

    if not lat_col1:
        lat_col1 = next((c for c in df.columns if 'lat' in c.lower() or 'vĩ độ' in c.lower()), None)
        lon_col1 = next((c for c in df.columns if 'lng' in c.lower() or 'lon' in c.lower() or 'kinh độ' in c.lower()), None)

    st.sidebar.markdown("---")
    
    if 'Tên đoạn cáp' in df.columns:
        df['POP'] = df['Tên đoạn cáp'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
        pop_list = sorted(df['POP'].unique())
        
        selected_pops = st.sidebar.multiselect(
            "LỌC DỮ LIỆU POP", 
            options=pop_list, 
            default=st.session_state.selected_pops,
            key="pop_multiselect"
        )
        st.session_state.selected_pops = selected_pops

        if selected_pops:
            pop_df = df[df['POP'].isin(selected_pops)].copy()
        else:
            pop_df = df.copy()
    else:
        pop_df = df.copy()

    G = nx.Graph()
    node_coords = {}

    for _, row in pop_df.iterrows():
        k1 = str(row.get('Điểm KN1', '')).strip()
        k2 = str(row.get('Điểm KN2', '')).strip()
        cable = str(row.get('Tên đoạn cáp', f"{k1}-{k2}")).strip()
        
        len_val = row.get('Chiều dài thực (m)')
        length = float(len_val) if pd.notnull(len_val) else 0.0
        
        try:
            if lat_col1 and lon_col1 and pd.notnull(row[lat_col1]) and pd.notnull(row[lon_col1]):
                node_coords[k1] = (float(row[lat_col1]), float(row[lon_col1]))
            if lat_col2 and lon_col2 and pd.notnull(row[lat_col2]) and pd.notnull(row[lon_col2]):
                node_coords[k2] = (float(row[lat_col2]), float(row[lon_col2]))
        except Exception:
            pass

        if k1 and k2:
            G.add_edge(k1, k2, cable=cable, length=length)

    # Hiển thị lộ trình nếu đã nhận diện GPS & có chọn POP
    pop_targets = []
    for node, coords in node_coords.items():
        pop_targets.append({"name": node, "coords": coords})

    optimal_route = []
    if st.session_state.user_gps:
        st.sidebar.success(f"📍 Đã lấy mốc xuất phát: `{st.session_state.user_gps[0]:.5f}, {st.session_state.user_gps[1]:.5f}`")
        if selected_pops and pop_targets:
            optimal_route = calculate_optimal_route(st.session_state.user_gps, pop_targets)
            
            st.sidebar.markdown("### 🚗 LỘ TRÌNH DỰ KIẾN (TỐI ƯU)")
            st.sidebar.markdown("**Thứ tự di chuyển đề xuất:**")
            
            # Tạo link Google Maps Directions
            waypoints_str = "/".join([f"{item['coords'][0]},{item['coords'][1]}" for item in optimal_route])
            gmaps_dir_url = f"https://www.google.com/maps/dir/{st.session_state.user_gps[0]},{st.session_state.user_gps[1]}/{waypoints_str}"
            
            for idx, step in enumerate(optimal_route, 1):
                st.sidebar.markdown(f"**{idx}.** Điểm `{step['name']}`")

            st.sidebar.link_button("🗺️ Mở Lộ Trình Trên Google Maps", gmaps_dir_url, type="primary", use_container_width=True)
    else:
        st.sidebar.warning("Vui lòng bấm '📍 Tôi đang đứng' trước để lấy mốc xuất phát!")

    # Dữ liệu Bản đồ
    map_center = [21.0285, 105.8542]
    zoom_lvl = 12

    if st.session_state.user_gps:
        map_center = list(st.session_state.user_gps)
        zoom_lvl = 14
    elif len(node_coords) > 0:
        first_coord = list(node_coords.values())[0]
        map_center = [first_coord[0], first_coord[1]]
        zoom_lvl = 14

    polylines = []
    markers = []

    # Vẽ tuyến cáp mặc định
    for u, v, data in G.edges(data=True):
        if u in node_coords and v in node_coords:
            polylines.append({
                "coords": [node_coords[u], node_coords[v]],
                "color": "#38BDF8",
                "weight": 3,
                "opacity": 0.7,
                "tooltip": f"Cáp: {data.get('cable', '')}"
            })

    # Vẽ các điểm tập điểm
    for node_id, coord in node_coords.items():
        markers.append({
            "coords": coord,
            "popup": f"<b>Điểm KN:</b> {node_id}",
            "tooltip": str(node_id),
            "color": "#818CF8",
            "radius": 5
        })

    # Vẽ đường Lộ trình tối ưu (Đường màu đỏ/cam nổi bật nối từ vị trí đứng qua các điểm)
    route_polyline = []
    if st.session_state.user_gps and optimal_route:
        route_coords = [list(st.session_state.user_gps)] + [list(item['coords']) for item in optimal_route]
        route_polyline = {
            "coords": route_coords,
            "color": "#F59E0B",
            "weight": 5,
            "opacity": 0.9,
            "dashArray": "8, 8"
        }

    # Leaflet HTML Render
    leaflet_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            html, body {{ width: 100%; height: 100vh; margin: 0; padding: 0; overflow: hidden; background-color: #0E1117; }}
            #map {{ width: 100%; height: 100vh; background: #0E1117; }}
            .leaflet-control-layers, .leaflet-bar {{ background-color: #1E293B !important; border: 1px solid #334155 !important; color: #F8FAFC !important; }}
            .leaflet-control-layers-toggle {{ filter: invert(1); }}
            .leaflet-control-zoom-in, .leaflet-control-zoom-out {{ color: #F8FAFC !important; background-color: #1E293B !important; }}
            
            .user-start-marker {{
                background-color: #EF4444;
                border: 3px solid #FFFFFF;
                border-radius: 50%;
                width: 20px !important;
                height: 20px !important;
                margin-left: -10px !important;
                margin-top: -10px !important;
                box-shadow: 0 0 12px rgba(239, 68, 68, 1);
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
                }}).setView({json.dumps(map_center)}, {zoom_lvl});

                var baseMaps = {{
                    "🗺️ Google Đường phố": googleStreets,
                    "🛰️ Google Vệ tinh": googleSat,
                    "🌐 Google Hybrid": googleHybrid
                }};
                L.control.layers(baseMaps, null, {{ position: 'topright' }}).addTo(map);

                // Vẽ các tuyến cáp
                var polylinesData = {json.dumps(polylines)};
                polylinesData.forEach(function(item) {{
                    var line = L.polyline(item.coords, {{ color: item.color, weight: item.weight, opacity: item.opacity }}).addTo(map);
                    if (item.tooltip) line.bindTooltip(item.tooltip);
                }});

                // Vẽ các điểm POP
                var markersData = {json.dumps(markers)};
                markersData.forEach(function(item) {{
                    var circle = L.circleMarker(item.coords, {{
                        radius: item.radius, color: item.color, fillColor: '#0F172A', fillOpacity: 0.9, weight: 2
                    }}).addTo(map);
                    if (item.popup) circle.bindPopup(item.popup);
                    if (item.tooltip) circle.bindTooltip(item.tooltip);
                }});

                // Vẽ vị trí người dùng (Điểm xuất phát)
                var userGps = {json.dumps(st.session_state.user_gps)};
                if (userGps) {{
                    var userIcon = L.divIcon({{ className: 'user-start-marker' }});
                    L.marker(userGps, {{ icon: userIcon }}).addTo(map)
                        .bindPopup("<b>📍 Vị trí bạn đang đứng (Mốc xuất phát)</b>").openPopup();
                }}

                // Vẽ đường lộ trình tối ưu nối các điểm
                var routeData = {json.dumps(route_polyline)};
                if (routeData && routeData.coords) {{
                    L.polyline(routeData.coords, {{
                        color: routeData.color,
                        weight: routeData.weight,
                        opacity: routeData.opacity,
                        dashArray: routeData.dashArray
                    }}).addTo(map);
                }}

                setTimeout(function() {{ map.invalidateSize(); }}, 200);
            }});
        </script>
    </body>
    </html>
    """

    components.html(leaflet_html, height=1000, scrolling=False)

else:
    st.error("❌ Không tìm thấy file Excel trên Server. Vui lòng kiểm tra lại file data.")
