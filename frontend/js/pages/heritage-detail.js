// 页面加载完成后执行


document.addEventListener('DOMContentLoaded', function() {
    console.log('详情页面加载完成');
    
    // 加载浏览历史模块
    const historyScript = document.createElement('script');
    historyScript.src = '../js/common/browsing-history.js';
    document.head.appendChild(historyScript);
    
    // 获取URL参数中的项目ID
    const urlParams = new URLSearchParams(window.location.search);
    const itemId = parseInt(urlParams.get('id'));
    console.log('获取到项目ID:', itemId);
    
    // 检查ID是否有效
    if (isNaN(itemId)) {
        console.error('项目ID无效');
        showErrorMessage('项目ID无效，请返回列表页重新选择');
        return;
    }
    
    // 显示加载中
    showLoading();
    
    // 从API获取详情数据
    heritageAPI.getItemDetail(itemId)
        .then(item => {
            if (!item) {
                showErrorMessage('未找到该非遗项目');
                return;
            }
            
            // 渲染详情
            renderHeritageDetail(item);
            
            // 隐藏加载中
            hideLoading();
            
            // 添加到浏览历史
            if (typeof addToHistory === 'function') {
                addToHistory(item);
            } else {
                // 如果浏览历史模块尚未加载完成，等待加载
                historyScript.onload = function() {
                    addToHistory(item);
                };
            }
        })
        .catch(error => {
            console.error('加载详情失败:', error);
            showErrorMessage('加载详情失败，请稍后重试');
        });
        
    // 添加收藏按钮点击事件监听
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'favorite-btn') {
            toggleFavorite(itemId);
        }
    });
});




// 使用全局api-utils中的showErrorMessage函数
function showErrorMessage(message) {
    if (window.apiUtils && window.apiUtils.showErrorMessage) {
        window.apiUtils.showErrorMessage(message, 'heritage-detail-container');
    } else {
        // 回退到原有实现
        const detailContainer = document.querySelector('.heritage-detail-container');
        if (detailContainer) {
            detailContainer.innerHTML = `
                <div class="error-message">
                    <h2>出错了</h2>
                    <p>${message}</p>
                    <a href="non-heritage-list.html" class="back-button">返回列表页</a>
                </div>
            `;
        }
    }
}

// 渲染项目详情
function renderHeritageDetail(item) {
    console.log('开始渲染项目详情:', item.name);
    
    // 获取容器元素
    const detailContainer = document.querySelector('.heritage-detail-container');
    if (!detailContainer) {
        console.error('未找到详情容器元素');
        return;
    }
    
    // 使用基本路径，不指定具体文件名
    // 从 API 返回的 images 数组中查找主图片
    const mainImageObj = item.images && item.images.find(img => img.is_main);
    // 使用 API 提供的完整 URL，如果找不到主图或没有图片，则使用空字符串
    const mainImagePath = mainImageObj ? mainImageObj.image : '';
    
    // 构建HTML结构
    let detailHTML = `
        <h1 class="heritage-title">${item.name}</h1>
        
        <div class="heritage-info-section">
            <div class="heritage-main-image">
                <img src="${mainImagePath}" alt="${item.name}">
                <div class="image-overlay"></div>
            </div>
            
            <div class="heritage-basic-info">
                <div class="heritage-meta">
                    <div class="heritage-meta-item"><strong>级别:</strong> ${item.level}</div>
                    <div class="heritage-meta-item"><strong>类别:</strong> ${item.category}</div>
                    <div class="heritage-meta-item"><strong>地区:</strong> ${item.region}</div>
                </div>
            
                <div class="heritage-description">
                    ${item.description}
                </div>
            </div>
        </div>
        
        <!-- 添加历史背景部分 -->
        <div class="heritage-history-section">
            <h2 class="history-title">历史背景</h2>
            <div class="heritage-history">
                ${item.history || '暂无历史背景信息'}
            </div>
        </div>
        
        <div class="heritage-gallery-section">
            <h2 class="gallery-title">项目图集</h2>
            <div id="gallery-container" class="gallery-container">
                <div class="loading-indicator">正在加载图片...</div>
            </div>
        </div>
    `;
    






    

    
    // 添加返回按钮
    detailHTML += `
        <a href="non-heritage-list.html" class="back-button">返回列表</a>
    `;
    
    // 更新容器内容
    detailContainer.innerHTML = detailHTML;
    
    // 主图片已在 HTML 中设置 src，无需额外加载逻辑
    
    // 加载图集
    loadGalleryImages(item);
}

// 加载图集图片
function loadGalleryImages(item) {
    console.log('加载图集图片');
    
    const galleryContainer = document.getElementById('gallery-container');
    if (!galleryContainer) {
        console.error('未找到图集容器');
        return;
    }
    
    // 清空容器
    galleryContainer.innerHTML = '';
    
    // 确保gallery-container使用网格布局
    galleryContainer.style.display = 'grid';
    galleryContainer.style.gridTemplateColumns = 'repeat(2, 1fr)';
    galleryContainer.style.gap = '20px';
    galleryContainer.style.width = '100%';
    galleryContainer.style.maxWidth = '1000px';
    galleryContainer.style.margin = '20px auto';
    
    // 使用 API 返回的包含完整 URL 的 images 数组
    if (item.images && item.images.length > 0) {
        item.images.forEach(imageObj => {
            // 创建gallery-item容器
            const galleryItem = document.createElement('div');
            galleryItem.className = 'gallery-item';
            
            // 创建图片容器，用于实现悬停效果
            const imgContainer = document.createElement('div');
            imgContainer.className = 'gallery-img-container';
            imgContainer.style.position = 'relative';
            imgContainer.style.overflow = 'hidden';
            imgContainer.style.borderRadius = '8px';
            imgContainer.style.aspectRatio = '4/3';
            imgContainer.style.backgroundColor = '#f5f5f5';
            
            // imageObj.image 已经是完整的 URL
            const imgUrl = imageObj.image;
            const imgElement = document.createElement('img');
            imgElement.src = imgUrl;
            imgElement.alt = item.name;
            imgElement.classList.add('gallery-img');
            imgElement.style.width = '100%';
            imgElement.style.height = '100%';
            imgElement.style.objectFit = 'cover';
            imgElement.style.transition = 'transform 0.5s ease';
            
            // 添加错误处理
            imgElement.onerror = function() {
                this.src = '/static/common/default-image.jpg';
                this.onerror = null;
            };
            
            // 将图片添加到图片容器中
            imgContainer.appendChild(imgElement);
            
            // 创建悬停遮罩
            const overlay = document.createElement('div');
            overlay.className = 'gallery-overlay';
            overlay.style.position = 'absolute';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100%';
            overlay.style.height = '100%';
            overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
            overlay.style.opacity = '0';
            overlay.style.transition = 'opacity 0.3s ease';
            overlay.style.display = 'flex';
            overlay.style.justifyContent = 'center';
            overlay.style.alignItems = 'center';
            overlay.style.color = 'white';
            overlay.style.fontSize = '24px';
            
            // 创建放大图标
            const zoomIcon = document.createElement('div');
            zoomIcon.innerHTML = '🔍';
            zoomIcon.style.transform = 'scale(0)';
            zoomIcon.style.transition = 'transform 0.3s ease';
            overlay.appendChild(zoomIcon);
            
            // 添加悬停效果
            imgContainer.addEventListener('mouseover', function() {
                overlay.style.opacity = '1';
                zoomIcon.style.transform = 'scale(1)';
                imgElement.style.transform = 'scale(1.1)';
            });
            
            imgContainer.addEventListener('mouseout', function() {
                overlay.style.opacity = '0';
                zoomIcon.style.transform = 'scale(0)';
                imgElement.style.transform = 'scale(1)';
            });

            
            // 将遮罩添加到图片容器
            imgContainer.appendChild(overlay);
            
            // 将图片容器添加到gallery-item
            galleryItem.appendChild(imgContainer);
            
            // 添加图片说明文字
            const caption = document.createElement('div');
            caption.className = 'gallery-caption';
            caption.textContent = imageObj.description || `${item.name}图片${item.images.indexOf(imageObj) + 1}`;
            caption.style.padding = '10px 5px';
            caption.style.textAlign = 'center';
            caption.style.fontWeight = '500';
            caption.style.color = '#333';
            galleryItem.appendChild(caption);
            
            // 点击放大
            galleryItem.addEventListener('click', function() {
                openLightbox(imgUrl, caption.textContent);
            });


            // 将gallery-item添加到gallery-container中
            galleryContainer.appendChild(galleryItem);
        });

    } else {
        // 没有图片时显示美化后的提示信息，使用emoji代替图标
        galleryContainer.innerHTML = '<div class="no-images-message"><div class="icon">🖼️</div><p class="title">暂无项目图片</p><p class="subtitle">该非遗项目暂未上传相关图片资料</p></div>';
    }
}

// 图片放大功能实现

// 图片放大功能
function openLightbox(imageSrc, imageAlt) {
    // 获取当前项目的所有图片
    const allGalleryItems = document.querySelectorAll('.gallery-item');
    const allImages = [];
    let currentIndex = -1;
    
    // 收集所有图片信息
    allGalleryItems.forEach((item, index) => {
        const img = item.querySelector('img');
        const caption = item.querySelector('.gallery-caption');
        if (img) {
            const imgInfo = {
                src: img.src,
                alt: caption ? caption.textContent : img.alt
            };
            allImages.push(imgInfo);
            
            // 找到当前图片的索引
            if (img.src === imageSrc) {
                currentIndex = index;
            }
        }
    });

    
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'lightbox-overlay';
    
    // 创建图片容器
    const imgContainer = document.createElement('div');
    imgContainer.style.position = 'relative';
    imgContainer.style.width = '85%';
    imgContainer.style.height = '85%';
    imgContainer.style.display = 'flex';
    imgContainer.style.justifyContent = 'center';
    imgContainer.style.alignItems = 'center';
    imgContainer.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
    imgContainer.style.borderRadius = '12px';
    imgContainer.style.padding = '20px';
    imgContainer.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.3)';
    imgContainer.style.backdropFilter = 'blur(5px)';
    
    // 创建背景模糊效果
    const blurBg = document.createElement('div');
    blurBg.style.position = 'absolute';
    blurBg.style.top = '0';
    blurBg.style.left = '0';
    blurBg.style.width = '100%';
    blurBg.style.height = '100%';
    blurBg.style.backgroundImage = `url(${imageSrc})`;
    blurBg.style.backgroundSize = 'cover';
    blurBg.style.backgroundPosition = 'center';
    blurBg.style.filter = 'blur(30px) brightness(0.3)';
    blurBg.style.opacity = '0.4';
    blurBg.style.borderRadius = '12px';
    blurBg.style.zIndex = '-1';
    
    // 创建图片
    const img = document.createElement('img');
    img.src = imageSrc;
    img.alt = imageAlt;
    img.style.maxWidth = '100%';
    img.style.maxHeight = '100%';
    img.style.objectFit = 'contain';
    img.style.border = '3px solid rgba(255, 255, 255, 0.2)';
    img.style.borderRadius = '8px';
    img.style.boxShadow = '0 5px 25px rgba(0, 0, 0, 0.5)';
    img.style.zIndex = '2';
    
    // 添加加载动画
    const loadingIndicator = document.createElement('div');
    loadingIndicator.className = 'loading-spinner';
    loadingIndicator.style.position = 'absolute';
    loadingIndicator.style.top = '50%';
    loadingIndicator.style.left = '50%';
    loadingIndicator.style.transform = 'translate(-50%, -50%)';
    loadingIndicator.style.width = '50px';
    loadingIndicator.style.height = '50px';
    loadingIndicator.style.border = '5px solid rgba(255, 255, 255, 0.3)';
    loadingIndicator.style.borderTop = '5px solid white';
    loadingIndicator.style.borderRadius = '50%';
    loadingIndicator.style.animation = 'spin 1s linear infinite';
    loadingIndicator.style.zIndex = '3';
    
    // 图片加载完成后隐藏加载动画
    img.onload = function() {
        loadingIndicator.style.display = 'none';
    };
    
    // 创建标题
    const titleElement = document.createElement('div');
    titleElement.textContent = imageAlt;
    titleElement.style.position = 'absolute';
    titleElement.style.bottom = '10px';
    titleElement.style.left = '0';
    titleElement.style.width = '100%';
    titleElement.style.textAlign = 'center';
    titleElement.style.color = 'white';
    titleElement.style.padding = '10px';
    titleElement.style.fontSize = '16px';
    titleElement.style.fontWeight = 'bold';
    titleElement.style.textShadow = '0 1px 3px rgba(0, 0, 0, 0.8)';
    titleElement.style.zIndex = '2';
    
    // 创建关闭按钮
    const closeBtn = document.createElement('div');
    closeBtn.innerHTML = '&times;';
    closeBtn.className = 'lightbox-close';
    
    // 添加关闭事件
    closeBtn.addEventListener('click', function() {
        document.body.removeChild(overlay);
    });
    
    // 点击遮罩层也可以关闭
    overlay.addEventListener('click', function(e) {
        if (e.target === overlay) {
            document.body.removeChild(overlay);
        }
    });

    
    // 添加键盘事件支持
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && document.body.contains(overlay)) {
            document.body.removeChild(overlay);
        }
        
        // 左右箭头切换图片
        if (allImages.length > 1) {
            if (e.key === 'ArrowLeft' && document.body.contains(overlay)) {
                navigateImage(-1);
            } else if (e.key === 'ArrowRight' && document.body.contains(overlay)) {
                navigateImage(1);
            }
        }
    });

    
    // 如果有多张图片，添加导航按钮
    if (allImages.length > 1) {
        // 创建左侧导航按钮
        const prevBtn = document.createElement('div');
        prevBtn.className = 'lightbox-nav lightbox-nav-prev';
        prevBtn.innerHTML = '&#10094;';
        prevBtn.style.position = 'absolute';
        prevBtn.style.left = '20px';
        prevBtn.style.top = '50%';
        prevBtn.style.transform = 'translateY(-50%)';
        prevBtn.style.color = 'white';
        prevBtn.style.fontSize = '30px';
        prevBtn.style.cursor = 'pointer';
        prevBtn.style.zIndex = '3';
        prevBtn.style.width = '50px';
        prevBtn.style.height = '50px';
        prevBtn.style.display = 'flex';
        prevBtn.style.justifyContent = 'center';
        prevBtn.style.alignItems = 'center';
        prevBtn.style.backgroundColor = 'rgba(0, 0, 0, 0.3)';
        prevBtn.style.borderRadius = '50%';
        prevBtn.style.transition = 'background-color 0.3s';
        
        prevBtn.addEventListener('mouseover', function() {
            this.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
        });
        
        prevBtn.addEventListener('mouseout', function() {
            this.style.backgroundColor = 'rgba(0, 0, 0, 0.3)';
        });
        
        prevBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            navigateImage(-1);
        });

        
        // 创建右侧导航按钮
        const nextBtn = document.createElement('div');
        nextBtn.className = 'lightbox-nav lightbox-nav-next';
        nextBtn.innerHTML = '&#10095;';
        nextBtn.style.position = 'absolute';
        nextBtn.style.right = '20px';
        nextBtn.style.top = '50%';
        nextBtn.style.transform = 'translateY(-50%)';
        nextBtn.style.color = 'white';
        nextBtn.style.fontSize = '30px';
        nextBtn.style.cursor = 'pointer';
        nextBtn.style.zIndex = '3';
        nextBtn.style.width = '50px';
        nextBtn.style.height = '50px';
        nextBtn.style.display = 'flex';
        nextBtn.style.justifyContent = 'center';
        nextBtn.style.alignItems = 'center';
        nextBtn.style.backgroundColor = 'rgba(0, 0, 0, 0.3)';
        nextBtn.style.borderRadius = '50%';
        nextBtn.style.transition = 'background-color 0.3s';
        
        nextBtn.addEventListener('mouseover', function() {
            this.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
        });
        
        nextBtn.addEventListener('mouseout', function() {
            this.style.backgroundColor = 'rgba(0, 0, 0, 0.3)';
        });
        
        nextBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            navigateImage(1);
        });

        
        imgContainer.appendChild(prevBtn);
        imgContainer.appendChild(nextBtn);
    }
    
    // 导航到上一张/下一张图片
    function navigateImage(direction) {
        if (allImages.length <= 1) return;
        
        currentIndex = (currentIndex + direction + allImages.length) % allImages.length;
        const newImage = allImages[currentIndex];
        
        // 显示加载动画
        loadingIndicator.style.display = 'block';
        
        // 更新图片和标题
        img.src = newImage.src;
        img.alt = newImage.alt;
        titleElement.textContent = newImage.alt;
        
        // 更新背景
        blurBg.style.backgroundImage = `url(${newImage.src})`;
        
        // 尝试加载高清版本
        const highResPath = newImage.src.replace(/(\.\w+)$/, '-hd$1');
        const highResImage = new Image();
        highResImage.onload = function() {
            img.src = this.src;
            blurBg.style.backgroundImage = `url(${this.src})`;
        };
        highResImage.src = highResPath;
    }
    
    // 组装并添加到页面
    imgContainer.appendChild(blurBg);
    imgContainer.appendChild(loadingIndicator);
    imgContainer.appendChild(img);
    imgContainer.appendChild(titleElement);
    imgContainer.appendChild(closeBtn);
    overlay.appendChild(imgContainer);
    document.body.appendChild(overlay);
    
    // 添加淡入效果
    overlay.style.opacity = '0';
    imgContainer.style.transform = 'scale(0.9)';
    imgContainer.style.transition = 'transform 0.3s ease-out';
    overlay.style.transition = 'opacity 0.3s ease-out';
    
    setTimeout(() => {
        overlay.style.opacity = '1';
        imgContainer.style.transform = 'scale(1)';
    }, 10);
    
    // 尝试加载高清版本图片
    const highResImage = new Image();
    highResImage.onload = function() {
        img.src = this.src;
        // 更新背景图片
        blurBg.style.backgroundImage = `url(${this.src})`;
    };
    
    // 构建高清图片路径 (如果有的话)
    const highResPath = imageSrc.replace(/(\.\w+)$/, '-hd$1');
    highResImage.src = highResPath;
}

// 显示加载中提示
function showLoading() {
    const detailContainer = document.querySelector('.heritage-detail-container');
    if (detailContainer) {
        detailContainer.innerHTML = `
            <div class="loading-indicator">
                <div class="spinner"></div>
                <p>正在加载非遗项目详情...</p>
            </div>
        `;
    }
}

// 隐藏加载中提示
function hideLoading() {
    // 加载完成后，加载提示会被详情内容替换，无需额外操作
    console.log('加载完成');
}

