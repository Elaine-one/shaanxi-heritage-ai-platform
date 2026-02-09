# 生产环境配置文件
import os
from .settings import *

# 生产环境安全设置
DEBUG = False

# 允许的主机列表 - 继承自 settings.py，请通过环境变量 ALLOWED_HOSTS 配置
# ALLOWED_HOSTS = [...]

# 生产环境密钥 - 请使用环境变量或生成新的密钥
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable is not set!")

# 数据库配置 - 继承自 settings.py，请通过环境变量配置
# DATABASES = ...

# 生产环境CORS设置 - 继承自 settings.py，请通过环境变量配置
# CORS_ALLOWED_ORIGINS = ...

# CSRF信任的来源 - 继承自 settings.py，请通过环境变量配置
# CSRF_TRUSTED_ORIGINS = ...

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