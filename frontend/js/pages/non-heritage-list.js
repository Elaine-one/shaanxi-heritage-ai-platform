// API会通过apiUtils在DOMContentLoaded事件中自动初始化
// 此处无需额外初始化

// 请求缓存对象
const apiCache = {
    data: {},
    // 缓存过期时间：5分钟
    expireTime: 5 * 60 * 1000,
    
    // 设置缓存
    set(key, value) {
        this.data[key] = {
            value: value,
            timestamp: Date.now()
        };
    },
    
    // 获取缓存
    get(key) {
        const cached = this.data[key];
        if (!cached) return null;
        
        // 检查缓存是否过期
        if (Date.now() - cached.timestamp > this.expireTime) {
            // 缓存过期，移除
            delete this.data[key];
            return null;
        }
        
        return cached.value;
    },
    
    // 清除指定缓存
    clear(key) {
        delete this.data[key];
    },
    
    // 清除所有缓存
    clearAll() {
        this.data = {};
    }
};

// 生成缓存键
function generateCacheKey(apiMethod, params) {
    // 排除分页参数，因为不同页的数据不同
    const { page, ...restParams } = params;
    return `${apiMethod}_${JSON.stringify(restParams)}`;
}

// 分页变量
let currentPage = 1;
const itemsPerPage = 12; // 每页显示12个项目（4列3行）
let actualTotalPages = 1; // 新增：存储实际总页数

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();
});

// 页面初始化
async function initPage() {
    try {
        // 更新日期时间
        updateCurrentDate();
        
        // 加载筛选选项
        await loadFilterOptions();
        
        // 设置事件监听器
        setupEventListeners();
        
        // 检查URL参数中是否有搜索关键词
        const urlParams = new URLSearchParams(window.location.search);
        const searchParam = urlParams.get('search');
        
        // 如果URL中有搜索参数，则设置到搜索框中
        if (searchParam) {
            const searchInput = document.getElementById('search-input');
            if (searchInput) {
                searchInput.value = searchParam;
                console.log('从URL参数获取搜索关键词:', searchParam);
            }
        }
        
        // 更新用户头像
        updateUserIcon();
        
        // 直接加载非遗项目数据，不使用本地数据作为备份
        loadHeritageItems();
    } catch (error) {
        console.error('页面初始化失败:', error);
        showErrorMessage('加载数据失败，请刷新页面重试');
    }
}

// 更新当前日期显示
function updateCurrentDate() {
    // 使用统一的日期时间工具模块
    if (window.dateUtils) {
        window.dateUtils.updateDateTimeDisplay('current-date', window.dateUtils.FORMAT.FULL);
    } else {
        // 兼容处理：如果dateUtils模块未加载，使用原始方法
        const dateElement = document.getElementById('current-date');
        if (!dateElement) return;
        
        const now = new Date();
        const options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric', 
            weekday: 'long',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        dateElement.textContent = now.toLocaleDateString('zh-CN', options);
    }
}

// 显示错误消息
function showErrorMessage(message) {
    // 使用公共API工具模块显示错误消息
    if (window.apiUtils) {
        window.apiUtils.showErrorMessage(message, 'heritage-list');
    } else {
        // 兼容处理：如果apiUtils模块未加载，使用原始方法
        const listContainer = document.getElementById('heritage-list');
        if (listContainer) {
            listContainer.innerHTML = `<div class="error-message">${message}</div>`;
        }
    }
}

// 加载筛选选项
async function loadFilterOptions() {
    try {
        // 确保API对象存在
        if (!window.API || !window.API.heritage) {
            console.error('API.heritage 未定义');
            return;
        }
        
        // 并行加载所有选项数据
        // 调用 API.heritage.getLevels() 获取级别信息
        const [categories, levels, regions] = await Promise.all([
            window.API.heritage.getCategories(),
            window.API.heritage.getLevels(), // 重新启用 API.heritage.getLevels()
            window.API.heritage.getRegions()
        ]);
        
        // 填充类别选择器
        const categorySelect = document.getElementById('category-filter');
        categorySelect.innerHTML = '<option value="">全部类别</option>';
        if (Array.isArray(categories)) {
            categories.forEach(category => {
                if (category && typeof category.id !== 'undefined' && typeof category.name !== 'undefined' && String(category.name).trim() !== '') {
                    const option = document.createElement('option');
                    option.value = category.id;
                    option.textContent = category.name;
                    categorySelect.appendChild(option);
                }
            });
        }
        
        // 填充级别选择器
        const levelSelect = document.getElementById('level-filter');
        levelSelect.innerHTML = '<option value="">全部级别</option>';
        // 假设 levels API 返回的是对象数组 {id: 'xxx', name: 'yyy'} 或简单字符串数组
        if (Array.isArray(levels)) {
            levels.forEach(level => {
                const option = document.createElement('option');
                let validOption = false;
                if (typeof level === 'object' && level !== null && typeof level.id !== 'undefined' && typeof level.name !== 'undefined' && String(level.name).trim() !== '') {
                    option.value = level.id;
                    option.textContent = level.name;
                    validOption = true;
                } else if (typeof level === 'string' && level.trim() !== '' && level.toLowerCase() !== 'undefined') {
                    option.value = level;
                    option.textContent = level;
                    validOption = true;
                }
                if (validOption) {
                    levelSelect.appendChild(option);
                }
            });
        }
        levelSelect.disabled = false; // 启用选择器
        
        // 填充地区选择器
        const regionSelect = document.getElementById('region-filter');
        regionSelect.innerHTML = '<option value="">全部地区</option>';
        if (Array.isArray(regions)) {
            regions.forEach(region => {
                if (region && typeof region.id !== 'undefined' && typeof region.name !== 'undefined' && String(region.name).trim() !== '') {
                    const option = document.createElement('option');
                    option.value = region.id;
                    option.textContent = region.name;
                    regionSelect.appendChild(option);
                }
            });
        }
    } catch (error) {
        console.error('加载筛选选项失败:', error);
        throw error;
    }
}

// 防抖函数
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// 设置事件监听器
function setupEventListeners() {
    // 筛选器变更事件
    document.getElementById('level-filter').addEventListener('change', () => {
        currentPage = 1;
        loadHeritageItems();
    });
    
    document.getElementById('category-filter').addEventListener('change', () => {
        currentPage = 1;
        loadHeritageItems();
    });
    
    document.getElementById('region-filter').addEventListener('change', () => {
        currentPage = 1;
        loadHeritageItems();
    });
    
    // 搜索框事件
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');

    if (searchInput && searchBtn) {
        // 创建防抖搜索函数，延迟300ms执行
        const debouncedSearch = debounce(() => {
            currentPage = 1;
            console.log('执行搜索，关键词:', searchInput.value.trim());
            loadHeritageItems();
        }, 300);

        const performSearch = () => {
            currentPage = 1;
            console.log('执行搜索，关键词:', searchInput.value.trim());
            loadHeritageItems();
        };

        // 添加输入事件，使用防抖
        searchInput.addEventListener('input', debouncedSearch);

        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                // 立即执行搜索，不使用防抖
                performSearch();
            }
        });

        searchBtn.addEventListener('click', performSearch);
    } else {
        console.warn('未能找到搜索输入框或搜索按钮，搜索功能可能无法正常工作。');
    }
    
    // 分页按钮事件
    document.getElementById('first-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage = 1;
            loadHeritageItems();
        }
    });
    
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadHeritageItems();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        const totalPages = parseInt(document.getElementById('total-pages').textContent);
        if (currentPage < totalPages) {
            currentPage++;
            loadHeritageItems();
        }
    });
    
    document.getElementById('last-page').addEventListener('click', () => {
        const totalPages = parseInt(document.getElementById('total-pages').textContent);
        if (currentPage < totalPages) {
            currentPage = totalPages;
            loadHeritageItems();
        }
    });
    
    document.getElementById('go-page').addEventListener('click', goToInputPage);
    
    document.getElementById('page-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            goToInputPage();
        }
    });
}

// 跳转到输入的页码
function goToInputPage() {
    const pageInput = document.getElementById('page-input');
    const pageNumber = parseInt(pageInput.value);
    
    // 获取总页数
    const totalPages = parseInt(document.getElementById('total-pages').textContent);
    
    if (pageNumber >= 1 && pageNumber <= totalPages) {
        currentPage = pageNumber;
        loadHeritageItems();
    } else {
        // 输入无效，重置为当前页
        pageInput.value = currentPage;
        alert(`请输入有效的页码 (1-${totalPages})`);
    }
}

// 加载非遗项目数据
async function loadHeritageItems() {
    const listContainer = document.getElementById('heritage-list');
    listContainer.innerHTML = '<div class="loading-indicator">正在加载非遗项目...</div>';
    
    try {
        // 获取筛选条件
        const levelFilter = document.getElementById('level-filter').value;
        const categoryFilter = document.getElementById('category-filter').value;
        const regionFilter = document.getElementById('region-filter').value;
        
        // 获取搜索关键词，优先从URL参数获取
        const urlParams = new URLSearchParams(window.location.search);
        const urlSearchParam = urlParams.get('search');
        
        // 如果URL中有搜索参数但搜索框为空，则将URL参数填入搜索框
        const searchInput = document.getElementById('search-input');
        if (urlSearchParam && (!searchInput.value || searchInput.value.trim() === '')) {
            searchInput.value = urlSearchParam;
        }
        
        // 获取最终的搜索文本（可能来自URL或搜索框）
        const searchText = searchInput.value.trim();
        
        const params = {
            page: currentPage,
            page_size: itemsPerPage
        };
        
        if (levelFilter && levelFilter !== '全部') params.level = levelFilter;
        if (categoryFilter && categoryFilter !== '全部') params.category = categoryFilter;
        if (regionFilter && regionFilter !== '全部') params.region = regionFilter;
        
        // 确保搜索关键词正确传递 - 只使用search参数
        if (searchText) {
            params.search = searchText; // 使用标准的search参数
            console.log('添加搜索关键词:', searchText);
        }
        
        console.log('请求参数:', params);
        
        // 生成缓存键
        const cacheKey = generateCacheKey('getAllItems', params);
        
        // 检查缓存
        const cachedResponse = apiCache.get(cacheKey);
        
        let response;
        if (cachedResponse) {
            console.log('使用缓存数据:', cacheKey);
            response = cachedResponse;
        } else {
            // 确保API对象存在
            if (!window.API || !window.API.heritage || !window.API.heritage.getAllItems) {
                console.error('API.heritage.getAllItems 未定义');
                throw new Error('API未定义');
            }
            
            // 统一使用window.API.heritage.getAllItems
            response = await window.API.heritage.getAllItems(params);
            console.log('API响应:', response);
            
            // 将响应存入缓存
            apiCache.set(cacheKey, response);
        }
        
        if (!response || !response.results) {
            throw new Error('API响应格式不正确');
        }

        // 更新实际总页数
        // 严格使用API返回的count字段
        if (response && typeof response.count === 'number') {
            actualTotalPages = Math.ceil(response.count / itemsPerPage);
            if (currentPage > actualTotalPages) {
                currentPage = actualTotalPages;
            }
        } else {
            console.error('API响应缺少count字段');
            throw new Error('分页数据不完整');
        }
        
        const itemsToDisplay = Array.isArray(response.results) ? response.results.slice(0, itemsPerPage) : [];
        
        updatePagination(); // 调用时不传 response，让它使用全局 currentPage 和 actualTotalPages
        renderHeritageList(itemsToDisplay);

    } catch (error) {
        console.error('加载非遗项目失败:', error);
        
        // 处理404错误
        if (error.status === 404) {
            handle404Error(error, listContainer);
            return;
        }
        
        // 处理其他错误
        listContainer.innerHTML = `<div class="error-message">无法从服务器获取数据（${error.message || '未知错误'}），请检查网络连接或稍后再试。</div>`;
    }
}

// 处理404错误
function handle404Error(apiError, listContainer) {
    if (apiError.data && typeof apiError.data.count === 'number') {
        // We have count information, even with a 404.
        // This likely means we requested a page past the end, but the server still knows the total count.
        const serverTotalCount = apiError.data.count;
        actualTotalPages = Math.ceil(serverTotalCount / itemsPerPage) || 1; // Ensure actualTotalPages is at least 1

        if (currentPage > actualTotalPages) {
            // Requested page is beyond the actual last page
            currentPage = actualTotalPages;
            listContainer.innerHTML = `<div class="no-results">请求的页面不存在，已自动跳转到最后一页 (第 ${currentPage} 页)。</div>`;
            updatePagination(); // Update with new currentPage and actualTotalPages
            // Instead of reloading, if results are in apiError.data, render them if on the last page
            if (apiError.data.results && apiError.data.results.length >= 0) {
               renderHeritageList(apiError.data.results);
            } else {
               renderHeritageList([]); // Render empty if no results for last page
            }
        } else if (currentPage === actualTotalPages) {
            // This is the last page, and it might be empty or partially filled.
            // This is NOT an error. Render whatever results we got (could be an empty array).
            console.log(`正常处理最后一页 (第 ${currentPage} 页) 的404，总项目数: ${serverTotalCount}`);
            updatePagination();
            renderHeritageList(apiError.data.results || []);
        } else {
            // This case should ideally not happen if count is correct and currentPage <= actualTotalPages
            // But as a fallback, treat as a generic "page not found"
            listContainer.innerHTML = `<div class="no-results">请求的页面 (第 ${currentPage} 页) 未找到。总页数: ${actualTotalPages}</div>`;
            updatePagination(); // Update display, but don't reload unless user navigates
        }
    } else {
        // 404 without count information, or currentPage is 1 and still 404 (no items at all)
        if (currentPage > 1) {
            let targetPage = currentPage - 1;
            // Ensure targetPage doesn't exceed a potentially stale actualTotalPages if we don't have fresh count
            if (actualTotalPages > 0 && targetPage > actualTotalPages) {
                 targetPage = actualTotalPages;
            }
            if (targetPage < 1) targetPage = 1;
            currentPage = targetPage;
            listContainer.innerHTML = `<div class="no-results">请求的页面不存在或无更多项目，已自动返回第 ${currentPage} 页。</div>`;
            updatePagination();
            setTimeout(() => loadHeritageItems(), 1500); 
        } else {
            listContainer.innerHTML = '<div class="no-results">没有找到符合条件的非遗项目</div>';
            actualTotalPages = 1;
            currentPage = 1;
            updatePagination();
        }
    }
}

// 更新分页控件
function updatePagination() { 
    const currentPageDisplay = document.getElementById('current-page');
    const totalPagesDisplay = document.getElementById('total-pages');
    const pageInput = document.getElementById('page-input');

    if (currentPageDisplay) currentPageDisplay.textContent = currentPage;
    if (totalPagesDisplay) totalPagesDisplay.textContent = actualTotalPages; 
    if (pageInput) {
        pageInput.value = currentPage;
        pageInput.max = actualTotalPages; 
    }

    updatePaginationButtons();
}

// 更新分页按钮状态
function updatePaginationButtons() {
    const prevButton = document.getElementById('prev-page');
    const nextButton = document.getElementById('next-page');
    const pageInput = document.getElementById('page-input');
    const jumpButton = document.getElementById('jump-to-page');

    if (prevButton) prevButton.disabled = currentPage <= 1;
    if (nextButton) nextButton.disabled = currentPage >= actualTotalPages;
    
    if (pageInput) {
        pageInput.min = 1;
        pageInput.max = actualTotalPages;
        pageInput.disabled = actualTotalPages <= 1;
    }

    if (jumpButton) {
        jumpButton.disabled = actualTotalPages <= 1;
    }
}

// 渲染非遗项目列表
function renderHeritageList(items) {
    const listContainer = document.getElementById('heritage-list');
    
    // 清空容器
    listContainer.innerHTML = '';
    
    // 检查是否有结果
    if (!items || items.length === 0) {
        listContainer.innerHTML = '<div class="no-results">没有找到符合条件的非遗项目</div>';
        return;
    }
    
    // 直接使用API返回的结果，不再进行额外的切片操作
    console.log(`显示 ${items.length} 个项目`);
    
    // 获取当前搜索关键词（如果有）
    const searchText = document.getElementById('search-input').value.trim();
    
    // 渲染每个项目
    items.forEach(item => {
        const itemElement = createHeritageItem(item);
        listContainer.appendChild(itemElement);
    });
    
    // 添加搜索结果提示信息
    const messageElement = document.createElement('div');
    messageElement.className = 'list-message';
    
    if (searchText) {
        messageElement.textContent = `搜索"${searchText}"：找到 ${items.length} 个项目`;
    } else if (items.length < itemsPerPage) {
        messageElement.textContent = `当前条件下共有 ${items.length} 个项目`;
    } else {
        messageElement.textContent = `当前页显示 ${items.length} 个项目（共${actualTotalPages}页）`;
    }
    
    listContainer.appendChild(messageElement);

}

// 创建非遗项目元素
// Helper function to get displayable string or a default value
function getDisplayableString(value, defaultValue = '未知') {
    // 处理对象类型的值（API返回的格式）
    if (value && typeof value === 'object' && value !== null) {
        // 如果有name属性，优先使用name
        if (typeof value.name === 'string' && value.name.trim() !== '') {
            return value.name.trim();
        }
        // 如果没有name但有id属性
        if (typeof value.id === 'string' && value.id.trim() !== '') {
            return value.id.trim();
        }
    }
    // 处理字符串类型的值（本地数据的格式）
    if (value && typeof value === 'string' && value.trim() !== '' && value.toLowerCase() !== 'undefined') {
        return value.trim();
    }
    return defaultValue;
}

// 添加收藏功能
async function addToFavorites(itemId) {
    // 检查用户是否已登录
    const userString = localStorage.getItem('user');
    const user = userString ? JSON.parse(userString) : null;
    
    if (!user || !user.username) {
        // 用户未登录，显示登录提示
        showLoginPrompt();
        return;
    }

    try {
        await window.API.heritage.addFavorite(itemId);
        showToast('已添加到收藏');
        const button = document.querySelector(`.favorite-btn[data-id="${itemId}"]`);
        if (button) {
            button.classList.add('favorited');
            button.textContent = '已收藏';
            button.title = '取消收藏';
        }
    } catch (error) {
        console.error('添加到收藏失败:', error);
        showToast(error.message || '添加到收藏失败');
    }
}

/**
 * 显示登录提示
 */
function showLoginPrompt() {
    // 创建提示框
    const promptDiv = document.createElement('div');
    promptDiv.className = 'login-prompt';
    promptDiv.innerHTML = `
        <div class="login-prompt-content">
            <h3>需要登录</h3>
            <p>收藏功能需要登录后才能使用</p>
            <div class="login-prompt-actions">
                <button id="go-login" class="login-btn">去登录</button>
                <button id="cancel-login" class="cancel-btn">取消</button>
            </div>
        </div>
    `;
    
    // 添加到页面
    document.body.appendChild(promptDiv);
    
    // 添加事件监听
    document.getElementById('go-login').addEventListener('click', function() {
        // 跳转到登录页面
        const isInPagesDir = window.location.pathname.includes('/pages/');
        const loginPath = isInPagesDir ? 'login.html' : 'pages/login.html';
        window.location.href = loginPath;
    });
    
    document.getElementById('cancel-login').addEventListener('click', function() {
        // 移除提示框
        promptDiv.remove();
    });
}

function createHeritageItem(item) {
    const itemElement = document.createElement('div');
    itemElement.className = 'heritage-item';
    
    // 获取图片URL
    const defaultImageUrl = '/media/heritage_images/'; // 默认图片路径，不指定具体文件名
    
    // 处理图片URL - 优先使用后端media文件夹中的图片
    let imageUrl = defaultImageUrl;
    
    // 如果有main_image_url字段，直接使用
    if (item.main_image_url) {
        imageUrl = item.main_image_url;
    } 
    // 如果有images数组，查找主图
    else if (item.images && Array.isArray(item.images) && item.images.length > 0) {
        // 查找标记为主图的图片
        const mainImage = item.images.find(img => img && img.is_main);
        if (mainImage && mainImage.image) {
            // 如果有具体的图片名称，使用heritageImages.getMainImage获取正确路径
            if (typeof window.heritageImages === 'object' && typeof window.heritageImages.getMainImage === 'function') {
                imageUrl = window.heritageImages.getMainImage(item.id, mainImage.image);
            } else {
                imageUrl = mainImage.image;
            }
        } else if (item.images[0] && item.images[0].image) {
            // 如果没有主图标记，使用第一张图片
            if (typeof window.heritageImages === 'object' && typeof window.heritageImages.getMainImage === 'function') {
                imageUrl = window.heritageImages.getMainImage(item.id, item.images[0].image);
            } else {
                imageUrl = item.images[0].image;
            }
        }
    }
    // 使用项目ID直接构建图片路径
    else if (item.id) {
        // 使用heritageImages工具获取图片路径
        if (typeof window.heritageImages === 'object' && typeof window.heritageImages.getMainImage === 'function') {
            imageUrl = window.heritageImages.getMainImage(item.id);
        } else {
            imageUrl = `/media/heritage-items/${item.id}/main.jpg`;
        }
    }
    
    // 确保图片URL是绝对路径或相对于后端的路径
    if (imageUrl && !imageUrl.startsWith('http') && !imageUrl.startsWith('/media/')) {
        // 添加后端media路径前缀，并移除可能存在的media/前缀
        imageUrl = `/media/${imageUrl.replace(/^media\//, '')}`;
    }
    
    // 获取正确的级别、类别和地区信息
    const levelName = getDisplayableString(item.level, '未知级别');
    const categoryName = getDisplayableString(item.category, '未知类别');
    const regionName = getDisplayableString(item.region, '未知地区');
    
    // 设置HTML内容
    itemElement.innerHTML = `
        <div class="heritage-image-container">
            <img src="/static/common/default-heritage.jpg" data-src="${imageUrl}" alt="${item.name}" class="heritage-image" loading="lazy">
            <button class="favorite-btn" onclick="addToFavorites(${item.id})" title="收藏">
                <i class="fa fa-heart-o"></i>
            </button>
        </div>
        <div class="heritage-content">
            <h3 class="heritage-title">${item.name}</h3>
            <div class="heritage-tags">
                <span class="heritage-tag heritage-level">${levelName}</span>
                <span class="heritage-tag heritage-category">${categoryName}</span>
            </div>
            <div class="heritage-region">${regionName}</div>
            <a href="heritage-detail.html?id=${item.id || ''}" class="view-details">查看详情 →</a>
        </div>
    `;
    
    // 添加图片加载事件
    const img = itemElement.querySelector('.heritage-image');
    const container = itemElement.querySelector('.heritage-image-container');
    
    container.classList.add('loading');
    
    // 图片加载完成处理
    img.onload = function() {
        container.classList.remove('loading');
    };
    
    // 图片加载错误处理
    img.onerror = function() {
        container.classList.remove('loading');
        // 使用默认图片
        this.src = '/static/common/default-heritage.jpg';
    };
    
    // 初始化懒加载
    if ('IntersectionObserver' in window) {
        // 如果浏览器支持IntersectionObserver，使用它来触发图片加载
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const lazyImage = entry.target;
                    lazyImage.src = lazyImage.dataset.src;
                    observer.unobserve(lazyImage);
                }
            });
        });
        
        observer.observe(img);
    } else {
        // 降级方案：立即加载所有图片
        img.src = img.dataset.src;
    }
    
    // 添加点击事件
    itemElement.addEventListener('click', function(e) {
        if (!e.target.classList.contains('view-details')) {
            if (item.id && item.id > 0) {
                window.location.href = `heritage-detail.html?id=${item.id}`;
            } else {
                console.warn('无效的项目ID:', item.id);
            }
        }
    });
    
    return itemElement;
}

// 更新用户头像
// updateUserIcon函数已在auth.js中定义，无需重复定义