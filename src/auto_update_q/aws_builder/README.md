# AWS Builder ID Automatic Registration Module

AWS Builder ID automatic registration functionality module based on Selenium, featuring modular design, separation of concerns, and clean maintainable code.

## 🎯 Features

### Modular Design
- **Separation of Concerns**: Each module handles specific functionality, reducing coupling
- **Code Reuse**: Components can be used and tested independently
- **Easy Maintenance**: Modifying one feature doesn't affect other modules
- **High Extensibility**: Easy to add new features or replace components

### Core Components

| Component | File | Responsibility |
|-----------|------|----------------|
| **Configuration Management** | `config.py` | Centralized management of all configuration items |
| **Browser Management** | `browser_manager.py` | Browser initialization and configuration |
| **Element Waiting** | `element_waiter.py` | Page element waiting and finding |
| **Form Handling** | `form_handler.py` | Form filling logic |
| **CAPTCHA Handling** | `captcha_handler.py` | Image and email verification code handling |
| **Registration Checking** | `registration_checker.py` | Registration status verification |
| **Selector Configuration** | `optimized_selectors.py` | Page element selectors |
| **Main Controller** | `aws_builder.py` | Main business logic coordination |

## 🚀 Features

- ✅ **Automatic Form Filling** - Intelligent form recognition and filling
- ✅ **Email Verification Handling** - Support for manual input and automatic verification code retrieval
- ✅ **Image CAPTCHA Handling** - Intelligent detection and manual input support
- ✅ **Session Management** - Maintain login state, support page navigation
- ✅ **Password Generation** - Automatically generate secure passwords that meet requirements
- ✅ **Multiple Selectors** - Improve element finding success rate
- ✅ **Intelligent Retry** - Automatic retry mechanism to improve success rate
- ✅ **Dynamic Waiting** - Intelligent waiting for page changes, no hardcoded delays
- ✅ **Detailed Logging** - Complete operation log recording
- ✅ **Error Handling** - Comprehensive exception handling mechanism

## 📦 Install Dependencies

```bash
uv add selenium webdriver-manager
```

## 🎮 Quick Usage

### Basic Registration

```python
from auto_update_q.aws_builder import AWSBuilder

# Use context manager (recommended)
with AWSBuilder(headless=False, debug=True) as aws_builder:
    credentials = aws_builder.register_aws_builder(
        email="your-email@example.com",
        name="Your Name"
    )
    
    if credentials:
        print(f"Registration successful! Email: {credentials.email}")
        print(f"Password: {credentials.password}")
    else:
        print("Registration failed")
```

### Integration with Temporary Email

```python
from auto_update_q.aws_builder import AWSBuilder
from auto_update_q.temp_mail import DropMail

# Create temporary email
dropmail = DropMail()
temp_email = dropmail.get_temp_email()

# Register using temporary email (auto-get verification code)
with AWSBuilder() as aws_builder:
    credentials = aws_builder.register_aws_builder(
        email=temp_email,
        name="Test User",
        dropmail=dropmail  # Auto-get email verification code
    )
```

### Custom Configuration

```python
with AWSBuilder(
    headless=False,      # Show browser interface
    timeout=60,          # Timeout duration
    debug=True,          # Enable debug logging
    keep_browser=True    # Keep browser open
) as aws_builder:
    credentials = aws_builder.register_aws_builder(
        email="test@example.com",
        name="Test User",
        password="CustomPassword123!"  # Custom password
    )
```

## 🏗️ Architecture Design

### Component Relationship Diagram

```
AWSBuilder (Main Controller)
├── BrowserManager (Browser Management)
├── ElementWaiter (Element Waiting)
├── FormHandler (Form Handling)
│   └── ElementWaiter
├── CaptchaHandler (CAPTCHA Handling)
│   └── ElementWaiter
├── RegistrationChecker (Status Checking)
│   └── ElementWaiter
└── Config (Configuration Management)
```

### Data Flow

```
1. Initialize Components → 2. Setup Browser → 3. Navigate Page
                                           ↓
8. Return Credentials ← 7. Check Status ← 6. Handle CAPTCHA ← 4. Fill Form
                                           ↓
                                       5. Email Verification
```

## 🔧 Configuration

### Browser Configuration (`config.py`)

```python
BROWSER_OPTIONS = {
    "headless_args": [...],      # Headless mode arguments
    "common_args": [...],        # Common arguments
    "experimental_options": {...} # Experimental options
}
```

### Selector Configuration (`optimized_selectors.py`)

```python
OPTIMIZED_SELECTORS = {
    "email_input": [...],        # Email input field selectors
    "name_input": [...],         # Name input field selectors
    "password_input": [...],     # Password input field selectors
    # ... more selectors
}
```

### Timeout and Retry Configuration

```python
TIMEOUT_CONFIG = {
    "email_input": 15,           # Email input timeout
    "default": 10,               # Default timeout
}

RETRY_CONFIG = {
    "email_input": {
        "max_rounds": 3,         # Maximum retry rounds
        "timeout": 5             # Timeout per round
    }
}
```

## 🧪 Testing and Demo

### Run Demo

```bash
# Run demo
uv run python src/auto_update_q/aws_builder/demo.py
```

### Unit Testing

```bash
# Test individual components
uv run python test/test_aws_builder_refactored.py
```

## 🔍 Troubleshooting

### Common Issues

1. **Browser Launch Failure**
   - Check if Edge browser is installed
   - Check network connection
   - Try manually downloading EdgeDriver

2. **Element Finding Failure**
   - Check if selector configuration is up to date
   - Enable debug mode to view detailed logs
   - Update selector configuration

3. **CAPTCHA Handling Failure**
   - Ensure running in GUI mode
   - Check if CAPTCHA input is correct
   - Check logs for specific errors

### Debugging Tips

```python
# Enable detailed logging
with AWSBuilder(debug=True) as aws_builder:
    # ... registration logic

# Keep browser open for debugging
with AWSBuilder(keep_browser=True) as aws_builder:
    # ... registration logic
    input("Press Enter to close browser...")
```

## 🛠️ Extension Development

### Adding New Form Fields

1. Add selectors in `optimized_selectors.py`
2. Add handling methods in `form_handler.py`
3. Call new methods in main flow

### Adding New CAPTCHA Types

1. Add handling methods in `captcha_handler.py`
2. Update main flow call logic

### Custom Browser Configuration

1. Modify configuration in `config.py`
2. Or pass custom parameters during initialization

## 🎉 Core Advantages

Through modular design, we achieved:

1. **Clear Code**: Separation of concerns, clear logic
2. **Easy Maintenance**: Modular design facilitates modification and extension
3. **High Testability**: Each component can be tested independently
4. **Intelligent Waiting**: Dynamic waiting mechanism, no hardcoded delays
5. **Strong Extensibility**: Foundation for future feature expansion

The modular design makes the code clearer and more maintainable, while also providing convenience for team collaboration and feature expansion.
