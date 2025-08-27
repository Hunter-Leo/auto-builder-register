# DropMail 使用指南

## 快速开始

### 1. 导入模块

```python
from auto_update_q.temp_mail import DropMail
```

### 2. 创建实例并获取临时邮箱

```python
# 创建 DropMail 实例
dropmail = DropMail()

# 获取临时邮箱地址
temp_email = dropmail.get_temp_email()
print(f"临时邮箱: {temp_email}")
```

### 3. 接收邮件

```python
# 方法1: 检查现有邮件
mails = dropmail.get_mails()
for mail in mails:
    print(f"从: {mail.from_addr}")
    print(f"主题: {mail.subject}")
    print(f"内容: {mail.text}")

# 方法2: 等待新邮件
new_mail = dropmail.wait_for_mail(timeout=60)  # 等待1分钟
if new_mail:
    print(f"收到新邮件: {new_mail.subject}")
```

### 4. 发送邮件

```python
# 使用Gmail SMTP发送邮件
success = dropmail.send_email(
    to_email=temp_email,
    subject="测试邮件",
    body="这是一封测试邮件",
    from_email="your_email@gmail.com",
    password="your_app_password"  # Gmail应用专用密码
)

if success:
    print("邮件发送成功!")
```

## 完整示例

```python
from auto_update_q.temp_mail import DropMail
import time

def main():
    # 创建实例
    dropmail = DropMail()
    
    # 获取临时邮箱
    temp_email = dropmail.get_temp_email()
    print(f"临时邮箱: {temp_email}")
    
    # 发送测试邮件到临时邮箱
    print("发送测试邮件...")
    success = dropmail.send_email(
        to_email=temp_email,
        subject="自动化测试邮件",
        body="这是一封自动化测试邮件，用于验证临时邮箱功能。",
        from_email="your_email@gmail.com",
        password="your_app_password"
    )
    
    if success:
        print("邮件发送成功，等待接收...")
        
        # 等待邮件到达
        new_mail = dropmail.wait_for_mail(timeout=30)
        if new_mail:
            print("收到邮件!")
            print(f"主题: {new_mail.subject}")
            print(f"内容: {new_mail.text}")
        else:
            print("未在指定时间内收到邮件")
    else:
        print("邮件发送失败")

if __name__ == "__main__":
    main()
```

## 运行演示

```bash
# 运行快速演示
uv run python src/auto_update_q/temp_mail/quick_demo.py

# 运行完整示例
uv run python src/auto_update_q/temp_mail/example.py

# 运行测试
uv run python src/auto_update_q/temp_mail/test_dropmail.py
```

## 注意事项

1. **Gmail SMTP配置**: 如需发送邮件，请确保：
   - 启用Gmail两步验证
   - 生成应用专用密码
   - 使用应用专用密码而非账户密码

2. **会话管理**: 
   - 会话会自动过期，但每次访问会延长过期时间
   - 可以通过 `get_session_info()` 查看会话状态

3. **错误处理**: 
   - 建议在生产环境中添加适当的异常处理
   - 网络问题可能导致API调用失败

4. **速率限制**: 
   - 请合理使用API，避免过于频繁的请求
   - 建议在循环中添加适当的延时
