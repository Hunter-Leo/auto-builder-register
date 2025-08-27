"""
AWS Builder ID 自动注册模块

该模块提供自动注册 AWS Builder ID 账号的功能，支持：
- 自动填写注册表单
- 处理邮箱验证
- 处理图形验证码（手动输入）
- 会话管理
- 返回登录凭证
"""

import logging
import time
import random
import string
from typing import Optional, Dict, Any
from dataclasses import dataclass

from selenium import webdriver
from .optimized_selectors import (
    get_selector, get_all_selectors, get_timeout, get_retry_config
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from datetime import datetime


@dataclass
class AWSBuilderCredentials:
    """AWS Builder ID 登录凭证"""
    email: str
    password: str
    name: str
    builder_id: Optional[str] = None


class AWSBuilder:
    """AWS Builder ID 自动注册器"""
    
    def __init__(self, headless: bool = False, timeout: int = 30, debug: bool = False, keep_browser: bool = False):
        """
        初始化 AWS Builder 注册器
        
        Args:
            headless: 是否使用无头模式
            timeout: 等待超时时间（秒）
            debug: 是否启用调试模式
            keep_browser: 是否在结束后保持浏览器打开
        """
        self.headless = headless
        self.timeout = timeout
        self.debug = debug
        self.keep_browser = keep_browser
        self.debug = debug
        self.driver: Optional[webdriver.Edge] = None
        self.logger = logging.getLogger(__name__)
        
        # 配置日志
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _setup_driver(self) -> webdriver.Edge:
        """设置 Edge 浏览器驱动"""
        self.logger.info("正在设置 Edge 浏览器驱动...")
        
        options = EdgeOptions()
        if self.headless:
            options.add_argument("--headless")
        
        # 启用隐私浏览模式（InPrivate）
        options.add_argument("--inprivate")
        
        # 添加反检测选项
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 添加一些常用选项
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        # 禁用缓存和存储
        options.add_argument("--disable-application-cache")
        options.add_argument("--disable-background-sync")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-backgrounding-occluded-windows")
        
        # 设置更真实的用户代理
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0")
        
        try:
            # 首先尝试使用系统已安装的 Edge 驱动
            try:
                self.logger.info("尝试使用系统 Edge 驱动（隐私模式）...")
                driver = webdriver.Edge(options=options)
                driver.implicitly_wait(10)
                
                # 执行反检测脚本
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                self.logger.info("使用系统 Edge 驱动成功（隐私模式）")
                return driver
            except Exception as e:
                self.logger.info(f"系统 Edge 驱动不可用: {e}")
            
            # 如果系统驱动不可用，尝试使用 WebDriver Manager
            self.logger.info("尝试使用 WebDriver Manager 下载驱动（隐私模式）...")
            service = EdgeService(EdgeChromiumDriverManager().install())
            driver = webdriver.Edge(service=service, options=options)
            driver.implicitly_wait(10)
            
            # 执行反检测脚本
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("WebDriver Manager 设置成功（隐私模式）")
            return driver
            
        except Exception as e:
            self.logger.error(f"设置 Edge 浏览器驱动失败: {e}")
            self.logger.error("请确保：")
            self.logger.error("1. 已安装 Microsoft Edge 浏览器")
            self.logger.error("2. 网络连接正常")
            self.logger.error("3. 或手动下载 EdgeDriver 并添加到 PATH")
            raise
    
    def _wait_for_element_with_retry(self, selectors: list, element_name: str, max_rounds: int = None, timeout_per_selector: int = None) -> Any:
        """
        使用优化配置的多轮重试等待元素
        
        Args:
            selectors: 选择器列表
            element_name: 元素名称（用于日志）
            max_rounds: 最大重试轮数（None时使用优化配置）
            timeout_per_selector: 每个选择器的超时时间（None时使用优化配置）
            
        Returns:
            找到的元素或None
        """
        if max_rounds is None:
            max_rounds = get_retry_config()['max_rounds']
        if timeout_per_selector is None:
            timeout_per_selector = get_timeout('element_wait')
            
        for round_num in range(1, max_rounds + 1):
            self.logger.info(f"第 {round_num} 轮尝试查找{element_name}...")
            
            for selector in selectors:
                try:
                    self.logger.info(f"尝试选择器: {selector}")
                    element = self._wait_for_element(By.CSS_SELECTOR, selector, timeout=timeout_per_selector)
                    if element:
                        self.logger.info(f"找到{element_name}: {selector}")
                        return element
                    else:
                        self.logger.info(f"选择器 {selector} 未找到元素")
                except Exception as e:
                    self.logger.info(f"选择器 {selector} 出现异常: {e}")
                    continue
            
            if round_num < max_rounds:
                retry_delay = get_retry_config()['retry_delay']
                self.logger.info(f"第 {round_num} 轮未找到{element_name}，{retry_delay}秒后重试...")
                time.sleep(retry_delay)
        
        self.logger.error(f"经过 {max_rounds} 轮尝试仍未找到{element_name}")
        return None
    
    def _wait_for_clickable_with_retry(self, selectors: list, element_name: str, max_rounds: int = 3, timeout_per_selector: int = 3) -> Any:
        """
        使用多个选择器等待可点击元素，支持多轮重试
        
        Args:
            selectors: 选择器列表
            element_name: 元素名称（用于日志）
            max_rounds: 最大重试轮数
            timeout_per_selector: 每个选择器的超时时间
            
        Returns:
            找到的元素或None
        """
        for round_num in range(1, max_rounds + 1):
            self.logger.info(f"第 {round_num} 轮尝试查找{element_name}...")
            
            for selector in selectors:
                try:
                    self.logger.info(f"尝试选择器: {selector}")
                    element = self._wait_for_clickable(By.CSS_SELECTOR, selector, timeout=timeout_per_selector)
                    if element:
                        self.logger.info(f"找到{element_name}: {selector}")
                        return element
                    else:
                        self.logger.info(f"选择器 {selector} 未找到元素")
                except Exception as e:
                    self.logger.info(f"选择器 {selector} 出现异常: {e}")
                    continue
            
            if round_num < max_rounds:
                self.logger.info(f"第 {round_num} 轮未找到{element_name}，等待后重试...")
                time.sleep(2)  # 轮次间等待
        
        self.logger.error(f"经过 {max_rounds} 轮尝试仍未找到{element_name}")
        return None

    def _wait_for_redirect(self, initial_url: str, max_wait: int = 30) -> bool:
        """
        动态等待页面重定向完成
        
        Args:
            initial_url: 初始URL
            max_wait: 最大等待时间（秒）
            
        Returns:
            bool: 是否成功重定向
        """
        self.logger.info("动态等待页面重定向...")
        start_time = time.time()
        last_url = initial_url
        stable_count = 0
        
        while time.time() - start_time < max_wait:
            current_url = self.driver.current_url
            
            # 如果URL发生变化，重置稳定计数
            if current_url != last_url:
                self.logger.info(f"URL变化: {current_url}")
                last_url = current_url
                stable_count = 0
            else:
                stable_count += 1
            
            # 如果URL稳定1秒且不是初始URL，认为重定向完成
            if stable_count >= 2 and current_url != initial_url:  # 2次检查 * 0.5秒 = 1秒稳定
                self.logger.info(f"重定向完成，最终URL: {current_url}")
                return True
            
            # 检查是否已经到达目标页面（包含Builder ID相关内容）
            if any(keyword in current_url.lower() for keyword in ['signin.aws', 'profile.aws', 'builder']):
                try:
                    # 检查页面是否包含预期内容
                    page_source = self.driver.page_source.lower()
                    if any(keyword in page_source for keyword in ['builder id', 'email', 'create', 'sign']):
                        self.logger.info("检测到目标页面内容，重定向完成")
                        return True
                except:
                    pass
            
            time.sleep(0.5)  # 每0.5秒检查一次
        
        self.logger.warning(f"重定向等待超时，当前URL: {self.driver.current_url}")
        return False
    
    def _generate_random_password(self, length: int = 12) -> str:
        """生成随机密码"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        # 确保密码包含大小写字母、数字和特殊字符
        password = (
            random.choice(string.ascii_lowercase) +
            random.choice(string.ascii_uppercase) +
            random.choice(string.digits) +
            random.choice("!@#$%^&*") +
            ''.join(random.choice(characters) for _ in range(length - 4))
        )
        # 打乱密码字符顺序
        password_list = list(password)
        random.shuffle(password_list)
        return ''.join(password_list)
    
    def _wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> Any:
        """等待元素出现"""
        wait_timeout = timeout or 10  # 减少默认超时时间
        try:
            element = WebDriverWait(self.driver, wait_timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            # 不抛出异常，返回None让调用者继续尝试其他选择器
            return None
    
    def _wait_for_clickable(self, by: By, value: str, timeout: Optional[int] = None) -> Any:
        """等待元素可点击"""
        wait_timeout = timeout or 10  # 减少默认超时时间
        try:
            element = WebDriverWait(self.driver, wait_timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            return element
        except TimeoutException:
            # 不抛出异常，返回None让调用者继续尝试其他选择器
            return None
    
    def _handle_captcha(self) -> bool:
        """处理图形验证码（基于实际监控数据）"""
        try:
            # 检查是否存在验证码图片
            captcha_selectors = [
                "img[data-testid='test-captcha-image']",
                "img[src*='opfcaptcha']",
                "img[src*='captcha']",
                "[data-testid='test-captcha']",
                ".captcha img"
            ]
            
            captcha_image = None
            for selector in captcha_selectors:
                try:
                    captcha_image = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if captcha_image:
                        self.logger.info(f"发现验证码图片: {selector}")
                        break
                except:
                    continue
            
            if not captcha_image:
                self.logger.info("未发现验证码，继续...")
                return True
            
            # 主动刷新验证码以获取更清晰的图片
            self.logger.info("主动刷新验证码...")
            refresh_selectors = [
                "button[data-testid='test-captcha-button-refresh']",
                "#captcha-refresh button",
                "button[id='captcha-refresh']",
                "[data-testid='test-captcha-button-refresh'] button"
            ]
            
            refresh_button = None
            for selector in refresh_selectors:
                try:
                    refresh_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if refresh_button:
                        self.logger.info(f"找到刷新按钮: {selector}")
                        break
                except:
                    continue
            
            if refresh_button:
                try:
                    refresh_button.click()
                    time.sleep(1)  # 减少等待时间，验证码刷新很快
                    self.logger.info("验证码已刷新")
                    
                    # 重新获取验证码图片URL
                    captcha_image = self.driver.find_element(By.CSS_SELECTOR, captcha_selectors[0])
                except Exception as e:
                    self.logger.warning(f"刷新验证码失败: {e}")
            
            # 获取验证码图片URL
            captcha_src = captcha_image.get_attribute("src")
            self.logger.info(f"验证码图片URL: {captcha_src}")
            
            print("\n" + "="*50)
            print("检测到图形验证码！")
            print(f"验证码图片URL: {captcha_src}")
            print("验证码已自动刷新，请在浏览器中查看并手动输入")
            print("注意：请确保验证码输入正确，避免'Invalid captcha'错误")
            print("如果验证码不清晰，可以点击刷新按钮获取新的验证码")
            print("="*50)
            
            # 获取用户输入的验证码
            captcha_code = input("请输入图形验证码: ")
            
            # 查找验证码输入框
            captcha_input_selectors = [
                "input[data-testid='test-captcha-input'] input",
                "input[id*='captcha-input']",
                "input[class*='captcha']",
                "input[autocomplete='off'][type='text']"
            ]
            
            captcha_input = None
            for selector in captcha_input_selectors:
                try:
                    captcha_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if captcha_input:
                        self.logger.info(f"找到验证码输入框: {selector}")
                        break
                except:
                    continue
            
            if captcha_input:
                try:
                    # 确保输入框是可见和可交互的
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", captcha_input)
                    time.sleep(0.3)  # 减少等待时间
                    
                    # 清空输入框并输入验证码
                    captcha_input.clear()
                    time.sleep(0.2)  # 减少等待时间
                    captcha_input.send_keys(captcha_code)
                    time.sleep(0.2)  # 减少等待时间
                    
                    self.logger.info("已输入验证码")
                    return True
                except Exception as e:
                    self.logger.error(f"输入验证码时出错: {e}")
                    # 尝试使用JavaScript输入
                    try:
                        self.driver.execute_script("arguments[0].value = arguments[1];", captcha_input, captcha_code)
                        self.logger.info("使用JavaScript输入验证码成功")
                        return True
                    except Exception as js_error:
                        self.logger.error(f"JavaScript输入验证码也失败: {js_error}")
                        return False
            else:
                self.logger.error("无法找到验证码输入框")
                return False
            
        except Exception as e:
            self.logger.error(f"处理验证码时出错: {e}")
            return False
    
    def register_aws_builder(self, email: str, name: str = "Crazy Joe", password: str = None, dropmail: 'DropMail' = None) -> Optional[AWSBuilderCredentials]:
        """
        注册 AWS Builder ID 账号
        
        Args:
            email: 邮箱地址
            name: 用户姓名（默认：Crazy Joe）
            password: 密码（如果不提供则生成随机密码）
            dropmail: DropMail实例，用于自动获取验证码
            
        Returns:
            AWSBuilderCredentials: 注册成功的凭证信息
        """
        self.logger.info(f"开始注册 AWS Builder ID: {email}")
        
        try:
            # 设置浏览器驱动
            self.driver = self._setup_driver()
            
            # 生成或使用提供的密码
            if password is None:
                password = self._generate_password()
                self.logger.info("已生成随机密码")
            else:
                self.logger.info("使用提供的密码")
            
            # 显示账号信息
            self.logger.info("="*50)
            self.logger.info("注册账号信息:")
            self.logger.info(f"邮箱: {email}")
            self.logger.info(f"姓名: {name}")
            self.logger.info(f"密码: {password}")
            self.logger.info("="*50)
            
            # 访问注册页面
            self.logger.info("访问 AWS Profile 主页面...")
            initial_url = "https://profile.aws.amazon.com/"
            self.driver.get(initial_url)
            
            # 动态等待页面重定向完成 - 优化等待时间
            if not self._wait_for_redirect(initial_url, max_wait=30):  # 减少到30秒
                self.logger.warning("重定向可能未完成，但继续执行...")
            
            # 处理可能的 Cookie 同意弹窗 - 使用优化选择器
            try:
                cookie_selectors = get_all_selectors('cookie_accept')
                cookie_button = self._wait_for_element_with_retry(
                    cookie_selectors, "Cookie同意按钮", max_rounds=1, timeout_per_selector=2
                )
                
                if cookie_button:
                    self.logger.info("处理 Cookie 同意弹窗")
                    cookie_button.click()
                    time.sleep(get_timeout('input_delay'))
                else:
                    self.logger.info("未发现 Cookie 弹窗")
                    
            except Exception as e:
                self.logger.info(f"Cookie 弹窗处理异常: {e}")
            
            # 打印当前页面信息用于调试
            self.logger.info(f"当前页面URL: {self.driver.current_url}")
            self.logger.info(f"页面标题: {self.driver.title}")
            
            # 如果页面标题包含 "Create AWS Builder ID"，说明已经在正确页面
            # 智能检测当前页面状态并快速导航到邮箱输入页面
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            # 检查是否已经在正确的页面
            if any(keyword in page_source for keyword in ['create your aws builder id', 'email address', 'builder id']):
                self.logger.info("已经在 AWS Builder ID 创建页面")
            elif any(keyword in current_url for keyword in ['signin', 'profile', 'builder']):
                self.logger.info("尝试快速导航到创建页面...")
                # 使用更智能的等待策略，最多等待10秒
                try:
                    # 先尝试查找邮箱输入框，如果存在说明已经在正确页面
                    email_test = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
                    )
                    self.logger.info("检测到邮箱输入框，页面已就绪")
                except TimeoutException:
                    # 如果没有邮箱输入框，尝试查找创建按钮
                    self.logger.info("查找创建 Builder ID 的入口...")
                    create_selectors = [
                        "a[href*='create']",
                        "button[data-testid*='create']", 
                        "a[data-testid*='builder']",
                        "button:contains('Create')",
                        "a:contains('Builder')",
                        "[class*='create']"
                    ]
                    
                    create_button = None
                    for selector in create_selectors:
                        try:
                            create_button = WebDriverWait(self.driver, 1).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                            self.logger.info(f"找到创建入口: {selector}")
                            break
                        except TimeoutException:
                            continue
                    
                    if create_button:
                        create_button.click()
                        # 等待页面跳转，最多3秒
                        time.sleep(3)
                    else:
                        self.logger.info("未找到明确的创建入口，继续尝试邮箱输入")
            else:
                self.logger.warning("页面状态未知，直接尝试邮箱输入")
            
            # 尝试多种邮箱输入框选择器（基于成功的选择器优化顺序）
            # 使用优化的邮箱输入选择器
            email_selectors = get_all_selectors('email_input')
            
            email_input = self._wait_for_element_with_retry(
                selectors=email_selectors,
                element_name="邮箱输入框",
                max_rounds=2,  # 减少重试轮数
                timeout_per_selector=3  # 减少每个选择器的等待时间
            )
            
            if not email_input:
                self.logger.error("无法找到邮箱输入框，请检查页面结构")
                # 保存页面截图用于调试
                try:
                    self.driver.save_screenshot("debug_page.png")
                    self.logger.info("已保存页面截图到 debug_page.png")
                except:
                    pass
                
                if self.debug:
                    print("\n" + "="*50)
                    print("调试模式：无法找到邮箱输入框")
                    print("请在浏览器中手动检查页面")
                    print("="*50)
                    input("按 Enter 继续...")
                
                return None
            
            # 输入邮箱
            self.logger.info("输入邮箱地址...")
            email_input.clear()
            email_input.send_keys(email)
            time.sleep(get_timeout('input_delay'))
            
            # 使用优化的Next按钮选择器
            next_selectors = get_all_selectors('email_next_button')
            
            next_button = self._wait_for_clickable_with_retry(
                selectors=next_selectors,
                element_name="下一步按钮"
            )
            
            if not next_button:
                self.logger.error("无法找到下一步按钮")
                return None
                
            next_button.click()
            time.sleep(get_timeout('page_load'))
            
            time.sleep(1)  # 减少等待时间
            
            # 输入姓名（基于成功的选择器优化顺序）
            self.logger.info("输入用户姓名...")
            name_selectors = [
                "input[placeholder*='Maria José Silva']",  # 成功的选择器
                "input[data-testid='signup-full-name-input'] input",
                "input[aria-labelledby*='name']",
                "input[id*='formField'][type='text']:not([aria-labelledby*='email'])",
                "input[type='text'][autocomplete='on']:not([aria-labelledby*='email'])"
            ]
            
            name_input = self._wait_for_element_with_retry(
                selectors=name_selectors,
                element_name="姓名输入框",
                max_rounds=3,
                timeout_per_selector=3
            )
            
            if not name_input:
                self.logger.error("无法找到姓名输入框")
                return None
            
            name_input.clear()
            name_input.send_keys(name)
            
            # 点击下一步 - 使用姓名页面专用的Next按钮选择器
            name_next_selectors = get_all_selectors('name_next_button')
            next_button2 = self._wait_for_clickable_with_retry(
                selectors=name_next_selectors,
                element_name="第二个下一步按钮",
                max_rounds=3,
                timeout_per_selector=3
            )
            
            if not next_button2:
                self.logger.error("无法找到第二个下一步按钮")
                return None
                
            next_button2.click()
            
            time.sleep(2)
            
            # 处理邮箱验证 - 使用自动验证码获取
            self.logger.info("开始邮箱验证流程...")
            
            if dropmail:
                # 自动获取验证码
                self.logger.info("使用DropMail自动获取验证码...")
                from .verification_handler import VerificationCodeHandler
                verification_handler = VerificationCodeHandler(self.driver, dropmail, self.logger)
                
                # 使用自动验证码处理
                if verification_handler.handle_verification_process_auto(email_timeout=300):
                    self.logger.info("自动验证码处理成功")
                else:
                    self.logger.error("自动验证码处理失败")
                    # 调试页面元素
                    verification_handler.debug_page_elements()
                    return None
            else:
                # 手动输入验证码（保持向后兼容）
                print("\n" + "="*50)
                print("请检查邮箱获取验证码")
                print(f"邮箱: {email}")
                print("="*50)
                verification_code = input("请输入邮箱验证码: ")
                
                from .verification_handler import VerificationCodeHandler
                verification_handler = VerificationCodeHandler(self.driver, None, self.logger)
                
                # 使用手动验证码处理
                if verification_handler.handle_verification_process(verification_code):
                    self.logger.info("手动验证码处理成功")
                else:
                    self.logger.error("手动验证码处理失败")
                    # 调试页面元素
                    verification_handler.debug_page_elements()
                    return None
            
            # 设置密码（基于实际监控数据）
            self.logger.info("设置密码...")
            
            # 动态等待页面跳转到密码设置页面
            self.logger.info("等待页面跳转到密码设置页面...")
            password_page_ready = False
            max_wait = 10  # 最多等待10秒
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    # 检查是否有密码输入框出现
                    test_password = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                    if test_password.is_displayed():
                        self.logger.info("密码设置页面已就绪")
                        password_page_ready = True
                        break
                except:
                    pass
                time.sleep(0.5)
            
            if not password_page_ready:
                self.logger.warning("密码页面可能未完全加载，继续尝试...")
            
            # 使用优化的密码输入框选择器
            password_selectors = get_all_selectors('password_input')
            self.logger.info(f"使用优化配置中的密码选择器 ({len(password_selectors)} 个)")
            
            password_input = None
            for i, selector in enumerate(password_selectors, 1):
                try:
                    self.logger.info(f"尝试密码输入框选择器 {i}/{len(password_selectors)}: {selector}")
                    password_input = self._wait_for_element(By.CSS_SELECTOR, selector, timeout=5)
                    if password_input and password_input.is_displayed() and password_input.is_enabled():
                        self.logger.info(f"✓ 找到可用的密码输入框: {selector}")
                        self.logger.info(f"  元素ID: {password_input.get_attribute('id')}")
                        self.logger.info(f"  元素Class: {password_input.get_attribute('class')}")
                        break
                    else:
                        self.logger.info(f"  密码输入框不可用")
                        password_input = None
                except TimeoutException:
                    self.logger.info(f"  选择器超时")
                    continue
                except Exception as e:
                    self.logger.info(f"  选择器异常: {e}")
                    continue
            
            if not password_input:
                self.logger.error("无法找到密码输入框")
                return None
                
            password_input.clear()
            password_input.send_keys(password)
            
            # 确认密码
            self.logger.info("查找确认密码输入框...")
            confirm_password_selectors = get_all_selectors('confirm_password_input')
            self.logger.info(f"使用优化配置中的确认密码选择器 ({len(confirm_password_selectors)} 个)")
            
            confirm_password_input = None
            for i, selector in enumerate(confirm_password_selectors, 1):
                try:
                    self.logger.info(f"尝试确认密码选择器 {i}/{len(confirm_password_selectors)}: {selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem != password_input and elem.is_displayed() and elem.is_enabled():
                            confirm_password_input = elem
                            self.logger.info(f"✓ 找到确认密码输入框: {selector}")
                            self.logger.info(f"  元素ID: {elem.get_attribute('id')}")
                            self.logger.info(f"  元素Class: {elem.get_attribute('class')}")
                            break
                    if confirm_password_input:
                        break
                except Exception as e:
                    self.logger.info(f"  选择器异常: {e}")
                    continue
            
            if confirm_password_input:
                confirm_password_input.clear()
                confirm_password_input.send_keys(password)
            else:
                self.logger.warning("未找到确认密码输入框，可能不需要")
            
            # 处理可能的验证码
            self._handle_captcha()
            
            # 点击创建账号（使用优化选择器）
            self.logger.info("查找创建账号按钮...")
            create_selectors = get_all_selectors('create_button')
            self.logger.info(f"使用优化配置中的创建按钮选择器 ({len(create_selectors)} 个)")
            
            create_button = None
            for i, selector in enumerate(create_selectors, 1):
                try:
                    self.logger.info(f"尝试创建按钮选择器 {i}/{len(create_selectors)}: {selector}")
                    create_button = self._wait_for_clickable(By.CSS_SELECTOR, selector, timeout=3)
                    if create_button and create_button.is_displayed() and create_button.is_enabled():
                        self.logger.info(f"✓ 找到可用的创建账号按钮: {selector}")
                        self.logger.info(f"  按钮文本: {create_button.text}")
                        self.logger.info(f"  按钮Class: {create_button.get_attribute('class')}")
                        break
                    else:
                        self.logger.info(f"  创建按钮不可用")
                        create_button = None
                except TimeoutException:
                    self.logger.info(f"  选择器超时")
                    continue
                except Exception as e:
                    self.logger.info(f"  选择器异常: {e}")
                    continue
            
            if not create_button:
                self.logger.error("无法找到创建账号按钮")
                # 调试信息：打印页面中所有按钮
                try:
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    self.logger.info(f"页面中共有 {len(all_buttons)} 个按钮:")
                    for i, btn in enumerate(all_buttons[:5]):  # 只显示前5个
                        self.logger.info(f"  按钮{i+1}: text='{btn.text}', class='{btn.get_attribute('class')}'")
                except:
                    pass
                return None
                
            create_button.click()
            
            # 动态等待页面重定向完成
            self.logger.info("等待注册提交后的页面重定向...")
            current_url = self.driver.current_url
            redirect_success = self._wait_for_redirect(current_url, max_wait=30)
            
            if redirect_success:
                self.logger.info("页面重定向完成，检查注册结果...")
            else:
                self.logger.warning("页面重定向可能未完成，继续检查注册状态...")
            
            # 检查是否注册成功
            if self._check_registration_success():
                self.logger.info("AWS Builder ID 注册成功！")
                return AWSBuilderCredentials(
                    email=email,
                    password=password,
                    name=name
                )
            else:
                self.logger.error("注册失败，请检查页面状态")
                return None
                
        except Exception as e:
            self.logger.error(f"注册过程中出现错误: {e}")
            return None
        finally:
            if self.driver:
                if self.keep_browser:
                    self.logger.info("保持浏览器会话...")
                    self.logger.info("浏览器将保持打开状态，您可以继续操作")
                else:
                    self.logger.info("关闭浏览器...")
                    self.driver.quit()
                    self.driver = None
    
    def _check_registration_success(self) -> bool:
        """检查注册是否成功"""
        try:
            # 等待页面稳定
            time.sleep(2)
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            page_source = self.driver.page_source.lower()
            
            self.logger.info(f"检查注册状态 - URL: {current_url}")
            self.logger.info(f"检查注册状态 - 页面标题: {page_title}")
            
            # 检查URL中的成功指示器 - 如果跳转到登录页面，说明注册成功
            if "signin.aws" in current_url.lower() and "login" in current_url.lower():
                self.logger.info("✓ 检测到AWS登录页面，注册成功！")
                return True
            
            # 检查URL中的其他成功指示器
            url_success_indicators = [
                "dashboard",
                "profile", 
                "welcome",
                "success",
                "complete",
                "builder-id",
                "home"
            ]
            
            for indicator in url_success_indicators:
                if indicator in current_url.lower():
                    self.logger.info(f"✓ URL中检测到成功指示器: {indicator}")
                    return True
            
            # 检查页面标题中的成功指示器
            title_success_indicators = [
                "welcome",
                "dashboard", 
                "profile",
                "builder id",
                "success"
            ]
            
            for indicator in title_success_indicators:
                if indicator in page_title.lower():
                    self.logger.info(f"✓ 页面标题中检测到成功指示器: {indicator}")
                    return True
            
            # 检查页面内容中的成功指示器
            content_success_indicators = [
                "welcome to aws",
                "builder id created",
                "registration successful",
                "account created",
                "successfully created",
                "your aws builder id",
                "sign in to aws"  # 登录页面也是成功的标志
            ]
            
            for indicator in content_success_indicators:
                if indicator in page_source:
                    self.logger.info(f"✓ 页面内容中检测到成功指示器: {indicator}")
                    return True
            
            # 特殊情况：如果页面标题是"Amazon Web Services"且URL包含signin，很可能是成功的
            if "amazon web services" in page_title.lower() and "signin" in current_url.lower():
                self.logger.info("✓ 检测到AWS登录页面标题，判断为注册成功")
                return True
            
            # 检查是否有严重的注册失败错误信息
            critical_error_indicators = [
                "registration failed",
                "account creation failed",
                "invalid captcha", 
                "captcha is required",
                "email already exists",
                "email is already in use"
            ]
            
            for indicator in critical_error_indicators:
                if indicator in page_source:
                    self.logger.warning(f"⚠️ 检测到关键错误指示器: {indicator}")
                    return False
            
            # 如果包含"try again later"但同时在登录页面，可能是成功的
            if "try again later" in page_source and "signin" in current_url.lower():
                self.logger.info("✓ 虽然检测到'try again later'，但已在登录页面，判断为注册成功")
                return True
            
            self.logger.info("未检测到明确的成功或失败指示器，建议手动检查页面状态")
            return False
            
        except Exception as e:
            self.logger.error(f"检查注册状态时出错: {e}")
            return False
    
    def navigate_to_url(self, url: str) -> bool:
        """
        导航到指定URL（保持会话）
        
        Args:
            url: 目标URL
            
        Returns:
            bool: 是否成功导航
        """
        try:
            if not self.driver:
                self.logger.error("浏览器会话不存在，请先注册账号")
                return False
            
            self.logger.info(f"导航到: {url}")
            self.driver.get(url)
            time.sleep(3)
            return True
            
        except Exception as e:
            self.logger.error(f"导航失败: {e}")
            return False
    
    def get_current_url(self) -> Optional[str]:
        """获取当前页面URL"""
        try:
            if self.driver:
                return self.driver.current_url
            return None
        except Exception as e:
            self.logger.error(f"获取当前URL失败: {e}")
            return None
    
    def get_page_title(self) -> Optional[str]:
        """获取当前页面标题"""
        try:
            if self.driver:
                return self.driver.title
            return None
        except Exception as e:
            self.logger.error(f"获取页面标题失败: {e}")
            return None
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            if self.keep_browser:
                self.logger.info("保持浏览器打开，会话继续...")
                self.logger.info("您可以继续在浏览器中操作，或手动关闭浏览器")
            else:
                self.logger.info("关闭浏览器...")
                self.driver.quit()
                self.driver = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if not self.keep_browser:
            self.close()
