// 注册页面脚本
document.addEventListener('DOMContentLoaded', function() {
    // 获取注册表单和消息显示区域
    const registerForm = document.getElementById('register-form');
    const registerMessage = document.getElementById('register-message');
    
    // 验证码相关元素
    let captchaKey = '';
    const captchaImage = document.getElementById('captcha-image');
    const captchaInput = document.getElementById('captcha');
    const refreshCaptchaBtn = document.getElementById('refresh-captcha');
    
    // 加载验证码
    loadCaptcha();
    
    // 绑定验证码图片点击事件
    if (captchaImage) {
        captchaImage.addEventListener('click', loadCaptcha);
    }
    
    // 密码可见性切换功能
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const togglePasswordBtn = document.getElementById('toggle-password');
    const toggleConfirmPasswordBtn = document.getElementById('toggle-confirm-password');
    
    // 通用的密码切换函数
    function setupPasswordToggle(inputElement, toggleElement) {
        if (inputElement && toggleElement) {
            // 当密码输入框有内容时显示切换图标
            inputElement.addEventListener('input', function() {
                toggleElement.style.display = this.value ? 'inline-block' : 'none';
            });
            
            // 点击图标切换密码可见性
            toggleElement.addEventListener('click', function() {
                const type = inputElement.getAttribute('type') === 'password' ? 'text' : 'password';
                inputElement.setAttribute('type', type);
                
                // 切换图标样式类
                this.classList.toggle('show-password');
            });
        }
    }
    
    // 为密码和确认密码输入框设置切换功能
    setupPasswordToggle(passwordInput, togglePasswordBtn);
    setupPasswordToggle(confirmPasswordInput, toggleConfirmPasswordBtn);
    
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
    registerForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        // 获取表单数据
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        const captchaValue = captchaInput.value;
        
        // 验证表单数据
        if (!email || !password || !confirmPassword || !captchaValue) {
            showMessage('请填写所有必填字段', 'error');
            return;
        }
        
        // 验证邮箱格式
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(email)) {
            showMessage('邮箱格式不正确', 'error');
            return;
        }
        
        // 验证密码强度
        if (password.length < 8) {
            showMessage('密码长度至少8位', 'error');
            return;
        }
        
        if (!/[A-Z]/.test(password)) {
            showMessage('密码必须包含至少一个大写字母', 'error');
            return;
        }
        
        if (!/[a-z]/.test(password)) {
            showMessage('密码必须包含至少一个小写字母', 'error');
            return;
        }
        
        if (!/\d/.test(password)) {
            showMessage('密码必须包含至少一个数字', 'error');
            return;
        }
        
        if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
            showMessage('密码必须包含至少一个特殊字符', 'error');
            return;
        }
        
        if (password !== confirmPassword) {
            showMessage('两次输入的密码不一致', 'error');
            return;
        }
        
        // Ensure CSRF cookie is set before making a POST request
        try {
            await fetch('/api/auth/csrf/');
            console.log('CSRF token endpoint called for register.');
        } catch (csrfError) {
            console.warn('Failed to fetch CSRF token, proceeding with existing cookie if any:', csrfError);
            // Proceed even if this fails, as the cookie might already be set
        }
        
        // 发送注册请求
        fetch('/api/auth/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                email: email,
                password: password,
                captcha_key: captchaKey,
                captcha_value: captchaValue
            }),
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    // 刷新验证码
                    loadCaptcha();
                    throw new Error(data.message || '注册失败');
                });
            }
            return response.json();
        })
        .then(data => {
            // 注册成功
            showMessage('注册成功，请登录', 'success');
            
            // 延迟后跳转到登录页面
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        })
        .catch(error => {
            showMessage(error.message || '注册失败，请稍后重试', 'error');
            console.error('注册错误:', error);
        });
    });
    
    // 显示消息函数
    function showMessage(message, type) {
        registerMessage.textContent = message;
        registerMessage.className = 'auth-message ' + type;
    }
    
    // 使用公共的getCookie函数（已在utils.js中定义）
});