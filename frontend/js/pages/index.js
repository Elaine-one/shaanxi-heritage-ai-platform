// API会通过apiUtils在DOMContentLoaded事件中自动初始化
// 此处无需额外初始化

// 分页变量
let currentPage = 1;
const itemsPerPage = 12; // 每页显示12个项目（4列3行）

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面
    initPage();
});

// 初始化页面
async function initPage() {
    try {
        // 更新日期时间
        updateCurrentDate();
        
        // 加载非遗数据
        const data = await loadHeritageData();
        
        // 初始化推荐位
        initFeaturedItems(data);
        
        // 初始化搜索
        initSearch(data);
        
        // 初始化地图
        initMap(data);
    } catch (error) {
        console.error('页面初始化失败:', error);
        window.apiUtils.showErrorMessage('加载数据失败，请刷新页面重试');
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

// 使用全局api-utils中的showErrorMessage函数

/**
 * 加载非遗数据
 * @returns {Promise<Array>} 非遗数据数组
 */
async function loadHeritageData() {
    console.log('[loadHeritageData] window.API:', window.API);
    try {
        // 确保API对象存在
        if (!window.API || !window.API.heritage || !window.API.heritage.getAllItems) {
            console.error('API.heritage.getAllItems 未定义');
            return [];
        }
        
        // 尝试从API获取数据
        const response = await window.API.heritage.getAllItems();
        return response.results || [];
    } catch (error) {
        console.error('API调用失败:', error);
        // 不再回退到本地数据，直接抛出错误或显示错误信息
        // showErrorMessage('从服务器获取非遗数据失败，请稍后重试。');
        // return []; // 返回空数组以避免页面完全崩溃，错误将在initPage中处理
        throw error; // 抛出错误，由调用者 (initPage) 处理
    }
}

/**
 * 初始化搜索功能
 * @param {Array} data 非遗数据
 */
function initSearch(data) {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    
    if (!searchInput || !searchButton) return;
    
    // 搜索按钮点击事件
    searchButton.addEventListener('click', () => {
        performSearch(searchInput.value, data);
    });
    
    // 输入框回车事件
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch(searchInput.value, data);
        }
    });
}

/**
 * 执行搜索
 * @param {string} query 搜索关键词
 * @param {Array} data 非遗数据
 */
function performSearch(query, data) {
    if (!query.trim()) {
        alert('请输入搜索关键词');
        return;
    }
    
    // 将搜索关键词添加到URL参数
    const searchParams = new URLSearchParams();
    searchParams.set('search', query.trim());
    
    // 跳转到列表页面，修复路径问题
    window.location.href = `../pages/non-heritage-list.html?${searchParams.toString()}`;
}

/**
 * 初始化地图
 * @param {Array} data 非遗数据
 */
function initMap(data) {
    const mapContainer = document.getElementById('map-preview');
    if (!mapContainer) return;
    
    // 地图初始化代码...
    console.log('地图初始化 (未实现)', data.length);
    
    // 添加查看完整地图按钮点击事件
    const viewMapButton = document.getElementById('view-full-map');
    if (viewMapButton) {
        viewMapButton.addEventListener('click', () => {
            window.location.href = '../pages/heritage-map.html';
        });
    }
}

/**
 * 初始化推荐位
 * @param {Array} data 非遗数据
 */
/**
 * 初始化推荐位
 * @param {Array} data 非遗数据
 */
async function initFeaturedItems(data) {
    // 获取首页的推荐项目容器
    const featuredItems = document.querySelector('.featured-items');
    if (!featuredItems) return;
    
    // 获取所有推荐项目元素
    const itemElements = featuredItems.querySelectorAll('.featured-item');
    if (!itemElements || itemElements.length === 0) return;
    
    // 指定要显示的项目ID
    const featuredIds = [1, 8,22];
    
    try {
        // 确保API对象存在
        if (!window.API || !window.API.heritage) {
            console.error('API.heritage 未定义');
            return;
        }
        
        // 如果data中没有足够的数据，尝试从API获取特定ID的项目
        let featuredItems = [];
        
        // 从现有数据中查找
        if (Array.isArray(data)) {
            featuredItems = featuredIds.map(id => data.find(item => item.id === id)).filter(Boolean);
        }
        
        // 如果没有找到足够的项目，尝试从API获取
        if (featuredItems.length < featuredIds.length) {
            console.log('从API获取推荐项目数据');
            try {
                // 为每个ID单独获取数据
                const apiPromises = featuredIds.map(async id => {
                    try {
                        const response = await window.API.heritage.getAllItems({ id: id });
                        // 处理API返回的两种可能格式：单个对象或包含results数组的对象
                        if (response && response.results && response.results.length > 0) {
                            return response.results[0];
                        } else if (response && response.id) {
                            // 直接返回单个项目对象
                            return response;
                        }
                        return null;
                    } catch (err) {
                        console.warn(`获取ID为${id}的项目失败:`, err);
                        return null;
                    }
                });
                
                // 等待所有请求完成
                const apiResults = await Promise.all(apiPromises);
                
                // 合并结果，优先使用API结果
                featuredItems = featuredIds.map(id => {
                    const apiItem = apiResults.find(item => item && item.id === id);
                    if (apiItem) return apiItem;
                    
                    return featuredItems.find(item => item && item.id === id);
                }).filter(Boolean);
            } catch (apiError) {
                console.error('获取推荐项目数据失败:', apiError);
            }
        }
        
        // 遍历每个推荐项目元素
        itemElements.forEach((itemElement, index) => {
            // 获取元素的data-id属性
            const itemId = parseInt(itemElement.getAttribute('data-id'));
            if (!itemId || !featuredIds.includes(itemId)) return;
            
            // 从数据中查找对应ID的项目
            const item = featuredItems.find(item => item && item.id === itemId);
            if (!item) {
                console.warn(`未找到ID为${itemId}的项目数据`);
                return;
            }
            
            // 获取图片URL
            const defaultImageUrl = '/static/common/default-heritage.jpg';
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
                    imageUrl = mainImage.image;
                } else if (item.images[0] && item.images[0].image) {
                    // 如果没有主图标记，使用第一张图片
                    imageUrl = item.images[0].image;
                }
            }
            
            // 确保图片URL是绝对路径或相对于后端的路径
            // 统一处理媒体路径
            if (imageUrl && !imageUrl.startsWith('http') && !imageUrl.startsWith('/media/')) {
                imageUrl = `/media/${imageUrl.replace(/^media\//, '')}`;
            }
            
            // 更新图片
            const imageElement = itemElement.querySelector('.item-image');
            if (imageElement) {
                // imageElement.src = imageUrl; // Incorrect for div, should use background-image
                // imageElement.alt = item.name || '未知名称'; // alt attribute is not applicable to div elements

                // Use an Image object to handle loading and errors, then set background
                const img = new Image();
                img.onload = () => {
                    imageElement.style.backgroundImage = `url('${imageUrl}')`;
                    imageElement.classList.remove('error'); // Remove error class if image loads successfully
                };
                img.onerror = () => {
                    // Fallback to default image if loading fails
                    imageElement.style.backgroundImage = `url('/static/common/default-heritage.jpg')`;
                    imageElement.classList.add('error');
                };
                img.src = imageUrl; // This initiates the image loading
            }
            
            // 更新标题和描述
            const titleElement = itemElement.querySelector('.item-title');
            if (titleElement) {
                titleElement.textContent = item.name || '未知项目';
            }
            
            const descElement = itemElement.querySelector('.item-desc');
            if (descElement) {
                descElement.textContent = item.brief || '暂无描述';
            }
            
            // 清除旧的点击事件（避免重复绑定）
            const newItemElement = itemElement.cloneNode(true);
            itemElement.parentNode.replaceChild(newItemElement, itemElement);
            
            // 添加新的点击事件
            newItemElement.addEventListener('click', (e) => {
                // 阻止默认行为和事件冒泡
                e.preventDefault();
                e.stopPropagation();
                
                // 跳转到详情页，确保itemId有效
                if (itemId && itemId > 0) {
                    window.location.href = `./pages/heritage-detail.html?id=${itemId}`;
                } else {
                    console.warn('无效的项目ID:', itemId);
                }
            });
            
            // 添加鼠标悬停效果
            newItemElement.addEventListener('mouseenter', () => {
                newItemElement.style.transform = 'translateY(-10px)';
                const img = newItemElement.querySelector('.item-image');
                if (img) {
                    img.style.transform = 'scale(1.05)';
                }
            });
            
            newItemElement.addEventListener('mouseleave', () => {
                newItemElement.style.transform = 'translateY(0)';
                const img = newItemElement.querySelector('.item-image');
                if (img) {
                    img.style.transform = 'scale(1)';
                }
            });
        });
    } catch (error) {
        console.error('初始化推荐项目失败:', error);
    }
}
/**
 * 初始化分类展示 (占位符)
 * @param {Array} data 非遗数据
 */
function initCategoryDisplay(data) {
    console.log('初始化分类展示 (未实现)', data.length);
    // 在这里添加根据数据动态生成分类展示区域的代码
}