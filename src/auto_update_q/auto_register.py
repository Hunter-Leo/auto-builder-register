#!/usr/bin/env python3
"""
AWS Builder ID 自动注册命令行工具
使用Typer框架实现，支持自动注册到图形验证码前停止
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


# 应用实例
app = typer.Typer(
    name="auto-register-aws-builder",
    help="AWS Builder ID 自动注册工具 - 自动完成注册流程直到图形验证码前",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True  # 无参数时显示帮助
)

# 全局变量
current_browser = None
registration_data = None


def setup_logging(debug: bool = False) -> logging.Logger:
    """设置日志记录器"""
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
    """信号处理器，用于优雅退出"""
    logger = logging.getLogger("auto_register")
    logger.info("收到退出信号，正在清理资源...")
    
    if current_browser:
        try:
            current_browser.close()
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")
    
    sys.exit(0)


def save_registration_data(email: str, password: str, name: str, 
                         cache_file: Path, logger: logging.Logger) -> None:
    """
    保存注册数据到CSV文件
    
    Args:
        email: 邮箱地址
        password: 密码
        name: 姓名
        cache_file: 缓存文件路径
        logger: 日志记录器
    """
    try:
        # 确保目录存在
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 检查文件是否存在，如果不存在则创建并写入标题行
        file_exists = cache_file.exists()
        
        with open(cache_file, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'email', 'password', 'name', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # 如果文件不存在，写入标题行
            if not file_exists:
                writer.writeheader()
            
            # 写入数据
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'email': email,
                'password': password,
                'name': name,
                'status': 'pending_captcha'
            })
        
        logger.info(f"注册数据已保存到: {cache_file}")
        
    except Exception as e:
        logger.error(f"保存注册数据失败: {e}")


def select_session_from_list(dropmail: DropMail, logger: logging.Logger) -> Optional[str]:
    """
    显示可恢复的 Session 列表供用户选择
    
    Args:
        dropmail: DropMail 实例
        logger: 日志记录器
        
    Returns:
        选择的 Session ID，如果取消则返回 None
    """
    logger.info("🔍 正在检查可用的 Sessions...")
    
    # 清理过期的 Sessions
    expired_count = dropmail.cleanup_expired_sessions()
    if expired_count > 0:
        logger.info(f"🧹 已清理 {expired_count} 个过期的 Sessions")
    
    # 获取可用的 Sessions
    sessions = dropmail.list_cached_sessions()
    
    if not sessions:
        logger.warning("📭 没有找到可恢复的 Sessions")
        return None
    
    # 验证 Sessions 有效性并过滤
    valid_sessions = []
    logger.info("🔍 验证 Sessions 有效性...")
    
    for session_cache in sessions:
        # 临时切换到该 session 进行验证
        old_token = dropmail.auth_token
        old_session = dropmail.session_id
        
        dropmail.auth_token = session_cache.auth_token
        dropmail.session_id = session_cache.session_id
        
        if dropmail._verify_session():
            valid_sessions.append(session_cache)
        else:
            logger.info(f"❌ Session {session_cache.session_id[:8]}... 已过期，将被删除")
            dropmail._remove_expired_session(session_cache.session_id)
        
        # 恢复原来的设置
        dropmail.auth_token = old_token
        dropmail.session_id = old_session
    
    if not valid_sessions:
        logger.warning("📭 没有找到有效的 Sessions")
        return None
    
    # 显示 Sessions 列表
    logger.info("📋 可恢复的 Sessions:")
    logger.info("=" * 80)
    
    for i, session_cache in enumerate(valid_sessions, 1):
        # 格式化时间显示
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
        
        logger.info(f"{i}. 邮箱: {session_cache.email_address}")
        logger.info(f"   Session ID: {session_cache.session_id}")
        logger.info(f"   创建时间: {created_time}")
        logger.info(f"   最后访问: {last_accessed}")
        logger.info("-" * 40)
    
    # 用户选择
    while True:
        try:
            choice = input(f"\n请选择要恢复的 Session (1-{len(valid_sessions)}, 0=取消): ").strip()
            
            if choice == '0':
                logger.info("❌ 用户取消选择")
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(valid_sessions):
                selected_session = valid_sessions[choice_num - 1]
                logger.info(f"✓ 选择了 Session: {selected_session.email_address}")
                return selected_session.session_id
            else:
                print(f"❌ 请输入 1-{len(valid_sessions)} 之间的数字")
                
        except ValueError:
            print("❌ 请输入有效的数字")
        except KeyboardInterrupt:
            logger.info("\n❌ 用户中断选择")
            return None


def monitor_emails(dropmail: DropMail, logger: logging.Logger, check_interval: int = 10) -> None:
    """
    持续监控邮件并展示新收到的邮件
    
    Args:
        dropmail: DropMail 实例
        logger: 日志记录器
        check_interval: 检查间隔（秒）
    """
    logger.info("📧 开始监控邮件...")
    logger.info(f"📬 邮箱地址: {dropmail.addresses[0].address if dropmail.addresses else 'N/A'}")
    logger.info(f"🔄 检查间隔: {check_interval} 秒")
    logger.info("⚠️  按 Ctrl+C 停止监控")
    logger.info("=" * 60)
    
    # 获取当前已有的邮件数量
    try:
        existing_mails = dropmail.get_mails()
        last_mail_count = len(existing_mails)
        last_mail_id = existing_mails[-1].id if existing_mails else None
        
        if existing_mails:
            logger.info(f"📨 当前已有 {last_mail_count} 封邮件")
            logger.info("最近的邮件:")
            for mail in existing_mails[-3:]:  # 显示最近3封邮件
                logger.info(f"  • 来自: {mail.from_addr}")
                logger.info(f"    主题: {mail.subject}")
                logger.info(f"    时间: {mail.received_at}")
                logger.info("-" * 30)
        else:
            logger.info("📭 暂无邮件")
            
    except Exception as e:
        logger.error(f"❌ 获取现有邮件失败: {e}")
        last_mail_id = None
        last_mail_count = 0
    
    logger.info("🔍 开始监控新邮件...")
    
    try:
        while True:
            try:
                # 检查新邮件
                if last_mail_id:
                    new_mails = dropmail.get_mails(after_mail_id=last_mail_id)
                else:
                    all_mails = dropmail.get_mails()
                    new_mails = all_mails[last_mail_count:] if len(all_mails) > last_mail_count else []
                
                if new_mails:
                    logger.info(f"🎉 收到 {len(new_mails)} 封新邮件!")
                    logger.info("=" * 60)
                    
                    for mail in new_mails:
                        logger.info(f"📧 新邮件:")
                        logger.info(f"   来自: {mail.from_addr}")
                        logger.info(f"   收件: {mail.to_addr}")
                        logger.info(f"   主题: {mail.subject}")
                        logger.info(f"   时间: {mail.received_at}")
                        logger.info(f"   内容预览: {mail.text[:100]}..." if len(mail.text) > 100 else f"   内容: {mail.text}")
                        logger.info("-" * 40)
                    
                    # 更新最后邮件ID和数量
                    last_mail_id = new_mails[-1].id
                    last_mail_count += len(new_mails)
                    
                    logger.info("🔍 继续监控新邮件...")
                
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ 检查邮件时出错: {e}")
                time.sleep(check_interval)
                
    except KeyboardInterrupt:
        logger.info("\n⚠️  停止邮件监控")


def wait_for_user_action(timeout_minutes: int, logger: logging.Logger) -> None:
    """
    等待用户操作或超时
    
    Args:
        timeout_minutes: 超时时间（分钟）
        logger: 日志记录器
    """
    logger.info(f"等待用户操作，{timeout_minutes}分钟后自动退出...")
    logger.info("您可以:")
    logger.info("1. 在浏览器中手动完成图形验证码")
    logger.info("2. 按 Ctrl+C 提前退出")
    logger.info("3. 直接关闭浏览器")
    
    start_time = time.time()
    timeout_seconds = timeout_minutes * 60
    
    try:
        while time.time() - start_time < timeout_seconds:
            # 检查浏览器是否还在运行
            if current_browser and current_browser.driver:
                try:
                    # 尝试获取当前URL，如果浏览器关闭会抛出异常
                    current_browser.driver.current_url
                    time.sleep(5)  # 每5秒检查一次
                except Exception:
                    logger.info("检测到浏览器已关闭，程序退出")
                    return
            else:
                break
        
        logger.info(f"{timeout_minutes}分钟超时，程序自动退出")
        
    except KeyboardInterrupt:
        logger.info("用户手动退出")


@app.command()
def register(
    email: Annotated[Optional[str], typer.Option(
        "--email", "-e",
        help="📧 指定邮箱地址。如果不提供，将自动生成临时邮箱"
    )] = None,
    
    name: Annotated[str, typer.Option(
        "--name", "-n",
        help="👤 用户姓名"
    )] = "Crazy Joe",
    
    password: Annotated[Optional[str], typer.Option(
        "--password", "-p",
        help="🔐 指定密码。如果不提供，将使用默认密码 CrazyJoe@2025"
    )] = "CrazyJoe@2025",
    
    headless: Annotated[bool, typer.Option(
        "--headless",
        help="👻 使用无头模式运行浏览器（不显示浏览器窗口）"
    )] = False,
    
    browser: Annotated[str, typer.Option(
        "--browser", "-b",
        help="🌐 指定浏览器类型",
        click_type=click.Choice(["safari", "edge"], case_sensitive=False)
    )] = "edge",
    
    timeout: Annotated[int, typer.Option(
        "--timeout", "-t",
        help="⏱️ 操作超时时间（秒）",
        min=10, max=300
    )] = 30,
    
    wait_minutes: Annotated[int, typer.Option(
        "--wait-minutes", "-w",
        help="⏳ 停止自动化后等待用户操作的时间（分钟）",
        min=1, max=120
    )] = 30,
    
    cache_file: Annotated[str, typer.Option(
        "--cache-file", "-c",
        help="💾 注册数据缓存文件路径"
    )] = ".cache/auto_register_aws_builder.csv",
    
    debug: Annotated[bool, typer.Option(
        "--debug", "-d",
        help="🐛 启用调试模式，显示详细日志"
    )] = False,
    
    no_temp_email: Annotated[bool, typer.Option(
        "--no-temp-email",
        help="🚫 不使用临时邮箱，需要手动处理邮箱验证"
    )] = False,
    
    dropmail_cache: Annotated[str, typer.Option(
        "--dropmail-cache",
        help="📁 DropMail Session 缓存文件路径"
    )] = ".cache/dropmail_sessions.json",
    
    only_mail: Annotated[bool, typer.Option(
        "--only-mail",
        help="📧 只注册临时邮箱并监控邮件，不进行 AWS Builder ID 注册"
    )] = False
):
    """
    自动注册 AWS Builder ID 账号
    
    该工具会自动完成注册流程直到图形验证码步骤，然后停止自动化操作，
    允许用户手动完成剩余步骤。
    
    [bold green]功能特性:[/bold green]
    
    • 自动生成或使用指定的临时邮箱
    • 自动填写注册表单
    • 自动处理邮箱验证码
    • 在图形验证码前停止，等待用户手动操作
    • 支持 Safari 浏览器
    • 自动保存注册信息到CSV文件
    • 支持 Session 持久化
    • 支持只注册邮箱模式
    
    [bold yellow]使用示例:[/bold yellow]
    
    # 使用默认设置自动注册
    auto-register-aws-builder register
    
    # 指定邮箱和姓名
    auto-register-aws-builder register --email test@example.com --name "John Doe"
    
    # 只注册临时邮箱并监控邮件
    auto-register-aws-builder register --only-mail
    
    # 使用无头模式
    auto-register-aws-builder register --headless
    
    # 启用调试模式
    auto-register-aws-builder register --debug
    """
    global current_browser, registration_data
    
    # 设置日志
    logger = setup_logging(debug)
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 开始 AWS Builder ID 自动注册")
    logger.info("=" * 60)
    
    try:
        # 步骤1: 准备邮箱
        dropmail = None
        if only_mail or (not email and not no_temp_email):
            logger.info("📧 创建临时邮箱...")
            dropmail = DropMail(cache_file=dropmail_cache)
            email = dropmail.get_temp_email()
            logger.info(f"✓ 临时邮箱: {email}")
            logger.info(f"✓ Session ID: {dropmail.session_id}")
            
            if only_mail:
                # 只注册邮箱模式，直接开始监控
                logger.info("📧 只注册邮箱模式，开始监控邮件...")
                monitor_emails(dropmail, logger, check_interval=10)
                return  # 只监控邮件，不进行 AWS Builder ID 注册
                
        elif not email:
            logger.error("❌ 必须提供邮箱地址或启用临时邮箱")
            raise typer.Exit(1)
        
        # 步骤2: 初始化注册器
        logger.info("🔧 初始化 AWS Builder 注册器...")
        current_browser = AWSBuilder(
            headless=headless,
            timeout=timeout,
            debug=debug,
            keep_browser=True,  # 保持浏览器打开
            browser_type=browser
        )
        logger.info("✓ 注册器初始化完成")
        
        # 步骤3: 显示注册信息
        logger.info("📋 注册信息:")
        logger.info("-" * 40)
        logger.info(f"邮箱: {email}")
        logger.info(f"姓名: {name}")
        logger.info(f"浏览器: {browser}")
        logger.info(f"无头模式: {headless}")
        logger.info(f"等待时间: {wait_minutes}分钟")
        logger.info("-" * 40)
        
        # 步骤4: 执行自动注册（到图形验证码前）
        logger.info("🎯 开始自动注册流程...")
        
        # 修改注册流程，在图形验证码前停止
        result = current_browser.register_aws_builder_until_captcha(
            email=email,
            name=name,
            password=password,
            dropmail=dropmail
        )
        
        if not result:
            logger.error("❌ 自动注册流程失败")
            raise typer.Exit(1)
        
        # 保存注册数据
        registration_data = result
        cache_path = Path(cache_file)
        save_registration_data(
            email=result.email,
            password=result.password,
            name=result.name,
            cache_file=cache_path,
            logger=logger
        )
        
        # 步骤5: 显示结果并等待用户操作
        logger.info("🎉 自动注册流程完成！")
        logger.info("=" * 60)
        logger.info("📊 注册信息:")
        logger.info(f"✓ 邮箱: {result.email}")
        logger.info(f"✓ 密码: {result.password}")
        logger.info(f"✓ 姓名: {result.name}")
        logger.info("=" * 60)
        
        logger.info("⚠️  请在浏览器中手动完成图形验证码")
        
        # 等待用户操作
        wait_for_user_action(wait_minutes, logger)
        
    except KeyboardInterrupt:
        logger.info("⚠️  用户中断操作")
    except Exception as e:
        logger.error(f"❌ 发生错误: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        raise typer.Exit(1)
    finally:
        # 清理资源
        logger.info("🧹 清理资源...")
        if current_browser:
            try:
                current_browser.close()
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")
        logger.info("✓ 程序结束")


@app.command()
def sessions(
    dropmail_cache: Annotated[str, typer.Option(
        "--cache-file", "-c",
        help="📁 DropMail Session 缓存文件路径"
    )] = ".cache/dropmail_sessions.json",
    
    cleanup: Annotated[bool, typer.Option(
        "--cleanup",
        help="🧹 清理过期的 Sessions"
    )] = False,
    
    restore: Annotated[bool, typer.Option(
        "--restore", "-r",
        help="🔄 显示可恢复的 Sessions 列表供选择并监控邮件"
    )] = False,
    
    monitor: Annotated[Optional[str], typer.Option(
        "--monitor", "-m",
        help="📧 监控指定 Session ID 的邮件"
    )] = None
):
    """
    管理 DropMail Sessions
    
    显示、清理、恢复和监控 DropMail Sessions。
    
    [bold yellow]使用示例:[/bold yellow]
    
    # 显示所有 Sessions
    auto-register-aws-builder sessions
    
    # 清理过期的 Sessions
    auto-register-aws-builder sessions --cleanup
    
    # 恢复 Session 并监控邮件
    auto-register-aws-builder sessions --restore
    
    # 监控指定 Session 的邮件
    auto-register-aws-builder sessions --monitor SESSION_ID
    """
    dropmail = DropMail(cache_file=dropmail_cache)
    logger = setup_logging(False)
    
    if restore:
        # 显示 Session 列表供用户选择并监控
        logger.info("🔄 恢复 DropMail Session")
        
        selected_session_id = select_session_from_list(dropmail, logger)
        if not selected_session_id:
            logger.info("❌ 未选择 Session，程序退出")
            raise typer.Exit(0)
        
        if dropmail.restore_session(selected_session_id):
            email = dropmail.addresses[0].address if dropmail.addresses else None
            if email:
                logger.info(f"✓ 成功恢复邮箱: {email}")
                logger.info(f"✓ Session ID: {selected_session_id}")
                
                # 开始监控邮件
                monitor_emails(dropmail, logger, check_interval=10)
                return
            else:
                logger.error("❌ 恢复的 Session 中没有找到邮箱地址")
                raise typer.Exit(1)
        else:
            logger.error(f"❌ 无法恢复 Session: {selected_session_id}")
            raise typer.Exit(1)
    
    if monitor:
        # 监控指定 Session 的邮件
        if dropmail.restore_session(monitor):
            logger.info(f"✓ 成功恢复 Session: {monitor}")
            monitor_emails(dropmail, logger, check_interval=10)
        else:
            logger.error(f"❌ 无法恢复 Session: {monitor}")
            raise typer.Exit(1)
        return
    
    if cleanup:
        # 清理过期的 Sessions
        logger.info("🧹 清理过期的 Sessions...")
        expired_count = dropmail.cleanup_expired_sessions()
        logger.info(f"✓ 已清理 {expired_count} 个过期的 Sessions")
    
    # 显示所有 Sessions
    sessions_list = dropmail.list_cached_sessions()
    
    if not sessions_list:
        typer.echo("📭 没有找到任何 Sessions")
        return
    
    typer.echo(f"📋 共找到 {len(sessions_list)} 个 Sessions:")
    typer.echo("=" * 80)
    
    for i, session_cache in enumerate(sessions_list, 1):
        # 格式化时间显示
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
        
        # 验证 Session 是否有效
        old_token = dropmail.auth_token
        old_session = dropmail.session_id
        
        dropmail.auth_token = session_cache.auth_token
        dropmail.session_id = session_cache.session_id
        
        is_valid = dropmail._verify_session()
        status = "✓ 有效" if is_valid else "❌ 无效"
        
        # 恢复原来的设置
        dropmail.auth_token = old_token
        dropmail.session_id = old_session
        
        typer.echo(f"{i}. 邮箱: {session_cache.email_address}")
        typer.echo(f"   Session ID: {session_cache.session_id}")
        typer.echo(f"   状态: {status}")
        typer.echo(f"   创建时间: {created_time}")
        typer.echo(f"   最后访问: {last_accessed}")
        typer.echo("-" * 40)


@app.command()
def list_records(
    cache_file: Annotated[str, typer.Option(
        "--cache-file", "-c",
        help="💾 注册数据缓存文件路径"
    )] = ".cache/auto_register_aws_builder.csv",
    
    limit: Annotated[int, typer.Option(
        "--limit", "-l",
        help="📊 显示记录数量限制",
        min=1, max=100
    )] = 10
):
    """
    列出最近的注册记录
    
    显示保存在缓存文件中的注册记录，包括时间戳、邮箱、密码等信息。
    """
    cache_path = Path(cache_file)
    
    if not cache_path.exists():
        typer.echo("❌ 缓存文件不存在")
        raise typer.Exit(1)
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            records = list(reader)
        
        if not records:
            typer.echo("📝 暂无注册记录")
            return
        
        # 显示最近的记录
        recent_records = records[-limit:]
        
        typer.echo(f"📋 最近 {len(recent_records)} 条注册记录:")
        typer.echo("=" * 80)
        
        for i, record in enumerate(recent_records, 1):
            timestamp = record.get('timestamp', 'N/A')
            email = record.get('email', 'N/A')
            password = record.get('password', 'N/A')
            name = record.get('name', 'N/A')
            status = record.get('status', 'N/A')
            
            typer.echo(f"{i}. 时间: {timestamp}")
            typer.echo(f"   邮箱: {email}")
            typer.echo(f"   密码: {password}")
            typer.echo(f"   姓名: {name}")
            typer.echo(f"   状态: {status}")
            typer.echo("-" * 40)
            
    except Exception as e:
        typer.echo(f"❌ 读取缓存文件失败: {e}")
        raise typer.Exit(1)


@app.command()
def version():
    """显示版本信息"""
    typer.echo("auto-register-aws-builder v0.1.0")
    typer.echo("AWS Builder ID 自动注册工具")


if __name__ == "__main__":
    app()
