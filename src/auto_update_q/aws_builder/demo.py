#!/usr/bin/env python3
"""
AWS Builder ID 自动注册演示
展示模块的使用方法
"""

import sys
import os
sys.path.append('./src')

from auto_update_q.aws_builder import AWSBuilder
from auto_update_q.temp_mail import DropMail


def demo_basic_registration():
    """基础注册演示"""
    print("=== 基础注册演示 ===")
    
    with AWSBuilder(headless=False, debug=True) as aws_builder:
        credentials = aws_builder.register_aws_builder(
            email="test@example.com",
            name="Test User"
        )
        
        if credentials:
            print(f"✓ 注册成功！")
            print(f"邮箱: {credentials.email}")
            print(f"密码: {credentials.password}")
            print(f"姓名: {credentials.name}")
        else:
            print("✗ 注册失败")


def demo_with_temp_email():
    """使用临时邮箱的注册演示"""
    print("=== 使用临时邮箱注册演示 ===")
    
    # 创建临时邮箱
    dropmail = DropMail()
    temp_email = dropmail.get_temp_email()
    print(f"临时邮箱: {temp_email}")
    
    # 使用临时邮箱注册
    with AWSBuilder(headless=False, debug=True) as aws_builder:
        credentials = aws_builder.register_aws_builder(
            email=temp_email,
            name="Temp User",
            dropmail=dropmail  # 自动获取验证码
        )
        
        if credentials:
            print(f"✓ 注册成功！")
            print(f"邮箱: {credentials.email}")
            print(f"密码: {credentials.password}")
            
            # 注册成功后导航到其他页面
            success = aws_builder.navigate_to_url("https://view.awsapps.com/start")
            if success:
                print(f"当前页面: {aws_builder.get_current_url()}")
        else:
            print("✗ 注册失败")


def demo_custom_password():
    """自定义密码注册演示"""
    print("=== 自定义密码注册演示 ===")
    
    custom_password = "MySecurePassword123!"
    
    with AWSBuilder(headless=False, debug=True) as aws_builder:
        credentials = aws_builder.register_aws_builder(
            email="custom@example.com",
            name="Custom User",
            password=custom_password
        )
        
        if credentials:
            print(f"✓ 注册成功！")
            print(f"使用的密码: {credentials.password}")
        else:
            print("✗ 注册失败")


def main():
    """主函数"""
    print("AWS Builder ID 自动注册演示")
    print("=" * 50)
    
    demos = [
        ("1", "基础注册演示", demo_basic_registration),
        ("2", "使用临时邮箱注册演示", demo_with_temp_email),
        ("3", "自定义密码注册演示", demo_custom_password),
    ]
    
    print("可用演示：")
    for key, name, _ in demos:
        print(f"  {key}. {name}")
    
    choice = input("\n请选择演示 (1-3, 或按回车运行基础演示): ").strip()
    
    if choice == "":
        choice = "1"  # 默认运行基础演示
    
    # 运行指定演示
    for key, name, func in demos:
        if choice == key:
            print(f"\n{'='*20} {name} {'='*20}")
            try:
                func()
            except KeyboardInterrupt:
                print("\n用户中断演示")
            except Exception as e:
                print(f"演示出错: {e}")
            break
    else:
        print("无效选择")


if __name__ == "__main__":
    main()
