#!/usr/bin/env python3
"""
Test script for mail.md requirements
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from auto_update_q.temp_mail.dropmail import DropMail

def test_com_domain_preference():
    """Test .com domain preference"""
    print("Testing .com domain preference...")
    
    dropmail = DropMail()
    
    try:
        # Get available domains
        domains = dropmail.get_domains()
        print(f"Available domains: {len(domains)}")
        
        # Check for .com domains
        com_domains = [d for d in domains if d.get('name', '').endswith('.com')]
        print(f".com domains found: {len(com_domains)}")
        
        if com_domains:
            print("First .com domain:", com_domains[0])
            
        # Test creating session with .com preference
        email = dropmail.get_temp_email(prefer_com=True)
        print(f"Generated email: {email}")
        
        if email.endswith('.com'):
            print("✓ Successfully generated .com email")
        else:
            print("⚠️  Generated non-.com email (might be expected if no .com domains available)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_session_cache_structure():
    """Test session cache structure"""
    print("\nTesting session cache structure...")
    
    dropmail = DropMail(cache_file="../.cache/dropmail_sessions.json")
    
    try:
        # List cached sessions
        sessions = dropmail.list_cached_sessions()
        print(f"Found {len(sessions)} cached sessions")
        
        for i, session in enumerate(sessions[:3], 1):  # Show first 3
            print(f"{i}. Email: {session.email_address}")
            print(f"   Password: {session.password}")
            print(f"   Created: {session.created_at}")
            print(f"   Last accessed: {session.last_accessed}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_restore_expired_session():
    """Test restoring an expired session"""
    print("\nTesting restore expired session...")
    
    dropmail = DropMail(cache_file="../.cache/dropmail_sessions.json")
    
    try:
        # List cached sessions
        sessions = dropmail.list_cached_sessions()
        if not sessions:
            print("No cached sessions found")
            return
            
        # Try to restore the first session (likely expired)
        first_session = sessions[0]
        print(f"Attempting to restore session: {first_session.email_address}")
        print(f"Session ID: {first_session.session_id}")
        print(f"Has restore keys: {len(first_session.restore_keys) > 0}")
        
        success = dropmail.restore_session(first_session.session_id)
        
        if success:
            print("✅ Session restored successfully!")
            if dropmail.addresses:
                print(f"Email: {dropmail.addresses[0].address}")
        else:
            print("❌ Failed to restore session")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_com_domain_preference()
    test_session_cache_structure()
    test_restore_expired_session()
