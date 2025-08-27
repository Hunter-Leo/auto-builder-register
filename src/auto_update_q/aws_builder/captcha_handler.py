"""
验证码处理器
负责处理图形验证码和邮箱验证码
"""

import logging
import time
import re
from typing import Optional, Tuple
from selenium import webdriver

from .element_waiter import ElementWaiter
from .optimized_selectors import get_selector


class CaptchaHandler:
    """验证码处理器"""
    
    def __init__(self, driver: webdriver.Edge, element_waiter: ElementWaiter,
                 logger: Optional[logging.Logger] = None):
        """
        初始化验证码处理器
        
        Args:
            driver: 浏览器驱动
            element_waiter: 元素等待器
            logger: 日志记录器
        """
        self.driver = driver
        self.element_waiter = element_waiter
        self.logger = logger or logging.getLogger(__name__)
    
    def check_image_captcha_exists(self) -> bool:
        """
        检查是否存在图形验证码（不进行交互）
        
        Returns:
            是否存在图形验证码
        """
        self.logger.info("检查是否存在图形验证码...")
        
        # 检查验证码容器
        captcha_selectors = get_selector("captcha_container")
        captcha_container = self.element_waiter.wait_for_element_with_retry(
            captcha_selectors, "验证码容器", max_rounds=2, timeout_per_selector=3
        )
        
        if captcha_container:
            self.logger.info("检测到图形验证码")
            return True
        else:
            self.logger.info("未检测到图形验证码")
            return False
    
    def handle_image_captcha(self) -> bool:
        """
        处理图形验证码（手动输入）
        
        Returns:
            是否成功处理验证码
        """
        self.logger.info("检查是否存在图形验证码...")
        
        # 检查验证码容器
        captcha_selectors = get_selector("captcha_container")
        captcha_container = self.element_waiter.wait_for_element_with_retry(
            captcha_selectors, "验证码容器", max_rounds=2, timeout_per_selector=3
        )
        
        if not captcha_container:
            self.logger.info("未检测到图形验证码")
            return True
        
        self.logger.info("检测到图形验证码，需要手动输入")
        
        # 查找验证码输入框
        captcha_input_selectors = get_selector("captcha_input")
        captcha_input = self.element_waiter.wait_for_element_with_retry(
            captcha_input_selectors, "验证码输入框"
        )
        
        if not captcha_input:
            self.logger.error("未找到验证码输入框")
            return False
        
        # 提示用户手动输入
        print("\n" + "="*50)
        print("检测到图形验证码，请手动输入：")
        print("1. 查看浏览器中的验证码图片")
        print("2. 在下方输入验证码")
        print("="*50)
        
        # 等待用户输入
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                captcha_code = input(f"请输入验证码 (尝试 {attempt + 1}/{max_attempts}): ").strip()
                
                if not captcha_code:
                    print("验证码不能为空，请重新输入")
                    continue
                
                # 填写验证码
                captcha_input.clear()
                captcha_input.send_keys(captcha_code)
                self.logger.info(f"已输入验证码: {captcha_code}")
                
                # 点击提交按钮
                if self._submit_captcha():
                    # 等待验证结果
                    if self._wait_for_captcha_result():
                        self.logger.info("验证码验证成功")
                        return True
                    else:
                        print(f"验证码错误，请重试 (剩余 {max_attempts - attempt - 1} 次)")
                        continue
                else:
                    print("提交验证码失败，请重试")
                    continue
                    
            except KeyboardInterrupt:
                self.logger.info("用户取消验证码输入")
                return False
            except Exception as e:
                self.logger.error(f"处理验证码时出错: {e}")
                print(f"处理验证码时出错: {e}")
                continue
        
        self.logger.error("验证码验证失败，已达到最大尝试次数")
        return False
    
    def extract_verification_code_from_email(self, email_content: str) -> Optional[str]:
        """
        从邮件内容中提取验证码
        
        Args:
            email_content: 邮件内容
            
        Returns:
            提取到的验证码，如果未找到则返回None
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
                self.logger.info(f"从邮件中提取到验证码: {code}")
                return code
        
        self.logger.warning("未能从邮件中提取到验证码")
        return None
    
    def wait_for_email_verification_code(self, dropmail=None, timeout: int = 300) -> Optional[str]:
        """
        等待邮箱验证码
        
        Args:
            dropmail: DropMail实例，如果提供则自动获取验证码
            timeout: 超时时间（秒）
            
        Returns:
            验证码，如果获取失败则返回None
        """
        if dropmail:
            return self._auto_get_verification_code(dropmail, timeout)
        else:
            return self._manual_get_verification_code()
    
    def _auto_get_verification_code(self, dropmail, timeout: int) -> Optional[str]:
        """自动从邮箱获取验证码，支持超时自动刷新"""
        self.logger.info("等待邮箱验证码...")
        
        max_attempts = 3  # 最多尝试3次
        wait_time_per_attempt = 10  # 每次等待10秒
        
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"第 {attempt + 1} 次尝试获取验证码...")
                
                # 等待新邮件（每次等待10秒）
                new_mail = dropmail.wait_for_mail(timeout=wait_time_per_attempt)
                
                if new_mail:
                    # 提取验证码
                    verification_code = self.extract_verification_code_from_email(new_mail.text)
                    if verification_code:
                        self.logger.info(f"自动获取到验证码: {verification_code}")
                        return verification_code
                    else:
                        self.logger.warning("邮件中未找到验证码，继续等待...")
                else:
                    # 超时未收到邮件，尝试重发验证码
                    if attempt < max_attempts - 1:  # 不是最后一次尝试
                        self.logger.info(f"等待 {wait_time_per_attempt} 秒未收到验证码，尝试重发...")
                        if self._resend_verification_code():
                            self.logger.info("已重发验证码，继续等待...")
                            continue
                        else:
                            self.logger.warning("重发验证码失败，继续等待...")
                    else:
                        self.logger.error("最后一次尝试仍未收到验证邮件")
                        
            except Exception as e:
                self.logger.error(f"第 {attempt + 1} 次尝试获取验证码时出错: {e}")
                if attempt < max_attempts - 1:
                    continue
        
        self.logger.error("所有尝试均失败，无法获取验证码")
        return None
    
    def _resend_verification_code(self) -> bool:
        """重发验证码"""
        try:
            from .optimized_selectors import get_selector
            
            self.logger.info("尝试查找重发验证码按钮...")
            
            # 查找重发按钮
            resend_selectors = get_selector("resend_code_button")
            self.logger.debug(f"使用选择器: {resend_selectors}")
            
            # 尝试每个选择器
            resend_button = None
            for i, selector in enumerate(resend_selectors):
                try:
                    self.logger.debug(f"尝试选择器 {i+1}: {selector}")
                    elements = self.driver.find_elements("css selector", selector)
                    if elements:
                        resend_button = elements[0]
                        self.logger.info(f"✓ 找到重发按钮，使用选择器: {selector}")
                        break
                    else:
                        self.logger.debug(f"选择器 {selector} 未找到元素")
                except Exception as e:
                    self.logger.debug(f"选择器 {selector} 出错: {e}")
                    continue
            
            if not resend_button:
                self.logger.warning("未找到重发验证码按钮")
                # 打印当前页面的按钮信息用于调试
                try:
                    buttons = self.driver.find_elements("css selector", "button")
                    self.logger.debug(f"页面上共找到 {len(buttons)} 个按钮")
                    for i, btn in enumerate(buttons[:5]):  # 只显示前5个
                        try:
                            test_id = btn.get_attribute("data-testid") or "无"
                            text = btn.text or "无文本"
                            self.logger.debug(f"按钮 {i+1}: data-testid='{test_id}', text='{text}'")
                        except:
                            pass
                except:
                    pass
                return False
            
            # 检查按钮是否可点击
            if not resend_button.is_enabled():
                self.logger.warning("重发按钮不可点击")
                return False
            
            # 滚动到按钮位置
            self.driver.execute_script("arguments[0].scrollIntoView(true);", resend_button)
            
            # 点击重发按钮
            resend_button.click()
            self.logger.info("✓ 已点击重发验证码按钮")
            
            # 等待一下让请求发送
            import time
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"重发验证码时出错: {e}")
            return False
    
    def _manual_get_verification_code(self) -> Optional[str]:
        """手动输入验证码"""
        print("\n" + "="*50)
        print("请检查您的邮箱并输入验证码：")
        print("1. 查看邮箱中的验证邮件")
        print("2. 在下方输入6位验证码")
        print("="*50)
        
        try:
            verification_code = input("请输入邮箱验证码: ").strip()
            if len(verification_code) == 6 and verification_code.isalnum():
                self.logger.info(f"手动输入验证码: {verification_code}")
                return verification_code
            else:
                self.logger.error("验证码格式不正确，应为6位字母数字组合")
                return None
        except KeyboardInterrupt:
            self.logger.info("用户取消验证码输入")
            return None
    
    def _submit_captcha(self) -> bool:
        """提交验证码"""
        submit_selectors = get_selector("captcha_submit")
        submit_button = self.element_waiter.wait_for_clickable_with_retry(
            submit_selectors, "验证码提交按钮"
        )
        
        if not submit_button:
            self.logger.error("未找到验证码提交按钮")
            return False
        
        try:
            submit_button.click()
            self.logger.info("已提交验证码")
            return True
        except Exception as e:
            self.logger.error(f"提交验证码时出错: {e}")
            return False
    
    def _wait_for_captcha_result(self, timeout: int = 10) -> bool:
        """等待验证码验证结果"""
        self.logger.info("等待验证码验证结果...")
        
        # 检查错误提示和成功指标
        error_selectors = get_selector("captcha_error")
        
        # 使用动态等待检查结果
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 检查是否有错误提示
            error_element = self.element_waiter.wait_for_any_element(error_selectors, timeout=1)
            if error_element and error_element.is_displayed():
                self.logger.info("验证码验证失败")
                return False
            
            # 检查是否验证成功（验证码容器消失或页面跳转）
            current_url = self.driver.current_url
            if "captcha" not in current_url.lower():
                self.logger.info("验证码验证成功，页面已跳转")
                return True
            
            # 检查页面是否有变化
            if self.element_waiter.wait_for_page_change(timeout=1):
                self.logger.info("验证码验证成功，页面已变化")
                return True
        
        self.logger.warning("等待验证码结果超时")
        return False
