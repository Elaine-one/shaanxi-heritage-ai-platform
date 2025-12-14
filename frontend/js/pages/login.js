// 登录页面脚本
document.addEventListener('DOMContentLoaded', function() {
    // 获取登录表单和消息显示区域
    const loginForm = document.getElementById('login-form');
    const loginMessage = document.getElementById('login-message');
    const userIcon = document.querySelector('.user-icon');
    
    // 验证码相关元素
    let captchaKey = '';
    const captchaImage = document.getElementById('captcha-image');
    const captchaInput = document.getElementById('captcha');
    const refreshCaptchaBtn = document.getElementById('refresh-captcha');
    
    // 检查DOM元素是否已加载
    if (!loginForm || !loginMessage || !userIcon) {
        console.error('DOM元素未正确加载，请检查页面结构');
        return;
    }
    
    // 密码可见性切换功能
    const passwordInput = document.getElementById('password');
    const togglePassword = document.getElementById('toggle-password');
    
    if (passwordInput && togglePassword) {
        // 当密码输入框有内容时显示切换图标
        passwordInput.addEventListener('input', function() {
            togglePassword.style.display = this.value ? 'inline-block' : 'none';
        });
        
        // 点击图标切换密码可见性
        togglePassword.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // 切换图标样式类
            this.classList.toggle('show-password');
        });
    }
    
    // 检查用户是否已登录
    checkLoginStatus();
    
    // 加载验证码
    loadCaptcha();
    
    // 绑定验证码图片点击事件
    if (captchaImage) {
        captchaImage.addEventListener('click', loadCaptcha);
    }
    
    // 加载验证码图片
    function loadCaptcha() {
        fetch('/api/auth/captcha/generate/', {
            method: 'GET',
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            captchaKey = data.captcha_key;
            captchaImage.src = `data:image/png;base64,${data.captcha_image}`;
        })
        .catch(error => {
            console.error('加载验证码失败:', error);
            showMessage('加载验证码失败，请重试', 'error');
        });
    }
    
    // 添加表单提交事件监听器
    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        // 获取表单数据 - 添加空值检查
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        const rememberMeCheckbox = document.getElementById('remember-me');
        
        if (!emailInput || !passwordInput || !captchaInput) {
            showMessage('表单元素未正确加载，请刷新页面重试', 'error');
            return;
        }
        
        const email = emailInput.value;
        const password = passwordInput.value;
        const rememberMe = rememberMeCheckbox ? rememberMeCheckbox.checked : false;
        const captchaValue = captchaInput.value;
        
        // 验证表单数据
        if (!email || !password || !captchaValue) {
            showMessage('请填写邮箱地址、密码和验证码', 'error');
            return;
        }
        
        // 验证邮箱格式
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            showMessage('请输入有效的邮箱地址', 'error');
            return;
        }
        
        // Ensure CSRF cookie is set before making a POST request
        try {
            const csrfResponse = await fetch('/api/auth/csrf/');
            if (csrfResponse.ok) {
                console.log('CSRF token endpoint called for login.');
            } else {
                console.warn('CSRF token endpoint returned non-OK status:', csrfResponse.status);
            }
        } catch (csrfError) {
            console.warn('Failed to fetch CSRF token, proceeding with existing cookie if any:', csrfError);
            // Proceed even if this fails, as the cookie might already be set
        }
        
        // 发送登录请求
        fetch('/api/auth/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                email: email,
                password: password,
                remember_me: rememberMe,
                captcha_key: captchaKey,
                captcha_value: captchaValue
            }),
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                // 处理不同的错误状态
                if (response.status === 429) {
                    throw new Error('登录失败次数过多，请稍后再试');
                } else if (response.status === 403) {
                    throw new Error('账户已被禁用');
                } else if (response.status === 401) {
                    throw new Error('用户名或密码错误');
                } else if (response.status === 400) {
                    // 400错误可能是验证码错误或其他参数错误
                    return response.json().then(data => {
                        // 刷新验证码
                        loadCaptcha();
                        throw new Error(data.message || '登录失败，请检查输入');
                    });
                } else {
                    // 其他错误也刷新验证码
                    loadCaptcha();
                    throw new Error('登录失败');
                }
            }
            return response.json();
        })
        .then(data => {
            // 登录成功
            showMessage('登录成功，正在跳转...', 'success');
            
            // 保存用户信息到本地存储
            localStorage.setItem('user', JSON.stringify({
                username: data.username,
                userId: data.id // Assuming data.id is the user ID
            }));
            // 不再使用token认证，完全依赖session认证
            console.log('登录成功，使用session认证');
            
            // 延迟后跳转到首页
            setTimeout(() => {
                window.location.href = '../index.html';
            }, 1500);
        })
        .catch(error => {
            showMessage(error.message || '登录失败，请重试', 'error');
            console.error('登录错误:', error);
        });
    });
    
    // 显示消息函数
    function showMessage(message, type) {
        loginMessage.textContent = message;
        loginMessage.className = 'auth-message ' + type;
    }
    
    // 使用公共的getCookie函数（已在utils.js中定义）
    
    // 检查登录状态 - 使用全局updateUserIcon函数
    window.updateUserIcon();
});