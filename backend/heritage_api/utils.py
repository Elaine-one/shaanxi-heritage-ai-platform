"""
通用工具函数模块
"""
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def format_datetime(dt, format_str='%Y-%m-%d %H:%M'):
    """
    统一的日期时间格式化方法
    
    Args:
        dt: datetime对象
        format_str: 格式化字符串，默认 '%Y-%m-%d %H:%M'
    
    Returns:
        格式化后的日期时间字符串，如果dt为None则返回None
    """
    return dt.strftime(format_str) if dt else None


def handle_redis_operation(operation_name, fallback_func, *args, **kwargs):
    """
    统一处理Redis操作的错误处理
    
    Args:
        operation_name: 操作名称，用于日志记录
        fallback_func: 降级处理函数
        *args, **kwargs: 传递给操作的参数
    
    Returns:
        操作结果或降级处理结果
    """
    try:
        # 这里可以添加实际的Redis操作逻辑
        # 目前只是一个框架，需要根据实际情况实现
        logger.debug(f"执行 {operation_name} 操作")
        # 实际的操作逻辑应该在这里
        pass
    except Exception as e:
        logger.error(f"{operation_name} 操作失败: {e}")
        if fallback_func:
            return fallback_func(*args, **kwargs)
        return None


def get_client_ip(request):
    """
    获取客户端IP地址
    
    Args:
        request: Django请求对象
    
    Returns:
        客户端IP地址字符串
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def validate_file_size(file, max_size_mb=10):
    """
    验证文件大小
    
    Args:
        file: 文件对象
        max_size_mb: 最大文件大小（MB）
    
    Returns:
        (is_valid, error_message) 元组
    """
    if file.size > max_size_mb * 1024 * 1024:
        return False, f"文件大小不能超过 {max_size_mb}MB"
    return True, None


def sanitize_html_content(content):
    """
    清理HTML内容，移除危险标签和属性
    
    Args:
        content: HTML内容字符串
    
    Returns:
        清理后的HTML内容
    """
    # 这里可以集成bleach等HTML清理库
    # 目前只是一个简单的实现
    if not content:
        return content
    
    # 移除script标签
    import re
    content = re.sub(r'<script.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # 移除事件处理器属性
    content = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
    
    return content


def handle_view_count_increase(instance, content_type='generic'):
    """
    统一处理浏览量增加的通用函数
    
    Args:
        instance: 模型实例（如News, Policy等）
        content_type: 内容类型，用于Redis键名区分（如'news', 'policy'）
    
    Returns:
        更新后的浏览量数值
    """
    try:
        from .redis_utils import redis_client
        redis_client.incr_view_count(content_type, instance.id)
        logger.debug(f"{content_type} {instance.id} 浏览量已通过Redis增加")
        
        # 获取当前浏览量（优先从Redis读取）
        current_view_count = redis_client.get_view_count(content_type, instance.id)
        if current_view_count is not None:
            # 临时设置实例的浏览量为Redis中的值（不保存到数据库）
            instance.view_count = current_view_count
            return current_view_count
            
    except Exception as e:
        logger.error(f"Redis增加浏览量失败: {e}，降级到数据库直接更新")
        # 降级到直接数据库更新
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
    return instance.view_count


def generate_captcha(length=4, width=390, height=45):
    """
    生成图形验证码
    
    Args:
        length: 验证码字符长度，默认4位
        width: 验证码图片宽度，默认390px
        height: 验证码图片高度，默认60px
    
    Returns:
        tuple: (验证码文本, 验证码图片字节流)
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import random
        import string
        from io import BytesIO
        
        # 生成随机验证码文本
        chars = string.ascii_uppercase + string.digits  # 只使用大写字母和数字
        captcha_text = ''.join(random.choice(chars) for _ in range(length))
        
        # 创建图片对象
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # 增加干扰元素
        # 添加大量干扰点
        for _ in range(150):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            draw.point((x, y), fill=(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
        
        # 添加更多干扰线
        for _ in range(5):
            x1 = random.randint(0, width - 1)
            y1 = random.randint(0, height - 1)
            x2 = random.randint(0, width - 1)
            y2 = random.randint(0, height - 1)
            draw.line((x1, y1, x2, y2), fill=(random.randint(100, 180), random.randint(100, 180), random.randint(100, 180)), width=2)
        
        # 添加噪点块
        for _ in range(10):
            x = random.randint(0, width - 20)
            y = random.randint(0, height - 20)
            # 使用半透明颜色值代替fill-opacity参数
            # RGBA颜色值，最后一位是透明度（0-255）
            fill_color = (random.randint(80, 180), random.randint(80, 180), random.randint(80, 180), random.randint(50, 120))
            draw.rectangle(
                [(x, y), (x + random.randint(5, 20), y + random.randint(5, 20))],
                fill=fill_color,
                outline=None
            )
        
        # 尝试使用系统字体，缩小字体大小
        font = None
        font_size = 32  # 缩小字体大小
        
        # 尝试使用Windows系统字体
        try:
            import os
            windows_fonts = [
                r'C:\Windows\Fonts\arial.ttf',
                r'C:\Windows\Fonts\cour.ttf',  # Courier字体
            ]
            
            for font_path in windows_fonts:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
        except Exception:
            pass
        
        # 如果找不到系统字体，使用PIL的默认字体
        if not font:
            font = ImageFont.load_default()
        
        # 计算文本位置，居中显示
        try:
            text_bbox = draw.textbbox((0, 0), captcha_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # 确保文本居中，并有足够的边距
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # 绘制文本，使用随机深色
            draw.text((x, y), captcha_text, font=font, fill=(random.randint(0, 80), random.randint(0, 80), random.randint(0, 80)))
        except Exception:
            # 如果文本绘制失败，使用逐个字符绘制的方式，增加随机性
            char_width = width // (length + 1)
            for i, char in enumerate(captcha_text):
                # 随机位置，增加扭曲效果
                x = i * char_width + random.randint(5, 15)
                y = random.randint(5, height // 3)
                draw.text((x, y), char, font=font, fill=(random.randint(0, 80), random.randint(0, 80), random.randint(0, 80)))
        
        # 将图片转换为字节流
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return captcha_text, buffer
    except Exception as e:
        logger.error(f"生成验证码失败: {e}")
        return None, None