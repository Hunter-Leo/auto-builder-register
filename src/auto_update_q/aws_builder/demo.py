#!/usr/bin/env python3
"""
AWS Builder ID automatic registration demo
Demonstrates module usage
"""

import sys
import os
sys.path.append('./src')

from auto_update_q.aws_builder import AWSBuilder
from auto_update_q.temp_mail import DropMail


def demo_basic_registration():
    """Basic registration demo"""
    print("=== Basic Registration Demo ===")
    
    with AWSBuilder(headless=False, debug=True) as aws_builder:
        credentials = aws_builder.register_aws_builder(
            email="test@example.com",
            name="Test User"
        )
        
        if credentials:
            print(f"✓ Registration successful!")
            print(f"Email: {credentials.email}")
            print(f"Password: {credentials.password}")
            print(f"Name: {credentials.name}")
        else:
            print("✗ Registration failed")


def demo_with_temp_email():
    """Registration demo using temporary email"""
    print("=== Registration Demo with Temporary Email ===")
    
    # Create temporary email
    dropmail = DropMail()
    temp_email = dropmail.get_temp_email()
    print(f"Temporary email: {temp_email}")
    
    # Register using temporary email
    with AWSBuilder(headless=False, debug=True) as aws_builder:
        credentials = aws_builder.register_aws_builder(
            email=temp_email,
            name="Temp User",
            dropmail=dropmail  # Auto-get verification code
        )
        
        if credentials:
            print(f"✓ Registration successful!")
            print(f"Email: {credentials.email}")
            print(f"Password: {credentials.password}")
            
            # Navigate to other pages after successful registration
            success = aws_builder.navigate_to_url("https://view.awsapps.com/start")
            if success:
                print(f"Current page: {aws_builder.get_current_url()}")
        else:
            print("✗ Registration failed")


def demo_custom_password():
    """Custom password registration demo"""
    print("=== Custom Password Registration Demo ===")
    
    custom_password = "MySecurePassword123!"
    
    with AWSBuilder(headless=False, debug=True) as aws_builder:
        credentials = aws_builder.register_aws_builder(
            email="custom@example.com",
            name="Custom User",
            password=custom_password
        )
        
        if credentials:
            print(f"✓ Registration successful!")
            print(f"Password used: {credentials.password}")
        else:
            print("✗ Registration failed")


def main():
    """Main function"""
    print("AWS Builder ID Automatic Registration Demo")
    print("=" * 50)
    
    demos = [
        ("1", "Basic Registration Demo", demo_basic_registration),
        ("2", "Registration Demo with Temporary Email", demo_with_temp_email),
        ("3", "Custom Password Registration Demo", demo_custom_password),
    ]
    
    print("Available demos:")
    for key, name, _ in demos:
        print(f"  {key}. {name}")
    
    choice = input("\nPlease select demo (1-3, or press Enter for basic demo): ").strip()
    
    if choice == "":
        choice = "1"  # Default to basic demo
    
    # Run selected demo
    for key, name, func in demos:
        if choice == key:
            print(f"\n{'='*20} {name} {'='*20}")
            try:
                func()
            except KeyboardInterrupt:
                print("\nDemo interrupted by user")
            except Exception as e:
                print(f"Demo error: {e}")
            break
    else:
        print("Invalid selection")


if __name__ == "__main__":
    main()
