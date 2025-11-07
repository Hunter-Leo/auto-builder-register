"""
DropMail Temporary Email Class

Temporary email functionality based on dropmail.me API
Supports Session persistence and recovery functionality
"""

import json
import time
import uuid
import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


@dataclass
class SessionCache:
    """Session cache data class"""
    session_id: str
    auth_token: str
    email_address: str
    expires_at: str
    created_at: str
    last_accessed: str
    restore_keys: List[str]
    password: Optional[str] = None  # Add password field
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionCache':
        """Create instance from dictionary"""
        # Handle backward compatibility for existing cache files
        if 'password' not in data:
            data['password'] = None
        return cls(**data)


@dataclass
class Mail:
    """Email data class"""
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
    """Email address data class"""
    id: str
    address: str
    restore_key: str


@dataclass
class Session:
    """Session data class"""
    id: str
    expires_at: str
    addresses: List[Address]
    mails: List[Mail]


class DropMail:
    """DropMail temporary email class"""
    
    def __init__(self, auth_token: Optional[str] = None, cache_file: Optional[str] = None):
        """
        Initialize DropMail instance
        
        Args:
            auth_token: Authentication token, automatically generated if not provided
            cache_file: Cache file path, defaults to .cache/dropmail_sessions.json
        """
        self.auth_token = auth_token or self._generate_auth_token()
        self.base_url = "https://dropmail.me/api/graphql"
        self.session_id: Optional[str] = None
        self.addresses: List[Address] = []
        self.logger = logging.getLogger("dropmail")
        
        # Set cache file path
        if cache_file:
            self.cache_file = Path(cache_file)
        else:
            self.cache_file = Path(".cache/dropmail_sessions.json")
        
        # Ensure cache directory exists
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
    def _generate_auth_token(self) -> str:
        """Generate authentication token"""
        return str(uuid.uuid4()).replace('-', '')[:16]
    
    def save_successful_session(self, password: Optional[str] = None) -> bool:
        """
        Save session after successful registration
        
        Args:
            password: Password used for registration
        
        Returns:
            Whether save was successful
        """
        if not self.session_id or not self.addresses:
            return False
        
        try:
            # Read existing cache
            sessions = self._load_cache()
            
            # Create cache data
            session_cache = SessionCache(
                session_id=self.session_id,
                auth_token=self.auth_token,
                email_address=self.addresses[0].address if self.addresses else "",
                expires_at="",  # Will be updated during validation
                created_at=datetime.now().isoformat(),
                last_accessed=datetime.now().isoformat(),
                restore_keys=[addr.restore_key for addr in self.addresses],
                password=password
            )
            
            # Update expiration time
            session_info = self.get_session_info()
            if session_info:
                session_cache.expires_at = session_info.expires_at
            
            # Save to cache
            sessions[self.session_id] = session_cache.to_dict()
            
            # Write to file
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
            return False
    
    def update_last_accessed(self) -> bool:
        """
        Update last accessed time for current session
        
        Returns:
            Whether update was successful
        """
        if not self.session_id:
            return False
            
        try:
            sessions = self._load_cache()
            if self.session_id in sessions:
                sessions[self.session_id]['last_accessed'] = datetime.now().isoformat()
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(sessions, f, indent=2, ensure_ascii=False)
                return True
        except Exception as e:
            self.logger.error(f"Failed to update last accessed time: {e}")
        return False
        """
        Save current session to cache file
        
        Returns:
            Whether save was successful
        """
        if not self.session_id or not self.addresses:
            return False
        
        try:
            # Read existing cache
            sessions = self._load_cache()
            
            # Create cache data
            session_cache = SessionCache(
                session_id=self.session_id,
                auth_token=self.auth_token,
                email_address=self.addresses[0].address if self.addresses else "",
                expires_at="",  # Will be updated during validation
                created_at=datetime.now().isoformat(),
                last_accessed=datetime.now().isoformat(),
                restore_keys=[addr.restore_key for addr in self.addresses]
            )
            
            # Update expiration time
            session_info = self.get_session_info()
            if session_info:
                session_cache.expires_at = session_info.expires_at
            
            # Save to cache
            sessions[self.session_id] = session_cache.to_dict()
            
            # Write to file
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
            return False
    
    def _load_cache(self) -> Dict[str, Dict[str, Any]]:
        """
        Load cache file
        
        Returns:
            Cache data dictionary
        """
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load cache file: {e}")
            return {}
    
    def list_cached_sessions(self) -> List[SessionCache]:
        """
        List all cached sessions
        
        Returns:
            Session cache list
        """
        sessions_data = self._load_cache()
        sessions = []
        
        for session_data in sessions_data.values():
            try:
                sessions.append(SessionCache.from_dict(session_data))
            except Exception as e:
                self.logger.error(f"Failed to parse session data: {e}")
                continue
        
        # Sort by creation time
        sessions.sort(key=lambda x: x.created_at, reverse=True)
        return sessions
    
    def restore_session(self, session_id: str) -> bool:
        """
        Restore specified session (including expired ones using restore keys)
        
        Args:
            session_id: Session ID to restore
            
        Returns:
            Whether restore was successful
        """
        sessions_data = self._load_cache()
        
        if session_id not in sessions_data:
            self.logger.error(f"Session {session_id} not found")
            return False
        
        try:
            session_cache = SessionCache.from_dict(sessions_data[session_id])
            
            # Set authentication token and session ID
            self.auth_token = session_cache.auth_token
            self.session_id = session_id
            
            # First try to verify if session is still valid
            if self._verify_session():
                # Session is still valid, restore normally
                session_info = self.get_session_info()
                if session_info:
                    self.addresses = session_info.addresses
                    self.logger.info(f"Successfully restored active Session: {session_id}")
                    self.logger.info(f"Email address: {session_cache.email_address}")
                    return True
            else:
                # Session expired, try to restore using restore keys
                self.logger.info(f"Session {session_id} expired, attempting to restore using restore keys...")
                
                if session_cache.restore_keys:
                    success = self._restore_using_keys(session_cache.restore_keys)
                    if success:
                        self.logger.info(f"Successfully restored expired Session using restore keys")
                        self.logger.info(f"Email address: {session_cache.email_address}")
                        # Update session info in cache
                        self._update_restored_session(session_id, session_cache)
                        return True
                    else:
                        self.logger.warning(f"Failed to restore Session using restore keys")
                        return False
                else:
                    self.logger.warning(f"No restore keys available for Session {session_id}")
                    return False
                
        except Exception as e:
            self.logger.error(f"Failed to restore Session: {e}")
            return False
    
    def _restore_using_keys(self, restore_keys: List[str]) -> bool:
        """
        Restore session using restore keys
        
        Args:
            restore_keys: List of restore keys
            
        Returns:
            Whether restore was successful
        """
        # Get the original email address from cache
        sessions_data = self._load_cache()
        original_email = None
        
        if self.session_id in sessions_data:
            session_cache = SessionCache.from_dict(sessions_data[self.session_id])
            original_email = session_cache.email_address
        
        if not original_email:
            self.logger.error("Cannot find original email address for restore")
            return False
        
        # Create a new session first, then try to restore address to it
        try:
            new_session = self.create_session()
            new_session_id = self.session_id
        except Exception as e:
            self.logger.error(f"Failed to create new session: {e}")
            return False
        
        for restore_key in restore_keys:
            try:
                # Try with sessionId parameter
                query = """
                mutation($input: RestoreAddressInput!) {
                    restoreAddress(input: $input) {
                        id,
                        address,
                        restoreKey
                    }
                }
                """
                variables = {
                    "input": {
                        "sessionId": new_session_id,
                        "mailAddress": original_email,
                        "restoreKey": restore_key
                    }
                }
                
                data = self._make_request(query, variables)
                
                if "restoreAddress" in data and data["restoreAddress"]:
                    restore_data = data["restoreAddress"]
                    
                    # Update address information with restored address
                    self.addresses = [Address(
                        id=restore_data["id"],
                        address=restore_data["address"],
                        restore_key=restore_data["restoreKey"]
                    )]
                    
                    self.logger.info(f"Successfully restored address: {restore_data['address']}")
                    return True
                
            except Exception as e:
                # Restore keys can expire, this is expected behavior
                self.logger.debug(f"Restore attempt failed: {str(e)[:100]}...")
                continue
        
        self.logger.info("All restore keys have expired - this is normal for old sessions")
        return False
    
    def _update_restored_session(self, old_session_id: str, session_cache: SessionCache) -> None:
        """
        Update restored session information in cache
        
        Args:
            old_session_id: Original session ID
            session_cache: Original session cache data
        """
        try:
            sessions_data = self._load_cache()
            
            # Update with new session info
            session_cache.session_id = self.session_id
            session_cache.last_accessed = datetime.now().isoformat()
            session_cache.restore_keys = [addr.restore_key for addr in self.addresses]
            
            # Get new expiration time
            session_info = self.get_session_info()
            if session_info:
                session_cache.expires_at = session_info.expires_at
            
            # Remove old session and add new one
            if old_session_id in sessions_data:
                del sessions_data[old_session_id]
            
            sessions_data[self.session_id] = session_cache.to_dict()
            
            # Write to file
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(sessions_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to update restored session: {e}")
    
    def _verify_session(self) -> bool:
        """
        Verify if current session is valid
        
        Returns:
            Whether session is valid
        """
        if not self.session_id:
            return False
        
        try:
            query = f"""
            query {{
              session(id: "{self.session_id}") {{
                id
                expiresAt
              }}
            }}
            """
            
            response = self._make_request(query)
            return response.get('session') is not None
            
        except Exception:
            return False
    
    def _update_last_accessed(self, session_id: str) -> None:
        """
        Update session's last accessed time
        
        Args:
            session_id: Session ID
        """
        try:
            sessions_data = self._load_cache()
            
            if session_id in sessions_data:
                sessions_data[session_id]['last_accessed'] = datetime.now().isoformat()
                
                # Update expiration time
                session_info = self.get_session_info()
                if session_info:
                    sessions_data[session_id]['expires_at'] = session_info.expires_at
                
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(sessions_data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            self.logger.error(f"Failed to update last accessed time: {e}")
    
    def _remove_expired_session(self, session_id: str) -> None:
        """
        Remove expired session from cache
        
        Args:
            session_id: Session ID
        """
        try:
            sessions_data = self._load_cache()
            
            if session_id in sessions_data:
                del sessions_data[session_id]
                
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(sessions_data, f, indent=2, ensure_ascii=False)
                    
                self.logger.info(f"Removed expired Session: {session_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to remove expired Session: {e}")
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up all expired sessions
        
        Returns:
            Number of cleaned sessions
        """
        sessions = self.list_cached_sessions()
        expired_count = 0
        
        for session_cache in sessions:
            # Temporarily switch to that session for verification
            old_token = self.auth_token
            old_session = self.session_id
            
            self.auth_token = session_cache.auth_token
            self.session_id = session_cache.session_id
            
            if not self._verify_session():
                self._remove_expired_session(session_cache.session_id)
                expired_count += 1
            
            # Restore original settings
            self.auth_token = old_token
            self.session_id = old_session
        
        return expired_count
    
    def _make_request(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Send GraphQL request
        
        Args:
            query: GraphQL query statement
            variables: Query variables
            
        Returns:
            API response data
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
        Get available domain list
        
        Returns:
            Domain list
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
    
    def create_session(self, domain_id: Optional[str] = None, prefer_com: bool = True) -> Session:
        """
        Create new email session
        
        Args:
            domain_id: Specify domain ID, uses random domain if not provided
            prefer_com: Prefer .com domains when True
            
        Returns:
            Created session object
        """
        # If no domain specified and prefer_com is True, try to find .com domain
        if not domain_id and prefer_com:
            try:
                domains = self.get_domains()
                com_domains = [d for d in domains if d.get('name', '').endswith('.com')]
                if com_domains:
                    # Use first .com domain found
                    domain_id = com_domains[0]['id']
            except:
                pass  # Fall back to random domain
        
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
        
        # Parse address data
        addresses = []
        for addr_data in session_data["addresses"]:
            addresses.append(Address(
                id=addr_data["id"],
                address=addr_data["address"],
                restore_key=addr_data.get("restoreKey", "")
            ))
        
        # Create session object
        session = Session(
            id=session_data["id"],
            expires_at=session_data["expiresAt"],
            addresses=addresses,
            mails=[]
        )
        
        # Save session information
        self.session_id = session.id
        self.addresses = addresses
        
        # Auto save to cache - but don't save yet, wait for successful registration
        # self.save_session()
        
        return session
    
    def add_address(self, domain_id: Optional[str] = None) -> Address:
        """
        Add new email address to current session
        
        Args:
            domain_id: Specify domain ID, uses random domain if not provided
            
        Returns:
            Newly created address object
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
    
    def get_temp_email(self, prefer_com: bool = True) -> str:
        """
        Get temporary email address
        
        Args:
            prefer_com: Prefer .com domains when True
        
        Returns:
            Temporary email address
        """
        if not self.addresses:
            session = self.create_session(prefer_com=prefer_com)
            return session.addresses[0].address
        
        return self.addresses[0].address
    
    def get_mails(self, after_mail_id: Optional[str] = None) -> List[Mail]:
        """
        Get email list
        
        Args:
            after_mail_id: Get emails after specified email ID
            
        Returns:
            Email list
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
        
        # Update last accessed time
        if self.session_id:
            self._update_last_accessed(self.session_id)
        
        return mails
    
    def wait_for_mail(self, timeout: int = 300, check_interval: int = 5) -> Optional[Mail]:
        """
        Wait to receive email
        
        Args:
            timeout: Timeout in seconds
            check_interval: Check interval in seconds
            
        Returns:
            Received email, returns None if timeout
        """
        start_time = time.time()
        last_mail_id = None
        
        # Get existing emails
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
                    return new_mails[0]  # Return first new email
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error checking for mails: {e}")
                time.sleep(check_interval)
        
        return None
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   smtp_server: str = "smtp.gmail.com", smtp_port: int = 587,
                   from_email: Optional[str] = None, password: Optional[str] = None,
                   is_html: bool = False) -> bool:
        """
        Send email (using external SMTP server)
        
        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email content
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            from_email: Sender email
            password: Sender email password
            is_html: Whether HTML format
            
        Returns:
            Whether send was successful
        """
        if not from_email or not password:
            raise Exception("Sending email requires sender email and password")
        
        try:
            # Create email object
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add email content
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server and send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Enable TLS encryption
            server.login(from_email, password)
            
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            return False
    
    def get_session_info(self) -> Optional[Session]:
        """
        Get current session information
        
        Returns:
            Session information, returns None if no active session
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
            
            # Parse address data
            addresses = []
            for addr_data in session_data["addresses"]:
                addresses.append(Address(
                    id=addr_data["id"],
                    address=addr_data["address"],
                    restore_key=addr_data.get("restoreKey", "")
                ))
            
            # Parse email data
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
            self.logger.error(f"Failed to get session information: {e}")
            return None
