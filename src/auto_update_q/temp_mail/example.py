"""
DropMail 使用示例

演示如何使用 DropMail 类进行临时邮箱操作
"""

import time
from dropmail import DropMail


def main():
    """主函数，演示 DropMail 的基本用法"""
    
    # 1. 创建 DropMail 实例
    print("1. 创建 DropMail 实例...")
    dropmail = DropMail()
    print(f"认证令牌: {dropmail.auth_token}")
    
    # 2. 获取可用域名
    print("\n2. 获取可用域名...")
    try:
        domains = dropmail.get_domains()
        print("可用域名:")
        for domain in domains[:3]:  # 只显示前3个
            print(f"  - {domain['name']} (ID: {domain['id']})")
    except Exception as e:
        print(f"获取域名失败: {e}")
    
    # 3. 创建临时邮箱会话
    print("\n3. 创建临时邮箱会话...")
    try:
        session = dropmail.create_session()
        print(f"会话ID: {session.id}")
        print(f"过期时间: {session.expires_at}")
        print(f"临时邮箱地址: {session.addresses[0].address}")
    except Exception as e:
        print(f"创建会话失败: {e}")
        return
    
    # 4. 获取临时邮箱地址
    print("\n4. 获取临时邮箱地址...")
    temp_email = dropmail.get_temp_email()
    print(f"临时邮箱: {temp_email}")
    
    # 5. 添加额外的邮箱地址
    print("\n5. 添加额外的邮箱地址...")
    try:
        new_address = dropmail.add_address()
        print(f"新邮箱地址: {new_address.address}")
    except Exception as e:
        print(f"添加地址失败: {e}")
    
    # 6. 检查现有邮件
    print("\n6. 检查现有邮件...")
    try:
        mails = dropmail.get_mails()
        if mails:
            print(f"找到 {len(mails)} 封邮件:")
            for mail in mails:
                print(f"  - 从: {mail.from_addr}")
                print(f"    到: {mail.to_addr}")
                print(f"    主题: {mail.subject}")
                print(f"    时间: {mail.received_at}")
                print(f"    内容: {mail.text[:100]}...")
        else:
            print("暂无邮件")
    except Exception as e:
        print(f"获取邮件失败: {e}")
    
    # 7. 等待新邮件（演示用，实际使用时可以根据需要调整超时时间）
    print(f"\n7. 等待新邮件（30秒超时）...")
    print(f"请发送邮件到: {temp_email}")
    
    try:
        new_mail = dropmail.wait_for_mail(timeout=30, check_interval=3)
        if new_mail:
            print("收到新邮件!")
            print(f"  从: {new_mail.from_addr}")
            print(f"  主题: {new_mail.subject}")
            print(f"  内容: {new_mail.text}")
        else:
            print("超时，未收到新邮件")
    except Exception as e:
        print(f"等待邮件失败: {e}")
    
    # 8. 发送邮件示例（需要配置SMTP信息）
    print("\n8. 发送邮件示例...")
    print("注意: 发送邮件需要配置有效的SMTP服务器信息")
    
    # 取消注释以下代码并填入有效的SMTP信息来测试发送功能
    """
    try:
        success = dropmail.send_email(
            to_email=temp_email,
            subject="测试邮件",
            body="这是一封测试邮件",
            from_email="your_email@gmail.com",  # 替换为你的邮箱
            password="your_password"  # 替换为你的密码或应用专用密码
        )
        if success:
            print("邮件发送成功!")
        else:
            print("邮件发送失败!")
    except Exception as e:
        print(f"发送邮件异常: {e}")
    """
    
    # 9. 获取会话信息
    print("\n9. 获取会话信息...")
    try:
        session_info = dropmail.get_session_info()
        if session_info:
            print(f"会话ID: {session_info.id}")
            print(f"过期时间: {session_info.expires_at}")
            print(f"地址数量: {len(session_info.addresses)}")
            print(f"邮件数量: {len(session_info.mails)}")
        else:
            print("无法获取会话信息")
    except Exception as e:
        print(f"获取会话信息失败: {e}")


if __name__ == "__main__":
    main()
