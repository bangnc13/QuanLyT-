import json
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# 1. Cấu hình trang Streamlit
st.set_page_config(
    page_title="Tối Ưu Lộ Trình Di Chuyển Tập Điểm",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS Tùy chỉnh giao diện Fullscreen, Sidebar Trong Suốt, Logo Trong Suốt & Nút bấm Toggle xanh Neon
st.markdown(
    """
    <style>
        /* ========================================================= */
        /* 0. ẨN TẤT CẢ ICON THANH TRÊN, FOOTER VÀ WATERMARK/BADGE CỦA STREAMLIT */
        /* ========================================================= */
        header[data-testid="stHeader"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        footer,
        #MainMenu,
        .viewerBadge_container__163Vn,
        .styles_viewerBadge__1yB5_,
        [data-testid="stStatusWidget"],
        [data-testid="stConnectionStatus"],
        .stAppViewBlockContainer iframe,
        div[class*="viewerBadge"],
        div[class*="styles_viewerBadge"],
        a[href*="streamlit.io"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            height: 0px !important;
            width: 0px !important;
            pointer-events: none !important;
        }

        /* Ẩn triệt để các phần tử cố định ở góc dưới màn hình */
        div[style*="position: fixed"][style*="bottom"],
        div[style*="position: absolute"][style*="bottom"] {
            z-index: -999999 !important;
        }

        /* ========================================================= */
        /* 1. Thiết lập tràn màn hình tuyệt đối */
        /* ========================================================= */
        html, body, [data-testid="stAppViewContainer"], .main, .stApp {
            margin: 0 !important;
            padding: 0 !important;
            height: 100vh !important;
            overflow: hidden !important;
            background-color: transparent !important;
        }

        /* 2. LÀM TRONG SUỐT VÀ MỜ KÍNH CHO SIDEBAR (MENU) */
        section[data-testid="stSidebar"] {
            z-index: 999999 !important;
            background-color: rgba(255, 255, 255, 0.4) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.3) !important;
            box-shadow: 4px 0 15px rgba(0, 0, 0, 0.05) !important;
        }

        /* Điều chỉnh container bên trong Sidebar */
        section[data-testid="stSidebar"] > div:first-child {
            background: transparent !important;
            padding-top: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }

        /* 3. LÀM NỀN LOGO TRONG SUỐT HOÀN TOÀN */
        [data-testid="stSidebar"] [data-testid="stImage"] {
            background: transparent !important;
            backdrop-filter: none !important;
            -webkit-backdrop-filter: none !important;
            border-radius: 0px !important;
            padding: 0px !important;
            margin-bottom: 12px !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stImage"] img {
            background: transparent !important;
            border-radius: 0px !important;
            object-fit: contain !important;
        }

        /* 4. BO TRÒN VÀ MÀU XANH NEON CHO NÚT MỞ/ẨN SIDEBAR CỦA STREAMLIT */
        [data-testid="stSidebarCollapseButton"], 
        [data-testid="stSidebarNavItems"] button,
        button[aria-label="Close sidebar"],
        button[aria-label="Open sidebar"] {
            background-color: #00FF66 !important;
            color: #000000 !important;
            border-radius: 20px !important;
            border: 2px solid #00FF66 !important;
            box-shadow: 0 0 12px #00FF66, 0 0 20px rgba(0, 255, 102, 0.6) !important;
            transition: all 0.3s ease !important;
        }
        [data-testid="stSidebarCollapseButton"]:hover {
            background-color: #00CC52 !important;
            box-shadow: 0 0 18px #00FF66, 0 0 30px rgba(0, 255, 102, 0.9) !important;
            transform: scale(1.05);
        }

        .sidebar-title {
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            color: #111827 !important;
            margin-bottom: 2px !important;
        }
        .sidebar-subtitle {
            font-size: 0.8rem !important;
            color: #374151 !important;
            margin-bottom: 12px !important;
            font-weight: 500 !important;
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
""",
    unsafe_allow_html=True,
)


# 2. Đọc file Excel dữ liệu điểm
@st.cache_data
def load_excel_data():
    possible_files = [
        "QuanLyTĐ.xlsx",
        "QuanLyTD.xlsx",
        "Danh-Sách-Đoạn-Cáp.xlsx",
        "data.xlsx",
    ]

    selected_file = None
    for f in possible_files:
        if os.path.exists(f):
            selected_file = f
            break

    if not selected_file:
        files = [
            f
            for f in os.listdir(".")
            if f.endswith(".xlsx") or f.endswith(".xls")
        ]
        if files:
            selected_file = files[0]

    if selected_file:
        df = pd.read_excel(selected_file)
        return df, selected_file
    return None, None


df, file_name = load_excel_data()

# -------------------------------------------------------------
# LOGO VÀO TRÊN CÙNG SIDEBAR CÓ NỀN TRONG SUỐT
# -------------------------------------------------------------
if os.path.exists("FPT_Telecom_logo.png"):
    st.sidebar.image("FPT_Telecom_logo.png", use_container_width=True)
else:
    st.sidebar.caption("📷 *[FPT Telecom Logo]*")

st.sidebar.markdown(
    '<div class="sidebar-title"></div>', unsafe_allow_html=True
)
st.sidebar.markdown(
    '<div class="sidebar-subtitle"> Make by BangNC13 </div>',
    unsafe_allow_html=True,
)

# Khởi tạo session state kích hoạt tối ưu từ sidebar
if "trigger_optimize" not in st.session_state:
    st.session_state.trigger_optimize = False

if df is not None:
    df.columns = [str(col).strip() for col in df.columns]

    # Tìm tự động các cột Tên điểm, Vĩ độ (Lat), Kinh độ (Lng)
    name_col = next(
        (
            c
            for c in df.columns
            if any(k in c.lower() for k in ["tên", "điểm", "kn", "station", "name"])
        ),
        df.columns[0],
    )
    lat_col = next(
        (
            c
            for c in df.columns
            if any(k in c.lower() for k in ["lat", "vĩ độ", "vi do"])
        ),
        None,
    )
    lon_col = next(
        (
            c
            for c in df.columns
            if any(k in c.lower() for k in ["lng", "lon", "kinh độ", "kinh do"])
        ),
        None,
    )

    points_dict = {}
    if lat_col and lon_col:
        for _, row in df.iterrows():
            p_name = str(row[name_col]).strip()
            try:
                if pd.notnull(row[lat_col]) and pd.notnull(row[lon_col]):
                    points_dict[p_name] = {
                        "lat": float(row[lat_col]),
                        "lng": float(row[lon_col]),
                    }
            except Exception:
                pass
    else:
        lat_col1 = next(
            (
                c
                for c in df.columns
                if "lat" in c.lower() and "1" in c.lower()
            ),
            None,
        )
        lon_col1 = next(
            (
                c
                for c in df.columns
                if ("lng" in c.lower() or "lon" in c.lower()) and "1" in c.lower()
            ),
            None,
        )
        k1_col = next(
            (c for c in df.columns if "kn1" in c.lower() or "điểm 1" in c.lower()),
            name_col,
        )

        if lat_col1 and lon_col1:
            for _, row in df.iterrows():
                p_name = str(row[k1_col]).strip()
                try:
                    if pd.notnull(row[lat_col1]) and pd.notnull(row[lon_col1]):
                        points_dict[p_name] = {
                            "lat": float(row[lat_col1]),
                            "lng": float(row[lon_col1]),
                        }
                except Exception:
                    pass

    all_point_names = sorted(list(points_dict.keys()))

    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 CHỌN CÁC TẬP ĐIỂM CẦN ĐẾN")

    selected_points = st.sidebar.multiselect(
        "Chọn các điểm cần đi qua:",
        options=all_point_names,
        default=(
            all_point_names[:5]
            if len(all_point_names) >= 5
            else all_point_names
        ),
        help=(
            "Thứ tự tối ưu sẽ được tự động tính toán dựa theo vị trí GPS xuất"
            " phát của bạn."
        ),
    )

    selected_data = []
    for p in selected_points:
        selected_data.append({
            "name": p,
            "lat": points_dict[p]["lat"],
            "lng": points_dict[p]["lng"],
        })

    st.sidebar.info(f"Đã chọn **{len(selected_data)}** tập điểm.")

    # 🔘 NÚT TỐI ƯU LỘ TRÌNH TRÊN SIDEBAR
    if st.sidebar.button(
        "🚀 Tối ưu lộ trình di chuyển", type="primary", use_container_width=True
    ):
        st.session_state.trigger_optimize = True

    map_center = [21.0285, 105.8542]
    if len(selected_data) > 0:
        map_center = [selected_data[0]["lat"], selected_data[0]["lng"]]

    # Giao diện Leaflet JS + GPS Realtime + Đánh số thứ tự + Tối ưu lộ trình + Google Maps
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

            /* ẨN TOÀN BỘ CÁC BIỂU TƯỢNG VÀ NÚT Ở GÓC DƯỚI BÊN PHẢI BẢN ĐỒ */
            .leaflet-bottom.leaflet-right {{
                display: none !important;
                visibility: hidden !important;
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

            .leaflet-top.leaflet-left {{
                top: 15px !important;
                left: 10px !important;
            }}

            .custom-btn-container {{
                display: flex !important;
                flex-direction: row !important;
                gap: 8px !important;
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
                flex-wrap: wrap !important;
            }}

            .leaflet-control-btn {{
                border-radius: 20px !important;
                padding: 7px 14px;
                cursor: pointer;
                font-size: 13px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
                white-space: nowrap;
                transition: all 0.3s ease;
            }}
            .leaflet-control-btn:hover {{
                transform: translateY(-2px);
            }}

            /* 1. NÚT GPS: NỀN XANH DƯƠNG */
            .btn-blue-neon {{
                background-color: #0066FF !important;
                color: #FFFFFF !important;
                border: 2px solid #3399FF !important;
                box-shadow: 0 0 10px #0066FF, 0 0 18px rgba(51, 153, 255, 0.8) !important;
            }}
            .btn-blue-neon:hover {{
                background-color: #0052CC !important;
                box-shadow: 0 0 15px #0066FF, 0 0 25px rgba(51, 153, 255, 1) !important;
            }}

            /* 2. NÚT TỐI ƯU LỘ TRÌNH: NỀN CAM */
            .btn-orange-neon {{
                background-color: #FF6600 !important;
                color: #FFFFFF !important;
                border: 2px solid #FF9933 !important;
                box-shadow: 0 0 10px #FF6600, 0 0 18px rgba(255, 153, 51, 0.8) !important;
            }}
            .btn-orange-neon:hover {{
                background-color: #CC5200 !important;
                box-shadow: 0 0 15px #FF6600, 0 0 25px rgba(255, 153, 51, 1) !important;
            }}

            /* 3. NÚT GOOGLE MAPS: NỀN ĐỎ NEON */
            .btn-gmaps-neon {{
                background-color: #EA4335 !important;
                color: #FFFFFF !important;
                border: 2px solid #FF7769 !important;
                box-shadow: 0 0 10px #EA4335, 0 0 18px rgba(234, 67, 53, 0.8) !important;
            }}
            .btn-gmaps-neon:hover {{
                background-color: #C5221F !important;
                box-shadow: 0 0 15px #EA4335, 0 0 25px rgba(234, 67, 53, 1) !important;
            }}

            /* 4. NÚT MENU: NỀN XANH LÁ */
            .btn-green-neon {{
                background-color: #00CC44 !important;
                color: #FFFFFF !important;
                border: 2px solid #33FF66 !important;
                box-shadow: 0 0 10px #00CC44, 0 0 18px rgba(51, 255, 102, 0.8) !important;
            }}
            .btn-green-neon:hover {{
                background-color: #009933 !important;
                box-shadow: 0 0 15px #00CC44, 0 0 25px rgba(51, 255, 102, 1) !important;
            }}

            .leaflet-routing-container {{
                display: none !important;
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

                var map = L.map('map', {{
                    zoomControl: false,
                    attributionControl: false,
                    layers: [googleStreets]
                }}).setView({json.dumps(map_center)}, 14);

                L.control.zoom({{ position: 'bottomleft' }}).addTo(map);

                var targets = {json.dumps(selected_data)};
                var markersGroup = L.layerGroup().addTo(map);

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
                        markersGroup.addLayer(marker);
                    }});
                }}
                renderInitialMarkers();

                // Định vị GPS
                var userLatLng = null;
                var userMarker = null;
                var accuracyCircle = null;
                var autoOptimizeTriggered = false;

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

                    var autoOptimize = {json.dumps(st.session_state.trigger_optimize)};
                    if (autoOptimize && !autoOptimizeTriggered) {{
                        autoOptimizeTriggered = true;
                        optimizeAndRoute(true);
                    }}
                }}

                map.on('locationfound', onLocationFound);
                map.on('locationerror', function(e) {{
                    console.log("GPS Error: " + e.message);
                }});
                map.locate({{ watch: true, setView: false, enableHighAccuracy: true }});

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

                    route.push(startPt);
                    return route;
                }}

                var routingControl = null;
                var currentOptimizedRoute = null;

                function optimizeAndRoute(isAuto) {{
                    if (!userLatLng) {{
                        if (!isAuto) {{
                            alert("Đang bắt tín hiệu GPS... Vui lòng bật quyền vị trí trên trình duyệt và thử lại.");
                        }}
                        return;
                    }}

                    if (targets.length === 0) {{
                        alert("Vui lòng chọn ít nhất 1 tập điểm ở Sidebar.");
                        return;
                    }}

                    var startPoint = {{ name: "Điểm Xuất Phát (GPS)", lat: userLatLng.lat, lng: userLatLng.lng }};
                    currentOptimizedRoute = solveTSP(startPoint, targets);

                    markersGroup.clearLayers();

                    currentOptimizedRoute.forEach(function(pt, idx) {{
                        var iconClass = 'number-icon';
                        var labelText = idx.toString();

                        if (idx === 0) {{
                            labelText = '🏁';
                            iconClass = 'start-end-icon';
                        }} else if (idx === currentOptimizedRoute.length - 1) {{
                            return;
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
                        markersGroup.addLayer(m);
                    }});

                    var waypoints = currentOptimizedRoute.map(function(pt) {{
                        return L.latLng(pt.lat, pt.lng);
                    }});

                    if (routingControl) {{
                        map.removeControl(routingControl);
                    }}

                    routingControl = L.Routing.control({{
                        waypoints: waypoints,
                        routeWhileDragging: false,
                        addWaypoints: false,
                        show: false,
                        createMarker: function() {{ return null; }},
                        lineOptions: {{
                            styles: [{{ color: '#FF6600', opacity: 0.85, weight: 6 }}]
                        }}
                    }}).addTo(map);
                }}

                // Hàm mở Google Maps với lộ trình đã được sắp xếp
                function openGoogleMaps() {{
                    if (targets.length === 0) {{
                        alert("Vui lòng chọn ít nhất 1 tập điểm.");
                        return;
                    }}

                    var routePoints = [];

                    if (currentOptimizedRoute && currentOptimizedRoute.length > 0) {{
                        routePoints = currentOptimizedRoute.slice(0, currentOptimizedRoute.length - 1);
                    }} else {{
                        if (userLatLng) {{
                            routePoints.push({{ lat: userLatLng.lat, lng: userLatLng.lng }});
                        }}
                        targets.forEach(function(pt) {{ routePoints.push(pt); }});
                    }}

                    if (routePoints.length < 2) {{
                        alert("Không đủ điểm để tạo lộ trình trên Google Maps.");
                        return;
                    }}

                    var origin = routePoints[0].lat + "," + routePoints[0].lng;
                    var destination = routePoints[routePoints.length - 1].lat + "," + routePoints[routePoints.length - 1].lng;
                    
                    var waypointsArr = [];
                    for (var i = 1; i < routePoints.length - 1; i++) {{
                        waypointsArr.push(routePoints[i].lat + "," + routePoints[i].lng);
                    }}

                    var mapsUrl = "https://www.google.com/maps/dir/?api=1" +
                        "&origin=" + encodeURIComponent(origin) +
                        "&destination=" + encodeURIComponent(destination);

                    if (waypointsArr.length > 0) {{
                        mapsUrl += "&waypoints=" + encodeURIComponent(waypointsArr.join("|"));
                    }}

                    mapsUrl += "&travelmode=driving";

                    window.open(mapsUrl, '_blank');
                }}

                var CustomControls = L.Control.extend({{
                    options: {{ position: 'topleft' }},
                    onAdd: function (map) {{
                        var container = L.DomUtil.create('div', 'custom-btn-container');

                        // 1. Nút GPS
                        var btnLocate = L.DomUtil.create('div', 'leaflet-control-btn btn-blue-neon', container);
                        btnLocate.innerHTML = '🎯 GPS';
                        btnLocate.onclick = function() {{
                            if (userLatLng) {{
                                map.setView(userLatLng, 17);
                            }} else {{
                                map.locate({{ setView: true, maxZoom: 17, enableHighAccuracy: true }});
                            }}
                        }};

                        // 2. Nút Tối ưu lộ trình
                        var btnRoute = L.DomUtil.create('div', 'leaflet-control-btn btn-orange-neon', container);
                        btnRoute.innerHTML = '🚀 Tối ưu lộ trình';
                        btnRoute.onclick = function() {{
                            optimizeAndRoute(false);
                        }};

                        // 3. Nút Google Maps
                        var btnGmaps = L.DomUtil.create('div', 'leaflet-control-btn btn-gmaps-neon', container);
                        btnGmaps.innerHTML = '🗺️ Google Maps';
                        btnGmaps.onclick = function() {{
                            openGoogleMaps();
                        }};

                        // 4. Nút Menu Sidebar
                        var btnToggleSidebar = L.DomUtil.create('div', 'leaflet-control-btn btn-green-neon', container);
                        btnToggleSidebar.innerHTML = '👁️ Menu';
                        btnToggleSidebar.onclick = function() {{
                            var sidebarBtn = window.parent.document.querySelector('[data-testid="stSidebarCollapseButton"] button') ||
                                             window.parent.document.querySelector('button[aria-label="Close sidebar"]') ||
                                             window.parent.document.querySelector('button[aria-label="Open sidebar"]');
                            if (sidebarBtn) {{
                                sidebarBtn.click();
                            }}
                        }};

                        return container;
                    }}
                }});

                map.addControl(new CustomControls());

                var autoOptimize = {json.dumps(st.session_state.trigger_optimize)};
                if (autoOptimize) {{
                    setTimeout(function() {{
                        if (!autoOptimizeTriggered && !userLatLng) {{
                            alert("Đang bắt tín hiệu GPS... Vui lòng kiểm tra quyền truy cập vị trí trên trình duyệt và thử lại.");
                        }}
                    }}, 8000);
                }}
            }});
        </script>
    </body>
    </html>
    """

    components.html(leaflet_html, height=1000, scrolling=False)

    st.session_state.trigger_optimize = False

else:
    st.warning(
        "⚠️ Không tìm thấy tệp dữ liệu Excel `.xlsx` hoặc `.xls` trong thư mục"
        " làm việc."
    )
