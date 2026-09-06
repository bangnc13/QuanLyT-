import os
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# 1. Cấu hình trang Streamlit
st.set_page_config(
    page_title="Tối Ưu Lộ Trình Di Chuyển Tập Điểm", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# CSS Tùy chỉnh giao diện Fullscreen & Sidebar
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"], .main, .stApp {
            margin: 0 !important;
            padding: 0 !important;
            height: 100vh !important;
            overflow: hidden !important;
        }

        section[data-testid="stSidebar"] {
            z-index: 999999 !important;
        }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        .sidebar-title {
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            color: #1F2937 !important;
            margin-bottom: 2px !important;
        }
        .sidebar-subtitle {
            font-size: 0.8rem !important;
            color: #6B7280 !important;
            margin-bottom: 12px !important;
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
    </style>
""", unsafe_allow_html=True)

# 2. Đọc file Excel dữ liệu điểm
@st.cache_data 
def load_excel_data(): 
    possible_files = [ 
        "QuanLyTĐ.xlsx",
        "QuanLyTD.xlsx",
        "Danh-Sách-Đoạn-Cáp.xlsx",  
        "data.xlsx" 
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

df, file_name = load_excel_data() 

st.sidebar.markdown('<div class="sidebar-title">🗺️ TỐI ƯU LỘ TRÌNH TẬP ĐIỂM</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-subtitle">Tối ưu quãng đường thu cước - Make by BangNC13 </div>', unsafe_allow_html=True)

# Khởi tạo session state kích hoạt tối ưu từ sidebar
if "trigger_optimize" not in st.session_state:
    st.session_state.trigger_optimize = False

if df is not None: 
    df.columns = [str(col).strip() for col in df.columns] 
    
    # Tìm tự động các cột Tên điểm, Vĩ độ (Lat), Kinh độ (Lng)
    name_col = next((c for c in df.columns if any(k in c.lower() for k in ['tên', 'điểm', 'kn', 'station', 'name'])), df.columns[0])
    lat_col = next((c for c in df.columns if any(k in c.lower() for k in ['lat', 'vĩ độ', 'vi do'])), None) 
    lon_col = next((c for c in df.columns if any(k in c.lower() for k in ['lng', 'lon', 'kinh độ', 'kinh do'])), None) 

    points_dict = {}
    if lat_col and lon_col:
        for _, row in df.iterrows():
            p_name = str(row[name_col]).strip()
            try:
                if pd.notnull(row[lat_col]) and pd.notnull(row[lon_col]):
                    points_dict[p_name] = {
                        "lat": float(row[lat_col]),
                        "lng": float(row[lon_col])
                    }
            except Exception:
                pass
    else:
        lat_col1 = next((c for c in df.columns if 'lat' in c.lower() and '1' in c.lower()), None) 
        lon_col1 = next((c for c in df.columns if ('lng' in c.lower() or 'lon' in c.lower()) and '1' in c.lower()), None)
        k1_col = next((c for c in df.columns if 'kn1' in c.lower() or 'điểm 1' in c.lower()), name_col)
        
        if lat_col1 and lon_col1:
            for _, row in df.iterrows():
                p_name = str(row[k1_col]).strip()
                try:
                    if pd.notnull(row[lat_col1]) and pd.notnull(row[lon_col1]):
                        points_dict[p_name] = {
                            "lat": float(row[lat_col1]),
                            "lng": float(row[lon_col1])
                        }
                except Exception:
                    pass

    all_point_names = sorted(list(points_dict.keys()))
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 CHỌN CÁC TẬP ĐIỂM CẦN ĐẾN")
    
    selected_points = st.sidebar.multiselect(
        "Chọn các điểm cần đi qua:",
        options=all_point_names,
        default=all_point_names[:5] if len(all_point_names) >= 5 else all_point_names,
        help="Thứ tự tối ưu sẽ được tự động tính toán dựa theo vị trí GPS xuất phát của bạn."
    )

    selected_data = []
    for p in selected_points:
        selected_data.append({
            "name": p,
            "lat": points_dict[p]["lat"],
            "lng": points_dict[p]["lng"]
        })

    st.sidebar.info(f"Đã chọn **{len(selected_data)}** tập điểm.")

    # 🔘 NÚT TỐI ƯU LỘ TRÌNH TRÊN SIDEBAR
    if st.sidebar.button("🚀 Tối ưu lộ trình di chuyển", type="primary", use_container_width=True):
        st.session_state.trigger_optimize = True

    map_center = [21.0285, 105.8542]
    if len(selected_data) > 0:
        map_center = [selected_data[0]["lat"], selected_data[0]["lng"]]

    # Giao diện Leaflet JS + GPS Realtime + Đánh số thứ tự + Tối ưu lộ trình
    leaflet_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        
        <!-- Leaflet CSS & JS -->
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

        <!-- Leaflet Routing Machine CSS & JS -->
        <link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.css" />
        <script src="https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.js"></script>

        <style>
            html, body {{
                width: 100%;
                height: 100vh;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }}
            #map {{
                width: 100%;
                height: 100vh;
                background: #e5e3df;
            }}
            .user-location-marker {{
                background-color: #2563EB;
                border: 3px solid #FFFFFF;
                border-radius: 50%;
                width: 20px !important;
                height: 20px !important;
                margin-left: -10px !important;
                margin-top: -10px !important;
                box-shadow: 0 0 10px rgba(37, 99, 235, 0.8);
            }}
            /* CSS Đánh số thứ tự các điểm trên bản đồ */
            .number-icon {{
                background-color: #EF4444;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
                border-radius: 50%;
                font-weight: bold;
                font-size: 13px;
                text-align: center;
                line-height: 22px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.4);
            }}
            .start-end-icon {{
                background-color: #10B981;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
                border-radius: 50%;
                font-weight: bold;
                font-size: 12px;
                text-align: center;
                line-height: 22px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.4);
            }}
            .leaflet-control-btn {{
                background-color: #ffffff;
                border: 2px solid rgba(0,0,0,0.2);
                border-radius: 6px;
                padding: 6px 12px;
                cursor: pointer;
                font-size: 13px;
                font-weight: bold;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            .leaflet-control-btn:hover {{
                background-color: #f4f4f4;
            }}
            .leaflet-routing-container {{
                background: white !important;
                padding: 10px !important;
                border-radius: 8px !important;
                max-height: 280px !important;
                overflow-y: auto !important;
                font-size: 12px !important;
            }}
            .leaflet-bottom {{
                margin-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                var googleStreets = L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}', {{
                    maxZoom: 20,
                    attribution: 'Google Maps'
                }});

                var googleSat = L.tileLayer('https://mt1.google.com/vt/lyrs=s,h&x={{x}}&y={{y}}&z={{z}}', {{
                    maxZoom: 20,
                    attribution: 'Google Maps Satellite'
                }});

                var map = L.map('map', {{
                    zoomControl: false,
                    attributionControl: false,
                    layers: [googleStreets]
                }}).setView({json.dumps(map_center)}, 14);

                L.control.zoom({{ position: 'bottomleft' }}).addTo(map);
                L.control.layers({{ "🗺️ Đường phố": googleStreets, "🛰️ Vệ tinh": googleSat }}, null, {{ position: 'bottomright' }}).addTo(map);

                var targets = {json.dumps(selected_data)};
                var markersGroup = L.layerGroup().addTo(map);

                // Vẽ các điểm ban đầu
                function renderInitialMarkers() {{
                    markersGroup.clearLayers();
                    targets.forEach(function(pt) {{
                        var marker = L.circleMarker([pt.lat, pt.lng], {{
                            radius: 8,
                            color: '#EF4444',
                            fillColor: '#FFFFFF',
                            fillOpacity: 0.9,
                            weight: 3
                        }});
                        marker.bindPopup("<b>Tập điểm:</b> " + pt.name);
                        marker.bindTooltip(pt.name, {{ permanent: false, direction: 'top' }});
                        markersGroup.addLayer(marker);
                    }});
                }}
                renderInitialMarkers();

                // Định vị GPS
                var userLatLng = null;
                var userMarker = null;
                var accuracyCircle = null;

                function onLocationFound(e) {{
                    userLatLng = e.latlng;
                    var radius = e.accuracy / 2;

                    if (userMarker) {{
                        userMarker.setLatLng(e.latlng);
                        accuracyCircle.setLatLng(e.latlng).setRadius(radius);
                    }} else {{
                        var userIcon = L.divIcon({{ className: 'user-location-marker' }});
                        userMarker = L.marker(e.latlng, {{ icon: userIcon }}).addTo(map)
                            .bindPopup("<b>Vị trí xuất phát của bạn (GPS)</b>");
                        accuracyCircle = L.circle(e.latlng, radius, {{
                            color: '#2563EB',
                            fillColor: '#3B82F6',
                            fillOpacity: 0.15,
                            weight: 1
                        }}).addTo(map);
                    }}
                }}

                map.on('locationfound', onLocationFound);
                map.on('locationerror', function(e) {{
                    console.log("GPS Error: " + e.message);
                }});
                map.locate({{ watch: true, setView: false, enableHighAccuracy: true }});

                // Thuật toán Haversine
                function getDistance(lat1, lon1, lat2, lon2) {{
                    var R = 6371;
                    var dLat = (lat2 - lat1) * Math.PI / 180;
                    var dLon = (lon2 - lon1) * Math.PI / 180;
                    var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                            Math.sin(dLon/2) * Math.sin(dLon/2);
                    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
                    return R * c;
                }}

                // Giải bài toán TSP
                function solveTSP(startPt, pts) {{
                    var unvisited = pts.slice();
                    var route = [startPt];
                    var current = startPt;

                    while (unvisited.length > 0) {{
                        var nearestIdx = 0;
                        var minDst = Infinity;

                        for (var i = 0; i < unvisited.length; i++) {{
                            var dst = getDistance(current.lat, current.lng, unvisited[i].lat, unvisited[i].lng);
                            if (dst < minDst) {{
                                minDst = dst;
                                nearestIdx = i;
                            }}
                        }}

                        current = unvisited[nearestIdx];
                        route.push(current);
                        unvisited.splice(nearestIdx, 1);
                    }}

                    // Quay về điểm GPS ban đầu
                    route.push(startPt);
                    return route;
                }}

                var routingControl = null;

                function optimizeAndRoute() {{
                    if (!userLatLng) {{
                        alert("Đang bắt tín hiệu GPS... Vui lòng bật quyền vị trí trên trình duyệt và thử lại.");
                        return;
                    }}

                    if (targets.length === 0) {{
                        alert("Vui lòng chọn ít nhất 1 tập điểm ở Sidebar.");
                        return;
                    }}

                    var startPoint = {{ name: "Điểm Xuất Phát (GPS)", lat: userLatLng.lat, lng: userLatLng.lng }};
                    var optimizedRoute = solveTSP(startPoint, targets);

                    // Xóa marker cũ và thay bằng Marker có ĐÁNH SỐ THỨ TỰ
                    markersGroup.clearLayers();

                    optimizedRoute.forEach(function(pt, idx) {{
                        var iconClass = 'number-icon';
                        var labelText = idx.toString();

                        if (idx === 0) {{
                            labelText = '🏁';
                            iconClass = 'start-end-icon';
                        }} else if (idx === optimizedRoute.length - 1) {{
                            return; // Điểm cuối trùng điểm xuất phát
                        }}

                        var numIcon = L.divIcon({{
                            className: iconClass,
                            html: labelText,
                            iconSize: [26, 26],
                            iconAnchor: [13, 13]
                        }});

                        var m = L.marker([pt.lat, pt.lng], {{ icon: numIcon }});
                        var popupMsg = idx === 0 ? "<b>Điểm Xuất Phát (GPS)</b>" : "<b>Thứ tự " + idx + ":</b> " + pt.name;
                        m.bindPopup(popupMsg);
                        m.bindTooltip(idx === 0 ? "Xuất phát (GPS)" : "Thứ tự " + idx + ": " + pt.name, {{ permanent: true, direction: 'top' }});
                        markersGroup.addLayer(m);
                    }});

                    var waypoints = optimizedRoute.map(function(pt) {{
                        return L.latLng(pt.lat, pt.lng);
                    }});

                    if (routingControl) {{
                        map.removeControl(routingControl);
                    }}

                    routingControl = L.Routing.control({{
                        waypoints: waypoints,
                        routeWhileDragging: false,
                        addWaypoints: false,
                        show: true,
                        lineOptions: {{
                            styles: [{{ color: '#10B981', opacity: 0.85, weight: 6 }}]
                        }}
                    }}).addTo(map);
                }}

                // Nút điều khiển nhanh góc trên trái
                var CustomControls = L.Control.extend({{
                    options: {{ position: 'topleft' }},
                    onAdd: function (map) {{
                        var container = L.DomUtil.create('div', 'leaflet-bar');
                        container.style.display = 'flex';
                        container.style.flexDirection = 'column';
                        container.style.gap = '6px';

                        var btnLocate = L.DomUtil.create('div', 'leaflet-control-btn', container);
                        btnLocate.innerHTML = '🎯 GPS của tôi';
                        btnLocate.onclick = function() {{
                            if (userLatLng) {{
                                map.setView(userLatLng, 17);
                            }} else {{
                                map.locate({{ setView: true, maxZoom: 17, enableHighAccuracy: true }});
                            }}
                        }};

                        var btnRoute = L.DomUtil.create('div', 'leaflet-control-btn', container);
                        btnRoute.innerHTML = '🚀 Tối ưu lộ trình di chuyển';
                        btnRoute.style.backgroundColor = '#10B981';
                        btnRoute.style.color = '#FFFFFF';
                        btnRoute.onclick = function() {{
                            optimizeAndRoute();
                        }};

                        return container;
                    }}
                }});

                map.addControl(new CustomControls());

                // Tự động kích hoạt khi bấm nút trên Sidebar
                var autoOptimize = {json.dumps(st.session_state.trigger_optimize)};
                if (autoOptimize) {{
                    setTimeout(function() {{
                        optimizeAndRoute();
                    }}, 800);
                }}
            }});
        </script>
    </body>
    </html>
    """

    components.html(leaflet_html, height=1000, scrolling=False)

else:
    st.warning("⚠️ Không tìm thấy tệp dữ liệu Excel `.xlsx` hoặc `.xls` trong thư mục làm việc.")
