"""
DropMail 临时邮箱类

基于 dropmail.me API 实现的临时邮箱功能
"""

import json
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


@dataclass
class Mail:
    """邮件数据类"""
    id: str
    from_addr: str
    to_addr: str
    subject: str
    text: str
    html: Optional[str]
    received_at: str
    raw_size: int
    download_url: str
    raw: Optional[str] = None


@dataclass
class Address:
    """邮箱地址数据类"""
    id: str
    address: str
    restore_key: str


@dataclass
class Session:
    """会话数据类"""
    id: str
    expires_at: str
    addresses: List[Address]
    mails: List[Mail]


class DropMail:
    """DropMail 临时邮箱类"""
    
    def __init__(self, auth_token: Optional[str] = None):
        """
        初始化 DropMail 实例
        
        Args:
            auth_token: 认证令牌，如果不提供则自动生成
        """
        self.auth_token = auth_token or self._generate_auth_token()
        self.base_url = "https://dropmail.me/api/graphql"
        self.session_id: Optional[str] = None
        self.addresses: List[Address] = []
        
    def _generate_auth_token(self) -> str:
        """生成认证令牌"""
        return str(uuid.uuid4()).replace('-', '')[:16]
    
    def _make_request(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        发送 GraphQL 请求
        
        Args:
            query: GraphQL 查询语句
            variables: 查询变量
            
        Returns:
            API 响应数据
        """
        url = f"{self.base_url}/{self.auth_token}"
        
        payload = {
            "query": query
        }
        
        if variables:
            payload["variables"] = variables
            
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            raise Exception(f"GraphQL Error: {data['errors']}")
            
        return data["data"]
    
    def get_domains(self) -> List[Dict[str, Any]]:
        """
        获取可用域名列表
        
        Returns:
            域名列表
        """
        query = """
        query {
            domains {
                id,
                name,
                availableVia
            }
        }
        """
        
        data = self._make_request(query)
        return data["domains"]
    
    def create_session(self, domain_id: Optional[str] = None) -> Session:
        """
        创建新的邮箱会话
        
        Args:
            domain_id: 指定域名ID，如果不提供则使用随机域名
            
        Returns:
            创建的会话对象
        """
        if domain_id:
            query = """
            mutation($domainId: ID!) {
                introduceSession(input: {withAddress: true, domainId: $domainId}) {
                    id,
                    expiresAt,
                    addresses {
                        id,
                        address,
                        restoreKey
                    }
                }
            }
            """
            variables = {"domainId": domain_id}
        else:
            query = """
            mutation {
                introduceSession {
                    id,
                    expiresAt,
                    addresses {
                        id,
                        address,
                        restoreKey
                    }
                }
            }
            """
            variables = None
        
        data = self._make_request(query, variables)
        session_data = data["introduceSession"]
        
        # 解析地址数据
        addresses = []
        for addr_data in session_data["addresses"]:
            addresses.append(Address(
                id=addr_data["id"],
                address=addr_data["address"],
                restore_key=addr_data.get("restoreKey", "")
            ))
        
        # 创建会话对象
        session = Session(
            id=session_data["id"],
            expires_at=session_data["expiresAt"],
            addresses=addresses,
            mails=[]
        )
        
        # 保存会话信息
        self.session_id = session.id
        self.addresses = addresses
        
        return session
    
    def add_address(self, domain_id: Optional[str] = None) -> Address:
        """
        为当前会话添加新的邮箱地址
        
        Args:
            domain_id: 指定域名ID，如果不提供则使用随机域名
            
        Returns:
            新创建的地址对象
        """
        if not self.session_id:
            raise Exception("No active session. Please create a session first.")
        
        if domain_id:
            query = """
            mutation($sessionId: ID!, $domainId: ID!) {
                introduceAddress(input: {sessionId: $sessionId, domainId: $domainId}) {
                    id,
                    address,
                    restoreKey
                }
            }
            """
            variables = {"sessionId": self.session_id, "domainId": domain_id}
        else:
            query = """
            mutation($sessionId: ID!) {
                introduceAddress(input: {sessionId: $sessionId}) {
                    id,
                    address,
                    restoreKey
                }
            }
            """
            variables = {"sessionId": self.session_id}
        
        data = self._make_request(query, variables)
        addr_data = data["introduceAddress"]
        
        address = Address(
            id=addr_data["id"],
            address=addr_data["address"],
            restore_key=addr_data.get("restoreKey", "")
        )
        
        self.addresses.append(address)
        return address
    
    def get_temp_email(self) -> str:
        """
        获取临时邮箱地址
        
        Returns:
            临时邮箱地址
        """
        if not self.addresses:
            session = self.create_session()
            return session.addresses[0].address
        
        return self.addresses[0].address
    
    def get_mails(self, after_mail_id: Optional[str] = None) -> List[Mail]:
        """
        获取邮件列表
        
        Args:
            after_mail_id: 获取指定邮件ID之后的邮件
            
        Returns:
            邮件列表
        """
        if not self.session_id:
            raise Exception("No active session. Please create a session first.")
        
        if after_mail_id:
            query = """
            query($sessionId: ID!, $mailId: ID!) {
                session(id: $sessionId) {
                    mailsAfterId(mailId: $mailId) {
                        id,
                        fromAddr,
                        toAddr,
                        headerSubject,
                        text,
                        html,
                        receivedAt,
                        rawSize,
                        downloadUrl,
                        raw
                    }
                }
            }
            """
            variables = {"sessionId": self.session_id, "mailId": after_mail_id}
        else:
            query = """
            query($sessionId: ID!) {
                session(id: $sessionId) {
                    mails {
                        id,
                        fromAddr,
                        toAddr,
                        headerSubject,
                        text,
                        html,
                        receivedAt,
                        rawSize,
                        downloadUrl,
                        raw
                    }
                }
            }
            """
            variables = {"sessionId": self.session_id}
        
        data = self._make_request(query, variables)
        
        if not data["session"]:
            raise Exception("Session not found or expired")
        
        mail_field = "mailsAfterId" if after_mail_id else "mails"
        mails_data = data["session"][mail_field]
        
        mails = []
        for mail_data in mails_data:
            mail = Mail(
                id=mail_data["id"],
                from_addr=mail_data["fromAddr"],
                to_addr=mail_data["toAddr"],
                subject=mail_data.get("headerSubject", ""),
                text=mail_data.get("text", ""),
                html=mail_data.get("html"),
                received_at=mail_data["receivedAt"],
                raw_size=mail_data["rawSize"],
                download_url=mail_data["downloadUrl"],
                raw=mail_data.get("raw")
            )
            mails.append(mail)
        
        return mails
    
    def wait_for_mail(self, timeout: int = 300, check_interval: int = 5) -> Optional[Mail]:
        """
        等待接收邮件
        
        Args:
            timeout: 超时时间（秒）
            check_interval: 检查间隔（秒）
            
        Returns:
            接收到的邮件，如果超时则返回 None
        """
        start_time = time.time()
        last_mail_id = None
        
        # 获取当前已有的邮件
        existing_mails = self.get_mails()
        if existing_mails:
            last_mail_id = existing_mails[-1].id
        
        while time.time() - start_time < timeout:
            try:
                if last_mail_id:
                    new_mails = self.get_mails(after_mail_id=last_mail_id)
                else:
                    new_mails = self.get_mails()
                
                if new_mails:
                    return new_mails[0]  # 返回第一封新邮件
                
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"Error checking for mails: {e}")
                time.sleep(check_interval)
        
        return None
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   smtp_server: str = "smtp.gmail.com", smtp_port: int = 587,
                   from_email: Optional[str] = None, password: Optional[str] = None,
                   is_html: bool = False) -> bool:
        """
        发送邮件（使用外部SMTP服务器）
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            body: 邮件内容
            smtp_server: SMTP服务器地址
            smtp_port: SMTP服务器端口
            from_email: 发件人邮箱
            password: 发件人邮箱密码
            is_html: 是否为HTML格式
            
        Returns:
            发送是否成功
        """
        if not from_email or not password:
            raise Exception("发送邮件需要提供发件人邮箱和密码")
        
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加邮件内容
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # 连接SMTP服务器并发送邮件
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # 启用TLS加密
            server.login(from_email, password)
            
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False
    
    def get_session_info(self) -> Optional[Session]:
        """
        获取当前会话信息
        
        Returns:
            会话信息，如果没有活动会话则返回 None
        """
        if not self.session_id:
            return None
        
        query = """
        query($sessionId: ID!) {
            session(id: $sessionId) {
                id,
                expiresAt,
                addresses {
                    id,
                    address,
                    restoreKey
                },
                mails {
                    id,
                    fromAddr,
                    toAddr,
                    headerSubject,
                    text,
                    html,
                    receivedAt,
                    rawSize,
                    downloadUrl
                }
            }
        }
        """
        
        variables = {"sessionId": self.session_id}
        
        try:
            data = self._make_request(query, variables)
            
            if not data["session"]:
                return None
            
            session_data = data["session"]
            
            # 解析地址数据
            addresses = []
            for addr_data in session_data["addresses"]:
                addresses.append(Address(
                    id=addr_data["id"],
                    address=addr_data["address"],
                    restore_key=addr_data.get("restoreKey", "")
                ))
            
            # 解析邮件数据
            mails = []
            for mail_data in session_data["mails"]:
                mail = Mail(
                    id=mail_data["id"],
                    from_addr=mail_data["fromAddr"],
                    to_addr=mail_data["toAddr"],
                    subject=mail_data.get("headerSubject", ""),
                    text=mail_data.get("text", ""),
                    html=mail_data.get("html"),
                    received_at=mail_data["receivedAt"],
                    raw_size=mail_data["rawSize"],
                    download_url=mail_data["downloadUrl"]
                )
                mails.append(mail)
            
            return Session(
                id=session_data["id"],
                expires_at=session_data["expiresAt"],
                addresses=addresses,
                mails=mails
            )
            
        except Exception as e:
            print(f"获取会话信息失败: {e}")
            return None
