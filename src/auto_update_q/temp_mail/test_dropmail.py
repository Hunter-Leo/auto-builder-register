"""
DropMail 测试文件

测试 DropMail 类的各项功能
"""

import unittest
from unittest.mock import patch, MagicMock
from dropmail import DropMail, Mail, Address, Session


class TestDropMail(unittest.TestCase):
    """DropMail 测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.dropmail = DropMail("test_token_12345678")
    
    def test_init(self):
        """测试初始化"""
        # 测试使用指定token
        dm = DropMail("custom_token")
        self.assertEqual(dm.auth_token, "custom_token")
        
        # 测试自动生成token
        dm2 = DropMail()
        self.assertIsNotNone(dm2.auth_token)
        self.assertGreaterEqual(len(dm2.auth_token), 8)
    
    @patch('requests.post')
    def test_get_domains(self, mock_post):
        """测试获取域名列表"""
        # 模拟API响应
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
        """测试创建会话"""
        # 模拟API响应
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
        """测试获取邮件"""
        # 先设置会话ID
        self.dropmail.session_id = "session123"
        
        # 模拟API响应
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
        """测试在没有会话时获取临时邮箱"""
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
        """测试在已有地址时获取临时邮箱"""
        self.dropmail.addresses = [Address("addr123", "existing@dropmail.me", "key123")]
        
        email = self.dropmail.get_temp_email()
        
        self.assertEqual(email, "existing@dropmail.me")
    
    @patch('smtplib.SMTP')
    def test_send_email(self, mock_smtp):
        """测试发送邮件"""
        # 模拟SMTP服务器
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
        """测试没有提供凭据时发送邮件"""
        with self.assertRaises(Exception) as context:
            self.dropmail.send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                body="Test Body"
            )
        
        self.assertIn("发送邮件需要提供发件人邮箱和密码", str(context.exception))


def run_basic_test():
    """运行基本功能测试"""
    print("开始基本功能测试...")
    
    try:
        # 创建实例
        dropmail = DropMail()
        print(f"✓ 创建 DropMail 实例成功，Token: {dropmail.auth_token}")
        
        # 测试获取域名
        domains = dropmail.get_domains()
        print(f"✓ 获取域名成功，共 {len(domains)} 个域名")
        
        # 测试创建会话
        session = dropmail.create_session()
        print(f"✓ 创建会话成功，邮箱: {session.addresses[0].address}")
        
        # 测试获取邮件
        mails = dropmail.get_mails()
        print(f"✓ 获取邮件成功，共 {len(mails)} 封邮件")
        
        print("所有基本功能测试通过!")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False


if __name__ == "__main__":
    # 运行单元测试
    print("运行单元测试...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "="*50)
    
    # 运行基本功能测试（需要网络连接）
    run_basic_test()
