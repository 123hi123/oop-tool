import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, 
                            QComboBox, QSlider, QGroupBox, QListWidget, 
                            QCheckBox, QMessageBox, QColorDialog)
from PyQt6.QtGui import QPixmap, QImage, QColor
from PyQt6.QtCore import Qt
from PIL import Image, ImageEnhance, ImageOps
import numpy as np

class ColorFilterTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("圖片濾鏡工具")
        self.setGeometry(100, 100, 1200, 700)
        
        # 初始化變數
        self.original_images = []  # 存儲多個圖片
        self.current_images = []   # 存儲處理後的多個圖片
        self.image_paths = []      # 存儲所有圖片路徑
        self.selected_image_index = -1  # 當前選擇的圖片索引
        self.filter_color = "red"  # 默認濾鏡顏色
        self.filter_intensity = 0.5  # 默認濾鏡強度
        self.gray_mode = False     # 灰度模式
        self.background_color = (255, 255, 255)  # 默認背景顏色（白色）
        self.bg_threshold = 30     # 背景顏色閾值
        
        # 創建UI
        self.init_ui()
    
    def init_ui(self):
        # 主佈局
        main_layout = QHBoxLayout()
        
        # 左側面板 - 控制區
        left_panel = QVBoxLayout()
        
        # 載入圖片按鈕
        self.load_btn = QPushButton("載入多張圖片")
        self.load_btn.clicked.connect(self.load_images)
        left_panel.addWidget(self.load_btn)
        
        # 圖片列表
        images_group = QGroupBox("已載入圖片")
        images_layout = QVBoxLayout()
        self.images_list = QListWidget()
        self.images_list.currentRowChanged.connect(self.select_image)
        images_layout.addWidget(self.images_list)
        images_group.setLayout(images_layout)
        left_panel.addWidget(images_group)
        
        # 灰度模式選項
        self.gray_checkbox = QCheckBox("灰度模式 (添加_gray後綴)")
        self.gray_checkbox.stateChanged.connect(self.update_filter)
        left_panel.addWidget(self.gray_checkbox)
        
        # 背景顏色設置
        bg_color_group = QGroupBox("背景顏色設置 (灰度模式下)")
        bg_color_layout = QVBoxLayout()
        
        # 選擇背景顏色按鈕
        self.bg_color_btn = QPushButton("選擇背景顏色")
        self.bg_color_btn.clicked.connect(self.select_background_color)
        bg_color_layout.addWidget(self.bg_color_btn)
        
        # 顯示當前背景顏色的標籤
        self.bg_color_preview = QLabel("當前背景顏色")
        self.bg_color_preview.setFixedHeight(20)
        self.bg_color_preview.setStyleSheet(f"background-color: rgb(255, 255, 255); border: 1px solid black;")
        bg_color_layout.addWidget(self.bg_color_preview)
        
        # 背景閾值設置
        bg_threshold_layout = QHBoxLayout()
        bg_threshold_layout.addWidget(QLabel("背景閾值:"))
        self.bg_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.bg_threshold_slider.setMinimum(0)
        self.bg_threshold_slider.setMaximum(100)
        self.bg_threshold_slider.setValue(30)  # 默認30
        self.bg_threshold_slider.valueChanged.connect(self.update_bg_threshold)
        bg_threshold_layout.addWidget(self.bg_threshold_slider)
        self.bg_threshold_label = QLabel("30")
        bg_threshold_layout.addWidget(self.bg_threshold_label)
        bg_color_layout.addLayout(bg_threshold_layout)
        
        bg_color_group.setLayout(bg_color_layout)
        left_panel.addWidget(bg_color_group)
        
        # 濾鏡顏色選擇
        color_group = QGroupBox("濾鏡顏色")
        color_layout = QVBoxLayout()
        self.color_combo = QComboBox()
        self.color_combo.addItems(["紅色 (Red)", "綠色 (Green)", "藍色 (Blue)", 
                                 "黃色 (Yellow)", "紫色 (Purple)", "青色 (Cyan)",
                                 "橙色 (Orange)", "棕色 (Brown)", "粉色 (Pink)"])
        self.color_combo.currentIndexChanged.connect(self.update_filter)
        color_layout.addWidget(self.color_combo)
        color_group.setLayout(color_layout)
        left_panel.addWidget(color_group)
        
        # 強度調節滑桿
        intensity_group = QGroupBox("濾鏡強度")
        intensity_layout = QVBoxLayout()
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setMinimum(0)
        self.intensity_slider.setMaximum(100)
        self.intensity_slider.setValue(50)  # 默認為50%
        self.intensity_slider.valueChanged.connect(self.update_filter)
        self.intensity_label = QLabel("50%")
        intensity_layout.addWidget(self.intensity_slider)
        intensity_layout.addWidget(self.intensity_label)
        intensity_group.setLayout(intensity_layout)
        left_panel.addWidget(intensity_group)
        
        # 處理並保存按鈕
        self.process_all_btn = QPushButton("處理並保存所有圖片")
        self.process_all_btn.clicked.connect(self.process_and_save_all)
        self.process_all_btn.setEnabled(False)  # 初始禁用，直到加載了圖片
        left_panel.addWidget(self.process_all_btn)
        
        # 保存當前按鈕
        self.save_btn = QPushButton("僅保存當前圖片")
        self.save_btn.clicked.connect(self.save_image)
        self.save_btn.setEnabled(False)  # 初始禁用，直到加載了圖片
        left_panel.addWidget(self.save_btn)
        
        # 添加彈性空間
        left_panel.addStretch()
        
        # 右側面板 - 圖片顯示區
        right_panel = QVBoxLayout()
        
        # 原始圖片
        original_group = QGroupBox("原始圖片")
        original_layout = QVBoxLayout()
        self.original_label = QLabel("請載入圖片...")
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setMinimumSize(500, 250)
        original_layout.addWidget(self.original_label)
        original_group.setLayout(original_layout)
        
        # 濾鏡效果圖片
        filtered_group = QGroupBox("濾鏡效果")
        filtered_layout = QVBoxLayout()
        self.filtered_label = QLabel("處理後的圖片會顯示在這裡...")
        self.filtered_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filtered_label.setMinimumSize(500, 250)
        filtered_layout.addWidget(self.filtered_label)
        filtered_group.setLayout(filtered_layout)
        
        right_panel.addWidget(original_group)
        right_panel.addWidget(filtered_group)
        
        # 將左右面板添加到主佈局
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(300)
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget)
        
        # 設置主窗口
        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def select_background_color(self):
        color = QColorDialog.getColor(QColor(*self.background_color), self, "選擇背景顏色")
        if color.isValid():
            self.background_color = (color.red(), color.green(), color.blue())
            self.bg_color_preview.setStyleSheet(f"background-color: rgb({color.red()}, {color.green()}, {color.blue()}); border: 1px solid black;")
            self.update_filter()
    
    def update_bg_threshold(self):
        value = self.bg_threshold_slider.value()
        self.bg_threshold_label.setText(str(value))
        self.bg_threshold = value
        self.update_filter()
    
    def load_images(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "選擇多張圖片", "", "圖片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_paths:
            # 清除現有圖片
            self.original_images = []
            self.current_images = []
            self.image_paths = []
            self.images_list.clear()
            
            # 加載新的圖片
            for file_path in file_paths:
                # 保存路徑
                self.image_paths.append(file_path)
                
                # 添加到列表
                image_name = os.path.basename(file_path)
                self.images_list.addItem(image_name)
                
                # 使用PIL打開圖片
                try:
                    img = Image.open(file_path)
                    self.original_images.append(img)
                    self.current_images.append(None)  # 先設為None，等待處理
                except Exception as e:
                    print(f"無法載入圖片 {file_path}: {e}")
            
            # 如果有圖片被載入
            if self.original_images:
                self.process_all_btn.setEnabled(True)
                # 選擇第一張圖片
                self.images_list.setCurrentRow(0)
                self.select_image(0)
    
    def select_image(self, index):
        if index < 0 or index >= len(self.original_images):
            return
        
        self.selected_image_index = index
        self.update_filter()  # 應用濾鏡
        self.save_btn.setEnabled(True)  # 啟用保存按鈕
    
    def update_filter(self):
        if not self.original_images or self.selected_image_index < 0:
            return
        
        # 獲取當前滑桿值並更新標籤
        intensity_value = self.intensity_slider.value()
        self.intensity_label.setText(f"{intensity_value}%")
        self.filter_intensity = intensity_value / 100.0
        
        # 獲取選擇的濾鏡顏色
        color_index = self.color_combo.currentIndex()
        color_name = ["red", "green", "blue", "yellow", "purple", "cyan", 
                     "orange", "brown", "pink"][color_index]
        self.filter_color = color_name
        
        # 獲取灰度模式狀態
        self.gray_mode = self.gray_checkbox.isChecked()
        
        # 應用濾鏡到當前選擇的圖片
        self.apply_filter(self.selected_image_index)
        
        # 更新顯示
        self.update_display()
    
    def apply_filter(self, index):
        if index < 0 or index >= len(self.original_images):
            return
        
        # 複製原始圖片
        img = self.original_images[index].copy()
        
        # 先檢查是否應用灰度模式
        if self.gray_mode:
            # 轉換為numpy數組進行處理
            img_array = np.array(img)
            
            # 根據圖片模式處理
            if img.mode == "RGBA":
                # 有透明通道，保留完全透明的部分不變
                alpha_channel = img_array[:, :, 3]
                
                # 創建新的圖像數組，初始化為原始圖像
                gray_array = img_array.copy()
                
                # 首先檢測背景像素（這裡有兩種方式：透明度或接近背景顏色）
                is_background = np.zeros_like(alpha_channel, dtype=bool)
                
                # 方式1：完全透明的像素
                if np.any(alpha_channel < 255):
                    is_background = (alpha_channel < 128)  # 透明度小於128
                
                # 方式2：顏色接近背景顏色的像素
                br, bg, bb = self.background_color
                threshold = self.bg_threshold
                
                # 計算每個像素與背景顏色的差異
                color_diff = np.abs(img_array[:, :, 0] - br) + \
                             np.abs(img_array[:, :, 1] - bg) + \
                             np.abs(img_array[:, :, 2] - bb)
                
                # 合併兩種背景檢測方法
                is_background = is_background | (color_diff < threshold * 3)
                
                # 將非背景部分轉換為灰度
                # 先計算灰度值
                gray_values = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
                gray_values = gray_values.astype(np.uint8)
                
                # 只對非背景部分應用灰度
                for i in range(3):  # R, G, B通道
                    gray_array[:, :, i] = np.where(is_background, img_array[:, :, i], gray_values)
                
                # 保存處理後的圖片
                self.current_images[index] = Image.fromarray(gray_array)
                
            else:
                # 沒有透明通道的圖片
                if img.mode != "RGB":
                    img = img.convert("RGB")
                    img_array = np.array(img)
                
                # 檢測接近背景顏色的像素
                br, bg, bb = self.background_color
                threshold = self.bg_threshold
                
                color_diff = np.abs(img_array[:, :, 0] - br) + \
                             np.abs(img_array[:, :, 1] - bg) + \
                             np.abs(img_array[:, :, 2] - bb)
                
                is_background = (color_diff < threshold * 3)
                
                # 創建新的數組，初始化為原始圖像
                gray_array = img_array.copy()
                
                # 計算灰度值
                gray_values = 0.299 * img_array[:, :, 0] + 0.587 * img_array[:, :, 1] + 0.114 * img_array[:, :, 2]
                gray_values = gray_values.astype(np.uint8)
                
                # 只對非背景部分應用灰度
                for i in range(3):  # R, G, B通道
                    gray_array[:, :, i] = np.where(is_background, img_array[:, :, i], gray_values)
                
                # 保存處理後的圖片
                self.current_images[index] = Image.fromarray(gray_array)
                
            return
        
        # 獲取濾鏡顏色RGB值
        color_map = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "purple": (128, 0, 128),
            "cyan": (0, 255, 255),
            "orange": (255, 165, 0),
            "brown": (165, 42, 42),
            "pink": (255, 192, 203)
        }
        
        r, g, b = color_map[self.filter_color]
        
        # 將圖片轉換為numpy數組進行處理
        img_array = np.array(img)
        
        # 如果圖片是RGBA格式，保留Alpha通道
        if img.mode == "RGBA":
            # 獲取原始Alpha通道
            alpha_channel = img_array[:, :, 3]
            
            # 應用濾鏡，保持原始顏色的一部分，添加濾鏡顏色的一部分
            tinted_array = img_array.copy()
            tinted_array[:, :, 0] = img_array[:, :, 0] * (1 - self.filter_intensity) + r * self.filter_intensity
            tinted_array[:, :, 1] = img_array[:, :, 1] * (1 - self.filter_intensity) + g * self.filter_intensity
            tinted_array[:, :, 2] = img_array[:, :, 2] * (1 - self.filter_intensity) + b * self.filter_intensity
            
            # 確保值在0-255範圍內
            tinted_array = np.clip(tinted_array, 0, 255).astype(np.uint8)
            
            # 保存處理後的圖片
            self.current_images[index] = Image.fromarray(tinted_array)
        else:
            # 非RGBA圖片處理
            if img.mode != "RGB":
                img = img.convert("RGB")
                img_array = np.array(img)
            
            # 應用濾鏡，保持原始顏色的一部分，添加濾鏡顏色的一部分
            tinted_array = img_array.copy()
            tinted_array[:, :, 0] = img_array[:, :, 0] * (1 - self.filter_intensity) + r * self.filter_intensity
            tinted_array[:, :, 1] = img_array[:, :, 1] * (1 - self.filter_intensity) + g * self.filter_intensity
            tinted_array[:, :, 2] = img_array[:, :, 2] * (1 - self.filter_intensity) + b * self.filter_intensity
            
            # 確保值在0-255範圍內
            tinted_array = np.clip(tinted_array, 0, 255).astype(np.uint8)
            
            # 保存處理後的圖片
            self.current_images[index] = Image.fromarray(tinted_array)
    
    def update_display(self):
        if self.selected_image_index < 0 or not self.original_images:
            return
            
        # 顯示原始圖片
        original_img = self.original_images[self.selected_image_index].copy()
        original_img.thumbnail((500, 300))  # 調整大小以適應顯示區域
        original_qimg = self.pil_to_qimage(original_img)
        original_pixmap = QPixmap.fromImage(original_qimg)
        self.original_label.setPixmap(original_pixmap)
        
        # 顯示處理後的圖片
        if self.current_images[self.selected_image_index] is not None:
            filtered_img = self.current_images[self.selected_image_index].copy()
            filtered_img.thumbnail((500, 300))  # 調整大小以適應顯示區域
            filtered_qimg = self.pil_to_qimage(filtered_img)
            filtered_pixmap = QPixmap.fromImage(filtered_qimg)
            self.filtered_label.setPixmap(filtered_pixmap)
    
    def pil_to_qimage(self, pil_image):
        # 將PIL圖像轉換為QImage
        if pil_image.mode == "RGB":
            data = pil_image.convert("RGB").tobytes("raw", "RGB")
            return QImage(data, pil_image.size[0], pil_image.size[1], pil_image.size[0] * 3, QImage.Format.Format_RGB888)
        elif pil_image.mode == "RGBA":
            data = pil_image.convert("RGBA").tobytes("raw", "RGBA")
            return QImage(data, pil_image.size[0], pil_image.size[1], pil_image.size[0] * 4, QImage.Format.Format_RGBA8888)
        elif pil_image.mode == "L":
            # 灰度圖像
            data = pil_image.tobytes("raw", "L")
            return QImage(data, pil_image.size[0], pil_image.size[1], pil_image.size[0], QImage.Format.Format_Grayscale8)
        else:
            # 轉換其他模式為RGB
            pil_image = pil_image.convert("RGB")
            return self.pil_to_qimage(pil_image)
    
    def process_and_save_all(self):
        # 處理所有圖片
        for i in range(len(self.original_images)):
            # 應用濾鏡
            self.apply_filter(i)
            
            # 保存處理後的圖片
            self.save_specific_image(i)
        
        # 顯示完成消息
        QMessageBox.information(self, "處理完成", f"已處理並保存 {len(self.original_images)} 張圖片")
    
    def save_image(self):
        if self.selected_image_index < 0 or not self.current_images[self.selected_image_index]:
            return
        
        # 保存當前選中的圖片
        self.save_specific_image(self.selected_image_index)
        
        # 顯示保存成功消息
        file_name = os.path.basename(self.image_paths[self.selected_image_index])
        self.statusBar().showMessage(f"圖片已保存: {file_name}", 3000)
    
    def save_specific_image(self, index):
        if index < 0 or index >= len(self.image_paths) or not self.current_images[index]:
            return
        
        # 獲取原始路徑信息
        file_path = self.image_paths[index]
        image_dir = os.path.dirname(file_path)
        image_name = os.path.basename(file_path)
        image_name_without_ext, image_ext = os.path.splitext(image_name)
        
        # 根據處理模式確定新文件名
        if self.gray_mode:
            suffix = "_gray"
        else:
            suffix = f"_{self.filter_color}"
        
        new_filename = f"{image_name_without_ext}{suffix}{image_ext}"
        save_path = os.path.join(image_dir, new_filename)
        
        # 保存圖片
        self.current_images[index].save(save_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorFilterTool()
    window.show()
    sys.exit(app.exec()) 