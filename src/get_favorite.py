#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取B站指定收藏夹的信息
使用 biliFav 中的 get_fav_bv 函数获取收藏夹中的视频列表
该脚本独立运行，不涉及UI功能
"""

import sys
import os
import argparse
from Tools.bili_tools import biliFav
from Tools.util.Colorful_Console import ColoredText as CT


def get_favorite_info(media_id, cookie_path=None):
    """
    获取指定收藏夹的信息

    Args:
        media_id (int): 收藏夹的media_id
        cookie_path (str, optional): cookie文件路径。默认为None，使用默认路径

    Returns:
        list: 收藏夹中的BV号列表，失败时返回None
    """
    try:
        # 创建biliFav实例
        bili_fav = biliFav()

        # 获取收藏夹中的BV号列表
        print(f"{CT('正在获取收藏夹信息...').blue()}")
        print(f"{CT('收藏夹ID: ').green()}{media_id}")

        bvids, fav_data = bili_fav.get_fav_bv(media_id)

        if bvids is None:
            print(f"{CT('获取收藏夹信息失败').red()}")
            return None

        print(f"{CT('获取成功！收藏夹中共有 ').green()}{len(bvids)}{CT(' 个视频').green()}")
        return bvids, fav_data

    except Exception as e:
        print(f"{CT('发生错误: ').red()}{str(e)}")
        return None


def display_favorite_info(bvids, show_details=False):
    """
    显示收藏夹信息

    Args:
        bvids (list): BV号列表
        show_details (bool): 是否显示详细信息
    """
    if not bvids:
        print(f"{CT('收藏夹为空或获取失败').yellow()}")
        return

    print(f"\n{CT('=== 收藏夹视频列表 ===').blue()}")
    print(f"{CT('总计: ').green()}{len(bvids)}{CT(' 个视频').green()}")

    if show_details:
        print(f"\n{CT('视频详情:').yellow()}")
        for i, bvid in enumerate(bvids, 1):
            print(f"{i:3d}. {bvid}")
    else:
        # 简略显示，每行显示5个
        print(f"\n{CT('视频列表 (每行5个):').yellow()}")
        for i in range(0, len(bvids), 5):
            batch = bvids[i:i+5]
            print("  ".join(f"{bv:15}" for bv in batch))


def save_to_file(bvids, filename):
    """
    将BV号列表保存到文件

    Args:
        bvids (list): BV号列表
        filename (str): 保存的文件名
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# 收藏夹视频列表\n")
            f.write(f"# 总计: {len(bvids)} 个视频\n\n")
            for bvid in bvids:
                f.write(f"{bvid}\n")
        print(f"{CT('结果已保存到: ').green()}{filename}")
    except Exception as e:
        print(f"{CT('保存文件失败: ').red()}{str(e)}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='获取B站指定收藏夹的信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python get_favorite.py 1234567890                    # 获取收藏夹ID为1234567890的信息
  python get_favorite.py 1234567890 -d                 # 显示详细信息
  python get_favorite.py 1234567890 -o favorite.txt    # 保存到文件
  python get_favorite.py 1234567890 -d -o favorite.txt # 显示详细信息并保存到文件
        """
    )

    parser.add_argument('media_id', type=int, help='收藏夹的media_id')
    parser.add_argument('-d', '--details', action='store_true',
                       help='显示详细信息（列出所有BV号）')
    parser.add_argument('-o', '--output', type=str, metavar='FILENAME',
                       help='将结果保存到指定文件')
    parser.add_argument('-c', '--cookie', type=str, metavar='PATH',
                       help='指定cookie文件路径（可选）')

    args = parser.parse_args()

    print(f"{CT('B站收藏夹信息获取工具').blue()}")
    print(f"{CT('=' * 50).blue()}")

    # 获取收藏夹信息
    bvids, fav_data = get_favorite_info(args.media_id, args.cookie)

    if bvids is not None:
        # 显示信息
        display_favorite_info(bvids, args.details)
        print(fav_data)

        # 保存到文件
        if args.output:
            save_to_file(bvids, args.output)

        print(f"\n{CT('操作完成！').green()}")
    else:
        print(f"\n{CT('获取收藏夹信息失败，请检查:').red()}")
        print(f"  1. 收藏夹ID是否正确")
        print(f"  2. cookie文件是否存在且有效")
        print(f"  3. 网络连接是否正常")
        sys.exit(1)


if __name__ == '__main__':
    main()

'''
uv run get_favorite.py 3656879060 -o favorite.txt
'''