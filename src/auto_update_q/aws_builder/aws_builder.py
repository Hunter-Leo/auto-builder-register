"""
AWS Builder ID Automatic Registrar
Using modular design, separation of concerns, clean code
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
    """AWS Builder ID login credentials"""
    email: str
    password: str
    name: str
    builder_id: Optional[str] = None


class AWSBuilder:
    """AWS Builder ID Automatic Registrar"""
    
    def __init__(self, headless: bool = False, timeout: int = 30, 
                 debug: bool = False, keep_browser: bool = False, browser_type: str = "safari"):
        """
        Initialize AWS Builder registrar
        
        Args:
            headless: Whether to use headless mode
            timeout: Wait timeout duration (seconds)
            debug: Whether to enable debug mode
            keep_browser: Whether to keep browser open after completion
            browser_type: Browser type ("safari" or "edge")
        """
        self.headless = headless
        self.timeout = timeout
        self.debug = debug
        self.keep_browser = keep_browser
        self.browser_type = browser_type
        
        # Initialize logging
        self.logger = self._setup_logger()
        
        # Initialize components
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
        Register AWS Builder ID account
        
        Args:
            email: Email address
            name: User name
            password: Specified password (optional, auto-generated if not specified)
            dropmail: DropMail instance (optional, for auto-getting verification code)
            
        Returns:
            Registration credentials on success, None on failure
        """
        self.logger.info("Starting AWS Builder ID registration process")
        self.logger.info(f"Email: {email}, Name: {name}")
        
        try:
            # Initialize browser and components
            if not self._initialize_components():
                return None
            
            # Execute registration flow
            return self._execute_registration_flow(email, name, password, dropmail)
            
        except Exception as e:
            self.logger.error(f"Error occurred during registration: {e}")
            return None
        finally:
            if not self.keep_browser:
                self.close()
    
    def register_aws_builder_until_captcha(self, email: str, name: str = "Crazy Joe", 
                                         password: Optional[str] = None, 
                                         dropmail=None) -> Optional[AWSBuilderCredentials]:
        """
        Register AWS Builder ID account until before image CAPTCHA
        
        Args:
            email: Email address
            name: User name
            password: Specified password (optional, auto-generated if not specified)
            dropmail: DropMail instance (optional, for auto-getting verification code)
            
        Returns:
            Registration info (including email and password), None on failure
        """
        self.logger.info("Starting AWS Builder ID registration process (until before image CAPTCHA)")
        self.logger.info(f"Email: {email}, Name: {name}")
        
        try:
            # Initialize browser and components
            if not self._initialize_components():
                return None
            
            # Execute registration flow until before image CAPTCHA
            return self._execute_registration_flow_until_captcha(email, name, password, dropmail)
            
        except Exception as e:
            self.logger.error(f"Error occurred during registration: {e}")
            return None
    
    def navigate_to_url(self, url: str) -> bool:
        """
        Navigate to specified URL (maintain session)
        
        Args:
            url: Target URL
            
        Returns:
            Whether navigation was successful
        """
        if not self.driver:
            self.logger.error("Browser not initialized")
            return False
        
        try:
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            return self.element_waiter.wait_for_page_change(timeout=10)
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False
    
    def get_current_url(self) -> Optional[str]:
        """Get current page URL"""
        if not self.driver:
            return None
        
        try:
            return self.driver.current_url
        except Exception as e:
            self.logger.error(f"Failed to get current URL: {e}")
            return None
    
    def get_page_title(self) -> Optional[str]:
        """Get current page title"""
        if not self.driver:
            return None
        
        try:
            return self.driver.title
        except Exception as e:
            self.logger.error(f"Failed to get page title: {e}")
            return None
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.browser_manager.close_driver(self.driver)
            self.driver = None
            self.logger.info("Browser closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if not self.keep_browser:
            self.close()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger"""
        logger = logging.getLogger(__name__)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(LOG_FORMAT)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        
        return logger
    
    def _initialize_components(self) -> bool:
        """Initialize all components"""
        try:
            # Setup browser driver
            self.driver = self.browser_manager.setup_driver()
            
            # Initialize other components
            self.element_waiter = ElementWaiter(self.driver, self.logger)
            self.form_handler = FormHandler(self.driver, self.element_waiter, self.logger)
            self.captcha_handler = CaptchaHandler(self.driver, self.element_waiter, self.logger)
            self.registration_checker = RegistrationChecker(self.driver, self.element_waiter, self.logger)
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            return False
    
    def _execute_registration_flow(self, email: str, name: str, 
                                 password: Optional[str], dropmail) -> Optional[AWSBuilderCredentials]:
        """Execute registration flow"""
        # Navigate to registration page
        if not self._navigate_to_signup_page():
            return None
        
        # Handle cookie consent
        self._handle_cookie_consent()
        
        # Fill email form
        if not self.form_handler.fill_email_form(email):
            return None
        
        # Fill name form
        if not self.form_handler.fill_name_form(name):
            return None
        
        # Handle email verification code
        verification_code = self.captcha_handler.wait_for_email_verification_code(
            dropmail, timeout=300
        )
        if not verification_code:
            return None
        
        if not self.form_handler.fill_verification_code(verification_code):
            return None
        
        # Fill password form
        used_password = self.form_handler.fill_password_form(password)
        if not used_password:
            return None
        
        # Handle image CAPTCHA (if exists)
        if not self.captcha_handler.handle_image_captcha():
            return None
        
        # Wait for registration completion
        if not self.registration_checker.wait_for_registration_completion():
            return None
        
        # Get registration info
        registration_info = self.registration_checker.get_registration_info()
        
        # Create credentials object
        credentials = AWSBuilderCredentials(
            email=email,
            password=used_password,
            name=name,
            builder_id=registration_info.get("builder_id")
        )
        
        self.logger.info("✓ AWS Builder ID registration successful")
        return credentials
    
    def _execute_registration_flow_until_captcha(self, email: str, name: str, 
                                               password: Optional[str], dropmail) -> Optional[AWSBuilderCredentials]:
        """Execute registration flow until before image CAPTCHA"""
        # Navigate to registration page
        if not self._navigate_to_signup_page():
            return None
        
        # Handle cookie consent
        self._handle_cookie_consent()
        
        # Fill email form
        if not self.form_handler.fill_email_form(email):
            return None
        
        # Fill name form
        if not self.form_handler.fill_name_form(name):
            return None
        
        # Handle email verification code
        verification_code = self.captcha_handler.wait_for_email_verification_code(
            dropmail, timeout=300
        )
        if not verification_code:
            return None
        
        if not self.form_handler.fill_verification_code(verification_code):
            return None
        
        # Fill password form
        used_password = self.form_handler.fill_password_form(password)
        if not used_password:
            return None
        
        # Password form completed, stop automation process
        self.logger.info("✓ Password form completed, automation process stopped")
        self.logger.info("Please manually complete image CAPTCHA and submit registration in browser")
        
        # Show notification popup in browser
        self._show_browser_notification(email, name, used_password)
        
        # Create credentials object (without builder_id since registration is incomplete)
        credentials = AWSBuilderCredentials(
            email=email,
            password=used_password,
            name=name
        )
        
        return credentials
    
    def _show_browser_notification(self, email: str, name: str, password: str):
        """Show notification popup in browser with user information"""
        try:
            # Create custom popup with user information
            notification_script = f"""
            // Create custom notification popup
            if (!document.getElementById('aws-builder-notification')) {{
                // Create popup container
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
                
                // Add CSS animation
                var style = document.createElement('style');
                style.textContent = `
                    @keyframes slideIn {{
                        from {{ transform: translateX(100%); opacity: 0; }}
                        to {{ transform: translateX(0); opacity: 1; }}
                    }}
                `;
                document.head.appendChild(style);
                
                // Create notification content
                notification.innerHTML = `
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <div style="font-size: 24px; margin-right: 10px;">🤖</div>
                        <div style="font-weight: bold; font-size: 16px;">AWS Builder ID Registration Assistant</div>
                    </div>
                    <div style="margin-bottom: 15px; line-height: 1.4;">
                        ✅ <strong>Auto-fill completed!</strong><br>
                        📝 Email, name, verification code, password auto-filled<br>
                        🔐 Please manually complete image CAPTCHA and submit registration
                    </div>
                    <div style="background: rgba(255,255,255,0.2); padding: 12px; border-radius: 5px; margin-bottom: 15px; font-family: monospace;">
                        <div style="margin-bottom: 8px;"><strong>📧 Email:</strong> {email}</div>
                        <div style="margin-bottom: 8px;"><strong>👤 Name:</strong> {name}</div>
                        <div><strong>🔐 Password:</strong> {password}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.2); padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                        ⏰ <strong>Note:</strong> Program will auto-exit after 30 minutes
                    </div>
                    <button onclick="this.parentElement.remove()" 
                            style="background: rgba(255,255,255,0.3); border: none; color: white; 
                                   padding: 8px 15px; border-radius: 5px; cursor: pointer; 
                                   font-size: 12px; transition: background 0.3s;">
                        Got it ✓
                    </button>
                `;
                
                // Add to page
                document.body.appendChild(notification);
                
                // Auto fade out after 10 seconds (if user doesn't click close)
                setTimeout(function() {{
                    if (notification && notification.parentElement) {{
                        notification.style.transition = 'opacity 1s ease-out';
                        notification.style.opacity = '0.8';
                    }}
                }}, 10000);
            }}
            """
            
            # Execute JavaScript
            self.driver.execute_script(notification_script)
            self.logger.info("✓ Notification popup displayed in browser (with user information)")
            
        except Exception as e:
            self.logger.warning(f"Error showing browser notification: {e}")
            # If custom popup fails, use simple alert as backup
            try:
                alert_message = f"""🤖 AWS Builder ID Registration Assistant

✅ Auto-fill completed!
📝 Email, name, verification code, password auto-filled
🔐 Please manually complete image CAPTCHA and submit registration

📧 Email: {email}
👤 Name: {name}
🔐 Password: {password}

⏰ Note: Program will auto-exit after 30 minutes"""
                
                self.driver.execute_script(f"alert({repr(alert_message)});")
                self.logger.info("✓ Simple popup notification displayed")
            except Exception as e2:
                self.logger.warning(f"Simple popup also failed: {e2}")
    
    def _navigate_to_signup_page(self) -> bool:
        """Navigate to registration page"""
        try:
            self.logger.info(f"Navigating to registration page: {AWS_BUILDER_SIGNUP_URL}")
            self.driver.get(AWS_BUILDER_SIGNUP_URL)
            
            # Wait for page to load completely
            return self.element_waiter.wait_for_redirect(AWS_BUILDER_SIGNUP_URL, max_wait=30)
                
        except Exception as e:
            self.logger.error(f"Failed to navigate to registration page: {e}")
            return False
    
    def _handle_cookie_consent(self) -> None:
        """Handle cookie consent popup"""
        try:
            self.logger.info("Checking for cookie consent popup...")
            
            cookie_selectors = get_selector("cookie_accept")
            cookie_button = self.element_waiter.wait_for_clickable_with_retry(
                cookie_selectors, "Cookie consent button", max_rounds=1, timeout_per_selector=2
            )
            
            if cookie_button:
                cookie_button.click()
                self.logger.info("Clicked cookie consent button")
                # Wait for popup to disappear
                self.element_waiter.wait_for_page_change(timeout=2)
            else:
                self.logger.info("No cookie consent popup detected")
                
        except Exception as e:
            self.logger.warning(f"Error handling cookie consent: {e}")
            # Cookie handling failure doesn't affect main flow
