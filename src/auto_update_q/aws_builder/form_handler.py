"""
表单处理器
负责AWS Builder ID注册表单的填写逻辑
"""

import logging
import random
import string
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException

from .config import PASSWORD_CONFIG
from .element_waiter import ElementWaiter
from .optimized_selectors import get_selector


class FormHandler:
    """表单处理器"""
    
    def __init__(self, driver: webdriver.Edge, element_waiter: ElementWaiter, 
                 logger: Optional[logging.Logger] = None):
        """
        初始化表单处理器
        
        Args:
            driver: 浏览器驱动
            element_waiter: 元素等待器
            logger: 日志记录器
        """
        self.driver = driver
        self.element_waiter = element_waiter
        self.logger = logger or logging.getLogger(__name__)
    
    def fill_email_form(self, email: str) -> bool:
        """
        填写邮箱表单
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否成功填写
        """
        self.logger.info("开始填写邮箱表单...")
        
        # 等待邮箱输入框
        email_selectors = get_selector("email_input")
        email_input = self.element_waiter.wait_for_element_with_retry(
            email_selectors, "邮箱输入框"
        )
        
        if not email_input:
            self.logger.error("未找到邮箱输入框")
            return False
        
        # 填写邮箱
        try:
            self._fill_input_field(email_input, email, "邮箱")
            
            # 点击下一步按钮
            return self._click_next_button("email_next_button", "邮箱页面下一步按钮")
            
        except Exception as e:
            self.logger.error(f"填写邮箱时出错: {e}")
            return False
    
    def fill_name_form(self, name: str) -> bool:
        """
        填写姓名表单
        
        Args:
            name: 用户姓名
            
        Returns:
            是否成功填写
        """
        self.logger.info("开始填写姓名表单...")
        
        # 等待姓名输入框
        name_selectors = get_selector("name_input")
        name_input = self.element_waiter.wait_for_element_with_retry(
            name_selectors, "姓名输入框"
        )
        
        if not name_input:
            self.logger.error("未找到姓名输入框")
            return False
        
        # 填写姓名
        try:
            self._fill_input_field(name_input, name, "姓名")
            
            # 点击下一步按钮
            return self._click_next_button("name_next_button", "姓名页面下一步按钮")
            
        except Exception as e:
            self.logger.error(f"填写姓名时出错: {e}")
            return False
    
    def fill_password_form(self, password: Optional[str] = None) -> Optional[str]:
        """
        填写密码表单
        
        Args:
            password: 指定密码，如果为None则自动生成
            
        Returns:
            使用的密码，失败时返回None
        """
        self.logger.info("开始填写密码表单...")
        
        # 生成或使用指定密码
        if password is None:
            password = self.generate_random_password()
            self.logger.info("已生成随机密码")
        
        # 等待密码输入框
        password_selectors = get_selector("password_input")
        password_input = self.element_waiter.wait_for_element_with_retry(
            password_selectors, "密码输入框"
        )
        
        if not password_input:
            self.logger.error("未找到密码输入框")
            return None
        
        # 等待确认密码输入框
        confirm_selectors = get_selector("confirm_password_input")
        confirm_input = self.element_waiter.wait_for_element_with_retry(
            confirm_selectors, "确认密码输入框"
        )
        
        if not confirm_input:
            self.logger.error("未找到确认密码输入框")
            return None
        
        # 填写密码
        try:
            self._fill_input_field(password_input, password, "密码")
            self._fill_input_field(confirm_input, password, "确认密码")
            
            # 密码填写完成，返回密码（不点击下一步按钮，让用户手动处理图形验证码）
            self.logger.info("密码表单填写完成，等待用户手动处理图形验证码")
            return password
                
        except Exception as e:
            self.logger.error(f"填写密码时出错: {e}")
            return None
    
    def fill_verification_code(self, code: str) -> bool:
        """
        填写验证码
        
        Args:
            code: 验证码
            
        Returns:
            是否成功填写
        """
        self.logger.info("开始填写验证码...")
        
        # 等待验证码输入框
        code_selectors = get_selector("verification_code_input")
        code_input = self.element_waiter.wait_for_element_with_retry(
            code_selectors, "验证码输入框"
        )
        
        if not code_input:
            self.logger.error("未找到验证码输入框")
            return False
        
        # 填写验证码
        try:
            self._fill_input_field(code_input, code, "验证码")
            
            # 点击验证按钮
            return self._click_next_button("verify_button", "验证按钮")
            
        except Exception as e:
            self.logger.error(f"填写验证码时出错: {e}")
            return False
    
    def generate_random_password(self, length: Optional[int] = None) -> str:
        """
        生成随机密码
        
        Args:
            length: 密码长度
            
        Returns:
            生成的密码
        """
        length = length or PASSWORD_CONFIG["length"]
        
        # 确保密码包含所有必需的字符类型
        password_list = []
        
        # 每种类型至少包含一个字符
        for char_type, chars in PASSWORD_CONFIG["required_types"].items():
            password_list.append(random.choice(chars))
        
        # 填充剩余长度
        remaining_length = length - len(password_list)
        all_chars = PASSWORD_CONFIG["characters"]
        
        for _ in range(remaining_length):
            password_list.append(random.choice(all_chars))
        
        # 打乱顺序
        random.shuffle(password_list)
        
        return ''.join(password_list)
    
    def _fill_input_field(self, element, value: str, field_name: str) -> None:
        """
        填写输入字段的通用方法
        
        Args:
            element: 输入元素
            value: 要填写的值
            field_name: 字段名称（用于日志）
        """
        # 滚动到元素位置
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        
        # 等待元素可见和可交互
        self.element_waiter.wait_for_element_interactive(element)
        
        # 清空并填写
        element.clear()
        element.send_keys(value)
        self.logger.info(f"已填写{field_name}: {value if field_name != '密码' else '***'}")
    
    def _click_next_button(self, button_key: str, button_name: str) -> bool:
        """
        点击下一步按钮
        
        Args:
            button_key: 按钮选择器键名
            button_name: 按钮名称（用于日志）
            
        Returns:
            是否成功点击
        """
        button_selectors = get_selector(button_key)
        button = self.element_waiter.wait_for_clickable_with_retry(
            button_selectors, button_name
        )
        
        if not button:
            self.logger.error(f"未找到{button_name}")
            return False
        
        try:
            # 滚动到按钮位置
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            
            # 等待按钮可点击
            self.element_waiter.wait_for_element_interactive(button)
            
            # 点击按钮
            button.click()
            self.logger.info(f"已点击{button_name}")
            
            # 等待页面响应
            return self.element_waiter.wait_for_page_change()
            
        except Exception as e:
            self.logger.error(f"点击{button_name}时出错: {e}")
            return False
