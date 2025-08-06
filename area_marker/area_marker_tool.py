import sys
import os
import json
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QLabel, 
                            QPushButton, QVBoxLayout, QHBoxLayout, QWidget, 
                            QComboBox, QMessageBox, QScrollArea, QButtonGroup, QRadioButton,
                            QDialog, QRadioButton, QDialogButtonBox)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont, QShortcut, QKeySequence
from PIL import Image

class LoadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("選擇載入類型")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout()
        
        self.image_radio = QRadioButton("載入單張圖片")
        self.project_radio = QRadioButton("載入項目資料夾")
        self.image_radio.setChecked(True)
        
        layout.addWidget(self.image_radio)
        layout.addWidget(self.project_radio)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
        self.setLayout(layout)
    
    def get_load_type(self):
        if self.image_radio.isChecked():
            return "image"
        else:
            return "project"

class AreaMarkerTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("區域標記工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化變數
        self.image_path = None
        self.image = None
        self.pixmap = None
        self.scaled_pixmap = None
        self.drawing = False
        self.moving = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.areas = {"不能放的": [], "水路": []}  # 存儲區域
        self.current_area_type = "不能放的"  # 預設區域類型
        self.rectangles = []
        self.history = []  # 操作歷史，用於撤銷功能
        self.drawing_first_point = True  # 是否是繪製的第一個點
        self.temp_first_point = None  # 暫存第一個點
        self.draw_mode = "draw"  # 繪製模式: "draw" 或 "move"
        self.selected_rect_index = -1  # 選中的矩形索引
        self.moving_offset = QPoint()  # 移動矩形時的偏移量
        self.project_folder = None  # 項目資料夾路徑
        
        # 創建UI
        self.setup_ui()
        
        # 設置快捷鍵
        self.setup_shortcuts()
    
    def setup_shortcuts(self):
        # Ctrl+Z 撤銷快捷鍵
        self.undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        self.undo_shortcut.activated.connect(self.undo_last_action)
    
    def setup_ui(self):
        # 主佈局
        main_layout = QHBoxLayout()
        
        # 圖片顯示區域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumWidth(800)
        
        self.image_label = QLabel("請載入一張圖片")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(800, 600)
        self.image_label.setStyleSheet("background-color: #f0f0f0;")
        self.image_label.setMouseTracking(True)
        self.image_label.mousePressEvent = self.mouse_press_event
        self.image_label.mouseMoveEvent = self.mouse_move_event
        self.image_label.mouseReleaseEvent = self.mouse_release_event
        
        self.scroll_area.setWidget(self.image_label)
        
        # 控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout()
        
        # 載入圖片按鈕
        self.load_button = QPushButton("載入圖片")
        self.load_button.clicked.connect(self.load_image)
        
        # 繪畫狀態選擇
        mode_layout = QHBoxLayout()
        mode_label = QLabel("繪畫狀態:")
        self.mode_group = QButtonGroup()
        self.draw_radio = QRadioButton("繪製方塊")
        self.move_radio = QRadioButton("移動方塊")
        self.draw_radio.setChecked(True)
        self.mode_group.addButton(self.draw_radio)
        self.mode_group.addButton(self.move_radio)
        self.draw_radio.toggled.connect(self.change_draw_mode)
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.draw_radio)
        mode_layout.addWidget(self.move_radio)
        
        # 區域類型選擇
        area_layout = QHBoxLayout()
        area_label = QLabel("區域類型:")
        self.area_combobox = QComboBox()
        self.area_combobox.addItems(["不能放的", "水路"])
        self.area_combobox.currentTextChanged.connect(self.change_area_type)
        
        area_layout.addWidget(area_label)
        area_layout.addWidget(self.area_combobox)
        
        # 刪除最後一個區域
        self.delete_button = QPushButton("刪除最後一個區域")
        self.delete_button.clicked.connect(self.delete_last_rectangle)
        
        # 撤銷按鈕
        self.undo_button = QPushButton("撤銷操作 (Ctrl+Z)")
        self.undo_button.clicked.connect(self.undo_last_action)
        
        # 清除所有區域
        self.clear_button = QPushButton("清除所有區域")
        self.clear_button.clicked.connect(self.clear_all_rectangles)
        
        # 導出數據
        self.export_button = QPushButton("導出數據")
        self.export_button.clicked.connect(self.export_data)
        
        # 複製 Raw 數據到剪貼板
        self.copy_raw_button = QPushButton("複製 Raw 數據到剪貼板")
        self.copy_raw_button.clicked.connect(self.copy_raw_to_clipboard)
        
        # 座標顯示
        self.coords_label = QLabel("座標: (0, 0)")
        
        # 狀態提示
        self.status_label = QLabel("點擊一個點開始繪製")
        
        # 添加所有控件到控制面板
        control_layout.addWidget(self.load_button)
        control_layout.addLayout(mode_layout)
        control_layout.addLayout(area_layout)
        control_layout.addWidget(self.delete_button)
        control_layout.addWidget(self.undo_button)
        control_layout.addWidget(self.clear_button)
        control_layout.addWidget(self.export_button)
        control_layout.addWidget(self.copy_raw_button)
        control_layout.addStretch()
        control_layout.addWidget(self.status_label)
        control_layout.addWidget(self.coords_label)
        
        control_panel.setLayout(control_layout)
        
        # 添加到主佈局
        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(control_panel)
        
        # 設置主窗口
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def change_draw_mode(self, checked):
        if checked:  # 如果選中的是繪製方塊按鈕
            self.draw_mode = "draw"
            self.status_label.setText("點擊一個點開始繪製")
        else:
            self.draw_mode = "move"
            self.status_label.setText("點擊方塊進行移動")
        
        # 重置繪製狀態
        self.drawing_first_point = True
        self.temp_first_point = None
        self.selected_rect_index = -1
        self.update_image()
    
    def load_image(self):
        # 先詢問用戶要載入圖片還是項目資料夾
        dialog = LoadDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        load_type = dialog.get_load_type()
        
        if load_type == "image":
            # 載入單張圖片
            file_path, _ = QFileDialog.getOpenFileName(
                self, "選擇圖片", "", "圖片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
            )
            
            if file_path:
                self.image_path = file_path
                self.image = QImage(file_path)
                
                if self.image.isNull():
                    QMessageBox.critical(self, "錯誤", "無法載入圖片")
                    return
                
                # 創建項目資料夾
                self.create_project_folder(file_path)
                
                # 保存歷史狀態
                self.save_history()
                
                # 重置區域
                self.areas = {"不能放的": [], "水路": []}
                self.rectangles = []
                
                # 顯示圖片
                self.pixmap = QPixmap.fromImage(self.image)
                self.update_image()
                
                # 更新日誌
                self.update_log(f"已載入圖片: {os.path.basename(file_path)}")
        else:
            # 載入項目資料夾
            folder_path = QFileDialog.getExistingDirectory(self, "選擇項目資料夾")
            if folder_path:
                # 檢查資料夾是否包含必要的文件
                image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
                json_file = os.path.join(folder_path, "project_data.json")
                
                if not image_files:
                    QMessageBox.critical(self, "錯誤", "項目資料夾中沒有找到圖片文件")
                    return
                
                if not os.path.exists(json_file):
                    reply = QMessageBox.question(self, "警告", "項目資料夾中沒有找到項目數據文件，是否只載入圖片？",
                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.No:
                        return
                
                # 載入圖片
                image_path = os.path.join(folder_path, image_files[0])
                self.image_path = image_path
                self.image = QImage(image_path)
                
                if self.image.isNull():
                    QMessageBox.critical(self, "錯誤", "無法載入圖片")
                    return
                
                # 設置項目資料夾
                self.project_folder = folder_path
                
                # 重置區域數據
                self.areas = {"不能放的": [], "水路": []}
                self.rectangles = []
                
                # 先創建 pixmap，這對於座標轉換很重要
                self.pixmap = QPixmap.fromImage(self.image)
                
                # 從JSON載入區域數據
                if os.path.exists(json_file):
                    try:
                        print(f"嘗試載入JSON數據: {json_file}")
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        print(f"JSON數據已載入，開始處理")
                        print(f"圖片尺寸: {self.pixmap.width()} x {self.pixmap.height()}")
                        
                        # 檢查JSON格式，確保包含areas字段
                        if "areas" in data:
                            print(f"發現區域數據: {len(data['areas'])} 種類型")
                            # 從世界座標重建矩形
                            for area_type, areas in data["areas"].items():
                                print(f"處理區域類型: {area_type}, 數量: {len(areas)}")
                                # 確保區域類型存在
                                if area_type not in self.areas:
                                    self.areas[area_type] = []
                                
                                # 從世界座標創建螢幕座標的矩形
                                for i, area in enumerate(areas):
                                    try:
                                        # 確保格式正確
                                        if len(area) != 2:
                                            print(f"區域 {i} 格式錯誤: 需要2個點，但有 {len(area)} 個點")
                                            continue
                                        
                                        world_start = area[0]
                                        world_end = area[1]
                                        
                                        # 確保座標格式正確
                                        if not isinstance(world_start, list) or not isinstance(world_end, list) or len(world_start) != 2 or len(world_end) != 2:
                                            print(f"區域 {i} 座標格式錯誤: {world_start}, {world_end}")
                                            continue
                                        
                                        print(f"處理區域 {i}: 從 {world_start} 到 {world_end}")
                                        
                                        # 轉換為螢幕座標
                                        start_point = self.from_world_coords(float(world_start[0]), float(world_start[1]))
                                        end_point = self.from_world_coords(float(world_end[0]), float(world_end[1]))
                                        
                                        print(f"  轉換為螢幕座標: 從 {start_point.x()}, {start_point.y()} 到 {end_point.x()}, {end_point.y()}")
                                        
                                        # 創建矩形
                                        rect = QRect(start_point, end_point).normalized()
                                        
                                        # 添加到矩形列表
                                        self.rectangles.append((area_type, rect, start_point, end_point))
                                        # 添加到區域列表
                                        self.areas[area_type].append([world_start, world_end])
                                        
                                        print(f"  成功添加矩形")
                                    except Exception as e:
                                        print(f"處理區域 {i} 時出錯: {str(e)}")
                            
                            print(f"總共載入 {len(self.rectangles)} 個矩形")
                            self.update_log(f"已載入項目: {os.path.basename(folder_path)}")
                        else:
                            print("JSON中沒有找到areas字段")
                            QMessageBox.warning(self, "警告", "項目數據格式不正確")
                    except Exception as e:
                        print(f"載入JSON時出錯: {str(e)}")
                        QMessageBox.warning(self, "警告", f"載入項目數據時出錯: {str(e)}")
                        self.areas = {"不能放的": [], "水路": []}
                        self.rectangles = []
                
                # 更新顯示
                self.update_image()
                self.update_log(f"已載入項目資料夾: {os.path.basename(folder_path)}")
    
    def create_project_folder(self, image_path):
        """根據圖片名稱創建項目資料夾"""
        try:
            # 獲取圖片文件名（不含擴展名）
            image_name = os.path.basename(image_path)
            image_name_without_ext = os.path.splitext(image_name)[0]
            
            # 項目資料夾基礎路徑
            base_folder = os.path.dirname(os.path.dirname(image_path))
            area_marker_folder = os.path.join(base_folder, "area_marker")
            
            # 確保area_marker資料夾存在
            if not os.path.exists(area_marker_folder):
                os.makedirs(area_marker_folder)
            
            # 嘗試創建以圖片名稱命名的項目資料夾
            project_folder = os.path.join(area_marker_folder, image_name_without_ext)
            
            # 如果資料夾已存在，添加數字後綴
            counter = 1
            original_project_folder = project_folder
            while os.path.exists(project_folder):
                project_folder = f"{original_project_folder}_{counter}"
                counter += 1
            
            # 創建項目資料夾
            os.makedirs(project_folder)
            
            # 複製圖片到項目資料夾
            image_dest = os.path.join(project_folder, image_name)
            shutil.copy2(image_path, image_dest)
            
            # 設置項目資料夾路徑
            self.project_folder = project_folder
            
            self.update_log(f"創建了項目資料夾: {os.path.basename(project_folder)}")
            return project_folder
        
        except Exception as e:
            QMessageBox.warning(self, "警告", f"創建項目資料夾時出錯: {str(e)}")
            return None
    
    def save_history(self):
        """保存當前狀態到歷史記錄中並保存項目數據到JSON"""
        # 保存到歷史記錄
        history_item = {
            "rectangles": self.rectangles.copy(),
            "areas": {key: value.copy() for key, value in self.areas.items()}
        }
        self.history.append(history_item)
        
        # 如果有項目資料夾，保存數據到JSON
        if self.project_folder and self.image_path:
            try:
                json_file = os.path.join(self.project_folder, "project_data.json")
                
                # 確保世界座標格式正確
                formatted_areas = {}
                for area_type, areas in self.areas.items():
                    formatted_areas[area_type] = []
                    for area in areas:
                        # 確保每個區域都是兩個點的列表
                        if len(area) == 2 and isinstance(area[0], (list, tuple)) and isinstance(area[1], (list, tuple)):
                            # 確保每個點都是兩個浮點數
                            if len(area[0]) == 2 and len(area[1]) == 2:
                                formatted_area = [
                                    [float(area[0][0]), float(area[0][1])],
                                    [float(area[1][0]), float(area[1][1])]
                                ]
                                formatted_areas[area_type].append(formatted_area)
                
                # 準備要保存的數據
                data = {
                    "image_path": self.image_path,
                    "areas": formatted_areas,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 保存到JSON
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"已保存項目數據到: {json_file}")
            
            except Exception as e:
                print(f"保存項目數據時出錯: {str(e)}")
    
    def undo_last_action(self):
        """撤銷上一步操作"""
        if self.history:
            last_state = self.history.pop()
            self.rectangles = last_state["rectangles"].copy()
            self.areas = {key: value.copy() for key, value in last_state["areas"].items()}
            self.update_image()
            self.update_log("撤銷了上一步操作")
    
    def update_image(self):
        if self.pixmap:
            # 創建一個新的可繪圖的pixmap
            display_pixmap = QPixmap(self.pixmap)
            painter = QPainter(display_pixmap)
            
            # 繪製所有矩形
            for i, (area_type, rect, start_point, end_point) in enumerate(self.rectangles):
                if area_type == "不能放的":
                    pen = QPen(QColor(255, 0, 0, 100), 2)  # 紅色，半透明
                    fill_color = QColor(255, 0, 0, 50)
                else:  # 水路
                    pen = QPen(QColor(0, 0, 255, 100), 2)  # 藍色，半透明
                    fill_color = QColor(0, 0, 255, 50)
                
                # 如果是被選中的矩形
                if i == self.selected_rect_index:
                    pen.setWidth(4)  # 加粗邊框
                    pen.setColor(QColor(0, 255, 0, 150))  # 綠色邊框
                
                painter.setPen(pen)
                painter.setBrush(fill_color)
                painter.drawRect(rect)
                
                # 在矩形上標註其世界座標
                painter.setPen(QPen(Qt.GlobalColor.black, 1))
                painter.setFont(QFont("Arial", 8))
                
                # 計算世界座標
                world_start = self.to_world_coords(start_point)
                world_end = self.to_world_coords(end_point)
                
                coord_text = f"({world_start[0]:.1f}, {world_start[1]:.1f}) - ({world_end[0]:.1f}, {world_end[1]:.1f})"
                painter.drawText(rect.center(), coord_text)
            
            # 如果正在繪製第二個點，顯示臨時矩形
            if not self.drawing_first_point and self.temp_first_point and self.draw_mode == "draw":
                if self.current_area_type == "不能放的":
                    pen = QPen(QColor(255, 0, 0, 100), 2)  # 紅色，半透明
                    fill_color = QColor(255, 0, 0, 50)
                else:  # 水路
                    pen = QPen(QColor(0, 0, 255, 100), 2)  # 藍色，半透明
                    fill_color = QColor(0, 0, 255, 50)
                
                current_pos = QPoint(self.end_point)
                temp_rect = QRect(self.temp_first_point, current_pos).normalized()
                
                painter.setPen(pen)
                painter.setBrush(fill_color)
                painter.drawRect(temp_rect)
                
                # 繪製第一個點
                painter.setPen(QPen(Qt.GlobalColor.black, 3))
                painter.drawPoint(self.temp_first_point)
            
            painter.end()
            
            # 顯示到標籤
            self.image_label.setPixmap(display_pixmap)
            self.image_label.setFixedSize(display_pixmap.size())
    
    def to_world_coords(self, point):
        """將螢幕座標轉換為世界座標（以圖片中心為原點）"""
        if not self.pixmap:
            return (0, 0)
        
        center_x = self.pixmap.width() / 2
        center_y = self.pixmap.height() / 2
        
        world_x = point.x() - center_x
        world_y = center_y - point.y()  # 反轉Y軸，因為螢幕座標Y向下
        
        return (world_x, world_y)
    
    def from_world_coords(self, world_x, world_y):
        """將世界座標轉換為螢幕座標"""
        if not self.pixmap:
            print("錯誤：pixmap 未初始化")
            return QPoint(0, 0)
        
        try:
            # 確保輸入是數字
            world_x = float(world_x)
            world_y = float(world_y)
            
            center_x = self.pixmap.width() / 2
            center_y = self.pixmap.height() / 2
            
            screen_x = world_x + center_x
            screen_y = center_y - world_y  # 反轉Y軸，因為螢幕座標Y向下
            
            print(f"座標轉換: 世界座標 ({world_x}, {world_y}) -> 螢幕座標 ({screen_x}, {screen_y})")
            
            return QPoint(int(screen_x), int(screen_y))
        
        except (ValueError, TypeError) as e:
            print(f"座標轉換錯誤: {str(e)}")
            print(f"無法將 {world_x}, {world_y} 轉換為數字")
            return QPoint(0, 0)
        except Exception as e:
            print(f"座標轉換時發生未知錯誤: {str(e)}")
            return QPoint(0, 0)
    
    def change_area_type(self, area_type):
        self.current_area_type = area_type
    
    def find_rect_at_pos(self, pos):
        """找出點擊位置的矩形索引"""
        for i, (_, rect, _, _) in enumerate(self.rectangles):
            if rect.contains(pos):
                return i
        return -1
    
    def mouse_press_event(self, event):
        if not self.pixmap:
            return
        
        # 獲取點擊位置
        pos = event.position().toPoint()
        
        if event.button() == Qt.MouseButton.LeftButton:
            if self.draw_mode == "draw":
                # 繪製模式
                if self.drawing_first_point:
                    # 第一個點
                    self.temp_first_point = pos
                    self.drawing_first_point = False
                    self.status_label.setText("點擊第二個點完成矩形")
                else:
                    # 第二個點，完成矩形
                    self.end_point = pos
                    self.complete_rectangle()
                    self.drawing_first_point = True
                    self.temp_first_point = None
                    self.status_label.setText("點擊一個點開始繪製")
            else:
                # 移動模式
                self.selected_rect_index = self.find_rect_at_pos(pos)
                if self.selected_rect_index != -1:
                    self.moving = True
                    self.moving_offset = pos
                    self.status_label.setText("移動方塊中...")
        
        self.update_image()
    
    def mouse_move_event(self, event):
        if not self.pixmap:
            return
        
        # 更新座標顯示
        position = event.position().toPoint()
        world_coords = self.to_world_coords(position)
        self.coords_label.setText(f"座標: ({world_coords[0]:.1f}, {world_coords[1]:.1f})")
        
        if not self.drawing_first_point and self.temp_first_point and self.draw_mode == "draw":
            # 在繪製第二個點時，更新臨時矩形
            self.end_point = position
            self.update_image()
        elif self.moving and self.selected_rect_index != -1 and self.draw_mode == "move":
            # 移動選中的矩形
            new_pos = position
            dx = new_pos.x() - self.moving_offset.x()
            dy = new_pos.y() - self.moving_offset.y()
            
            # 獲取選中的矩形
            area_type, rect, start_point, end_point = self.rectangles[self.selected_rect_index]
            
            # 移動矩形各頂點
            new_start = QPoint(start_point.x() + dx, start_point.y() + dy)
            new_end = QPoint(end_point.x() + dx, end_point.y() + dy)
            new_rect = QRect(new_start, new_end).normalized()
            
            # 更新矩形
            self.rectangles[self.selected_rect_index] = (area_type, new_rect, new_start, new_end)
            
            # 更新世界座標
            world_start = self.to_world_coords(new_start)
            world_end = self.to_world_coords(new_end)
            
            # 更新區域數據
            area_index = -1
            for i, area in enumerate(self.areas[area_type]):
                # 找出對應的區域數據
                old_world_start = self.to_world_coords(start_point)
                old_world_end = self.to_world_coords(end_point)
                if abs(area[0][0] - old_world_start[0]) < 0.1 and abs(area[0][1] - old_world_start[1]) < 0.1:
                    area_index = i
                    break
            
            if area_index != -1:
                self.areas[area_type][area_index] = [world_start, world_end]
            
            # 更新移動偏移
            self.moving_offset = new_pos
            
            # 更新顯示
            self.update_image()
    
    def mouse_release_event(self, event):
        if not self.pixmap:
            return
        
        if event.button() == Qt.MouseButton.LeftButton and self.moving and self.selected_rect_index != -1:
            # 結束移動
            self.moving = False
            self.save_history()  # 保存歷史記錄
            self.status_label.setText("點擊方塊進行移動")
            self.update_log("移動了一個區域")
            
            # 自動保存項目數據
            if self.project_folder:
                self.save_history()
    
    def complete_rectangle(self):
        """完成矩形繪製"""
        if not self.temp_first_point:
            return
        
        # 保存歷史狀態
        self.save_history()
        
        # 確保矩形有一定大小
        rect = QRect(self.temp_first_point, self.end_point).normalized()
        if rect.width() > 5 and rect.height() > 5:
            # 確定左上角和右下角點
            x1, y1 = self.temp_first_point.x(), self.temp_first_point.y()
            x2, y2 = self.end_point.x(), self.end_point.y()
            
            # 確保點的順序是左上到右下
            left_top = QPoint(min(x1, x2), min(y1, y2))
            right_bottom = QPoint(max(x1, x2), max(y1, y2))
            
            # 保存矩形
            self.rectangles.append((self.current_area_type, rect, left_top, right_bottom))
            
            # 保存到對應的區域
            world_left_top = self.to_world_coords(left_top)
            world_right_bottom = self.to_world_coords(right_bottom)
            
            # 我們需要矩形的兩個對角點（按左上到右下的順序）
            self.areas[self.current_area_type].append([world_left_top, world_right_bottom])
            
            self.update_log(f"添加了一個{self.current_area_type}區域: ({world_left_top[0]:.1f}, {world_left_top[1]:.1f}) - ({world_right_bottom[0]:.1f}, {world_right_bottom[1]:.1f})")
            
            # 每次完成矩形繪製後，自動保存項目數據
            if self.project_folder:
                self.save_history()
    
    def delete_last_rectangle(self):
        if self.rectangles:
            # 保存歷史狀態
            self.save_history()
            
            last_rect = self.rectangles.pop()
            area_type = last_rect[0]
            self.areas[area_type].pop()
            self.update_image()
            self.update_log(f"刪除了一個{area_type}區域")
            
            # 自動保存項目數據
            if self.project_folder:
                self.save_history()
    
    def clear_all_rectangles(self):
        if self.rectangles:
            # 保存歷史狀態
            self.save_history()
            
            self.rectangles.clear()
            self.areas = {"不能放的": [], "水路": []}
            self.update_image()
            self.update_log("清除了所有區域")
            
            # 自動保存項目數據
            if self.project_folder:
                self.save_history()
    
    def export_data(self):
        if not self.areas["不能放的"] and not self.areas["水路"]:
            QMessageBox.warning(self, "警告", "沒有可導出的區域")
            return
        
        # 確保保存 JSON 數據
        if self.project_folder:
            self.save_history()
        
        # 確定導出路徑
        if self.project_folder:
            # 使用項目資料夾中的默認文件名
            default_path = os.path.join(self.project_folder, "exported_data.txt")
        else:
            # 使用默認路徑
            default_path = ""
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存數據", default_path, "文本文件 (*.txt)"
        )
        
        if file_path:
            # 確保擴展名為 .txt
            if not file_path.lower().endswith('.txt'):
                file_path += '.txt'
            
            # 獲取文件名（不含擴展名）和路徑
            file_path_without_ext = file_path[:-4]  # 移除 .txt
            
            try:
                # 生成數據格式
                formatted_data = self.generate_data_format()
                
                # 格式1：帶前綴
                with open(file_path, 'w', encoding='utf-8') as f:
                    # 格式化輸出
                    result = "std::vector<std::vector<std::vector<glm::vec2>>>="
                    result += formatted_data
                    f.write(result)
                
                # 格式2：不帶前綴
                raw_file_path = f"{file_path_without_ext}_raw.txt"
                with open(raw_file_path, 'w', encoding='utf-8') as f:
                    # 只包含數據部分
                    f.write(formatted_data)
                
                # 如果是保存到項目資料夾外部，同時複製到項目資料夾
                if self.project_folder and not file_path.startswith(self.project_folder):
                    # 項目資料夾中的文件路徑
                    project_file_path = os.path.join(self.project_folder, "exported_data.txt")
                    project_raw_file_path = os.path.join(self.project_folder, "exported_data_raw.txt")
                    
                    # 複製文件到項目資料夾
                    with open(project_file_path, 'w', encoding='utf-8') as f:
                        result = "std::vector<std::vector<std::vector<glm::vec2>>>="
                        result += formatted_data
                        f.write(result)
                    
                    with open(project_raw_file_path, 'w', encoding='utf-8') as f:
                        f.write(formatted_data)
                    
                    QMessageBox.information(self, "成功", 
                                          f"數據已保存到：\n1. {file_path}\n2. {raw_file_path}\n" + 
                                          f"並複製到項目資料夾：\n1. {project_file_path}\n2. {project_raw_file_path}")
                    self.update_log(f"導出數據到多個位置，包括項目資料夾: {os.path.basename(self.project_folder)}")
                else:
                    QMessageBox.information(self, "成功", f"數據已保存到：\n1. {file_path}\n2. {raw_file_path}")
                    self.update_log(f"導出數據到 {file_path} 和 {raw_file_path}")
            
            except Exception as e:
                QMessageBox.critical(self, "錯誤", f"保存數據時出錯: {str(e)}")
    
    def generate_data_format(self):
        """生成數據格式，返回格式化的字符串"""
        # 陸地部分（不能放的）
        land_parts = []
        if self.areas["不能放的"]:
            for rect in self.areas["不能放的"]:
                land_parts.append("{" + f"glm::vec2({rect[0][0]:.1f}, {rect[0][1]:.1f}),glm::vec2({rect[1][0]:.1f}, {rect[1][1]:.1f})" + "}")
        
        # 水路部分
        water_parts = []
        if self.areas["水路"]:
            for rect in self.areas["水路"]:
                water_parts.append("{" + f"glm::vec2({rect[0][0]:.1f}, {rect[0][1]:.1f}),glm::vec2({rect[1][0]:.1f}, {rect[1][1]:.1f})" + "}")
        
        # 組合兩個部分，確保即使沒有區域也會有空括號
        result = "{" + ",".join(land_parts) + "},{" + ",".join(water_parts) + "}"
        
        return result
    
    def copy_raw_to_clipboard(self):
        """複製 Raw 數據到剪貼板"""
        if not self.areas["不能放的"] and not self.areas["水路"]:
            QMessageBox.warning(self, "警告", "沒有可複製的區域")
            return
        
        try:
            # 獲取 Raw 數據
            raw_data = self.generate_data_format()
            
            # 複製到剪貼板
            clipboard = QApplication.clipboard()
            clipboard.setText(raw_data)
            
            QMessageBox.information(self, "成功", "Raw 數據已複製到剪貼板")
            self.update_log("複製 Raw 數據到剪貼板")
        
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"複製數據時出錯: {str(e)}")
    
    def update_log(self, message):
        """更新日誌文件"""
        try:
            log_file = "log.md"
            now = datetime.now()
            date_str = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M")
            
            # 檢查日誌文件是否存在
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                content = ""
            
            # 檢查今天的日期是否已經存在
            if f"# {date_str}" in content:
                # 尋找今天的日期區塊
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 檢查當前時間是否存在
                time_exists = False
                for i, line in enumerate(lines):
                    if line.strip() == f"# {date_str}":
                        j = i + 1
                        while j < len(lines) and not lines[j].startswith("# "):
                            if lines[j].strip() == f"## {time_str}":
                                time_exists = True
                                # 找到相同時間區塊，添加新消息
                                k = j + 1
                                while k < len(lines) and not lines[k].startswith("## ") and not lines[k].startswith("# "):
                                    k += 1
                                lines.insert(k, f"    {message}\n")
                                break
                            j += 1
                        break
                
                # 如果當前時間不存在，新增時間區塊
                if not time_exists:
                    for i, line in enumerate(lines):
                        if line.strip() == f"# {date_str}":
                            # 找到下一個標題位置
                            j = i + 1
                            while j < len(lines) and not lines[j].startswith("# "):
                                j += 1
                            
                            # 添加新時間區塊
                            time_block = [f"## {time_str}\n", f"    {message}\n", "\n"]
                            for k, text in enumerate(time_block):
                                lines.insert(j + k - 1, text)
                            break
                
                # 寫回文件
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            
            else:
                # 今天的日期不存在，添加新日期和時間區塊
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n# {date_str}\n")
                    f.write(f"## {time_str}\n")
                    f.write(f"    {message}\n")
        
        except Exception as e:
            print(f"更新日誌時出錯: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = AreaMarkerTool()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 