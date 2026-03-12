/**
 * Modal Manager
 * 统一的模态框管理器
 */

const ModalManager = {
    activeModals: new Map(),
    modalCounter: 0,
    
    /**
     * 生成唯一的模态框ID
     * @returns {string}
     */
    generateId() {
        return `modal-${++this.modalCounter}`;
    },
    
    /**
     * 创建模态框遮罩
     * @returns {HTMLElement}
     */
    createOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
            animation: fadeIn 0.3s ease-in-out;
        `;
        return overlay;
    },
    
    /**
     * 创建模态框内容容器
     * @param {string} size - 尺寸: 'small', 'medium', 'large'
     * @returns {HTMLElement}
     */
    createContent(size = 'medium') {
        const content = document.createElement('div');
        content.className = `modal-content ${size}`;
        content.style.cssText = `
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            max-width: 90%;
            max-height: 90%;
            overflow: auto;
            animation: slideIn 0.3s ease-out;
        `;
        
        // 设置尺寸
        const sizeMap = {
            small: '400px',
            medium: '600px',
            large: '800px'
        };
        content.style.maxWidth = sizeMap[size] || sizeMap.medium;
        
        return content;
    },
    
    /**
     * 创建模态框头部
     * @param {string} title - 标题
     * @param {Function} onClose - 关闭回调
     * @returns {HTMLElement}
     */
    createHeader(title, onClose) {
        const header = document.createElement('div');
        header.className = 'modal-header';
        header.style.cssText = `
            padding: 20px 24px;
            border-bottom: 2px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #C1302E 0%, #8B0000 100%);
            position: relative;
        `;
        
        const titleEl = document.createElement('h2');
        titleEl.textContent = title;
        titleEl.style.cssText = `
            margin: 0;
            font-size: 20px;
            font-weight: 600;
            color: #ffffff;
            font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        `;
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'modal-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.style.cssText = `
            background: rgba(255, 255, 255, 0.2);
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #ffffff;
            padding: 0;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 4px;
            transition: background 0.2s;
        `;
        closeBtn.addEventListener('mouseenter', () => {
            closeBtn.style.background = 'rgba(255, 255, 255, 0.3)';
        });
        closeBtn.addEventListener('mouseleave', () => {
            closeBtn.style.background = 'rgba(255, 255, 255, 0.2)';
        });
        closeBtn.addEventListener('click', onClose);
        
        header.appendChild(titleEl);
        header.appendChild(closeBtn);
        
        return header;
    },
    
    /**
     * 创建模态框主体
     * @param {string} content - 内容HTML
     * @returns {HTMLElement}
     */
    createBody(content) {
        const body = document.createElement('div');
        body.className = 'modal-body';
        body.style.cssText = `
            padding: 24px;
        `;
        body.innerHTML = content;
        return body;
    },
    
    /**
     * 创建模态框底部
     * @param {Array} buttons - 按钮数组
     * @returns {HTMLElement}
     */
    createFooter(buttons) {
        const footer = document.createElement('div');
        footer.className = 'modal-footer';
        footer.style.cssText = `
            padding: 16px 24px;
            border-top: 1px solid #e0e0e0;
            display: flex;
            justify-content: flex-end;
            gap: 12px;
        `;
        
        buttons.forEach(btn => {
            const button = document.createElement('button');
            button.textContent = btn.text;
            button.style.cssText = `
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: all 0.2s;
            `;
            
            if (btn.primary) {
                button.classList.add('primary');
            }
            
            button.addEventListener('click', btn.onClick);
            footer.appendChild(button);
        });
        
        return footer;
    },
    
    /**
     * 显示自定义模态框
     * @param {Object} options - 配置选项
     * @returns {Promise}
     */
    showCustomModal(options) {
        return new Promise((resolve) => {
            const {
                title = '提示',
                content = '',
                size = 'medium',
                buttons = [
                    { text: '取消', onClick: () => this.closeModal(modalId) },
                    { text: '确定', primary: true, onClick: () => { this.closeModal(modalId); resolve(true); } }
                ],
                onClose = null,
                closeOnOverlayClick = true
            } = options;
            
            const modalId = this.generateId();
            
            const overlay = this.createOverlay();
            const modalContent = this.createContent(size);
            const header = this.createHeader(title, () => {
                if (onClose) onClose();
                this.closeModal(modalId);
                resolve(false);
            });
            const body = this.createBody(content);
            const footer = this.createFooter(buttons);
            
            modalContent.appendChild(header);
            modalContent.appendChild(body);
            modalContent.appendChild(footer);
            overlay.appendChild(modalContent);
            
            if (closeOnOverlayClick) {
                overlay.addEventListener('click', (e) => {
                    if (e.target === overlay) {
                        if (onClose) onClose();
                        this.closeModal(modalId);
                        resolve(false);
                    }
                });
            }
            
            document.body.appendChild(overlay);
            this.activeModals.set(modalId, overlay);
            
            document.body.style.overflow = 'hidden';
        });
    },
    
    /**
     * 显示确认对话框
     * @param {Object} options - 配置选项
     * @returns {Promise<boolean>}
     */
    showConfirmModal(options) {
        const {
            title = '确认',
            message = '确定要执行此操作吗？',
            confirmText = '确定',
            cancelText = '取消',
            onConfirm = null,
            onCancel = null
        } = options;
        
        return new Promise((resolve) => {
            const modalId = this.generateId();
            
            const overlay = this.createOverlay();
            const modalContent = this.createContent('small');
            const header = this.createHeader(title, () => {
                if (onCancel) onCancel();
                this.closeModal(modalId);
                resolve(false);
            });
            const body = this.createBody(`<p style="margin: 0; font-size: 16px; color: #666;">${message}</p>`);
            
            const buttons = [
                { 
                    text: cancelText, 
                    onClick: () => {
                        if (onCancel) onCancel();
                        this.closeModal(modalId);
                        resolve(false);
                    }
                },
                { 
                    text: confirmText, 
                    primary: true,
                    onClick: () => {
                        if (onConfirm) onConfirm();
                        this.closeModal(modalId);
                        resolve(true);
                    }
                }
            ];
            const footer = this.createFooter(buttons);
            
            modalContent.appendChild(header);
            modalContent.appendChild(body);
            modalContent.appendChild(footer);
            overlay.appendChild(modalContent);
            
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    if (onCancel) onCancel();
                    this.closeModal(modalId);
                    resolve(false);
                }
            });
            
            document.body.appendChild(overlay);
            this.activeModals.set(modalId, overlay);
            document.body.style.overflow = 'hidden';
        });
    },
    
    /**
     * 显示登录模态框
     * @param {Object} options - 配置选项
     * @returns {Promise<boolean>}
     */
    showLoginModal(options = {}) {
        const {
            title = '需要登录',
            message = '您需要登录后才能进行此操作',
            action = null,
            showRegister = true,
            autoRedirect = true,
            onLogin = null,
            onRegister = null
        } = options;
        
        let contentHtml = `<p style="margin: 0; font-size: 16px; color: #666;">${message}</p>`;
        
        if (action) {
            contentHtml += `<p style="margin: 12px 0 0 0; font-size: 14px; color: #999;">操作：${action}</p>`;
        }
        
        return this.showCustomModal({
            title,
            content: contentHtml,
            size: 'small',
            buttons: [
                { 
                    text: '取消', 
                    onClick: function() {
                        // 关闭模态框
                        const modal = this.closest('.modal-overlay');
                        if (modal) {
                            modal.remove();
                            document.body.style.overflow = '';
                        }
                    }
                },
                ...(showRegister ? [{ 
                    text: '去注册', 
                    onClick: () => {
                        if (autoRedirect) {
                            window.location.href = AuthRedirect.getRegisterUrl();
                        }
                        if (onRegister) onRegister();
                    }
                }] : []),
                { 
                    text: '去登录', 
                    primary: true, 
                    onClick: () => {
                        if (autoRedirect) {
                            window.location.href = AuthRedirect.getLoginUrl();
                        }
                        if (onLogin) onLogin();
                    }
                }
            ],
            onClose: () => {
                // 模态框关闭时的回调
            }
        });
    },
    
    /**
     * 关闭指定模态框
     * @param {string} modalId - 模态框ID
     */
    closeModal(modalId) {
        const overlay = this.activeModals.get(modalId);
        if (overlay) {
            overlay.style.animation = 'fadeOut 0.3s ease-in-out';
            setTimeout(() => {
                overlay.remove();
                this.activeModals.delete(modalId);
                
                if (this.activeModals.size === 0) {
                    document.body.style.overflow = '';
                }
            }, 300);
        }
    },
    
    /**
     * 关闭所有模态框
     */
    closeAllModals() {
        this.activeModals.forEach((overlay, modalId) => {
            this.closeModal(modalId);
        });
    }
};

if (typeof window !== 'undefined') {
    window.ModalManager = ModalManager;
}