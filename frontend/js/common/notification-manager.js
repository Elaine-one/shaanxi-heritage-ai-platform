/**
 * Notification Manager
 * 统一的通知管理系统
 */

const NotificationManager = {
    notifications: [],
    notificationCounter: 0,
    maxNotifications: 5,
    defaultDuration: 3000,
    
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
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 2000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
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
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            min-width: 300px;
            max-width: 400px;
            padding: 12px 16px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideInRight 0.2s ease-out;
            cursor: ${onClick ? 'pointer' : 'default'};
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
            icon.textContent = config.icon;
            icon.style.cssText = `
                flex-shrink: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                background: ${config.bgColor};
                color: white;
                font-size: 12px;
                font-weight: bold;
            `;
            notification.appendChild(icon);
        }
        
        const text = document.createElement('span');
        text.textContent = message;
        text.style.cssText = `
            flex: 1;
            font-size: 14px;
            color: white;
            word-break: break-word;
        `;
        notification.appendChild(text);
        
        if (showClose) {
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '&times;';
            closeBtn.style.cssText = `
                flex-shrink: 0;
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                cursor: pointer;
                padding: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                opacity: 0.8;
                transition: opacity 0.2s;
            `;
            closeBtn.addEventListener('mouseenter', () => {
                closeBtn.style.opacity = '1';
            });
            closeBtn.addEventListener('mouseleave', () => {
                closeBtn.style.opacity = '0.8';
            });
            closeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeNotification(notificationId);
            });
            notification.appendChild(closeBtn);
        }
        
        if (onClick) {
            notification.addEventListener('click', onClick);
        }
        
        const notificationId = this.generateId();
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
        
        const { element, id } = this.createNotification(type, message, options);
        container.appendChild(element);
        this.notifications.push(id);
        
        const { duration = this.defaultDuration } = options;
        if (duration > 0) {
            setTimeout(() => {
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
        const container = document.getElementById('notification-container');
        if (!container) return;
        
        const notification = container.querySelector(`[data-id="${notificationId}"]`);
        if (notification) {
            notification.style.animation = 'slideOutRight 0.2s ease-in';
            setTimeout(() => {
                notification.remove();
                this.notifications = this.notifications.filter(id => id !== notificationId);
                
                if (container.children.length === 0) {
                    container.remove();
                }
            }, 200);
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