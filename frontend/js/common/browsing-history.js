/**
 * 浏览历史记录管理模块
 * 用于记录用户浏览的非遗项目，并提供历史记录管理功能
 * 历史记录将存储在数据库中，与用户账户关联
 */

// 最大历史记录数量
const MAX_HISTORY_ITEMS = 50;
// API基础URL
const HISTORY_API_BASE_URL = '/api/history/';



/**
 * 添加浏览历史记录
 * @param {Object} item 非遗项目数据
 */
async function addToHistory(item) {
    if (!item || !item.id) {
        console.warn('添加历史记录失败：项目数据无效');
        return;
    }

    try {
        // Ensure CSRF cookie is set before making a POST request
        try {
            await fetch('/api/auth/csrf/');
            console.log('CSRF token endpoint called.');
        } catch (csrfError) {
            console.warn('Failed to fetch CSRF token, proceeding with existing cookie if any:', csrfError);
            // Proceed even if this fails, as the cookie might already be set
        }

        const user = window.getCurrentUser();
        
        // 创建历史记录对象
        const historyItem = {
            heritage_id: item.id,
            visit_time: new Date().toISOString()
        };
        
        if (user && user.username) {
            // 用户已登录，通过API保存到数据库
            try {
                // Corrected URL construction for adding history
                console.log('[History] Attempting to add history via API for item:', item.name, 'ID:', item.id);
                const csrfToken = window.getCsrfToken();
                console.log('[History] CSRF token for addHistory API:', csrfToken);

                const response = await fetch(`${HISTORY_API_BASE_URL}add/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': window.getCsrfToken()
                    },
                    body: JSON.stringify(historyItem),
                    credentials: 'include' // Ensure cookies (like CSRF token) are sent
                });
                
                if (!response.ok) {
                    throw new Error(`API错误: ${response.status}`);
                }
                
                const responseData = await response.json(); // Assuming API returns JSON
                console.log('已添加浏览历史记录到数据库:', item.name, 'API Response:', responseData);
            } catch (apiError) {
                console.error('API保存浏览历史失败:', apiError);
                // 如果API保存失败，回退到本地存储
                saveToLocalStorage(item);
            }
        } else {
            // 用户未登录，保存到本地存储
            saveToLocalStorage(item);
        }
    } catch (error) {
        console.error('保存浏览历史失败:', error);
    }
}

/**
 * 保存历史记录到本地存储（未登录用户或API失败时的备用方案）
 * @param {Object} item 非遗项目数据
 */
function saveToLocalStorage(item) {
    try {
        // 获取现有历史记录
        let history = getLocalHistory();
        
        // 检查是否已存在该项目
        const existingIndex = history.findIndex(h => h.id === item.id);
        if (existingIndex !== -1) {
            // 如果已存在，移除旧记录
            history.splice(existingIndex, 1);
        }
        
        // 添加新记录到开头
        history.unshift({
            id: item.id,
            name: item.name,
            category: item.category,
            region: item.region,
            imageUrl: item.main_image_url || item.imageUrl,
            visitTime: new Date().toISOString()
        });
        
        // 限制历史记录数量
        if (history.length > MAX_HISTORY_ITEMS) {
            history = history.slice(0, MAX_HISTORY_ITEMS);
        }
        
        // 保存历史记录
        localStorage.setItem('browsing_history', JSON.stringify(history));
        
        console.log('已添加浏览历史记录到本地存储:', item.name);
    } catch (error) {
        console.error('保存本地浏览历史失败:', error);
    }
}

/**
 * 获取浏览历史记录
 * @returns {Promise<Array>} 历史记录数组的Promise
 */
async function getHistory() {
    const user = window.getCurrentUser();
    
    if (user && user.username) {
        // 用户已登录，从API获取
        console.log('[History] Attempting to get history via API for user:', user.username);
        try {
            const response = await fetch(`${HISTORY_API_BASE_URL}list_history/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error(`API错误: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('[History] Received history from API:', data);
            return data;
        } catch (apiError) {
            console.error('API获取浏览历史失败:', apiError);
            // 如果API获取失败，回退到本地存储
            return getLocalHistory();
        }
    } else {
        // 用户未登录，从本地存储获取
        const localData = getLocalHistory();
        console.log('[History] Received history from localStorage:', localData);
        return localData;
    }
}

/**
 * 从本地存储获取浏览历史记录
 * @returns {Array} 历史记录数组
 */
function getLocalHistory() {
    try {
        const history = localStorage.getItem('browsing_history');
        return history ? JSON.parse(history) : [];
    } catch (error) {
        console.error('获取本地浏览历史失败:', error);
        return [];
    }
}

/**
 * 清空浏览历史记录
 * @returns {Promise<boolean>} 操作是否成功的Promise
 */
async function clearHistory() {
    const user = getCurrentUser();
    
    if (user && user.username) {
        // 用户已登录，通过API清空
        try {
            const response = await fetch(`${HISTORY_API_BASE_URL}clear/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': window.getCsrfToken()
                },
                credentials: 'include' // Ensure cookies (like CSRF token) are sent
            });
            
            if (!response.ok) {
                throw new Error(`API错误: ${response.status}`);
            }
            
            console.log('已通过API清空浏览历史记录');
            return true;
        } catch (apiError) {
            console.error('API清空浏览历史失败:', apiError);
            // 如果API清空失败，尝试清空本地存储
            return clearLocalHistory();
        }
    } else {
        // 用户未登录，清空本地存储
        return clearLocalHistory();
    }
}

/**
 * 清空本地存储中的浏览历史记录
 * @returns {boolean} 操作是否成功
 */
function clearLocalHistory() {
    try {
        localStorage.removeItem('browsing_history');
        console.log('已清空本地浏览历史记录');
        return true;
    } catch (error) {
        console.error('清空本地浏览历史失败:', error);
        return false;
    }
}

/**
 * 删除指定的历史记录
 * @param {number|string} itemId 要删除的项目ID
 */
function removeFromHistory(itemId) {
    if (!itemId) return false;
    
    try {
        // 获取现有历史记录
        let history = getHistory();
        
        // 过滤掉要删除的项目
        const newHistory = history.filter(item => String(item.id) !== String(itemId));
        
        // 如果长度没变，说明没有找到要删除的项目
        if (newHistory.length === history.length) {
            return false;
        }
        
        // 保存新的历史记录
        localStorage.setItem('browsing_history', JSON.stringify(newHistory));
        console.log('已从历史记录中删除项目:', itemId);
        return true;
    } catch (error) {
        console.error('删除历史记录失败:', error);
        return false;
    }
}

// 导出函数到全局作用域
window.addToHistory = addToHistory;
window.getHistory = getHistory;
window.clearHistory = clearHistory;
window.removeFromHistory = removeFromHistory;