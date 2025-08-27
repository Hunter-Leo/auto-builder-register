"""
Auto Update Q - AWS Builder ID Automatic Registration Tool

This package provides automatic AWS Builder ID account registration functionality, including:
- Temporary email service (temp_mail)
- AWS Builder registrar (aws_builder)
- Command line tool (auto_register)
"""

__version__ = "0.1.0"
__author__ = "Auto Update Q Team"
__description__ = "AWS Builder ID Automatic Registration Tool"

# Export main components
from .aws_builder.aws_builder import AWSBuilder, AWSBuilderCredentials
from .temp_mail.dropmail import DropMail

__all__ = [
    "AWSBuilder",
    "AWSBuilderCredentials", 
    "DropMail"
]
