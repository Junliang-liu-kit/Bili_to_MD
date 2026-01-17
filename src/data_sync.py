#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili收藏夹数据同步和转换工具

该脚本用于将收藏夹视频信息从JSON格式转换为Markdown格式，并支持增量同步功能。
主要功能：
1. 从原始JSON数据中提取视频列表
2. 读取历史同步记录，实现增量同步
3. 筛选核心信息字段并转换时间戳
4. 按格式存储为Markdown文件
5. 更新同步记录

使用示例:
    python data_sync.py src/output/bv_info_20251102_215941.json 3656879060
    python data_sync.py --json-file src/output/bv_info_20251102_215941.json --media-id 3656879060 --output-dir output/markdown
"""

import json
import os
import sys
import argparse
import re
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path


class DataSyncManager:
    """数据同步管理器"""

    def __init__(self, output_dir: str = "output/markdown", sync_records_dir: str = "output/sync_records"):
        """
        初始化数据同步管理器

        Args:
            output_dir: Markdown文件输出目录
            sync_records_dir: 同步记录存储目录
        """
        self.output_dir = Path(output_dir)
        self.sync_records_dir = Path(sync_records_dir)

        # 确保目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sync_records_dir.mkdir(parents=True, exist_ok=True)

        # 核心信息字段
        self.core_fields = ["bv", "url_bv", "title", "desc", "time", "up", "fetch_time"]

    def extract_video_list(self, json_file: str) -> List[str]:
        """
        从原始JSON数据中提取视频BV列表

        Args:
            json_file: JSON文件路径

        Returns:
            BV号列表
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 提取所有成功获取的视频的BV号
            bv_list = []
            for item in data:
                if item.get('success', False) and 'bv' in item:
                    bv_list.append(item['bv'])

            print(f"从 {json_file} 中提取到 {len(bv_list)} 个视频")
            return bv_list

        except Exception as e:
            print(f"提取视频列表失败: {e}")
            return []

    def load_sync_record(self, media_id: int) -> Set[str]:
        """
        读取指定收藏夹的历史同步记录

        Args:
            media_id: 收藏夹ID

        Returns:
            已同步的BV号集合
        """
        # 查找最新的同步记录文件
        pattern = f"sync_record_{media_id}_*.json"
        record_files = list(self.sync_records_dir.glob(pattern))

        if not record_files:
            print(f"未找到收藏夹 {media_id} 的历史同步记录")
            return set()

        # 按文件名排序，取最新的
        record_files.sort(key=lambda x: x.name, reverse=True)
        latest_record = record_files[0]

        try:
            with open(latest_record, 'r', encoding='utf-8') as f:
                record_data = json.load(f)

            synced_bvs = set(record_data.get('synced_bvs', []))
            print(f"从历史记录中读取到 {len(synced_bvs)} 个已同步视频")
            return synced_bvs

        except Exception as e:
            print(f"读取历史同步记录失败: {e}")
            return set()

    def compare_and_filter(self, current_bvs: List[str], synced_bvs: Set[str]) -> List[str]:
        """
        新旧数据去重对比，确定需要同步的视频清单

        Args:
            current_bvs: 当前视频列表
            synced_bvs: 已同步视频集合

        Returns:
            需要同步的BV号列表
        """
        current_set = set(current_bvs)
        new_bvs = current_set - synced_bvs

        print(f"当前视频总数: {len(current_bvs)}")
        print(f"已同步视频数: {len(synced_bvs)}")
        print(f"需要同步视频数: {len(new_bvs)}")

        return list(new_bvs)

    def extract_video_info(self, json_file: str, target_bvs: List[str]) -> List[Dict]:
        """
        从原始JSON数据中提取目标视频的完整信息

        Args:
            json_file: JSON文件路径
            target_bvs: 目标BV号列表

        Returns:
            视频信息列表
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            target_set = set(target_bvs)
            video_info_list = []

            for item in data:
                if (item.get('success', False) and
                    'bv' in item and
                    item['bv'] in target_set):
                    video_info_list.append(item)

            print(f"成功提取 {len(video_info_list)} 个视频的完整信息")
            return video_info_list

        except Exception as e:
            print(f"提取视频信息失败: {e}")
            return []

    def filter_core_fields(self, video_info: Dict) -> Dict:
        """
        筛选核心信息字段并转换时间戳

        Args:
            video_info: 完整的视频信息

        Returns:
            筛选后的核心信息
        """
        core_info = {}

        # 筛选核心字段
        for field in self.core_fields:
            if field in video_info:
                core_info[field] = video_info[field]

        # 转换时间戳格式
        if 'time' in core_info and isinstance(core_info['time'], (int, float)):
            # Unix时间戳转换为标准时间格式
            core_info['time'] = datetime.fromtimestamp(core_info['time']).strftime('%Y-%m-%d %H-%M-%S')

        if 'fetch_time' in core_info:
            # ISO格式时间戳转换为标准时间格式
            try:
                dt = datetime.fromisoformat(core_info['fetch_time'].replace('Z', '+00:00'))
                core_info['fetch_time'] = dt.strftime('%Y-%m-%d %H-%M-%S')
            except:
                # 如果转换失败，保持原格式
                pass

        return core_info

    def sanitize_filename(self, filename: str, max_length: int = 100) -> str:
        """
        处理文件名中的特殊字符

        Args:
            filename: 原始文件名
            max_length: 最大长度限制

        Returns:
            处理后的安全文件名
        """
        # 移除或替换Windows文件名中的非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        safe_name = re.sub(illegal_chars, '_', filename)

        # 移除多余的空格和点
        safe_name = re.sub(r'\s+', ' ', safe_name).strip()
        safe_name = safe_name.strip('.')

        # 限制长度
        if len(safe_name) > max_length:
            safe_name = safe_name[:max_length].strip()

        # 如果为空，使用默认名称
        if not safe_name:
            safe_name = "untitled"

        return safe_name

    def clean_markdown_content(self, content: str) -> str:
        """
        清理和规范化 Markdown 内容，处理转义符和换行符

        Args:
            content: 原始 Markdown 内容字符串

        Returns:
            清理后的 Markdown 内容
        """
        if not content:
            return ""
        
        cleaned = content
        
        # 首先处理反斜杠转义，注意顺序很重要
        # 先处理双反斜杠，避免影响其他转义字符的处理
        cleaned = cleaned.replace('\\\\', '\x00')  # 临时替换，避免干扰
        
        # 处理 JSON 字符串中的转义字符（字面的 \n, \t, \r 等）
        cleaned = cleaned.replace('\\n', '\n')
        cleaned = cleaned.replace('\\t', '\t')
        cleaned = cleaned.replace('\\r', '\r')
        cleaned = cleaned.replace('\\"', '"')
        cleaned = cleaned.replace("\\'", "'")
        
        # 恢复真正的反斜杠
        cleaned = cleaned.replace('\x00', '\\')
        
        # 规范化换行符：统一使用 \n
        cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
        
        # 移除开头和结尾的多余空白字符
        cleaned = cleaned.strip()
        
        # 移除连续的空行（保留最多两个连续换行，用于 Markdown 段落分隔）
        # 将3个或更多连续换行符替换为2个换行符
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned

    def extract_subtitle_content(self, video_info: Dict) -> str:
        """
        从视频信息中提取字幕内容，按优先级选择：
        1. 优先使用排版后字幕（reformatted_content）
        2. 如果没有排版后字幕，使用原始字幕（content）
        3. 如果都没有，返回"无视频字幕"
        
        该方法会内部调用 get_subtitle.py 的 get_video_subtitles 方法获取字幕

        Args:
            video_info: 视频信息字典

        Returns:
            字幕内容字符串
        """
        try:
            # 导入字幕提取器
            from get_subtitle import SubtitleExtractor
            
            # 创建字幕提取器实例
            subtitle_extractor = SubtitleExtractor()
            
            # 获取单个视频的字幕（启用排版功能）
            subtitle_result = subtitle_extractor.get_video_subtitles(
                video_info, 
                reformat=True
            )
            
            # 检查是否成功获取字幕
            if not subtitle_result.get('success', False):
                return "无视频字幕"
            
            # 检查是否有字幕数据
            subtitles = subtitle_result.get('subtitles', [])
            
            if not subtitles or not isinstance(subtitles, list):
                return "无视频字幕"
            
            # 遍历所有字幕，优先查找有 reformatted_content 的
            for subtitle in subtitles:
                if not isinstance(subtitle, dict):
                    continue
                
                # 优先使用排版后字幕
                reformatted_content = subtitle.get('reformatted_content', '')
                if reformatted_content and reformatted_content.strip():
                    # 清理和规范化 Markdown 内容
                    cleaned_content = self.clean_markdown_content(reformatted_content)
                    return cleaned_content if cleaned_content else "无视频字幕"
            
            # 如果没有排版后字幕，查找原始字幕
            for subtitle in subtitles:
                if not isinstance(subtitle, dict):
                    continue
                
                content = subtitle.get('content', '')
                if content and content.strip():
                    # 原始字幕也进行基本清理
                    cleaned_content = self.clean_markdown_content(content)
                    return cleaned_content if cleaned_content else "无视频字幕"
            
            # 如果都没有，返回默认提示
            return "无视频字幕"
            
        except Exception as e:
            # 如果获取字幕失败，返回默认提示
            print(f"  警告：获取字幕失败 ({video_info.get('bv', 'unknown')}): {e}")
            return "无视频字幕"

    def save_to_markdown(self, video_info: Dict) -> bool:
        """
        将视频信息保存为Markdown文件

        Args:
            video_info: 视频信息

        Returns:
            是否保存成功
        """
        try:
            # 筛选核心信息
            core_info = self.filter_core_fields(video_info)

            # 生成文件名
            title = core_info.get('title', 'untitled')
            safe_filename = self.sanitize_filename(title)
            filepath = self.output_dir / f"{safe_filename}.md"

            # 处理文件名冲突
            counter = 1
            while filepath.exists():
                filepath = self.output_dir / f"{safe_filename}_{counter}.md"
                counter += 1

            # 生成Front Matter
            front_matter = []
            front_matter.append("---")
            for key, value in core_info.items():
                if key == 'desc':
                    # 描述内容可能较长，单独处理
                    continue
                front_matter.append(f"{key}: {value}")
            front_matter.append("---")

            # 生成Markdown内容
            content_lines = front_matter.copy()
            content_lines.append("")  # 空行

            # 添加描述内容
            if 'desc' in core_info and core_info['desc']:
                content_lines.append(f"# {title}")
                content_lines.append("")
                content_lines.append(core_info['desc'])
            else:
                content_lines.append(f"# {title}")
                content_lines.append("")
                content_lines.append("*该视频暂无描述*")

            # 添加字幕内容（内部会自动获取字幕）
            content_lines.append("")  # 空行
            content_lines.append("## 视频字幕")
            content_lines.append("")
            subtitle_content = self.extract_subtitle_content(video_info)
            content_lines.append(subtitle_content)

            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content_lines))

            print(f"✓ 已保存: {filepath}")
            return True

        except Exception as e:
            print(f"✗ 保存失败 {video_info.get('bv', 'unknown')}: {e}")
            return False

    def update_sync_record(self, media_id: int, all_synced_bvs: List[str]) -> bool:
        """
        更新同步记录

        Args:
            media_id: 收藏夹ID
            all_synced_bvs: 所有已同步的BV号列表

        Returns:
            是否更新成功
        """
        try:
            # 生成新的同步记录文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            record_filename = f"sync_record_{media_id}_{timestamp}.json"
            record_path = self.sync_records_dir / record_filename

            # 准备记录数据
            record_data = {
                'media_id': media_id,
                'sync_time': datetime.now().isoformat(),
                'synced_bvs': sorted(all_synced_bvs),
                'total_count': len(all_synced_bvs)
            }

            # 写入记录文件
            with open(record_path, 'w', encoding='utf-8') as f:
                json.dump(record_data, f, ensure_ascii=False, indent=2)

            print(f"✓ 同步记录已更新: {record_path}")
            return True

        except Exception as e:
            print(f"✗ 更新同步记录失败: {e}")
            return False

    def sync_data(self, json_file: str, media_id: int) -> bool:
        """
        执行完整的数据同步流程

        Args:
            json_file: JSON数据文件路径
            media_id: 收藏夹ID

        Returns:
            是否同步成功
        """
        print(f"开始同步收藏夹 {media_id} 的数据...")
        print(f"数据源文件: {json_file}")
        print("-" * 50)

        # 步骤1: 提取原始视频列表
        current_bvs = self.extract_video_list(json_file)
        if not current_bvs:
            print("未找到有效视频数据，同步终止")
            return False

        # 步骤2: 读取历史同步记录
        synced_bvs = self.load_sync_record(media_id)

        # 步骤3: 新旧记录去重对比
        target_bvs = self.compare_and_filter(current_bvs, synced_bvs)

        if not target_bvs:
            print("没有新的视频需要同步")
            return True

        # 步骤4: 提取目标视频信息
        video_info_list = self.extract_video_info(json_file, target_bvs)
        if not video_info_list:
            print("未能提取到有效视频信息，同步终止")
            return False

        # 步骤5: 筛选核心信息并保存为Markdown（字幕获取在 save_to_markdown 内部自动完成）
        print(f"\n步骤5: 开始保存 {len(video_info_list)} 个视频的Markdown文件...")
        success_count = 0
        for video_info in video_info_list:
            if self.save_to_markdown(video_info):
                success_count += 1

        print(f"成功保存: {success_count}/{len(video_info_list)} 个文件")

        # 步骤7: 更新同步记录
        all_synced_bvs = list(set(current_bvs))  # 所有当前视频都算作已同步
        if self.update_sync_record(media_id, all_synced_bvs):
            print("-" * 50)
            print("✓ 数据同步完成!")
            return True
        else:
            print("-" * 50)
            print("⚠ 同步完成，但更新记录失败")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Bilibili收藏夹数据同步和转换工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python data_sync.py src/output/bv_info_20251102_215941.json 3656879060
  python data_sync.py --json-file src/output/bv_info_20251102_215941.json --media-id 3656879060
  python data_sync.py --json-file src/output/bv_info_20251102_215941.json --media-id 3656879060 --output-dir custom/markdown
        """
    )

    parser.add_argument('json_file', nargs='?', help='JSON数据文件路径')
    parser.add_argument('media_id', nargs='?', type=int, help='收藏夹ID')
    parser.add_argument('--json-file', dest='json_file_alt', help='JSON数据文件路径（替代位置参数）')
    parser.add_argument('--media-id', dest='media_id_alt', type=int, help='收藏夹ID（替代位置参数）')
    parser.add_argument('--output-dir', default='output/markdown', help='Markdown文件输出目录（默认：output/markdown）')
    parser.add_argument('--sync-records-dir', default='output/sync_records', help='同步记录存储目录（默认：output/sync_records）')

    args = parser.parse_args()

    # 获取参数
    json_file = args.json_file or args.json_file_alt
    media_id = args.media_id or args.media_id_alt

    if not json_file or not media_id:
        print("错误: 必须指定JSON文件路径和收藏夹ID")
        print("使用方法: python data_sync.py <json_file> <media_id>")
        print("或使用: python data_sync.py --json-file <json_file> --media-id <media_id>")
        sys.exit(1)

    if not os.path.exists(json_file):
        print(f"错误: JSON文件不存在: {json_file}")
        sys.exit(1)

    # 创建同步管理器
    sync_manager = DataSyncManager(
        output_dir=args.output_dir,
        sync_records_dir=args.sync_records_dir
    )

    # 执行同步
    success = sync_manager.sync_data(json_file, media_id)

    if success:
        print("\n同步操作成功完成!")
        sys.exit(0)
    else:
        print("\n同步操作失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()