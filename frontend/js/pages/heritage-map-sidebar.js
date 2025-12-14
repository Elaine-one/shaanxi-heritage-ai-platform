/**
 * 非遗地图左侧栏功能管理
 * 包括筛选功能、项目清单、预览和收藏系统
 */

// 全局变量
let collections = []; // 收藏的项目

/**
 * 初始化左侧栏
 * @param {Array} heritageData 非遗项目数据
 */
function initSidebar(heritageData) {
    console.log('初始化侧边栏...', heritageData?.length || 0, '个项目');
    
    // 保存数据到全局变量，确保其他函数可以访问
    window.heritageData = heritageData || [];
    
    // 添加筛选器
    addFilters();
    
    // 添加项目列表容器
    addFilteredProjectsContainer();
    
    // 初始化收藏系统
    initCollectionSystem();
    
    // 立即应用筛选，显示所有数据
    if (window.HeritageFilters && typeof window.HeritageFilters.applyFilters === 'function') {
        window.HeritageFilters.applyFilters(window.heritageData);
    }
    
    console.log('侧边栏初始化完成');
}

// 引用筛选功能
// 注意：这里使用全局变量而非ES模块导入
// 确保heritage-filters.js在HTML中先于此脚本加载
const { initFilters, applyFilters, resetFilters } = window.HeritageFilters || {};

/**
 * 添加筛选器功能
 */
function addFilters() {
    // 初始化筛选器
    initFilters(window.heritageData);
}

/**
 * 添加项目清单容器
 */
function addFilteredProjectsContainer() {
    // 项目清单容器已经在HTML中存在，不需要动态创建
    console.log('项目清单容器已存在于HTML中');
}

/**
 * 更新项目清单
 * @param {Array} items 筛选后的项目数组
 */
window.updateFilteredProjectList = function(items) {
    console.log('更新项目清单...', items?.length || 0);
    const listContainer = document.getElementById('filtered-project-list');
    
    // 如果容器不存在，记录错误并返回
    if (!listContainer) {
        console.error('无法找到项目清单容器 #filtered-project-list');
        return;
    }
    
    // 清空列表
    listContainer.innerHTML = '';
    
    // 如果items不是数组或为空，显示提示
    if (!Array.isArray(items) || items.length === 0) {
        listContainer.innerHTML = '<div class="project-empty">没有符合条件的项目</div>';
        return;
    }
    
    // 对项目按级别和名称排序
    try {
        const sortedItems = [...items].sort((a, b) => {
            // 首先按级别排序
            const levelOrder = {
                '国家级': 1,
                '省级': 2,
                '市级': 3,
                '县级': 4,
                '其他': 5
            };
            
            const levelA = levelOrder[a?.level] || 5;
            const levelB = levelOrder[b?.level] || 5;
            
            if (levelA !== levelB) {
                return levelA - levelB;
            }
            
            // 如果级别相同，按名称排序
            return (a?.name || '').localeCompare((b?.name || ''), 'zh-CN');
        });
        
        // 添加项目到列表
        sortedItems.forEach(item => {
            if (!item) return;
            
            const projectItem = document.createElement('div');
            projectItem.className = 'project-item';
            projectItem.dataset.id = item.id || 0;
            
            // 获取星级显示
            let stars = '';
            let levelClass = '';
            
            switch (item.level) {
                case '国家级': 
                    stars = '★★★★★'; 
                    levelClass = 'level-national';
                    break;
                case '省级': 
                    stars = '★★★★'; 
                    levelClass = 'level-provincial';
                    break;
                case '市级': 
                    stars = '★★★'; 
                    levelClass = 'level-city';
                    break;
                case '县级': 
                    stars = '★★'; 
                    levelClass = 'level-county';
                    break;
                default: 
                    stars = '★'; 
                    levelClass = 'level-other';
                    break;
            }
            
            // 设置项目内容
            projectItem.innerHTML = `
                <span class="project-name">${item.name || '未命名项目'}</span>
                <span class="project-stars ${levelClass}">${stars}</span>
            `;
            
            // 添加点击事件，定位到地图标记
            projectItem.addEventListener('click', function() {
                // 移除其他项目的活动状态
                document.querySelectorAll('.project-item').forEach(item => {
                    item.classList.remove('active');
                });
                
                // 添加当前项目的活动状态
                this.classList.add('active');
                
                // 安全地获取项目ID
                const itemId = parseInt(this.dataset.id) || 0;
                
                // 优先使用项目本身的坐标数据
                if (item?.lat && item?.lng && window.map) {
                    try {
                        // 使用BMap定位到指定位置
                        if (typeof window.BMap !== 'undefined') {
                            const point = new window.BMap.Point(item.lng, item.lat);
                            if (window.map && typeof window.map.panTo === 'function') {
                                window.map.panTo(point);
                                window.map.setZoom(15);
                                
                                // 如果有标记管理功能，高亮对应标记
                                if (window.MapCore && typeof window.MapCore.highlightMarker === 'function') {
                                    window.MapCore.highlightMarker(item.id);
                                }
                                
                                console.log(`地图已定位到: ${item.name} (${item.lng}, ${item.lat})`);
                            } else {
                                console.warn('地图实例不可用，无法定位');
                            }
                        } else {
                            console.error('BMap未定义，无法创建地图点');
                        }
                        
                        // 显示预览信息
                        if (typeof window.showHeritagePreview === 'function') {
                            window.showHeritagePreview(item);
                        }
                        return;
                    } catch (e) {
                        console.error('地图定位失败:', e);
                    }
                }
                
                // 备选方案：在marker数组中查找
                if (window.markers && Array.isArray(window.markers)) {
                    // 在marker数据结构中查找
                    const markerInfo = window.markers.find(m => m?.item && m.item.id === itemId);
                    if (markerInfo?.marker) {
                        try {
                            // 定位到标记
                            window.map.panTo(markerInfo.marker.getPosition());
                            
                            // 触发标记点击事件，显示预览
                            setTimeout(() => {
                                // 显示预览信息
                                if (typeof window.showHeritagePreview === 'function') {
                                    window.showHeritagePreview(item);
                                }
                            }, 300);
                        } catch (e) {
                            console.error('标记定位失败:', e);
                            // 直接显示预览信息作为备选方案
                            if (typeof window.showHeritagePreview === 'function') {
                                window.showHeritagePreview(item);
                            }
                        }
                    } else {
                        console.warn('未找到项目对应的标记点');
                        // 仍然显示预览信息
                        if (typeof window.showHeritagePreview === 'function') {
                            window.showHeritagePreview(item);
                        }
                    }
                } else {
                    console.warn('标记数组不可用，无法定位');
                    // 仍然显示预览信息
                    if (typeof window.showHeritagePreview === 'function') {
                        window.showHeritagePreview(item);
                    }
                }
            });
            
            // 添加到列表
            listContainer.appendChild(projectItem);
        });
        
        // 添加项目数量统计
        const countElement = document.querySelector('.project-count');
        if (countElement) {
            countElement.textContent = `共找到 ${sortedItems.length} 个项目`;
        }
        
    } catch (error) {
        console.error('更新项目清单失败:', error);
        listContainer.innerHTML = '<div class="project-empty">加载项目列表失败</div>';
    }
}

/**
 * 初始化收藏系统
 */
function initCollectionSystem() {
    // 加载本地存储的收藏数据
    loadCollectionsFromStorage();
    
    // 监听预览卡片中的收藏按钮点击事件
    document.addEventListener('click', function(e) {
        const collectBtn = e.target.closest('.collect-btn');
        if (collectBtn) {
            // 检查用户是否已登录
            const userString = localStorage.getItem('user');
            const user = userString ? JSON.parse(userString) : null;
            
            if (!user || !user.username) {
                // 用户未登录，显示登录提示
                showLoginPrompt();
                return;
            }
            
            // 用户已登录，可以继续收藏操作
            const itemId = parseInt(collectBtn.dataset.id);
            if (!isNaN(itemId)) {
                // 调用toggleCollection函数处理收藏操作
                toggleCollection(itemId, e);
            }
        }
    });
    
    // 初始化时更新所有收藏按钮状态
    updateCollectionButtonsState();
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

/**
 * 更新所有收藏按钮的状态
 * 确保UI与实际收藏状态保持一致
 */
function updateCollectionButtonsState() {
    // 获取所有收藏按钮
    const collectButtons = document.querySelectorAll('.collect-btn');
    
    // 确保collections是数组
    const collectionsArray = Array.isArray(collections) ? collections : [];
    
    // 遍历所有按钮，更新其状态
    collectButtons.forEach(button => {
        const itemId = button.dataset.id; // 不强制转换为数字，保留原始类型
        if (itemId) {
            // 检查是否已收藏
            const isCollected = collectionsArray.some(c => {
                if (typeof c === 'number' && !isNaN(parseInt(itemId))) {
                    return c === parseInt(itemId);
                } else if (typeof c === 'object' && c && c.id) {
                    // 处理ID可能是字符串或数字的情况
                    return String(c.id) === String(itemId);
                } else {
                    // 处理收藏项可能只是ID的情况
                    return String(c) === String(itemId);
                }
            });
            
            // 更新按钮状态
            if (isCollected) {
                button.classList.add('collected');
                button.textContent = '❤';
            } else {
                button.classList.remove('collected');
                button.textContent = '♡';
            }
        }
    });
}

/**
 * 获取当前用户的收藏存储键名
 * @returns {string} 用户专属的存储键名
 */
function getUserCollectionKey() {
    const userString = localStorage.getItem('user');
    console.log('localStorage中的user:', userString);
    
    if (userString) {
        try {
            const user = JSON.parse(userString);
            console.log('解析后的用户信息:', user);
            
            // 兼容多种用户ID字段名
            const userId = user.userId || user.id || user.username;
            console.log('用户ID:', userId);
            
            if (userId) {
                const key = `heritage_collections_${userId}`;
                console.log('生成的存储键:', key);
                return key;
            }
        } catch (e) {
            console.error('解析用户信息失败:', e);
        }
    }
    
    // 如果没有用户信息，使用默认键名（用于未登录用户的临时存储）
    const guestKey = 'heritage_collections_guest';
    console.log('使用默认存储键:', guestKey);
    return guestKey;
}

/**
 * 从本地存储加载收藏数据
 */
function loadCollectionsFromStorage() {
    try {
        const collectionKey = getUserCollectionKey();
        const storedCollections = localStorage.getItem(collectionKey);
        collections = storedCollections ? JSON.parse(storedCollections) : [];
        console.log('已加载收藏数据:', collections.length, '项', '存储键:', collectionKey);
    } catch (error) {
        console.error('加载收藏数据失败:', error);
        collections = [];
    }
}

/**
 * 保存收藏数据到本地存储
 */
function saveCollectionsToStorage() {
    try {
        const collectionKey = getUserCollectionKey();
        // 确保collections是数组
        const collectionsArray = Array.isArray(collections) ? collections : [];
        localStorage.setItem(collectionKey, JSON.stringify(collectionsArray));
        console.log('已保存收藏数据:', collectionsArray.length, '项', '存储键:', collectionKey);
    } catch (error) {
        console.error('保存收藏数据失败:', error);
        showToast('保存收藏失败，请稍后再试');
    }
}

/**
 * 更新收藏计数
 */
function updateCollectionCount() {
    // 更新收藏数量显示
    const collectionCountElem = document.getElementById('collection-count');
    if (collectionCountElem) {
        collectionCountElem.textContent = `(${collections.length})`;
    }
    
    // 更新我的收藏区域
    const myCollectionList = document.getElementById('my-collection-list');
    if (myCollectionList) {
        // 清空现有内容
        myCollectionList.innerHTML = '';
        
        if (collections.length === 0) {
            myCollectionList.innerHTML = '<div class="collection-empty">暂无收藏项目</div>';
            return;
        }
        
        // 添加收藏项目
        collections.forEach(item => {
            const itemId = typeof item === 'number' ? item : item.id;
            let itemName = '';
            
            if (typeof item === 'object' && item && item.name) {
                // 如果收藏项是对象且有name属性，直接使用
                itemName = item.name;
            } else {
                // 否则在heritageData中查找
                const heritageItem = window.heritageData?.find(h => {
                    return String(h?.id) === String(itemId);
                });
                itemName = heritageItem?.name || `项目 ${itemId}`;
            }
            
            const collectionItem = document.createElement('div');
            collectionItem.className = 'collection-item';
            collectionItem.dataset.id = itemId;
            collectionItem.innerHTML = `
                <span class="collection-name">${itemName}</span>
                <button class="remove-collection" title="移除收藏">×</button>
            `;
            
            // 添加点击事件
            collectionItem.addEventListener('click', function(e) {
                if (!e.target.classList.contains('remove-collection')) {
                    // 查找并显示项目
                    const fullItem = window.heritageData?.find(h => String(h?.id) === String(itemId));
                    if (fullItem) {
                        // 显示项目预览
                        if (typeof window.showHeritagePreview === 'function') {
                            window.showHeritagePreview(fullItem);
                        }
                    } else if (typeof item === 'object' && item.lat && item.lng) {
                        // 如果在heritageData中找不到但收藏项有完整信息，直接使用收藏项
                        if (typeof window.showHeritagePreview === 'function') {
                            window.showHeritagePreview(item);
                        }
                    }
                }
            });
            
            // 添加移除按钮事件
            const removeBtn = collectionItem.querySelector('.remove-collection');
            if (removeBtn) {
                removeBtn.addEventListener('click', function(e) {
                    e.stopPropagation();
                    toggleCollection(itemId);
                    collectionItem.remove();
                });
            }
            
            myCollectionList.appendChild(collectionItem);
        });
    }
}

/**
 * 切换收藏状态
 * @param {string|number} itemId 项目ID
 * @param {Event} event 事件对象
 */
function toggleCollection(itemId, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    if (!itemId) {
        console.warn('无效的项目ID');
        return false;
    }
    
    // 检查用户是否已登录
    const userString = localStorage.getItem('user');
    const user = userString ? JSON.parse(userString) : null;
    
    if (!user || !user.username) {
        showLoginPrompt();
        return false;
    }
    
    // 获取项目详情
    const item = window.heritageData.find(h => h.id === parseInt(itemId));
    if (!item) {
        console.error('无法找到项目详情:', itemId);
        return false;
    }

    // 检查当前收藏状态
    window.heritageAPI.checkFavoriteStatus(itemId)
        .then(isFavorited => {
            console.log('当前收藏状态:', isFavorited, '项目ID:', itemId);
            
            if (isFavorited) {
                // 已收藏，尝试移除收藏
                return window.heritageAPI.removeFavorite(itemId)
                    .then(() => {
                        showToast('已取消收藏');
                        return false;
                    });
            } else {
                // 未收藏，尝试添加收藏
                return window.heritageAPI.addFavorite(itemId)
                    .then(() => {
                        showToast('已添加到收藏');
                        return true;
                    });
            }
        })
        .then(result => {
            console.log('收藏操作结果:', result);
            // 无论成功失败，都重新加载收藏列表并更新UI
            return window.heritageAPI.getUserFavorites();
        })
        .then(favorites => {
            console.log('获取到的收藏列表:', favorites);
            // 更新本地收藏列表，确保favorites是数组
            collections = Array.isArray(favorites) ? favorites : [];
            console.log('更新后的本地收藏列表:', collections);
            saveCollectionsToStorage();
            
            // 直接更新UI中的收藏按钮状态，不依赖事件系统
            const collectButtons = document.querySelectorAll('.collect-btn');
            collectButtons.forEach(button => {
                if (button.dataset.id == itemId) {
                    // 直接检查最新的收藏状态
                    window.heritageAPI.checkFavoriteStatus(itemId)
                        .then(isCollected => {
                            console.log('直接更新收藏按钮状态:', isCollected, '项目ID:', itemId);
                            if (isCollected) {
                                button.classList.add('collected');
                                button.textContent = '❤';
                            } else {
                                button.classList.remove('collected');
                                button.textContent = '♡';
                            }
                        });
                }
            });
            
            // 更新UI
            updateCollectionCount();
            updateCollectionButtonsState();
        })
        .catch(error => {
            console.error('切换收藏状态失败:', error);
            showToast('操作失败，请稍后重试');
        });
    
    return true;
}

// 标签系统和旅游规划功能相关代码已移除，精简代码

/**
 * 使用全局api-utils中的showErrorMessage函数
 * @param {string} message 错误消息
 */
function showErrorMessage(message) {
    if (window.apiUtils && window.apiUtils.showErrorMessage) {
        window.apiUtils.showErrorMessage(message, 'heritage-preview');
    } else {
        // 回退到原有实现
        const previewElement = document.getElementById('heritage-preview');
        const contentElement = previewElement.querySelector('.preview-content');
        
        // 更新预览内容为错误消息
        contentElement.innerHTML = `
            <div class="preview-placeholder">
                <i class="fas fa-exclamation-circle"></i>
                ${message}
            </div>
        `;
    }
}

/**
 * 显示项目预览
 * @param {Object} item 项目数据
 */
window.showHeritagePreview = function(item) {
    if (!item) return;
    
    const previewContainer = document.getElementById('heritage-preview');
    if (!previewContainer) return;
    
    const previewContent = previewContainer.querySelector('.preview-content');
    if (!previewContent) return;
    
    // 获取项目级别对应的星级显示
    let stars = '';
    let levelClass = '';
    
    switch (item.level) {
        case '国家级': 
            stars = '★★★★★'; 
            levelClass = 'level-national';
            break;
        case '省级': 
            stars = '★★★★'; 
            levelClass = 'level-provincial';
            break;
        case '市级': 
            stars = '★★★'; 
            levelClass = 'level-city';
            break;
        case '县级': 
            stars = '★★'; 
            levelClass = 'level-county';
            break;
        default: 
            stars = '★'; 
            levelClass = 'level-other';
            break;
    }
    
    // 构建预览HTML - 紧凑布局，移除图片显示
    const previewHTML = `
        <div class="preview-card">
            <div class="preview-info">
                <div class="preview-title">
                    ${item.name || '未命名项目'}
                    <span class="preview-stars ${levelClass}">${stars}</span>
                </div>
                
                <div class="preview-meta">
                    <div class="preview-meta-item">
                        <span class="preview-meta-label">类别：</span>
                        <span class="preview-meta-value">
                            <span class="preview-category ${levelClass}">${item.category || '未分类'}</span>
                        </span>
                    </div>
                    
                    <div class="preview-meta-item">
                        <span class="preview-meta-label">地区：</span>
                        <span class="preview-meta-value">${item.region || '未知地区'}</span>
                    </div>
                    
                    <div class="preview-meta-item">
                        <span class="preview-meta-label">描述：</span>
                        <span class="preview-meta-value">${item.description ? item.description.substring(0, 80) + '...' : '暂无描述'}</span>
                    </div>
                </div>
                
                <div class="preview-actions">
                    <a href="heritage-detail.html?id=${item.id}" class="detail-btn" target="_blank">查看详情</a>
                    <button class="collect-btn" data-id="${item.id}" title="收藏此项目">♡</button>
                </div>
            </div>
        </div>
    `;
    
    // 更新预览内容
    previewContent.innerHTML = previewHTML;
    
    // 更新收藏按钮状态
    const collectBtn = previewContent.querySelector('.collect-btn');
    if (collectBtn) {
        // 使用API检查实际收藏状态
        window.heritageAPI.checkFavoriteStatus(item.id)
            .then(isCollected => {
                if (isCollected) {
                    collectBtn.classList.add('collected');
                    collectBtn.textContent = '❤';
                } else {
                    collectBtn.classList.remove('collected');
                    collectBtn.textContent = '♡';
                }
            })
            .catch(error => {
                console.error('检查收藏状态失败:', error);
            });
        
        // 添加收藏按钮点击事件
        collectBtn.addEventListener('click', function(e) {
            window.toggleCollection(item.id, e);
        });
    }
}

/**
 * 获取级别对应的CSS类名
 * @param {string} level 级别
 * @returns {string} CSS类名
 */
function getLevelClass(level) {
    switch(level) {
        case '国家级': return 'national';
        case '省级': return 'provincial';
        case '市级': return 'city';
        case '县级': return 'county';
        default: return 'other';
    }
}

// 使用全局UI组件
const { showToast } = window;


// 导出旅游规划功能已移除，相关代码已在profile.js中清理

// 只导出必要的函数到全局
window.initSidebar = initSidebar;
window.updateFilteredProjectList = updateFilteredProjectList;
window.showHeritagePreview = showHeritagePreview;
window.toggleCollection = toggleCollection;
window.addFilters = addFilters;
window.updateCollectionButtonsState = updateCollectionButtonsState;

// 监听收藏状态变化事件
if (window.heritageEvents) {
    window.heritageEvents.on('favoriteChanged', function(data) {
        console.log('地图侧边栏收到收藏状态变化事件:', data);
        // 更新所有收藏按钮状态
        updateCollectionButtonsState();
        // 更新收藏计数
        updateCollectionCount();
    });
}