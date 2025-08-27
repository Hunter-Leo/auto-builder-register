"""
注册状态检查器
负责检查AWS Builder ID注册状态和结果
"""

import logging
import time
from typing import Optional, Dict, Any
from selenium import webdriver

from .element_waiter import ElementWaiter
from .optimized_selectors import get_selector


class RegistrationChecker:
    """注册状态检查器"""
    
    def __init__(self, driver: webdriver.Edge, element_waiter: ElementWaiter,
                 logger: Optional[logging.Logger] = None):
        """
        初始化注册状态检查器
        
        Args:
            driver: 浏览器驱动
            element_waiter: 元素等待器
            logger: 日志记录器
        """
        self.driver = driver
        self.element_waiter = element_waiter
        self.logger = logger or logging.getLogger(__name__)
    
    def check_registration_success(self) -> bool:
        """
        检查注册是否成功
        
        Returns:
            是否注册成功
        """
        self.logger.info("检查注册状态...")
        
        # 等待页面稳定
        self.element_waiter.wait_for_page_change(timeout=5)
        
        current_url = self.driver.current_url
        self.logger.info(f"当前URL: {current_url}")
        
        # 检查成功指标
        success_indicators = [
            self._check_success_url(),
            self._check_success_elements(),
            self._check_dashboard_access(),
        ]
        
        # 检查失败指标
        failure_indicators = [
            self._check_error_messages(),
            self._check_registration_form_still_present(),
        ]
        
        success_count = sum(success_indicators)
        failure_count = sum(failure_indicators)
        
        self.logger.info(f"成功指标: {success_count}/3, 失败指标: {failure_count}/2")
        
        if success_count >= 2:
            self.logger.info("✓ 注册成功")
            return True
        elif failure_count >= 1:
            self.logger.warning("✗ 注册失败")
            return False
        else:
            self.logger.info("注册状态不明确，可能需要更多时间")
            return False
    
    def get_registration_info(self) -> Dict[str, Any]:
        """
        获取注册相关信息
        
        Returns:
            包含注册信息的字典
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
        等待注册流程完成
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            是否成功完成注册
        """
        self.logger.info(f"等待注册完成，超时时间: {timeout}秒")
        
        start_time = time.time()
        last_url = self.driver.current_url
        check_interval = 2
        
        while time.time() - start_time < timeout:
            try:
                current_url = self.driver.current_url
                
                # 检查URL变化
                if current_url != last_url:
                    self.logger.info(f"URL变化: {current_url}")
                    last_url = current_url
                
                # 检查注册状态
                if self.check_registration_success():
                    return True
                
                # 检查是否有错误
                if self._check_error_messages():
                    self.logger.error("检测到错误消息，注册失败")
                    return False
                
                # 动态调整检查间隔
                remaining_time = timeout - (time.time() - start_time)
                if remaining_time < 10:
                    check_interval = 0.5  # 最后10秒更频繁检查
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.warning(f"等待注册完成时出错: {e}")
                time.sleep(check_interval)
        
        self.logger.warning("等待注册完成超时")
        return False
    
    def _check_success_url(self) -> bool:
        """检查成功URL模式"""
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
                self.logger.info(f"✓ 检测到成功URL模式: {pattern}")
                return True
        
        return False
    
    def _check_success_elements(self) -> bool:
        """检查成功页面元素"""
        success_selectors = get_selector("success_indicators")
        
        # 使用快速检查，不等待太久
        element = self.element_waiter.wait_for_any_element(success_selectors, timeout=3)
        if element and element.is_displayed():
            self.logger.info("✓ 检测到成功元素")
            return True
        
        return False
    
    def _check_dashboard_access(self) -> bool:
        """检查是否能访问控制台"""
        dashboard_selectors = get_selector("dashboard_elements")
        
        # 使用快速检查
        element = self.element_waiter.wait_for_any_element(dashboard_selectors, timeout=3)
        if element and element.is_displayed():
            self.logger.info("✓ 检测到控制台元素")
            return True
        
        return False
    
    def _check_error_messages(self) -> bool:
        """检查错误消息"""
        error_selectors = get_selector("error_messages")
        
        # 快速检查错误消息
        element = self.element_waiter.wait_for_any_element(error_selectors, timeout=1)
        if element and element.is_displayed():
            error_text = element.text
            self.logger.warning(f"✗ 检测到错误消息: {error_text}")
            return True
        
        return False
    
    def _check_registration_form_still_present(self) -> bool:
        """检查注册表单是否仍然存在"""
        form_selectors = get_selector("registration_form")
        
        # 快速检查表单是否还在
        element = self.element_waiter.wait_for_any_element(form_selectors, timeout=2)
        if element and element.is_displayed():
            self.logger.warning("✗ 注册表单仍然存在")
            return True
        
        return False
    
    def _get_page_title(self) -> Optional[str]:
        """获取页面标题"""
        try:
            return self.driver.title
        except Exception as e:
            self.logger.warning(f"获取页面标题失败: {e}")
            return None
    
    def _extract_builder_id(self) -> Optional[str]:
        """提取Builder ID"""
        try:
            # 尝试从URL中提取
            current_url = self.driver.current_url
            if "builder" in current_url.lower():
                # 这里可以添加具体的提取逻辑
                pass
            
            # 尝试从页面元素中提取
            builder_id_selectors = get_selector("builder_id_display")
            element = self.element_waiter.wait_for_any_element(builder_id_selectors, timeout=2)
            if element:
                builder_id = element.text.strip()
                if builder_id:
                    self.logger.info(f"提取到Builder ID: {builder_id}")
                    return builder_id
            
            return None
            
        except Exception as e:
            self.logger.warning(f"提取Builder ID失败: {e}")
            return None
