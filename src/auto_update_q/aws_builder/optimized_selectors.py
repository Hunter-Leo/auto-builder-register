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
        "form#SignUp button[type='submit'][data-testid='signup-next-button']",  # 表单上下文
        "button[data-analytics-funnel-value*='button26']",  # 分析属性选择器
        "button[data-analytics-performance-mark*='27-']",  # 性能标记选择器
        "button[type='submit'][class*='primary']",  # 备用选择器
    ],
    
    # 步骤4: 邮箱验证码页面
    "verification_input": [
        "input[type='text'][autocomplete='on']",  # 成功的选择器 - 基于日志调整到最前面
        "input.awsui_input_2rhyz_7gdci_149[type='text']",  # 基于实际class
        "input[id*='formField'][type='text']",  # 基于ID模式 formField81-1756216788163-2256
        "input[aria-labelledby*='formField'][type='text']",  # 基于aria-labelledby
        "[data-testid='email-verification-form-code-input'] input",  # 测试ID选择器
        "input[type='text'][autocomplete='on'][value='']",  # 空值的文本输入框
    ],
    "verification_verify_button": [
        "button[data-testid='email-verification-verify-button']",  # 精确的测试ID - 从实际元素确认
        "button._2xAbzS8kNKd3Tl_k7Hlfav.awsui_variant-primary_vjswe_gmc8h_231",  # 完整class组合
        "button.awsui_variant-primary_vjswe_gmc8h_231[data-testid='email-verification-verify-button']",  # class+testid组合
        "button[data-analytics-funnel-value*='button82']",  # 基于analytics属性
        "button[data-analytics-performance-mark*='83-']",  # 基于performance标记
        "button[type='submit']:contains('Verify')",  # 基于文本内容
        "button[type='submit'][class*='primary']",  # 备用选择器
    ],
    "verification_resend_button": [
        "button[data-testid='email-verification-resend-code-button']",  # 重发按钮
    ],
    
    # 步骤5: 密码设置页面
    "password_input": [
        "input#awsui-input-2[type='password']",  # 基于实际元素的精确ID
        "input.awsui-input-type-password[type='password']",  # 基于实际class
        "input[type='password'][autocomplete='on']",  # 基于属性组合
        "input[aria-describedby*='error'][type='password']",  # 基于aria-describedby
        "input.awsui-input[type='password']",  # 基于通用class
        "input[type='password']:first-of-type",  # 第一个密码输入框
        "input[type='password'][aria-labelledby*='label']",  # 基于aria-labelledby
    ],
    "confirm_password_input": [
        "input[type='password']:not(#awsui-input-2)",  # 排除第一个密码框
        "input[type='password']:last-of-type",  # 最后一个密码输入框
        "input[type='password']:nth-of-type(2)",  # 第二个密码输入框
        "input[data-testid*='confirm']",  # 基于测试ID
        "input[aria-labelledby*='confirm']",  # 基于确认标签
    ],
    "captcha_input": [
        "input[id='awsui-input-1'][type='text']",  # 基于页面源码的精确ID
        "[data-testid='test-captcha-input'] input",  # 测试ID选择器
        "input[autocomplete='off'][type='text']",  # CAPTCHA通常关闭自动完成
    ],
    "captcha_refresh_button": [
        "button[data-testid='test-captcha-button-refresh']",  # 精确的测试ID
        "awsui-button[id='captcha-refresh'] button",  # 基于ID的组合选择器
    ],
    "create_button": [
        "button.awsui-button-variant-primary[type='submit']",  # 基于实际元素的精确选择器
        "button:contains('Create AWS Builder ID')",  # 基于按钮文本
        "button[awsui-button-region='text']:contains('Create')",  # 基于区域和文本
        "button.awsui-button.awsui-button-variant-primary",  # 基于完整class
        "button[type='submit'][class*='primary']",  # 通用primary按钮
        "button[data-testid='test-primary-button']",  # 测试ID选择器
        "button[class*='awsui-button-variant-primary']",  # class包含匹配
        "button[type='submit']",  # 最通用的提交按钮
        "input[type='submit']"  # input提交按钮
    ],
    
    # 通用选择器
    "primary_button": [
        "button[data-testid='test-primary-button']",
        "awsui-button[data-testid='test-primary-button'] button",
        "button[class*='awsui-button-variant-primary']",
        "button[type='submit'][class*='primary']",
        "button[type='submit']",
    ],
    "secondary_button": [
        "button[class*='awsui-button-variant-normal']",
        "button[class*='secondary']",
    ],
}

# 等待时间配置（秒）
OPTIMIZED_TIMEOUTS = {
    "element_wait": 1,  # 减少元素等待时间
    "page_load": 3,     # 减少页面加载等待时间
    "redirect_wait": 5, # 减少重定向等待时间
    "captcha_wait": 2,  # CAPTCHA处理等待时间
    "input_delay": 0.3, # 输入延迟
}

# 重试配置
RETRY_CONFIG = {
    "max_rounds": 2,    # 减少重试轮数
    "retry_delay": 1,   # 减少重试延迟
}

def get_selector(element_type: str, index: int = 0) -> str:
    """
    获取指定元素类型的选择器
    
    Args:
        element_type: 元素类型
        index: 选择器索引（0为最优先）
        
    Returns:
        str: CSS选择器
    """
    selectors = OPTIMIZED_SELECTORS.get(element_type, [])
    if index < len(selectors):
        return selectors[index]
    return selectors[0] if selectors else ""

def get_all_selectors(element_type: str) -> list:
    """
    获取指定元素类型的所有选择器
    
    Args:
        element_type: 元素类型
        
    Returns:
        list: CSS选择器列表
    """
    return OPTIMIZED_SELECTORS.get(element_type, [])

def get_timeout(timeout_type: str) -> int:
    """
    获取指定类型的超时时间
    
    Args:
        timeout_type: 超时类型
        
    Returns:
        int: 超时时间（秒）
    """
    return OPTIMIZED_TIMEOUTS.get(timeout_type, 3)

def get_retry_config() -> dict:
    """
    获取重试配置
    
    Returns:
        dict: 重试配置
    """
    return RETRY_CONFIG.copy()
