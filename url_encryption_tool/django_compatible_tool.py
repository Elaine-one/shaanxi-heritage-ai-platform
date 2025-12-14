"""
Django兼容版URL加密解密工具
提供可视化界面，用于安全地加密和解密URL地址
与Django项目的encryption_utils模块兼容
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import sys

# 添加Django项目路径到系统路径
django_project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if django_project_path not in sys.path:
    sys.path.append(django_project_path)

# 尝试导入Django和项目的加密工具
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heritage_project.settings')
    import django
    django.setup()
    
    # 导入Django项目的加密工具
    from heritage_api.encryption_utils import encrypt_agent_url, decrypt_agent_url
    DJANGO_AVAILABLE = True
except ImportError as e:
    print(f"无法导入Django模块: {e}")
    DJANGO_AVAILABLE = False
    # 定义备用函数
    def encrypt_agent_url(url):
        return "Django不可用，无法加密"
    
    def decrypt_agent_url(encrypted_url):
        return "Django不可用，无法解密"
except Exception as e:
    print(f"初始化Django时出错: {e}")
    DJANGO_AVAILABLE = False
    # 定义备用函数
    def encrypt_agent_url(url):
        return "Django初始化失败，无法加密"
    
    def decrypt_agent_url(encrypted_url):
        return "Django初始化失败，无法解密"

# 尝试导入pyperclip，如果失败则使用tkinter的剪贴板功能
try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


class DjangoURLEncryptionApp:
    """Django兼容版URL加密解密应用程序"""
    
    def __init__(self, root):
        """初始化应用程序"""
        self.root = root
        self.root.title("Django兼容版 - URL加密解密工具")
        self.root.geometry("650x550")
        self.root.resizable(True, True)
        
        # 设置应用图标和样式
        self.setup_styles()
        
        # 创建UI组件
        self.create_widgets()
        
        # 设置焦点到输入框
        self.input_text.focus_set()
        
        # 显示状态信息
        if DJANGO_AVAILABLE:
            if CLIPBOARD_AVAILABLE:
                self.status_var.set("就绪 - Django兼容模式，剪贴板功能可用")
            else:
                self.status_var.set("就绪 - Django兼容模式，剪贴板功能不可用，请安装pyperclip库")
        else:
            self.status_var.set("警告 - Django不可用，使用备用功能")
    
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
        title_label = ttk.Label(main_frame, text="Django兼容版 - URL加密解密工具", font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Django状态标签
        django_status = "可用" if DJANGO_AVAILABLE else "不可用"
        django_status_color = "green" if DJANGO_AVAILABLE else "red"
        django_status_label = tk.Label(main_frame, text=f"Django状态: {django_status}", 
                                     fg=django_status_color, font=('Arial', 10, 'bold'))
        django_status_label.grid(row=1, column=0, columnspan=3, pady=(0, 10))
        
        # 输入区域
        input_label = ttk.Label(main_frame, text="输入URL:")
        input_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.input_text = scrolledtext.ScrolledText(main_frame, height=5, width=70, wrap=tk.WORD)
        self.input_text.grid(row=3, column=0, columnspan=3, pady=(0, 10), sticky=tk.EW)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
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
        output_label.grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        
        self.output_text = scrolledtext.ScrolledText(main_frame, height=5, width=70, wrap=tk.WORD)
        self.output_text.grid(row=6, column=0, columnspan=3, pady=(0, 10), sticky=tk.EW)
        
        # 复制按钮区域
        copy_frame = ttk.Frame(main_frame)
        copy_frame.grid(row=7, column=0, columnspan=3, pady=5)
        
        if CLIPBOARD_AVAILABLE:
            copy_button = ttk.Button(copy_frame, text="复制结果", command=self.copy_to_clipboard)
            copy_button.pack(side=tk.LEFT, padx=(0, 10))
        
        if DJANGO_AVAILABLE:
            env_button = ttk.Button(copy_frame, text="复制为环境变量格式", command=self.copy_as_env_format)
            env_button.pack(side=tk.LEFT)
        
        # 状态栏
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(6, weight=1)
    
    def encrypt_url(self):
        """加密URL"""
        input_text = self.input_text.get("1.0", tk.END).strip()
        
        if not input_text:
            messagebox.showwarning("警告", "请输入要加密的URL")
            return
        
        try:
            encrypted_url = encrypt_agent_url(input_text)
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
            decrypted_url = decrypt_agent_url(input_text)
            
            if not decrypted_url or decrypted_url.startswith("Django"):
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
    
    def copy_as_env_format(self):
        """复制结果为环境变量格式"""
        output_text = self.output_text.get("1.0", tk.END).strip()
        
        if not output_text:
            messagebox.showwarning("警告", "没有可复制的内容")
            return
        
        try:
            env_format = f"AGENT_SERVICE_URL={output_text}"
            
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(env_format)
                self.status_var.set("已复制环境变量格式到剪贴板")
            else:
                # 使用tkinter的剪贴板
                self.root.clipboard_clear()
                self.root.clipboard_append(env_format)
                self.status_var.set("已复制环境变量格式到剪贴板")
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
    app = DjangoURLEncryptionApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()