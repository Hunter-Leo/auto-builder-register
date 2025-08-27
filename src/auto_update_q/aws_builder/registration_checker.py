"""
Registration Status Checker
Responsible for checking AWS Builder ID registration status and results
"""

import logging
import time
from typing import Optional, Dict, Any
from selenium import webdriver

from .element_waiter import ElementWaiter
from .optimized_selectors import get_selector


class RegistrationChecker:
    """Registration Status Checker"""
    
    def __init__(self, driver: webdriver.Edge, element_waiter: ElementWaiter,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize registration status checker
        
        Args:
            driver: Browser driver
            element_waiter: Element waiter
            logger: Logger instance
        """
        self.driver = driver
        self.element_waiter = element_waiter
        self.logger = logger or logging.getLogger(__name__)
    
    def check_registration_success(self) -> bool:
        """
        Check if registration was successful
        
        Returns:
            Whether registration was successful
        """
        self.logger.info("Checking registration status...")
        
        # Wait for page to stabilize
        self.element_waiter.wait_for_page_change(timeout=5)
        
        current_url = self.driver.current_url
        self.logger.info(f"Current URL: {current_url}")
        
        # Check success indicators
        success_indicators = [
            self._check_success_url(),
            self._check_success_elements(),
            self._check_dashboard_access(),
        ]
        
        # Check failure indicators
        failure_indicators = [
            self._check_error_messages(),
            self._check_registration_form_still_present(),
        ]
        
        success_count = sum(success_indicators)
        failure_count = sum(failure_indicators)
        
        self.logger.info(f"Success indicators: {success_count}/3, Failure indicators: {failure_count}/2")
        
        if success_count >= 2:
            self.logger.info("✓ Registration successful")
            return True
        elif failure_count >= 1:
            self.logger.warning("✗ Registration failed")
            return False
        else:
            self.logger.info("Registration status unclear, may need more time")
            return False
    
    def get_registration_info(self) -> Dict[str, Any]:
        """
        Get registration related information
        
        Returns:
            Dictionary containing registration information
        """
        info = {
            "current_url": self.driver.current_url,
            "page_title": self._get_page_title(),
            "builder_id": self._extract_builder_id(),
            "success": self.check_registration_success(),
            "timestamp": time.time()
        }
        
        return info
    
    def wait_for_registration_completion(self, timeout: int = 60) -> bool:
        """
        Wait for registration process completion
        
        Args:
            timeout: Timeout duration (seconds)
            
        Returns:
            Whether registration completed successfully
        """
        self.logger.info(f"Waiting for registration completion, timeout: {timeout} seconds")
        
        start_time = time.time()
        last_url = self.driver.current_url
        check_interval = 2
        
        while time.time() - start_time < timeout:
            try:
                current_url = self.driver.current_url
                
                # Check URL changes
                if current_url != last_url:
                    self.logger.info(f"URL changed: {current_url}")
                    last_url = current_url
                
                # Check registration status
                if self.check_registration_success():
                    return True
                
                # Check for errors
                if self._check_error_messages():
                    self.logger.error("Error message detected, registration failed")
                    return False
                
                # Dynamically adjust check interval
                remaining_time = timeout - (time.time() - start_time)
                if remaining_time < 10:
                    check_interval = 0.5  # More frequent checks in last 10 seconds
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.warning(f"Error while waiting for registration completion: {e}")
                time.sleep(check_interval)
        
        self.logger.warning("Registration completion wait timeout")
        return False
    
    def _check_success_url(self) -> bool:
        """Check success URL patterns"""
        current_url = self.driver.current_url.lower()
        success_patterns = [
            "dashboard",
            "console",
            "welcome",
            "success",
            "complete",
            "view.awsapps.com"
        ]
        
        for pattern in success_patterns:
            if pattern in current_url:
                self.logger.info(f"✓ Success URL pattern detected: {pattern}")
                return True
        
        return False
    
    def _check_success_elements(self) -> bool:
        """Check success page elements"""
        success_selectors = get_selector("success_indicators")
        
        # Use quick check, don't wait too long
        element = self.element_waiter.wait_for_any_element(success_selectors, timeout=3)
        if element and element.is_displayed():
            self.logger.info("✓ Success element detected")
            return True
        
        return False
    
    def _check_dashboard_access(self) -> bool:
        """Check if dashboard is accessible"""
        dashboard_selectors = get_selector("dashboard_elements")
        
        # Use quick check
        element = self.element_waiter.wait_for_any_element(dashboard_selectors, timeout=3)
        if element and element.is_displayed():
            self.logger.info("✓ Dashboard element detected")
            return True
        
        return False
    
    def _check_error_messages(self) -> bool:
        """Check error messages"""
        error_selectors = get_selector("error_messages")
        
        # Quick check for error messages
        element = self.element_waiter.wait_for_any_element(error_selectors, timeout=1)
        if element and element.is_displayed():
            error_text = element.text
            self.logger.warning(f"✗ Error message detected: {error_text}")
            return True
        
        return False
    
    def _check_registration_form_still_present(self) -> bool:
        """Check if registration form still exists"""
        form_selectors = get_selector("registration_form")
        
        # Quick check if form is still there
        element = self.element_waiter.wait_for_any_element(form_selectors, timeout=2)
        if element and element.is_displayed():
            self.logger.warning("✗ Registration form still present")
            return True
        
        return False
    
    def _get_page_title(self) -> Optional[str]:
        """Get page title"""
        try:
            return self.driver.title
        except Exception as e:
            self.logger.warning(f"Failed to get page title: {e}")
            return None
    
    def _extract_builder_id(self) -> Optional[str]:
        """Extract Builder ID"""
        try:
            # Try to extract from URL
            current_url = self.driver.current_url
            if "builder" in current_url.lower():
                # Specific extraction logic can be added here
                pass
            
            # Try to extract from page elements
            builder_id_selectors = get_selector("builder_id_display")
            element = self.element_waiter.wait_for_any_element(builder_id_selectors, timeout=2)
            if element:
                builder_id = element.text.strip()
                if builder_id:
                    self.logger.info(f"Builder ID extracted: {builder_id}")
                    return builder_id
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to extract Builder ID: {e}")
            return None
