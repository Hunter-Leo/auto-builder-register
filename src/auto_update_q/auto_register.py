#!/usr/bin/env python3
"""
AWS Builder ID Automatic Registration Command Line Tool
Implemented using Typer framework, supports automatic registration until graphic captcha
"""

import csv
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

import typer
import click
from typing_extensions import Annotated

from .aws_builder.aws_builder import AWSBuilder
from .temp_mail.dropmail import DropMail


# Application instance
app = typer.Typer(
    name="auto-register-aws-builder",
    help="AWS Builder ID Automatic Registration Tool - Automatically complete registration process until graphic captcha",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True  # Show help when no arguments provided
)

# Global variables
current_browser = None
registration_data = None


def setup_logging(debug: bool = False) -> logging.Logger:
    """Setup logger"""
    logger = logging.getLogger("auto_register")
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    return logger


def signal_handler(signum, frame):
    """Signal handler for graceful exit"""
    logger = logging.getLogger("auto_register")
    logger.info("Received exit signal, cleaning up resources...")
    
    if current_browser:
        try:
            current_browser.close()
        except Exception as e:
            logger.warning(f"Error closing browser: {e}")
    
    sys.exit(0)


def save_registration_data(email: str, password: str, name: str, 
                         cache_file: Path, logger: logging.Logger) -> None:
    """
    Save registration data to CSV file
    
    Args:
        email: Email address
        password: Password
        name: Name
        cache_file: Cache file path
        logger: Logger
    """
    try:
        # Ensure directory exists
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists, create and write header if not
        file_exists = cache_file.exists()
        
        with open(cache_file, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'email', 'password', 'name', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header if file doesn't exist
            if not file_exists:
                writer.writeheader()
            
            # Write data
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'email': email,
                'password': password,
                'name': name,
                'status': 'pending_captcha'
            })
        
        logger.info(f"Registration data saved to: {cache_file}")
        
    except Exception as e:
        logger.error(f"Failed to save registration data: {e}")


def select_session_from_list(dropmail: DropMail, logger: logging.Logger) -> Optional[str]:
    """
    Display recoverable Session list for user selection
    
    Args:
        dropmail: DropMail instance
        logger: Logger
        
    Returns:
        Selected Session ID, None if cancelled
    """
    logger.info("🔍 Checking available Sessions...")
    
    # Clean up expired Sessions
    expired_count = dropmail.cleanup_expired_sessions()
    if expired_count > 0:
        logger.info(f"🧹 Cleaned up {expired_count} expired Sessions")
    
    # Get available Sessions
    sessions = dropmail.list_cached_sessions()
    
    if not sessions:
        logger.warning("📭 No recoverable Sessions found")
        return None
    
    # Validate Sessions and filter
    valid_sessions = []
    logger.info("🔍 Validating Sessions...")
    
    for session_cache in sessions:
        # Temporarily switch to this session for validation
        old_token = dropmail.auth_token
        old_session = dropmail.session_id
        
        dropmail.auth_token = session_cache.auth_token
        dropmail.session_id = session_cache.session_id
        
        if dropmail._verify_session():
            valid_sessions.append(session_cache)
        else:
            logger.info(f"❌ Session {session_cache.session_id[:8]}... expired, will be deleted")
            dropmail._remove_expired_session(session_cache.session_id)
        
        # Restore original settings
        dropmail.auth_token = old_token
        dropmail.session_id = old_session
    
    if not valid_sessions:
        logger.warning("📭 No valid Sessions found")
        return None
    
    # Display Sessions list
    logger.info("📋 Recoverable Sessions:")
    logger.info("=" * 80)
    
    for i, session_cache in enumerate(valid_sessions, 1):
        # Format time display
        try:
            created_dt = datetime.fromisoformat(session_cache.created_at.replace('Z', '+00:00'))
            created_time = created_dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            created_time = session_cache.created_at[:19].replace('T', ' ')
        
        try:
            accessed_dt = datetime.fromisoformat(session_cache.last_accessed.replace('Z', '+00:00'))
            last_accessed = accessed_dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            last_accessed = session_cache.last_accessed[:19].replace('T', ' ')
        
        logger.info(f"{i}. Email: {session_cache.email_address}")
        logger.info(f"   Session ID: {session_cache.session_id}")
        logger.info(f"   Created: {created_time}")
        logger.info(f"   Last accessed: {last_accessed}")
        logger.info("-" * 40)
    
    # User selection
    while True:
        try:
            choice = input(f"\nPlease select Session to restore (1-{len(valid_sessions)}, 0=cancel): ").strip()
            
            if choice == '0':
                logger.info("❌ User cancelled selection")
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(valid_sessions):
                selected_session = valid_sessions[choice_num - 1]
                logger.info(f"✓ Selected Session: {selected_session.email_address}")
                return selected_session.session_id
            else:
                print(f"❌ Please enter a number between 1-{len(valid_sessions)}")
                
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            logger.info("\n❌ User interrupted selection")
            return None


def monitor_emails(dropmail: DropMail, logger: logging.Logger, check_interval: int = 10) -> None:
    """
    Continuously monitor emails and display newly received emails
    
    Args:
        dropmail: DropMail instance
        logger: Logger
        check_interval: Check interval (seconds)
    """
    logger.info("📧 Starting email monitoring...")
    logger.info(f"📬 Email address: {dropmail.addresses[0].address if dropmail.addresses else 'N/A'}")
    logger.info(f"🔄 Check interval: {check_interval} seconds")
    logger.info("⚠️  Press Ctrl+C to stop monitoring")
    logger.info("=" * 60)
    
    # Get current existing email count
    try:
        existing_mails = dropmail.get_mails()
        last_mail_count = len(existing_mails)
        last_mail_id = existing_mails[-1].id if existing_mails else None
        
        if existing_mails:
            logger.info(f"📨 Currently have {last_mail_count} emails")
            logger.info("Recent emails:")
            for mail in existing_mails[-3:]:  # Show last 3 emails
                logger.info(f"  • From: {mail.from_addr}")
                logger.info(f"    Subject: {mail.subject}")
                logger.info(f"    Time: {mail.received_at}")
                logger.info("-" * 30)
        else:
            logger.info("📭 No emails yet")
            
    except Exception as e:
        logger.error(f"❌ Failed to get existing emails: {e}")
        last_mail_id = None
        last_mail_count = 0
    
    logger.info("🔍 Starting to monitor new emails...")
    
    try:
        while True:
            try:
                # Check for new emails
                if last_mail_id:
                    new_mails = dropmail.get_mails(after_mail_id=last_mail_id)
                else:
                    all_mails = dropmail.get_mails()
                    new_mails = all_mails[last_mail_count:] if len(all_mails) > last_mail_count else []
                
                if new_mails:
                    logger.info(f"🎉 Received {len(new_mails)} new emails!")
                    logger.info("=" * 60)
                    
                    for mail in new_mails:
                        logger.info(f"📧 New email:")
                        logger.info(f"   From: {mail.from_addr}")
                        logger.info(f"   To: {mail.to_addr}")
                        logger.info(f"   Subject: {mail.subject}")
                        logger.info(f"   Time: {mail.received_at}")
                        logger.info(f"   Content preview: {mail.text[:100]}..." if len(mail.text) > 100 else f"   Content: {mail.text}")
                        logger.info("-" * 40)
                    
                    # Update last mail ID and count
                    last_mail_id = new_mails[-1].id
                    last_mail_count += len(new_mails)
                    
                    logger.info("🔍 Continue monitoring new emails...")
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error checking emails: {e}")
                time.sleep(check_interval)
                
    except KeyboardInterrupt:
        logger.info("\n⚠️  Stopped email monitoring")


def wait_for_user_action(timeout_minutes: int, logger: logging.Logger) -> None:
    """
    Wait for user action or timeout
    
    Args:
        timeout_minutes: Timeout in minutes
        logger: Logger
    """
    logger.info(f"Waiting for user action, will auto-exit after {timeout_minutes} minutes...")
    logger.info("You can:")
    logger.info("1. Manually complete the graphic captcha in browser")
    logger.info("2. Press Ctrl+C to exit early")
    logger.info("3. Close the browser directly")
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    try:
        while time.time() - start_time < timeout_seconds:
            # Check if browser is still running
            if current_browser and current_browser.driver:
                try:
                    # Try to get current URL, will throw exception if browser is closed
                    current_browser.driver.current_url
                    time.sleep(5)  # Check every 5 seconds
                except Exception:
                    logger.info("Detected browser closed, program exits")
                    return
            else:
                break
        
        logger.info(f"{timeout_minutes} minutes timeout, program auto-exits")
        
    except KeyboardInterrupt:
        logger.info("User manually exited")


@app.command()
def register(
    email: Annotated[Optional[str], typer.Option(
        "--email", "-e",
        help="📧 Specify email address. If not provided, will auto-generate temporary email"
    )] = None,
    
    name: Annotated[str, typer.Option(
        "--name", "-n",
        help="👤 User name"
    )] = "Crazy Joe",
    
    password: Annotated[Optional[str], typer.Option(
        "--password", "-p",
        help="🔐 Specify password. If not provided, will use default password CrazyJoe@2025"
    )] = "CrazyJoe@2025",
    
    headless: Annotated[bool, typer.Option(
        "--headless",
        help="👻 Run browser in headless mode (no browser window displayed)"
    )] = False,
    
    browser: Annotated[str, typer.Option(
        "--browser", "-b",
        help="🌐 Specify browser type",
        click_type=click.Choice(["edge"], case_sensitive=False)
    )] = "edge",
    
    timeout: Annotated[int, typer.Option(
        "--timeout", "-t",
        help="⏱️ Operation timeout (seconds)",
        min=10, max=300
    )] = 30,
    
    wait_minutes: Annotated[int, typer.Option(
        "--wait-minutes", "-w",
        help="⏳ Wait time for user action after stopping automation (minutes)",
        min=1, max=120
    )] = 30,
    
    cache_file: Annotated[str, typer.Option(
        "--cache-file", "-c",
        help="💾 Registration data cache file path"
    )] = ".cache/auto_register_aws_builder.csv",
    
    debug: Annotated[bool, typer.Option(
        "--debug", "-d",
        help="🐛 Enable debug mode, show detailed logs"
    )] = False,
    
    no_temp_email: Annotated[bool, typer.Option(
        "--no-temp-email",
        help="🚫 Don't use temporary email, need to handle email verification manually"
    )] = False,
    
    dropmail_cache: Annotated[str, typer.Option(
        "--dropmail-cache",
        help="📁 DropMail Session cache file path"
    )] = ".cache/dropmail_sessions.json",
    
    only_mail: Annotated[bool, typer.Option(
        "--only-mail",
        help="📧 Only register temporary email and monitor emails, don't perform AWS Builder ID registration"
    )] = False
):
    """
    Automatically register AWS Builder ID account
    
    This tool will automatically complete the registration process until the graphic captcha step,
    then stop automation and allow users to manually complete the remaining steps.
    
    [bold green]Features:[/bold green]
    
    • Auto-generate or use specified temporary email
    • Auto-fill registration form
    • Auto-handle email verification code
    • Stop before graphic captcha, wait for manual user action
    • Support Safari browser
    • Auto-save registration info to CSV file
    • Support Session persistence
    • Support email-only mode
    
    [bold yellow]Usage Examples:[/bold yellow]
    
    # Auto-register with default settings
    auto-register-aws-builder register
    
    # Specify email and name
    auto-register-aws-builder register --email test@example.com --name "John Doe"
    
    # Only register temporary email and monitor emails
    auto-register-aws-builder register --only-mail
    
    # Use headless mode
    auto-register-aws-builder register --headless
    
    # Enable debug mode
    auto-register-aws-builder register --debug
    """
    global current_browser, registration_data
    
    # Setup logging
    logger = setup_logging(debug)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Starting AWS Builder ID automatic registration")
    logger.info("=" * 60)
    
    try:
        # Step 1: Prepare email
        dropmail = None
        if only_mail or (not email and not no_temp_email):
            logger.info("📧 Creating temporary email...")
            dropmail = DropMail(cache_file=dropmail_cache)
            email = dropmail.get_temp_email()
            logger.info(f"✓ Temporary email: {email}")
            logger.info(f"✓ Session ID: {dropmail.session_id}")
            
            if only_mail:
                # Email-only mode, start monitoring directly
                logger.info("📧 Email-only mode, starting email monitoring...")
                monitor_emails(dropmail, logger, check_interval=10)
                return  # Only monitor emails, don't perform AWS Builder ID registration
                
        elif not email:
            logger.error("❌ Must provide email address or enable temporary email")
            raise typer.Exit(1)
        
        # Step 2: Initialize registrar
        logger.info("🔧 Initializing AWS Builder registrar...")
        current_browser = AWSBuilder(
            headless=headless,
            timeout=timeout,
            debug=debug,
            keep_browser=True,  # Keep browser open
            browser_type=browser
        )
        logger.info("✓ Registrar initialization complete")
        
        # Step 3: Display registration info
        logger.info("📋 Registration info:")
        logger.info("-" * 40)
        logger.info(f"Email: {email}")
        logger.info(f"Name: {name}")
        logger.info(f"Browser: {browser}")
        logger.info(f"Headless mode: {headless}")
        logger.info(f"Wait time: {wait_minutes} minutes")
        logger.info("-" * 40)
        
        # Step 4: Execute automatic registration (until graphic captcha)
        logger.info("🎯 Starting automatic registration process...")
        
        # Modify registration process to stop before graphic captcha
        result = current_browser.register_aws_builder_until_captcha(
            email=email,
            name=name,
            password=password,
            dropmail=dropmail
        )
        
        if not result:
            logger.error("❌ Automatic registration process failed")
            raise typer.Exit(1)
        
        # Save registration data
        registration_data = result
        cache_path = Path(cache_file)
        save_registration_data(
            email=result.email,
            password=result.password,
            name=result.name,
            cache_file=cache_path,
            logger=logger
        )
        
        # Step 5: Display results and wait for user action
        logger.info("🎉 Automatic registration process complete!")
        logger.info("=" * 60)
        logger.info("📊 Registration info:")
        logger.info(f"✓ Email: {result.email}")
        logger.info(f"✓ Password: {result.password}")
        logger.info(f"✓ Name: {result.name}")
        logger.info("=" * 60)
        
        logger.info("⚠️  Please manually complete the graphic captcha in browser")
        
        # Wait for user action
        wait_for_user_action(wait_minutes, logger)
        
    except KeyboardInterrupt:
        logger.info("⚠️  User interrupted operation")
    except Exception as e:
        logger.error(f"❌ Error occurred: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)
    finally:
        # Clean up resources
        logger.info("🧹 Cleaning up resources...")
        if current_browser:
            try:
                current_browser.close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
        logger.info("✓ Program ended")


@app.command()
def sessions(
    dropmail_cache: Annotated[str, typer.Option(
        "--cache-file", "-c",
        help="📁 DropMail Session cache file path"
    )] = ".cache/dropmail_sessions.json",
    
    cleanup: Annotated[bool, typer.Option(
        "--cleanup",
        help="🧹 Clean up expired Sessions"
    )] = False,
    
    restore: Annotated[bool, typer.Option(
        "--restore", "-r",
        help="🔄 Display recoverable Sessions list for selection and monitor emails"
    )] = False,
    
    monitor: Annotated[Optional[str], typer.Option(
        "--monitor", "-m",
        help="📧 Monitor emails for specified Session ID"
    )] = None
):
    """
    Manage DropMail Sessions
    
    Display, clean up, restore and monitor DropMail Sessions.
    
    [bold yellow]Usage Examples:[/bold yellow]
    
    # Display all Sessions
    auto-register-aws-builder sessions
    
    # Clean up expired Sessions
    auto-register-aws-builder sessions --cleanup
    
    # Restore Session and monitor emails
    auto-register-aws-builder sessions --restore
    
    # Monitor emails for specified Session
    auto-register-aws-builder sessions --monitor SESSION_ID
    """
    dropmail = DropMail(cache_file=dropmail_cache)
    logger = setup_logging(False)
    
    if restore:
        # Display Session list for user selection and monitoring
        logger.info("🔄 Restoring DropMail Session")
        
        selected_session_id = select_session_from_list(dropmail, logger)
        if not selected_session_id:
            logger.info("❌ No Session selected, program exits")
            raise typer.Exit(0)
        
        if dropmail.restore_session(selected_session_id):
            email = dropmail.addresses[0].address if dropmail.addresses else None
            if email:
                logger.info(f"✓ Successfully restored email: {email}")
                logger.info(f"✓ Session ID: {selected_session_id}")
                
                # Start monitoring emails
                monitor_emails(dropmail, logger, check_interval=10)
                return
            else:
                logger.error("❌ No email address found in restored Session")
                raise typer.Exit(1)
        else:
            logger.error(f"❌ Cannot restore Session: {selected_session_id}")
            raise typer.Exit(1)
    
    if monitor:
        # Monitor emails for specified Session
        if dropmail.restore_session(monitor):
            logger.info(f"✓ Successfully restored Session: {monitor}")
            monitor_emails(dropmail, logger, check_interval=10)
        else:
            logger.error(f"❌ Cannot restore Session: {monitor}")
            raise typer.Exit(1)
        return
    
    if cleanup:
        # Clean up expired Sessions
        logger.info("🧹 Cleaning up expired Sessions...")
        expired_count = dropmail.cleanup_expired_sessions()
        logger.info(f"✓ Cleaned up {expired_count} expired Sessions")
    
    # Display all Sessions
    sessions_list = dropmail.list_cached_sessions()
    
    if not sessions_list:
        typer.echo("📭 No Sessions found")
        return
    
    typer.echo(f"📋 Found {len(sessions_list)} Sessions:")
    typer.echo("=" * 80)
    
    for i, session_cache in enumerate(sessions_list, 1):
        # Format time display
        try:
            created_dt = datetime.fromisoformat(session_cache.created_at.replace('Z', '+00:00'))
            created_time = created_dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            created_time = session_cache.created_at[:19].replace('T', ' ')
        
        try:
            accessed_dt = datetime.fromisoformat(session_cache.last_accessed.replace('Z', '+00:00'))
            last_accessed = accessed_dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            last_accessed = session_cache.last_accessed[:19].replace('T', ' ')
        
        # Verify if Session is valid
        old_token = dropmail.auth_token
        old_session = dropmail.session_id
        
        dropmail.auth_token = session_cache.auth_token
        dropmail.session_id = session_cache.session_id
        
        is_valid = dropmail._verify_session()
        status = "✓ Valid" if is_valid else "❌ Invalid"
        
        # Restore original settings
        dropmail.auth_token = old_token
        dropmail.session_id = old_session
        
        typer.echo(f"{i}. Email: {session_cache.email_address}")
        typer.echo(f"   Session ID: {session_cache.session_id}")
        typer.echo(f"   Status: {status}")
        typer.echo(f"   Created: {created_time}")
        typer.echo(f"   Last accessed: {last_accessed}")
        typer.echo("-" * 40)


@app.command()
def list_records(
    cache_file: Annotated[str, typer.Option(
        "--cache-file", "-c",
        help="💾 Registration data cache file path"
    )] = ".cache/auto_register_aws_builder.csv",
    
    limit: Annotated[int, typer.Option(
        "--limit", "-l",
        help="📊 Limit number of records to display",
        min=1, max=100
    )] = 10
):
    """
    List recent registration records
    
    Display registration records saved in cache file, including timestamp, email, password and other info.
    """
    cache_path = Path(cache_file)
    
    if not cache_path.exists():
        typer.echo("❌ Cache file does not exist")
        raise typer.Exit(1)
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            records = list(reader)
        
        if not records:
            typer.echo("📝 No registration records")
            return
        
        # Display recent records
        recent_records = records[-limit:]
        
        typer.echo(f"📋 Recent {len(recent_records)} registration records:")
        typer.echo("=" * 80)
        
        for i, record in enumerate(recent_records, 1):
            timestamp = record.get('timestamp', 'N/A')
            email = record.get('email', 'N/A')
            password = record.get('password', 'N/A')
            name = record.get('name', 'N/A')
            status = record.get('status', 'N/A')
            
            typer.echo(f"{i}. Time: {timestamp}")
            typer.echo(f"   Email: {email}")
            typer.echo(f"   Password: {password}")
            typer.echo(f"   Name: {name}")
            typer.echo(f"   Status: {status}")
            typer.echo("-" * 40)
            
    except Exception as e:
        typer.echo(f"❌ Failed to read cache file: {e}")
        raise typer.Exit(1)


@app.command()
def version():
    """Display version information"""
    typer.echo("auto-register-aws-builder v0.1.0")
    typer.echo("AWS Builder ID Automatic Registration Tool")


if __name__ == "__main__":
    app()
