#!/usr/bin/env python
"""
URL加密工具
用于加密Agent服务URL，以便在环境变量中安全存储
"""

import os
import sys
import base64
from pathlib import Path

# 添加项目路径到系统路径
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 导入加密工具
from heritage_api.encryption_utils import encrypt_agent_url


def encrypt_url_tool():
    """加密URL的交互式工具"""
    print("=" * 50)
    print("Agent服务URL加密工具")
    print("=" * 50)
    
    # 获取用户输入的URL
    url = input("请输入要加密的Agent服务URL: ").strip()
    
    if not url:
        print("错误: URL不能为空")
        return
    
    # 验证URL格式
    if not url.startswith(('http://', 'https://')):
        print("警告: URL应该以http://或https://开头")
        confirm = input("是否继续? (y/n): ").strip().lower()
        if confirm != 'y':
            return
    
    # 加密URL
    encrypted_url = encrypt_agent_url(url)
    
    print("\n" + "=" * 50)
    print("加密结果:")
    print("=" * 50)
    print(f"原始URL: {url}")
    print(f"加密后:  {encrypted_url}")
    print("\n请将以下行添加到.env文件中:")
    print(f"AGENT_SERVICE_URL={encrypted_url}")
    print("=" * 50)


if __name__ == "__main__":
    encrypt_url_tool()