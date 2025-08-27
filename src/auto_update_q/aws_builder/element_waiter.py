"""
Element Waiter
Responsible for waiting and finding page elements
"""

import logging
import time
from typing import Optional, List, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from .config import DEFAULT_TIMEOUT, DEFAULT_RETRY_ROUNDS, DEFAULT_RETRY_TIMEOUT
from .optimized_selectors import get_selector, get_timeout, get_retry_config


class ElementWaiter:
    """Element Waiter"""
    
    def __init__(self, driver: webdriver.Edge, logger: Optional[logging.Logger] = None):
        """
        Initialize element waiter
        
        Args:
            driver: Browser driver
            logger: Logger instance
        """
        self.driver = driver
        self.logger = logger or logging.getLogger(__name__)
    
    def wait_for_element_with_retry(self, selectors: List[str], element_name: str, 
                                  max_rounds: Optional[int] = None, 
                                  timeout_per_selector: Optional[int] = None) -> Optional[Any]:
        """
        Wait for element using multiple selectors with retry support
        
        Args:
            selectors: List of selectors
            element_name: Element name (for logging)
            max_rounds: Maximum retry rounds
            timeout_per_selector: Timeout per selector
            
        Returns:
            Found element or None
        """
        # Use optimized configuration or default values
        max_rounds = max_rounds or get_retry_config(element_name, "max_rounds", DEFAULT_RETRY_ROUNDS)
        timeout_per_selector = timeout_per_selector or get_retry_config(element_name, "timeout", DEFAULT_RETRY_TIMEOUT)
        
        self.logger.info(f"Starting to wait for element: {element_name}")
        
        for round_num in range(1, max_rounds + 1):
            self.logger.debug(f"Round {round_num}/{max_rounds} attempt")
            
            for i, selector in enumerate(selectors, 1):
                self.logger.debug(f"  Trying selector {i}/{len(selectors)}: {selector}")
                
                element = self._try_single_selector(selector, timeout_per_selector)
                if element:
                    self.logger.info(f"✓ Found element {element_name}, using selector: {selector}")
                    return element
            
            if round_num < max_rounds:
                wait_time = min(2 ** round_num, 8)  # Exponential backoff, max 8 seconds
                self.logger.debug(f"Round {round_num} failed, waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        self.logger.warning(f"✗ All attempts failed, element not found: {element_name}")
        return None
    
    def wait_for_clickable_with_retry(self, selectors: List[str], element_name: str,
                                    max_rounds: int = 3, 
                                    timeout_per_selector: int = 3) -> Optional[Any]:
        """
        Wait for clickable element using multiple selectors with retry support
        
        Args:
            selectors: List of selectors
            element_name: Element name
            max_rounds: Maximum retry rounds
            timeout_per_selector: Timeout per selector
            
        Returns:
            Found clickable element or None
        """
        self.logger.info(f"Starting to wait for clickable element: {element_name}")
        
        for round_num in range(1, max_rounds + 1):
            self.logger.debug(f"Round {round_num}/{max_rounds} attempt")
            
            for i, selector in enumerate(selectors, 1):
                self.logger.debug(f"  Trying selector {i}/{len(selectors)}: {selector}")
                
                element = self._try_clickable_selector(selector, timeout_per_selector)
                if element:
                    self.logger.info(f"✓ Found clickable element {element_name}, using selector: {selector}")
                    return element
            
            if round_num < max_rounds:
                wait_time = 2
                self.logger.debug(f"Round {round_num} failed, waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        
        self.logger.warning(f"✗ All attempts failed, clickable element not found: {element_name}")
        return None
    
    def wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> Optional[Any]:
        """Wait for single element to appear"""
        wait_timeout = timeout or DEFAULT_TIMEOUT
        try:
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            self.logger.warning(f"Element wait timeout: {by}={value}")
            return None
    
    def wait_for_clickable(self, by: By, value: str, timeout: Optional[int] = None) -> Optional[Any]:
        """Wait for single element to be clickable"""
        wait_timeout = timeout or DEFAULT_TIMEOUT
        try:
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            self.logger.warning(f"Clickable element wait timeout: {by}={value}")
            return None
    
    def wait_for_element_interactive(self, element, timeout: int = 10) -> bool:
        """
        Wait for element to become interactive
        
        Args:
            element: Page element
            timeout: Timeout duration
            
        Returns:
            Whether element became interactive successfully
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if element.is_displayed() and element.is_enabled():
                    return True
                time.sleep(0.1)
            except StaleElementReferenceException:
                self.logger.warning("Element reference stale, need to refind")
                return False
            except Exception as e:
                self.logger.warning(f"Error checking element interactive state: {e}")
                time.sleep(0.1)
        
        self.logger.warning("Element interactive wait timeout")
        return False
    
    def wait_for_page_change(self, timeout: int = 10) -> bool:
        """
        Wait for page change (URL change or new elements appear)
        
        Args:
            timeout: Timeout duration
            
        Returns:
            Whether page change was detected
        """
        initial_url = self.driver.current_url
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                current_url = self.driver.current_url
                if current_url != initial_url:
                    self.logger.info(f"Page change detected: {current_url}")
                    return True
                
                # Check if page has new loading state
                if self._check_page_loading_complete():
                    time.sleep(0.5)  # Give page some time to stabilize
                    return True
                
                time.sleep(0.2)
                
            except Exception as e:
                self.logger.warning(f"Error checking page change: {e}")
                time.sleep(0.2)
        
        self.logger.debug("No page change detected")
        return False
    
    def wait_for_redirect(self, initial_url: str, max_wait: int = 30) -> bool:
        """
        Dynamically wait for page redirect completion
        
        Args:
            initial_url: Initial URL
            max_wait: Maximum wait time
            
        Returns:
            Whether redirect was successful
        """
        self.logger.info(f"Waiting for page redirect, initial URL: {initial_url}")
        
        start_time = time.time()
        last_url = initial_url
        stable_count = 0
        
        while time.time() - start_time < max_wait:
            try:
                current_url = self.driver.current_url
                
                if current_url != initial_url:
                    if current_url == last_url:
                        stable_count += 1
                        if stable_count >= 3:  # URL stable for 3 checks
                            self.logger.info(f"Page redirect completed: {current_url}")
                            return True
                    else:
                        stable_count = 0
                        last_url = current_url
                        self.logger.debug(f"URL change detected: {current_url}")
                
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.warning(f"Error checking redirect: {e}")
                time.sleep(0.5)
        
        self.logger.warning(f"Redirect wait timeout, current URL: {self.driver.current_url}")
        return False
    
    def wait_for_any_element(self, selectors: List[str], timeout: int = 10) -> Optional[Any]:
        """
        Wait for any element matching the selectors to appear
        
        Args:
            selectors: List of selectors
            timeout: Timeout duration
            
        Returns:
            First found element or None
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            for selector in selectors:
                element = self._try_single_selector(selector, 0.1)
                if element:
                    return element
            time.sleep(0.1)
        
        return None
    
    def _try_single_selector(self, selector: str, timeout: int) -> Optional[Any]:
        """Try single selector"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except (TimeoutException, NoSuchElementException):
            return None
    
    def _try_clickable_selector(self, selector: str, timeout: int) -> Optional[Any]:
        """Try single clickable selector"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        except (TimeoutException, NoSuchElementException):
            return None
    
    def _check_page_loading_complete(self) -> bool:
        """Check if page loading is complete"""
        try:
            return self.driver.execute_script("return document.readyState") == "complete"
        except Exception:
            return False
