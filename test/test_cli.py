#!/usr/bin/env python3
"""
命令行接口测试脚本
测试 auto-register-aws-builder 命令行工具
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_help_command():
    """测试帮助命令"""
    print("🧪 测试帮助命令...")
    
    try:
        # 测试主帮助
        result = subprocess.run([
            sys.executable, "-m", "auto_update_q.auto_register", "--help"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + "/..")
        
        print(f"返回码: {result.returncode}")
        print(f"输出长度: {len(result.stdout)} 字符")
        
        if result.returncode == 0:
            print("✅ 主帮助命令测试通过")
            # 检查关键词
            if "AWS Builder ID" in result.stdout and "register" in result.stdout:
                print("✅ 帮助内容包含预期关键词")
            else:
                print("⚠️  帮助内容可能不完整")
        else:
            print(f"❌ 主帮助命令失败: {result.stderr}")
        
        # 测试 register 子命令帮助
        result = subprocess.run([
            sys.executable, "-m", "auto_update_q.auto_register", "register", "--help"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + "/..")
        
        if result.returncode == 0:
            print("✅ register 帮助命令测试通过")
        else:
            print(f"❌ register 帮助命令失败: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 测试帮助命令时出错: {e}")


def test_version_command():
    """测试版本命令"""
    print("\n🧪 测试版本命令...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "auto_update_q.auto_register", "version"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + "/..")
        
        print(f"返回码: {result.returncode}")
        print(f"输出: {result.stdout.strip()}")
        
        if result.returncode == 0:
            print("✅ 版本命令测试通过")
            if "auto-register-aws-builder" in result.stdout:
                print("✅ 版本信息包含程序名称")
        else:
            print(f"❌ 版本命令失败: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 测试版本命令时出错: {e}")


def test_list_records_command():
    """测试列出记录命令"""
    print("\n🧪 测试列出记录命令...")
    
    try:
        # 创建临时缓存文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("timestamp,email,password,name,status\n")
            f.write("2025-01-01T00:00:00,test@example.com,TestPass123,Test User,pending_captcha\n")
            temp_cache = f.name
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "auto_update_q.auto_register", "list-records",
                "--cache-file", temp_cache
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__) + "/..")
            
            print(f"返回码: {result.returncode}")
            
            if result.returncode == 0:
                print("✅ 列出记录命令测试通过")
                if "test@example.com" in result.stdout:
                    print("✅ 记录内容正确显示")
            else:
                print(f"❌ 列出记录命令失败: {result.stderr}")
        finally:
            # 清理临时文件
            os.unlink(temp_cache)
            
    except Exception as e:
        print(f"❌ 测试列出记录命令时出错: {e}")


def test_register_command_dry_run():
    """测试注册命令（模拟运行）"""
    print("\n🧪 测试注册命令参数验证...")
    
    try:
        # 测试无效浏览器类型
        result = subprocess.run([
            sys.executable, "-m", "auto_update_q.auto_register", "register",
            "--browser", "invalid_browser",
            "--no-temp-email",
            "--email", "test@example.com"
        ], capture_output=True, text=True, timeout=10, 
        cwd=os.path.dirname(__file__) + "/..")
        
        print(f"无效浏览器测试返回码: {result.returncode}")
        
        # 测试参数解析（不实际运行注册）
        # 这里只测试命令行参数是否能正确解析，不会实际启动浏览器
        
    except subprocess.TimeoutExpired:
        print("⚠️  命令超时（预期行为，因为会尝试启动浏览器）")
    except Exception as e:
        print(f"❌ 测试注册命令时出错: {e}")


def main():
    """主测试函数"""
    print("🚀 开始命令行接口测试")
    print("=" * 50)
    
    # 检查项目结构
    project_root = Path(__file__).parent.parent
    auto_register_path = project_root / "src" / "auto_update_q" / "auto_register.py"
    
    if not auto_register_path.exists():
        print(f"❌ 找不到 auto_register.py: {auto_register_path}")
        return
    
    print(f"✅ 找到 auto_register.py: {auto_register_path}")
    
    # 运行测试
    test_help_command()
    test_version_command()
    test_list_records_command()
    test_register_command_dry_run()
    
    print("\n" + "=" * 50)
    print("🏁 命令行接口测试完成")
    print("\n💡 提示:")
    print("- 完整的注册测试需要手动运行，因为涉及浏览器交互")
    print("- 使用 'uv run auto-register-aws-builder register --help' 查看完整选项")


if __name__ == "__main__":
    main()
