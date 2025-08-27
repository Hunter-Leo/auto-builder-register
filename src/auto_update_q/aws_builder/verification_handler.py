#!/usr/bin/env python3
"""
专门处理AWS Builder ID验证码输入的模块
基于实际页面源码分析优化的验证码处理逻辑
集成DropMail自动获取验证码功能
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import re
from typing import Optional, Tuple
from ..temp_mail.dropmail import DropMail

class VerificationCodeHandler:
    """验证码处理器 - 集成自动邮件获取功能"""
    
    def __init__(self, driver: webdriver.Edge, dropmail: DropMail, logger: logging.Logger = None):
        self.driver = driver
        self.dropmail = dropmail
        self.logger = logger or logging.getLogger(__name__)
    
    def extract_verification_code(self, email_content: str) -> Optional[str]:
        """
        从邮件内容中提取验证码
        
        Args:
            email_content: 邮件内容
            
        Returns:
            str: 验证码，如果未找到则返回None
        """
        # 常见的验证码模式
        patterns = [
            r'verification code[:\s]+([A-Z0-9]{6})',  # verification code: XXXXXX
            r'code[:\s]+([A-Z0-9]{6})',  # code: XXXXXX
            r'([A-Z0-9]{6})',  # 6位大写字母数字组合
            r'(\d{6})',  # 6位数字
            r'([A-Z]{6})',  # 6位大写字母
        ]
        
        for pattern in patterns:
            match = re.search(pattern, email_content, re.IGNORECASE)
            if match:
                code = match.group(1)
                self.logger.info(f"提取到验证码: {code}")
                return code
        
        self.logger.warning("未能从邮件中提取验证码")
        return None
    
    def wait_for_verification_email(self, timeout: int = 300) -> Optional[str]:
        """
        等待并获取验证码邮件
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            str: 验证码，如果获取失败则返回None
        """
        self.logger.info(f"等待验证码邮件，超时时间: {timeout}秒")
        
        start_time = time.time()
        check_interval = 10  # 每10秒检查一次
        
        while time.time() - start_time < timeout:
            try:
                # 获取邮件
                mails = self.dropmail.get_mails()
                
                if mails:
                    self.logger.info(f"收到 {len(mails)} 封邮件")
                    
                    # 查找AWS相关的验证邮件
                    for mail in mails:
                        # 检查发件人和主题
                        if any(keyword in mail.from_addr.lower() for keyword in ['aws', 'amazon', 'no-reply']):
                            self.logger.info(f"找到AWS验证邮件: {mail.subject}")
                            
                            # 提取验证码
                            verification_code = self.extract_verification_code(mail.text or mail.html or "")
                            if verification_code:
                                return verification_code
                        
                        # 也检查主题中是否包含验证相关关键词
                        if any(keyword in mail.subject.lower() for keyword in ['verification', 'verify', 'code', 'confirm']):
                            self.logger.info(f"找到验证邮件: {mail.subject}")
                            
                            # 提取验证码
                            verification_code = self.extract_verification_code(mail.text or mail.html or "")
                            if verification_code:
                                return verification_code
                
                # 等待一段时间后再次检查
                self.logger.info(f"暂未收到验证邮件，{check_interval}秒后重试...")
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"检查邮件时出错: {e}")
                time.sleep(check_interval)
        
        self.logger.error("等待验证码邮件超时")
        return None
    
    def find_verification_input(self, timeout: int = 10) -> Optional[webdriver.remote.webelement.WebElement]:
        """
        查找验证码输入框
        基于实际页面源码分析的选择器优先级 - 使用优化选择器
        """
        # 导入优化选择器
        from .optimized_selectors import get_all_selectors
        
        # 使用优化的验证码输入框选择器
        selectors = get_all_selectors('verification_input')
        
        # 如果没有找到优化选择器，使用备用选择器
        if not selectors:
            selectors = [
                "input[type='text'][autocomplete='on']",  # 成功的选择器
                "input.awsui_input_2rhyz_7gdci_149[type='text']",  # 基于实际class
                "input[id*='formField'][type='text']",  # 基于ID模式
                "input[aria-labelledby*='formField'][type='text']",  # 基于aria-labelledby
            ]
        
        for i, selector in enumerate(selectors, 1):
            try:
                self.logger.info(f"尝试选择器 {i}/{len(selectors)}: {selector}")
                
                # 等待元素出现
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                
                # 验证元素是否可见和可用
                if element.is_displayed() and element.is_enabled():
                    self.logger.info(f"✓ 找到可用的验证码输入框: {selector}")
                    self.logger.info(f"  元素ID: {element.get_attribute('id')}")
                    self.logger.info(f"  元素Class: {element.get_attribute('class')}")
                    return element
                else:
                    self.logger.info(f"  元素不可见或不可用")
                    
            except TimeoutException:
                self.logger.info(f"  选择器超时")
                continue
            except Exception as e:
                self.logger.info(f"  选择器异常: {e}")
                continue
        
        self.logger.error("未找到可用的验证码输入框")
        return None
    
    def input_verification_code(self, code: str, max_retries: int = 3) -> bool:
        """
        输入验证码
        
        Args:
            code: 验证码
            max_retries: 最大重试次数
            
        Returns:
            bool: 是否输入成功
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"第 {attempt + 1} 次尝试输入验证码: {code}")
                
                # 查找输入框
                input_element = self.find_verification_input()
                if not input_element:
                    self.logger.error("未找到验证码输入框")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return False
                
                # 清空输入框
                input_element.clear()
                time.sleep(0.5)
                
                # 输入验证码
                input_element.send_keys(code)
                time.sleep(0.5)
                
                # 验证输入是否成功
                actual_value = input_element.get_attribute('value')
                if actual_value == code:
                    self.logger.info(f"✓ 验证码输入成功: {actual_value}")
                    return True
                else:
                    self.logger.warning(f"验证码输入不匹配: 期望 {code}, 实际 {actual_value}")
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return False
                    
            except Exception as e:
                self.logger.error(f"输入验证码异常: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return False
        
        return False
    
    def find_verify_button(self, timeout: int = 10) -> Optional[webdriver.remote.webelement.WebElement]:
        """
        查找验证按钮
        基于实际页面源码分析 - 使用优化选择器
        """
        # 导入优化选择器
        from .optimized_selectors import get_all_selectors
        
        # 使用优化的验证按钮选择器
        selectors = get_all_selectors('verification_verify_button')
        
        # 如果没有找到优化选择器，使用备用选择器
        if not selectors:
            selectors = [
                "button[data-testid='email-verification-verify-button']",  # 精确的测试ID
                "button._2xAbzS8kNKd3Tl_k7Hlfav.awsui_variant-primary_vjswe_gmc8h_231",  # 完整class组合
                "button[type='submit'][class*='primary']",  # 备用选择器
            ]
        
        for i, selector in enumerate(selectors, 1):
            try:
                self.logger.info(f"尝试验证按钮选择器 {i}/{len(selectors)}: {selector}")
                
                element = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                
                if element.is_displayed() and element.is_enabled():
                    self.logger.info(f"✓ 找到可用的验证按钮: {selector}")
                    self.logger.info(f"  按钮文本: {element.text}")
                    self.logger.info(f"  按钮Class: {element.get_attribute('class')}")
                    return element
                    
            except TimeoutException:
                self.logger.info(f"  选择器超时")
                continue
            except Exception as e:
                self.logger.info(f"  按钮选择器异常: {e}")
                continue
        
        self.logger.error("未找到可用的验证按钮")
        return None
    
    def click_verify_button(self, max_retries: int = 3) -> bool:
        """
        点击验证按钮
        
        Args:
            max_retries: 最大重试次数
            
        Returns:
            bool: 是否点击成功
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"第 {attempt + 1} 次尝试点击验证按钮")
                
                verify_button = self.find_verify_button()
                if not verify_button:
                    self.logger.error("未找到验证按钮")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                        continue
                    return False
                
                # 点击按钮
                verify_button.click()
                self.logger.info("✓ 验证按钮点击成功")
                return True
                
            except Exception as e:
                self.logger.error(f"点击验证按钮异常: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return False
        
        return False
    
    def handle_verification_process_auto(self, email_timeout: int = 300) -> bool:
        """
        自动处理验证码流程 - 自动获取邮件中的验证码
        
        Args:
            email_timeout: 等待邮件的超时时间（秒）
            
        Returns:
            bool: 是否处理成功
        """
        self.logger.info("开始自动验证码处理流程")
        
        # 自动等待并获取验证码
        verification_code = self.wait_for_verification_email(timeout=email_timeout)
        if not verification_code:
            self.logger.error("未能获取验证码")
            return False
        
        # 输入验证码
        if not self.input_verification_code(verification_code):
            self.logger.error("验证码输入失败")
            return False
        
        # 点击验证按钮
        if not self.click_verify_button():
            self.logger.error("验证按钮点击失败")
            return False
        
        self.logger.info("自动验证码处理完成")
        return True
    
    def handle_verification_process(self, code: str) -> bool:
        """
        手动验证码处理流程 - 使用提供的验证码
        
        Args:
            code: 验证码
            
        Returns:
            bool: 是否处理成功
        """
        self.logger.info(f"开始手动验证码处理: {code}")
        
        # 输入验证码
        if not self.input_verification_code(code):
            self.logger.error("验证码输入失败")
            return False
        
        # 点击验证按钮
        if not self.click_verify_button():
            self.logger.error("验证按钮点击失败")
            return False
        
        self.logger.info("手动验证码处理完成")
        return True
    
    def debug_page_elements(self):
        """调试页面元素，打印所有相关信息"""
        try:
            self.logger.info("=== 页面元素调试信息 ===")
            
            # 打印所有input元素
            all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
            self.logger.info(f"页面上共有 {len(all_inputs)} 个input元素:")
            
            for i, inp in enumerate(all_inputs):
                try:
                    self.logger.info(f"Input {i+1}:")
                    self.logger.info(f"  ID: {inp.get_attribute('id')}")
                    self.logger.info(f"  Class: {inp.get_attribute('class')}")
                    self.logger.info(f"  Type: {inp.get_attribute('type')}")
                    self.logger.info(f"  Name: {inp.get_attribute('name')}")
                    self.logger.info(f"  Autocomplete: {inp.get_attribute('autocomplete')}")
                    self.logger.info(f"  Spellcheck: {inp.get_attribute('spellcheck')}")
                    self.logger.info(f"  Aria-describedby: {inp.get_attribute('aria-describedby')}")
                    self.logger.info(f"  是否可见: {inp.is_displayed()}")
                    self.logger.info(f"  是否启用: {inp.is_enabled()}")
                    self.logger.info("")
                except:
                    continue
            
            # 打印所有button元素
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            self.logger.info(f"页面上共有 {len(all_buttons)} 个button元素:")
            
            for i, btn in enumerate(all_buttons):
                try:
                    self.logger.info(f"Button {i+1}:")
                    self.logger.info(f"  Class: {btn.get_attribute('class')}")
                    self.logger.info(f"  Type: {btn.get_attribute('type')}")
                    self.logger.info(f"  Data-testid: {btn.get_attribute('data-testid')}")
                    self.logger.info(f"  Text: {btn.text}")
                    self.logger.info(f"  是否可见: {btn.is_displayed()}")
                    self.logger.info(f"  是否启用: {btn.is_enabled()}")
                    self.logger.info("")
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"调试页面元素失败: {e}")
