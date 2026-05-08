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
    if not content:
        return content

    try:
        import bleach

        allowed_tags = [
            'b', 'i', 'em', 'strong', 'u', 's', 'del', 'ins', 'mark',
            'a', 'p', 'br', 'hr',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li',
            'blockquote', 'pre', 'code',
            'img', 'span', 'div',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'sub', 'sup'
        ]

        allowed_attrs = {
            '*': ['class', 'id'],
            'a': ['href', 'title', 'target', 'rel'],
            'img': ['src', 'alt', 'width', 'height'],
            'td': ['colspan', 'rowspan'],
            'th': ['colspan', 'rowspan'],
        }

        allowed_protocols = ['http', 'https', 'mailto', 'ftp']

        cleaned = bleach.clean(
            content,
            tags=allowed_tags,
            attributes=allowed_attrs,
            protocols=allowed_protocols,
            strip=True,
        )

        return cleaned
    except ImportError:
        return content


def handle_view_count_increase(instance, content_type='generic'):
    """
    统一处理浏览量增加的通用函数

    Args:
        instance: 模型实例（如News, Policy等）
        content_type: 内容类型，用于Redis键名区分

    Returns:
        更新后的浏览量数值
    """
    try:
        from .redis_utils import redis_client
        redis_client.incr_view_count(content_type, instance.id)
        logger.debug(f"{content_type} {instance.id} 浏览量已通过Redis增加")

    except Exception as e:
        logger.error(f"Redis增加浏览量失败: {e}，降级到数据库直接更新")
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
        import os
        
        # 生成随机验证码文本
        chars = string.ascii_uppercase + string.digits
        captcha_text = ''.join(random.choice(chars) for _ in range(length))
        
        # 创建图片对象
        image = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # 增加干扰元素
        for _ in range(150):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            draw.point((x, y), fill=(random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
        
        for _ in range(5):
            x1 = random.randint(0, width - 1)
            y1 = random.randint(0, height - 1)
            x2 = random.randint(0, width - 1)
            y2 = random.randint(0, height - 1)
            draw.line((x1, y1, x2, y2), fill=(random.randint(100, 180), random.randint(100, 180), random.randint(100, 180)), width=2)
        
        for _ in range(10):
            x = random.randint(0, width - 20)
            y = random.randint(0, height - 20)
            fill_color = (random.randint(80, 180), random.randint(80, 180), random.randint(80, 180), random.randint(50, 120))
            draw.rectangle(
                [(x, y), (x + random.randint(5, 20), y + random.randint(5, 20))],
                fill=fill_color,
                outline=None
            )
        
        # 字体设置
        font = None
        font_size = 32
        
        # 优先尝试Windows系统字体
        windows_fonts = [
            r'C:\Windows\Fonts\arial.ttf',
            r'C:\Windows\Fonts\cour.ttf',
        ]
        
        for font_path in windows_fonts:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                break
        
        # 回退到默认字体
        if not font:
            font = ImageFont.load_default()
        
        # 绘制文本
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