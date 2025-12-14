"""
加密工具模块
用于加密和解密敏感信息，如IP地址等
"""

import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import django.conf


class EncryptionUtils:
    """加密工具类"""
    
    def __init__(self):
        """初始化加密工具"""
        # 从Django设置中获取密钥，如果没有则使用默认密钥
        self.encryption_key = self._get_or_create_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_key(self):
        """获取或创建加密密钥"""
        # 尝试从环境变量获取密钥
        key = os.environ.get('ENCRYPTION_KEY')
        
        if key:
            # 如果环境变量中有密钥，使用它
            return base64.urlsafe_b64decode(key.encode())
        else:
            # 如果没有，使用Django的SECRET_KEY派生一个密钥
            # 这样确保每个项目有唯一的密钥
            django_secret = django.conf.settings.SECRET_KEY.encode()
            salt = b'heritage_project_salt'  # 固定盐值，确保密钥一致性
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(django_secret))
            return key
    
    def encrypt_url(self, url):
        """
        加密URL
        
        Args:
            url (str): 要加密的URL
            
        Returns:
            str: 加密后的URL（Base64编码）
        """
        if not url:
            return ""
        
        # 将URL转换为字节
        url_bytes = url.encode('utf-8')
        
        # 加密
        encrypted_bytes = self.cipher_suite.encrypt(url_bytes)
        
        # 转换为Base64字符串，便于传输和存储
        encrypted_str = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        
        return encrypted_str
    
    def decrypt_url(self, encrypted_url):
        """
        解密URL
        
        Args:
            encrypted_url (str): 加密的URL（Base64编码）
            
        Returns:
            str: 解密后的原始URL
        """
        if not encrypted_url:
            return ""
        
        try:
            # 从Base64字符串转换为字节
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_url.encode('utf-8'))
            
            # 解密
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            
            # 转换回字符串
            url = decrypted_bytes.decode('utf-8')
            
            return url
        except Exception as e:
            print(f"解密URL失败: {e}")
            return ""


# 创建全局实例
encryption_utils = EncryptionUtils()


def encrypt_agent_url(url):
    """
    加密Agent服务URL的便捷函数
    
    Args:
        url (str): Agent服务URL
        
    Returns:
        str: 加密后的URL
    """
    return encryption_utils.encrypt_url(url)


def decrypt_agent_url(encrypted_url):
    """
    解密Agent服务URL的便捷函数
    
    Args:
        encrypted_url (str): 加密的Agent服务URL
        
    Returns:
        str: 解密后的原始URL
    """
    return encryption_utils.decrypt_url(encrypted_url)