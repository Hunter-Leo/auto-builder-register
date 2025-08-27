#!/usr/bin/env python3
"""
基于实际页面源码分析的优化选择器配置
通过分析page_source_step*.html文件得出的最精确选择器

关键发现（基于page_source_step3_name_page_165012.html分析）:
- 邮箱输入: input[autocomplete='on'][type='text'] 
- 姓名输入: input[placeholder='Maria José Silva']
- Next按钮: button[data-testid='signup-next-button'] (确认存在)
- 表单ID: form#SignUp
- 主要CSS类: awsui_variant-primary_vjswe_gmc8h_231, _2xAbzS8kNKd3Tl_k7Hlfav
"""

# 优化后的选择器配置，按优先级排序
OPTIMIZED_SELECTORS = {
    # 步骤1: 主页面 - Cookie处理
    "cookie_accept": [
        "button[data-id='awsccc-cb-btn-accept']",  # 精确的data-id选择器
        ".awsccc-u-btn-primary",  # 备用class选择器
        "button[aria-label*='Accept']",  # 备用aria-label选择器
    ],
    
    # 步骤2: 邮箱输入页面
    "email_input": [
        "input[autocomplete='on'][type='text']",  # 基于页面源码的精确属性组合
        "input#formField24-1756198202888-5657",  # 基于页面源码的精确ID
        "[data-testid='signup-email-input'] input",  # 测试ID选择器
        "input.awsui_input_2rhyz_7gdci_149[autocomplete='on']",  # class和属性组合
        "input[aria-labelledby*='email']",  # 可访问性选择器
        "input[type='text'][value*='@']",  # 邮箱模式匹配
    ],
    "email_next_button": [
        "awsui-button[data-testid='test-primary-button'] button",  # 精确的组合选择器
        "button[data-testid='test-primary-button']",  # 直接按钮选择器
        "button[type='submit'][class*='primary']",  # 备用选择器
    ],
    
    # 步骤3: 姓名输入页面
    "name_input": [
        "input[placeholder='Maria José Silva']",  # 基于placeholder的精确选择器
        "input#formField25-1756198202888-4727",  # 基于页面源码的精确ID
        "[data-testid='signup-full-name-input'] input",  # 测试ID选择器
        "input[type='text'][autocomplete='on']:not([value*='@'])",  # 非邮箱的文本输入框
        "input.awsui_input_2rhyz_7gdci_149[placeholder]",  # 基于class和placeholder
    ],
    "name_next_button": [
        "button[data-testid='signup-next-button']",  # 精确的测试ID（从页面源码确认）
        "button[data-testid='signup-next-button'][type='submit']",  # 更具体的选择器
        "button.awsui_variant-primary_vjswe_gmc8h_231[data-testid='signup-next-button']",  # 完整class匹配
        "button._2xAbzS8kNKd3Tl_k7Hlfav.awsui_variant-primary_vjswe_gmc8h_231",  # 组合class选择器
    ],
    
    # 步骤4: 邮箱验证码页面
    "verification_code_input": [
        "input[class*='awsui_input'][autocomplete='on'][type='text']",  # 匹配实际页面元素
        "input[aria-labelledby*='formField'][type='text']",  # 基于aria-labelledby属性
        "input[data-testid='verification-code-input']",
        "input[placeholder*='code']",
        "input[type='text'][maxlength='6']",
        "input[aria-label*='verification']",
        ".verification-code input",
        "input[type='text'][value='']",  # 空值的文本输入框
    ],
    "verify_button": [
        "button[data-testid='email-verification-verify-button']",  # 匹配实际的验证按钮
        "button[data-testid*='verification'][data-testid*='verify']",  # 通用验证按钮模式
        "awsui-button[data-testid='test-primary-button'] button",  # 匹配AWS UI按钮
        "button[data-testid='signup-next-button']",  # 注册下一步按钮
        "button[data-testid='verify-button']",
        "button[type='submit'][class*='primary']",
        "button:contains('Verify')",
        "button[class*='awsui'][class*='primary']",  # AWS UI主要按钮
        "button[type='submit'][class*='awsui_variant-primary']",  # AWS UI主要提交按钮
        ".verify-btn",
    ],
    "resend_code_button": [
        "button[data-testid='email-verification-resend-code-button']",  # 精确匹配重发按钮
        "button[class*='awsui_variant-normal'][data-testid*='resend']",  # 通用重发按钮模式
        "button[class*='awsui_button'][class*='variant-normal']",  # AWS UI普通按钮
        "button[type='button'][data-testid*='resend']",  # 按类型和testid匹配
        ".resend-code-btn",
    ],
    
    # 步骤5: 密码设置页面
    "password_input": [
        "input#awsui-input-1",  # 密码输入框的精确ID
        "input[class*='awsui-input'][class*='type-password'][type='password']:nth-of-type(2)",  # 第二个密码框
        "input[type='password'][autocomplete='on']:nth-of-type(2)",  # 第二个密码输入框
        "input[class*='awsui-input'][type='password']:nth-of-type(2)",  # 第二个awsui密码框
        "input[data-testid='password-input']",
        "input[type='password'][autocomplete='new-password']:nth-of-type(2)",
        "input[aria-label*='password']:not([aria-label*='confirm'])",
        "#password",
    ],
    "confirm_password_input": [
        "input#awsui-input-0",  # 密码确认框的精确ID
        "input[class*='awsui-input'][class*='type-password'][type='password']:nth-of-type(1)",  # 第一个密码框
        "input[type='password'][autocomplete='on']:nth-of-type(1)",  # 第一个密码输入框
        "input[class*='awsui-input'][type='password']:nth-of-type(1)",  # 第一个awsui密码框
        "input[data-testid='test-retype-input']",  # 直接匹配data-testid
        "input[data-testid='confirm-password-input']",
        "input[aria-label*='confirm']",
        "#confirmPassword",
    ],
    "password_next_button": [
        "button[data-testid='password-next-button']",
        "button[type='submit'][class*='primary']",
        "button[class*='awsui'][class*='primary']",
    ],
    
    # 验证码相关
    "captcha_container": [
        ".captcha-container",
        "[data-testid='captcha']",
        ".challenge-container",
        "#captcha",
    ],
    "captcha_input": [
        "input[data-testid='captcha-input']",
        "input[placeholder*='captcha']",
        ".captcha-input input",
        "input[aria-label*='captcha']",
    ],
    "captcha_submit": [
        "button[data-testid='captcha-submit']",
        "button[type='submit']:contains('Submit')",
        ".captcha-submit",
    ],
    "captcha_error": [
        ".captcha-error",
        "[data-testid='captcha-error']",
        ".error-message:contains('captcha')",
    ],
    
    # 成功和错误指标
    "success_indicators": [
        ".success-message",
        "[data-testid='success']",
        ".registration-complete",
        "h1:contains('Welcome')",
        ".dashboard",
    ],
    "error_messages": [
        ".error-message",
        "[data-testid='error']",
        ".alert-error",
        ".validation-error",
    ],
    "registration_form": [
        "form[data-testid='signup-form']",
        "#SignUp",
        ".signup-form",
    ],
    "dashboard_elements": [
        ".aws-console",
        "[data-testid='dashboard']",
        ".builder-dashboard",
        "nav[aria-label*='AWS']",
    ],
    "builder_id_display": [
        "[data-testid='builder-id']",
        ".builder-id",
        "#builderId",
    ],
}

# 超时配置
TIMEOUT_CONFIG = {
    "email_input": 15,
    "name_input": 10,
    "verification_code_input": 10,
    "password_input": 10,
    "captcha_container": 5,
    "default": 10,
}

# 重试配置
RETRY_CONFIG = {
    "email_input": {"max_rounds": 3, "timeout": 5},
    "name_input": {"max_rounds": 3, "timeout": 3},
    "verification_code_input": {"max_rounds": 2, "timeout": 5},
    "password_input": {"max_rounds": 2, "timeout": 3},
    "captcha_container": {"max_rounds": 2, "timeout": 2},
    "default": {"max_rounds": 3, "timeout": 3},
}


def get_selector(element_name: str) -> list:
    """
    获取指定元素的选择器列表
    
    Args:
        element_name: 元素名称
        
    Returns:
        选择器列表
    """
    return OPTIMIZED_SELECTORS.get(element_name, [])


def get_all_selectors() -> dict:
    """
    获取所有选择器配置
    
    Returns:
        完整的选择器配置字典
    """
    return OPTIMIZED_SELECTORS.copy()


def get_timeout(element_name: str, default: int = 10) -> int:
    """
    获取指定元素的超时配置
    
    Args:
        element_name: 元素名称
        default: 默认超时时间
        
    Returns:
        超时时间（秒）
    """
    return TIMEOUT_CONFIG.get(element_name, TIMEOUT_CONFIG.get("default", default))


def get_retry_config(element_name: str, config_key: str, default_value) -> any:
    """
    获取指定元素的重试配置
    
    Args:
        element_name: 元素名称
        config_key: 配置键名（max_rounds 或 timeout）
        default_value: 默认值
        
    Returns:
        配置值
    """
    element_config = RETRY_CONFIG.get(element_name, RETRY_CONFIG.get("default", {}))
    return element_config.get(config_key, default_value)


def add_selector(element_name: str, selector: str, priority: int = -1) -> None:
    """
    添加新的选择器
    
    Args:
        element_name: 元素名称
        selector: 选择器字符串
        priority: 优先级（0为最高，-1为最低）
    """
    if element_name not in OPTIMIZED_SELECTORS:
        OPTIMIZED_SELECTORS[element_name] = []
    
    if priority == -1:
        OPTIMIZED_SELECTORS[element_name].append(selector)
    else:
        OPTIMIZED_SELECTORS[element_name].insert(priority, selector)


def update_timeout(element_name: str, timeout: int) -> None:
    """
    更新元素的超时配置
    
    Args:
        element_name: 元素名称
        timeout: 超时时间（秒）
    """
    TIMEOUT_CONFIG[element_name] = timeout


def update_retry_config(element_name: str, max_rounds: int = None, timeout: int = None) -> None:
    """
    更新元素的重试配置
    
    Args:
        element_name: 元素名称
        max_rounds: 最大重试轮数
        timeout: 每轮超时时间
    """
    if element_name not in RETRY_CONFIG:
        RETRY_CONFIG[element_name] = {}
    
    if max_rounds is not None:
        RETRY_CONFIG[element_name]["max_rounds"] = max_rounds
    
    if timeout is not None:
        RETRY_CONFIG[element_name]["timeout"] = timeout
