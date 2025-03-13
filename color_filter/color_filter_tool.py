import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, 
                            QComboBox, QSlider, QGroupBox)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from PIL import Image, ImageEnhance, ImageOps
import numpy as np

class ColorFilterTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("圖片濾鏡工具")
        self.setGeometry(100, 100, 1000, 600)
        
        # 初始化變數
        self.original_image = None
        self.current_image = None
        self.filter_color = "red"  # 默認濾鏡顏色
        self.filter_intensity = 0.5  # 默認濾鏡強度
        
        # 創建UI
        self.init_ui()
    
    def init_ui(self):
        # 主佈局
        main_layout = QHBoxLayout()
        
        # 左側面板 - 控制區
        left_panel = QVBoxLayout()
        
        # 載入圖片按鈕
        self.load_btn = QPushButton("載入圖片")
        self.load_btn.clicked.connect(self.load_image)
        left_panel.addWidget(self.load_btn)
        
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
        
        # 保存按鈕
        self.save_btn = QPushButton("保存圖片")
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
        self.original_label = QLabel()
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setMinimumSize(400, 200)
        original_layout.addWidget(self.original_label)
        original_group.setLayout(original_layout)
        
        # 濾鏡效果圖片
        filtered_group = QGroupBox("濾鏡效果")
        filtered_layout = QVBoxLayout()
        self.filtered_label = QLabel()
        self.filtered_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filtered_label.setMinimumSize(400, 200)
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
    
    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "選擇圖片", "", "圖片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            # 保存原始路徑和文件名
            self.image_path = file_path
            self.image_dir = os.path.dirname(file_path)
            self.image_name = os.path.basename(file_path)
            self.image_name_without_ext = os.path.splitext(self.image_name)[0]
            self.image_ext = os.path.splitext(self.image_name)[1]
            
            # 使用PIL打開圖片
            self.original_image = Image.open(file_path)
            self.update_filter()  # 應用濾鏡
            self.save_btn.setEnabled(True)  # 啟用保存按鈕
    
    def update_filter(self):
        if self.original_image is None:
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
        
        # 應用濾鏡
        self.apply_filter()
        
        # 更新顯示
        self.update_display()
    
    def apply_filter(self):
        # 複製原始圖片
        img = self.original_image.copy()
        
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
            self.current_image = Image.fromarray(tinted_array)
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
            self.current_image = Image.fromarray(tinted_array)
    
    def update_display(self):
        # 顯示原始圖片
        original_img = self.original_image.copy()
        original_img.thumbnail((400, 300))  # 調整大小以適應顯示區域
        original_qimg = self.pil_to_qimage(original_img)
        original_pixmap = QPixmap.fromImage(original_qimg)
        self.original_label.setPixmap(original_pixmap)
        
        # 顯示處理後的圖片
        filtered_img = self.current_image.copy()
        filtered_img.thumbnail((400, 300))  # 調整大小以適應顯示區域
        filtered_qimg = self.pil_to_qimage(filtered_img)
        filtered_pixmap = QPixmap.fromImage(filtered_qimg)
        self.filtered_label.setPixmap(filtered_pixmap)
    
    def pil_to_qimage(self, pil_image):
        # 將PIL圖像轉換為QImage
        if pil_image.mode == "RGB":
            r, g, b = pil_image.split()
            img = QImage(pil_image.size[0], pil_image.size[1], QImage.Format.Format_RGB32)
            for x in range(pil_image.size[0]):
                for y in range(pil_image.size[1]):
                    img.setPixel(x, y, (r.getpixel((x, y)) << 16) | 
                                      (g.getpixel((x, y)) << 8) | 
                                       b.getpixel((x, y)))
            return img
        elif pil_image.mode == "RGBA":
            data = pil_image.convert("RGBA").tobytes("raw", "RGBA")
            return QImage(data, pil_image.size[0], pil_image.size[1], QImage.Format.Format_RGBA8888)
        else:
            # 轉換其他模式為RGB
            pil_image = pil_image.convert("RGB")
            return self.pil_to_qimage(pil_image)
    
    def save_image(self):
        if self.current_image is None:
            return
        
        # 生成新的文件名
        color_suffix = f"_{self.filter_color}"
        new_filename = f"{self.image_name_without_ext}{color_suffix}{self.image_ext}"
        save_path = os.path.join(self.image_dir, new_filename)
        
        # 保存圖片
        self.current_image.save(save_path)
        
        # 顯示保存成功消息
        self.statusBar().showMessage(f"圖片已保存為 {new_filename}", 3000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorFilterTool()
    window.show()
    sys.exit(app.exec()) 