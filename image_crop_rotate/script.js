document.addEventListener('DOMContentLoaded', function() {
    // 獲取元素
    const imageInput = document.getElementById('imageInput');
    const sourceCanvas = document.getElementById('sourceCanvas');
    const selectionCanvas = document.getElementById('selectionCanvas');
    const previewCanvas = document.getElementById('previewCanvas');
    const previewContainer = document.querySelector('.preview-container');
    const rotateLeftBtn = document.getElementById('rotateLeftBtn');
    const rotateRightBtn = document.getElementById('rotateRightBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const resetBtn = document.getElementById('resetBtn');
    
    // 畫布上下文
    const sourceCtx = sourceCanvas.getContext('2d');
    const selectionCtx = selectionCanvas.getContext('2d');
    const previewCtx = previewCanvas.getContext('2d');
    
    // 固定畫布大小
    const CANVAS_SIZE = 1024;
    
    // 變數
    let originalImage = null;
    let isSelecting = false;
    let pathPoints = []; // 儲存繪製路徑的點
    let croppedImage = null;
    let rotationAngle = 0;
    let originalImageScale = 1; // 原始圖片的縮放比例
    
    // 圖片上傳處理
    imageInput.addEventListener('change', function(e) {
        if (e.target.files && e.target.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(event) {
                const img = new Image();
                img.onload = function() {
                    originalImage = img;
                    resetSelection();
                    drawOriginalImage();
                };
                img.src = event.target.result;
            };
            
            reader.readAsDataURL(e.target.files[0]);
        }
    });
    
    // 繪製原始圖片
    function drawOriginalImage() {
        if (!originalImage) return;
        
        // 設定固定大小的畫布
        sourceCanvas.width = CANVAS_SIZE;
        sourceCanvas.height = CANVAS_SIZE;
        selectionCanvas.width = CANVAS_SIZE;
        selectionCanvas.height = CANVAS_SIZE;
        
        // 隱藏預覽區域
        previewContainer.style.display = 'none';
        
        // 計算縮放比例，保持圖片比例
        const scale = Math.min(
            CANVAS_SIZE / originalImage.width,
            CANVAS_SIZE / originalImage.height
        );
        
        // 保存縮放比例，用於之後的座標轉換
        originalImageScale = scale;
        
        // 計算居中顯示的位置
        const x = (CANVAS_SIZE - originalImage.width * scale) / 2;
        const y = (CANVAS_SIZE - originalImage.height * scale) / 2;
        
        // 清除畫布
        sourceCtx.clearRect(0, 0, sourceCanvas.width, sourceCanvas.height);
        
        // 繪製灰色背景（可以清楚地看到圖片範圍）
        sourceCtx.fillStyle = '#f0f0f0';
        sourceCtx.fillRect(0, 0, sourceCanvas.width, sourceCanvas.height);
        
        // 繪製圖片
        sourceCtx.drawImage(
            originalImage,
            x, y,
            originalImage.width * scale,
            originalImage.height * scale
        );
        
        // 設置畫布容器的尺寸
        const canvasContainer = document.querySelector('.canvas-container');
        canvasContainer.style.width = CANVAS_SIZE + 'px';
        canvasContainer.style.height = CANVAS_SIZE + 'px';
        
        // 清除選擇區域
        selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
        
        // 顯示提示
        displayInstructions();
    }
    
    // 顯示使用提示
    function displayInstructions() {
        selectionCtx.font = '16px Arial';
        selectionCtx.fillStyle = 'black';
        selectionCtx.fillText('點擊圖片上的點以創建選擇區域，點擊第一個點完成選擇', 20, 30);
    }
    
    // 點擊事件監聽，用於選擇頂點
    selectionCanvas.addEventListener('click', addSelectionPoint);
    
    // 滑鼠移動事件，用於預覽線段
    selectionCanvas.addEventListener('mousemove', previewSelectionLine);
    
    // 雙擊事件，用於完成選擇
    selectionCanvas.addEventListener('dblclick', function() {
        if (pathPoints.length >= 3) {
            completeSelection();
            cropImage(); // 自動裁剪
        }
    });
    
    // 添加選擇點
    function addSelectionPoint(e) {
        if (!originalImage) return;
        
        const rect = selectionCanvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // 檢查是否點擊了第一個點（完成封閉路徑）
        if (pathPoints.length > 2) {
            const firstPoint = pathPoints[0];
            const distance = Math.sqrt(
                Math.pow(x - firstPoint.x, 2) + Math.pow(y - firstPoint.y, 2)
            );
            
            // 如果點擊接近第一個點，則封閉路徑
            if (distance < 20) {
                completeSelection();
                // 自動裁剪
                cropImage();
                return;
            }
        }
        
        // 添加新點
        pathPoints.push({x, y});
        
        // 重新繪製路徑
        drawSelectionPath();
    }
    
    // 預覽選擇線段
    function previewSelectionLine(e) {
        if (!originalImage || pathPoints.length === 0) return;
        
        const rect = selectionCanvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // 重新繪製路徑
        drawSelectionPath();
        
        // 繪製預覽線段
        selectionCtx.beginPath();
        selectionCtx.moveTo(pathPoints[pathPoints.length - 1].x, pathPoints[pathPoints.length - 1].y);
        selectionCtx.lineTo(x, y);
        selectionCtx.strokeStyle = '#3498db';
        selectionCtx.lineWidth = 2;
        selectionCtx.stroke();
        
        // 如果有多個點，且滑鼠接近第一個點，則顯示可以封閉路徑的提示
        if (pathPoints.length > 2) {
            const firstPoint = pathPoints[0];
            const distance = Math.sqrt(
                Math.pow(x - firstPoint.x, 2) + Math.pow(y - firstPoint.y, 2)
            );
            
            if (distance < 20) {
                selectionCtx.beginPath();
                selectionCtx.arc(firstPoint.x, firstPoint.y, 10, 0, Math.PI * 2);
                selectionCtx.fillStyle = 'rgba(52, 152, 219, 0.3)';
                selectionCtx.fill();
                selectionCtx.stroke();
            }
        }
    }
    
    // 完成選擇區域
    function completeSelection() {
        if (pathPoints.length < 3) {
            alert('請至少選擇三個點以形成有效的區域');
            return;
        }
        
        // 封閉路徑
        drawSelectionMask();
    }
    
    // 繪製選擇路徑
    function drawSelectionPath() {
        // 清除畫布
        selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
        
        // 如果沒有點，則顯示提示
        if (pathPoints.length === 0) {
            displayInstructions();
            return;
        }
        
        // 繪製已選擇的點和線段
        selectionCtx.beginPath();
        selectionCtx.moveTo(pathPoints[0].x, pathPoints[0].y);
        
        for (let i = 1; i < pathPoints.length; i++) {
            selectionCtx.lineTo(pathPoints[i].x, pathPoints[i].y);
        }
        
        selectionCtx.strokeStyle = '#3498db';
        selectionCtx.lineWidth = 2;
        selectionCtx.stroke();
        
        // 繪製頂點
        for (const point of pathPoints) {
            selectionCtx.beginPath();
            selectionCtx.arc(point.x, point.y, 5, 0, Math.PI * 2);
            selectionCtx.fillStyle = '#3498db';
            selectionCtx.fill();
        }
    }
    
    // 繪製選擇區域遮罩
    function drawSelectionMask() {
        // 創建臨時畫布用於遮罩
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = selectionCanvas.width;
        tempCanvas.height = selectionCanvas.height;
        const tempCtx = tempCanvas.getContext('2d');
        
        // 繪製路徑
        tempCtx.beginPath();
        tempCtx.moveTo(pathPoints[0].x, pathPoints[0].y);
        for (let i = 1; i < pathPoints.length; i++) {
            tempCtx.lineTo(pathPoints[i].x, pathPoints[i].y);
        }
        tempCtx.closePath();
        
        // 填充路徑內部
        tempCtx.fillStyle = 'rgba(255, 255, 255, 1)';
        tempCtx.fill();
        
        // 清除選擇畫布
        selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
        
        // 繪製半透明遮罩
        selectionCtx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        selectionCtx.fillRect(0, 0, selectionCanvas.width, selectionCanvas.height);
        
        // 使用目標區域作為剪切區域
        selectionCtx.globalCompositeOperation = 'destination-out';
        selectionCtx.drawImage(tempCanvas, 0, 0);
        selectionCtx.globalCompositeOperation = 'source-over';
        
        // 重新繪製邊框
        selectionCtx.beginPath();
        selectionCtx.moveTo(pathPoints[0].x, pathPoints[0].y);
        for (let i = 1; i < pathPoints.length; i++) {
            selectionCtx.lineTo(pathPoints[i].x, pathPoints[i].y);
        }
        selectionCtx.closePath();
        selectionCtx.strokeStyle = '#3498db';
        selectionCtx.lineWidth = 2;
        selectionCtx.stroke();
        
        // 繪製頂點
        for (const point of pathPoints) {
            selectionCtx.beginPath();
            selectionCtx.arc(point.x, point.y, 5, 0, Math.PI * 2);
            selectionCtx.fillStyle = '#3498db';
            selectionCtx.fill();
        }
    }
    
    // 裁剪圖片
    function cropImage() {
        if (pathPoints.length < 3) return;
        
        // 找出繪製區域的邊界
        let minX = Number.MAX_SAFE_INTEGER;
        let minY = Number.MAX_SAFE_INTEGER;
        let maxX = 0;
        let maxY = 0;
        
        for (const point of pathPoints) {
            minX = Math.min(minX, point.x);
            minY = Math.min(minY, point.y);
            maxX = Math.max(maxX, point.x);
            maxY = Math.max(maxY, point.y);
        }
        
        const width = maxX - minX;
        const height = maxY - minY;
        
        // 創建臨時畫布用於裁剪
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = width;
        tempCanvas.height = height;
        const tempCtx = tempCanvas.getContext('2d');
        
        // 繪製路徑（偏移到邊界）
        tempCtx.beginPath();
        tempCtx.moveTo(pathPoints[0].x - minX, pathPoints[0].y - minY);
        for (let i = 1; i < pathPoints.length; i++) {
            tempCtx.lineTo(pathPoints[i].x - minX, pathPoints[i].y - minY);
        }
        tempCtx.closePath();
        
        // 剪切路徑內部區域
        tempCtx.save();
        tempCtx.clip();
        
        // 將原始圖像繪製到臨時畫布（僅顯示剪切區域內的內容）
        tempCtx.drawImage(
            sourceCanvas,
            minX, minY, width, height,
            0, 0, width, height
        );
        
        tempCtx.restore();
        
        // 獲取裁剪後的圖像數據
        croppedImage = tempCanvas;
        
        // 設置預覽畫布的大小
        previewCanvas.width = width;
        previewCanvas.height = height;
        
        // 重置旋轉角度
        rotationAngle = 0;
        
        // 繪製預覽
        drawPreview();
        
        // 顯示預覽區域
        previewContainer.style.display = 'block';
    }
    
    // 繪製預覽
    function drawPreview() {
        // 設置畫布大小
        const maxSize = 300;
        const scale = Math.min(1, maxSize / Math.max(croppedImage.width, croppedImage.height));
        const displayWidth = croppedImage.width * scale;
        const displayHeight = croppedImage.height * scale;
        
        // 計算旋轉後需要的畫布大小（基於對角線長度）
        // 對於任意角度旋轉，需要足夠的空間容納整個旋轉後的圖像
        const diagonalLength = Math.sqrt(displayWidth * displayWidth + displayHeight * displayHeight);
        const canvasSize = Math.ceil(diagonalLength);
        
        // 設置預覽畫布大小（足夠大以容納任何角度的旋轉）
        previewCanvas.width = canvasSize;
        previewCanvas.height = canvasSize;
        
        // 清除畫布
        previewCtx.clearRect(0, 0, previewCanvas.width, previewCanvas.height);
        
        // 將原點移到畫布中心
        previewCtx.save();
        previewCtx.translate(previewCanvas.width / 2, previewCanvas.height / 2);
        
        // 旋轉
        previewCtx.rotate(rotationAngle * Math.PI / 180);
        
        // 繪製圖像（相對於中心點）
        previewCtx.drawImage(
            croppedImage,
            -displayWidth / 2,
            -displayHeight / 2,
            displayWidth,
            displayHeight
        );
        
        // 恢復畫布狀態
        previewCtx.restore();
        
        // 更新旋轉角度顯示
        if (document.getElementById('rotationValue')) {
            document.getElementById('rotationValue').textContent = rotationAngle + '°';
        }
    }
    
    // 向左旋轉
    rotateLeftBtn.addEventListener('click', function() {
        rotationAngle = (rotationAngle - 90) % 360;
        // 更新滑動條的值
        if (document.getElementById('rotationSlider')) {
            document.getElementById('rotationSlider').value = rotationAngle;
        }
        drawPreview();
    });
    
    // 向右旋轉
    rotateRightBtn.addEventListener('click', function() {
        rotationAngle = (rotationAngle + 90) % 360;
        // 更新滑動條的值
        if (document.getElementById('rotationSlider')) {
            document.getElementById('rotationSlider').value = rotationAngle;
        }
        drawPreview();
    });
    
    // 下載圖片
    downloadBtn.addEventListener('click', function() {
        // 創建臨時畫布用於導出
        const exportCanvas = document.createElement('canvas');
        
        // 計算旋轉後需要的畫布大小，基於對角線長度
        const diagonalLength = Math.sqrt(croppedImage.width * croppedImage.width + croppedImage.height * croppedImage.height);
        const canvasSize = Math.ceil(diagonalLength);
        
        // 設置導出畫布大小（足夠大以容納任何角度的旋轉）
        exportCanvas.width = canvasSize;
        exportCanvas.height = canvasSize;
        
        const exportCtx = exportCanvas.getContext('2d');
        
        // 設置透明背景
        exportCtx.clearRect(0, 0, exportCanvas.width, exportCanvas.height);
        
        // 將原點移到畫布中心
        exportCtx.translate(exportCanvas.width / 2, exportCanvas.height / 2);
        
        // 旋轉
        exportCtx.rotate(rotationAngle * Math.PI / 180);
        
        // 繪製圖像
        exportCtx.drawImage(
            croppedImage,
            -croppedImage.width / 2,
            -croppedImage.height / 2,
            croppedImage.width,
            croppedImage.height
        );
        
        // 創建裁剪後的畫布，去除多餘的透明區域
        const trimmedCanvas = trimCanvas(exportCanvas);
        
        // 創建下載連結
        const link = document.createElement('a');
        link.download = 'cropped_image.png';
        link.href = trimmedCanvas.toDataURL('image/png');
        link.click();
    });
    
    // 裁剪掉透明區域，只保留有內容的部分
    function trimCanvas(canvas) {
        const ctx = canvas.getContext('2d');
        const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = pixels.data;
        
        let left = canvas.width;
        let top = canvas.height;
        let right = 0;
        let bottom = 0;
        
        // 掃描像素數據，找出非透明區域的邊界
        for (let x = 0; x < canvas.width; x++) {
            for (let y = 0; y < canvas.height; y++) {
                const index = (y * canvas.width + x) * 4;
                // 檢查像素是否非透明 (alpha > 0)
                if (data[index + 3] > 0) {
                    left = Math.min(left, x);
                    top = Math.min(top, y);
                    right = Math.max(right, x);
                    bottom = Math.max(bottom, y);
                }
            }
        }
        
        // 計算實際內容區域的寬高
        const trimWidth = right - left + 1;
        const trimHeight = bottom - top + 1;
        
        // 確保有真實內容
        if (trimWidth <= 0 || trimHeight <= 0) {
            return canvas;
        }
        
        // 創建新畫布，僅包含非透明區域
        const trimmedCanvas = document.createElement('canvas');
        trimmedCanvas.width = trimWidth;
        trimmedCanvas.height = trimHeight;
        
        // 繪製有內容的部分
        const trimmedCtx = trimmedCanvas.getContext('2d');
        trimmedCtx.drawImage(
            canvas,
            left, top, trimWidth, trimHeight,
            0, 0, trimWidth, trimHeight
        );
        
        return trimmedCanvas;
    }
    
    // 重置選擇
    resetBtn.addEventListener('click', function() {
        resetSelection();
        if (originalImage) {
            drawOriginalImage();
        }
    });
    
    // 重置選擇區域
    function resetSelection() {
        pathPoints = [];
        isSelecting = false;
        rotationAngle = 0;
        croppedImage = null;
        previewContainer.style.display = 'none';
        
        // 清除畫布
        if (selectionCanvas.width > 0) {
            selectionCtx.clearRect(0, 0, selectionCanvas.width, selectionCanvas.height);
            displayInstructions();
        }
    }
    
    // 添加旋轉角度控制滑動條
    function createRotationSlider() {
        const sliderContainer = document.createElement('div');
        sliderContainer.className = 'rotation-slider-container';
        sliderContainer.style.margin = '15px 0';
        sliderContainer.style.display = 'flex';
        sliderContainer.style.alignItems = 'center';
        
        const sliderLabel = document.createElement('label');
        sliderLabel.textContent = '旋轉角度: ';
        sliderLabel.htmlFor = 'rotationSlider';
        sliderLabel.style.marginRight = '10px';
        
        const slider = document.createElement('input');
        slider.type = 'range';
        slider.id = 'rotationSlider';
        slider.min = '0';
        slider.max = '359';
        slider.value = '0';
        slider.style.flex = '1';
        
        const valueDisplay = document.createElement('span');
        valueDisplay.id = 'rotationValue';
        valueDisplay.textContent = '0°';
        valueDisplay.style.marginLeft = '10px';
        valueDisplay.style.minWidth = '40px';
        valueDisplay.style.textAlign = 'right';
        
        sliderContainer.appendChild(sliderLabel);
        sliderContainer.appendChild(slider);
        sliderContainer.appendChild(valueDisplay);
        
        // 當滑動條值變化時更新旋轉角度
        slider.addEventListener('input', function() {
            rotationAngle = parseInt(this.value);
            drawPreview();
        });
        
        return sliderContainer;
    }
    
    // 在預覽控制區域中添加旋轉滑動條
    const sliderContainer = createRotationSlider();
    const controlsDiv = document.querySelector('.controls');
    controlsDiv.insertBefore(sliderContainer, downloadBtn);
    
    // 添加"確認選擇"按鈕
    const confirmBtn = document.createElement('button');
    confirmBtn.textContent = '確認選擇';
    confirmBtn.id = 'confirmBtn';
    confirmBtn.style.background = '#f39c12';
    confirmBtn.addEventListener('click', function() {
        if (pathPoints.length >= 3) {
            cropImage();
        } else if (pathPoints.length > 0) {
            alert('請至少選擇三個點以形成有效的區域');
        } else {
            alert('請先在圖片上選擇區域');
        }
    });
    
    const canvasContainer = document.querySelector('.canvas-container');
    canvasContainer.insertAdjacentElement('afterend', confirmBtn);
}); 