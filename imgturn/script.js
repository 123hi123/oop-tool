document.addEventListener('DOMContentLoaded', () => {
    const imageUpload = document.getElementById('image-upload');
    const previewImage = document.getElementById('preview-image');
    const rotationSlider = document.getElementById('rotation-slider');
    const rotationValue = document.getElementById('rotation-value');
    const resetButton = document.getElementById('reset-button');
    const downloadButton = document.getElementById('download-button');
    
    // 當選擇圖片時
    imageUpload.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            // 檢查檔案類型
            if (!file.type.match('image.*')) {
                alert('請選擇圖片文件！');
                return;
            }
            
            const reader = new FileReader();
            
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                // 重置旋轉角度
                rotationSlider.value = 0;
                rotationValue.textContent = '0';
                previewImage.style.transform = 'rotate(0deg)';
                // 啟用下載按鈕
                downloadButton.disabled = false;
            };
            
            reader.readAsDataURL(file);
        }
    });
    
    // 當滑動調整旋轉角度時
    rotationSlider.addEventListener('input', function() {
        const angle = this.value;
        rotationValue.textContent = angle;
        previewImage.style.transform = `rotate(${angle}deg)`;
    });
    
    // 重置按鈕
    resetButton.addEventListener('click', function() {
        rotationSlider.value = 0;
        rotationValue.textContent = '0';
        previewImage.style.transform = 'rotate(0deg)';
    });
    
    // 下載按鈕
    downloadButton.addEventListener('click', function() {
        if (!previewImage.src) {
            alert('請先上傳圖片！');
            return;
        }
        
        // 創建畫布來繪製旋轉後的圖片
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // 等待圖片完全加載
        const img = new Image();
        img.onload = function() {
            // 旋轉角度
            const angle = parseInt(rotationSlider.value);
            const radians = (angle * Math.PI) / 180;
            
            // 計算旋轉後的畫布大小
            let width = img.width;
            let height = img.height;
            
            // 如果旋轉角度不是90度的倍數，需要計算新的畫布大小
            if (angle % 90 !== 0) {
                const cos = Math.abs(Math.cos(radians));
                const sin = Math.abs(Math.sin(radians));
                width = Math.ceil(img.width * cos + img.height * sin);
                height = Math.ceil(img.width * sin + img.height * cos);
            }
            
            // 設定畫布大小
            canvas.width = width;
            canvas.height = height;
            
            // 清除畫布並設為透明
            ctx.clearRect(0, 0, width, height);
            
            // 移動到畫布中心
            ctx.translate(width / 2, height / 2);
            
            // 旋轉
            ctx.rotate(radians);
            
            // 繪製圖片
            ctx.drawImage(img, -img.width / 2, -img.height / 2);
            
            // 將畫布轉換為數據URL
            try {
                // 嘗試保持原始圖片格式
                const originalFormat = getImageFormat(previewImage.src);
                const mimeType = originalFormat === 'png' ? 'image/png' : 'image/jpeg';
                const dataURL = canvas.toDataURL(mimeType, 1.0);
                
                // 創建下載連結
                const a = document.createElement('a');
                const fileName = `rotated_image_${angle}degrees.${originalFormat}`;
                a.href = dataURL;
                a.download = fileName;
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            } catch (error) {
                console.error('下載圖片時出錯：', error);
                alert('下載圖片時出錯，請檢查控制台以獲取詳細信息。');
            }
        };
        
        img.src = previewImage.src;
    });
    
    // 獲取圖片格式
    function getImageFormat(dataURL) {
        if (dataURL.startsWith('data:image/png')) {
            return 'png';
        } else if (dataURL.startsWith('data:image/jpeg') || dataURL.startsWith('data:image/jpg')) {
            return 'jpg';
        } else if (dataURL.startsWith('data:image/gif')) {
            return 'gif';
        } else {
            return 'png';  // 默認為PNG以保持透明度
        }
    }
    
    // 拖放功能
    const previewContainer = document.querySelector('.preview-container');
    
    // 防止瀏覽器預設的拖放行為
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        previewContainer.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // 高亮拖放區域
    ['dragenter', 'dragover'].forEach(eventName => {
        previewContainer.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        previewContainer.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        previewContainer.classList.add('highlight');
    }
    
    function unhighlight() {
        previewContainer.classList.remove('highlight');
    }
    
    // 處理拖放的文件
    previewContainer.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        
        if (file && file.type.match('image.*')) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                // 重置旋轉角度
                rotationSlider.value = 0;
                rotationValue.textContent = '0';
                previewImage.style.transform = 'rotate(0deg)';
                // 啟用下載按鈕
                downloadButton.disabled = false;
            };
            
            reader.readAsDataURL(file);
        } else {
            alert('請拖放圖片文件！');
        }
    }
    
    // 預加載現有圖片
    const urlParams = new URLSearchParams(window.location.search);
    const imageParam = urlParams.get('image');
    
    if (imageParam) {
        previewImage.src = decodeURIComponent(imageParam);
        downloadButton.disabled = false;
    }
}); 