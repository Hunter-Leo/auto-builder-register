"""
DropMail Quick Demo Script
"""

from dropmail import DropMail


def main():
    """Quick demonstration of DropMail's main features"""
    
    print("=== DropMail Quick Demo ===\n")
    
    # 1. Create instance
    print("1. Creating DropMail instance...")
    dropmail = DropMail()
    print(f"   Authentication token: {dropmail.auth_token}\n")
    
    # 2. Get available domains
    print("2. Getting available domains...")
    try:
        domains = dropmail.get_domains()
        print(f"   Found {len(domains)} available domains:")
        for i, domain in enumerate(domains[:5]):  # Show only first 5
            print(f"   {i+1}. {domain['name']}")
        print()
    except Exception as e:
        print(f"   Error: {e}\n")
        return
    
    # 3. Create temporary email
    print("3. Creating temporary email...")
    try:
        session = dropmail.create_session()
        temp_email = session.addresses[0].address
        print(f"   Temporary email address: {temp_email}")
        print(f"   Session ID: {session.id}")
        print(f"   Expires at: {session.expires_at}\n")
    except Exception as e:
        print(f"   Error: {e}\n")
        return
    
    # 4. Add additional address
    print("4. Adding additional email address...")
    try:
        new_address = dropmail.add_address()
        print(f"   New address: {new_address.address}\n")
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # 5. Check existing emails
    print("5. Checking existing emails...")
    try:
        mails = dropmail.get_mails()
        if mails:
            print(f"   Found {len(mails)} emails:")
            for i, mail in enumerate(mails):
                print(f"   Email {i+1}:")
                print(f"     From: {mail.from_addr}")
                print(f"     Subject: {mail.subject}")
                print(f"     Time: {mail.received_at}")
        else:
            print("   No emails found")
        print()
    except Exception as e:
        print(f"   Error: {e}\n")
    
    # 6. Get session information
    print("6. Getting session information...")
    try:
        session_info = dropmail.get_session_info()
        if session_info:
            print(f"   Session ID: {session_info.id}")
            print(f"   Address count: {len(session_info.addresses)}")
            print(f"   Email count: {len(session_info.mails)}")
            print("   All addresses:")
            for i, addr in enumerate(session_info.addresses):
                print(f"     {i+1}. {addr.address}")
        else:
            print("   Unable to get session information")
        print()
    except Exception as e:
        print(f"   Error: {e}\n")
    
    print("=== Demo Complete ===")
    print(f"\nYou can send test emails to the following addresses:")
    for addr in dropmail.addresses:
        print(f"  - {addr.address}")
    print("\nThen use dropmail.get_mails() or dropmail.wait_for_mail() to receive emails.")


if __name__ == "__main__":
    main()
