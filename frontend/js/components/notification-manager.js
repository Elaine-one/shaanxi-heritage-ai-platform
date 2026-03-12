/**
 * Notification Manager
 * 统一的通知管理系统
 */

const NotificationManager = {
    notifications: [],
    notificationCounter: 0,
    maxNotifications: 5,
    defaultDuration: 5000,
    
    /**
     * 生成唯一的通知ID
     * @returns {string}
     */
    generateId() {
        return `notification-${++this.notificationCounter}`;
    },
    
    /**
     * 创建通知容器
     * @returns {HTMLElement}
     */
    createContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            document.body.appendChild(container);
        }
        return container;
    },
    
    /**
     * 创建通知元素
     * @param {string} type - 类型: 'success', 'error', 'warning', 'info'
     * @param {string} message - 消息内容
     * @param {Object} options - 配置选项
     * @returns {HTMLElement}
     */
    createNotification(type, message, options = {}) {
        const {
            duration = this.defaultDuration,
            showIcon = true,
            showClose = true,
            onClick = null
        } = options;
        
        // 先生成ID，确保在事件处理中可以使用
        const notificationId = this.generateId();
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        if (onClick) {
            notification.classList.add('clickable');
        }
        notification.style.cssText = `
            position: relative;
            overflow: hidden;
        `;
        
        const typeConfig = {
            success: { icon: '✓', color: '#4CAF50', bgColor: '#4CAF50' },
            error: { icon: '✕', color: '#F44336', bgColor: '#F44336' },
            warning: { icon: '⚠', color: '#FF9800', bgColor: '#FF9800' },
            info: { icon: 'ℹ', color: '#2196F3', bgColor: '#2196F3' }
        };
        
        const config = typeConfig[type] || typeConfig.info;
        
        if (showIcon) {
            const icon = document.createElement('span');
            icon.className = 'notification-icon';
            icon.textContent = config.icon;
            notification.appendChild(icon);
        }
        
        const text = document.createElement('span');
        text.className = 'notification-text';
        text.textContent = message;
        notification.appendChild(text);
        
        if (showClose) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'notification-close';
            closeBtn.innerHTML = '&times;';
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeNotification(notificationId);
            });
            notification.appendChild(closeBtn);
        }
        
        if (onClick) {
            notification.addEventListener('click', onClick);
        }
        
        notification.dataset.id = notificationId;
        
        return { element: notification, id: notificationId };
    },
    
    /**
     * 显示通知
     * @param {string} type - 类型
     * @param {string} message - 消息
     * @param {Object} options - 配置
     * @returns {string} 通知ID
     */
    show(type, message, options = {}) {
        const container = this.createContainer();
        
        if (this.notifications.length >= this.maxNotifications) {
            this.removeNotification(this.notifications[0]);
        }
        
        // 先获取duration，确保在使用前已定义
        const { duration = this.defaultDuration } = options;
        
        const { element, id } = this.createNotification(type, message, options);
        
        // 添加进度条
        if (duration > 0) {
            const progressBar = document.createElement('div');
            progressBar.style.cssText = `
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background: rgba(255, 255, 255, 0.7);
                width: 100%;
                transform-origin: left;
                animation: notification-progress ${duration}ms linear forwards;
            `;
            element.appendChild(progressBar);
        }
        
        container.appendChild(element);
        this.notifications.push(id);
        
        console.log(`[NotificationManager] 创建通知: ${message}, 持续时间: ${duration}ms`);
        if (duration > 0) {
            setTimeout(() => {
                console.log(`[NotificationManager] 定时移除通知: ${id}`);
                this.removeNotification(id);
            }, duration);
        }
        
        console.log(`[NotificationManager] ${type.toUpperCase()}: ${message}`);
        return id;
    },
    
    /**
     * 显示成功通知
     * @param {string} message - 消息
     * @param {Object} options - 配置
     * @returns {string} 通知ID
     */
    success(message, options = {}) {
        return this.show('success', message, options);
    },
    
    /**
     * 显示错误通知
     * @param {string} message - 消息
     * @param {Object} options - 配置
     * @returns {string} 通知ID
     */
    error(message, options = {}) {
        return this.show('error', message, options);
    },
    
    /**
     * 显示警告通知
     * @param {string} message - 消息
     * @param {Object} options - 配置
     * @returns {string} 通知ID
     */
    warning(message, options = {}) {
        return this.show('warning', message, options);
    },
    
    /**
     * 显示信息通知
     * @param {string} message - 消息
     * @param {Object} options - 配置
     * @returns {string} 通知ID
     */
    info(message, options = {}) {
        return this.show('info', message, options);
    },
    
    /**
     * 显示登录必需通知
     * @param {string} action - 操作名称
     * @param {Object} options - 配置
     * @returns {string} 通知ID
     */
    loginRequired(action, options = {}) {
        const {
            message = `${action}功能需要登录后才能使用`,
            autoRedirect = true,
            redirectUrl = null,
            onClick = null
        } = options;
        
        const notificationId = this.show('warning', message, {
            duration: 0,
            showClose: true,
            onClick: (e) => {
                if (onClick) {
                    onClick(e);
                } else if (autoRedirect) {
                    window.location.href = AuthRedirect.getLoginUrl(redirectUrl);
                }
            }
        });
        
        return notificationId;
    },
    
    /**
     * 移除通知
     * @param {string} notificationId - 通知ID
     */
    removeNotification(notificationId) {
        console.log(`[NotificationManager] 开始移除通知: ${notificationId}`);
        const container = document.getElementById('notification-container');
        if (!container) {
            console.log('[NotificationManager] 容器不存在，跳过移除');
            return;
        }
        
        const notification = container.querySelector(`[data-id="${notificationId}"]`);
        if (notification) {
            console.log('[NotificationManager] 找到通知元素，开始动画移除');
            notification.style.animation = 'slideOutRight 0.2s ease-in';
            setTimeout(() => {
                notification.remove();
                this.notifications = this.notifications.filter(id => id !== notificationId);
                console.log(`[NotificationManager] 通知已移除，剩余通知: ${this.notifications.length}`);
                
                if (container.children.length === 0) {
                    container.remove();
                }
            }, 200);
        } else {
            console.log(`[NotificationManager] 未找到通知元素: ${notificationId}`);
        }
    },
    
    /**
     * 清除所有通知
     */
    clear() {
        const container = document.getElementById('notification-container');
        if (container) {
            container.remove();
            this.notifications = [];
        }
    }
};

if (typeof window !== 'undefined') {
    window.NotificationManager = NotificationManager;
}