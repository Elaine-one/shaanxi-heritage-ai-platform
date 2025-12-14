// API基础URL - 使用相对路径，适配生产环境
const COMMON_API_BASE_URL = '/api'; // 后端API地址

// 获取CSRF token的函数 - 使用全局utils中的getCookie

// 通用API请求函数
async function apiRequest(endpoint, options = {}) {
    // 设置默认请求头
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    // 添加CSRF token到请求头（用于POST、PUT、DELETE等请求）
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes((options.method || 'GET').toUpperCase())) {
        const csrfToken = window.getCookie('csrftoken');
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
    }
    
    // 构建完整URL
    const url = `${COMMON_API_BASE_URL}${endpoint}`;
    
    // 发送请求
    try {
        console.log('发送API请求:', {
            url,
            method: options.method || 'GET',
            headers,
            body: options.body
        });
        
        const response = await fetch(url, {
            ...options,
            headers,
            credentials: 'include' // 包含cookies以支持session认证
        });
        
        console.log('API响应状态:', response.status, response.statusText);
        
        // 检查响应状态
        if (!response.ok) {
            // 尝试解析错误信息
            let errorData;
            try {
                errorData = await response.json();
                console.log('API错误响应数据:', errorData);
            } catch (e) {
                errorData = { detail: '请求失败' };
                console.log('无法解析错误响应，使用默认错误信息');
            }
            
            const error = {
                status: response.status,
                data: errorData
            };
            console.error('API请求失败，抛出错误:', error);
            throw error;
        }
        
        // 解析响应数据
        const data = await response.json();
        console.log('API请求成功，响应数据:', data);
        return data;
    } catch (error) {
        console.error('API请求异常:', error);
        throw error;
    }
}

// 非遗项目相关API
const heritageAPI = {
    // 获取所有非遗项目
    getAllItems: async (params = {}) => {
        let allItems = [];
        let currentPage = params.page || 1; // Start with the requested page or default to 1
        
        // Use the page_size from input params for the first request.
        // If backend limits this, actualReturnedPageSize will reflect it.
        const requestedPageSize = params.page_size || 100; // Default if not specified

        const initialRequestParams = { ...params, page: currentPage, page_size: requestedPageSize };
        
        const buildQueryString = (p) => {
            const query = new URLSearchParams();
            Object.entries(p).forEach(([key, value]) => {
                if (key === 'page' || key === 'page_size') {
                    if (value !== undefined && value !== null) query.append(key, value);
                } else if (value) { // For other filters like level, category, region
                    query.append(key, value);
                }
            });
            return query.toString();
        };

        let currentQueryString = buildQueryString(initialRequestParams);
        console.log(`[heritageAPI.getAllItems] Initial request: /items/?${currentQueryString}`);
        
        try {
            let response = await apiRequest(`/items/?${currentQueryString}`);
            
            if (response && response.results) {
                allItems = allItems.concat(response.results);
                const totalCount = response.count || 0;
                let actualReturnedPageSize = response.results.length;

                console.log(`[heritageAPI.getAllItems] Page ${currentPage} fetched. Items: ${actualReturnedPageSize}/${totalCount}. Total collected: ${allItems.length}`);

                while (allItems.length < totalCount && actualReturnedPageSize > 0) {
                    currentPage++;
                    const nextPageParams = { ...params, page: currentPage, page_size: actualReturnedPageSize };
                    currentQueryString = buildQueryString(nextPageParams);
                    
                    console.log(`[heritageAPI.getAllItems] Fetching next page ${currentPage}: /items/?${currentQueryString}`);
                response = await apiRequest(`/items/?${currentQueryString}`);

                    if (response && response.results && response.results.length > 0) {
                        allItems = allItems.concat(response.results);
                        actualReturnedPageSize = response.results.length;
                        console.log(`[heritageAPI.getAllItems] Page ${currentPage} fetched. Items: ${actualReturnedPageSize}/${totalCount}. Total collected: ${allItems.length}`);
                    } else {
                        console.warn(`[heritageAPI.getAllItems] Page ${currentPage} returned no more results or an error. Stopping pagination.`);
                        break;
                    }
                }
                
                console.log(`[heritageAPI.getAllItems] Finished fetching. Total items collected: ${allItems.length}`);
                return {
                    count: totalCount,
                    results: allItems,
                };

            } else {
                console.error('[heritageAPI.getAllItems] Initial API request failed or returned invalid data.');
                return { count: 0, results: [] };
            }
        } catch (error) {
            console.error('[heritageAPI.getAllItems] Error during fetching items:', error);
            return { count: 0, results: [], error: error.message || 'Unknown error' };
        }
    },
    
    // 获取单个非遗项目详情
    getItemDetail: (itemId) => {
        return apiRequest(`/items/${itemId}/`); // Correct path already includes /api via COMMON_API_BASE_URL
    },
    
    // 获取所有类别
    getCategories: () => {
        return apiRequest('/items/categories/');
    },
    
    // 获取所有级别
    getLevels: () => {
        return apiRequest('/items/levels/');
    },
    
    // 获取所有地区
    getRegions: () => {
        return apiRequest('/items/regions/');
    },
    
    // 切换收藏状态
    toggleCollection: (itemId) => {
        return apiRequest(`/items/${itemId}/toggle_collection/`, { // Correct path already includes /api via COMMON_API_BASE_URL
            method: 'POST'
        });
    },
    
    // 获取用户收藏
    getUserCollections: () => {
        return apiRequest('/heritage/collections/'); // Correct path already includes /api via COMMON_API_BASE_URL
    }
};

// 用户账户API
const accountAPI = {
    // 用户注册
    register: (userData) => {
        return apiRequest('/accounts/register/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    },
    
    // 用户登录
    login: (credentials) => {
        return apiRequest('/accounts/login/', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
    },
    
    // 用户退出
    logout: () => {
        return apiRequest('/accounts/logout/', {
            method: 'POST'
        });
    },
    
    // 获取用户资料
    getProfile: () => {
        return apiRequest('/accounts/profile/');
    },
    
    // 更新用户资料
    updateProfile: (profileData) => {
        return apiRequest('/accounts/profile/', {
            method: 'PATCH',
            body: JSON.stringify(profileData)
        });
    }
};

// 导出API模块
window.API = {
    heritage: heritageAPI,
    account: accountAPI
};