/**
 * Login Modal Component
 * 专门的登录提醒组件
 */

const LoginModal = {
    /**
     * 显示登录模态框
     * @param {Object} options - 配置选项
     * @returns {Promise<boolean>}
     */
    show(options = {}) {
        const {
            title = '需要登录',
            message = '您需要登录后才能进行此操作',
            action = null,
            showRegister = true,
            autoRedirect = true,
            redirectUrl = null,
            onLogin = null,
            onRegister = null,
            onCancel = null
        } = options;
        
        return ModalManager.showLoginModal({
            title,
            message,
            action,
            showRegister,
            autoRedirect,
            redirectUrl,
            onLogin: () => {
                if (onLogin) onLogin();
            },
            onRegister: () => {
                if (onRegister) onRegister();
            },
            onClose: () => {
                if (onCancel) onCancel();
            }
        });
    },
    
    /**
     * 显示收藏登录提醒
     * @param {Object} options - 配置选项
     * @returns {Promise<boolean>}
     */
    showForFavorite(options = {}) {
        return this.show({
            title: '需要登录',
            message: '收藏功能需要登录后才能使用',
            action: '收藏',
            showRegister: true,
            ...options
        });
    },
    
    /**
     * 显示评论登录提醒
     * @param {Object} options - 配置选项
     * @returns {Promise<boolean>}
     */
    showForComment(options = {}) {
        return this.show({
            title: '需要登录',
            message: '评论功能需要登录后才能使用',
            action: '评论',
            showRegister: true,
            ...options
        });
    },
    
    /**
     * 显示发布登录提醒
     * @param {Object} options - 配置选项
     * @returns {Promise<boolean>}
     */
    showForPost(options = {}) {
        return this.show({
            title: '需要登录',
            message: '发布功能需要登录后才能使用',
            action: '发布',
            showRegister: true,
            ...options
        });
    },
    
    /**
     * 显示点赞登录提醒
     * @param {Object} options - 配置选项
     * @returns {Promise<boolean>}
     */
    showForLike(options = {}) {
        return this.show({
            title: '需要登录',
            message: '点赞功能需要登录后才能使用',
            action: '点赞',
            showRegister: true,
            ...options
        });
    },
    
    /**
     * 显示关注登录提醒
     * @param {Object} options - 配置选项
     * @returns {Promise<boolean>}
     */
    showForFollow(options = {}) {
        return this.show({
            title: '需要登录',
            message: '关注功能需要登录后才能使用',
            action: '关注',
            showRegister: true,
            ...options
        });
    }
};

if (typeof window !== 'undefined') {
    window.LoginModal = LoginModal;
}