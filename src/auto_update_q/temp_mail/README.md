# DropMail 临时邮箱模块

基于 [dropmail.me](https://dropmail.me) API 实现的临时邮箱功能模块。

## 功能特性

- ✅ 获取临时邮箱地址
- ✅ 接收邮件
- ✅ 发送邮件（通过外部SMTP服务器）
- ✅ 会话管理
- ✅ 多域名支持
- ✅ 邮件等待功能

## 安装依赖

```bash
uv add requests
```

## 快速开始

### 1. 基本使用

```python
from auto_update_q.temp_mail import DropMail

# 创建 DropMail 实例
dropmail = DropMail()

# 获取临时邮箱地址
temp_email = dropmail.get_temp_email()
print(f"临时邮箱: {temp_email}")

# 检查邮件
mails = dropmail.get_mails()
for mail in mails:
    print(f"从: {mail.from_addr}")
    print(f"主题: {mail.subject}")
    print(f"内容: {mail.text}")
```

### 2. 等待新邮件

```python
# 等待新邮件（最多等待5分钟）
new_mail = dropmail.wait_for_mail(timeout=300)
if new_mail:
    print(f"收到新邮件: {new_mail.subject}")
else:
    print("超时，未收到新邮件")
```

### 3. 发送邮件

```python
# 发送邮件（需要配置SMTP服务器）
success = dropmail.send_email(
    to_email="recipient@example.com",
    subject="测试邮件",
    body="这是一封测试邮件",
    from_email="your_email@gmail.com",
    password="your_app_password"  # Gmail 应用专用密码
)

if success:
    print("邮件发送成功!")
```

### 4. 指定域名

```python
# 获取可用域名
domains = dropmail.get_domains()
for domain in domains:
    print(f"域名: {domain['name']}, ID: {domain['id']}")

# 使用指定域名创建会话
session = dropmail.create_session(domain_id="RG9tYWluOjE=")
```

## API 参考

### DropMail 类

#### 构造函数

```python
DropMail(auth_token: Optional[str] = None)
```

- `auth_token`: 认证令牌，如果不提供则自动生成

#### 主要方法

##### get_temp_email() -> str
获取临时邮箱地址。如果没有活动会话，会自动创建一个。

##### create_session(domain_id: Optional[str] = None) -> Session
创建新的邮箱会话。

- `domain_id`: 指定域名ID，如果不提供则使用随机域名

##### get_mails(after_mail_id: Optional[str] = None) -> List[Mail]
获取邮件列表。

- `after_mail_id`: 获取指定邮件ID之后的邮件

##### wait_for_mail(timeout: int = 300, check_interval: int = 5) -> Optional[Mail]
等待接收新邮件。

- `timeout`: 超时时间（秒）
- `check_interval`: 检查间隔（秒）

##### send_email(...) -> bool
发送邮件。

参数：
- `to_email`: 收件人邮箱
- `subject`: 邮件主题
- `body`: 邮件内容
- `smtp_server`: SMTP服务器地址（默认: smtp.gmail.com）
- `smtp_port`: SMTP服务器端口（默认: 587）
- `from_email`: 发件人邮箱
- `password`: 发件人邮箱密码
- `is_html`: 是否为HTML格式（默认: False）

##### get_domains() -> List[Dict[str, Any]]
获取可用域名列表。

##### add_address(domain_id: Optional[str] = None) -> Address
为当前会话添加新的邮箱地址。

##### get_session_info() -> Optional[Session]
获取当前会话信息。

### 数据类

#### Mail
邮件数据类，包含以下属性：
- `id`: 邮件ID
- `from_addr`: 发件人地址
- `to_addr`: 收件人地址
- `subject`: 邮件主题
- `text`: 纯文本内容
- `html`: HTML内容（可选）
- `received_at`: 接收时间
- `raw_size`: 原始大小
- `download_url`: 下载链接

#### Address
邮箱地址数据类，包含以下属性：
- `id`: 地址ID
- `address`: 邮箱地址
- `restore_key`: 恢复密钥

#### Session
会话数据类，包含以下属性：
- `id`: 会话ID
- `expires_at`: 过期时间
- `addresses`: 地址列表
- `mails`: 邮件列表

## 使用示例

查看 `example.py` 文件获取完整的使用示例。

## 测试

运行测试：

```bash
python test_dropmail.py
```

## 注意事项

1. **认证令牌**: API 目前处于公测阶段，可以使用任意8位以上字符串作为认证令牌。
2. **会话过期**: 会话会自动过期，但每次访问会延长过期时间。
3. **发送邮件**: 发送功能需要配置外部SMTP服务器，推荐使用Gmail的应用专用密码。
4. **速率限制**: 请合理使用API，避免过于频繁的请求。

## Gmail SMTP 配置

如果使用Gmail发送邮件，需要：

1. 启用两步验证
2. 生成应用专用密码
3. 使用以下配置：
   - SMTP服务器: smtp.gmail.com
   - 端口: 587
   - 使用应用专用密码而不是账户密码

## 错误处理

模块会抛出以下异常：
- `Exception`: 当API返回错误或网络请求失败时
- `requests.RequestException`: 当HTTP请求失败时

建议在使用时添加适当的异常处理。

## 许可证

本模块基于项目许可证发布。
