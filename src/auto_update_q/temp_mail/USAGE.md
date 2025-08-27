# DropMail Usage Guide

## Quick Start

### 1. Import Module

```python
from auto_update_q.temp_mail import DropMail
```

### 2. Create Instance and Get Temporary Email

```python
# Create DropMail instance
dropmail = DropMail()

# Get temporary email address
temp_email = dropmail.get_temp_email()
print(f"Temporary email: {temp_email}")
```

### 3. Receive Emails

```python
# Method 1: Check existing emails
mails = dropmail.get_mails()
for mail in mails:
    print(f"From: {mail.from_addr}")
    print(f"Subject: {mail.subject}")
    print(f"Content: {mail.text}")

# Method 2: Wait for new email
new_mail = dropmail.wait_for_mail(timeout=60)  # Wait for 1 minute
if new_mail:
    print(f"Received new email: {new_mail.subject}")
```

### 4. Send Email

```python
# Send email using Gmail SMTP
success = dropmail.send_email(
    to_email=temp_email,
    subject="Test Email",
    body="This is a test email",
    from_email="your_email@gmail.com",
    password="your_app_password"  # Gmail app-specific password
)

if success:
    print("Email sent successfully!")
```

## Complete Example

```python
from auto_update_q.temp_mail import DropMail
import time

def main():
    # Create instance
    dropmail = DropMail()
    
    # Get temporary email
    temp_email = dropmail.get_temp_email()
    print(f"Temporary email: {temp_email}")
    
    # Send test email to temporary email
    print("Sending test email...")
    success = dropmail.send_email(
        to_email=temp_email,
        subject="Automated Test Email",
        body="This is an automated test email to verify temporary email functionality.",
        from_email="your_email@gmail.com",
        password="your_app_password"
    )
    
    if success:
        print("Email sent successfully, waiting to receive...")
        
        # Wait for email to arrive
        new_mail = dropmail.wait_for_mail(timeout=30)
        if new_mail:
            print("Email received!")
            print(f"Subject: {new_mail.subject}")
            print(f"Content: {new_mail.text}")
        else:
            print("No email received within specified time")
    else:
        print("Failed to send email")

if __name__ == "__main__":
    main()
```

## Run Demos

```bash
# Run quick demo
uv run python src/auto_update_q/temp_mail/quick_demo.py

# Run complete example
uv run python src/auto_update_q/temp_mail/example.py

# Run tests
uv run python src/auto_update_q/temp_mail/test_dropmail.py
```

## Notes

1. **Gmail SMTP Configuration**: To send emails, ensure:
   - Enable Gmail two-factor authentication
   - Generate app-specific password
   - Use app-specific password instead of account password

2. **Session Management**: 
   - Sessions expire automatically, but each access extends expiration time
   - Use `get_session_info()` to check session status

3. **Error Handling**: 
   - Recommend adding appropriate exception handling in production
   - Network issues may cause API calls to fail

4. **Rate Limiting**: 
   - Use API reasonably, avoid overly frequent requests
   - Recommend adding appropriate delays in loops
