import redis
import logging
from django.conf import settings
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis客户端工具类"""
    
    def __init__(self):
        self.redis_client = None
        # 延迟连接，避免Django启动时设置未完全加载
    
    def _connect(self):
        """连接Redis"""
        try:
            redis_config = {
                'host': getattr(settings, 'REDIS_HOST', 'localhost'),
                'port': getattr(settings, 'REDIS_PORT', 6379),
                'password': getattr(settings, 'REDIS_PASSWORD', None),
                'db': getattr(settings, 'REDIS_DB', 0),
                'decode_responses': True
            }
            
            self.redis_client = redis.Redis(**redis_config)
            # 测试连接
            self.redis_client.ping()
            logger.info("Redis连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        if not self.redis_client:
            self._connect()  # 尝试连接Redis
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def incr_view_count(self, content_type: str, content_id: int) -> Optional[int]:
        """增加浏览量
        
        Args:
            content_type: 内容类型 ('news' 或 'policy')
            content_id: 内容ID
            
        Returns:
            新的浏览量，如果失败返回None
        """
        if not self.is_available():
            return None
            
        try:
            key = f"{content_type}:view_count:{content_id}"
            new_count = self.redis_client.incr(key)
            # 设置过期时间为7天，避免Redis内存无限增长
            self.redis_client.expire(key, 7 * 24 * 3600)
            return new_count
        except Exception as e:
            logger.error(f"Redis增加浏览量失败: {e}")
            return None
    
    def get_view_count(self, content_type: str, content_id: int) -> Optional[int]:
        """获取浏览量
        
        Args:
            content_type: 内容类型 ('news' 或 'policy')
            content_id: 内容ID
            
        Returns:
            浏览量，如果失败返回None
        """
        if not self.is_available():
            return None
            
        try:
            key = f"{content_type}:view_count:{content_id}"
            count = self.redis_client.get(key)
            return int(count) if count else None
        except Exception as e:
            logger.error(f"Redis获取浏览量失败: {e}")
            return None
    
    def get_all_view_counts(self, content_type: str) -> Dict[int, int]:
        """获取所有浏览量数据
        
        Args:
            content_type: 内容类型 ('news' 或 'policy')
            
        Returns:
            {content_id: view_count} 字典
        """
        if not self.is_available():
            return {}
            
        try:
            pattern = f"{content_type}:view_count:*"
            keys = self.redis_client.keys(pattern)
            
            result = {}
            for key in keys:
                # 从key中提取ID
                content_id = int(key.split(':')[-1])
                count = self.redis_client.get(key)
                if count:
                    result[content_id] = int(count)
            
            return result
        except Exception as e:
            logger.error(f"Redis获取所有浏览量失败: {e}")
            return {}
    
    def delete_view_count(self, content_type: str, content_id: int) -> bool:
        """删除浏览量缓存
        
        Args:
            content_type: 内容类型 ('news' 或 'policy')
            content_id: 内容ID
            
        Returns:
            是否删除成功
        """
        if not self.is_available():
            return False
            
        try:
            key = f"{content_type}:view_count:{content_id}"
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis删除浏览量失败: {e}")
            return False
    
    def set_captcha(self, captcha_id: str, captcha_text: str, expire: int = 300) -> bool:
        """存储验证码到Redis
        
        Args:
            captcha_id: 验证码ID
            captcha_text: 验证码文本
            expire: 过期时间（秒），默认5分钟
            
        Returns:
            是否存储成功
        """
        if not self.is_available():
            return False
            
        try:
            key = f"captcha:{captcha_id}"
            self.redis_client.setex(key, expire, captcha_text)
            return True
        except Exception as e:
            logger.error(f"Redis存储验证码失败: {e}")
            return False
    
    def get_captcha(self, captcha_id: str) -> Optional[str]:
        """从Redis获取验证码
        
        Args:
            captcha_id: 验证码ID
            
        Returns:
            验证码文本，如果不存在返回None
        """
        if not self.is_available():
            return None
            
        try:
            key = f"captcha:{captcha_id}"
            return self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Redis获取验证码失败: {e}")
            return None
    
    def delete_captcha(self, captcha_id: str) -> bool:
        """删除Redis中的验证码
        
        Args:
            captcha_id: 验证码ID
            
        Returns:
            是否删除成功
        """
        if not self.is_available():
            return False
            
        try:
            key = f"captcha:{captcha_id}"
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis删除验证码失败: {e}")
            return False
    
    def incr_login_attempts(self, email: str, ip_address: str = '') -> Optional[int]:
        """增加登录尝试次数
        
        Args:
            email: 用户邮箱
            ip_address: 用户IP地址
            
        Returns:
            新的尝试次数，如果失败返回None
        """
        if not self.is_available():
            return None
            
        try:
            # 按邮箱和IP地址分别记录
            key_email = f"login_attempts:email:{email}"
            key_ip = f"login_attempts:ip:{ip_address}"
            
            # 增加邮箱尝试次数
            new_count_email = self.redis_client.incr(key_email)
            self.redis_client.expire(key_email, 3600)  # 1小时过期
            
            # 增加IP尝试次数
            new_count_ip = self.redis_client.incr(key_ip)
            self.redis_client.expire(key_ip, 3600)  # 1小时过期
            
            return max(new_count_email, new_count_ip)
        except Exception as e:
            logger.error(f"Redis增加登录尝试次数失败: {e}")
            return None
    
    def get_login_attempts(self, email: str, ip_address: str = '') -> Optional[int]:
        """获取登录尝试次数
        
        Args:
            email: 用户邮箱
            ip_address: 用户IP地址
            
        Returns:
            尝试次数，如果不存在返回0
        """
        if not self.is_available():
            return 0
            
        try:
            # 同时检查邮箱和IP地址的尝试次数
            key_email = f"login_attempts:email:{email}"
            key_ip = f"login_attempts:ip:{ip_address}"
            
            count_email = self.redis_client.get(key_email)
            count_email = int(count_email) if count_email else 0
            
            count_ip = self.redis_client.get(key_ip)
            count_ip = int(count_ip) if count_ip else 0
            
            return max(count_email, count_ip)
        except Exception as e:
            logger.error(f"Redis获取登录尝试次数失败: {e}")
            return 0
    
    def reset_login_attempts(self, email: str, ip_address: str = '') -> bool:
        """重置登录尝试次数
        
        Args:
            email: 用户邮箱
            ip_address: 用户IP地址
            
        Returns:
            是否重置成功
        """
        if not self.is_available():
            return False
            
        try:
            # 同时重置邮箱和IP地址的尝试次数
            keys = [
                f"login_attempts:email:{email}",
                f"login_attempts:ip:{ip_address}"
            ]
            self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Redis重置登录尝试次数失败: {e}")
            return False
    
    def is_login_locked(self, email: str, ip_address: str = '') -> Dict[str, Any]:
        """检查是否被登录锁定
        
        Args:
            email: 用户邮箱
            ip_address: 用户IP地址
            
        Returns:
            锁定状态字典，包含locked和remaining_minutes字段
        """
        if not self.is_available():
            return {'locked': False, 'remaining_minutes': 0}
            
        try:
            # 检查邮箱锁定
            lock_key_email = f"login_lockout:email:{email}"
            lock_time_email = self.redis_client.get(lock_key_email)
            
            # 检查IP锁定
            lock_key_ip = f"login_lockout:ip:{ip_address}"
            lock_time_ip = self.redis_client.get(lock_key_ip)
            
            # 检查是否有任何锁定
            lock_time = lock_time_email or lock_time_ip
            if not lock_time:
                # 检查尝试次数
                attempts = self.get_login_attempts(email, ip_address)
                if attempts >= 5:
                    # 锁定账户
                    self.redis_client.setex(lock_key_email, 900, str(datetime.now().timestamp()))  # 15分钟锁定
                    self.redis_client.setex(lock_key_ip, 900, str(datetime.now().timestamp()))  # 15分钟锁定
                    return {'locked': True, 'remaining_minutes': 15}
                return {'locked': False, 'remaining_minutes': 0}
            
            # 计算剩余锁定时间
            lock_time = float(lock_time)
            current_time = datetime.now().timestamp()
            remaining_seconds = 900 - (current_time - lock_time)
            
            if remaining_seconds > 0:
                return {
                    'locked': True,
                    'remaining_minutes': int(remaining_seconds / 60)
                }
            else:
                # 锁定时间已过，清除锁定
                self.redis_client.delete(lock_key_email, lock_key_ip)
                return {'locked': False, 'remaining_minutes': 0}
        except Exception as e:
            logger.error(f"Redis检查登录锁定状态失败: {e}")
            return {'locked': False, 'remaining_minutes': 0}
    
    def check_rate_limit(self, endpoint: str, ip_address: str, max_requests: int, window_seconds: int) -> Dict[str, Any]:
        """检查API请求速率限制
        
        Args:
            endpoint: API端点名称
            ip_address: 请求IP地址
            max_requests: 窗口内最大请求数
            window_seconds: 时间窗口（秒）
            
        Returns:
            速率限制状态字典，包含allowed和remaining字段
        """
        if not self.is_available():
            return {'allowed': True, 'remaining': max_requests}
            
        try:
            key = f"rate_limit:{endpoint}:{ip_address}"
            
            current = self.redis_client.get(key)
            if current:
                current = int(current)
                if current >= max_requests:
                    return {
                        'allowed': False,
                        'remaining': 0
                    }
                else:
                    self.redis_client.incr(key)
                    return {
                        'allowed': True,
                        'remaining': max_requests - current - 1
                    }
            else:
                self.redis_client.setex(key, window_seconds, 1)
                return {
                    'allowed': True,
                    'remaining': max_requests - 1
                }
        except Exception as e:
            logger.error(f"Redis检查速率限制失败: {e}")
            return {'allowed': True, 'remaining': max_requests}

# 全局Redis客户端实例
redis_client = RedisClient()