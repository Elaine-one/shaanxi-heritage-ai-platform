from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse
import re
from datetime import datetime, timedelta
import logging
import base64
from io import BytesIO

from heritage_api.utils import generate_captcha
from heritage_api.redis_utils import redis_client

logger = logging.getLogger(__name__)

def validate_password_strength(password):
    """验证密码强度"""
    if len(password) < 8:
        raise ValidationError("密码长度至少8位")
    
    if len(password) > 128:
        raise ValidationError("密码长度不能超过128位")
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError("密码必须包含至少一个大写字母")
    
    if not re.search(r'[a-z]', password):
        raise ValidationError("密码必须包含至少一个小写字母")
    
    if not re.search(r'\d', password):
        raise ValidationError("密码必须包含至少一个数字")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError("密码必须包含至少一个特殊字符")
    
    # 检查是否包含空格
    if ' ' in password:
        raise ValidationError("密码不能包含空格")

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """
    注册新用户 - 邮箱注册版
    """
    # 检查注册请求速率限制 (10次/分钟)
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    rate_limit_status = redis_client.check_rate_limit('register', ip_address, 10, 60)
    if not rate_limit_status['allowed']:
        return Response(
            {'message': '请求过于频繁，请稍后再试'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    email = request.data.get('email')
    password = request.data.get('password')
    captcha_key = request.data.get('captcha_key')
    captcha_value = request.data.get('captcha_value')
    
    # 验证数据
    if not email or not password or not captcha_key or not captcha_value:
        return Response({'message': '请提供邮箱、密码和验证码'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 验证邮箱格式和长度
    # 更严格的邮箱格式验证，确保包含有效域名
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return Response({'message': '邮箱格式不正确，请输入有效的邮箱地址'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 更严格的长度限制
    if len(email) > 254:
        return Response({'message': '邮箱长度不能超过254位'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(email) < 8:
        return Response({'message': '邮箱长度不能少于8位，请输入有效的邮箱地址'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 检查@符号位置，确保用户名和域名都有足够长度
    at_index = email.find('@')
    
    # 更严格的用户名部分限制
    username_part = email[:at_index]
    domain_part = email[at_index+1:]
    
    # 用户名部分验证：
    # - 如果是纯数字：至少8位
    # - 如果包含字母或其他字符：至少3位
    if username_part.isdigit():
        # 纯数字用户名至少8位
        if len(username_part) < 8:
            return Response({'message': '邮箱用户名部分如果是纯数字，不能少于8位字符，请输入有效的邮箱地址'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        # 包含字母的用户名至少3位
        if len(username_part) < 3:
            return Response({'message': '邮箱用户名部分不能少于3个字符，请输入有效的邮箱地址'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 域名部分至少4个字符，确保包含有效的二级域名和顶级域名
    if len(domain_part) < 4:
        return Response({'message': '邮箱域名部分格式不正确，请输入有效的邮箱地址'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 检查域名是否包含有效后缀
    if '.' not in domain_part or len(domain_part.split('.')[-1]) < 2:
        return Response({'message': '邮箱格式不正确，请输入有效的邮箱地址'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 验证验证码
    correct_captcha = redis_client.get_captcha(captcha_key)
    if not correct_captcha or captcha_value.lower() != correct_captcha.lower():
        redis_client.delete_captcha(captcha_key)
        return Response({'message': '验证码错误'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 删除已验证的验证码
    redis_client.delete_captcha(captcha_key)
    
    # 检查邮箱是否已存在 - 使用不区分大小写的查询
    if User.objects.filter(email__iexact=email).exists():
        return Response({'message': '邮箱已被注册'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 验证密码强度
    try:
        validate_password_strength(password)
        validate_password(password)
    except ValidationError as e:
        return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # 基于邮箱自动生成用户名
    # 使用邮箱前缀作为用户名基础，确保唯一性
    username_base = email.split('@')[0]
    username = username_base
    counter = 1
    
    # 确保用户名唯一
    while User.objects.filter(username__iexact=username).exists():
        username = f"{username_base}{counter}"
        counter += 1
        
        # 防止无限循环，设置最大尝试次数
        if counter > 100:
            return Response({'message': '无法生成唯一用户名，请稍后重试'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 创建新用户
    try:
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # 记录注册日志
        logger.info(f'用户注册成功: {username} ({email})', extra={
            'user_id': user.id,
            'username': username,
            'email': email,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown')
        })
        
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'message': '注册成功'
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f'用户注册失败: {str(e)}', extra={
            'email': email,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown')
        })
        return Response({'message': f'注册失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def check_login_attempts(username, ip_address):
    """检查登录尝试次数"""
    # 检查是否被锁定
    lock_status = redis_client.is_login_locked(username, ip_address)
    if lock_status['locked']:
        return False, f'登录失败次数过多，请{lock_status["remaining_minutes"]}分钟后再试'
    
    return True, None

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """
    用户登录 - 使用邮箱登录
    """
    # 检查登录请求速率限制 (10次/分钟)
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    rate_limit_status = redis_client.check_rate_limit('login', ip_address, 10, 60)
    if not rate_limit_status['allowed']:
        return Response(
            {'message': '请求过于频繁，请稍后再试'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    email = request.data.get('email')
    password = request.data.get('password')
    remember_me = request.data.get('remember_me', False)
    captcha_key = request.data.get('captcha_key')
    captcha_value = request.data.get('captcha_value')
    
    # 验证数据
    if not email or not password or not captcha_key or not captcha_value:
        return Response({'message': '请提供邮箱、密码和验证码'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 验证验证码
    correct_captcha = redis_client.get_captcha(captcha_key)
    if not correct_captcha or captcha_value.lower() != correct_captcha.lower():
        redis_client.delete_captcha(captcha_key)
        return Response({'message': '验证码错误'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 删除已验证的验证码
    redis_client.delete_captcha(captcha_key)
    
    # 验证邮箱格式和长度
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return Response({'message': '邮箱格式不正确'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(email) > 254:
        return Response({'message': '邮箱长度不能超过254位'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(email) < 5:
        return Response({'message': '邮箱长度不能少于5位'}, status=status.HTTP_400_BAD_REQUEST)
    
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    
    # 检查登录尝试次数
    allowed, error_message = check_login_attempts(email, ip_address)
    if not allowed:
        logger.warning(f'登录尝试被阻止: {email} from {ip_address} - {error_message}')
        return Response({'message': error_message}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    # 通过邮箱查找用户
    try:
        user = User.objects.get(email__iexact=email)
        
        # 使用用户名进行认证（Django authenticate需要用户名）
        authenticated_user = authenticate(username=user.username, password=password)
        
        if authenticated_user is not None:
            if not authenticated_user.is_active:
                logger.warning(f'尝试登录已禁用账户: {email} from {ip_address}')
                return Response({'message': '账户已被禁用'}, status=status.HTTP_403_FORBIDDEN)
            
            login(request, authenticated_user)
            
            # 设置session过期时间
            if remember_me:
                request.session.set_expiry(30 * 24 * 60 * 60)  # 30天
            else:
                request.session.set_expiry(0)  # 浏览器关闭时过期
            
            # 清除登录失败计数
            redis_client.reset_login_attempts(email, ip_address)
            
            # 记录登录日志
            logger.info(f'用户登录成功: {email} from {ip_address}', extra={
                'user_id': user.id,
                'username': user.username,
                'email': email,
                'ip_address': ip_address,
                'remember_me': remember_me
            })
            
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'message': '登录成功'
            })
        else:
            # 增加登录失败计数
            attempts = redis_client.incr_login_attempts(email, ip_address)
            
            # 记录失败日志
            logger.warning(f'登录失败: {email} from {ip_address} - 尝试次数: {attempts}', extra={
                'email': email,
                'ip_address': ip_address,
                'attempts': attempts
            })
            
            return Response({'message': '邮箱或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
            
    except User.DoesNotExist:
        # 用户不存在，也增加失败计数
        attempts = redis_client.incr_login_attempts(email, ip_address)
        
        logger.warning(f'登录失败: 邮箱不存在 {email} from {ip_address} - 尝试次数: {attempts}', extra={
            'email': email,
            'ip_address': ip_address,
            'attempts': attempts
        })
        
        return Response({'message': '邮箱或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """
    用户登出
    """
    logout(request)
    return Response({'message': '已成功登出'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """
    获取当前登录用户信息
    """
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    请求密码重置
    """
    # 检查密码重置请求速率限制 (5次/小时)
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    rate_limit_status = redis_client.check_rate_limit('password_reset', ip_address, 5, 3600)
    if not rate_limit_status['allowed']:
        return Response(
            {'message': '请求过于频繁，请稍后再试'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    email = request.data.get('email')
    
    if not email:
        return Response({'message': '请提供邮箱地址'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email__iexact=email)
        
        # 生成重置令牌
        reset_token = get_random_string(32)
        reset_key = f'password_reset:{reset_token}'
        
        # 存储重置信息（15分钟有效）
        cache.set(reset_key, {
            'user_id': user.id,
            'email': user.email,
            'timestamp': datetime.now().timestamp()
        }, 900)
        
        # 发送密码重置邮件
        try:
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:8000')
            reset_url = f'{frontend_url}/pages/reset-password.html?token={reset_token}'
            
            send_mail(
                '陕西非物质文化遗产保护平台 - 密码重置请求',
                f'''
尊敬的 {user.username}：

您收到了此邮件是因为您（或其他人）请求重置您在陕西非物质文化遗产保护平台的账户密码。

请点击以下链接重置密码：
{reset_url}

此链接将在15分钟后失效。

如果您没有请求重置密码，请忽略此邮件，您的密码将保持不变。

感谢您使用我们的平台！

陕西非物质文化遗产保护平台团队
                ''',
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@heritage-platform.com'),
                [user.email],
                fail_silently=False,
            )
            
            logger.info(f'密码重置邮件已发送: {user.email}')
            
        except Exception as e:
            logger.error(f'发送密码重置邮件失败: {str(e)}')
            # 开发环境下仍然返回调试令牌
            return Response({
                'message': '邮件发送失败，请检查邮箱配置',
                'debug_token': reset_token  # 仅开发环境使用
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        logger.info(f'密码重置请求: {user.email}', extra={
            'user_id': user.id,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown')
        })
        
        return Response({
            'message': '密码重置链接已发送到您的邮箱（开发环境中请查看控制台日志）',
            'debug_token': reset_token  # 仅开发环境使用
        })
        
    except User.DoesNotExist:
        # 出于安全考虑，不透露邮箱是否存在
        return Response({'message': '如果邮箱存在，重置链接将发送到您的邮箱'})

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    重置密码
    """
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    if not token or not new_password:
        return Response({'message': '请提供重置令牌和新密码'}, status=status.HTTP_400_BAD_REQUEST)
    
    reset_key = f'password_reset:{token}'
    reset_data = cache.get(reset_key)
    
    if not reset_data:
        return Response({'message': '重置令牌无效或已过期'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=reset_data['user_id'])
        
        # 验证密码强度
        try:
            validate_password_strength(new_password)
            validate_password(new_password)
        except ValidationError as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # 设置新密码
        user.set_password(new_password)
        user.save()
        
        # 删除重置令牌
        cache.delete(reset_key)
        
        # 记录密码重置日志
        logger.info(f'密码重置成功: {user.username}', extra={
            'user_id': user.id,
            'ip_address': request.META.get('REMOTE_ADDR', 'unknown')
        })
        
        return Response({'message': '密码重置成功'})
        
    except User.DoesNotExist:
        return Response({'message': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_security_status(request):
    """
    获取账户安全状态
    """
    user = request.user
    
    # 检查最近登录活动
    recent_logins = []  # 这里可以添加最近登录记录查询
    
    # 检查密码强度
    password_strength = '未知'
    
    return Response({
        'username': user.username,
        'email': user.email,
        'last_login': user.last_login.isoformat() if user.last_login else None,
        'date_joined': user.date_joined.isoformat(),
        'is_active': user.is_active,
        'password_strength': password_strength,
        'recent_logins': recent_logins
    })

@api_view(['GET'])
@ensure_csrf_cookie
@permission_classes([AllowAny])
def get_csrf_token(request):
    """
    获取CSRF令牌
    """
    from django.middleware.csrf import get_token
    # 强制生成并设置CSRF token
    csrf_token = get_token(request)
    return Response({
        'csrfToken': csrf_token,
        'message': 'CSRF cookie set'
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def generate_captcha_view(request):
    """
    生成图形验证码
    """
    # 检查验证码生成速率限制 (20次/分钟)
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    rate_limit_status = redis_client.check_rate_limit('captcha', ip_address, 20, 60)
    if not rate_limit_status['allowed']:
        return Response(
            {'message': '请求过于频繁，请稍后再试'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    # 生成验证码图片和验证码文本
    captcha_text, buffer = generate_captcha()
    
    if captcha_text is None or buffer is None:
        return Response({'message': '生成验证码失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # 将验证码存储到Redis，有效期5分钟
    captcha_key = get_random_string(32)
    redis_client.set_captcha(captcha_key, captcha_text)
    
    # 将图片转换为base64格式
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return Response({
        'captcha_key': captcha_key,
        'captcha_image': img_str,
        'message': '验证码生成成功'
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_captcha(request):
    """
    验证图形验证码
    """
    captcha_key = request.data.get('captcha_key')
    user_input = request.data.get('captcha_value')
    
    if not captcha_key or not user_input:
        return Response({
            'message': '验证码参数不完整',
            'valid': False
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 获取正确的验证码
    correct_captcha = redis_client.get_captcha(captcha_key)
    
    if not correct_captcha:
        return Response({
            'message': '验证码已过期或无效',
            'valid': False
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 验证验证码
    is_valid = user_input.lower() == correct_captcha.lower()
    
    # 无论验证成功与否，都删除验证码
    redis_client.delete_captcha(captcha_key)
    
    if is_valid:
        return Response({
            'message': '验证码验证成功',
            'valid': True
        })
    else:
        return Response({
            'message': '验证码错误',
            'valid': False
        }, status=status.HTTP_400_BAD_REQUEST)