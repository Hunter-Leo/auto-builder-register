"""
CAPTCHA Handler
Responsible for handling image CAPTCHAs and email verification codes
"""

import logging
import time
import re
from typing import Optional, Tuple
from selenium import webdriver

from .element_waiter import ElementWaiter
from .optimized_selectors import get_selector


class CaptchaHandler:
    """CAPTCHA Handler"""
    
    def __init__(self, driver: webdriver.Edge, element_waiter: ElementWaiter,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize CAPTCHA handler
        
        Args:
            driver: Browser driver
            element_waiter: Element waiter
            logger: Logger instance
        """
        self.driver = driver
        self.element_waiter = element_waiter
        self.logger = logger or logging.getLogger(__name__)
    
    def check_image_captcha_exists(self) -> bool:
        """
        Check if image CAPTCHA exists (without interaction)
        
        Returns:
            Whether image CAPTCHA exists
        """
        self.logger.info("Checking if image CAPTCHA exists...")
        
        # Check CAPTCHA container
        captcha_selectors = get_selector("captcha_container")
        captcha_container = self.element_waiter.wait_for_element_with_retry(
            captcha_selectors, "CAPTCHA container", max_rounds=2, timeout_per_selector=3
        )
        
        if captcha_container:
            self.logger.info("Image CAPTCHA detected")
            return True
        else:
            self.logger.info("No image CAPTCHA detected")
            return False
    
    def handle_image_captcha(self) -> bool:
        """
        Handle image CAPTCHA (manual input)
        
        Returns:
            Whether CAPTCHA was handled successfully
        """
        self.logger.info("Checking if image CAPTCHA exists...")
        
        # Check CAPTCHA container
        captcha_selectors = get_selector("captcha_container")
        captcha_container = self.element_waiter.wait_for_element_with_retry(
            captcha_selectors, "CAPTCHA container", max_rounds=2, timeout_per_selector=3
        )
        
        if not captcha_container:
            self.logger.info("No image CAPTCHA detected")
            return True
        
        self.logger.info("Image CAPTCHA detected, manual input required")
        
        # Find CAPTCHA input field
        captcha_input_selectors = get_selector("captcha_input")
        captcha_input = self.element_waiter.wait_for_element_with_retry(
            captcha_input_selectors, "CAPTCHA input field"
        )
        
        if not captcha_input:
            self.logger.error("CAPTCHA input field not found")
            return False
        
        # Prompt user for manual input
        print("\n" + "="*50)
        print("Image CAPTCHA detected, please enter manually:")
        print("1. View the CAPTCHA image in the browser")
        print("2. Enter the CAPTCHA code below")
        print("="*50)
        
        # Wait for user input
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                captcha_code = input(f"Please enter CAPTCHA code (attempt {attempt + 1}/{max_attempts}): ").strip()
                
                if not captcha_code:
                    print("CAPTCHA code cannot be empty, please try again")
                    continue
                
                # Fill CAPTCHA code
                captcha_input.clear()
                captcha_input.send_keys(captcha_code)
                self.logger.info(f"CAPTCHA code entered: {captcha_code}")
                
                # Click submit button
                if self._submit_captcha():
                    # Wait for verification result
                    if self._wait_for_captcha_result():
                        self.logger.info("CAPTCHA verification successful")
                        return True
                    else:
                        print(f"CAPTCHA code incorrect, please try again ({max_attempts - attempt - 1} attempts remaining)")
                        continue
                else:
                    print("Failed to submit CAPTCHA, please try again")
                    continue
                    
            except KeyboardInterrupt:
                self.logger.info("User cancelled CAPTCHA input")
                return False
            except Exception as e:
                self.logger.error(f"Error handling CAPTCHA: {e}")
                print(f"Error handling CAPTCHA: {e}")
                continue
        
        self.logger.error("CAPTCHA verification failed, maximum attempts reached")
        return False
    
    def extract_verification_code_from_email(self, email_content: str) -> Optional[str]:
        """
        Extract verification code from email content
        
        Args:
            email_content: Email content
            
        Returns:
            Extracted verification code, None if not found
        """
        # Common verification code patterns
        patterns = [
            r'verification code[:\s]+([A-Z0-9]{6})',  # verification code: XXXXXX
            r'code[:\s]+([A-Z0-9]{6})',  # code: XXXXXX
            r'([A-Z0-9]{6})',  # 6-digit uppercase alphanumeric
            r'(\d{6})',  # 6-digit number
            r'([A-Z]{6})',  # 6-digit uppercase letters
        ]
        
        for pattern in patterns:
            match = re.search(pattern, email_content, re.IGNORECASE)
            if match:
                code = match.group(1)
                self.logger.info(f"Verification code extracted from email: {code}")
                return code
        
        self.logger.warning("Unable to extract verification code from email")
        return None
    
    def wait_for_email_verification_code(self, dropmail=None, timeout: int = 300) -> Optional[str]:
        """
        Wait for email verification code
        
        Args:
            dropmail: DropMail instance, if provided will automatically get verification code
            timeout: Timeout duration (seconds)
            
        Returns:
            Verification code, None if failed to get
        """
        if dropmail:
            return self._auto_get_verification_code(dropmail, timeout)
        else:
            return self._manual_get_verification_code()
    
    def _auto_get_verification_code(self, dropmail, timeout: int) -> Optional[str]:
        """Automatically get verification code from email with timeout auto-refresh"""
        self.logger.info("Waiting for email verification code...")
        
        max_attempts = 3  # Maximum 3 attempts
        wait_time_per_attempt = 300  # Wait 10 seconds per attempt
        
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Attempt {attempt + 1} to get verification code...")
                
                # Wait for new email (10 seconds per attempt)
                new_mail = dropmail.wait_for_mail(timeout=wait_time_per_attempt)
                
                if new_mail:
                    # Extract verification code
                    verification_code = self.extract_verification_code_from_email(new_mail.text)
                    if verification_code:
                        self.logger.info(f"Automatically got verification code: {verification_code}")
                        return verification_code
                    else:
                        self.logger.warning("No verification code found in email, continuing to wait...")
                else:
                    # Timeout without receiving email, try to resend verification code
                    if attempt < max_attempts - 1:  # Not the last attempt
                        self.logger.info(f"No verification code received after waiting {wait_time_per_attempt} seconds, trying to resend...")
                        if self._resend_verification_code():
                            self.logger.info("Verification code resent, continuing to wait...")
                            continue
                        else:
                            self.logger.warning("Failed to resend verification code, continuing to wait...")
                    else:
                        self.logger.error("Last attempt still did not receive verification email")
                        
            except Exception as e:
                self.logger.error(f"Error getting verification code on attempt {attempt + 1}: {e}")
                if attempt < max_attempts - 1:
                    continue
        
        self.logger.error("All attempts failed, unable to get verification code")
        return None
    
    def _resend_verification_code(self) -> bool:
        """Resend verification code"""
        try:
            from .optimized_selectors import get_selector
            
            self.logger.info("Trying to find resend verification code button...")
            
            # Find resend button
            resend_selectors = get_selector("resend_code_button")
            self.logger.debug(f"Using selectors: {resend_selectors}")
            
            # Try each selector
            resend_button = None
            for i, selector in enumerate(resend_selectors):
                try:
                    self.logger.debug(f"Trying selector {i+1}: {selector}")
                    elements = self.driver.find_elements("css selector", selector)
                    if elements:
                        resend_button = elements[0]
                        self.logger.info(f"✓ Found resend button, using selector: {selector}")
                        break
                    else:
                        self.logger.debug(f"Selector {selector} found no elements")
                except Exception as e:
                    self.logger.debug(f"Selector {selector} error: {e}")
                    continue
            
            if not resend_button:
                self.logger.warning("Resend verification code button not found")
                # Print current page button info for debugging
                try:
                    buttons = self.driver.find_elements("css selector", "button")
                    self.logger.debug(f"Found {len(buttons)} buttons on page")
                    for i, btn in enumerate(buttons[:5]):  # Only show first 5
                        try:
                            test_id = btn.get_attribute("data-testid") or "none"
                            text = btn.text or "no text"
                            self.logger.debug(f"Button {i+1}: data-testid='{test_id}', text='{text}'")
                        except:
                            pass
                except:
                    pass
                return False
            
            # Check if button is clickable
            if not resend_button.is_enabled():
                self.logger.warning("Resend button is not clickable")
                return False
            
            # Scroll to button position
            self.driver.execute_script("arguments[0].scrollIntoView(true);", resend_button)
            
            # Click resend button
            resend_button.click()
            self.logger.info("✓ Clicked resend verification code button")
            
            # Wait a moment for request to be sent
            import time
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resending verification code: {e}")
            return False
    
    def _manual_get_verification_code(self) -> Optional[str]:
        """Manual verification code input"""
        print("\n" + "="*50)
        print("Please check your email and enter the verification code:")
        print("1. Check the verification email in your mailbox")
        print("2. Enter the 6-digit verification code below")
        print("="*50)
        
        try:
            verification_code = input("Please enter email verification code: ").strip()
            if len(verification_code) == 6 and verification_code.isalnum():
                self.logger.info(f"Manual verification code input: {verification_code}")
                return verification_code
            else:
                self.logger.error("Verification code format incorrect, should be 6-digit alphanumeric")
                return None
        except KeyboardInterrupt:
            self.logger.info("User cancelled verification code input")
            return None
    
    def _submit_captcha(self) -> bool:
        """Submit CAPTCHA"""
        submit_selectors = get_selector("captcha_submit")
        submit_button = self.element_waiter.wait_for_clickable_with_retry(
            submit_selectors, "CAPTCHA submit button"
        )
        
        if not submit_button:
            self.logger.error("CAPTCHA submit button not found")
            return False
        
        try:
            submit_button.click()
            self.logger.info("CAPTCHA submitted")
            return True
        except Exception as e:
            self.logger.error(f"Error submitting CAPTCHA: {e}")
            return False
    
    def _wait_for_captcha_result(self, timeout: int = 10) -> bool:
        """Wait for CAPTCHA verification result"""
        self.logger.info("Waiting for CAPTCHA verification result...")
        
        # Check error messages and success indicators
        error_selectors = get_selector("captcha_error")
        
        # Use dynamic wait to check result
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check for error messages
            error_element = self.element_waiter.wait_for_any_element(error_selectors, timeout=1)
            if error_element and error_element.is_displayed():
                self.logger.info("CAPTCHA verification failed")
                return False
            
            # Check if verification successful (CAPTCHA container disappears or page redirects)
            current_url = self.driver.current_url
            if "captcha" not in current_url.lower():
                self.logger.info("CAPTCHA verification successful, page redirected")
                return True
            
            # Check if page has changed
            if self.element_waiter.wait_for_page_change(timeout=1):
                self.logger.info("CAPTCHA verification successful, page changed")
                return True
        
        self.logger.warning("CAPTCHA result wait timeout")
        return False
