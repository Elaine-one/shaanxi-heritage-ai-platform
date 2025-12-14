// 通用用户认证脚本

// 缓存认证状态，避免重复请求
let authCheckPromise = null;
let lastAuthCheck = 0;
const AUTH_CACHE_DURATION = 30000; // 30秒缓存

/**
 * 检查后端session是否有效
 */
async function checkBackendAuth(forceRefresh = false) {
    try {
        // 不再使用localStorage，改为直接调用后端API
        
        // 如果已有进行中的请求，等待该请求完成
        if (authCheckPromise) {
            return await authCheckPromise;
        }
        
        // 创建新的认证请求
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
            // 请求完成后清除promise
            authCheckPromise = null;
        });
        
        return await authCheckPromise;
    } catch (error) {
        console.error('[auth.js] Error checking backend auth:', error);
        authCheckPromise = null;
        return null;
    }
}

/**
 * 检查用户登录状态并更新用户图标
 * 在所有页面中使用此函数来保持用户界面的一致性
 */
async function updateUserIcon() {
    console.log('[auth.js] updateUserIcon called.');
    const userIcon = document.querySelector('.user-icon');
    if (!userIcon) {
        console.error('[auth.js] User icon element (.user-icon) not found.');
        return;
    }
    console.log('[auth.js] User icon element found:', userIcon);
    
    // 检查后端认证状态
    const user = await checkBackendAuth();
    console.log('[auth.js] Backend auth check result:', user);
    
    if (user && user.username) {
        console.log('[auth.js] User is logged in:', user);
        
        // 尝试从API获取用户头像
        let hasAvatar = false;
        try {
            // 直接调用后端API获取用户详细信息，不依赖外部API对象
            const response = await fetch('/api/profile/me/', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (response.ok) {
                const userData = await response.json();
                if (userData.profile && userData.profile.avatar) {
                    // 有头像，显示头像
                    userIcon.textContent = '';
                    let avatarUrl = userData.profile.avatar;
                    // 如果是相对URL，添加域名
                    if (avatarUrl.startsWith('/media/')) {
                        avatarUrl = window.location.origin + avatarUrl;
                    }
                    userIcon.style.backgroundImage = `url(${avatarUrl})`;
                    userIcon.style.backgroundSize = 'cover';
                    userIcon.style.backgroundPosition = 'center';
                    // 清除可能存在的文本内容样式
                    userIcon.style.backgroundColor = '';
                    userIcon.style.color = '';
                    hasAvatar = true;
                }
            }
        } catch (error) {
            console.error('[auth.js] Error fetching user profile:', error);
            // 出错时继续执行，后面会显示默认首字母
        }
        
        if (!hasAvatar) {
            // 没有头像或获取失败，显示用户名首字母
            userIcon.textContent = user.username.charAt(0).toUpperCase();
            // 清除背景图像
            userIcon.style.backgroundImage = '';
            userIcon.style.backgroundSize = '';
            userIcon.style.backgroundPosition = '';
            // 设置默认样式
            userIcon.style.backgroundColor = '#8c2e2e';
            userIcon.style.color = 'white';
        }
        
        userIcon.title = `${user.username} (点击查看个人中心)`;
        // 只设置通用样式，不覆盖头像相关样式
        userIcon.style.borderRadius = '50%';
        userIcon.style.width = '30px';
        userIcon.style.height = '30px';
        userIcon.style.display = 'flex';
        userIcon.style.justifyContent = 'center';
        userIcon.style.alignItems = 'center';
        console.log('[auth.js] User icon styled for logged-in user.');
        
        // 点击跳转到个人中心
        userIcon.onclick = function() {
            console.log('[auth.js] User icon clicked (logged in). Attempting to navigate to profile.');
            // 根据当前页面路径确定个人中心页面的相对路径
            const isInPagesDir = window.location.pathname.includes('/pages/');
            const profilePath = isInPagesDir ? 'profile.html' : 'pages/profile.html';
            console.log('[auth.js] Navigating to profilePath:', profilePath);
            window.location.href = profilePath;
        };
        console.log('[auth.js] onclick handler set for profile page.');
    } else {
        console.log('[auth.js] User is not logged in or user data is incomplete.');
        // 用户未登录
        userIcon.textContent = '👤';
        userIcon.title = '登录/注册';
        // Reset styles to default if they were changed
        userIcon.style.backgroundColor = ''; 
        userIcon.style.color = '';
        userIcon.style.borderRadius = '';
        userIcon.style.width = '';
        userIcon.style.height = '';
        userIcon.style.display = '';
        userIcon.style.justifyContent = '';
        userIcon.style.alignItems = '';
        console.log('[auth.js] User icon styled for logged-out user.');
        
        // 点击跳转到登录页面
        userIcon.onclick = function() {
            console.log('[auth.js] User icon clicked (logged out). Attempting to navigate to login.');
            // 根据当前页面路径确定登录页面的相对路径
            const isInPagesDir = window.location.pathname.includes('/pages/');
            const loginPath = isInPagesDir ? 'login.html' : 'pages/login.html';
            console.log('[auth.js] Navigating to loginPath:', loginPath);
            window.location.href = loginPath;
        };
        console.log('[auth.js] onclick handler set for login page.');
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