"""
浏览器管理器
负责浏览器的初始化、配置和基础操作
支持 Safari 和 Edge 浏览器
"""

import logging
from typing import Optional, Union
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.safari.options import Options as SafariOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from .config import BROWSER_OPTIONS


class BrowserManager:
    """浏览器管理器"""
    
    def __init__(self, headless: bool = False, browser_type: str = "safari", 
                 logger: Optional[logging.Logger] = None):
        """
        初始化浏览器管理器
        
        Args:
            headless: 是否使用无头模式
            browser_type: 浏览器类型 ("safari" 或 "edge")
            logger: 日志记录器
        """
        self.headless = headless
        self.browser_type = browser_type.lower()
        self.logger = logger or logging.getLogger(__name__)
        self.driver: Optional[Union[webdriver.Safari, webdriver.Edge]] = None
    
    def setup_driver(self) -> Union[webdriver.Safari, webdriver.Edge]:
        """设置并返回浏览器驱动"""
        if self.browser_type == "safari":
            return self._setup_safari_driver()
        elif self.browser_type == "edge":
            return self._setup_edge_driver()
        else:
            raise ValueError(f"不支持的浏览器类型: {self.browser_type}")
    
    def _setup_safari_driver(self) -> webdriver.Safari:
        """设置 Safari 浏览器驱动"""
        self.logger.info("正在设置 Safari 浏览器驱动...")
        
        if self.headless:
            self.logger.warning("Safari 不支持无头模式，将使用有界面模式")
        
        try:
            options = SafariOptions()
            driver = webdriver.Safari(options=options)
            self._configure_driver(driver)
            self.logger.info("Safari 浏览器驱动设置成功")
            return driver
            
        except Exception as e:
            self.logger.error(f"设置 Safari 浏览器驱动失败: {e}")
            self._log_safari_setup_help()
            raise
    
    def _setup_edge_driver(self) -> webdriver.Edge:
        """设置 Edge 浏览器驱动"""
        self.logger.info("正在设置 Edge 浏览器驱动...")
        
        options = self._create_edge_options()
        
        try:
            # 尝试使用系统已安装的 Edge 驱动
            driver = self._try_system_edge_driver(options)
            if driver:
                return driver
            
            # 使用 WebDriver Manager 下载驱动
            return self._try_webdriver_manager(options)
            
        except Exception as e:
            self.logger.error(f"设置 Edge 浏览器驱动失败: {e}")
            self._log_edge_setup_help()
            raise
    
    def _create_edge_options(self) -> EdgeOptions:
        """创建 Edge 浏览器选项"""
        options = EdgeOptions()
        
        # 添加通用参数
        for arg in BROWSER_OPTIONS["common_args"]:
            options.add_argument(arg)
        
        # 添加无头模式参数
        if self.headless:
            for arg in BROWSER_OPTIONS["headless_args"]:
                options.add_argument(arg)
        
        # 添加实验性选项
        for key, value in BROWSER_OPTIONS["experimental_options"].items():
            options.add_experimental_option(key, value)
        
        return options
    
    def _try_system_edge_driver(self, options: EdgeOptions) -> Optional[webdriver.Edge]:
        """尝试使用系统 Edge 驱动"""
        try:
            self.logger.info("尝试使用系统 Edge 驱动...")
            driver = webdriver.Edge(options=options)
            self._configure_driver(driver)
            self.logger.info("使用系统 Edge 驱动成功")
            return driver
        except Exception as e:
            self.logger.info(f"系统 Edge 驱动不可用: {e}")
            return None
    
    def _try_webdriver_manager(self, options: EdgeOptions) -> webdriver.Edge:
        """使用 WebDriver Manager 下载驱动"""
        self.logger.info("尝试使用 WebDriver Manager 下载驱动...")
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)
        self._configure_driver(driver)
        self.logger.info("WebDriver Manager 设置成功")
        return driver
    
    def _configure_driver(self, driver: Union[webdriver.Safari, webdriver.Edge]) -> None:
        """配置驱动器"""
        driver.implicitly_wait(10)
        
        # 对于支持的浏览器执行反检测脚本
        try:
            if isinstance(driver, webdriver.Edge):
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            self.logger.warning(f"执行反检测脚本失败: {e}")
    
    def _log_safari_setup_help(self) -> None:
        """记录 Safari 设置帮助信息"""
        self.logger.error("Safari 浏览器设置失败，请确保：")
        self.logger.error("1. 已安装 Safari 浏览器")
        self.logger.error("2. 在 Safari 偏好设置 > 高级 中启用了 '在菜单栏中显示开发菜单'")
        self.logger.error("3. 在 开发 菜单中启用了 '允许远程自动化'")
    
    def _log_edge_setup_help(self) -> None:
        """记录 Edge 设置帮助信息"""
        self.logger.error("Edge 浏览器设置失败，请确保：")
        self.logger.error("1. 已安装 Microsoft Edge 浏览器")
        self.logger.error("2. 网络连接正常")
        self.logger.error("3. 或手动下载 EdgeDriver 并添加到 PATH")
    
    def close_driver(self, driver: Optional[Union[webdriver.Safari, webdriver.Edge]]) -> None:
        """关闭浏览器驱动"""
        if driver:
            try:
                driver.quit()
                self.logger.info("浏览器已关闭")
            except Exception as e:
                self.logger.error(f"关闭浏览器时出错: {e}")
