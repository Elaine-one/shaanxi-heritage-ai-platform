/**
 * 非遗数据API接口
 * 负责处理所有数据API调用和相关功能
 */

// API基础URL - 使用相对URL避免跨域问题
const HERITAGE_SPECIFIC_API_BASE_URL = '/api/';
const CONFIG_API_BASE_URL = '/api/config/';

/**
 * 获取地图配置信息，包括百度地图AK
 * @param {Function} callback 回调函数
 * @returns {Promise} 包含地图配置的Promise
 */
function getMapConfig() {
    return new Promise((resolve, reject) => {
        fetch(`${HERITAGE_SPECIFIC_API_BASE_URL}map/config/`)
            .then(response => response.json())
            .then(data => {
                if (data && data.bmap_ak) {
                    resolve(data);
                } else {
                    console.warn('获取的地图配置数据不完整');
                    reject(new Error('地图配置数据不完整'));
                }
            })
            .catch(error => {
                console.error('获取地图配置失败:', error);
                reject(error);
            });
    });
}

// 将getMapConfig函数导出到全局作用域
window.getMapConfig = getMapConfig;

// API V2 Base URL (favorites) - 使用相对URL避免跨域问题
const FAVORITES_API_BASE_URL = '/api/favorites/';

/**
 * 检查用户是否已登录
 * @returns {Promise<boolean>} 用户是否已登录的Promise
 */
async function isUserLoggedIn() {
    try {
        // 直接调用后端API检查登录状态，不再使用localStorage
        const response = await fetch('/api/auth/user/', {
            method: 'GET',
            credentials: 'include' // 使用session认证
        });
        
        if (response.ok) {
            const userData = await response.json();
            console.log('后端用户检查结果:', true, '用户数据:', userData);
            return true; // 后端确认用户已登录
        } else {
            console.log('后端用户检查结果:', false);
            return false;
        }
    } catch (error) {
        console.error('检查登录状态失败:', error);
        return false; // 如果API调用失败，默认为未登录
    }
}

/**
 * 获取当前用户ID
 * @returns {Promise<number|null>} 用户ID或null的Promise
 */
async function getCurrentUserId() {
    try {
        // 直接调用后端API获取用户信息，不再使用localStorage
        const response = await fetch('/api/auth/user/', {
            method: 'GET',
            credentials: 'include' // 使用session认证
        });
        
        if (response.ok) {
            const user = await response.json();
            return user && (user.userId || user.id) ? (user.userId || user.id) : null; // 兼容两种字段名
        }
        return null;
    } catch (error) {
        console.error('获取用户ID失败:', error);
        return null;
    }
}

// 使用全局utils中的getCookie函数

/**
 * 获取CSRF令牌，如果不存在则尝试从服务器获取
 * @returns {Promise<string|null>} CSRF令牌，如果获取失败则返回null
 */
async function getCSRFToken() {
    // 首先尝试从cookie中获取
    let csrfToken = window.getCookie('csrftoken');
    
    // 如果没有CSRF令牌，则调用CSRF端点获取
    if (!csrfToken) {
        try {
            const csrfResponse = await fetch('/api/auth/csrf/', {
                method: 'GET',
                credentials: 'include' // 确保包含cookies
            });
            
            if (csrfResponse.ok) {
                // 获取CSRF令牌成功后，再次从cookie中读取
                csrfToken = window.getCookie('csrftoken');
                console.log('成功获取CSRF令牌:', csrfToken);
            } else {
                console.error('获取CSRF令牌失败:', csrfResponse.status);
            }
        } catch (csrfError) {
            console.error('获取CSRF令牌出错:', csrfError);
        }
    }
    
    return csrfToken;
}

/**
 * 添加非遗项目到用户收藏
 * @param {number} heritageId 非遗项目ID
 * @returns {Promise<Object>} 添加结果
 */
async function addFavorite(heritageId) {
    const loggedIn = await isUserLoggedIn();
    if (!loggedIn) {
        return Promise.reject(new Error('用户未登录，无法添加收藏。'));
    }
    
    try {
        // 获取CSRF令牌
        const csrfToken = await getCSRFToken();
        
        if (!csrfToken) {
            console.warn('无法获取CSRF令牌，收藏操作可能会失败');
        }
        
        console.log('用于addFavorite的CSRF令牌:', csrfToken);

        // 构建请求头
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // 只有在有CSRF令牌的情况下才添加到请求头
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        // 检查是否已经收藏
        const isFavorited = await checkFavoriteStatus(heritageId);
        if (isFavorited) {
            // 已经收藏，直接返回成功
            return { message: 'Already favorited' };
        }
        
        const response = await fetch(`${FAVORITES_API_BASE_URL}add/`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ heritage_id: heritageId }),
            credentials: 'include' // 使用session认证
        });
        
        if (!response.ok) {
            // 尝试解析错误信息
            let errorMessage;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.error || `添加收藏失败: ${response.status}`;
            } catch (e) {
                errorMessage = `添加收藏失败: ${response.status}`;
            }
            
            console.error('添加收藏请求失败:', errorMessage);
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        
        // 成功后触发事件
        if (window.heritageEvents) {
            window.heritageEvents.emit('favoriteChanged', { id: heritageId, action: 'add' });
        }
        
        return result;
    } catch (error) {
        console.error('addFavorite API调用失败:', error);
        throw error;
    }
}

/**
 * 从用户收藏中移除非遗项目
 * @param {number} heritageId 非遗项目ID
 * @returns {Promise<void>} 操作成功则resolve
 */
async function removeFavorite(heritageId) {
    const loggedIn = await isUserLoggedIn();
    if (!loggedIn) {
        return Promise.reject(new Error('用户未登录，无法移除收藏。'));
    }
    
    try {
        // 获取CSRF令牌
        const csrfToken = await getCSRFToken();
        
        if (!csrfToken) {
            console.warn('无法获取CSRF令牌，取消收藏操作可能会失败');
        }
        
        console.log('用于removeFavorite的CSRF令牌:', csrfToken);

        // 构建请求头
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // 只有在有CSRF令牌的情况下才添加到请求头
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        // 首先获取用户的所有收藏，找到对应的收藏ID
        const favoritesResponse = await fetch(`${FAVORITES_API_BASE_URL}`, {
            method: 'GET',
            headers: headers,
            credentials: 'include' // 使用session认证
        });
        
        if (!favoritesResponse.ok) {
            throw new Error(`获取收藏列表失败: ${favoritesResponse.status}`);
        }
        
        const favorites = await favoritesResponse.json();
        
        // 确保favorites是数组
        const favoritesArray = Array.isArray(favorites) ? favorites : [];
        
        console.log('所有收藏:', favoritesArray);
        console.log('要删除的项目ID:', heritageId);
        
        // 找到对应的收藏 - 处理不同的数据结构
        let favoriteToRemove = null;
        
        // 遍历所有收藏，查找匹配的记录
        for (let i = 0; i < favoritesArray.length; i++) {
            const fav = favoritesArray[i];
            console.log('当前收藏项:', fav);
            
            if (fav) {
                // 处理不同的数据结构
                if (fav.heritage && fav.heritage.id) {
                    // 结构1: { heritage: { id: 12 }, ... }
                    console.log('结构1 - heritage.id:', fav.heritage.id, '是否匹配:', fav.heritage.id === heritageId);
                    if (fav.heritage.id === heritageId) {
                        favoriteToRemove = fav;
                        break;
                    }
                } else if (fav.heritage_id) {
                    // 结构2: { heritage_id: 12, ... }
                    console.log('结构2 - heritage_id:', fav.heritage_id, '是否匹配:', fav.heritage_id === heritageId);
                    if (fav.heritage_id === heritageId) {
                        favoriteToRemove = fav;
                        break;
                    }
                } else if (fav.id) {
                    // 结构3: { id: 12, ... } - 直接比较id
                    console.log('结构3 - id:', fav.id, '是否匹配:', fav.id === heritageId);
                    if (fav.id === heritageId) {
                        favoriteToRemove = fav;
                        break;
                    }
                }
            }
        }
        
        if (!favoriteToRemove || !favoriteToRemove.id) {
            console.error('未找到对应的收藏记录，检查数据结构');
            // 尝试使用另一种方法删除收藏 - 直接调用后端的remove_favorite接口
            console.log('尝试使用POST /remove/接口删除收藏');
            
            // 构建请求头
            const headers = {
                'Content-Type': 'application/json'
            };
            
            // 只有在有CSRF令牌的情况下才添加到请求头
            if (csrfToken) {
                headers['X-CSRFToken'] = csrfToken;
            }
            
            // 调用后端的remove_favorite接口
            const removeResponse = await fetch(`${FAVORITES_API_BASE_URL}remove/`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ heritage_id: heritageId }),
                credentials: 'include' // 使用session认证
            });
            
            if (!removeResponse.ok && removeResponse.status !== 204) {
                // 尝试解析错误信息
                let errorMessage;
                try {
                    const errorData = await removeResponse.json();
                    errorMessage = errorData.detail || errorData.error || `移除收藏失败: ${removeResponse.status}`;
                } catch (e) {
                    errorMessage = `移除收藏失败: ${removeResponse.status}`;
                }
                
                console.error('移除收藏请求失败:', errorMessage);
                throw new Error(errorMessage);
            }
            
            // 成功后触发事件
            if (window.heritageEvents) {
                window.heritageEvents.emit('favoriteChanged', { id: heritageId, action: 'remove' });
            }
            
            return;
        }
        
        // 使用DELETE方法删除收藏
        const deleteResponse = await fetch(`${FAVORITES_API_BASE_URL}${favoriteToRemove.id}/`, {
            method: 'DELETE',
            headers: headers,
            credentials: 'include' // 使用session认证
        });
        
        if (!deleteResponse.ok && deleteResponse.status !== 204) {
            // 尝试解析错误信息
            let errorMessage;
            try {
                const errorData = await deleteResponse.json();
                errorMessage = errorData.detail || errorData.error || `移除收藏失败: ${deleteResponse.status}`;
            } catch (e) {
                errorMessage = `移除收藏失败: ${deleteResponse.status}`;
            }
            
            console.error('移除收藏请求失败:', errorMessage);
            throw new Error(errorMessage);
        }
        
        // 成功后触发事件
        if (window.heritageEvents) {
            window.heritageEvents.emit('favoriteChanged', { id: heritageId, action: 'remove' });
        }
        
        return;
    } catch (error) {
        console.error('removeFavorite API调用失败:', error);
        throw error;
    }
}

/**
 * 检查指定非遗项目是否已被当前用户收藏
 * @param {number} heritageId 非遗项目ID
 * @returns {Promise<boolean>} 如果已收藏则为true，否则为false
 */
async function checkFavoriteStatus(heritageId) {
    const loggedIn = await isUserLoggedIn();
    if (!loggedIn) {
        return Promise.resolve(false); // 未登录用户默认未收藏
    }
    
    try {
        // 获取CSRF令牌 - 虽然GET请求不需要CSRF令牌，但为了一致性和可能的服务器端验证，我们仍然获取它
        await getCSRFToken();
        
        // 构建请求头
        const headers = {
            'Content-Type': 'application/json'
        };
        
        const response = await fetch(`${FAVORITES_API_BASE_URL}check/?heritage_id=${heritageId}`, {
            method: 'GET',
            headers: headers,
            credentials: 'include' // 使用session认证
        });
        
        if (!response.ok) {
            // 尝试解析错误信息
            let errorMessage;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.error || `检查收藏状态失败: ${response.status}`;
            } catch (e) {
                errorMessage = `检查收藏状态失败: ${response.status}`;
            }
            
            console.error('检查收藏状态请求失败:', errorMessage);
            return false; // 出错时返回未收藏状态，而不是抛出异常
        }
        
        const data = await response.json();
        return data.is_favorited;
    } catch (error) {
        console.error('checkFavoriteStatus API调用失败:', error);
        return false; // 出错时返回未收藏状态，而不是抛出异常
    }
}

/**
 * 获取当前用户的所有收藏列表
 * @returns {Promise<Array<Object>>} 用户的收藏列表
 */
async function getUserFavorites() {
    const loggedIn = await isUserLoggedIn();
    if (!loggedIn) {
        return Promise.resolve([]);
    }
    
    try {
        // 获取CSRF令牌 - 虽然GET请求不需要CSRF令牌，但为了一致性和可能的服务器端验证，我们仍然获取它
        await getCSRFToken();
        
        // 构建请求头
        const headers = {
            'Content-Type': 'application/json'
        };
        
        const response = await fetch(`${FAVORITES_API_BASE_URL}`, {
            method: 'GET',
            headers: headers,
            credentials: 'include' // 使用session认证
        });
        
        if (!response.ok) {
            // 尝试解析错误信息
            let errorMessage;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.error || `获取收藏列表失败: ${response.status}`;
            } catch (e) {
                errorMessage = `获取收藏列表失败: ${response.status}`;
            }
            
            console.error('获取收藏列表请求失败:', errorMessage);
            return []; // 出错时返回空数组，而不是抛出异常
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('getUserFavorites API调用失败:', error);
        return []; // 出错时返回空数组，而不是抛出异常
    }
}

// 将收藏相关函数导出到全局作用域
if (!window.heritageAPI) {
    window.heritageAPI = {};
}
window.heritageAPI.addFavorite = addFavorite;
window.heritageAPI.removeFavorite = removeFavorite;
window.heritageAPI.checkFavoriteStatus = checkFavoriteStatus;
window.heritageAPI.getUserFavorites = getUserFavorites;
window.heritageAPI.isUserLoggedIn = isUserLoggedIn;
window.heritageAPI.getCurrentUserId = getCurrentUserId;

// 事件系统实现
if (!window.heritageEvents) {
    window.heritageEvents = {
        listeners: {},
        on: function(event, callback) {
            if (!this.listeners[event]) {
                this.listeners[event] = [];
            }
            this.listeners[event].push(callback);
        },
        emit: function(event, data) {
            if (this.listeners[event]) {
                this.listeners[event].forEach(callback => callback(data));
            }
        }
    };
}

// 收藏状态变化事件处理
function updateFavoriteButtonsState() {
    console.log('收藏状态已更新，刷新UI');
    
    // 遍历所有收藏按钮
    const collectButtons = document.querySelectorAll('.collect-btn');
    
    collectButtons.forEach(button => {
        const itemId = parseInt(button.dataset.id);
        if (!isNaN(itemId)) {
            // 检查实际收藏状态
            checkFavoriteStatus(itemId)
                .then(isFavorited => {
                    if (isFavorited) {
                        button.classList.add('collected');
                        button.textContent = '❤';
                    } else {
                        button.classList.remove('collected');
                        button.textContent = '♡';
                    }
                })
                .catch(error => {
                    console.error('更新收藏按钮状态失败:', error);
                });
        }
    });
}

// 在各页面中监听事件
if (window.heritageEvents) {
    window.heritageEvents.on('favoriteChanged', function(data) {
        // 更新页面上的收藏按钮状态
        console.log('收到收藏状态变化事件:', data);
        updateFavoriteButtonsState();
        
        // 同时调用地图侧边栏的更新函数，确保所有收藏按钮都能及时更新
        if (window.updateCollectionButtonsState) {
            console.log('调用地图侧边栏的updateCollectionButtonsState函数');
            window.updateCollectionButtonsState();
        }
    });
}

/**
 * 获取地图统计数据
 * @param {Function} callback 回调函数
 */
function loadMapStatistics(callback) {
    fetch(`${HERITAGE_SPECIFIC_API_BASE_URL}map/statistics/`)
        .then(response => response.json())
        .then(data => {
            if (typeof callback === 'function') {
                callback(data);
            }
        })
        .catch(error => {
            console.error('获取地图统计数据失败:', error);
            if (typeof callback === 'function') {
                callback(null);
            }
        });
}

// 图片资源管理
const heritageImages = {
    // 默认图片路径
    defaultImage: '/static/common/default-heritage.jpg',
    
    /**
     * 获取非遗项目的主图片URL
     * @param {Object} heritage 非遗项目对象
     * @returns {string} 图片URL
     */
    getMainImageUrl: function(heritage) {
        if (heritage.main_image_url) {
            return heritage.main_image_url;
        }
        if (heritage.images && heritage.images.length > 0) {
            const mainImage = heritage.images.find(img => img.is_main);
            if (mainImage) {
                return mainImage.image;
            }
            return heritage.images[0].image;
        }
        return this.defaultImage;
    },
    
    /**
     * 获取非遗项目的所有图片URL列表
     * @param {Object} heritage 非遗项目对象
     * @returns {Array<string>} 图片URL列表
     */
    getAllImageUrls: function(heritage) {
        if (heritage.images && heritage.images.length > 0) {
            return heritage.images.map(img => img.image);
        }
        if (heritage.gallery_image_urls && heritage.gallery_image_urls.length > 0) {
            return heritage.gallery_image_urls;
        }
        return [this.defaultImage];
    }
};

/**
 * 加载非遗数据
 * @param {Object} filters 筛选条件
 */


function loadHeritageData(filters = {}) { // Removed callback, returns Promise
    return new Promise((resolve, reject) => {
        let url = `${HERITAGE_SPECIFIC_API_BASE_URL}items/`;
        const params = new URLSearchParams();
        
        // 添加筛选参数
        if (filters.category) params.append('category', filters.category);
        if (filters.level) params.append('level', filters.level);
        if (filters.region) params.append('region', filters.region);
        if (filters.search) params.append('search', filters.search);
        if (filters.page) params.append('page', filters.page);
        if (filters.page_size) params.append('page_size', filters.page_size); // Ensure page_size is passed
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        fetch(url)
            .then(async response => {
                if (!response.ok) {
                    let errorData = null;
                    try {
                        errorData = await response.json();
                    } catch (e) {
                        // Ignore if parsing fails
                    }
                    const error = new Error(`HTTP error! status: ${response.status}`);
                    error.status = response.status;
                    error.data = errorData;
                    reject(error); // Reject the promise with the custom error
                    return; // Stop further processing in .then chain
                }
                resolve(await response.json()); // Resolve with the JSON data
            })
            .catch(error => {
                // This catch handles network errors or errors from the .then block above (e.g. JSON parsing of non-OK response failed)
                console.error('获取非遗数据失败 (fetch catch):', error);
                reject(error); // Reject the promise
            });
    });
}

// 将主要函数挂载到全局作用域
// window.loadHeritageData = loadHeritageData; // No longer global if API object is used
window.loadMapStatistics = loadMapStatistics;
window.heritageImages = heritageImages;

// Ensure heritageAPI object exists and add getAllItems to it
if (typeof window.heritageAPI === 'undefined') {
    window.heritageAPI = {};
}
window.heritageAPI.getAllItems = loadHeritageData; // Assign the promise-based function

// 导出模块（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getMapConfig,
        loadHeritageData,
        loadMapStatistics,
        heritageImages,
        addFavorite,
        removeFavorite,
        checkFavoriteStatus,
        getUserFavorites,
        isUserLoggedIn,
        getCurrentUserId
    };
}