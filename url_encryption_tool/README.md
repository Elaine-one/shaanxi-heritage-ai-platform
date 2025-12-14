# URL加密解密工具

一个用于加密和解密URL的工具，提供独立版和Django兼容版两个版本。

## 特点

- 可视化界面，操作简单直观
- 支持URL加密和解密功能
- 支持剪贴板操作（需要安装pyperclip库）
- 提供独立版和Django兼容版两个版本
- Django兼容版可以生成与环境变量兼容的格式

## 文件说明

- `url_encryption_tool.py` - 独立版工具，不依赖Django项目
- `django_compatible_tool.py` - Django兼容版，与Django项目使用相同的密钥
- `run.bat` - 独立版工具启动脚本
- `run_django.bat` - Django兼容版工具启动脚本
- `requirements.txt` - 依赖列表
- `使用指南.md` - 详细使用说明
- `问题解决指南.md` - 常见问题解决方案

## 快速开始

### 安装依赖

工具需要以下Python库：

- `cryptography` - 用于加密解密功能（必需）
- `pyperclip` - 用于剪贴板功能（可选）

打开命令提示符，运行以下命令：

```
pip install cryptography
pip install pyperclip  # 可选，用于剪贴板功能
```

### 启动工具

#### 独立版工具

双击运行 `run.bat` 文件，或直接运行：

```
python url_encryption_tool.py
```

#### Django兼容版工具

双击运行 `run_django.bat` 文件，或直接运行：

```
python django_compatible_tool.py
```

## 使用方法

1. 在输入框中输入要加密或解密的URL
2. 点击相应的按钮：
   - 点击"加密"按钮对URL进行加密
   - 点击"解密"按钮对加密URL进行解密
3. 查看结果并可以复制到剪贴板

## 使用场景

### 独立版工具

适用于一般用途的URL加密，例如：
- 保护敏感URL信息
- 在不安全的环境中传输URL
- 作为简单的URL加密工具

### Django兼容版工具

适用于与Django项目集成的场景，例如：
- 为Django项目生成加密的Agent服务URL
- 在Django项目环境中解密URL
- 确保加密结果与Django项目完全兼容

## 技术实现

本工具使用Fernet对称加密（基于AES-128-CBC）：

- 独立版使用固定密钥
- Django兼容版使用PBKDF2从SECRET_KEY派生密钥
- 两个版本使用相同的盐值：heritage_project_salt
- 加密结果使用Base64编码，便于存储和传输

## 注意事项

1. 工具会在启动时检查必要的依赖（cryptography）
2. 如果pyperclip未安装，程序仍可正常运行，只是剪贴板功能不可用
3. Django兼容版需要确保Django项目路径正确（../backend/）
4. 加密和解密使用相同的密钥，请妥善保管

## 常见问题

请参考 [问题解决指南.md](问题解决指南.md) 获取详细的故障排除信息。

## 许可证

MIT License