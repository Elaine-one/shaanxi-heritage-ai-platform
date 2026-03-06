/**
 * API工具模块
 * 提供统一的API初始化和访问功能
 */

// 初始化API对象
function initAPI() {
    // 确保API对象存在
    if (typeof window.API === 'undefined') {
        console.warn('API对象未定义，正在创建...');
        window.API = {};
    }

    // 初始化heritage API
    initHeritageAPI();
    
    // 可以在这里添加其他API的初始化
    
    return window.API;
}

// 注意：date API 已移除，使用 dateUtils 代替

// 初始化非遗API
function initHeritageAPI() {
    if (typeof window.API.heritage === 'undefined') {
        console.warn('API.heritage对象未定义，正在初始化...');
        // 检查全局heritageAPI对象是否存在（来自heritage-api.js）
        if (typeof heritageAPI !== 'undefined') {
            console.log('使用heritageAPI初始化API.heritage');
            window.API.heritage = heritageAPI;
        } else {
            console.warn('heritageAPI未定义，使用临时API.heritage');
            window.API.heritage = {
                getAllItems: async function(params = {}) {
                    console.warn('使用临时API.heritage.getAllItems');
                    return { results: [] };
                },
                getCategories: async function() {
                    console.warn('使用临时API.heritage.getCategories');
                    return [];
                },
                getLevels: async function() {
                    console.warn('使用临时API.heritage.getLevels');
                    return [];
                },
                getRegions: async function() {
                    console.warn('使用临时API.heritage.getRegions');
                    return [];
                },
                getItemDetail: async function(id) {
                    console.warn('使用临时API.heritage.getItemDetail');
                    return null;
                }
            };
        }
    }
    
    return window.API.heritage;
}

// 显示错误消息
function showErrorMessage(message, containerId = null) {
    if (containerId) {
        // 如果提供了容器ID，在容器内显示错误
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `<div class="error-message">${message}</div>`;
            return;
        }
    }
    
    // 否则创建一个浮动的错误消息
    const errorContainer = document.createElement('div');
    errorContainer.className = 'error-message';
    errorContainer.textContent = message;
    
    // 添加到页面主要内容区域
    const mainContent = document.querySelector('.main-content') || document.body;
    mainContent.prepend(errorContainer);
    
    // 5秒后自动移除
    setTimeout(() => {
        errorContainer.remove();
    }, 5000);
}

// 显示成功消息
function showSuccess(message, options = {}) {
    if (typeof NotificationManager !== 'undefined') {
        return NotificationManager.success(message, options);
    }
    
    // 降级方案：使用旧的错误消息显示方式
    console.log('[Success]', message);
}

// 显示错误消息（新版本）
function showError(message, options = {}) {
    if (typeof NotificationManager !== 'undefined') {
        return NotificationManager.error(message, options);
    }
    
    // 降级方案：使用旧的错误消息显示方式
    showErrorMessage(message);
}

// 显示警告消息
function showWarning(message, options = {}) {
    if (typeof NotificationManager !== 'undefined') {
        return NotificationManager.warning(message, options);
    }
    
    // 降级方案：使用旧的错误消息显示方式
    console.warn('[Warning]', message);
}

// 显示信息消息
function showInfo(message, options = {}) {
    if (typeof NotificationManager !== 'undefined') {
        return NotificationManager.info(message, options);
    }
    
    // 降级方案：使用旧的错误消息显示方式
    console.info('[Info]', message);
}

// 显示登录必需提示
function showLoginRequired(action, options = {}) {
    if (typeof NotificationManager !== 'undefined') {
        return NotificationManager.loginRequired(action, options);
    }
    
    // 降级方案：使用旧的模态框显示方式
    console.warn('[Login Required]', action);
}

// 显示登录模态框
function showLoginModal(options = {}) {
    if (typeof ModalManager !== 'undefined') {
        return ModalManager.showLoginModal(options);
    }
    
    // 降级方案：使用旧的模态框显示方式
    console.warn('[Login Modal]', options);
}

// 显示加载中
function showLoading(containerId = null) {
    if (containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '<div class="loading-indicator">正在加载数据...</div>';
        }
    }
}

// 隐藏加载中
function hideLoading(containerId = null) {
    if (containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            const loadingIndicator = container.querySelector('.loading-indicator');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
        }
    }
}

// 导出模块
const apiUtils = {
    initAPI,
    initHeritageAPI,
    showErrorMessage,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showLoginRequired,
    showLoginModal,
    showLoading,
    hideLoading
};

// 如果在浏览器环境中，将模块添加到全局对象
if (typeof window !== 'undefined') {
    window.apiUtils = apiUtils;
    
    // 自动初始化API
    window.addEventListener('DOMContentLoaded', () => {
        apiUtils.initAPI();
    });
}

