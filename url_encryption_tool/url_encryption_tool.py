"""
URL加密解密工具
提供可视化界面，用于安全地加密和解密URL地址
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import base64
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

# 尝试导入pyperclip，如果失败则使用tkinter的剪贴板功能
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


class EncryptionUtils:
    """加密工具类"""
    
    def __init__(self, secret_key="default_secret_key_change_in_production"):
        """初始化加密工具"""
        # 使用提供的密钥或默认密钥
        self.encryption_key = self._get_or_create_key(secret_key)
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_key(self, secret_key):
        """获取或创建加密密钥"""
        # 使用提供的密钥派生一个加密密钥
        django_secret = secret_key.encode()
        # 使用与Django项目相同的盐值，确保加密结果一致
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


class URLEncryptionApp:
    """URL加密解密应用程序"""
    
    def __init__(self, root):
        """初始化应用程序"""
        self.root = root
        self.root.title("URL加密解密工具")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 设置应用图标和样式
        self.setup_styles()
        
        # 创建加密工具实例
        self.encryption_utils = EncryptionUtils()
        
        # 创建UI组件
        self.create_widgets()
        
        # 设置焦点到输入框
        self.input_text.focus_set()
        
        # 显示剪贴板支持状态
        if not CLIPBOARD_AVAILABLE:
            self.status_var.set("就绪 - 剪贴板功能不可用，请安装pyperclip库")
        else:
            self.status_var.set("就绪")
    
    def setup_styles(self):
        """设置应用样式"""
        # 设置主题
        style = ttk.Style()
        style.theme_use('clam')
        
        # 设置颜色主题
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        style.configure('TEntry', font=('Arial', 10))
        
        # 设置主窗口背景色
        self.root.configure(bg='#f0f0f0')
    
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="URL加密解密工具", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 输入区域
        input_label = ttk.Label(main_frame, text="输入URL:")
        input_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        self.input_text = scrolledtext.ScrolledText(main_frame, height=5, width=70, wrap=tk.WORD)
        self.input_text.grid(row=2, column=0, columnspan=3, pady=(0, 10), sticky=tk.EW)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)
        
        encrypt_button = ttk.Button(button_frame, text="加密", command=self.encrypt_url)
        encrypt_button.pack(side=tk.LEFT, padx=(0, 10))
        
        decrypt_button = ttk.Button(button_frame, text="解密", command=self.decrypt_url)
        decrypt_button.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_button = ttk.Button(button_frame, text="清空", command=self.clear_all)
        clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        if CLIPBOARD_AVAILABLE:
            paste_button = ttk.Button(button_frame, text="粘贴", command=self.paste_from_clipboard)
            paste_button.pack(side=tk.LEFT)
        
        # 输出区域
        output_label = ttk.Label(main_frame, text="结果:")
        output_label.grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        
        self.output_text = scrolledtext.ScrolledText(main_frame, height=5, width=70, wrap=tk.WORD)
        self.output_text.grid(row=5, column=0, columnspan=3, pady=(0, 10), sticky=tk.EW)
        
        # 复制按钮
        if CLIPBOARD_AVAILABLE:
            copy_button = ttk.Button(main_frame, text="复制结果", command=self.copy_to_clipboard)
            copy_button.grid(row=6, column=0, columnspan=3, pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(5, weight=1)
    
    def encrypt_url(self):
        """加密URL"""
        input_text = self.input_text.get("1.0", tk.END).strip()
        
        if not input_text:
            messagebox.showwarning("警告", "请输入要加密的URL")
            return
        
        try:
            encrypted_url = self.encryption_utils.encrypt_url(input_text)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, encrypted_url)
            self.status_var.set("加密成功")
        except Exception as e:
            messagebox.showerror("错误", f"加密失败: {str(e)}")
            self.status_var.set("加密失败")
    
    def decrypt_url(self):
        """解密URL"""
        input_text = self.input_text.get("1.0", tk.END).strip()
        
        if not input_text:
            messagebox.showwarning("警告", "请输入要解密的URL")
            return
        
        try:
            decrypted_url = self.encryption_utils.decrypt_url(input_text)
            
            if not decrypted_url:
                messagebox.showerror("错误", "解密失败，请检查输入是否为有效的加密URL")
                self.status_var.set("解密失败")
                return
            
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, decrypted_url)
            self.status_var.set("解密成功")
        except Exception as e:
            messagebox.showerror("错误", f"解密失败: {str(e)}")
            self.status_var.set("解密失败")
    
    def clear_all(self):
        """清空所有文本框"""
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.status_var.set("已清空")
        self.input_text.focus_set()
    
    def copy_to_clipboard(self):
        """复制结果到剪贴板"""
        output_text = self.output_text.get("1.0", tk.END).strip()
        
        if not output_text:
            messagebox.showwarning("警告", "没有可复制的内容")
            return
        
        try:
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(output_text)
                self.status_var.set("已复制到剪贴板")
            else:
                # 使用tkinter的剪贴板
                self.root.clipboard_clear()
                self.root.clipboard_append(output_text)
                self.status_var.set("已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {str(e)}")
            self.status_var.set("复制失败")
    
    def paste_from_clipboard(self):
        """从剪贴板粘贴内容"""
        try:
            if CLIPBOARD_AVAILABLE:
                clipboard_content = pyperclip.paste()
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert(tk.END, clipboard_content)
                self.status_var.set("已从剪贴板粘贴")
            else:
                # 使用tkinter的剪贴板
                clipboard_content = self.root.clipboard_get()
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert(tk.END, clipboard_content)
                self.status_var.set("已从剪贴板粘贴")
        except Exception as e:
            messagebox.showwarning("警告", "无法访问剪贴板")


def main():
    """主函数"""
    root = tk.Tk()
    app = URLEncryptionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()