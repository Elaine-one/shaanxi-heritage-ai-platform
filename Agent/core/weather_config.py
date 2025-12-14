# 天气服务配置文件

# 网络配置
NETWORK_TIMEOUT = 10  # 网络请求超时时间(秒)
MAX_RETRIES = 2  # 最大重试次数 - 减少到2次
RETRY_DELAY = 1  # 重试延迟(秒)

# SSL配置
SSL_VERIFY = True  # 是否启用SSL验证

# 缓存配置
CACHE_ENABLED = True  # 是否启用缓存
CACHE_TTL = 3600  # 缓存有效期(秒) - 1小时
CACHE_MAX_SIZE = 100  # 最大缓存项数量

# 环境特定配置
ENVIRONMENT_CONFIG = {
    'development': {
        'SSL_VERIFY': False,  # 开发环境禁用SSL验证
        'MAX_RETRIES': 2,  # 开发环境减少重试次数
    },
    'production': {
        'SSL_VERIFY': True,  # 生产环境启用SSL验证
        'MAX_RETRIES': 2,  # 生产环境减少重试次数
    },
    'ubuntu': {
        'SSL_VERIFY': False,  # Ubuntu服务器环境可能需要禁用SSL验证
        'MAX_RETRIES': 2,  # 减少重试次数
        'RETRY_DELAY': 2,  # 增加重试延迟
    },
    'docker': {
        'SSL_VERIFY': False,  # Docker环境可能需要禁用SSL验证
        'MAX_RETRIES': 2,  # 减少重试次数
    }
}