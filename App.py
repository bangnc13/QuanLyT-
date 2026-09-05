import os
import json
import pandas as pd
import networkx as nx
import streamlit as st
import streamlit.components.v1 as components

# 1. Cấu hình trang Streamlit
st.set_page_config(
    page_title="TQG - Tuyến đường thu cước",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Tùy chỉnh Dark Theme toàn bộ App & Sidebar
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

        /* Sidebar Dark Mode */
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
if "break_result" not in st.session_state:
    st.session_state.break_result = None
if "break_gps" not in st.session_state:
    st.session_state.break_gps = None
if "selected_pops" not in st.session_state:
    st.session_state.selected_pops = []

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

st.sidebar.markdown('<div class="sidebar-title">⚡ TQG - Tuyến Đường</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-subtitle">Voice by BangNC13 - FPT Telecom System</div>', unsafe_allow_html=True)

if df is not None:
    df.columns = [str(col).strip() for col in df.columns]
    
    lat_col1 = next((c for c in df.columns if 'lat' in c.lower() and '1' in c.lower()), None)
    lon_col1 = next((c for c in df.columns if 'lng' in c.lower() or ('lon' in c.lower() and '1' in c.lower())), None)
    lat_col2 = next((c for c in df.columns if 'lat' in c.lower() and '2' in c.lower()), None)
    lon_col2 = next((c for c in df.columns if 'lng' in c.lower() or ('lon' in c.lower() and '2' in c.lower())), None)

    if not lat_col1:
        lat_col1 = next((c for c in df.columns if 'lat' in c.lower() or 'vĩ độ' in c.lower()), None)
        lon_col1 = next((c for c in df.columns if 'lng' in c.lower() or 'lon' in c.lower() or 'kinh độ' in c.lower()), None)

    if 'Tên đoạn cáp' in df.columns:
        df['POP'] = df['Tên đoạn cáp'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x))
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
                st.session_state.break_result = None
                st.session_state.break_gps = None
                st.rerun()

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

    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 THÔNG TIN ĐO (OTDR)")
    
    all_nodes = sorted(list(G.nodes()))
    if all_nodes:
        start_node = st.sidebar.selectbox("Điểm đo (Đang đứng)", all_nodes, key="start_node")
        neighbors = list(G.neighbors(start_node)) if start_node in G else []
        direction_node = st.sidebar.selectbox("Hướng đo (Xuôi ngọn / Về ODF)", neighbors, key="direction_node")
        measured_len = st.sidebar.number_input("Chiều dài đo được (Mét)", min_value=0.0, value=170.0, step=10.0, key="measured_len")

        col_btn1, col_btn2 = st.sidebar.columns(2)
        with col_btn1:
            btn_calc = st.button("🎯 Xác định", type="primary", use_container_width=True)
        with col_btn2:
            btn_reset = st.button("❌ Xóa kết quả", use_container_width=True)

        if btn_reset:
            st.session_state.break_result = None
            st.session_state.break_gps = None
            st.rerun()

        if btn_calc and start_node and direction_node:
            current = start_node
            nxt = direction_node
            accumulated = 0.0
            visited = {current}

            b_res = None
            b_gps = None

            while True:
                edge_data = G[current][nxt]
                seg_len = edge_data['length']
                cable_id = edge_data['cable']
                visited.add(nxt)

                if accumulated + seg_len >= measured_len:
                    d1 = measured_len - accumulated
                    d2 = seg_len - d1
                    b_res = {
                        "cable": cable_id,
                        "from": current,
                        "to": nxt,
                        "d1": d1,
                        "d2": d2,
                        "seg_len": seg_len,
                        "total": measured_len
                    }

                    if current in node_coords and nxt in node_coords and seg_len > 0:
                        lat1, lon1 = node_coords[current]
                        lat2, lon2 = node_coords[nxt]
                        ratio = d1 / seg_len
                        break_lat = lat1 + (lat2 - lat1) * ratio
                        break_lon = lon1 + (lon2 - lon1) * ratio
                        b_gps = (break_lat, break_lon)
                    break
                else:
                    accumulated += seg_len
                    next_nodes = [n for n in G.neighbors(nxt) if n not in visited]
                    if not next_nodes:
                        break
                    current = nxt
                    nxt = next_nodes[0]

            st.session_state.break_result = b_res
            st.session_state.break_gps = b_gps
            st.rerun()

    if st.session_state.break_result:
        res = st.session_state.break_result
        st.sidebar.error("🚨 VỊ TRÍ ĐỨT CÁP DỰ KIẾN")
        st.sidebar.markdown(f"**Đoạn cáp:** `{res['cable']}`")
        st.sidebar.info(
            f"🔹 **Từ {res['from']}:** `{res['d1']:.1f} m`\n\n"
            f"🔸 **Từ {res['to']}:** `{res['d2']:.1f} m`"
        )
        if st.session_state.break_gps:
            gps = st.session_state.break_gps
            gmap_url = f"https://www.google.com/maps?q={gps[0]},{gps[1]}"
            st.sidebar.link_button("📍 Mở trên Google Maps", gmap_url, type="primary", use_container_width=True)

    # Dữ liệu Bản đồ
    map_center = [21.0285, 105.8542]
    zoom_lvl = 12

    if st.session_state.break_gps:
        map_center = list(st.session_state.break_gps)
        zoom_lvl = 18
    elif len(node_coords) > 0:
        first_coord = list(node_coords.values())[0]
        map_center = [first_coord[0], first_coord[1]]
        zoom_lvl = 15

    polylines = []
    markers = []
    break_marker = None

    if st.session_state.break_result:
        u = st.session_state.break_result['from']
        v = st.session_state.break_result['to']

        if u in node_coords and v in node_coords:
            polylines.append({
                "coords": [node_coords[u], node_coords[v]],
                "color": "#FF2A6D",
                "weight": 6,
                "opacity": 0.9,
                "tooltip": f"Sự cố đoạn: {st.session_state.break_result['cable']}"
            })

            for node in [u, v]:
                markers.append({
                    "coords": node_coords[node],
                    "popup": f"<b>Điểm Kết Nối:</b> {node}",
                    "tooltip": f"Điểm KN: {node}",
                    "color": "#05D5E7",
                    "radius": 7
                })

        if st.session_state.break_gps:
            res = st.session_state.break_result
            gps = st.session_state.break_gps
            gmap_url = f"https://www.google.com/maps?q={gps[0]},{gps[1]}"
            
            popup_html = f"""
            <div style="font-family: sans-serif; min-width: 180px; color: #1E293B;">
                <b style="color: #E11D48; font-size: 13px;">🚨 VỊ TRÍ ĐỨT CÁP: {res['cable']}</b><br/>
                <div style="margin: 6px 0; font-size: 12px; line-height: 1.4;">
                    • Cách <b>{res['from']}</b>: {res['d1']:.1f}m<br/>
                    • Cách <b>{res['to']}</b>: {res['d2']:.1f}m
                </div>
                <a href="{gmap_url}" target="_blank" style="
                    display: inline-block; width: 100%; text-align: center;
                    background-color: #10B981; color: white; padding: 6px 0;
                    margin-top: 4px; border-radius: 4px; text-decoration: none;
                    font-weight: bold; font-size: 11px;
                ">📍 Mở trên Google Maps</a>
            </div>
            """
            
            break_marker = {
                "coords": list(st.session_state.break_gps),
                "popup": popup_html,
                "tooltip": "🚨 Vị trí đứt cáp"
            }

    else:
        for u, v, data in G.edges(data=True):
            if u in node_coords and v in node_coords:
                polylines.append({
                    "coords": [node_coords[u], node_coords[v]],
                    "color": "#38BDF8",
                    "weight": 3,
                    "opacity": 0.7,
                    "tooltip": f"Cáp: {data.get('cable', '')}"
                })

        for node_id, coord in node_coords.items():
            markers.append({
                "coords": coord,
                "popup": f"<b>Điểm KN:</b> {node_id}",
                "tooltip": str(node_id),
                "color": "#818CF8",
                "radius": 4
            })

    # Leaflet HTML - Chuẩn hóa toàn bộ ngoặc nhọn JS/CSS dạng {{ }}
    polylines_json = json.dumps(polylines)
    markers_json = json.dumps(markers)
    break_marker_json = json.dumps(break_marker)
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
            .leaflet-control-zoom-in, .leaflet-control-zoom-out {{
                color: #F8FAFC !important;
                background-color: #1E293B !important;
            }}
            .custom-break-icon {{
                background-color: #FF2A6D;
                border: 2px solid #FFFFFF;
                border-radius: 50%;
                width: 24px !important;
                height: 24px !important;
                margin-left: -12px !important;
                margin-top: -12px !important;
                box-shadow: 0 0 15px rgba(255, 42, 109, 1);
                animation: pulse 1.2s infinite;
            }}
            @keyframes pulse {{
                0% {{ transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 42, 109, 0.8); }}
                70% {{ transform: scale(1.3); box-shadow: 0 0 0 15px rgba(255, 42, 109, 0); }}
                100% {{ transform: scale(0.9); box-shadow: 0 0 0 0 rgba(255, 42, 109, 0); }}
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
                var darkCarto = L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                    maxZoom: 20, attribution: 'CartoDB Dark'
                }});
                var googleStreets = L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}', {{
                    maxZoom: 20, attribution: 'Google Maps'
                }});
                var googleSat = L.tileLayer('https://mt1.google.com/vt/lyrs=s,h&x={{x}}&y={{y}}&z={{z}}', {{
                    maxZoom: 20, attribution: 'Google Satellite'
                }});

                var map = L.map('map', {{
                    zoomControl: true,
                    attributionControl: false,
                    layers: [darkCarto]
                }}).setView({map_center_json}, {zoom_lvl});

                var baseMaps = {{
                    "🌙 Dark Mode": darkCarto,
                    "🗺️ Google Đường phố": googleStreets,
                    "🛰️ Google Vệ tinh": googleSat
                }};
                L.control.layers(baseMaps, null, {{ position: 'topright' }}).addTo(map);

                var polylinesData = {polylines_json};
                polylinesData.forEach(function(item) {{
                    var line = L.polyline(item.coords, {{
                        color: item.color, weight: item.weight, opacity: item.opacity
                    }}).addTo(map);
                    if (item.tooltip) line.bindTooltip(item.tooltip);
                }});

                var markersData = {markers_json};
                markersData.forEach(function(item) {{
                    var circle = L.circleMarker(item.coords, {{
                        radius: item.radius, color: item.color, fillColor: '#0F172A', fillOpacity: 0.9, weight: 2
                    }}).addTo(map);
                    if (item.popup) circle.bindPopup(item.popup);
                    if (item.tooltip) circle.bindTooltip(item.tooltip);
                }});

                var breakMarkerData = {break_marker_json};
                if (breakMarkerData) {{
                    var breakIcon = L.divIcon({{ className: 'custom-break-icon' }});
                    var bMarker = L.marker(breakMarkerData.coords, {{ icon: breakIcon }}).addTo(map);
                    if (breakMarkerData.popup) bMarker.bindPopup(breakMarkerData.popup).openPopup();
                    if (breakMarkerData.tooltip) bMarker.bindTooltip(breakMarkerData.tooltip);
                }}

                var userMarker = null;
                var accuracyCircle = null;

                function updateLocation(pos) {{
                    var lat = pos.coords.latitude;
                    var lng = pos.coords.longitude;
                    var latlng = [lat, lng];
                    var radius = pos.coords.accuracy / 2;

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
    st.error("❌ Không tìm thấy file Excel trên Server. Vui lòng kiểm tra lại file data trong thư mục.")
