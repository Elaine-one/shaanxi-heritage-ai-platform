/**
 * Auth Redirect Manager
 * 管理登录跳转逻辑，支持多种跳转方式
 */

const AuthRedirect = {
    STORAGE_KEY: 'auth_redirect_url',
    
    /**
     * 保存当前页面，用于登录后返回
     * @returns {string} 保存的URL
     */
    saveCurrentPage() {
        const currentUrl = window.location.href;
        sessionStorage.setItem(this.STORAGE_KEY, currentUrl);
        console.log('[AuthRedirect] Saved current page:', currentUrl);
        return currentUrl;
    },
    
    /**
     * 获取登录后应该返回的页面
     * 优先级：URL参数 > SessionStorage > Referrer > 默认首页
     * @returns {string} 跳转URL
     */
    getRedirectUrl() {
        // 1. 检查URL参数
        const urlParams = new URLSearchParams(window.location.search);
        const redirectParam = urlParams.get('redirect');
        if (redirectParam) {
            const decodedUrl = decodeURIComponent(redirectParam);
            console.log('[AuthRedirect] Using URL parameter redirect:', decodedUrl);
            return decodedUrl;
        }
        
        // 2. 检查SessionStorage
        const storageUrl = sessionStorage.getItem(this.STORAGE_KEY);
        if (storageUrl) {
            console.log('[AuthRedirect] Using SessionStorage redirect:', storageUrl);
            return storageUrl;
        }
        
        // 3. 检查Referrer
        if (document.referrer && !document.referrer.includes('login.html')) {
            console.log('[AuthRedirect] Using Referrer redirect:', document.referrer);
            return document.referrer;
        }
        
        // 4. 默认返回首页
        const defaultUrl = '/index.html';
        console.log('[AuthRedirect] Using default redirect:', defaultUrl);
        return defaultUrl;
    },
    
    /**
     * 清除保存的跳转URL
     */
    clearRedirect() {
        sessionStorage.removeItem(this.STORAGE_KEY);
        console.log('[AuthRedirect] Cleared redirect URL');
    },
    
    /**
     * 生成登录URL（带redirect参数）
     * @param {string} redirectUrl - 要跳转的URL，默认为当前页面
     * @returns {string} 登录URL
     */
    getLoginUrl(redirectUrl = null) {
        const url = new URL('/pages/login.html', window.location.origin);
        const targetUrl = redirectUrl || window.location.href;
        url.searchParams.set('redirect', targetUrl);
        console.log('[AuthRedirect] Generated login URL:', url.toString());
        return url.toString();
    },
    
    /**
     * 生成注册URL（带redirect参数）
     * @param {string} redirectUrl - 要跳转的URL，默认为当前页面
     * @returns {string} 注册URL
     */
    getRegisterUrl(redirectUrl = null) {
        const url = new URL('/pages/register.html', window.location.origin);
        const targetUrl = redirectUrl || window.location.href;
        url.searchParams.set('redirect', targetUrl);
        console.log('[AuthRedirect] Generated register URL:', url.toString());
        return url.toString();
    },
    
    /**
     * 处理登录成功后的跳转
     */
    handleLoginSuccess() {
        const redirectUrl = this.getRedirectUrl();
        this.clearRedirect();
        console.log('[AuthRedirect] Redirecting after login to:', redirectUrl);
        window.location.href = redirectUrl;
    },
    
    /**
     * 处理注册成功后的跳转
     */
    handleRegisterSuccess() {
        const redirectUrl = this.getRedirectUrl();
        this.clearRedirect();
        console.log('[AuthRedirect] Redirecting after register to:', redirectUrl);
        window.location.href = redirectUrl;
    },
    
    /**
     * 检查是否在登录页面
     * @returns {boolean}
     */
    isLoginPage() {
        return window.location.pathname.includes('login.html');
    },
    
    /**
     * 检查是否在注册页面
     * @returns {boolean}
     */
    isRegisterPage() {
        return window.location.pathname.includes('register.html');
    }
};

if (typeof window !== 'undefined') {
    window.AuthRedirect = AuthRedirect;
}