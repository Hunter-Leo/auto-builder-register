# Auto Update Q

自动更新 Q 项目

## 模块

### AWS Builder ID 自动注册工具

基于 Selenium 和 DropMail 实现的 AWS Builder ID 自动注册命令行工具。

#### 功能特性

- ✅ 自动生成临时邮箱
- ✅ 自动填写注册表单
- ✅ 自动处理邮箱验证码
- ✅ 在图形验证码前停止自动化
- ✅ 支持 Safari 和 Edge 浏览器
- ✅ 自动保存注册信息
- ✅ 完整的命令行界面
- ✅ 丰富的配置选项

#### 快速使用

```bash
# 基本使用（自动生成临时邮箱）
uv run auto-register-aws-builder register

# 指定邮箱和姓名
uv run auto-register-aws-builder register --email test@example.com --name "John Doe"

# 使用 Safari 浏览器
uv run auto-register-aws-builder register --browser safari

# 启用调试模式
uv run auto-register-aws-builder register --debug

# 查看注册记录
uv run auto-register-aws-builder list-records

# 查看帮助
uv run auto-register-aws-builder --help
```

#### 命令行选项

```bash
# register 命令选项
--email, -e          📧 指定邮箱地址（可选，不提供则自动生成临时邮箱）
--name, -n           👤 用户姓名（默认: "Crazy Joe"）
--password, -p       🔐 指定密码（默认: "CrazyJoe@2025"）
--headless           👻 使用无头模式（Safari不支持）
--browser, -b        🌐 浏览器类型（safari/edge，默认: edge）
--timeout, -t        ⏱️ 操作超时时间（10-300秒，默认: 30）
--wait-minutes, -w   ⏳ 等待用户操作时间（1-120分钟，默认: 30）
--cache-file, -c     💾 缓存文件路径（默认: .cache/auto_register_aws_builder.csv）
--debug, -d          🐛 启用调试模式
--no-temp-email      🚫 不使用临时邮箱，需要手动处理邮箱验证
```

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
# 运行 AWS Builder ID 自动注册演示
uv run python demo_auto_register.py

# 运行临时邮箱演示
uv run python src/auto_update_q/temp_mail/quick_demo.py

# 运行测试
uv run python src/auto_update_q/temp_mail/test_dropmail.py
uv run python test/test_auto_register.py
uv run python test/test_cli.py
```

## 使用说明

### Safari 浏览器设置

使用 Safari 浏览器前需要进行以下设置：

1. 打开 Safari 偏好设置
2. 选择"高级"标签
3. 勾选"在菜单栏中显示开发菜单"
4. 在菜单栏的"开发"菜单中选择"允许远程自动化"

### 注册流程

1. 工具会自动创建临时邮箱（或使用指定邮箱）
2. 自动填写注册表单
3. 自动处理邮箱验证码
4. 在图形验证码前停止自动化
5. 用户手动完成图形验证码
6. 注册信息自动保存到 CSV 文件

### 注册记录

注册信息会保存到 `.cache/auto_register_aws_builder.csv` 文件中，包含：
- 时间戳
- 邮箱地址
- 密码
- 姓名
- 状态

## 开发

使用 uv 管理项目依赖：

```bash
# 安装依赖
uv sync

# 添加新依赖
uv add package_name

# 运行脚本
uv run python script.py

# 运行命令行工具
uv run auto-register-aws-builder --help
```

## 项目结构

```
auto-update-q/
├── src/
│   └── auto_update_q/
│       ├── __init__.py
│       ├── auto_register.py          # 主命令行工具
│       ├── aws_builder/              # AWS Builder 注册模块
│       │   ├── aws_builder.py        # 主注册器
│       │   ├── browser_manager.py    # 浏览器管理
│       │   ├── captcha_handler.py    # 验证码处理
│       │   ├── form_handler.py       # 表单处理
│       │   └── ...
│       └── temp_mail/                # 临时邮箱模块
│           ├── dropmail.py
│           └── ...
├── test/                             # 测试文件
│   ├── test_auto_register.py
│   └── test_cli.py
├── .cache/                           # 缓存目录
│   └── auto_register_aws_builder.csv
├── demo_auto_register.py             # 演示脚本
└── pyproject.toml                    # 项目配置
```
