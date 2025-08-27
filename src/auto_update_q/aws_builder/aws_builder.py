"""
AWS Builder ID 自动注册器
使用模块化设计，职责分离，代码清晰
"""

import logging
from typing import Optional
from dataclasses import dataclass
from selenium import webdriver

from .config import AWS_BUILDER_SIGNUP_URL, LOG_FORMAT
from .browser_manager import BrowserManager
from .element_waiter import ElementWaiter
from .form_handler import FormHandler
from .captcha_handler import CaptchaHandler
from .registration_checker import RegistrationChecker
from .optimized_selectors import get_selector


@dataclass
class AWSBuilderCredentials:
    """AWS Builder ID 登录凭证"""
    email: str
    password: str
    name: str
    builder_id: Optional[str] = None


class AWSBuilder:
    """AWS Builder ID 自动注册器"""
    
    def __init__(self, headless: bool = False, timeout: int = 30, 
                 debug: bool = False, keep_browser: bool = False, browser_type: str = "safari"):
        """
        初始化 AWS Builder 注册器
        
        Args:
            headless: 是否使用无头模式
            timeout: 等待超时时间（秒）
            debug: 是否启用调试模式
            keep_browser: 是否在结束后保持浏览器打开
            browser_type: 浏览器类型 ("safari" 或 "edge")
        """
        self.headless = headless
        self.timeout = timeout
        self.debug = debug
        self.keep_browser = keep_browser
        self.browser_type = browser_type
        
        # 初始化日志
        self.logger = self._setup_logger()
        
        # 初始化组件
        self.browser_manager = BrowserManager(headless, browser_type, self.logger)
        self.driver: Optional[webdriver.Edge] = None
        self.element_waiter: Optional[ElementWaiter] = None
        self.form_handler: Optional[FormHandler] = None
        self.captcha_handler: Optional[CaptchaHandler] = None
        self.registration_checker: Optional[RegistrationChecker] = None
    
    def register_aws_builder(self, email: str, name: str = "Crazy Joe", 
                           password: Optional[str] = None, 
                           dropmail=None) -> Optional[AWSBuilderCredentials]:
        """
        注册 AWS Builder ID 账号
        
        Args:
            email: 邮箱地址
            name: 用户姓名
            password: 指定密码（可选，不指定则自动生成）
            dropmail: DropMail实例（可选，用于自动获取验证码）
            
        Returns:
            注册成功的凭证信息，失败时返回None
        """
        self.logger.info("开始 AWS Builder ID 注册流程")
        self.logger.info(f"邮箱: {email}, 姓名: {name}")
        
        try:
            # 初始化浏览器和组件
            if not self._initialize_components():
                return None
            
            # 执行注册流程
            return self._execute_registration_flow(email, name, password, dropmail)
            
        except Exception as e:
            self.logger.error(f"注册过程中发生错误: {e}")
            return None
        finally:
            if not self.keep_browser:
                self.close()
    
    def register_aws_builder_until_captcha(self, email: str, name: str = "Crazy Joe", 
                                         password: Optional[str] = None, 
                                         dropmail=None) -> Optional[AWSBuilderCredentials]:
        """
        注册 AWS Builder ID 账号直到图形验证码前停止
        
        Args:
            email: 邮箱地址
            name: 用户姓名
            password: 指定密码（可选，不指定则自动生成）
            dropmail: DropMail实例（可选，用于自动获取验证码）
            
        Returns:
            注册信息（包含邮箱和密码），失败时返回None
        """
        self.logger.info("开始 AWS Builder ID 注册流程（到图形验证码前）")
        self.logger.info(f"邮箱: {email}, 姓名: {name}")
        
        try:
            # 初始化浏览器和组件
            if not self._initialize_components():
                return None
            
            # 执行注册流程直到图形验证码前
            return self._execute_registration_flow_until_captcha(email, name, password, dropmail)
            
        except Exception as e:
            self.logger.error(f"注册过程中发生错误: {e}")
            return None
    
    def navigate_to_url(self, url: str) -> bool:
        """
        导航到指定URL（保持会话）
        
        Args:
            url: 目标URL
            
        Returns:
            是否成功导航
        """
        if not self.driver:
            self.logger.error("浏览器未初始化")
            return False
        
        try:
            self.logger.info(f"导航到: {url}")
            self.driver.get(url)
            return self.element_waiter.wait_for_page_change(timeout=10)
        except Exception as e:
            self.logger.error(f"导航失败: {e}")
            return False
    
    def get_current_url(self) -> Optional[str]:
        """获取当前页面URL"""
        if not self.driver:
            return None
        
        try:
            return self.driver.current_url
        except Exception as e:
            self.logger.error(f"获取当前URL失败: {e}")
            return None
    
    def get_page_title(self) -> Optional[str]:
        """获取当前页面标题"""
        if not self.driver:
            return None
        
        try:
            return self.driver.title
        except Exception as e:
            self.logger.error(f"获取页面标题失败: {e}")
            return None
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            self.browser_manager.close_driver(self.driver)
            self.driver = None
            self.logger.info("浏览器已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if not self.keep_browser:
            self.close()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(LOG_FORMAT)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        
        return logger
    
    def _initialize_components(self) -> bool:
        """初始化所有组件"""
        try:
            # 设置浏览器驱动
            self.driver = self.browser_manager.setup_driver()
            
            # 初始化其他组件
            self.element_waiter = ElementWaiter(self.driver, self.logger)
            self.form_handler = FormHandler(self.driver, self.element_waiter, self.logger)
            self.captcha_handler = CaptchaHandler(self.driver, self.element_waiter, self.logger)
            self.registration_checker = RegistrationChecker(self.driver, self.element_waiter, self.logger)
            
            self.logger.info("所有组件初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"组件初始化失败: {e}")
            return False
    
    def _execute_registration_flow(self, email: str, name: str, 
                                 password: Optional[str], dropmail) -> Optional[AWSBuilderCredentials]:
        """执行注册流程"""
        # 导航到注册页面
        if not self._navigate_to_signup_page():
            return None
        
        # 处理Cookie同意
        self._handle_cookie_consent()
        
        # 填写邮箱表单
        if not self.form_handler.fill_email_form(email):
            return None
        
        # 填写姓名表单
        if not self.form_handler.fill_name_form(name):
            return None
        
        # 处理邮箱验证码
        verification_code = self.captcha_handler.wait_for_email_verification_code(
            dropmail, timeout=300
        )
        if not verification_code:
            return None
        
        if not self.form_handler.fill_verification_code(verification_code):
            return None
        
        # 填写密码表单
        used_password = self.form_handler.fill_password_form(password)
        if not used_password:
            return None
        
        # 处理图形验证码（如果存在）
        if not self.captcha_handler.handle_image_captcha():
            return None
        
        # 等待注册完成
        if not self.registration_checker.wait_for_registration_completion():
            return None
        
        # 获取注册信息
        registration_info = self.registration_checker.get_registration_info()
        
        # 创建凭证对象
        credentials = AWSBuilderCredentials(
            email=email,
            password=used_password,
            name=name,
            builder_id=registration_info.get("builder_id")
        )
        
        self.logger.info("✓ AWS Builder ID 注册成功")
        return credentials
    
    def _execute_registration_flow_until_captcha(self, email: str, name: str, 
                                               password: Optional[str], dropmail) -> Optional[AWSBuilderCredentials]:
        """执行注册流程直到图形验证码前停止"""
        # 导航到注册页面
        if not self._navigate_to_signup_page():
            return None
        
        # 处理Cookie同意
        self._handle_cookie_consent()
        
        # 填写邮箱表单
        if not self.form_handler.fill_email_form(email):
            return None
        
        # 填写姓名表单
        if not self.form_handler.fill_name_form(name):
            return None
        
        # 处理邮箱验证码
        verification_code = self.captcha_handler.wait_for_email_verification_code(
            dropmail, timeout=300
        )
        if not verification_code:
            return None
        
        if not self.form_handler.fill_verification_code(verification_code):
            return None
        
        # 填写密码表单
        used_password = self.form_handler.fill_password_form(password)
        if not used_password:
            return None
        
        # 密码填写完成，停止自动化流程
        self.logger.info("✓ 密码表单填写完成，自动化流程停止")
        self.logger.info("请在浏览器中手动完成图形验证码和注册提交")
        
        # 在浏览器中显示通知弹窗
        self._show_browser_notification(email, name, used_password)
        
        # 创建凭证对象（不包含builder_id，因为注册未完成）
        credentials = AWSBuilderCredentials(
            email=email,
            password=used_password,
            name=name
        )
        
        return credentials
    
    def _show_browser_notification(self, email: str, name: str, password: str):
        """在浏览器中显示通知弹窗，包含用户信息"""
        try:
            # 创建包含用户信息的自定义弹窗
            notification_script = f"""
            // 创建自定义通知弹窗
            if (!document.getElementById('aws-builder-notification')) {{
                // 创建弹窗容器
                var notification = document.createElement('div');
                notification.id = 'aws-builder-notification';
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                    z-index: 10000;
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    max-width: 400px;
                    animation: slideIn 0.5s ease-out;
                `;
                
                // 添加CSS动画
                var style = document.createElement('style');
                style.textContent = `
                    @keyframes slideIn {{
                        from {{ transform: translateX(100%); opacity: 0; }}
                        to {{ transform: translateX(0); opacity: 1; }}
                    }}
                `;
                document.head.appendChild(style);
                
                // 创建通知内容
                notification.innerHTML = `
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <div style="font-size: 24px; margin-right: 10px;">🤖</div>
                        <div style="font-weight: bold; font-size: 16px;">AWS Builder ID 注册助手</div>
                    </div>
                    <div style="margin-bottom: 15px; line-height: 1.4;">
                        ✅ <strong>自动填写已完成！</strong><br>
                        📝 邮箱、姓名、验证码、密码已自动填写<br>
                        🔐 请手动完成图形验证码并提交注册
                    </div>
                    <div style="background: rgba(255,255,255,0.2); padding: 12px; border-radius: 5px; margin-bottom: 15px; font-family: monospace;">
                        <div style="margin-bottom: 8px;"><strong>📧 邮箱:</strong> {email}</div>
                        <div style="margin-bottom: 8px;"><strong>👤 姓名:</strong> {name}</div>
                        <div><strong>🔐 密码:</strong> {password}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                        ⏰ <strong>注意：</strong>程序将在 30 分钟后自动退出
                    </div>
                    <button onclick="this.parentElement.remove()" 
                            style="background: rgba(255,255,255,0.3); border: none; color: white; 
                                   padding: 8px 15px; border-radius: 5px; cursor: pointer; 
                                   font-size: 12px; transition: background 0.3s;">
                        我知道了 ✓
                    </button>
                `;
                
                // 添加到页面
                document.body.appendChild(notification);
                
                // 10秒后自动淡出（如果用户没有点击关闭）
                setTimeout(function() {{
                    if (notification && notification.parentElement) {{
                        notification.style.transition = 'opacity 1s ease-out';
                        notification.style.opacity = '0.8';
                    }}
                }}, 10000);
            }}
            """
            
            # 执行JavaScript
            self.driver.execute_script(notification_script)
            self.logger.info("✓ 已在浏览器中显示通知弹窗（包含用户信息）")
            
        except Exception as e:
            self.logger.warning(f"显示浏览器通知时出错: {e}")
            # 如果自定义弹窗失败，使用简单的alert作为备用
            try:
                alert_message = f"""🤖 AWS Builder ID 注册助手

✅ 自动填写已完成！
📝 邮箱、姓名、验证码、密码已自动填写
🔐 请手动完成图形验证码并提交注册

📧 邮箱: {email}
👤 姓名: {name}
🔐 密码: {password}

⏰ 注意：程序将在 30 分钟后自动退出"""
                
                self.driver.execute_script(f"alert({repr(alert_message)});")
                self.logger.info("✓ 已显示简单弹窗通知")
            except Exception as e2:
                self.logger.warning(f"显示简单弹窗也失败: {e2}")
    
    def _navigate_to_signup_page(self) -> bool:
        """导航到注册页面"""
        try:
            self.logger.info(f"导航到注册页面: {AWS_BUILDER_SIGNUP_URL}")
            self.driver.get(AWS_BUILDER_SIGNUP_URL)
            
            # 等待页面加载完成
            return self.element_waiter.wait_for_redirect(AWS_BUILDER_SIGNUP_URL, max_wait=30)
                
        except Exception as e:
            self.logger.error(f"导航到注册页面失败: {e}")
            return False
    
    def _handle_cookie_consent(self) -> None:
        """处理Cookie同意弹窗"""
        try:
            self.logger.info("检查Cookie同意弹窗...")
            
            cookie_selectors = get_selector("cookie_accept")
            cookie_button = self.element_waiter.wait_for_clickable_with_retry(
                cookie_selectors, "Cookie同意按钮", max_rounds=1, timeout_per_selector=2
            )
            
            if cookie_button:
                cookie_button.click()
                self.logger.info("已点击Cookie同意按钮")
                # 等待弹窗消失
                self.element_waiter.wait_for_page_change(timeout=2)
            else:
                self.logger.info("未检测到Cookie同意弹窗")
                
        except Exception as e:
            self.logger.warning(f"处理Cookie同意时出错: {e}")
            # Cookie处理失败不影响主流程
