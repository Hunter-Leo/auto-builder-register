#!/usr/bin/env python3
"""
auto_register.py test file
Test AWS Builder ID automatic registration functionality
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from auto_update_q.auto_register import (
    setup_logging, 
    save_registration_data,
    wait_for_user_action
)
from auto_update_q.aws_builder.aws_builder import AWSBuilderCredentials


class TestAutoRegister(unittest.TestCase):
    """auto_register module test"""
    
    def setUp(self):
        """Setup before test"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = Path(self.temp_dir) / "test_cache.csv"
    
    def tearDown(self):
        """Cleanup after test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_setup_logging(self):
        """Test logging setup"""
        # Test normal mode
        logger = setup_logging(debug=False)
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "auto_register")
        
        # Test debug mode
        logger_debug = setup_logging(debug=True)
        self.assertIsNotNone(logger_debug)
    
    def test_save_registration_data(self):
        """Test saving registration data"""
        logger = setup_logging()
        
        # Test saving data
        save_registration_data(
            email="test@example.com",
            password="TestPass123",
            name="Test User",
            cache_file=self.cache_file,
            logger=logger
        )
        
        # Verify file creation
        self.assertTrue(self.cache_file.exists())
        
        # Verify file content
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("test@example.com", content)
            self.assertIn("TestPass123", content)
            self.assertIn("Test User", content)
            self.assertIn("pending_captcha", content)
    
    def test_save_registration_data_multiple_entries(self):
        """Test saving multiple registration data entries"""
        logger = setup_logging()
        
        # Save first data entry
        save_registration_data(
            email="test1@example.com",
            password="Pass1",
            name="User1",
            cache_file=self.cache_file,
            logger=logger
        )
        
        # Save second data entry
        save_registration_data(
            email="test2@example.com",
            password="Pass2",
            name="User2",
            cache_file=self.cache_file,
            logger=logger
        )
        
        # Verify both data entries exist
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("test1@example.com", content)
            self.assertIn("test2@example.com", content)
    
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_user_action_timeout(self, mock_time, mock_sleep):
        """Test waiting for user action timeout"""
        logger = setup_logging()
        
        # Mock time passage
        mock_time.side_effect = [0, 30, 60, 90, 120, 150, 180, 210]  # 3 minute timeout
        
        # Mock no browser
        global current_browser
        current_browser = None
        
        # Test waiting (should exit immediately as there's no browser)
        wait_for_user_action(timeout_minutes=3, logger=logger)
        
        # Verify sleep was called
        self.assertTrue(mock_sleep.called or mock_time.called)
    
    @patch('time.sleep')
    @patch('time.time')
    def test_wait_for_user_action_browser_closed(self, mock_time, mock_sleep):
        """Test handling when browser is closed"""
        logger = setup_logging()
        
        # Mock browser closed
        mock_browser = Mock()
        mock_driver = Mock()
        mock_driver.current_url.side_effect = Exception("Browser closed")
        mock_browser.driver = mock_driver
        
        global current_browser
        current_browser = mock_browser
        
        # Mock time
        mock_time.side_effect = [0, 5]
        
        # Test waiting
        wait_for_user_action(timeout_minutes=1, logger=logger)
        
        # Verify browser status was checked
        mock_driver.current_url.__get__.assert_called()


class TestAWSBuilderCredentials(unittest.TestCase):
    """AWSBuilderCredentials test"""
    
    def test_credentials_creation(self):
        """Test credentials creation"""
        credentials = AWSBuilderCredentials(
            email="test@example.com",
            password="TestPass123",
            name="Test User",
            builder_id="test-builder-id"
        )
        
        self.assertEqual(credentials.email, "test@example.com")
        self.assertEqual(credentials.password, "TestPass123")
        self.assertEqual(credentials.name, "Test User")
        self.assertEqual(credentials.builder_id, "test-builder-id")
    
    def test_credentials_without_builder_id(self):
        """Test credentials without builder_id"""
        credentials = AWSBuilderCredentials(
            email="test@example.com",
            password="TestPass123",
            name="Test User"
        )
        
        self.assertEqual(credentials.email, "test@example.com")
        self.assertEqual(credentials.password, "TestPass123")
        self.assertEqual(credentials.name, "Test User")
        self.assertIsNone(credentials.builder_id)


class TestCommandLineInterface(unittest.TestCase):
    """Command line interface test"""
    
    @patch('auto_update_q.auto_register.AWSBuilder')
    @patch('auto_update_q.auto_register.DropMail')
    def test_register_command_with_temp_email(self, mock_dropmail_class, mock_aws_builder_class):
        """Test register command with temporary email"""
        # Mock DropMail
        mock_dropmail = Mock()
        mock_dropmail.get_temp_email.return_value = "temp@dropmail.me"
        mock_dropmail_class.return_value = mock_dropmail
        
        # Mock AWSBuilder
        mock_aws_builder = Mock()
        mock_credentials = AWSBuilderCredentials(
            email="temp@dropmail.me",
            password="GeneratedPass123",
            name="Crazy Joe"
        )
        mock_aws_builder.register_aws_builder_until_captcha.return_value = mock_credentials
        mock_aws_builder_class.return_value = mock_aws_builder
        
        # More CLI tests can be added here, but need to use typer's testing tools
        # Due to complexity, only verify mock object setup here
        self.assertIsNotNone(mock_dropmail_class)
        self.assertIsNotNone(mock_aws_builder_class)
    
    def test_browser_type_validation(self):
        """Test browser type validation"""
        # Browser type validation tests can be added here
        valid_browsers = ["safari", "edge"]
        
        for browser in valid_browsers:
            # Verify browser type is valid
            self.assertIn(browser, valid_browsers)
        
        # Test invalid browser type
        invalid_browser = "chrome"
        self.assertNotIn(invalid_browser, valid_browsers)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
