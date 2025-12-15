# Agent服务URL加密使用指南

## 概述

为了保护Agent服务的公网IP地址不被直接暴露，我们实现了一个加密/解密机制。即使有人获取到环境变量文件，也只能看到加密后的字符串，无法直接获取真实的IP地址。

## 工作原理

1. **加密存储**：Agent服务的URL在环境变量中以加密形式存储
2. **动态解密**：后端API在需要使用URL时动态解密
3. **前端获取**：前端通过API获取解密后的URL，无法直接访问加密字符串

## 使用方法

### 1. 加密新的URL

如果您需要更换Agent服务的URL，请使用以下方法加密：

#### 方法一：使用加密工具脚本

```bash
cd backend
python encrypt_url.py
```

然后按照提示输入要加密的URL。

#### 方法二：使用Python代码

```python
from heritage_api.encryption_utils import encrypt_agent_url

url = "https://your-agent-service-url.com"
encrypted_url = encrypt_agent_url(url)
print(f"加密后的URL: {encrypted_url}")
```

### 2. 更新环境变量

将加密后的URL更新到`.env`文件中：

```env
# Agent服务配置（已加密）
AGENT_SERVICE_URL=Z0FBQUFBQm84TXFtVWE5aDMxbGxTSS13d0xwLUl2R1gtaGJnM3RQc0FkV0t1V3dMak5yOVBWRjI4MU1pcWJaRmFOQnRZWExPVkFDOEN2UzRuTE84VXh2VlhLZW11bU5weC1IdEtUZmtrWXgtUVZpX3hxMjJ6M0E9
```

### 3. 重启服务

更新环境变量后，需要重启Django服务使更改生效：

```bash
python manage.py runserver
```

## 安全性说明

1. **加密算法**：使用Fernet对称加密（基于AES-128-CBC）
2. **密钥派生**：基于Django的SECRET_KEY使用PBKDF2密钥派生函数
3. **密钥唯一性**：每个Django项目有唯一的加密密钥
4. **前端安全**：前端只能获取解密后的URL，无法获取加密字符串或密钥

## 测试验证

可以使用提供的测试脚本验证加密/解密功能：

```bash
# 测试解密功能
python test_decrypt.py

# 测试API端点
python test_api.py
```

## 版权声明

**© 2025 版权所有** - 本项目仅用于个人作品集展示，**禁止任何形式的使用、修改、分发或商业利用**。

* 本项目代码仅供学习和参考，不得用于任何实际项目
* 未经授权，禁止复制或引用本项目的任何代码
* 所有权利保留，侵权必究

## 联系方式

- 项目维护者: elaine
- 邮箱: onee20589@gmail.com
- 项目链接: https://github.com/Elaine-one/shaanxi-heritage-ai-platform

## 注意事项

1. **SECRET_KEY安全**：确保Django的SECRET_KEY安全，不要泄露
2. **环境变量备份**：更新环境变量前建议备份原始文件
3. **URL格式**：加密前确保URL格式正确（以http://或https://开头）
4. **测试验证**：更新后务必测试功能是否正常

## 故障排除

### 问题1：解密失败

**可能原因**：
- 加密字符串被修改
- SECRET_KEY发生变化
- 加密算法版本不匹配

**解决方案**：
- 重新生成加密字符串
- 确保SECRET_KEY未更改
- 检查cryptography库版本

### 问题2：API返回错误

**可能原因**：
- 环境变量未正确设置
- 加密工具模块导入失败

**解决方案**：
- 检查.env文件格式
- 确保cryptography库已安装
- 查看Django错误日志