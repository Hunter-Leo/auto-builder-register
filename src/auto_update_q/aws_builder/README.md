# AWS Builder ID 自动注册模块

基于 Selenium 实现的 AWS Builder ID 自动注册功能模块。

## 功能特性

- ✅ 自动填写注册表单
- ✅ 处理邮箱验证（手动输入验证码）
- ✅ 处理图形验证码（手动输入）
- ✅ 会话管理
- ✅ 自动生成安全密码
- ✅ 返回登录凭证
- ✅ 支持导航到其他页面（保持会话）

## 安装依赖

```bash
uv add selenium webdriver-manager pillow
```

## 快速使用

### 基本注册流程

```python
from auto_update_q.aws_builder import AWSBuilder

# 创建注册器实例
aws_builder = AWSBuilder(headless=False)  # 使用有界面模式

# 注册账号
credentials = aws_builder.register_aws_builder(
    email="your-email@example.com",
    name="Your Name"
)

if credentials:
    print(f"注册成功！")
    print(f"邮箱: {credentials.email}")
    print(f"密码: {credentials.password}")
    print(f"姓名: {credentials.name}")
else:
    print("注册失败")

# 关闭浏览器
aws_builder.close()
```

### 使用上下文管理器

```python
from auto_update_q.aws_builder import AWSBuilder

with AWSBuilder(headless=False) as aws_builder:
    credentials = aws_builder.register_aws_builder(
        email="your-email@example.com",
        name="Your Name"
    )
    
    if credentials:
        # 注册成功后导航到其他页面
        aws_builder.navigate_to_url("https://view.awsapps.com/start/#/device?user_code=XXXX-XXXX")
        print(f"当前页面: {aws_builder.get_current_url()}")
```

## API 参考

### AWSBuilder 类

#### 构造函数

```python
AWSBuilder(headless: bool = False, timeout: int = 30)
```

- `headless`: 是否使用无头模式（默认 False，推荐使用有界面模式便于处理验证码）
- `timeout`: 等待超时时间（秒）

#### 主要方法

##### register_aws_builder()

```python
register_aws_builder(email: str, name: str) -> Optional[AWSBuilderCredentials]
```

注册 AWS Builder ID 账号。

**参数：**
- `email`: 邮箱地址
- `name`: 用户姓名

**返回：**
- `AWSBuilderCredentials`: 注册成功的凭证信息
- `None`: 注册失败

##### navigate_to_url()

```python
navigate_to_url(url: str) -> bool
```

导航到指定URL（保持会话）。

**参数：**
- `url`: 目标URL

**返回：**
- `bool`: 是否成功导航

##### get_current_url()

```python
get_current_url() -> Optional[str]
```

获取当前页面URL。

##### get_page_title()

```python
get_page_title() -> Optional[str]
```

获取当前页面标题。

##### close()

```python
close()
```

关闭浏览器。

### AWSBuilderCredentials 数据类

```python
@dataclass
class AWSBuilderCredentials:
    email: str
    password: str
    name: str
    builder_id: Optional[str] = None
```

## 注册流程

1. **访问注册页面**: 自动导航到 AWS Builder ID 注册页面
2. **输入邮箱**: 自动填写邮箱地址
3. **输入姓名**: 自动填写用户姓名
4. **邮箱验证**: 提示用户手动输入邮箱验证码
5. **设置密码**: 自动生成并填写安全密码
6. **处理验证码**: 如果出现图形验证码，提示用户手动输入
7. **完成注册**: 检查注册状态并返回凭证

## 注意事项

1. **浏览器要求**: 需要安装 Microsoft Edge 浏览器
2. **手动验证**: 邮箱验证码和图形验证码需要手动输入
3. **网络环境**: 确保能够访问 AWS 相关网站
4. **会话保持**: 注册成功后浏览器会话保持打开，可以导航到其他页面

## 运行演示

```bash
# 运行注册演示
uv run python src/auto_update_q/aws_builder/demo.py

# 运行基础测试
uv run python src/auto_update_q/aws_builder/test_aws_builder.py
```

## 错误处理

模块包含完善的错误处理和日志记录：

- 超时处理
- 元素查找失败处理
- 网络错误处理
- 详细的日志输出

## 开发说明

### 项目结构

```
aws_builder/
├── __init__.py          # 模块入口
├── aws_builder.py       # 主要实现
├── demo.py             # 使用演示
├── test_aws_builder.py # 测试文件
├── README.md           # 文档
└── prompt.md           # 需求文档
```

### 扩展功能

如需扩展功能，可以：

1. 添加更多的验证码识别方法
2. 支持更多浏览器类型
3. 添加配置文件支持
4. 实现批量注册功能
