"""
AWS Builder ID 模块配置
"""

# 基础配置
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY_ROUNDS = 3
DEFAULT_RETRY_TIMEOUT = 3

# URL 配置
AWS_BUILDER_SIGNUP_URL = "https://profile.aws.amazon.com/"

# 浏览器配置
BROWSER_OPTIONS = {
    "headless_args": [
        "--headless",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--window-size=1920,1080"
    ],
    "common_args": [
        "--inprivate",
        "--disable-blink-features=AutomationControlled",
        "--disable-application-cache",
        "--disable-background-sync",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-backgrounding-occluded-windows",
        "--start-maximized",
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
    ],
    "experimental_options": {
        "excludeSwitches": ["enable-automation"],
        "useAutomationExtension": False
    }
}

# 密码生成配置
PASSWORD_CONFIG = {
    "length": 12,
    "characters": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*",
    "required_types": {
        "lowercase": "abcdefghijklmnopqrstuvwxyz",
        "uppercase": "ABCDEFGHIJKLMNOPQRSTUVWXYZ", 
        "digits": "0123456789",
        "special": "!@#$%^&*"
    }
}

# 日志配置
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
