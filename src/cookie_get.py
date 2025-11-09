#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站Cookie获取工具
通过二维码登录获取必要的cookie文件
支持自定义cookie保存路径
"""

import sys
import os
import argparse
import time
from Tools.bili_tools import biliLogin
from Tools.util.Colorful_Console import ColoredText as CT


def create_directory_if_not_exists(path):
    """
    如果目录不存在则创建

    Args:
        path (str): 目录路径
    """
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            print(f"{CT('已创建目录: ').green()}{path}")
        except Exception as e:
            print(f"{CT('创建目录失败: ').red()}{str(e)}")
            return False
    return True


def login_with_qr(save_path="cookie", save_name="qr_login", full_path=None, img_show=True):
    """
    通过二维码登录获取cookie

    Args:
        save_path (str): 保存路径
        save_name (str): 保存文件名
        full_path (str): 完整路径（可选）
        img_show (bool): 是否显示二维码图片

    Returns:
        bool: 登录是否成功
    """
    try:
        print(f"{CT('B站二维码登录工具').blue()}")
        print(f"{CT('=' * 50).blue()}")

        # 创建biliLogin实例
        bili_login = biliLogin()

        print(f"{CT('正在生成二维码...').yellow()}")

        # 执行二维码登录
        success = bili_login.qr_login(
            save_path=save_path,
            save_name=save_name,
            full_path=full_path,
            img_show=img_show
        )

        if success:
            print(f"{CT('登录成功！').green()}")

            # 确定最终保存的cookie文件路径
            if full_path:
                cookie_file = full_path
            else:
                cookie_file = os.path.join(save_path, f"{save_name}.txt")

            print(f"{CT('Cookie已保存到: ').green()}{cookie_file}")

            # 验证登录状态
            headers = {
                "User-Agent": bili_login.headers["User-Agent"],
                "Cookie": open(cookie_file, 'r').read(),
                'referer': "https://www.bilibili.com"
            }

            verify_login = biliLogin(headers)
            login_info = verify_login.get_login_state()

            if login_info["data"]["isLogin"]:
                print(f"{CT('登录验证成功！').green()}")
                print(f"{CT('用户信息:').yellow()}")
                print(f"  用户名: {login_info['data']['uname']}")
                print(f"  用户ID: {login_info['data']['mid']}")
                print(f"  等级: {login_info['data']['level_info']['current_level']}")
                return True
            else:
                print(f"{CT('警告: 登录验证失败，但cookie已保存').red()}")
                return False
        else:
            print(f"{CT('登录失败，请重试').red()}")
            return False

    except Exception as e:
        print(f"{CT('登录过程中发生错误: ').red()}{str(e)}")
        return False


def verify_cookie(cookie_file):
    """
    验证现有的cookie文件是否有效

    Args:
        cookie_file (str): cookie文件路径

    Returns:
        bool: cookie是否有效
    """
    try:
        if not os.path.exists(cookie_file):
            print(f"{CT('Cookie文件不存在: ').red()}{cookie_file}")
            return False

        # 读取cookie
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookie_content = f.read().strip()

        if not cookie_content:
            print(f"{CT('Cookie文件为空: ').red()}{cookie_file}")
            return False

        # 创建headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
            "Cookie": cookie_content,
            'referer': "https://www.bilibili.com"
        }

        # 验证登录状态
        bili_login = biliLogin(headers)
        login_info = bili_login.get_login_state()

        if login_info["data"]["isLogin"]:
            print(f"{CT('Cookie有效！').green()}")
            print(f"{CT('用户信息:').yellow()}")
            print(f"  用户名: {login_info['data']['uname']}")
            print(f"  用户ID: {login_info['data']['mid']}")
            print(f"  等级: {login_info['data']['level_info']['current_level']}")
            return True
        else:
            print(f"{CT('Cookie无效或已过期').red()}")
            return False

    except Exception as e:
        print(f"{CT('验证cookie时发生错误: ').red()}{str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='B站Cookie获取工具 - 通过二维码登录获取必要的cookie文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python cookie_get.py                                    # 使用默认设置登录
  python cookie_get.py --path custom_cookie              # 自定义保存路径
  python cookie_get.py --file my_cookies.txt             # 自定义文件名
  python cookie_get.py --full-path cookies/my.txt        # 指定完整路径
  python cookie_get.py --no-show                         # 不显示二维码图片
  python cookie_get.py --verify cookie/qr_login.txt      # 验证现有cookie
        """
    )

    # 登录相关参数
    parser.add_argument('--path', type=str, default='cookie', metavar='PATH',
                       help='cookie保存目录 (默认: cookie)')
    parser.add_argument('--file', type=str, default='qr_login', metavar='FILENAME',
                       help='cookie文件名 (默认: qr_login)')
    parser.add_argument('--full-path', type=str, metavar='PATH',
                       help='完整的cookie文件路径 (覆盖--path和--file)')
    parser.add_argument('--no-show', action='store_true',
                       help='不自动显示二维码图片')

    # 验证相关参数
    parser.add_argument('--verify', type=str, metavar='COOKIE_FILE',
                       help='验证指定的cookie文件是否有效')

    args = parser.parse_args()

    # 验证模式
    if args.verify:
        print(f"{CT('B站Cookie验证工具').blue()}")
        print(f"{CT('=' * 50).blue()}")
        success = verify_cookie(args.verify)
        sys.exit(0 if success else 1)

    # 登录模式
    print(f"{CT('B站Cookie获取工具').blue()}")
    print(f"{CT('=' * 50).blue()}")

    # 创建保存目录
    if not args.full_path:
        if not create_directory_if_not_exists(args.path):
            sys.exit(1)

    print(f"{CT('准备开始二维码登录...').yellow()}")
    print(f"{CT('请确保您的手机上已安装B站APP').yellow()}")
    print(f"{CT('将要打开二维码，请使用B站APP扫描').yellow()}")

    # 等待用户确认
    try:
        input(f"{CT('按回车键继续，或按 Ctrl+C 退出: ').blue()}")
    except KeyboardInterrupt:
        print(f"\n{CT('用户取消操作').yellow()}")
        sys.exit(0)

    # 执行登录
    success = login_with_qr(
        save_path=args.path,
        save_name=args.file,
        full_path=args.full_path,
        img_show=not args.no_show
    )

    if success:
        print(f"\n{CT('🎉 Cookie获取成功！现在可以使用其他工具了').green()}")
        print(f"{CT('例如: python get_favorite.py 1234567890').blue()}")
        sys.exit(0)
    else:
        print(f"\n{CT('❌ Cookie获取失败').red()}")
        print(f"{CT('请检查网络连接或重试').yellow()}")
        sys.exit(1)


if __name__ == '__main__':
    main()