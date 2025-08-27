"""
DropMail 快速演示脚本
"""

from dropmail import DropMail


def main():
    """快速演示 DropMail 的主要功能"""
    
    print("=== DropMail 快速演示 ===\n")
    
    # 1. 创建实例
    print("1. 创建 DropMail 实例...")
    dropmail = DropMail()
    print(f"   认证令牌: {dropmail.auth_token}\n")
    
    # 2. 获取可用域名
    print("2. 获取可用域名...")
    try:
        domains = dropmail.get_domains()
        print(f"   找到 {len(domains)} 个可用域名:")
        for i, domain in enumerate(domains[:5]):  # 只显示前5个
            print(f"   {i+1}. {domain['name']}")
        print()
    except Exception as e:
        print(f"   错误: {e}\n")
        return
    
    # 3. 创建临时邮箱
    print("3. 创建临时邮箱...")
    try:
        session = dropmail.create_session()
        temp_email = session.addresses[0].address
        print(f"   临时邮箱地址: {temp_email}")
        print(f"   会话ID: {session.id}")
        print(f"   过期时间: {session.expires_at}\n")
    except Exception as e:
        print(f"   错误: {e}\n")
        return
    
    # 4. 添加额外地址
    print("4. 添加额外邮箱地址...")
    try:
        new_address = dropmail.add_address()
        print(f"   新地址: {new_address.address}\n")
    except Exception as e:
        print(f"   错误: {e}\n")
    
    # 5. 检查现有邮件
    print("5. 检查现有邮件...")
    try:
        mails = dropmail.get_mails()
        if mails:
            print(f"   找到 {len(mails)} 封邮件:")
            for i, mail in enumerate(mails):
                print(f"   邮件 {i+1}:")
                print(f"     从: {mail.from_addr}")
                print(f"     主题: {mail.subject}")
                print(f"     时间: {mail.received_at}")
        else:
            print("   暂无邮件")
        print()
    except Exception as e:
        print(f"   错误: {e}\n")
    
    # 6. 获取会话信息
    print("6. 获取会话信息...")
    try:
        session_info = dropmail.get_session_info()
        if session_info:
            print(f"   会话ID: {session_info.id}")
            print(f"   地址数量: {len(session_info.addresses)}")
            print(f"   邮件数量: {len(session_info.mails)}")
            print("   所有地址:")
            for i, addr in enumerate(session_info.addresses):
                print(f"     {i+1}. {addr.address}")
        else:
            print("   无法获取会话信息")
        print()
    except Exception as e:
        print(f"   错误: {e}\n")
    
    print("=== 演示完成 ===")
    print(f"\n你可以向以下地址发送测试邮件:")
    for addr in dropmail.addresses:
        print(f"  - {addr.address}")
    print("\n然后使用 dropmail.get_mails() 或 dropmail.wait_for_mail() 来接收邮件。")


if __name__ == "__main__":
    main()
