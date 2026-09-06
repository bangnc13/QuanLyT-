import json
import os
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# 1. Cấu hình trang Streamlit
st.set_page_config(
    page_title="Tối Ưu Lộ Trình Di Chuyển",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS Tùy chỉnh tràn màn hình & ẩn các phần thừa của Streamlit
st.markdown(
    """
    <style>
        /* Ẩn Header, Footer, Toolbar của Streamlit */
        header[data-testid="stHeader"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        footer, #MainMenu,
        [data-testid="stStatusWidget"],
        [data-testid="stConnectionStatus"],
        a[href*="streamlit.io"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            height: 0px !important;
        }

        /* Fullscreen tuyệt đối cho ứng dụng */
        html, body, [data-testid="stAppViewContainer"], .main, .stApp {
            margin: 0 !important;
            padding: 0 !important;
            height: 100vh !important;
            width: 100vw !important;
            overflow: hidden !important;
            background-color: #000 !important;
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

points_dict = {}

if df is not None:
    df.columns = [str(col).strip() for col in df.columns]

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

if points_dict:
    # Chuẩn bị dữ liệu gửi trực tiếp sang Leaflet HTML
    points_json = json.dumps(points_dict, ensure_ascii=False)

    leaflet_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        
        <!-- Leaflet CSS & JS -->
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

        <!-- Leaflet Routing Machine -->
        <link rel="stylesheet" href="https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.css" />
        <script src="https://unpkg.com/leaflet-routing-machine@3.2.12/dist/leaflet-routing-machine.js"></script>

        <style>
            html, body {{
                width: 100%;
                height: 100vh;
                margin: 0;
                padding: 0;
                overflow: hidden;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }}
            #map {{
                width: 100%;
                height: 100vh;
                background: #e5e3df;
            }}

            /* Khung điều khiển nổi trên bản đồ dành riêng cho điện thoại */
            .mobile-panel {{
                position: absolute;
                top: 10px;
                left: 10px;
                right: 10px;
                z-index: 9999;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 14px;
                padding: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.25);
                max-height: 85vh;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}

            .panel-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-weight: bold;
                font-size: 14px;
                color: #111827;
            }}

            .author-tag {{
                font-size: 11px;
                color: #6B7280;
                font-weight: normal;
            }}

            /* Khung tìm kiếm và chọn danh sách dạng Native HTML */
            .select-container {{
                position: relative;
                width: 100%;
            }}

            .search-input {{
                width: 100%;
                padding: 10px 12px;
                border: 2px solid #0066FF;
                border-radius: 8px;
                font-size: 14px;
                box-sizing: border-box;
                outline: none;
            }}

            /* Danh sách gợi ý xổ xuống tự tạo - không bao giờ bị che */
            .dropdown-list {{
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: #ffffff;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                max-height: 220px;
                overflow-y: auto;
                z-index: 10000;
                display: none;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                margin-top: 4px;
            }}

            .dropdown-item {{
                padding: 10px 12px;
                font-size: 13px;
                cursor: pointer;
                border-bottom: 1px solid #F3F4F6;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}

            .dropdown-item:active, .dropdown-item:hover {{
                background-color: #EFF6FF;
                color: #0066FF;
            }}

            /* Các Chip điểm đã chọn */
            .selected-chips {{
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
                max-height: 90px;
                overflow-y: auto;
                padding: 2px;
            }}

            .chip {{
                background: #0066FF;
                color: white;
                padding: 4px 10px;
                border-radius: 16px;
                font-size: 12px;
                display: flex;
                align-items: center;
                gap: 6px;
                font-weight: 500;
            }}

            .chip-remove {{
                cursor: pointer;
                font-weight: bold;
                background: rgba(255,255,255,0.3);
                border-radius: 50%;
                width: 16px;
                height: 16px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 10px;
            }}

            /* Hàng nút bấm hành động */
            .btn-group {{
                display: flex;
                gap: 6px;
                margin-top: 4px;
            }}

            .btn {{
                flex: 1;
                padding: 10px 6px;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                color: white;
                cursor: pointer;
                text-align: center;
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            }}

            .btn-orange {{ background: #FF6600; }}
            .btn-purple {{ background: #8B5CF6; }}
            .btn-blue {{ background: #2563EB; }}

            /* Style Marker GPS và thứ tự */
            .user-location-marker {{
                background-color: #2563EB;
                border: 3px solid #FFFFFF;
                border-radius: 50%;
                width: 18px !important;
                height: 18px !important;
                box-shadow: 0 0 10px rgba(37, 99, 235, 0.8);
            }}

            .number-icon {{
                background-color: #EF4444;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
                border-radius: 50%;
                font-weight: bold;
                font-size: 12px;
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
                font-size: 11px;
                text-align: center;
                line-height: 22px;
            }}

            .leaflet-routing-container {{ display: none !important; }}
        </style>
    </head>
    <body>

        <div class="mobile-panel">
            <div class="panel-header">
                <span>📍 CHỌN TẬP ĐIỂM</span>
                <span class="author-tag">Make by BangNC13</span>
            </div>

            <!-- Khung tìm kiếm điểm -->
            <div class="select-container">
                <input type="text" id="searchInput" class="search-input" placeholder="🔍 Gõ tên tập điểm để tìm kiếm..." autocomplete="off">
                <div id="dropdownList" class="dropdown-list"></div>
            </div>

            <!-- Khung chứa các điểm đã chọn -->
            <div id="selectedChips" class="selected-chips"></div>

            <!-- Thanh Nút Thao Tác -->
            <div class="btn-group">
                <button class="btn btn-blue" onclick="locateUser()">🎯 GPS</button>
                <button class="btn btn-orange" onclick="optimizeAndRoute()">🚀 Tối Ưu Lộ Trình</button>
                <button class="btn btn-purple" onclick="openGoogleMaps()">🗺️ Google Maps</button>
            </div>
        </div>

        <div id="map"></div>

        <script>
            var allPoints = {points_json};
            var selectedNames = [];

            // Mặc định chọn 5 điểm đầu tiên làm mẫu
            var keys = Object.keys(allPoints);
            if (keys.length > 0) {{
                selectedNames = keys.slice(0, Math.min(5, keys.length));
            }}

            var map = L.map('map', {{ zoomControl: false, attributionControl: false }}).setView([21.0285, 105.8542], 13);
            L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}', {{ maxZoom: 20 }}).addTo(map);

            var markersGroup = L.layerGroup().addTo(map);
            var userLatLng = null;
            var userMarker = null;
            var routingControl = null;
            var currentOptimizedRoute = null;

            // Xử lý Tìm kiếm & Dropdown
            var searchInput = document.getElementById('searchInput');
            var dropdownList = document.getElementById('dropdownList');
            var selectedChipsContainer = document.getElementById('selectedChips');

            function renderDropdown(filterText) {{
                dropdownList.innerHTML = '';
                var count = 0;
                var filter = filterText.toLowerCase();

                for (var name in allPoints) {{
                    if (name.toLowerCase().includes(filter)) {{
                        var isSelected = selectedNames.includes(name);
                        var item = document.createElement('div');
                        item.className = 'dropdown-item';
                        item.innerHTML = '<span>' + name + '</span>' + (isSelected ? ' <span style="color:#10B981;">✓</span>' : '');
                        
                        (function(pName) {{
                            item.onclick = function(e) {{
                                e.stopPropagation();
                                toggleSelectPoint(pName);
                            }};
                        }})(name);

                        dropdownList.appendChild(item);
                        count++;
                        if (count >= 30) break; // Giới hạn 30 kết quả đầu để mượt màn hình
                    }}
                }}

                dropdownList.style.display = count > 0 ? 'block' : 'none';
            }}

            searchInput.addEventListener('focus', function() {{ renderDropdown(this.value); }});
            searchInput.addEventListener('input', function() {{ renderDropdown(this.value); }});

            document.addEventListener('click', function(e) {{
                if (!e.target.closest('.select-container')) {{
                    dropdownList.style.display = 'none';
                }}
            }});

            function toggleSelectPoint(name) {{
                var idx = selectedNames.indexOf(name);
                if (idx > -1) {{
                    selectedNames.splice(idx, 1);
                }} else {{
                    selectedNames.push(name);
                }}
                updateUI();
                renderDropdown(searchInput.value);
            }}

            function removePoint(name) {{
                var idx = selectedNames.indexOf(name);
                if (idx > -1) {{
                    selectedNames.splice(idx, 1);
                }}
                updateUI();
            }}

            function updateUI() {{
                selectedChipsContainer.innerHTML = '';
                selectedNames.forEach(function(name) {{
                    var chip = document.createElement('div');
                    chip.className = 'chip';
                    chip.innerHTML = name + ' <span class="chip-remove" onclick="removePoint(\'' + name + '\')">✕</span>';
                    selectedChipsContainer.appendChild(chip);
                }});

                renderMarkers();
            }}

            function renderMarkers() {{
                markersGroup.clearLayers();
                var bounds = [];

                selectedNames.forEach(function(name) {{
                    var pt = allPoints[name];
                    if (pt) {{
                        var marker = L.circleMarker([pt.lat, pt.lng], {{
                            radius: 7, color: '#EF4444', fillColor: '#FFFFFF', fillOpacity: 1, weight: 3
                        }}).bindPopup('<b>' + name + '</b>');
                        markersGroup.addLayer(marker);
                        bounds.push([pt.lat, pt.lng]);
                    }}
                }});

                if (bounds.length > 0 && !currentOptimizedRoute) {{
                    map.fitBounds(bounds, {{ padding: [80, 80] }});
                }}
            }}

            // Định vị GPS
            function locateUser() {{
                map.locate({{ setView: true, maxZoom: 16, enableHighAccuracy: true }});
            }}

            map.on('locationfound', function(e) {{
                userLatLng = e.latlng;
                if (!userMarker) {{
                    var icon = L.divIcon({{ className: 'user-location-marker' }});
                    userMarker = L.marker(e.latlng, {{ icon: icon }}).addTo(map).bindPopup("<b>Vị trí GPS của bạn</b>");
                }} else {{
                    userMarker.setLatLng(e.latlng);
                }}
            }});

            // Tính toán TSP Lộ trình tối ưu
            function getDistance(lat1, lon1, lat2, lon2) {{
                var R = 6371;
                var dLat = (lat2 - lat1) * Math.PI / 180;
                var dLon = (lon2 - lon1) * Math.PI / 180;
                var a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                        Math.sin(dLon/2) * Math.sin(dLon/2);
                return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
            }}

            function optimizeAndRoute() {{
                if (!userLatLng) {{
                    alert("Đang định vị GPS... Vui lòng bật quyền vị trí trên điện thoại và bấm lại nút 🎯 GPS.");
                    locateUser();
                    return;
                }}

                if (selectedNames.length === 0) {{
                    alert("Vui lòng chọn ít nhất 1 tập điểm!");
                    return;
                }}

                var pts = selectedNames.map(function(n) {{
                    return {{ name: n, lat: allPoints[n].lat, lng: allPoints[n].lng }};
                }});

                var unvisited = pts.slice();
                var route = [{{ name: "Điểm Xuất Phát (GPS)", lat: userLatLng.lat, lng: userLatLng.lng }}];
                var current = route[0];

                while (unvisited.length > 0) {{
                    var nearestIdx = 0;
                    var minDst = Infinity;
                    for (var i = 0; i < unvisited.length; i++) {{
                        var d = getDistance(current.lat, current.lng, unvisited[i].lat, unvisited[i].lng);
                        if (d < minDst) {{ minDst = d; nearestIdx = i; }}
                    }}
                    current = unvisited[nearestIdx];
                    route.push(current);
                    unvisited.splice(nearestIdx, 1);
                }}
                route.push(route[0]);

                currentOptimizedRoute = route;
                markersGroup.clearLayers();

                route.forEach(function(pt, idx) {{
                    if (idx === route.length - 1) return;
                    var iconClass = idx === 0 ? 'start-end-icon' : 'number-icon';
                    var label = idx === 0 ? '🏁' : idx.toString();

                    var icon = L.divIcon({{
                        className: iconClass, html: label, iconSize: [24, 24], iconAnchor: [12, 12]
                    }});
                    var m = L.marker([pt.lat, pt.lng], {{ icon: icon }}).bindPopup("<b>" + (idx === 0 ? "Bắt đầu" : "Thứ tự " + idx) + ":</b> " + pt.name);
                    markersGroup.addLayer(m);
                }});

                var waypoints = route.map(function(pt) {{ return L.latLng(pt.lat, pt.lng); }});

                if (routingControl) map.removeControl(routingControl);

                routingControl = L.Routing.control({{
                    waypoints: waypoints,
                    addWaypoints: false,
                    show: false,
                    createMarker: function() {{ return null; }},
                    lineOptions: {{ styles: [{{ color: '#FF6600', opacity: 0.9, weight: 6 }}] }}
                }}).addTo(map);
            }}

            // Mở ứng dụng Google Maps
            function openGoogleMaps() {{
                if (!currentOptimizedRoute || currentOptimizedRoute.length < 2) {{
                    alert("Vui lòng bấm '🚀 Tối Ưu Lộ Trình' trước khi mở Google Maps!");
                    return;
                }}

                var pts = currentOptimizedRoute.slice(0, currentOptimizedRoute.length - 1);
                var origin = pts[0].lat + "," + pts[0].lng;
                var destination = pts[pts.length - 1].lat + "," + pts[pts.length - 1].lng;
                var waypoints = pts.slice(1, pts.length - 1).map(function(p) {{ return p.lat + "," + p.lng; }}).join("|");

                var url = "https://www.google.com/maps/dir/?api=1&origin=" + encodeURIComponent(origin) + "&destination=" + encodeURIComponent(destination);
                if (waypoints) url += "&waypoints=" + encodeURIComponent(waypoints);
                url += "&travelmode=driving";

                window.open(url, '_blank');
            }}

            // Khởi tạo
            updateUI();
            locateUser();
        </script>
    </body>
    </html>
    """

    components.html(leaflet_html, height=1000, scrolling=False)
else:
    st.error(
        "⚠️ Không tìm thấy tệp dữ liệu Excel `.xlsx` hoặc dữ liệu rỗng. Vui"
        " lòng kiểm tra lại tệp!"
    )
