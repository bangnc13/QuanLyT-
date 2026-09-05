import sys
import os
import pandas as pd
import requests
import folium
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QAbstractItemView, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class MapApp(QMainWindow):
    def __init__(self, excel_file='QuanLyTĐ.xlsx'):
        super().__init__()
        self.setWindowTitle("Công cụ Tìm đường & Quản lý Tập điểm")
        self.setGeometry(100, 100, 1200, 700)
        self.excel_file = excel_file
        
        # Biến lưu vị trí
        self.current_location = None  # (lat, lon)
        self.df = self.load_data()
        
        self.init_ui()

    def load_data(self):
        """Đọc danh sách tập điểm từ file Excel"""
        try:
            df = pd.read_excel(self.excel_file)
            # Lọc bỏ các dòng thiếu tọa độ
            df = df.dropna(subset=['Latitude', 'Longitude'])
            return df
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể đọc file {self.excel_file}: {str(e)}")
            return pd.DataFrame(columns=['Tên đối tượng', 'Latitude', 'Longitude'])

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # === BẢNG ĐIỀU KHIỂN BÊN TRÁI ===
        left_panel = QVBoxLayout()
        
        # Label hướng dẫn
        lbl_select = QLabel("<b>Chọn tập điểm cần đến:</b>")
        left_panel.addWidget(lbl_select)
        
        # Danh sách chọn điểm (Cho phép chọn nhiều điểm nếu muốn)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.populate_list()
        left_panel.addWidget(self.list_widget)

        # Nút lấy vị trí hiện tại
        self.btn_get_location = QPushButton("📍 Lấy vị trí hiện tại")
        self.btn_get_location.clicked.connect(self.get_current_location)
        left_panel.addWidget(self.btn_get_location)

        # Label hiển thị vị trí hiện tại
        self.lbl_loc_status = QLabel("Vị trí hiện tại: Chưa xác định")
        left_panel.addWidget(self.lbl_loc_status)

        # Nút "Bấm" để tính toán lộ trình
        self.btn_route = QPushButton("Bấm")
        self.btn_route.setStyleSheet("font-weight: bold; background-color: #007bff; color: white; height: 40px;")
        self.btn_route.clicked.connect(self.generate_route)
        left_panel.addWidget(self.btn_route)

        # Set tỉ lệ khung hình bên trái
        left_container = QWidget()
        left_container.setLayout(left_panel)
        left_container.setMaximumWidth(320)
        main_layout.addWidget(left_container)

        # === BẢN ĐỒ BÊN PHẢI ===
        self.web_view = QWebEngineView()
        main_layout.addWidget(self.web_view, stretch=1)

        # Render bản đồ ban đầu
        self.render_map()

    def populate_list(self):
        """Nạp danh sách tập điểm vào List Widget"""
        for _, row in self.df.iterrows():
            item_text = f"{row['Tên đối tượng']} ({row['Latitude']:.5f}, {row['Longitude']:.5f})"
            self.list_widget.addItem(item_text)

    def get_current_location(self):
        """Lấy vị trí hiện tại dựa trên IP public (hoặc tọa độ mặc định nếu lỗi)"""
        try:
            res = requests.get('https://ipinfo.io/json', timeout=5).json()
            if 'loc' in res:
                lat, lon = map(float, res['loc'].split(','))
                self.current_location = (lat, lon)
                self.lbl_loc_status.setText(f"Vị trí: {lat:.5f}, {lon:.5f}")
                self.render_map()
                return
        except Exception:
            pass
        
        # Nếu không lấy được IP, lấy vị trí trung bình của tập điểm làm mốc giả định
        if not self.df.empty:
            avg_lat = self.df['Latitude'].mean()
            avg_lon = self.df['Longitude'].mean()
            self.current_location = (avg_lat, avg_lon)
            self.lbl_loc_status.setText(f"Vị trí (mặc định): {avg_lat:.5f}, {avg_lon:.5f}")
            self.render_map()

    def get_osrm_route(self, origin, destination):
        """Gọi API OSRM để lấy đường đi xe máy/xe cộ"""
        url = f"http://router.project-osrm.org/route/v1/driving/{origin[1]},{origin[0]};{destination[1]},{destination[0]}?overview=full&geometries=geojson"
        try:
            res = requests.get(url, timeout=5).json()
            if res.get('code') == 'Ok':
                coords = res['routes'][0]['geometry']['coordinates']
                # OSRM trả về [lon, lat], cần chuyển sang [lat, lon] cho Folium
                return [(lat, lon) for lon, lat in coords]
        except Exception as e:
            print(f"Lỗi lấy lộ trình: {e}")
        return [origin, destination]

    def render_map(self, route_coords=None, selected_points=None):
        """Tạo bản đồ Folium với Layer Google Maps"""
        # Xác định trung tâm bản đồ
        start_center = [21.817, 105.207]
        if self.current_location:
            start_center = self.current_location
        elif not self.df.empty:
            start_center = [self.df['Latitude'].iloc[0], self.df['Longitude'].iloc[0]]

        # Tạo map
        m = folium.Map(location=start_center, zoom_start=14)

        # Layer Google Maps Đường Phố
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Maps',
            overlay=False,
            control=True
        ).add_to(m)

        # Layer Google Maps Vệ Tinh
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=False,
            control=True
        ).add_to(m)

        # Hiển thị vị trí hiện tại
        if self.current_location:
            folium.Marker(
                location=self.current_location,
                popup="<b>Vị trí của bạn</b>",
                icon=folium.Icon(color='red', icon='user', prefix='fa')
            ).add_to(m)

        # Hiển thị các điểm được chọn
        if selected_points:
            for pt in selected_points:
                folium.Marker(
                    location=(pt['Latitude'], pt['Longitude']),
                    popup=f"<b>{pt['Tên đối tượng']}</b>",
                    icon=folium.Icon(color='green', icon='flag')
                ).add_to(m)

        # Vẽ lộ trình di chuyển
        if route_coords:
            folium.PolyLine(
                route_coords,
                color="blue",
                weight=5,
                opacity=0.8,
                tooltip="Lộ trình di chuyển xe máy"
            ).add_to(m)

        folium.LayerControl().add_to(m)

        # Lưu file HTML tạm và load vào QWebEngineView
        map_path = os.path.abspath("temp_map.html")
        m.save(map_path)
        self.web_view.setUrl(QUrl.fromLocalFile(map_path))

    def generate_route(self):
        """Xử lý khi bấm nút "Bấm""""
        if not self.current_location:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng bấm 'Lấy vị trí hiện tại' trước!")
            return

        selected_indexes = [item.row() for item in self.list_widget.selectedIndexes()]
        if not selected_indexes:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn ít nhất 1 tập điểm trong danh sách!")
            return

        # Lấy danh sách điểm được chọn
        selected_points = self.df.iloc[selected_indexes].to_dict('records')
        
        # Lấy điểm đầu tiên được chọn làm điểm đến
        destination = (selected_points[0]['Latitude'], selected_points[0]['Longitude'])
        
        # Tìm đường bằng OSRM
        route_coords = self.get_osrm_route(self.current_location, destination)
        
        # Vẽ lại bản đồ với tuyến đường
        self.render_map(route_coords=route_coords, selected_points=selected_points)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MapApp('QuanLyTĐ.xlsx')
    window.show()
    sys.exit(app.exec_())
