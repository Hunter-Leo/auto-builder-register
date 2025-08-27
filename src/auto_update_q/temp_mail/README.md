# DropMail Temporary Email Module

A temporary email functionality module based on the [dropmail.me](https://dropmail.me) API.

## Features

- ✅ Get temporary email addresses
- ✅ Receive emails
- ✅ Send emails (via external SMTP server)
- ✅ Session management
- ✅ Multiple domain support
- ✅ Email waiting functionality

## Install Dependencies

```bash
uv add requests
```

## Quick Start

### 1. Basic Usage

```python
from auto_update_q.temp_mail import DropMail

# Create DropMail instance
dropmail = DropMail()

# Get temporary email address
temp_email = dropmail.get_temp_email()
print(f"Temporary email: {temp_email}")

# Check emails
mails = dropmail.get_mails()
for mail in mails:
    print(f"From: {mail.from_addr}")
    print(f"Subject: {mail.subject}")
    print(f"Content: {mail.text}")
```

### 2. Wait for New Email

```python
# Wait for new email (up to 5 minutes)
new_mail = dropmail.wait_for_mail(timeout=300)
if new_mail:
    print(f"Received new email: {new_mail.subject}")
else:
    print("Timeout, no new email received")
```

### 3. Send Email

```python
# Send email (requires SMTP server configuration)
success = dropmail.send_email(
    to_email="recipient@example.com",
    subject="Test Email",
    body="This is a test email",
    from_email="your_email@gmail.com",
    password="your_app_password"  # Gmail app-specific password
)

if success:
    print("Email sent successfully!")
```

### 4. Specify Domain

```python
# Get available domains
domains = dropmail.get_domains()
for domain in domains:
    print(f"Domain: {domain['name']}, ID: {domain['id']}")

# Create session with specified domain
session = dropmail.create_session(domain_id="RG9tYWluOjE=")
```

## API Reference

### DropMail Class

#### Constructor

```python
DropMail(auth_token: Optional[str] = None)
```

- `auth_token`: Authentication token, automatically generated if not provided

#### Main Methods

##### get_temp_email() -> str
Get temporary email address. Automatically creates a session if no active session exists.

##### create_session(domain_id: Optional[str] = None) -> Session
Create new email session.

- `domain_id`: Specify domain ID, uses random domain if not provided

##### get_mails(after_mail_id: Optional[str] = None) -> List[Mail]
Get email list.

- `after_mail_id`: Get emails after specified email ID

##### wait_for_mail(timeout: int = 300, check_interval: int = 5) -> Optional[Mail]
Wait to receive new email.

- `timeout`: Timeout in seconds
- `check_interval`: Check interval in seconds

##### send_email(...) -> bool
Send email.

Parameters:
- `to_email`: Recipient email
- `subject`: Email subject
- `body`: Email content
- `smtp_server`: SMTP server address (default: smtp.gmail.com)
- `smtp_port`: SMTP server port (default: 587)
- `from_email`: Sender email
- `password`: Sender email password
- `is_html`: Whether HTML format (default: False)

##### get_domains() -> List[Dict[str, Any]]
Get available domain list.

##### add_address(domain_id: Optional[str] = None) -> Address
Add new email address to current session.

##### get_session_info() -> Optional[Session]
Get current session information.

### Data Classes

#### Mail
Email data class with the following attributes:
- `id`: Email ID
- `from_addr`: Sender address
- `to_addr`: Recipient address
- `subject`: Email subject
- `text`: Plain text content
- `html`: HTML content (optional)
- `received_at`: Received time
- `raw_size`: Raw size
- `download_url`: Download link

#### Address
Email address data class with the following attributes:
- `id`: Address ID
- `address`: Email address
- `restore_key`: Restore key

#### Session
Session data class with the following attributes:
- `id`: Session ID
- `expires_at`: Expiration time
- `addresses`: Address list
- `mails`: Email list

## Usage Examples

See the `example.py` file for complete usage examples.

## Testing

Run tests:

```bash
python test_dropmail.py
```

## Notes

1. **Authentication Token**: The API is currently in public beta, you can use any string with 8+ characters as authentication token.
2. **Session Expiration**: Sessions expire automatically, but each access extends the expiration time.
3. **Send Email**: Send functionality requires external SMTP server configuration, Gmail app-specific password is recommended.
4. **Rate Limiting**: Please use the API reasonably and avoid overly frequent requests.

## Gmail SMTP Configuration

To use Gmail for sending emails, you need to:

1. Enable two-factor authentication
2. Generate app-specific password
3. Use the following configuration:
   - SMTP server: smtp.gmail.com
   - Port: 587
   - Use app-specific password instead of account password

## Error Handling

The module throws the following exceptions:
- `Exception`: When API returns error or network request fails
- `requests.RequestException`: When HTTP request fails

It's recommended to add appropriate exception handling when using.

## License

This module is released under the project license.
