# Auto Update Q

自动更新 Q 项目

## 模块

### DropMail 临时邮箱模块

基于 [dropmail.me](https://dropmail.me) API 实现的临时邮箱功能模块。

#### 功能特性

- ✅ 获取临时邮箱地址
- ✅ 接收邮件
- ✅ 发送邮件（通过外部SMTP服务器）
- ✅ 会话管理
- ✅ 多域名支持
- ✅ 邮件等待功能

#### 快速使用

```python
from auto_update_q.temp_mail import DropMail

# 创建实例并获取临时邮箱
dropmail = DropMail()
temp_email = dropmail.get_temp_email()
print(f"临时邮箱: {temp_email}")

# 接收邮件
mails = dropmail.get_mails()
for mail in mails:
    print(f"从: {mail.from_addr}, 主题: {mail.subject}")

# 等待新邮件
new_mail = dropmail.wait_for_mail(timeout=60)
if new_mail:
    print(f"收到新邮件: {new_mail.subject}")
```

详细文档请查看 [temp_mail 模块文档](src/auto_update_q/temp_mail/README.md)

## 安装

```bash
uv sync
```

## 运行演示

```bash
# 运行临时邮箱演示
uv run python src/auto_update_q/temp_mail/quick_demo.py

# 运行测试
uv run python src/auto_update_q/temp_mail/test_dropmail.py
```

## 开发

使用 uv 管理项目依赖：

```bash
# 安装依赖
uv sync

# 添加新依赖
uv add package_name

# 运行脚本
uv run python script.py
```
