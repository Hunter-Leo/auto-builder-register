#!/usr/bin/env python3
"""
测试重构后的AWS Builder模块
验证各个组件是否正常工作
"""

import sys
import os
sys.path.append('./src')

def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        from auto_update_q.aws_builder import AWSBuilder, AWSBuilderCredentials
        print("✓ 主模块导入成功")
        
        from auto_update_q.aws_builder.config import DEFAULT_TIMEOUT, BROWSER_OPTIONS
        print("✓ 配置模块导入成功")
        
        from auto_update_q.aws_builder.browser_manager import BrowserManager
        print("✓ 浏览器管理器导入成功")
        
        from auto_update_q.aws_builder.element_waiter import ElementWaiter
        print("✓ 元素等待器导入成功")
        
        from auto_update_q.aws_builder.form_handler import FormHandler
        print("✓ 表单处理器导入成功")
        
        from auto_update_q.aws_builder.captcha_handler import CaptchaHandler
        print("✓ 验证码处理器导入成功")
        
        from auto_update_q.aws_builder.registration_checker import RegistrationChecker
        print("✓ 注册检查器导入成功")
        
        from auto_update_q.aws_builder.optimized_selectors import get_selector, get_timeout
        print("✓ 选择器配置导入成功")
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_configuration():
    """测试配置"""
    print("\n测试配置...")
    
    try:
        from auto_update_q.aws_builder.config import DEFAULT_TIMEOUT, BROWSER_OPTIONS, PASSWORD_CONFIG
        
        assert DEFAULT_TIMEOUT > 0, "默认超时时间应大于0"
        assert isinstance(BROWSER_OPTIONS, dict), "浏览器选项应为字典"
        assert isinstance(PASSWORD_CONFIG, dict), "密码配置应为字典"
        
        print("✓ 配置验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        return False


def test_selectors():
    """测试选择器配置"""
    print("\n测试选择器配置...")
    
    try:
        from auto_update_q.aws_builder.optimized_selectors import (
            get_selector, get_timeout, get_retry_config, OPTIMIZED_SELECTORS
        )
        
        # 测试获取选择器
        email_selectors = get_selector("email_input")
        assert isinstance(email_selectors, list), "选择器应返回列表"
        assert len(email_selectors) > 0, "应有至少一个邮箱选择器"
        
        # 测试获取超时配置
        timeout = get_timeout("email_input")
        assert isinstance(timeout, int), "超时时间应为整数"
        assert timeout > 0, "超时时间应大于0"
        
        # 测试获取重试配置
        retry_config = get_retry_config("email_input", "max_rounds", 3)
        assert isinstance(retry_config, int), "重试配置应为整数"
        
        print("✓ 选择器配置验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 选择器测试失败: {e}")
        return False


def test_credentials_dataclass():
    """测试凭证数据类"""
    print("\n测试凭证数据类...")
    
    try:
        from auto_update_q.aws_builder import AWSBuilderCredentials
        
        # 创建凭证实例
        credentials = AWSBuilderCredentials(
            email="test@example.com",
            password="password123",
            name="Test User",
            builder_id="test-id"
        )
        
        assert credentials.email == "test@example.com"
        assert credentials.password == "password123"
        assert credentials.name == "Test User"
        assert credentials.builder_id == "test-id"
        
        print("✓ 凭证数据类验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 凭证数据类测试失败: {e}")
        return False


def test_aws_builder_initialization():
    """测试AWSBuilder初始化"""
    print("\n测试AWSBuilder初始化...")
    
    try:
        from auto_update_q.aws_builder import AWSBuilder
        
        # 测试默认参数初始化
        aws_builder = AWSBuilder()
        assert aws_builder.headless == False
        assert aws_builder.timeout == 30
        assert aws_builder.debug == False
        assert aws_builder.keep_browser == False
        
        # 测试自定义参数初始化
        aws_builder2 = AWSBuilder(
            headless=True,
            timeout=60,
            debug=True,
            keep_browser=True
        )
        assert aws_builder2.headless == True
        assert aws_builder2.timeout == 60
        assert aws_builder2.debug == True
        assert aws_builder2.keep_browser == True
        
        print("✓ AWSBuilder初始化验证通过")
        return True
        
    except Exception as e:
        print(f"✗ AWSBuilder初始化测试失败: {e}")
        return False


def test_password_generation():
    """测试密码生成"""
    print("\n测试密码生成...")
    
    try:
        from auto_update_q.aws_builder.form_handler import FormHandler
        from auto_update_q.aws_builder.element_waiter import ElementWaiter
        
        # 创建一个模拟的FormHandler来测试密码生成
        # 注意：这里我们只测试密码生成逻辑，不需要真实的driver
        class MockDriver:
            pass
        
        class MockElementWaiter:
            pass
        
        form_handler = FormHandler(MockDriver(), MockElementWaiter())
        
        # 测试密码生成
        password = form_handler.generate_random_password()
        assert isinstance(password, str), "密码应为字符串"
        assert len(password) >= 12, "密码长度应至少12位"
        
        # 测试自定义长度
        password2 = form_handler.generate_random_password(16)
        assert len(password2) == 16, "自定义长度密码应为16位"
        
        print("✓ 密码生成验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 密码生成测试失败: {e}")
        return False


def test_module_structure():
    """测试模块结构"""
    print("\n测试模块结构...")
    
    try:
        import auto_update_q.aws_builder as aws_builder_module
        
        # 检查主要类是否存在
        assert hasattr(aws_builder_module, 'AWSBuilder'), "应有AWSBuilder类"
        assert hasattr(aws_builder_module, 'AWSBuilderCredentials'), "应有AWSBuilderCredentials类"
        
        # 检查AWSBuilder类的主要方法
        aws_builder_class = aws_builder_module.AWSBuilder
        required_methods = [
            'register_aws_builder',
            'navigate_to_url',
            'get_current_url',
            'get_page_title',
            'close',
            '__enter__',
            '__exit__'
        ]
        
        for method in required_methods:
            assert hasattr(aws_builder_class, method), f"AWSBuilder应有{method}方法"
        
        print("✓ 模块结构验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 模块结构测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("AWS Builder 重构版本测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_selectors,
        test_credentials_dataclass,
        test_aws_builder_initialization,
        test_password_generation,
        test_module_structure,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ 测试异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！重构成功！")
        return True
    else:
        print("❌ 部分测试失败，需要修复")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
