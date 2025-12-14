// 公共工具函数

// 更新日期时间显示
function updateDateTime() {
    if (window.dateUtils) {
        window.dateUtils.updateDateTimeDisplay('current-date');
    }
}

/**
 * 格式化标准日期时间信息
 * @returns {Object} 包含日期、星期、农历和节气的对象
 */
function formatStandardDateTime() {
    // 检查dateUtils是否可用
    if (!window.dateUtils) {
        // 如果dateUtils不可用，返回基本日期信息
        const now = new Date();
        return {
            date: now.toLocaleDateString('zh-CN'),
            weekday: now.toLocaleDateString('zh-CN', { weekday: 'long' }),
            lunar: '',
            solarTerm: ''
        };
    }
    
    // 使用dateUtils获取完整日期时间信息
    const dateInfo = window.dateUtils.getFullDateTimeInfo();
    return {
        date: dateInfo.formatted,
        weekday: dateInfo.weekday,
        lunar: dateInfo.lunar_date, // 修正属性名，与date-utils.js保持一致
        solarTerm: dateInfo.solar_term
    };
}

// 确保在页面加载完成后调用时间更新函数
document.addEventListener('DOMContentLoaded', function() {
    // 初始更新时间
    updateDateTime();
    
    // 每分钟更新一次时间
    setInterval(updateDateTime, 60000);
});

/**
 * 从cookie中获取指定名称的值
 * @param {string} name cookie的名称
 * @returns {string|null} cookie的值，如果未找到则返回null
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 安全地暴露工具函数到全局
if (typeof window !== 'undefined') {
    // 避免重复声明，只在utils对象不存在时创建
    if (!window.utils) {
        window.utils = {};
    }
    
    // 更新或添加工具函数
    window.utils.updateDateTime = updateDateTime;
    window.utils.formatStandardDateTime = formatStandardDateTime;
    window.utils.getCookie = getCookie;
    
    // 也直接暴露getCookie到全局，以兼容旧代码
    if (!window.getCookie) {
        window.getCookie = getCookie;
    }
}
