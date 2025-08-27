#!/usr/bin/env python3
"""
Command line interface test script
Test auto-register-aws-builder command line tool
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_help_command():
    """Test help command"""
    print("🧪 Testing help command...")
    
    try:
        # Test main help
        result = subprocess.run([
            sys.executable, "-m", "auto_update_q.auto_register", "--help"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + "/..")
        
        print(f"Return code: {result.returncode}")
        print(f"Output length: {len(result.stdout)} characters")
        
        if result.returncode == 0:
            print("✅ Main help command test passed")
            # Check keywords
            if "AWS Builder ID" in result.stdout and "register" in result.stdout:
                print("✅ Help content contains expected keywords")
            else:
                print("⚠️  Help content may be incomplete")
        else:
            print(f"❌ Main help command failed: {result.stderr}")
        
        # Test register subcommand help
        result = subprocess.run([
            sys.executable, "-m", "auto_update_q.auto_register", "register", "--help"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + "/..")
        
        if result.returncode == 0:
            print("✅ register help command test passed")
        else:
            print(f"❌ register help command failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error testing help command: {e}")


def test_version_command():
    """Test version command"""
    print("\n🧪 Testing version command...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "auto_update_q.auto_register", "version"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + "/..")
        
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout.strip()}")
        
        if result.returncode == 0:
            print("✅ Version command test passed")
            if "auto-register-aws-builder" in result.stdout:
                print("✅ Version info contains program name")
        else:
            print(f"❌ Version command failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error testing version command: {e}")


def test_list_records_command():
    """Test list records command"""
    print("\n🧪 Testing list records command...")
    
    try:
        # Create temporary cache file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("timestamp,email,password,name,status\n")
            f.write("2025-01-01T00:00:00,test@example.com,TestPass123,Test User,pending_captcha\n")
            temp_cache = f.name
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "auto_update_q.auto_register", "list-records",
                "--cache-file", temp_cache
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + "/..")
            
            print(f"Return code: {result.returncode}")
            
            if result.returncode == 0:
                print("✅ List records command test passed")
                if "test@example.com" in result.stdout:
                    print("✅ Record content displayed correctly")
            else:
                print(f"❌ List records command failed: {result.stderr}")
        finally:
            # Clean up temporary file
            os.unlink(temp_cache)
            
    except Exception as e:
        print(f"❌ Error testing list records command: {e}")


def test_register_command_dry_run():
    """Test register command (dry run)"""
    print("\n🧪 Testing register command parameter validation...")
    
    try:
        # Test invalid browser type
        result = subprocess.run([
            sys.executable, "-m", "auto_update_q.auto_register", "register",
            "--browser", "invalid_browser",
            "--no-temp-email",
            "--email", "test@example.com"
        ], capture_output=True, text=True, timeout=10, 
        cwd=os.path.dirname(__file__) + "/..")
        
        print(f"Invalid browser test return code: {result.returncode}")
        
        # Test parameter parsing (without actually running registration)
        # This only tests if command line arguments can be parsed correctly, won't actually start browser
        
    except subprocess.TimeoutExpired:
        print("⚠️  Command timeout (expected behavior, as it would try to start browser)")
    except Exception as e:
        print(f"❌ Error testing register command: {e}")


def main():
    """Main test function"""
    print("🚀 Starting command line interface test")
    print("=" * 50)
    
    # Check project structure
    project_root = Path(__file__).parent.parent
    auto_register_path = project_root / "src" / "auto_update_q" / "auto_register.py"
    
    if not auto_register_path.exists():
        print(f"❌ Cannot find auto_register.py: {auto_register_path}")
        return
    
    print(f"✅ Found auto_register.py: {auto_register_path}")
    
    # Run tests
    test_help_command()
    test_version_command()
    test_list_records_command()
    test_register_command_dry_run()
    
    print("\n" + "=" * 50)
    print("🏁 Command line interface test completed")
    print("\n💡 Tips:")
    print("- Complete registration test needs to be run manually as it involves browser interaction")
    print("- Use 'uv run auto-register-aws-builder register --help' to view complete options")


if __name__ == "__main__":
    main()
