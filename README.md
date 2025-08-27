# Auto Update Q

Automatic Q project updater

## Modules

### AWS Builder ID Auto Registration Tool

AWS Builder ID automatic registration command-line tool based on Selenium and DropMail.

#### Features

- ✅ Automatic temporary email generation
- ✅ Automatic registration form filling
- ✅ Automatic email verification code handling
- ✅ Stop automation before graphical captcha
- ✅ Support for Safari and Edge browsers
- ✅ Automatic registration information saving
- ✅ Complete command line interface
- ✅ Rich configuration options

#### Quick Start

```bash
# Basic usage (automatically generate temporary email)
uv run auto-register-aws-builder register

# Specify email and name
uv run auto-register-aws-builder register --email test@example.com --name "John Doe"

# Use Safari browser
uv run auto-register-aws-builder register --browser safari

# Enable debug mode
uv run auto-register-aws-builder register --debug

# View registration records
uv run auto-register-aws-builder list-records

# View help
uv run auto-register-aws-builder --help
```

#### Command Line Options

```bash
# register command options
--email, -e          📧 Specify email address (optional, auto-generate temp email if not provided)
--name, -n           👤 User name (default: "Crazy Joe")
--password, -p       🔐 Specify password (default: "CrazyJoe@2025")
--headless           👻 Use headless mode (Safari not supported)
--browser, -b        🌐 Browser type (safari/edge, default: edge)
--timeout, -t        ⏱️ Operation timeout (10-300 seconds, default: 30)
--wait-minutes, -w   ⏳ Wait time for user operation (1-120 minutes, default: 30)
--cache-file, -c     💾 Cache file path (default: .cache/auto_register_aws_builder.csv)
--debug, -d          🐛 Enable debug mode
--no-temp-email      🚫 Don't use temporary email, requires manual email verification
```

### DropMail Temporary Email Module

Temporary email functionality module based on [dropmail.me](https://dropmail.me) API.

#### Features

- ✅ Get temporary email addresses
- ✅ Receive emails
- ✅ Send emails (via external SMTP server)
- ✅ Session management
- ✅ Multi-domain support
- ✅ Email waiting functionality

#### Quick Usage

```python
from auto_update_q.temp_mail import DropMail

# Create instance and get temporary email
dropmail = DropMail()
temp_email = dropmail.get_temp_email()
print(f"Temporary email: {temp_email}")

# Receive emails
mails = dropmail.get_mails()
for mail in mails:
    print(f"From: {mail.from_addr}, Subject: {mail.subject}")

# Wait for new email
new_mail = dropmail.wait_for_mail(timeout=60)
if new_mail:
    print(f"Received new email: {new_mail.subject}")
```

For detailed documentation, see [temp_mail module documentation](src/auto_update_q/temp_mail/README.md)

## Installation

```bash
uv sync
```

## Run Demos

```bash
# Run AWS Builder ID auto registration demo
uv run python demo_auto_register.py

# Run temporary email demo
uv run python src/auto_update_q/temp_mail/quick_demo.py

# Run tests
uv run python src/auto_update_q/temp_mail/test_dropmail.py
uv run python test/test_auto_register.py
uv run python test/test_cli.py
```

## Usage Instructions

### Safari Browser Setup

Before using Safari browser, you need to configure the following settings:

1. Open Safari Preferences
2. Select the "Advanced" tab
3. Check "Show Develop menu in menu bar"
4. In the menu bar's "Develop" menu, select "Allow Remote Automation"

### Registration Process

1. The tool will automatically create a temporary email (or use specified email)
2. Automatically fill registration form
3. Automatically handle email verification code
4. Stop automation before graphical captcha
5. User manually completes graphical captcha
6. Registration information automatically saved to CSV file

### Registration Records

Registration information is saved to `.cache/auto_register_aws_builder.csv` file, containing:
- Timestamp
- Email address
- Password
- Name
- Status

## Development

Use uv to manage project dependencies:

```bash
# Install dependencies
uv sync

# Add new dependency
uv add package_name

# Run script
uv run python script.py

# Run command line tool
uv run auto-register-aws-builder --help
```

## Project Structure

```
auto-update-q/
├── src/
│   └── auto_update_q/
│       ├── __init__.py
│       ├── auto_register.py          # Main command line tool
│       ├── aws_builder/              # AWS Builder registration module
│       │   ├── aws_builder.py        # Main registrar
│       │   ├── browser_manager.py    # Browser management
│       │   ├── captcha_handler.py    # Captcha handling
│       │   ├── form_handler.py       # Form handling
│       │   └── ...
│       └── temp_mail/                # Temporary email module
│           ├── dropmail.py
│           └── ...
├── test/                             # Test files
│   ├── test_auto_register.py
│   └── test_cli.py
├── .cache/                           # Cache directory
│   └── auto_register_aws_builder.csv
├── demo_auto_register.py             # Demo script
└── pyproject.toml                    # Project configuration
```
