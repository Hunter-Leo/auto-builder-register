"""
DropMail Test File

Tests various functions of the DropMail class
"""

import unittest
from unittest.mock import patch, MagicMock
from dropmail import DropMail, Mail, Address, Session


class TestDropMail(unittest.TestCase):
    """DropMail test class"""
    
    def setUp(self):
        """Setup before tests"""
        self.dropmail = DropMail("test_token_12345678")
    
    def test_init(self):
        """Test initialization"""
        # Test with specified token
        dm = DropMail("custom_token")
        self.assertEqual(dm.auth_token, "custom_token")
        
        # Test auto-generated token
        dm2 = DropMail()
        self.assertIsNotNone(dm2.auth_token)
        self.assertGreaterEqual(len(dm2.auth_token), 8)
    
    @patch('requests.post')
    def test_get_domains(self, mock_post):
        """Test getting domain list"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "domains": [
                    {"id": "1", "name": "dropmail.me", "availableVia": ["API"]},
                    {"id": "2", "name": "10mail.org", "availableVia": ["API"]}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        domains = self.dropmail.get_domains()
        
        self.assertEqual(len(domains), 2)
        self.assertEqual(domains[0]["name"], "dropmail.me")
        self.assertEqual(domains[1]["name"], "10mail.org")
    
    @patch('requests.post')
    def test_create_session(self, mock_post):
        """Test creating session"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "introduceSession": {
                    "id": "session123",
                    "expiresAt": "2024-01-01T00:00:00Z",
                    "addresses": [
                        {
                            "id": "addr123",
                            "address": "test@dropmail.me",
                            "restoreKey": "key123"
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        session = self.dropmail.create_session()
        
        self.assertEqual(session.id, "session123")
        self.assertEqual(len(session.addresses), 1)
        self.assertEqual(session.addresses[0].address, "test@dropmail.me")
        self.assertEqual(self.dropmail.session_id, "session123")
    
    @patch('requests.post')
    def test_get_mails(self, mock_post):
        """Test getting emails"""
        # First set session ID
        self.dropmail.session_id = "session123"
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "session": {
                    "mails": [
                        {
                            "id": "mail123",
                            "fromAddr": "sender@example.com",
                            "toAddr": "test@dropmail.me",
                            "headerSubject": "Test Subject",
                            "text": "Test content",
                            "html": None,
                            "receivedAt": "2024-01-01T00:00:00Z",
                            "rawSize": 100,
                            "downloadUrl": "https://example.com/download"
                        }
                    ]
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        mails = self.dropmail.get_mails()
        
        self.assertEqual(len(mails), 1)
        self.assertEqual(mails[0].from_addr, "sender@example.com")
        self.assertEqual(mails[0].subject, "Test Subject")
    
    def test_get_temp_email_without_session(self):
        """Test getting temporary email without session"""
        with patch.object(self.dropmail, 'create_session') as mock_create:
            mock_session = Session(
                id="session123",
                expires_at="2024-01-01T00:00:00Z",
                addresses=[Address("addr123", "test@dropmail.me", "key123")],
                mails=[]
            )
            mock_create.return_value = mock_session
            
            email = self.dropmail.get_temp_email()
            
            self.assertEqual(email, "test@dropmail.me")
            mock_create.assert_called_once()
    
    def test_get_temp_email_with_existing_addresses(self):
        """Test getting temporary email with existing addresses"""
        self.dropmail.addresses = [Address("addr123", "existing@dropmail.me", "key123")]
        
        email = self.dropmail.get_temp_email()
        
        self.assertEqual(email, "existing@dropmail.me")
    
    @patch('smtplib.SMTP')
    def test_send_email(self, mock_smtp):
        """Test sending email"""
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        success = self.dropmail.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            from_email="sender@gmail.com",
            password="password123"
        )
        
        self.assertTrue(success)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("sender@gmail.com", "password123")
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
    
    def test_send_email_without_credentials(self):
        """Test sending email without credentials"""
        with self.assertRaises(Exception) as context:
            self.dropmail.send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                body="Test Body"
            )
        
        self.assertIn("Sending email requires sender email and password", str(context.exception))


def run_basic_test():
    """Run basic functionality test"""
    print("Starting basic functionality test...")
    
    try:
        # Create instance
        dropmail = DropMail()
        print(f"✓ DropMail instance created successfully, Token: {dropmail.auth_token}")
        
        # Test getting domains
        domains = dropmail.get_domains()
        print(f"✓ Domains retrieved successfully, total {len(domains)} domains")
        
        # Test creating session
        session = dropmail.create_session()
        print(f"✓ Session created successfully, Email: {session.addresses[0].address}")
        
        # Test getting emails
        mails = dropmail.get_mails()
        print(f"✓ Emails retrieved successfully, total {len(mails)} emails")
        
        print("All basic functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "="*50)
    
    # Run basic functionality test (requires network connection)
    run_basic_test()
