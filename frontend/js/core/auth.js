// 通用用户认证脚本

let authCheckPromise = null;
let lastAuthCheck = 0;
const AUTH_CACHE_DURATION = 30000;

async function checkBackendAuth(forceRefresh = false) {
    try {
        if (authCheckPromise) {
            return await authCheckPromise;
        }
        
        authCheckPromise = fetch('/api/auth/user/', {
            method: 'GET',
            credentials: 'include'
        }).then(async response => {
            if (response.ok) {
                const userData = await response.json();
                lastAuthCheck = Date.now();
                return userData;
            } else {
                lastAuthCheck = Date.now();
                return null;
            }
        }).finally(() => {
            authCheckPromise = null;
        });
        
        return await authCheckPromise;
    } catch (error) {
        console.error('[auth.js] Error checking auth:', error);
        authCheckPromise = null;
        return null;
    }
}

async function updateUserIcon() {
    const userIcon = document.querySelector('.user-icon');
    if (!userIcon) {
        return;
    }
    
    const user = await checkBackendAuth();
    
    if (user && user.username) {
        let hasAvatar = false;
        try {
            const response = await fetch('/api/profile/me/', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache'
                }
            });
            
            if (response.ok) {
                const userData = await response.json();
                if (userData.profile && userData.profile.avatar) {
                    userIcon.textContent = '';
                    
                    let avatarUrl = userData.profile.avatar;
                    if (typeof AvatarCache !== 'undefined') {
                        avatarUrl = AvatarCache.getCacheBustedUrl(avatarUrl, user.id);
                    } else {
                        if (avatarUrl.startsWith('/media/')) {
                            avatarUrl = window.location.origin + avatarUrl;
                        }
                        const separator = avatarUrl.includes('?') ? '&' : '?';
                        avatarUrl += `${separator}_v=${Date.now()}`;
                    }
                    
                    userIcon.style.backgroundImage = `url(${avatarUrl})`;
                    userIcon.style.backgroundSize = 'cover';
                    userIcon.style.backgroundPosition = 'center';
                    userIcon.style.backgroundColor = '';
                    userIcon.style.color = '';
                    hasAvatar = true;
                    
                    const userFromStorage = JSON.parse(localStorage.getItem('user')) || {};
                    userFromStorage.avatar = userData.profile.avatar;
                    userFromStorage.id = user.id;
                    localStorage.setItem('user', JSON.stringify(userFromStorage));
                }
            }
        } catch (error) {
            console.error('[auth.js] Error fetching user profile:', error);
        }
        
        if (!hasAvatar) {
            userIcon.textContent = user.username.charAt(0).toUpperCase();
            userIcon.style.backgroundImage = '';
            userIcon.style.backgroundSize = '';
            userIcon.style.backgroundPosition = '';
            userIcon.style.backgroundColor = '#8c2e2e';
            userIcon.style.color = 'white';
        }
        
        userIcon.title = `${user.username} (点击查看个人中心)`;
        userIcon.style.borderRadius = '50%';
        userIcon.style.width = '30px';
        userIcon.style.height = '30px';
        userIcon.style.display = 'flex';
        userIcon.style.justifyContent = 'center';
        userIcon.style.alignItems = 'center';
        
        userIcon.onclick = function() {
            const isInPagesDir = window.location.pathname.includes('/pages/');
            const profilePath = isInPagesDir ? 'profile.html' : 'pages/profile.html';
            window.location.href = profilePath;
        };
    } else {
        userIcon.textContent = '👤';
        userIcon.title = '登录/注册';
        userIcon.style.backgroundColor = ''; 
        userIcon.style.color = '';
        userIcon.style.borderRadius = '';
        userIcon.style.width = '';
        userIcon.style.height = '';
        userIcon.style.display = '';
        userIcon.style.justifyContent = '';
        userIcon.style.alignItems = '';
        userIcon.style.backgroundImage = '';
        userIcon.style.backgroundSize = '';
        userIcon.style.backgroundPosition = '';
        
        userIcon.onclick = function() {
            const isInPagesDir = window.location.pathname.includes('/pages/');
            const loginPath = isInPagesDir ? 'login.html' : 'pages/login.html';
            window.location.href = loginPath;
        };
    }
}

/**
 * 获取CSRF Token
 * @param {string} name - Cookie名称
 * @returns {string} - CSRF Token值
 */
function getCsrfToken(name = 'csrftoken') {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * 用户登出
 */
function logout() {
    fetch('/api/auth/logout/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        credentials: 'include'
    })
    .then(response => {
        // 无论成功与否，都跳转页面，不再使用localStorage
        window.location.href = window.location.pathname.includes('/pages/') ? '../index.html' : 'index.html';
    })
    .catch(error => {
        console.error('登出错误:', error);
        // 即使API调用失败，也跳转页面
        window.location.href = window.location.pathname.includes('/pages/') ? '../index.html' : 'index.html';
    });
}

// 检查登录状态函数
async function checkLoginStatus() {
    const user = await checkBackendAuth();
    return !!user;
}

// 获取当前用户信息
async function getCurrentUser() {
    return await checkBackendAuth();
}

// 将函数暴露到全局window对象
window.updateUserIcon = updateUserIcon;
window.getCsrfToken = getCsrfToken;
window.logout = logout;
window.checkBackendAuth = checkBackendAuth;
window.checkLoginStatus = checkLoginStatus;
window.getCurrentUser = getCurrentUser;

// 页面加载完成后更新用户图标
document.addEventListener('DOMContentLoaded', function() {
    updateUserIcon();
});