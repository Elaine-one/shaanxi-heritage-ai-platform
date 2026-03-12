// 忘记密码页面脚本
document.addEventListener('DOMContentLoaded', function() {
    // 获取表单和消息显示区域
    const forgotPasswordForm = document.getElementById('forgot-password-form');
    const forgotPasswordMessage = document.getElementById('forgot-password-message');
    
    // 添加表单提交事件监听器
    forgotPasswordForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        // 获取表单数据
        const email = document.getElementById('email').value;
        
        // 验证表单数据
        if (!email) {
            showMessage('请填写邮箱地址', 'error');
            return;
        }
        
        // 验证邮箱格式
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(email)) {
            showMessage('邮箱格式不正确', 'error');
            return;
        }
        
        // 发送重置密码请求
        try {
            // 确保CSRF cookie已设置
            await fetch('/api/auth/csrf/');
            
            const response = await fetch('/api/auth/request-password-reset/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    email: email
                }),
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showMessage('重置链接已发送到您的邮箱，请查收', 'success');
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 3000);
            } else {
                if (response.status === 404) {
                    showMessage('该邮箱地址未注册', 'error');
                } else if (response.status === 429) {
                    showMessage('请求过于频繁，请稍后重试', 'error');
                } else {
                    showMessage(data.message || '发送重置链接失败，请稍后重试', 'error');
                }
            }
            
        } catch (error) {
            console.error('请求密码重置失败:', error);
            showMessage('网络错误，请检查网络连接后重试', 'error');
        }
    });
    
    // 显示消息函数
    function showMessage(message, type) {
        forgotPasswordMessage.textContent = message;
        forgotPasswordMessage.className = 'auth-message ' + type;
    }
    
    // 使用公共的getCookie函数（已在utils.js中定义）
});