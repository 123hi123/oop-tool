import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os

class ImageSlicer:
    def __init__(self, root):
        self.root = root
        self.root.title("圖片切割工具")
        
        # 變量初始化
        self.image_path = None
        self.original_image = None
        self.photo_image = None
        self.canvas_image = None
        self.vertical_lines = []
        self.horizontal_lines = []
        self.canvas_width = 800
        self.canvas_height = 600
        self.scale_factor = 1.0
        
        self.setup_ui()
        
    def setup_ui(self):
        # 創建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 按鈕框架
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(self.button_frame, text="選擇圖片", command=self.load_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="添加垂直線", command=self.add_vertical_line).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="添加水平線", command=self.add_horizontal_line).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="清除所有線", command=self.clear_lines).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.button_frame, text="切割圖片", command=self.slice_image).pack(side=tk.LEFT, padx=5)
        
        # 創建畫布
        self.canvas = tk.Canvas(self.main_frame, width=self.canvas_width, height=self.canvas_height,
                              bg='white', relief='solid', bd=1)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 綁定事件
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        
        # 狀態標籤
        self.status_label = ttk.Label(self.root, text="請選擇一張圖片開始")
        self.status_label.pack(pady=5)
        
    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff")])
        
        if file_path:
            self.image_path = file_path
            self.original_image = Image.open(file_path)
            self.resize_image()
            self.display_image()
            self.status_label.config(text=f"已載入圖片: {os.path.basename(file_path)}")
            
    def resize_image(self):
        # 計算縮放比例
        width, height = self.original_image.size
        width_scale = self.canvas_width / width
        height_scale = self.canvas_height / height
        self.scale_factor = min(width_scale, height_scale)
        
        new_width = int(width * self.scale_factor)
        new_height = int(height * self.scale_factor)
        
        resized_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(resized_image)
        
    def display_image(self):
        self.canvas.delete("all")
        self.vertical_lines.clear()
        self.horizontal_lines.clear()
        
        # 在畫布中央顯示圖片
        x = (self.canvas_width - self.photo_image.width()) // 2
        y = (self.canvas_height - self.photo_image.height()) // 2
        self.canvas_image = self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo_image)
        
    def add_vertical_line(self):
        if not self.photo_image:
            messagebox.showwarning("警告", "請先載入圖片")
            return
            
        x = self.canvas_width // 2
        line = self.canvas.create_line(x, 0, x, self.canvas_height, fill='red', width=2)
        self.vertical_lines.append(line)
        
    def add_horizontal_line(self):
        if not self.photo_image:
            messagebox.showwarning("警告", "請先載入圖片")
            return
            
        y = self.canvas_height // 2
        line = self.canvas.create_line(0, y, self.canvas_width, y, fill='blue', width=2)
        self.horizontal_lines.append(line)
        
    def clear_lines(self):
        for line in self.vertical_lines + self.horizontal_lines:
            self.canvas.delete(line)
        self.vertical_lines.clear()
        self.horizontal_lines.clear()
        
    def on_press(self, event):
        self.canvas.scan_mark(event.x, event.y)
        
    def on_drag(self, event):
        closest = self.canvas.find_closest(event.x, event.y)
        if closest and closest[0] in self.vertical_lines:
            # 移動垂直線
            self.canvas.coords(closest[0], event.x, 0, event.x, self.canvas_height)
        elif closest and closest[0] in self.horizontal_lines:
            # 移動水平線
            self.canvas.coords(closest[0], 0, event.y, self.canvas_width, event.y)
            
    def on_release(self, event):
        pass
        
    def slice_image(self):
        if not self.original_image or not (self.vertical_lines or self.horizontal_lines):
            messagebox.showwarning("警告", "請先載入圖片並添加切割線")
            return
            
        # 獲取保存目錄
        save_dir = filedialog.askdirectory(title="選擇保存目錄")
        if not save_dir:
            return
            
        # 獲取圖片在畫布上的位置
        canvas_x = self.canvas.coords(self.canvas_image)[0]
        canvas_y = self.canvas.coords(self.canvas_image)[1]
        
        # 獲取所有切割線的位置
        v_cuts = []
        h_cuts = []
        
        for line in self.vertical_lines:
            x = self.canvas.coords(line)[0]
            # 轉換為原始圖片的坐標
            original_x = int((x - canvas_x) / self.scale_factor)
            if 0 < original_x < self.original_image.width:
                v_cuts.append(original_x)
                
        for line in self.horizontal_lines:
            y = self.canvas.coords(line)[1]
            # 轉換為原始圖片的坐標
            original_y = int((y - canvas_y) / self.scale_factor)
            if 0 < original_y < self.original_image.height:
                h_cuts.append(original_y)
                
        # 排序切割點
        v_cuts.sort()
        h_cuts.sort()
        
        # 執行切割
        regions = []
        start_y = 0
        
        # 如果沒有水平切割線，使用整個高度
        if not h_cuts:
            h_cuts = [self.original_image.height]
        
        # 如果沒有垂直切割線，使用整個寬度
        if not v_cuts:
            v_cuts = [self.original_image.width]
            
        for end_y in h_cuts:
            start_x = 0
            for end_x in v_cuts:
                regions.append((start_x, start_y, end_x, end_y))
                start_x = end_x
            if start_x < self.original_image.width:
                regions.append((start_x, start_y, self.original_image.width, end_y))
            start_y = end_y
            
        if start_y < self.original_image.height:
            start_x = 0
            for end_x in v_cuts:
                regions.append((start_x, start_y, end_x, self.original_image.height))
                start_x = end_x
            if start_x < self.original_image.width:
                regions.append((start_x, start_y, self.original_image.width, self.original_image.height))
                
        # 保存切割後的圖片
        for i, region in enumerate(regions):
            cropped = self.original_image.crop(region)
            save_path = os.path.join(save_dir, f'slice_{i+1}.png')
            cropped.save(save_path)
            
        messagebox.showinfo("完成", f"已將圖片切割為 {len(regions)} 份並保存到選擇的目錄")
        
if __name__ == '__main__':
    root = tk.Tk()
    app = ImageSlicer(root)
    root.mainloop() 