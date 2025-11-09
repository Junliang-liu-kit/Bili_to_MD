#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取BV视频信息脚本

该脚本利用biliVideo类获取指定BV号的所有基本属性和视频信息，
支持单个BV号和多个BV号批量获取，结果以JSON格式保存到output文件夹。

使用示例:
    # 获取单个视频信息
    python get_bv_info.py BV1ov42117yC

    # 获取多个视频信息
    python get_bv_info.py BV1ov42117yC BV1YS421d7Yx BV1Z1421k7nC

    # 从文件中读取BV号列表
    python get_bv_info.py --file bv_list.txt
"""

import sys
import json
import os
import time
import random
from datetime import datetime
from typing import List, Dict, Union, Optional

# 导入biliVideo类
from Tools.bili_tools import biliVideo


class BVInfoExtractor:
    """BV视频信息提取器"""

    def __init__(self, cookie_path: Optional[str] = None):
        """
        初始化信息提取器

        Args:
            cookie_path: cookie文件路径，默认为None使用默认路径
        """
        self.cookie_path = cookie_path
        self.results = []

    def get_single_video_info(self, bv_id: str) -> Dict:
        """
        获取单个视频的完整信息

        Args:
            bv_id: BV号

        Returns:
            包含视频信息的字典
        """
        print(f"正在获取 {bv_id} 的信息...")

        try:
            # 创建biliVideo实例
            video = biliVideo(bv=bv_id, cookie_path=self.cookie_path)

            # 获取视频基本信息
            video.get_content(stat=True, tag=True, up=True)

            # 获取用户互动信息（需要登录）
            try:
                video.get_user_action()
            except Exception as e:
                print(f"获取 {bv_id} 用户互动信息失败: {e}")
                # 设置默认值
                video.user_like = None
                video.user_coin = None
                video.user_fav = None

            # 构建信息字典
            video_info = {
                # 基本信息
                "bv": video.bv,
                "av": video.av,
                "cid": video.cid,
                "url_bv": video.url_bv,

                # 视频信息
                "title": video.title,
                "pic": video.pic,
                "desc": video.desc,
                "time": video.time,
                "tid": video.tid,
                "tname": video.tname,

                # 统计数据
                "stat": video.stat,
                "view": video.view,
                "dm": video.dm,
                "reply": video.reply,
                "like": video.like,
                "coin": video.coin,
                "fav": video.fav,
                "share": video.share,

                # 标签信息
                "tag": video.tag,

                # UP主信息
                "up": video.up,
                "up_mid": video.up_mid,
                "up_follow": video.up_follow,
                "up_followers": video.up_followers,

                # 用户互动信息
                "user_like": video.user_like,
                "user_coin": video.user_coin,
                "user_fav": video.user_fav,

                # 获取时间
                "fetch_time": datetime.now().isoformat(),

                # 状态信息
                "success": True,
                "error": None
            }

            print(f"✓ {bv_id} 信息获取成功: {video.title}")
            return video_info

        except Exception as e:
            error_info = {
                "bv": bv_id,
                "success": False,
                "error": str(e),
                "fetch_time": datetime.now().isoformat()
            }
            print(f"✗ {bv_id} 信息获取失败: {e}")
            return error_info

    def get_batch_video_info(self, bv_list: List[str], delay: float = 1.0) -> List[Dict]:
        """
        批量获取视频信息

        Args:
            bv_list: BV号列表
            delay: 请求间隔时间（秒），默认为1秒

        Returns:
            视频信息列表
        """
        results = []
        total = len(bv_list)

        print(f"开始批量获取 {total} 个视频的信息...")

        for i, bv_id in enumerate(bv_list, 1):
            print(f"[{i}/{total}] ", end="")

            # 获取单个视频信息
            video_info = self.get_single_video_info(bv_id)
            results.append(video_info)

            # 添加随机延迟避免请求过快
            if i < total:  # 最后一个不需要延迟
                sleep_time = delay + random.uniform(0, 0.5)
                time.sleep(sleep_time)

        print(f"批量获取完成，成功: {sum(1 for r in results if r.get('success', False))}，"
              f"失败: {sum(1 for r in results if not r.get('success', True))}")

        return results

    def save_results_to_json(self, results: List[Dict], filename: str = None) -> str:
        """
        将结果保存为JSON文件

        Args:
            results: 视频信息列表
            filename: 文件名，如果为None则自动生成

        Returns:
            保存的文件路径
        """
        # 确保output文件夹存在
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bv_info_{timestamp}.json"

        if not filename.endswith('.json'):
            filename += '.json'

        file_path = os.path.join(output_dir, filename)

        # 保存结果
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"结果已保存到: {file_path}")
        return file_path

    def read_bv_list_from_file(self, file_path: str) -> List[str]:
        """
        从文件中读取BV号列表

        Args:
            file_path: 文件路径

        Returns:
            BV号列表
        """
        bv_list = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and line.startswith('BV'):
                        bv_list.append(line)

            print(f"从文件 {file_path} 中读取到 {len(bv_list)} 个BV号")
            return bv_list

        except Exception as e:
            print(f"读取文件失败: {e}")
            return []


def main():
    """主函数"""

    # 创建信息提取器
    extractor = BVInfoExtractor()

    # 解析命令行参数
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python get_bv_info.py BV1ov42117yC")
        print("  python get_bv_info.py BV1ov42117yC BV1YS421d7Yx")
        print("  python get_bv_info.py --file bv_list.txt")
        print("  python get_bv_info.py --cookie cookie/qr_login.txt BV1ov42117yC")
        sys.exit(1)

    bv_list = []
    cookie_path = None
    output_filename = None

    # 解析参数
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '--file':
            if i + 1 < len(sys.argv):
                file_path = sys.argv[i + 1]
                bv_list = extractor.read_bv_list_from_file(file_path)
                i += 2
            else:
                print("--file 参数需要指定文件路径")
                sys.exit(1)
        elif arg == '--cookie':
            if i + 1 < len(sys.argv):
                cookie_path = sys.argv[i + 1]
                extractor.cookie_path = cookie_path
                i += 2
            else:
                print("--cookie 参数需要指定cookie路径")
                sys.exit(1)
        elif arg == '--output':
            if i + 1 < len(sys.argv):
                output_filename = sys.argv[i + 1]
                i += 2
            else:
                print("--output 参数需要指定输出文件名")
                sys.exit(1)
        else:
            # 直接的BV号参数
            if arg.startswith('BV'):
                bv_list.append(arg)
            else:
                print(f"无效的BV号: {arg}")
            i += 1

    if not bv_list:
        print("未指定有效的BV号")
        sys.exit(1)

    # 设置cookie路径
    if cookie_path:
        extractor.cookie_path = cookie_path

    print(f"准备获取 {len(bv_list)} 个视频的信息")
    print(f"Cookie路径: {extractor.cookie_path or '默认路径'}")
    print("-" * 50)

    # 获取视频信息
    if len(bv_list) == 1:
        # 单个视频
        results = [extractor.get_single_video_info(bv_list[0])]
    else:
        # 批量获取
        results = extractor.get_batch_video_info(bv_list, delay=1.0)

    # 保存结果
    output_path = extractor.save_results_to_json(results, output_filename)

    # 输出统计信息
    success_count = sum(1 for r in results if r.get('success', False))
    fail_count = len(results) - success_count

    print("-" * 50)
    print(f"处理完成!")
    print(f"总计: {len(results)} 个视频")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print(f"结果已保存到: {output_path}")


if __name__ == "__main__":
    main()