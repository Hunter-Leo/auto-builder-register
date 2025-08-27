"""
Form Handler
Responsible for AWS Builder ID registration form filling logic
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
    """Form Handler"""
    
    def __init__(self, driver: webdriver.Edge, element_waiter: ElementWaiter, 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize form handler
        
        Args:
            driver: Browser driver
            element_waiter: Element waiter
            logger: Logger instance
        """
        self.driver = driver
        self.element_waiter = element_waiter
        self.logger = logger or logging.getLogger(__name__)
    
    def fill_email_form(self, email: str) -> bool:
        """
        Fill email form
        
        Args:
            email: Email address
            
        Returns:
            Whether filling was successful
        """
        self.logger.info("Starting to fill email form...")
        
        # Wait for email input field
        email_selectors = get_selector("email_input")
        email_input = self.element_waiter.wait_for_element_with_retry(
            email_selectors, "email input field"
        )
        
        if not email_input:
            self.logger.error("Email input field not found")
            return False
        
        # Fill email
        try:
            self._fill_input_field(email_input, email, "email")
            
            # Click next button
            return self._click_next_button("email_next_button", "email page next button")
            
        except Exception as e:
            self.logger.error(f"Error filling email: {e}")
            return False
    
    def fill_name_form(self, name: str) -> bool:
        """
        Fill name form
        
        Args:
            name: User name
            
        Returns:
            Whether filling was successful
        """
        self.logger.info("Starting to fill name form...")
        
        # Wait for name input field
        name_selectors = get_selector("name_input")
        name_input = self.element_waiter.wait_for_element_with_retry(
            name_selectors, "name input field"
        )
        
        if not name_input:
            self.logger.error("Name input field not found")
            return False
        
        # Fill name
        try:
            self._fill_input_field(name_input, name, "name")
            
            # Click next button
            return self._click_next_button("name_next_button", "name page next button")
            
        except Exception as e:
            self.logger.error(f"Error filling name: {e}")
            return False
    
    def fill_password_form(self, password: Optional[str] = None) -> Optional[str]:
        """
        Fill password form
        
        Args:
            password: Specified password, if None will auto-generate
            
        Returns:
            Password used, None if failed
        """
        self.logger.info("Starting to fill password form...")
        
        # Generate or use specified password
        if password is None:
            password = self.generate_random_password()
            self.logger.info("Random password generated")
        
        # Wait for password input field
        password_selectors = get_selector("password_input")
        password_input = self.element_waiter.wait_for_element_with_retry(
            password_selectors, "password input field"
        )
        
        if not password_input:
            self.logger.error("Password input field not found")
            return None
        
        # Wait for confirm password input field
        confirm_selectors = get_selector("confirm_password_input")
        confirm_input = self.element_waiter.wait_for_element_with_retry(
            confirm_selectors, "confirm password input field"
        )
        
        if not confirm_input:
            self.logger.error("Confirm password input field not found")
            return None
        
        # Fill password
        try:
            self._fill_input_field(password_input, password, "password")
            self._fill_input_field(confirm_input, password, "confirm password")
            
            # Password form completed, return password (don't click next button, let user handle image CAPTCHA manually)
            self.logger.info("Password form completed, waiting for user to handle image CAPTCHA manually")
            return password
                
        except Exception as e:
            self.logger.error(f"Error filling password: {e}")
            return None
    
    def fill_verification_code(self, code: str) -> bool:
        """
        Fill verification code
        
        Args:
            code: Verification code
            
        Returns:
            Whether filling was successful
        """
        self.logger.info("Starting to fill verification code...")
        
        # Wait for verification code input field
        code_selectors = get_selector("verification_code_input")
        code_input = self.element_waiter.wait_for_element_with_retry(
            code_selectors, "verification code input field"
        )
        
        if not code_input:
            self.logger.error("Verification code input field not found")
            return False
        
        # Fill verification code
        try:
            self._fill_input_field(code_input, code, "verification code")
            
            # Click verify button
            return self._click_next_button("verify_button", "verify button")
            
        except Exception as e:
            self.logger.error(f"Error filling verification code: {e}")
            return False
    
    def generate_random_password(self, length: Optional[int] = None) -> str:
        """
        Generate random password
        
        Args:
            length: Password length
            
        Returns:
            Generated password
        """
        length = length or PASSWORD_CONFIG["length"]
        
        # Ensure password contains all required character types
        password_list = []
        
        # Include at least one character from each type
        for char_type, chars in PASSWORD_CONFIG["required_types"].items():
            password_list.append(random.choice(chars))
        
        # Fill remaining length
        remaining_length = length - len(password_list)
        all_chars = PASSWORD_CONFIG["characters"]
        
        for _ in range(remaining_length):
            password_list.append(random.choice(all_chars))
        
        # Shuffle order
        random.shuffle(password_list)
        
        return ''.join(password_list)
    
    def _fill_input_field(self, element, value: str, field_name: str) -> None:
        """
        Generic method for filling input fields
        
        Args:
            element: Input element
            value: Value to fill
            field_name: Field name (for logging)
        """
        # Scroll to element position
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        
        # Wait for element to be visible and interactive
        self.element_waiter.wait_for_element_interactive(element)
        
        # Clear and fill
        element.clear()
        element.send_keys(value)
        self.logger.info(f"Filled {field_name}: {value if field_name != 'password' else '***'}")
    
    def _click_next_button(self, button_key: str, button_name: str) -> bool:
        """
        Click next button
        
        Args:
            button_key: Button selector key name
            button_name: Button name (for logging)
            
        Returns:
            Whether click was successful
        """
        button_selectors = get_selector(button_key)
        button = self.element_waiter.wait_for_clickable_with_retry(
            button_selectors, button_name
        )
        
        if not button:
            self.logger.error(f"{button_name} not found")
            return False
        
        try:
            # Scroll to button position
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            
            # Wait for button to be clickable
            self.element_waiter.wait_for_element_interactive(button)
            
            # Click button
            button.click()
            self.logger.info(f"Clicked {button_name}")
            
            # Wait for page response
            return self.element_waiter.wait_for_page_change()
            
        except Exception as e:
            self.logger.error(f"Error clicking {button_name}: {e}")
            return False
