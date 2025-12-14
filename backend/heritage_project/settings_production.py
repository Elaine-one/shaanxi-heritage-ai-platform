# 生产环境配置文件
import os
from .settings import *

# 生产环境安全设置
DEBUG = False

# 生产环境允许的主机 - 请根据实际域名修改
ALLOWED_HOSTS = [
    'your-domain.com',  # 替换为您的实际域名
    'www.your-domain.com',  # 替换为您的实际域名
    'localhost',  # 保留用于本地测试
    '127.0.0.1',  # 保留用于本地测试
]

# 生产环境密钥 - 请使用环境变量或生成新的密钥
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', SECRET_KEY)

# 数据库配置 - 建议使用环境变量
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'heritage_db'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        }
    }
}

# 生产环境CORS设置
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'https://your-domain.com',  # 替换为您的实际域名
    'https://www.your-domain.com',  # 替换为您的实际域名
]

# CSRF信任的来源
CSRF_TRUSTED_ORIGINS = [
    'https://your-domain.com',  # 替换为您的实际域名
    'https://www.your-domain.com',  # 替换为您的实际域名
]

# 静态文件配置
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# 静态文件收集目录
STATICFILES_DIRS = [
    BASE_DIR.parent / 'frontend',
    BASE_DIR / 'static',
]

# 媒体文件配置
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# 安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS设置（如果使用HTTPS）
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# 创建日志目录
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# 百度地图API配置 - 使用环境变量
BAIDU_MAP_AK = os.environ.get('BAIDU_MAP_AK', '')