"""
Browser Manager
Responsible for browser initialization, configuration and basic operations
Supports Safari and Edge browsers
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
    """Browser Manager"""
    
    def __init__(self, headless: bool = False, browser_type: str = "safari", 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize browser manager
        
        Args:
            headless: Whether to use headless mode
            browser_type: Browser type ("safari" or "edge")
            logger: Logger instance
        """
        self.headless = headless
        self.browser_type = browser_type.lower()
        self.logger = logger or logging.getLogger(__name__)
        self.driver: Optional[Union[webdriver.Safari, webdriver.Edge]] = None
    
    def setup_driver(self) -> Union[webdriver.Safari, webdriver.Edge]:
        """Setup and return browser driver"""
        if self.browser_type == "safari":
            return self._setup_safari_driver()
        elif self.browser_type == "edge":
            return self._setup_edge_driver()
        else:
            raise ValueError(f"Unsupported browser type: {self.browser_type}")
    
    def _setup_safari_driver(self) -> webdriver.Safari:
        """Setup Safari browser driver"""
        self.logger.info("Setting up Safari browser driver...")
        
        if self.headless:
            self.logger.warning("Safari does not support headless mode, using GUI mode")
        
        try:
            options = SafariOptions()
            driver = webdriver.Safari(options=options)
            self._configure_driver(driver)
            self.logger.info("Safari browser driver setup successful")
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to setup Safari browser driver: {e}")
            self._log_safari_setup_help()
            raise
    
    def _setup_edge_driver(self) -> webdriver.Edge:
        """Setup Edge browser driver"""
        self.logger.info("Setting up Edge browser driver...")
        
        options = self._create_edge_options()
        
        try:
            # Try using system installed Edge driver
            driver = self._try_system_edge_driver(options)
            if driver:
                return driver
            
            # Use WebDriver Manager to download driver
            return self._try_webdriver_manager(options)
            
        except Exception as e:
            self.logger.error(f"Failed to setup Edge browser driver: {e}")
            self._log_edge_setup_help()
            raise
    
    def _create_edge_options(self) -> EdgeOptions:
        """Create Edge browser options"""
        options = EdgeOptions()
        
        # Add common arguments
        for arg in BROWSER_OPTIONS["common_args"]:
            options.add_argument(arg)
        
        # Add headless mode arguments
        if self.headless:
            for arg in BROWSER_OPTIONS["headless_args"]:
                options.add_argument(arg)
        
        # Add experimental options
        for key, value in BROWSER_OPTIONS["experimental_options"].items():
            options.add_experimental_option(key, value)
        
        return options
    
    def _try_system_edge_driver(self, options: EdgeOptions) -> Optional[webdriver.Edge]:
        """Try using system Edge driver"""
        try:
            self.logger.info("Trying to use system Edge driver...")
            driver = webdriver.Edge(options=options)
            self._configure_driver(driver)
            self.logger.info("System Edge driver setup successful")
            return driver
        except Exception as e:
            self.logger.info(f"System Edge driver not available: {e}")
            return None
    
    def _try_webdriver_manager(self, options: EdgeOptions) -> webdriver.Edge:
        """Use WebDriver Manager to download driver"""
        self.logger.info("Trying to use WebDriver Manager to download driver...")
        service = EdgeService(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)
        self._configure_driver(driver)
        self.logger.info("WebDriver Manager setup successful")
        return driver
    
    def _configure_driver(self, driver: Union[webdriver.Safari, webdriver.Edge]) -> None:
        """Configure driver"""
        driver.implicitly_wait(10)
        
        # Execute anti-detection script for supported browsers
        try:
            if isinstance(driver, webdriver.Edge):
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            self.logger.warning(f"Failed to execute anti-detection script: {e}")
    
    def _log_safari_setup_help(self) -> None:
        """Log Safari setup help information"""
        self.logger.error("Safari browser setup failed, please ensure:")
        self.logger.error("1. Safari browser is installed")
        self.logger.error("2. 'Show Develop menu in menu bar' is enabled in Safari Preferences > Advanced")
        self.logger.error("3. 'Allow Remote Automation' is enabled in Develop menu")
    
    def _log_edge_setup_help(self) -> None:
        """Log Edge setup help information"""
        self.logger.error("Edge browser setup failed, please ensure:")
        self.logger.error("1. Microsoft Edge browser is installed")
        self.logger.error("2. Network connection is available")
        self.logger.error("3. Or manually download EdgeDriver and add to PATH")
    
    def close_driver(self, driver: Optional[Union[webdriver.Safari, webdriver.Edge]]) -> None:
        """Close browser driver"""
        if driver:
            try:
                driver.quit()
                self.logger.info("Browser closed")
            except Exception as e:
                self.logger.error(f"Error closing browser: {e}")
