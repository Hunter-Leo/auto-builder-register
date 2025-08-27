#!/usr/bin/env python3
"""
AWS Builder ID 自动注册演示
展示使用DropMail自动获取验证码的完整流程
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from auto_update_q.aws_builder.aws_builder import AWSBuilder
from auto_update_q.temp_mail.dropmail import DropMail

def main():
    """主演示函数"""
    print("🚀 AWS Builder ID 自动注册演示")
    print("=" * 50)
    
    # 步骤1: 创建临时邮箱
    print("📧 步骤1: 创建临时邮箱...")
    dropmail = DropMail()
    temp_email = dropmail.get_temp_email()
    print(f"✓ 临时邮箱创建成功: {temp_email}")
    
    # 步骤2: 初始化注册器
    print("\n🔧 步骤2: 初始化AWS Builder注册器...")
    registrar = AWSBuilder(headless=False, debug=True, keep_browser=True)  # 保持浏览器打开
    print("✓ 注册器初始化完成")
    
    # 步骤3: 显示注册信息
    print("\n📋 步骤3: 注册信息")
    print("-" * 30)
    print(f"邮箱: {temp_email}")
    print("姓名: Crazy Joe")
    print("密码: CrazyJoe@2025")
    print("验证方式: 自动获取（DropMail）")
    print("-" * 30)
    
    try:
        # 步骤4: 开始自动注册
        print("\n🎯 步骤4: 开始自动注册流程...")
        print("注意: 程序将自动处理验证码，无需手动输入")
        
        result = registrar.register_aws_builder(
            email=temp_email,
            name="Crazy Joe",
            password="CrazyJoe@2025",
            dropmail=dropmail  # 关键：传入DropMail实例
        )
        
        # 步骤5: 显示结果
        print("\n📊 步骤5: 注册结果")
        print("=" * 50)
        
        if result:
            print("🎉 注册成功！")
            print(f"✓ 邮箱: {result.email}")
            print(f"✓ 密码: {result.password}")
            print("\n💡 提示: 请保存这些凭证信息")
        else:
            print("❌ 注册失败")
            print("请检查日志了解详细错误信息")
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        if not registrar.keep_browser:
            registrar.close()  # 只有在不保持浏览器时才关闭
        print("✓ 演示完成")
        if registrar.keep_browser:
            print("\n💡 浏览器保持打开状态，您可以继续操作或手动关闭")

if __name__ == "__main__":
    main()
