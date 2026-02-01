#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili收藏夹同步主程序

该脚本实现了完整的收藏夹同步工作流，包括：
1. 获取收藏夹视频列表
2. 检查历史同步记录
3. 筛选待同步视频
4. 批量获取视频信息
5. 保存为Markdown文件
6. 更新同步记录

使用示例:
    python main.py 3656879060
    python main.py 3656879060 --cookie custom_cookie.txt
    python main.py 3656879060 --output-dir custom_output
"""

import sys
import os
import configparser
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 导入模块化工具
from src.get_favorite import get_favorite_info
from src.get_bv_info import BVInfoExtractor
from src.data_sync import DataSyncManager


def sync_workflow(
    media_id: int,
    cookie_path: Optional[str] = None,
    output_dir: str = "output/markdown",
    reformat: bool = False,
    api_key: str = None,
    step5_max_workers: int = 2,
    llm_timeout_sec: int = 40,
    max_original_subtitle_chars: int = 8000,
    max_video_duration_sec: int = 1800,
) -> bool:
    """
    执行完整的收藏夹同步工作流

    Args:
        media_id: 收藏夹的media_id
        cookie_path: cookie文件路径，可选
        output_dir: 输出目录路径
        reformat: 是否重新排版
        api_key: GLM API密钥
    Returns:
        同步是否成功
    """
    print(f"开始同步收藏夹 {media_id}")
    print("=" * 50)

    try:
        # 步骤1: 获取收藏夹视频列表
        print("步骤1: 获取收藏夹视频列表...")
        result = get_favorite_info(media_id, cookie_path)
        if result is None:
            print("❌ 获取收藏夹信息失败")
            return False

        bvids, fav_data = result
        print(f"✓ 获取到 {len(bvids)} 个视频")

        # 步骤2: 检查历史同步记录
        print("\n步骤2: 检查历史同步记录...")
        sync_manager = DataSyncManager(
            output_dir=output_dir,
            reformat=reformat,
            api_key=api_key,
            step5_max_workers=step5_max_workers,
            llm_timeout_sec=llm_timeout_sec,
            max_original_subtitle_chars=max_original_subtitle_chars,
            max_video_duration_sec=max_video_duration_sec,
        )
        synced_bvs = sync_manager.load_sync_record(media_id)

        # 步骤3: 筛选待同步视频
        print("\n步骤3: 筛选待同步视频...")
        if synced_bvs:
            # 存在历史记录，进行差量同步
            target_bvs = sync_manager.compare_and_filter(bvids, synced_bvs)
            if not target_bvs:
                print("✓ 没有新的视频需要同步")
                return True
        else:
            # 不存在历史记录，同步全部视频
            target_bvs = bvids
            print(f"✓ 首次同步，将同步全部 {len(target_bvs)} 个视频")

        # 步骤4: 批量获取视频详细信息
        print(f"\n步骤4: 批量获取 {len(target_bvs)} 个视频的详细信息...")
        extractor = BVInfoExtractor(cookie_path=cookie_path)
        video_info_list = extractor.get_batch_video_info(target_bvs, delay=1.0)

        # 筛选成功获取信息的视频
        successful_videos = [video for video in video_info_list if video.get('success', False)]
        if not successful_videos:
            print("❌ 没有成功获取到任何视频信息")
            return False

        print(f"✓ 成功获取 {len(successful_videos)} 个视频的信息")

        # 保存视频信息到临时JSON文件（供data_sync模块使用）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as temp_file:
            json.dump(successful_videos, temp_file, ensure_ascii=False, indent=2)
            temp_json_path = temp_file.name

        try:
            # 步骤5: 保存为Markdown文件
            print(f"\n步骤5: 保存 {len(successful_videos)} 个视频为Markdown文件...")
            success_count = 0
            for video_info in successful_videos:
                if sync_manager.save_to_markdown(video_info):
                    success_count += 1

            print(f"✓ 成功保存 {success_count}/{len(successful_videos)} 个Markdown文件")

            # 步骤6: 更新同步记录
            print("\n步骤6: 更新同步记录...")
            all_synced_bvs = list(set(bvids))  # 所有当前视频都算作已同步
            if sync_manager.update_sync_record(media_id, all_synced_bvs):
                print("✓ 同步记录更新成功")
            else:
                print("⚠ 同步完成，但更新记录失败")

            return success_count > 0

        finally:
            # 清理临时文件
            try:
                os.unlink(temp_json_path)
            except:
                pass

    except Exception as e:
        print(f"❌ 同步过程中发生错误: {str(e)}")
        return False


def load_config():
    """从config/dev.ini加载配置参数"""
    config = configparser.ConfigParser()
    config_file = os.path.join(os.path.dirname(__file__), 'config', 'dev.ini')

    if not os.path.exists(config_file):
        print(f"❌ 错误：配置文件不存在: {config_file}")
        sys.exit(1)

    try:
        config.read(config_file, encoding='utf-8')

        # 从Sync Parameters section读取参数
        sync_params = config['Sync Parameters']

        media_id = sync_params.get('MEDIA_ID')
        cookie_path = sync_params.get('COOKIE_PATH')
        output_dir = sync_params.get('OUTPUT_DIR')

        llm_params = config['LLM Parameters for GLM']
        reformat = True if llm_params.get('REFORMAT') == 'True' else False
        api_key = llm_params.get('API_KEY')
        step5_max_workers = llm_params.getint('STEP5_MAX_WORKERS', fallback=2)
        llm_timeout_sec = llm_params.getint('LLM_TIMEOUT_SEC', fallback=40)
        max_original_subtitle_chars = llm_params.getint('MAX_ORIGINAL_SUBTITLE_CHARS', fallback=8000)
        max_video_duration_sec = llm_params.getint('MAX_VIDEO_DURATION_SEC', fallback=1800)

        # 处理MEDIA_ID字符串格式（去除引号）
        if media_id and media_id.startswith('"') and media_id.endswith('"'):
            media_id = media_id[1:-1]

        # 处理COOKIE_PATH字符串格式（去除引号）
        if cookie_path and cookie_path.startswith('"') and cookie_path.endswith('"'):
            cookie_path = cookie_path[1:-1]

        # 如果cookie_path是默认值或空字符串，则设置为None以使用默认路径
        if not cookie_path or cookie_path == "qr_login.txt":
            cookie_path = None

        # 处理OUTPUT_DIR字符串格式（去除引号）
        if output_dir and output_dir.startswith('"') and output_dir.endswith('"'):
            output_dir = output_dir[1:-1]

        # 转换media_id为整数
        try:
            media_id = int(media_id)
        except (ValueError, TypeError):
            print(f"❌ 错误：无效的MEDIA_ID格式: {media_id}")
            sys.exit(1)

        return (
            media_id,
            cookie_path,
            output_dir,
            reformat,
            api_key,
            step5_max_workers,
            llm_timeout_sec,
            max_original_subtitle_chars,
            max_video_duration_sec,
        )

    except Exception as e:
        print(f"❌ 错误：读取配置文件失败: {str(e)}")
        sys.exit(1)


def main():
    """主函数"""
    # 从配置文件加载参数
    (
        media_id,
        cookie_path,
        output_dir,
        reformat,
        api_key,
        step5_max_workers,
        llm_timeout_sec,
        max_original_subtitle_chars,
        max_video_duration_sec,
    ) = load_config()

    # 检查cookie文件（如果指定）
    if cookie_path and cookie_path != "qr_login.txt" and not os.path.exists(cookie_path):
        print(f"❌ 错误：指定的cookie文件不存在: {cookie_path}")
        sys.exit(1)

    # 显示配置信息
    print("Bilibili收藏夹同步工具")
    print("=" * 50)
    print(f"收藏夹ID: {media_id}")
    print(f"Cookie文件: {cookie_path or '使用默认路径'}")
    print(f"输出目录: {output_dir}")
    print("=" * 50)

    # 确保输出目录存在
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 执行同步工作流
    success = sync_workflow(
        media_id,
        cookie_path,
        output_dir,
        reformat,
        api_key,
        step5_max_workers,
        llm_timeout_sec,
        max_original_subtitle_chars,
        max_video_duration_sec,
    )

    print("\n" + "=" * 50)
    if success:
        print("✅ 同步操作成功完成!")
        sys.exit(0)
    else:
        print("❌ 同步操作失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
