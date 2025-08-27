"""
元素等待器
负责页面元素的等待和查找逻辑
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
    """元素等待器"""
    
    def __init__(self, driver: webdriver.Edge, logger: Optional[logging.Logger] = None):
        """
        初始化元素等待器
        
        Args:
            driver: 浏览器驱动
            logger: 日志记录器
        """
        self.driver = driver
        self.logger = logger or logging.getLogger(__name__)
    
    def wait_for_element_with_retry(self, selectors: List[str], element_name: str, 
                                  max_rounds: Optional[int] = None, 
                                  timeout_per_selector: Optional[int] = None) -> Optional[Any]:
        """
        使用多个选择器等待元素，支持多轮重试
        
        Args:
            selectors: 选择器列表
            element_name: 元素名称（用于日志）
            max_rounds: 最大重试轮数
            timeout_per_selector: 每个选择器的超时时间
            
        Returns:
            找到的元素或None
        """
        # 使用优化配置或默认值
        max_rounds = max_rounds or get_retry_config(element_name, "max_rounds", DEFAULT_RETRY_ROUNDS)
        timeout_per_selector = timeout_per_selector or get_retry_config(element_name, "timeout", DEFAULT_RETRY_TIMEOUT)
        
        self.logger.info(f"开始等待元素: {element_name}")
        
        for round_num in range(1, max_rounds + 1):
            self.logger.debug(f"第 {round_num}/{max_rounds} 轮尝试")
            
            for i, selector in enumerate(selectors, 1):
                self.logger.debug(f"  尝试选择器 {i}/{len(selectors)}: {selector}")
                
                element = self._try_single_selector(selector, timeout_per_selector)
                if element:
                    self.logger.info(f"✓ 找到元素 {element_name}，使用选择器: {selector}")
                    return element
            
            if round_num < max_rounds:
                wait_time = min(2 ** round_num, 8)  # 指数退避，最大8秒
                self.logger.debug(f"第 {round_num} 轮失败，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        self.logger.warning(f"✗ 所有尝试失败，未找到元素: {element_name}")
        return None
    
    def wait_for_clickable_with_retry(self, selectors: List[str], element_name: str,
                                    max_rounds: int = 3, 
                                    timeout_per_selector: int = 3) -> Optional[Any]:
        """
        使用多个选择器等待可点击元素，支持多轮重试
        
        Args:
            selectors: 选择器列表
            element_name: 元素名称
            max_rounds: 最大重试轮数
            timeout_per_selector: 每个选择器的超时时间
            
        Returns:
            找到的可点击元素或None
        """
        self.logger.info(f"开始等待可点击元素: {element_name}")
        
        for round_num in range(1, max_rounds + 1):
            self.logger.debug(f"第 {round_num}/{max_rounds} 轮尝试")
            
            for i, selector in enumerate(selectors, 1):
                self.logger.debug(f"  尝试选择器 {i}/{len(selectors)}: {selector}")
                
                element = self._try_clickable_selector(selector, timeout_per_selector)
                if element:
                    self.logger.info(f"✓ 找到可点击元素 {element_name}，使用选择器: {selector}")
                    return element
            
            if round_num < max_rounds:
                wait_time = 2
                self.logger.debug(f"第 {round_num} 轮失败，等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        self.logger.warning(f"✗ 所有尝试失败，未找到可点击元素: {element_name}")
        return None
    
    def wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> Optional[Any]:
        """等待单个元素出现"""
        wait_timeout = timeout or DEFAULT_TIMEOUT
        try:
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            self.logger.warning(f"等待元素超时: {by}={value}")
            return None
    
    def wait_for_clickable(self, by: By, value: str, timeout: Optional[int] = None) -> Optional[Any]:
        """等待单个元素可点击"""
        wait_timeout = timeout or DEFAULT_TIMEOUT
        try:
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            self.logger.warning(f"等待可点击元素超时: {by}={value}")
            return None
    
    def wait_for_element_interactive(self, element, timeout: int = 10) -> bool:
        """
        等待元素变为可交互状态
        
        Args:
            element: 页面元素
            timeout: 超时时间
            
        Returns:
            是否成功变为可交互状态
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if element.is_displayed() and element.is_enabled():
                    return True
                time.sleep(0.1)
            except StaleElementReferenceException:
                self.logger.warning("元素引用过期，重新查找")
                return False
            except Exception as e:
                self.logger.warning(f"检查元素交互状态时出错: {e}")
                time.sleep(0.1)
        
        self.logger.warning("等待元素可交互超时")
        return False
    
    def wait_for_page_change(self, timeout: int = 10) -> bool:
        """
        等待页面变化（URL变化或新元素出现）
        
        Args:
            timeout: 超时时间
            
        Returns:
            是否检测到页面变化
        """
        initial_url = self.driver.current_url
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                current_url = self.driver.current_url
                if current_url != initial_url:
                    self.logger.info(f"检测到页面变化: {current_url}")
                    return True
                
                # 检查页面是否有新的加载状态
                if self._check_page_loading_complete():
                    time.sleep(0.5)  # 给页面一点时间稳定
                    return True
                
                time.sleep(0.2)
                
            except Exception as e:
                self.logger.warning(f"检查页面变化时出错: {e}")
                time.sleep(0.2)
        
        self.logger.debug("未检测到页面变化")
        return False
    
    def wait_for_redirect(self, initial_url: str, max_wait: int = 30) -> bool:
        """
        动态等待页面重定向完成
        
        Args:
            initial_url: 初始URL
            max_wait: 最大等待时间
            
        Returns:
            是否成功重定向
        """
        self.logger.info(f"等待页面重定向，初始URL: {initial_url}")
        
        start_time = time.time()
        last_url = initial_url
        stable_count = 0
        
        while time.time() - start_time < max_wait:
            try:
                current_url = self.driver.current_url
                
                if current_url != initial_url:
                    if current_url == last_url:
                        stable_count += 1
                        if stable_count >= 3:  # URL稳定3次检查
                            self.logger.info(f"页面重定向完成: {current_url}")
                            return True
                    else:
                        stable_count = 0
                        last_url = current_url
                        self.logger.debug(f"检测到URL变化: {current_url}")
                
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.warning(f"检查重定向时出错: {e}")
                time.sleep(0.5)
        
        self.logger.warning(f"等待重定向超时，当前URL: {self.driver.current_url}")
        return False
    
    def wait_for_any_element(self, selectors: List[str], timeout: int = 10) -> Optional[Any]:
        """
        等待任意一个选择器匹配的元素出现
        
        Args:
            selectors: 选择器列表
            timeout: 超时时间
            
        Returns:
            找到的第一个元素或None
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
        """尝试单个选择器"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except (TimeoutException, NoSuchElementException):
            return None
    
    def _try_clickable_selector(self, selector: str, timeout: int) -> Optional[Any]:
        """尝试单个可点击选择器"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        except (TimeoutException, NoSuchElementException):
            return None
    
    def _check_page_loading_complete(self) -> bool:
        """检查页面是否加载完成"""
        try:
            return self.driver.execute_script("return document.readyState") == "complete"
        except Exception:
            return False
