import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QFileDialog, QLabel, 
                           QListWidget, QSpinBox, QCheckBox, QLineEdit,
                           QColorDialog, QRadioButton, QButtonGroup, QMessageBox)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QImage, QColor, QCursor
from PIL import Image
import os
import re

class ImageProcessor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("圖片批量處理工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化變量
        self.image_files = []
        self.current_index = 0
        self.excluded_images = set()
        self.background_color = QColor(255, 255, 255)  # 默認白色
        self.is_picking_color = False  # 是否正在使用吸色器
        self.current_preview_image = None  # 保存當前預覽圖片
        self.rename_mapping = {}  # 重命名映射
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        
        # 左側控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 添加按鈕
        self.add_folder_btn = QPushButton("添加文件夾")
        self.add_files_btn = QPushButton("添加圖片文件")
        left_layout.addWidget(self.add_folder_btn)
        left_layout.addWidget(self.add_files_btn)
        
        # 旋轉控制
        rotate_label = QLabel("旋轉角度:")
        self.rotate_spin = QSpinBox()
        self.rotate_spin.setRange(-360, 360)
        self.rotate_spin.setSingleStep(90)
        left_layout.addWidget(rotate_label)
        left_layout.addWidget(self.rotate_spin)
        
        # 縮放控制
        scale_label = QLabel("縮放比例 (%):")
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(1, 500)
        self.scale_spin.setValue(100)
        left_layout.addWidget(scale_label)
        left_layout.addWidget(self.scale_spin)
        
        # 背景填充控制
        padding_group = QWidget()
        padding_layout = QVBoxLayout(padding_group)
        
        padding_label = QLabel("背景填充:")
        self.padding_checkbox = QCheckBox("啟用背景填充")
        self.padding_spin = QSpinBox()
        self.padding_spin.setRange(0, 1000)
        self.padding_spin.setValue(50)
        self.padding_spin.setSuffix(" px")
        
        # 修改顏色選擇按鈕和預覽
        color_control = QWidget()
        color_layout = QHBoxLayout(color_control)
        self.color_btn = QPushButton("選擇顏色")
        self.picker_btn = QPushButton("吸取顏色")
        self.picker_btn.setCheckable(True)  # 可切換的按鈕
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(20, 20)
        self.update_color_preview()
        
        color_layout.addWidget(self.color_btn)
        color_layout.addWidget(self.picker_btn)
        color_layout.addWidget(self.color_preview)
        
        padding_layout.addWidget(padding_label)
        padding_layout.addWidget(self.padding_checkbox)
        padding_layout.addWidget(self.padding_spin)
        padding_layout.addWidget(color_control)
        
        left_layout.addWidget(padding_group)
        
        # 重命名控制
        rename_group = QWidget()
        rename_layout = QVBoxLayout(rename_group)
        rename_label = QLabel("重命名設置:")
        self.rename_checkbox = QCheckBox("啟用重命名")
        
        # 重命名模式選擇
        mode_group = QButtonGroup(self)
        self.number_mode = QRadioButton("數字序列")
        self.mapping_mode = QRadioButton("映射模式")
        mode_group.addButton(self.number_mode)
        mode_group.addButton(self.mapping_mode)
        self.number_mode.setChecked(True)
        
        # 前綴輸入框
        prefix_layout = QHBoxLayout()
        prefix_label = QLabel("前綴:")
        self.rename_prefix = QLineEdit()
        self.rename_prefix.setPlaceholderText("前綴 (可選)")
        prefix_layout.addWidget(prefix_label)
        prefix_layout.addWidget(self.rename_prefix)
        
        # 映射輸入框
        mapping_layout = QHBoxLayout()
        mapping_label = QLabel("映射:")
        self.mapping_input = QLineEdit()
        self.mapping_input.setPlaceholderText("格式: [a:aa,b:bb,c:cc,...]")
        mapping_layout.addWidget(mapping_label)
        mapping_layout.addWidget(self.mapping_input)
        
        rename_layout.addWidget(rename_label)
        rename_layout.addWidget(self.rename_checkbox)
        rename_layout.addWidget(self.number_mode)
        rename_layout.addWidget(self.mapping_mode)
        rename_layout.addLayout(prefix_layout)
        rename_layout.addLayout(mapping_layout)
        
        left_layout.addWidget(rename_group)
        
        # 排除當前圖片複選框
        self.exclude_checkbox = QCheckBox("排除當前圖片")
        left_layout.addWidget(self.exclude_checkbox)
        
        # 處理按鈕
        self.process_btn = QPushButton("處理圖片")
        left_layout.addWidget(self.process_btn)
        
        # 文件列表
        self.file_list = QListWidget()
        left_layout.addWidget(self.file_list)
        
        # 右側預覽面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMouseTracking(True)  # 啟用鼠標追蹤
        right_layout.addWidget(self.preview_label)
        
        layout.addWidget(left_panel, 1)
        layout.addWidget(right_panel, 2)
        
        # 連接信號
        self.add_folder_btn.clicked.connect(self.add_folder)
        self.add_files_btn.clicked.connect(self.add_files)
        self.process_btn.clicked.connect(self.process_images)
        self.file_list.currentRowChanged.connect(self.update_preview)
        self.exclude_checkbox.stateChanged.connect(self.toggle_exclude)
        self.color_btn.clicked.connect(self.choose_color)
        self.picker_btn.clicked.connect(self.toggle_color_picker)
        self.preview_label.mousePressEvent = self.preview_mouse_press
        self.preview_label.mouseMoveEvent = self.preview_mouse_move
        
        # 安裝事件過濾器以處理鍵盤事件
        self.installEventFilter(self)
        
        # 添加信號連接
        self.mapping_input.textChanged.connect(self.validate_mapping)
        self.mapping_mode.toggled.connect(self.toggle_rename_mode)
        self.number_mode.toggled.connect(self.toggle_rename_mode)
        
    def toggle_color_picker(self, checked):
        self.is_picking_color = checked
        if checked:
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.CrossCursor))
        else:
            QApplication.restoreOverrideCursor()
            
    def preview_mouse_press(self, event):
        if self.is_picking_color and self.current_preview_image:
            self.pick_color_from_image(event.pos())
            
    def preview_mouse_move(self, event):
        if self.is_picking_color and self.current_preview_image:
            self.pick_color_from_image(event.pos())
            
    def pick_color_from_image(self, pos):
        if not self.current_preview_image:
            return
            
        # 獲取點擊位置相對於圖片的坐標
        preview_size = self.preview_label.size()
        image_size = self.current_preview_image.size()
        
        # 計算圖片在預覽區域中的實際位置和大小
        scale_w = preview_size.width() / image_size.width()
        scale_h = preview_size.height() / image_size.height()
        scale = min(scale_w, scale_h)
        
        scaled_width = int(image_size.width() * scale)
        scaled_height = int(image_size.height() * scale)
        
        x_offset = (preview_size.width() - scaled_width) // 2
        y_offset = (preview_size.height() - scaled_height) // 2
        
        # 計算點擊位置在原圖中的坐標
        x = int((pos.x() - x_offset) / scale)
        y = int((pos.y() - y_offset) / scale)
        
        # 確保坐標在圖片範圍內
        if 0 <= x < image_size.width() and 0 <= y < image_size.height():
            color = self.current_preview_image.pixelColor(x, y)
            self.background_color = color
            self.update_color_preview()
            
    def update_preview(self, index):
        if 0 <= index < len(self.image_files):
            self.current_index = index
            pixmap = QPixmap(self.image_files[index])
            if not pixmap.isNull():
                # 保存當前預覽圖片
                self.current_preview_image = pixmap.toImage()
                
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                
                # 更新排除複選框狀態
                self.exclude_checkbox.setChecked(self.image_files[index] in self.excluded_images)
                
    def show_previous_image(self):
        if self.current_index > 0:
            self.file_list.setCurrentRow(self.current_index - 1)
            
    def show_next_image(self):
        if self.current_index < len(self.image_files) - 1:
            self.file_list.setCurrentRow(self.current_index + 1)
            
    def toggle_exclude(self, state):
        if self.current_index < len(self.image_files):
            current_file = self.image_files[self.current_index]
            if state == Qt.CheckState.Checked.value:
                self.excluded_images.add(current_file)
            else:
                self.excluded_images.discard(current_file)
                
    def choose_color(self):
        color = QColorDialog.getColor(self.background_color, self, "選擇背景顏色")
        if color.isValid():
            self.background_color = color
            self.update_color_preview()
            
    def update_color_preview(self):
        style = f"background-color: {self.background_color.name()}; border: 1px solid black;"
        self.color_preview.setStyleSheet(style)
        
    def toggle_rename_mode(self, checked):
        # 切換重命名模式時更新UI狀態
        self.rename_prefix.setEnabled(self.number_mode.isChecked())
        self.mapping_input.setEnabled(self.mapping_mode.isChecked())
        
    def validate_mapping(self, text):
        """驗證映射格式並更新映射字典"""
        if not text.strip():
            self.rename_mapping = {}
            return
            
        # 檢查基本格式 [key:value,key:value,...]
        if not (text.startswith('[') and text.endswith(']')):
            return
            
        # 提取映射對
        content = text[1:-1].strip()
        if not content:
            return
            
        try:
            # 分割並解析每個映射對
            pairs = content.split(',')
            mapping = {}
            for pair in pairs:
                if ':' not in pair:
                    if pair.strip():  # 如果有內容但沒有冒號
                        key = pair.strip()
                        mapping[key] = key  # 使用相同的值作為映射
                    continue
                    
                key, value = pair.split(':')
                key = key.strip()
                value = value.strip()
                if key and value:  # 確保鍵和值都不為空
                    mapping[key] = value
                    
            self.rename_mapping = mapping
            print("當前映射規則：", self.rename_mapping)  # 調試輸出
            
        except Exception as e:
            print(f"映射解析錯誤: {str(e)}")  # 調試輸出
            self.rename_mapping = {}
            
    def process_images(self):
        if not self.image_files:
            return
            
        rotation = self.rotate_spin.value()
        scale = self.scale_spin.value() / 100.0
        
        # 獲取重命名設置
        should_rename = self.rename_checkbox.isChecked()
        use_mapping = self.mapping_mode.isChecked()
        prefix = self.rename_prefix.text().strip()
        counter = 1
        
        # 驗證映射模式的設置
        if should_rename and use_mapping and not self.rename_mapping:
            QMessageBox.warning(self, "警告", "請輸入有效的重命名映射格式！\n格式: [a:aa,b:bb,c:cc,...]")
            return
            
        # 創建輸出目錄
        if self.image_files:
            first_file_dir = os.path.dirname(self.image_files[0])
            output_dir = os.path.join(first_file_dir, "processed")
            os.makedirs(output_dir, exist_ok=True)
            
        # 獲取填充設置
        should_pad = self.padding_checkbox.isChecked()
        padding = self.padding_spin.value()
        bg_color = (self.background_color.red(),
                   self.background_color.green(),
                   self.background_color.blue(),
                   255)  # 完全不透明
        
        for index, file_path in enumerate(self.image_files):
            if file_path in self.excluded_images:
                continue
                
            try:
                with Image.open(file_path) as img:
                    # 確保圖片有alpha通道
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    # 旋轉
                    if rotation != 0:
                        img = img.rotate(rotation, expand=True)
                    
                    # 縮放
                    if scale != 1.0:
                        new_size = tuple(int(dim * scale) for dim in img.size)
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                    
                    # 填充背景
                    if should_pad:
                        old_size = img.size
                        new_size = (old_size[0] + 2*padding, old_size[1] + 2*padding)
                        new_img = Image.new('RGBA', new_size, bg_color)
                        new_img.paste(img, (padding, padding), img)
                        img = new_img
                    
                    # 生成新文件名
                    original_name = os.path.splitext(os.path.basename(file_path))[0]
                    _, ext = os.path.splitext(file_path)
                    
                    if should_rename:
                        if use_mapping:
                            # 使用映射模式重命名
                            if original_name in self.rename_mapping:
                                new_filename = f"{self.rename_mapping[original_name]}{ext}"
                            else:
                                # 如果找不到映射，使用原始文件名
                                new_filename = f"{original_name}{ext}"
                        else:
                            # 使用數字序列重命名
                            new_filename = f"{prefix}{counter}{ext}" if prefix else f"{counter}{ext}"
                            counter += 1
                    else:
                        # 不重命名，直接使用原始文件名
                        new_filename = os.path.basename(file_path)
                    
                    # 保存到輸出目錄
                    new_path = os.path.join(output_dir, new_filename)
                    
                    # 如果文件已存在，添加編號
                    if os.path.exists(new_path) and not should_rename:
                        base_name, ext = os.path.splitext(new_filename)
                        counter = 1
                        while os.path.exists(new_path):
                            new_filename = f"{base_name}_{counter}{ext}"
                            new_path = os.path.join(output_dir, new_filename)
                            counter += 1
                    
                    img.save(new_path)
                    print(f"保存文件: {new_path}")  # 調試輸出
                    
            except Exception as e:
                print(f"處理圖片 {file_path} 時發生錯誤: {str(e)}")
                QMessageBox.warning(self, "錯誤", f"處理圖片 {file_path} 時發生錯誤: {str(e)}")
                
        QMessageBox.information(self, "完成", f"處理完成！\n輸出目錄: {output_dir}")

    def eventFilter(self, obj, event):
        if event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key.Key_Left:
                self.show_previous_image()
                return True
            elif event.key() == Qt.Key.Key_Right:
                self.show_next_image()
                return True
            elif event.key() == Qt.Key.Key_Escape:  # 按ESC取消吸色器
                if self.is_picking_color:
                    self.picker_btn.setChecked(False)
                    self.toggle_color_picker(False)
                    return True
        return super().eventFilter(obj, event)
        
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "選擇文件夾")
        if folder:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                        full_path = os.path.join(root, file)
                        if full_path not in self.image_files:
                            self.image_files.append(full_path)
                            self.file_list.addItem(file)
            if self.image_files:
                self.update_preview(0)
                
    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "選擇圖片文件",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        for file in files:
            if file not in self.image_files:
                self.image_files.append(file)
                self.file_list.addItem(os.path.basename(file))
        if self.image_files and self.file_list.count() == len(files):
            self.update_preview(0)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageProcessor()
    window.show()
    sys.exit(app.exec()) 