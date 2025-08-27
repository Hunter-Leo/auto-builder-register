# AWS Builder ID 自动注册模块

基于 Selenium 实现的 AWS Builder ID 自动注册功能模块，采用模块化设计，职责分离，代码清晰易维护。

## 🎯 功能特性

### 模块化设计
- **职责分离**: 每个模块负责特定功能，降低耦合度
- **代码复用**: 组件可独立使用和测试
- **易于维护**: 修改某个功能不影响其他模块
- **扩展性强**: 可轻松添加新功能或替换组件

### 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| **配置管理** | `config.py` | 集中管理所有配置项 |
| **浏览器管理** | `browser_manager.py` | 浏览器初始化和配置 |
| **元素等待** | `element_waiter.py` | 页面元素等待和查找 |
| **表单处理** | `form_handler.py` | 表单填写逻辑 |
| **验证码处理** | `captcha_handler.py` | 图形和邮箱验证码处理 |
| **注册检查** | `registration_checker.py` | 注册状态验证 |
| **选择器配置** | `optimized_selectors.py` | 页面元素选择器 |
| **主控制器** | `aws_builder.py` | 主要业务逻辑协调 |

## 🚀 功能特性

- ✅ **自动填写注册表单** - 智能表单识别和填写
- ✅ **邮箱验证处理** - 支持手动输入和自动获取验证码
- ✅ **图形验证码处理** - 智能检测和手动输入支持
- ✅ **会话管理** - 保持登录状态，支持页面导航
- ✅ **密码生成** - 自动生成符合要求的安全密码
- ✅ **多重选择器** - 提高元素查找成功率
- ✅ **智能重试** - 自动重试机制，提高成功率
- ✅ **动态等待** - 智能等待页面变化，无硬编码延时
- ✅ **详细日志** - 完整的操作日志记录
- ✅ **错误处理** - 完善的异常处理机制

## 📦 安装依赖

```bash
uv add selenium webdriver-manager
```

## 🎮 快速使用

### 基础注册

```python
from auto_update_q.aws_builder import AWSBuilder

# 使用上下文管理器（推荐）
with AWSBuilder(headless=False, debug=True) as aws_builder:
    credentials = aws_builder.register_aws_builder(
        email="your-email@example.com",
        name="Your Name"
    )
    
    if credentials:
        print(f"注册成功！邮箱: {credentials.email}")
        print(f"密码: {credentials.password}")
    else:
        print("注册失败")
```

### 集成临时邮箱

```python
from auto_update_q.aws_builder import AWSBuilder
from auto_update_q.temp_mail import DropMail

# 创建临时邮箱
dropmail = DropMail()
temp_email = dropmail.get_temp_email()

# 使用临时邮箱注册（自动获取验证码）
with AWSBuilder() as aws_builder:
    credentials = aws_builder.register_aws_builder(
        email=temp_email,
        name="Test User",
        dropmail=dropmail  # 自动获取邮箱验证码
    )
```

### 自定义配置

```python
with AWSBuilder(
    headless=False,      # 显示浏览器界面
    timeout=60,          # 超时时间
    debug=True,          # 启用调试日志
    keep_browser=True    # 保持浏览器打开
) as aws_builder:
    credentials = aws_builder.register_aws_builder(
        email="test@example.com",
        name="Test User",
        password="CustomPassword123!"  # 自定义密码
    )
```

## 🏗️ 架构设计

### 组件关系图

```
AWSBuilder (主控制器)
├── BrowserManager (浏览器管理)
├── ElementWaiter (元素等待)
├── FormHandler (表单处理)
│   └── ElementWaiter
├── CaptchaHandler (验证码处理)
│   └── ElementWaiter
├── RegistrationChecker (状态检查)
│   └── ElementWaiter
└── Config (配置管理)
```

### 数据流

```
1. 初始化组件 → 2. 设置浏览器 → 3. 导航页面
                                      ↓
8. 返回凭证 ← 7. 检查状态 ← 6. 处理验证码 ← 4. 填写表单
                                      ↓
                                  5. 邮箱验证
```

## 🔧 配置说明

### 浏览器配置 (`config.py`)

```python
BROWSER_OPTIONS = {
    "headless_args": [...],      # 无头模式参数
    "common_args": [...],        # 通用参数
    "experimental_options": {...} # 实验性选项
}
```

### 选择器配置 (`optimized_selectors.py`)

```python
OPTIMIZED_SELECTORS = {
    "email_input": [...],        # 邮箱输入框选择器
    "name_input": [...],         # 姓名输入框选择器
    "password_input": [...],     # 密码输入框选择器
    # ... 更多选择器
}
```

### 超时和重试配置

```python
TIMEOUT_CONFIG = {
    "email_input": 15,           # 邮箱输入超时
    "default": 10,               # 默认超时
}

RETRY_CONFIG = {
    "email_input": {
        "max_rounds": 3,         # 最大重试轮数
        "timeout": 5             # 每轮超时
    }
}
```

## 🧪 测试和演示

### 运行演示

```bash
# 运行演示
uv run python src/auto_update_q/aws_builder/demo.py
```

### 单元测试

```bash
# 测试各个组件
uv run python test/test_aws_builder_refactored.py
```

## 🔍 故障排除

### 常见问题

1. **浏览器启动失败**
   - 检查 Edge 浏览器是否已安装
   - 检查网络连接
   - 尝试手动下载 EdgeDriver

2. **元素查找失败**
   - 检查选择器配置是否最新
   - 启用调试模式查看详细日志
   - 更新选择器配置

3. **验证码处理失败**
   - 确保在有界面模式下运行
   - 检查验证码输入是否正确
   - 查看日志了解具体错误

### 调试技巧

```python
# 启用详细日志
with AWSBuilder(debug=True) as aws_builder:
    # ... 注册逻辑

# 保持浏览器打开进行调试
with AWSBuilder(keep_browser=True) as aws_builder:
    # ... 注册逻辑
    input("按回车关闭浏览器...")
```

## 🛠️ 扩展开发

### 添加新的表单字段

1. 在 `optimized_selectors.py` 中添加选择器
2. 在 `form_handler.py` 中添加处理方法
3. 在主流程中调用新方法

### 添加新的验证码类型

1. 在 `captcha_handler.py` 中添加处理方法
2. 更新主流程调用逻辑

### 自定义浏览器配置

1. 修改 `config.py` 中的配置
2. 或在初始化时传入自定义参数

## 🎉 核心优势

通过模块化设计，我们实现了：

1. **代码清晰**: 职责分离，逻辑清晰
2. **易于维护**: 模块化便于修改和扩展
3. **高可测试性**: 每个组件都可以独立测试
4. **智能等待**: 动态等待机制，无硬编码延时
5. **强扩展性**: 为未来功能扩展奠定基础

模块化的设计使得代码更加清晰、可维护，同时也为团队协作和功能扩展提供了便利。
