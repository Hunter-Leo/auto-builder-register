#!/usr/bin/env python3
"""
Test refactored AWS Builder module
Verify that all components work properly
"""

import sys
import os
sys.path.append('./src')

def test_imports():
    """Test module imports"""
    print("Testing module imports...")
    
    try:
        from auto_update_q.aws_builder import AWSBuilder, AWSBuilderCredentials
        print("✓ Main module imported successfully")
        
        from auto_update_q.aws_builder.config import DEFAULT_TIMEOUT, BROWSER_OPTIONS
        print("✓ Config module imported successfully")
        
        from auto_update_q.aws_builder.browser_manager import BrowserManager
        print("✓ Browser manager imported successfully")
        
        from auto_update_q.aws_builder.element_waiter import ElementWaiter
        print("✓ Element waiter imported successfully")
        
        from auto_update_q.aws_builder.form_handler import FormHandler
        print("✓ Form handler imported successfully")
        
        from auto_update_q.aws_builder.captcha_handler import CaptchaHandler
        print("✓ Captcha handler imported successfully")
        
        from auto_update_q.aws_builder.registration_checker import RegistrationChecker
        print("✓ Registration checker imported successfully")
        
        from auto_update_q.aws_builder.optimized_selectors import get_selector, get_timeout
        print("✓ Selector configuration imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_configuration():
    """Test configuration"""
    print("\nTesting configuration...")
    
    try:
        from auto_update_q.aws_builder.config import DEFAULT_TIMEOUT, BROWSER_OPTIONS, PASSWORD_CONFIG
        
        assert DEFAULT_TIMEOUT > 0, "Default timeout should be greater than 0"
        assert isinstance(BROWSER_OPTIONS, dict), "Browser options should be a dictionary"
        assert isinstance(PASSWORD_CONFIG, dict), "Password config should be a dictionary"
        
        print("✓ Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_selectors():
    """Test selector configuration"""
    print("\nTesting selector configuration...")
    
    try:
        from auto_update_q.aws_builder.optimized_selectors import (
            get_selector, get_timeout, get_retry_config, OPTIMIZED_SELECTORS
        )
        
        # Test getting selectors
        email_selectors = get_selector("email_input")
        assert isinstance(email_selectors, list), "Selector should return a list"
        assert len(email_selectors) > 0, "Should have at least one email selector"
        
        # Test getting timeout configuration
        timeout = get_timeout("email_input")
        assert isinstance(timeout, int), "Timeout should be an integer"
        assert timeout > 0, "Timeout should be greater than 0"
        
        # Test getting retry configuration
        retry_config = get_retry_config("email_input", "max_rounds", 3)
        assert isinstance(retry_config, int), "Retry config should be an integer"
        
        print("✓ Selector configuration validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Selector test failed: {e}")
        return False


def test_credentials_dataclass():
    """Test credentials dataclass"""
    print("\nTesting credentials dataclass...")
    
    try:
        from auto_update_q.aws_builder import AWSBuilderCredentials
        
        # Create credentials instance
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
        
        print("✓ Credentials dataclass validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Credentials dataclass test failed: {e}")
        return False


def test_aws_builder_initialization():
    """Test AWSBuilder initialization"""
    print("\nTesting AWSBuilder initialization...")
    
    try:
        from auto_update_q.aws_builder import AWSBuilder
        
        # Test default parameter initialization
        aws_builder = AWSBuilder()
        assert aws_builder.headless == False
        assert aws_builder.timeout == 30
        assert aws_builder.debug == False
        assert aws_builder.keep_browser == False
        
        # Test custom parameter initialization
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
        
        print("✓ AWSBuilder initialization validation passed")
        return True
        
    except Exception as e:
        print(f"✗ AWSBuilder initialization test failed: {e}")
        return False


def test_password_generation():
    """Test password generation"""
    print("\nTesting password generation...")
    
    try:
        from auto_update_q.aws_builder.form_handler import FormHandler
        from auto_update_q.aws_builder.element_waiter import ElementWaiter
        
        # Create a mock FormHandler to test password generation
        # Note: We only test password generation logic here, no real driver needed
        class MockDriver:
            pass
        
        class MockElementWaiter:
            pass
        
        form_handler = FormHandler(MockDriver(), MockElementWaiter())
        
        # Test password generation
        password = form_handler.generate_random_password()
        assert isinstance(password, str), "Password should be a string"
        assert len(password) >= 12, "Password length should be at least 12 characters"
        
        # Test custom length
        password2 = form_handler.generate_random_password(16)
        assert len(password2) == 16, "Custom length password should be 16 characters"
        
        print("✓ Password generation validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Password generation test failed: {e}")
        return False


def test_module_structure():
    """Test module structure"""
    print("\nTesting module structure...")
    
    try:
        import auto_update_q.aws_builder as aws_builder_module
        
        # Check if main classes exist
        assert hasattr(aws_builder_module, 'AWSBuilder'), "Should have AWSBuilder class"
        assert hasattr(aws_builder_module, 'AWSBuilderCredentials'), "Should have AWSBuilderCredentials class"
        
        # Check main methods of AWSBuilder class
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
            assert hasattr(aws_builder_class, method), f"AWSBuilder should have {method} method"
        
        print("✓ Module structure validation passed")
        return True
        
    except Exception as e:
        print(f"✗ Module structure test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("AWS Builder Refactored Version Test")
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
            print(f"✗ Test exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Refactoring successful!")
        return True
    else:
        print("❌ Some tests failed, need to fix")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
