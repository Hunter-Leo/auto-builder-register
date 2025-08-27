#!/usr/bin/env python3
"""
Optimized selector configuration based on actual page source analysis
Most accurate selectors derived from analyzing page_source_step*.html files

Key findings (based on page_source_step3_name_page_165012.html analysis):
- Email input: input[autocomplete='on'][type='text'] 
- Name input: input[placeholder='Maria José Silva']
- Next button: button[data-testid='signup-next-button'] (confirmed exists)
- Form ID: form#SignUp
- Main CSS classes: awsui_variant-primary_vjswe_gmc8h_231, _2xAbzS8kNKd3Tl_k7Hlfav
"""

# Optimized selector configuration, sorted by priority
OPTIMIZED_SELECTORS = {
    # Step 1: Main page - Cookie handling
    "cookie_accept": [
        "button[data-id='awsccc-cb-btn-accept']",  # Precise data-id selector
        ".awsccc-u-btn-primary",  # Backup class selector
        "button[aria-label*='Accept']",  # Backup aria-label selector
    ],
    
    # Step 2: Email input page
    "email_input": [
        "input[autocomplete='on'][type='text']",  # Precise attribute combination based on page source
        "input#formField24-1756198202888-5657",  # Precise ID based on page source
        "[data-testid='signup-email-input'] input",  # Test ID selector
        "input.awsui_input_2rhyz_7gdci_149[autocomplete='on']",  # Class and attribute combination
        "input[aria-labelledby*='email']",  # Accessibility selector
        "input[type='text'][value*='@']",  # Email pattern matching
    ],
    "email_next_button": [
        "awsui-button[data-testid='test-primary-button'] button",  # Precise combination selector
        "button[data-testid='test-primary-button']",  # Direct button selector
        "button[type='submit'][class*='primary']",  # Backup selector
    ],
    
    # Step 3: Name input page
    "name_input": [
        "input[placeholder='Maria José Silva']",  # Precise selector based on placeholder
        "input#formField25-1756198202888-4727",  # Precise ID based on page source
        "[data-testid='signup-full-name-input'] input",  # Test ID selector
        "input[type='text'][autocomplete='on']:not([value*='@'])",  # Non-email text input
        "input.awsui_input_2rhyz_7gdci_149[placeholder]",  # Based on class and placeholder
    ],
    "name_next_button": [
        "button[data-testid='signup-next-button']",  # Precise test ID (confirmed from page source)
        "button[data-testid='signup-next-button'][type='submit']",  # More specific selector
        "button.awsui_variant-primary_vjswe_gmc8h_231[data-testid='signup-next-button']",  # Complete class match
        "button._2xAbzS8kNKd3Tl_k7Hlfav.awsui_variant-primary_vjswe_gmc8h_231",  # Combined class selector
    ],
    
    # Step 4: Email verification code page
    "verification_code_input": [
        "input[class*='awsui_input'][autocomplete='on'][type='text']",  # Match actual page elements
        "input[aria-labelledby*='formField'][type='text']",  # Based on aria-labelledby attribute
        "input[data-testid='verification-code-input']",
        "input[placeholder*='code']",
        "input[type='text'][maxlength='6']",
        "input[aria-label*='verification']",
        ".verification-code input",
        "input[type='text'][value='']",  # Empty value text input field
    ],
    "verify_button": [
        "button[data-testid='email-verification-verify-button']",  # Match actual verification button
        "button[data-testid*='verification'][data-testid*='verify']",  # Generic verification button pattern
        "awsui-button[data-testid='test-primary-button'] button",  # Match AWS UI button
        "button[data-testid='signup-next-button']",  # Registration next button
        "button[data-testid='verify-button']",
        "button[type='submit'][class*='primary']",
        "button:contains('Verify')",
        "button[class*='awsui'][class*='primary']",  # AWS UI primary button
        "button[type='submit'][class*='awsui_variant-primary']",  # AWS UI primary submit button
        ".verify-btn",
    ],
    "resend_code_button": [
        "button[data-testid='email-verification-resend-code-button']",  # Precise match for resend button
        "button[class*='awsui_variant-normal'][data-testid*='resend']",  # Generic resend button pattern
        "button[class*='awsui_button'][class*='variant-normal']",  # AWS UI normal button
        "button[type='button'][data-testid*='resend']",  # Match by type and testid
        ".resend-code-btn",
    ],
    
    # Step 5: Password setup page
    "password_input": [
        "input#awsui-input-1",  # Precise ID for password input field
        "input[class*='awsui-input'][class*='type-password'][type='password']:nth-of-type(2)",  # Second password field
        "input[type='password'][autocomplete='on']:nth-of-type(2)",  # Second password input field
        "input[class*='awsui-input'][type='password']:nth-of-type(2)",  # Second awsui password field
        "input[data-testid='password-input']",
        "input[type='password'][autocomplete='new-password']:nth-of-type(2)",
        "input[aria-label*='password']:not([aria-label*='confirm'])",
        "#password",
    ],
    "confirm_password_input": [
        "input#awsui-input-0",  # Precise ID for password confirmation field
        "input[class*='awsui-input'][class*='type-password'][type='password']:nth-of-type(1)",  # First password field
        "input[type='password'][autocomplete='on']:nth-of-type(1)",  # First password input field
        "input[class*='awsui-input'][type='password']:nth-of-type(1)",  # First awsui password field
        "input[data-testid='test-retype-input']",  # Direct match for data-testid
        "input[data-testid='confirm-password-input']",
        "input[aria-label*='confirm']",
        "#confirmPassword",
    ],
    "password_next_button": [
        "button[data-testid='password-next-button']",
        "button[type='submit'][class*='primary']",
        "button[class*='awsui'][class*='primary']",
    ],
    
    # CAPTCHA related
    "captcha_container": [
        ".captcha-container",
        "[data-testid='captcha']",
        ".challenge-container",
        "#captcha",
    ],
    "captcha_input": [
        "input[data-testid='captcha-input']",
        "input[placeholder*='captcha']",
        ".captcha-input input",
        "input[aria-label*='captcha']",
    ],
    "captcha_submit": [
        "button[data-testid='captcha-submit']",
        "button[type='submit']:contains('Submit')",
        ".captcha-submit",
    ],
    "captcha_error": [
        ".captcha-error",
        "[data-testid='captcha-error']",
        ".error-message:contains('captcha')",
    ],
    
    # Success and error indicators
    "success_indicators": [
        ".success-message",
        "[data-testid='success']",
        ".registration-complete",
        "h1:contains('Welcome')",
        ".dashboard",
    ],
    "error_messages": [
        ".error-message",
        "[data-testid='error']",
        ".alert-error",
        ".validation-error",
    ],
    "registration_form": [
        "form[data-testid='signup-form']",
        "#SignUp",
        ".signup-form",
    ],
    "dashboard_elements": [
        ".aws-console",
        "[data-testid='dashboard']",
        ".builder-dashboard",
        "nav[aria-label*='AWS']",
    ],
    "builder_id_display": [
        "[data-testid='builder-id']",
        ".builder-id",
        "#builderId",
    ],
}

# Timeout configuration
TIMEOUT_CONFIG = {
    "email_input": 15,
    "name_input": 10,
    "verification_code_input": 10,
    "password_input": 10,
    "captcha_container": 5,
    "default": 10,
}

# Retry configuration
RETRY_CONFIG = {
    "email_input": {"max_rounds": 3, "timeout": 5},
    "name_input": {"max_rounds": 3, "timeout": 3},
    "verification_code_input": {"max_rounds": 2, "timeout": 5},
    "password_input": {"max_rounds": 2, "timeout": 3},
    "captcha_container": {"max_rounds": 2, "timeout": 2},
    "default": {"max_rounds": 3, "timeout": 3},
}


def get_selector(element_name: str) -> list:
    """
    Get selector list for specified element
    
    Args:
        element_name: Element name
        
    Returns:
        Selector list
    """
    return OPTIMIZED_SELECTORS.get(element_name, [])


def get_all_selectors() -> dict:
    """
    Get all selector configurations
    
    Returns:
        Complete selector configuration dictionary
    """
    return OPTIMIZED_SELECTORS.copy()


def get_timeout(element_name: str, default: int = 10) -> int:
    """
    Get timeout configuration for specified element
    
    Args:
        element_name: Element name
        default: Default timeout duration
        
    Returns:
        Timeout duration (seconds)
    """
    return TIMEOUT_CONFIG.get(element_name, TIMEOUT_CONFIG.get("default", default))


def get_retry_config(element_name: str, config_key: str, default_value) -> any:
    """
    Get retry configuration for specified element
    
    Args:
        element_name: Element name
        config_key: Configuration key name (max_rounds or timeout)
        default_value: Default value
        
    Returns:
        Configuration value
    """
    element_config = RETRY_CONFIG.get(element_name, RETRY_CONFIG.get("default", {}))
    return element_config.get(config_key, default_value)


def add_selector(element_name: str, selector: str, priority: int = -1) -> None:
    """
    Add new selector
    
    Args:
        element_name: Element name
        selector: Selector string
        priority: Priority (0 is highest, -1 is lowest)
    """
    if element_name not in OPTIMIZED_SELECTORS:
        OPTIMIZED_SELECTORS[element_name] = []
    
    if priority == -1:
        OPTIMIZED_SELECTORS[element_name].append(selector)
    else:
        OPTIMIZED_SELECTORS[element_name].insert(priority, selector)


def update_timeout(element_name: str, timeout: int) -> None:
    """
    Update element timeout configuration
    
    Args:
        element_name: Element name
        timeout: Timeout duration (seconds)
    """
    TIMEOUT_CONFIG[element_name] = timeout


def update_retry_config(element_name: str, max_rounds: int = None, timeout: int = None) -> None:
    """
    Update element retry configuration
    
    Args:
        element_name: Element name
        max_rounds: Maximum retry rounds
        timeout: Timeout per round
    """
    if element_name not in RETRY_CONFIG:
        RETRY_CONFIG[element_name] = {}
    
    if max_rounds is not None:
        RETRY_CONFIG[element_name]["max_rounds"] = max_rounds
    
    if timeout is not None:
        RETRY_CONFIG[element_name]["timeout"] = timeout
