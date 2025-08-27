"""
Auto Update Q - AWS Builder ID 自动注册工具

该包提供了自动注册 AWS Builder ID 账号的功能，包括：
- 临时邮箱服务 (temp_mail)
- AWS Builder 注册器 (aws_builder)
- 命令行工具 (auto_register)
"""

__version__ = "0.1.0"
__author__ = "Auto Update Q Team"
__description__ = "AWS Builder ID 自动注册工具"

# 导出主要组件
from .aws_builder.aws_builder import AWSBuilder, AWSBuilderCredentials
from .temp_mail.dropmail import DropMail

__all__ = [
    "AWSBuilder",
    "AWSBuilderCredentials", 
    "DropMail"
]
