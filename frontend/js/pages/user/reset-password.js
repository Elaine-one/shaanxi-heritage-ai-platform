// 密码重置页面JavaScript逻辑

// 获取URL参数
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    const results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

// 密码强度检查
function checkPasswordStrength(password) {
    let strength = 0;
    let text = '密码强度：弱';
    let color = '#ff4757';
    
    if (password.length >= 8) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    switch(strength) {
        case 0:
        case 1:
        case 2:
            text = '密码强度：弱';
            color = '#ff4757';
            break;
        case 3:
        case 4:
            text = '密码强度：中等';
            color = '#ffa500';
            break;
        case 5:
            text = '密码强度：强';
            color = '#2ed573';
            break;
    }
    
    return { strength: strength, text: text, color: color, width: (strength / 5) * 100 + '%' };
}

// 更新密码强度显示
function updatePasswordStrength() {
    const password = document.getElementById('new-password').value;
    const strengthInfo = checkPasswordStrength(password);
    
    document.getElementById('strength-fill').style.width = strengthInfo.width;
    document.getElementById('strength-fill').style.backgroundColor = strengthInfo.color;
    document.getElementById('strength-text').textContent = strengthInfo.text;
    document.getElementById('strength-text').style.color = strengthInfo.color;
}

// 检查密码是否匹配
function checkPasswordMatch() {
    const password = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const matchDiv = document.getElementById('password-match');
    
    if (confirmPassword === '') {
        matchDiv.textContent = '';
        matchDiv.className = 'password-match';
        return false;
    }
    
    if (password === confirmPassword) {
        matchDiv.textContent = '密码匹配';
        matchDiv.className = 'password-match match';
        return true;
    } else {
        matchDiv.textContent = '密码不匹配';
        matchDiv.className = 'password-match no-match';
        return false;
    }
}

// 显示消息
function showMessage(message, type = 'error') {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = message;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';
    
    if (type !== 'success') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }
}

// 确保CSRF Token已设置
async function ensureCsrfToken() {
    let csrfToken = window.getCsrfToken();
    if (csrfToken) return csrfToken;
    
    try {
        const response = await fetch('/api/auth/csrf/', {
            method: 'GET',
            credentials: 'include'
        });
        if (response.ok) {
            csrfToken = window.getCsrfToken();
        }
    } catch (error) {
        console.error('获取CSRF Token失败:', error);
    }
    return csrfToken;
}

// 表单提交处理
document.getElementById('reset-password-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const token = getUrlParameter('token');
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    // 验证token
    if (!token) {
        showMessage('重置链接无效，请重新申请密码重置');
        return;
    }
    
    // 验证密码
    if (newPassword.length < 8) {
        showMessage('密码长度至少为8位');
        return;
    }
    
    if (!checkPasswordMatch()) {
        showMessage('两次输入的密码不匹配');
        return;
    }
    
    // 检查密码强度
    const strengthInfo = checkPasswordStrength(newPassword);
    if (strengthInfo.strength < 3) {
        showMessage('密码强度较弱，建议使用包含大小写字母、数字和特殊字符的组合');
        return;
    }
    
    // 获取CSRF令牌
    const csrfToken = await ensureCsrfToken();
    if (!csrfToken) {
        showMessage('系统错误，无法获取安全令牌，请刷新页面重试');
        return;
    }
    
    // 显示加载状态
    const submitBtn = document.querySelector('.auth-button');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = '处理中...';
    submitBtn.disabled = true;
    
    // 发送重置请求
    try {
        const response = await fetch('/api/auth/reset-password/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'include',
            body: JSON.stringify({
                token: token,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('密码重置成功，请使用新密码登录', 'success');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
            showMessage(data.message || data.error || '密码重置失败，请稍后重试');
        }
    } catch (error) {
        console.error('密码重置请求失败:', error);
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        showMessage('网络错误，请检查网络连接后重试');
    }
});

// 添加事件监听器
document.getElementById('new-password').addEventListener('input', function() {
    updatePasswordStrength();
    checkPasswordMatch();
});

document.getElementById('confirm-password').addEventListener('input', checkPasswordMatch);

// 页面加载时检查token并确保CSRF
document.addEventListener('DOMContentLoaded', async function() {
    const token = getUrlParameter('token');
    if (!token) {
        showMessage('重置链接无效，请重新申请密码重置');
    }
    // 预先获取CSRF Token
    await ensureCsrfToken();
});
