/**
 * 背景图片处理工具
 * 处理data-bg-image属性，将其转换为CSS background-image
 */

class BackgroundImageHandler {
    static init() {
        // 处理页面加载时已存在的元素
        this.processElements();
        
        // 监听DOM变化，处理动态添加的元素
        this.observeChanges();
    }
    
    static processElements() {
        const elements = document.querySelectorAll('[data-bg-image]');
        elements.forEach(element => {
            this.setBackgroundImage(element);
        });
    }
    
    static setBackgroundImage(element) {
        const imageUrl = element.getAttribute('data-bg-image');
        if (imageUrl && imageUrl.trim() !== '') {
            element.style.backgroundImage = `url('${imageUrl}')`;
        }
    }
    
    static observeChanges() {
        // 创建MutationObserver来监听DOM变化
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                // 处理新添加的节点
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // 检查节点本身是否有data-bg-image属性
                            if (node.hasAttribute && node.hasAttribute('data-bg-image')) {
                                this.setBackgroundImage(node);
                            }
                            
                            // 检查子节点中是否有data-bg-image属性
                            const childElements = node.querySelectorAll ? node.querySelectorAll('[data-bg-image]') : [];
                            childElements.forEach(element => {
                                this.setBackgroundImage(element);
                            });
                        }
                    });
                }
                
                // 处理属性变化
                if (mutation.type === 'attributes' && mutation.attributeName === 'data-bg-image') {
                    this.setBackgroundImage(mutation.target);
                }
            });
        });
        
        // 开始观察
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['data-bg-image']
        });
    }
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        BackgroundImageHandler.init();
    });
} else {
    BackgroundImageHandler.init();
}

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BackgroundImageHandler;
}

// 全局访问
window.BackgroundImageHandler = BackgroundImageHandler;