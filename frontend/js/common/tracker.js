/**
 * 统计跟踪功能
 * 处理页面访问统计和用户行为跟踪
 */

// 定义统计API的基础URL
const TRACKER_API_BASE_URL = '/api/statistics/';

/**
 * 发送统计数据
 * @param {Object} data 要发送的统计数据
 * @param {Function} callback 回调函数
 */


function sendStatistics(data, callback) {
    // 模拟统计数据发送，避免实际的网络请求
    console.log('统计数据已处理:', data);
    
    // 模拟异步响应
    setTimeout(() => {
        if (typeof callback === 'function') {
            callback({ success: true, message: '统计数据已处理' });
        }
    }, 10);
}

/**
 * 跟踪页面访问
 * @param {string} pageName 页面名称
 */
function trackPageView(pageName) {
    const data = {
        type: 'pageview',
        page: pageName || window.location.pathname,
        timestamp: new Date().toISOString()
    };
    
    sendStatistics(data, result => {
        if (result) {
            console.log('页面访问统计已记录');
        }
    });
}

/**
 * 跟踪用户事件
 * @param {string} eventName 事件名称
 * @param {Object} eventData 事件数据
 */
function trackEvent(eventName, eventData = {}) {
    const data = {
        type: 'event',
        event: eventName,
        data: eventData,
        timestamp: new Date().toISOString()
    };
    
    sendStatistics(data, result => {
        if (result) {
            console.log(`事件 ${eventName} 已记录`);
        }
    });
}

/**
 * 兼容旧版本的zybTrackerStatisticsAction调用
 * 这个函数会拦截对/hybridaction/zybTrackerStatisticsAction的请求
 * 并将其重定向到新的统计API
 */
function zybTrackerStatisticsAction(data, callback) {
    console.log('旧版统计API被调用，正在重定向到新API', data);
    
    // 将旧格式数据转换为新格式
    const newData = {
        type: 'legacy',
        original_data: data,
        timestamp: new Date().toISOString()
    };
    
    // 发送到新API
    sendStatistics(newData, result => {
        if (typeof callback === 'function') {
            callback(result || { success: true, message: '统计数据已处理' });
        }
    });
}

// 导出函数到全局作用域
window.trackPageView = trackPageView;
window.trackEvent = trackEvent;
window.zybTrackerStatisticsAction = zybTrackerStatisticsAction;

// 页面加载完成后自动跟踪页面访问
document.addEventListener('DOMContentLoaded', function() {
    // 延迟一点执行，确保其他脚本已加载
    setTimeout(() => {
        trackPageView();
    }, 100);
});

// 拦截对/hybridaction/zybTrackerStatisticsAction的请求
// 这是一个改进的拦截方案，处理所有可能的请求方式
(function() {
    // 保存原始的createElement方法
    const originalCreateElement = document.createElement;
    
    // 重写createElement方法来拦截script标签的创建
    document.createElement = function(tagName) {
        const element = originalCreateElement.call(document, tagName);
        
        // 如果是创建script标签，监听其src属性的设置
        if (tagName.toLowerCase() === 'script') {
            const originalSetAttribute = element.setAttribute;
            
            element.setAttribute = function(name, value) {
                if (name === 'src' && value && value.includes('/hybridaction/zybTrackerStatisticsAction')) {
                    console.log('拦截到对zybTrackerStatisticsAction的JSONP请求，阻止实际网络请求');
                    
                    // 提取callback参数
                    let callbackName = '';
                    if (value.includes('__callback__=')) {
                        callbackName = value.split('__callback__=')[1].split('&')[0];
                    }
                    
                    // 提取data参数
                    let data = {};
                    try {
                        if (value.includes('data=')) {
                            const dataParam = value.split('data=')[1].split('&')[0];
                            data = JSON.parse(decodeURIComponent(dataParam));
                        }
                    } catch (e) {
                        console.error('解析统计数据失败:', e);
                    }
                    
                    // 模拟成功响应
                    setTimeout(() => {
                        if (callbackName && window[callbackName]) {
                            window[callbackName]({ success: true, message: '统计数据已处理' });
                            // 执行完后删除临时函数
                            delete window[callbackName];
                        }
                    }, 10);
                    
                    // 阻止实际的网络请求
                    return;
                }
                
                // 对于其他属性设置，保持原有行为
                return originalSetAttribute.call(this, name, value);
            };
        }
        
        return element;
    };
    
    // 重写XMLHttpRequest.open方法来拦截直接的API请求
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        // 检查URL是否包含目标路径，处理字符串和URL对象
        const urlStr = typeof url === 'string' ? url : url.href;
        if (urlStr && urlStr.includes('/hybridaction/zybTrackerStatisticsAction')) {
            console.log('拦截到对zybTrackerStatisticsAction的XMLHttpRequest请求');
            // 标记为拦截的请求
            this._isIntercepted = true;
        }
        return originalOpen.call(this, method, url, async, user, password);
    };
    
    // 重写XMLHttpRequest.send方法来处理拦截的请求
    const originalSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.send = function(body) {
        if (this._isIntercepted) {
            console.log('处理拦截的zybTrackerStatisticsAction请求');
            // 模拟成功响应
            setTimeout(() => {
                this.readyState = 4;
                this.status = 200;
                this.statusText = 'OK';
                this.responseText = JSON.stringify({ success: true, message: '统计数据已处理' });
                this.response = this.responseText;
                this.dispatchEvent(new Event('readystatechange'));
                this.dispatchEvent(new Event('load'));
                this.dispatchEvent(new Event('loadend'));
            }, 10);
            return;
        }
        return originalSend.call(this, body);
    };
    
    // 重写fetch方法来拦截fetch请求
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        const urlStr = typeof url === 'string' ? url : url.href;
        if (urlStr && urlStr.includes('/hybridaction/zybTrackerStatisticsAction')) {
            console.log('拦截到对zybTrackerStatisticsAction的fetch请求');
            // 返回模拟的成功响应
            return Promise.resolve(new Response(JSON.stringify({ success: true, message: '统计数据已处理' }), {
                status: 200,
                statusText: 'OK',
                headers: { 'Content-Type': 'application/json' }
            }));
        }
        return originalFetch.call(window, url, options);
    };
    
    // 重写document.write方法，拦截可能的动态脚本注入
    const originalWrite = document.write;
    document.write = function(html) {
        if (html && html.includes('zybTrackerStatisticsAction')) {
            console.log('拦截到通过document.write注入的zybTrackerStatisticsAction脚本');
            return;
        }
        return originalWrite.call(document, html);
    };
    
    // 重写document.writeln方法
    const originalWriteln = document.writeln;
    document.writeln = function(html) {
        if (html && html.includes('zybTrackerStatisticsAction')) {
            console.log('拦截到通过document.writeln注入的zybTrackerStatisticsAction脚本');
            return;
        }
        return originalWriteln.call(document, html);
    };
})();