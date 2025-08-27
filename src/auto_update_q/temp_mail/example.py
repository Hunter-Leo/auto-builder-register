"""
DropMail Usage Example

Demonstrates how to use the DropMail class for temporary email operations
"""

import time
from dropmail import DropMail


def main():
    """Main function demonstrating basic usage of DropMail"""
    
    # 1. Create DropMail instance
    print("1. Creating DropMail instance...")
    dropmail = DropMail()
    print(f"Authentication token: {dropmail.auth_token}")
    
    # 2. Get available domains
    print("\n2. Getting available domains...")
    try:
        domains = dropmail.get_domains()
        print("Available domains:")
        for domain in domains[:3]:  # Show only first 3
            print(f"  - {domain['name']} (ID: {domain['id']})")
    except Exception as e:
        print(f"Failed to get domains: {e}")
    
    # 3. Create temporary email session
    print("\n3. Creating temporary email session...")
    try:
        session = dropmail.create_session()
        print(f"Session ID: {session.id}")
        print(f"Expires at: {session.expires_at}")
        print(f"Temporary email address: {session.addresses[0].address}")
    except Exception as e:
        print(f"Failed to create session: {e}")
        return
    
    # 4. Get temporary email address
    print("\n4. Getting temporary email address...")
    temp_email = dropmail.get_temp_email()
    print(f"Temporary email: {temp_email}")
    
    # 5. Add additional email address
    print("\n5. Adding additional email address...")
    try:
        new_address = dropmail.add_address()
        print(f"New email address: {new_address.address}")
    except Exception as e:
        print(f"Failed to add address: {e}")
    
    # 6. Check existing emails
    print("\n6. Checking existing emails...")
    try:
        mails = dropmail.get_mails()
        if mails:
            print(f"Found {len(mails)} emails:")
            for mail in mails:
                print(f"  - From: {mail.from_addr}")
                print(f"    To: {mail.to_addr}")
                print(f"    Subject: {mail.subject}")
                print(f"    Time: {mail.received_at}")
                print(f"    Content: {mail.text[:100]}...")
        else:
            print("No emails found")
    except Exception as e:
        print(f"Failed to get emails: {e}")
    
    # 7. Wait for new email (demo purpose, adjust timeout as needed in actual use)
    print(f"\n7. Waiting for new email (30 second timeout)...")
    print(f"Please send email to: {temp_email}")
    
    try:
        new_mail = dropmail.wait_for_mail(timeout=30, check_interval=3)
        if new_mail:
            print("Received new email!")
            print(f"  From: {new_mail.from_addr}")
            print(f"  Subject: {new_mail.subject}")
            print(f"  Content: {new_mail.text}")
        else:
            print("Timeout, no new email received")
    except Exception as e:
        print(f"Failed to wait for email: {e}")
    
    # 8. Send email example (requires SMTP configuration)
    print("\n8. Send email example...")
    print("Note: Sending email requires valid SMTP server configuration")
    
    # Uncomment the following code and fill in valid SMTP information to test sending functionality
    """
    try:
        success = dropmail.send_email(
            to_email=temp_email,
            subject="Test Email",
            body="This is a test email",
            from_email="your_email@gmail.com",  # Replace with your email
            password="your_password"  # Replace with your password or app-specific password
        )
        if success:
            print("Email sent successfully!")
        else:
            print("Failed to send email!")
    except Exception as e:
        print(f"Email sending exception: {e}")
    """
    
    # 9. Get session information
    print("\n9. Getting session information...")
    try:
        session_info = dropmail.get_session_info()
        if session_info:
            print(f"Session ID: {session_info.id}")
            print(f"Expires at: {session_info.expires_at}")
            print(f"Address count: {len(session_info.addresses)}")
            print(f"Email count: {len(session_info.mails)}")
        else:
            print("Unable to get session information")
    except Exception as e:
        print(f"Failed to get session information: {e}")


if __name__ == "__main__":
    main()
