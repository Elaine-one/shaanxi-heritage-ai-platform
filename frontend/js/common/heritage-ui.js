/**
 * 非遗项目UI辅助函数
 * 负责处理所有UI相关功能
 */

/**
 * 显示一个简单的提示消息
 * @param {string} message 消息内容
 * @param {number} duration 显示时长(毫秒)，默认3000
 */
window.showToast = function(message, duration = 3000) {
    // 检查是否已存在toast
    let toast = document.getElementById('toast-message');
    
    if (!toast) {
        // 创建toast元素
        toast = document.createElement('div');
        toast.id = 'toast-message';
        toast.style.cssText = `
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            z-index: 1000;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s;
        `;
        document.body.appendChild(toast);
    }
    
    // 设置消息内容并显示
    toast.textContent = message;
    toast.style.opacity = '1';
    
    // 指定时间后隐藏
    setTimeout(() => {
        toast.style.opacity = '0';
    }, duration);
}

/**
 * 显示加载中动画
 * @param {string} message 加载提示消息，默认为"加载中..."
 * @returns {Object} 加载器对象，包含close方法
 */
function showLoading(message = "加载中...") {
    // 创建加载遮罩
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    // 创建加载内容
    const content = document.createElement('div');
    content.className = 'loading-content';
    content.style.cssText = `
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
        text-align: center;
    `;
    
    // 创建加载动画
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.style.cssText = `
        width: 40px;
        height: 40px;
        margin: 0 auto 10px;
        border: 4px solid #f3f3f3;
        border-top: 4px solid #c53b3b;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    `;
    
    // 添加动画样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
    
    // 创建消息文本
    const text = document.createElement('div');
    text.textContent = message;
    text.style.cssText = `
        color: #333;
        font-size: 14px;
    `;
    
    // 组装DOM
    content.appendChild(spinner);
    content.appendChild(text);
    overlay.appendChild(content);
    document.body.appendChild(overlay);
    
    // 返回加载器对象
    return {
        // 关闭加载动画
        close: function() {
            document.body.removeChild(overlay);
        },
        // 更新消息
        updateMessage: function(newMessage) {
            text.textContent = newMessage;
        }
    };
}

/**
 * 显示确认对话框
 * @param {string} message 确认消息
 * @param {Function} onConfirm 确认回调函数
 * @param {Function} onCancel 取消回调函数
 */
function showConfirm(message, onConfirm, onCancel) {
    // 创建对话框遮罩
    const overlay = document.createElement('div');
    overlay.className = 'confirm-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
    `;
    
    // 创建对话框
    const dialog = document.createElement('div');
    dialog.className = 'confirm-dialog';
    dialog.style.cssText = `
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
        max-width: 400px;
        width: 80%;
    `;
    
    // 创建消息
    const messageElem = document.createElement('div');
    messageElem.className = 'confirm-message';
    messageElem.textContent = message;
    messageElem.style.cssText = `
        margin-bottom: 20px;
        color: #333;
        font-size: 16px;
    `;
    
    // 创建按钮容器
    const buttons = document.createElement('div');
    buttons.className = 'confirm-buttons';
    buttons.style.cssText = `
        display: flex;
        justify-content: flex-end;
    `;
    
    // 取消按钮
    const cancelButton = document.createElement('button');
    cancelButton.textContent = '取消';
    cancelButton.style.cssText = `
        padding: 8px 15px;
        margin-right: 10px;
        border: 1px solid #ddd;
        background-color: #f5f5f5;
        color: #333;
        border-radius: 4px;
        cursor: pointer;
    `;
    
    // 确认按钮
    const confirmButton = document.createElement('button');
    confirmButton.textContent = '确认';
    confirmButton.style.cssText = `
        padding: 8px 15px;
        border: none;
        background-color: #c53b3b;
        color: white;
        border-radius: 4px;
        cursor: pointer;
    `;
    
    // 添加事件
    cancelButton.addEventListener('click', function() {
        document.body.removeChild(overlay);
        if (typeof onCancel === 'function') {
            onCancel();
        }
    });
    
    confirmButton.addEventListener('click', function() {
        document.body.removeChild(overlay);
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
    });
    
    // 组装DOM
    buttons.appendChild(cancelButton);
    buttons.appendChild(confirmButton);
    dialog.appendChild(messageElem);
    dialog.appendChild(buttons);
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
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

/**
 * 根据级别生成星级显示
 * @param {string} level 级别
 * @returns {string} 星级HTML
 */
function getStarsHTML(level) {
    let starCount = 0;
    
    switch (level) {
        case '国家级': starCount = 5; break;
        case '省级': starCount = 4; break;
        case '市级': starCount = 3; break;
        case '县级': starCount = 2; break;
        default: starCount = 1;
    }
    
    return '★'.repeat(starCount);
}

/**
 * 添加样式到页面头部
 * @param {string} css CSS样式内容
 * @param {string} id 样式标识ID
 */
function addStyle(css, id) {
    // 如果已存在相同ID的样式，则不重复添加
    if (id && document.getElementById(id)) {
        return;
    }
    
    const style = document.createElement('style');
    if (id) {
        style.id = id;
    }
    style.textContent = css;
    document.head.appendChild(style);
}

// 导出模块
window.HeritageUI = {
    showToast: showToast,
    addStyle: addStyle,
    showLoading: showLoading, //  确保 showLoading 也导出
    showConfirm: showConfirm, //  确保 showConfirm 也导出
    getLevelClass: getLevelClass, // 确保 getLevelClass 也导出
    getStarsHTML: getStarsHTML // 确保 getStarsHTML 也导出
};

// 如果其他地方确实需要单独导出 showToast, 可以保留，但通常 window.showToast 已经够用
// 如果不需要模块化导出，可以移除下面这行
// export { showToast }; 
// 为了解决报错，暂时注释或移除 export 语句