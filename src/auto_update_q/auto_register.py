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
    
    [bold yellow]使用示例:[/bold yellow]
    
    # 使用默认设置自动注册
    auto-register-aws-builder register
    
    # 指定邮箱和姓名
    auto-register-aws-builder register --email test@example.com --name "John Doe"
    
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
        if not email and not no_temp_email:
            logger.info("📧 创建临时邮箱...")
            dropmail = DropMail()
            email = dropmail.get_temp_email()
            logger.info(f"✓ 临时邮箱: {email}")
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
