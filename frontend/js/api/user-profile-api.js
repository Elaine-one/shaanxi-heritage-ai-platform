// 用户资料API模块
const USER_PROFILE_API_BASE_URL = '/api/profile/';

/**
 * 获取当前登录用户的详细信息，包括头像
 * @returns {Promise<Object>} 用户信息对象
 */
async function getUserProfile() {
    try {
        const response = await fetch(`${USER_PROFILE_API_BASE_URL}me/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `获取用户资料失败: ${response.status}` }));
            throw new Error(errorData.detail || errorData.error || `获取用户资料失败: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('获取用户资料错误:', error);
        throw error;
    }
}

/**
 * 更新用户资料
 * @param {Object} profileData - 要更新的资料数据
 * @returns {Promise<Object>} 更新后的用户信息
 */
async function updateUserProfile(profileData) {
    try {
        const response = await fetch(`${USER_PROFILE_API_BASE_URL}update_profile/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify(profileData),
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `更新用户资料失败: ${response.status}` }));
            throw new Error(errorData.detail || errorData.error || `更新用户资料失败: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('更新用户资料错误:', error);
        throw error;
    }
}

/**
 * 上传用户头像
 * @param {File} avatarFile - 头像文件
 * @returns {Promise<Object>} 包含头像URL的对象
 */
async function uploadUserAvatar(avatarFile) {
    try {
        const formData = new FormData();
        formData.append('avatar', avatarFile);
        
        const response = await fetch(`${USER_PROFILE_API_BASE_URL}upload-avatar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            body: formData,
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `上传头像失败: ${response.status}` }));
            throw new Error(errorData.detail || errorData.error || `上传头像失败: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('上传头像错误:', error);
        throw error;
    }
}

/**
 * 清除用户头像（设置为默认头像）
 * @returns {Promise<Object>} 更新后的用户资料
 */
async function clearUserAvatar() {
    try {
        const response = await fetch(`${USER_PROFILE_API_BASE_URL}clear-avatar/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: `清除头像失败: ${response.status}` }));
            throw new Error(errorData.detail || errorData.error || `清除头像失败: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('清除头像错误:', error);
        throw error;
    }
}

/**
 * 获取CSRF令牌
 * @returns {string} CSRF令牌
 */
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

// 导出API函数
window.API = window.API || {};
window.API.userProfile = {
    getUserProfile,
    updateUserProfile,
    uploadUserAvatar,
    clearUserAvatar
};