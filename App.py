navigator.geolocation.watchPosition(updateLocation, handleGPSError, {{
                        enableHighAccuracy: true,
                        maximumAge: 0,
                        timeout: 5000
                    }});
                }}

                // Nút bấm định vị vị trí hiện tại
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
