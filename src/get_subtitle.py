#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取视频字幕脚本

该脚本从包含视频信息的JSON文件中读取字幕信息，根据优先级获取字幕：
1. 优先获取所有原声字幕（非ai开头）
2. 如果没有原声字幕，获取ai-zh的ai生成中文字幕
3. 如果都没有，返回报错

使用示例:
    # 从JSON文件获取字幕
    python get_subtitle.py example/bv_info_example.json

    # 指定输出文件名
    python get_subtitle.py example/bv_info_example.json --output subtitle_result.json
"""

import sys
import json
import os
import requests
import time
import random
from datetime import datetime
from typing import List, Dict, Union, Optional

from Tools.config import useragent
from Tools.config import bilicookies


class SubtitleExtractor:
    """字幕提取器"""

    def __init__(
        self,
        cookie_path: Optional[str] = None,
        reformat: bool = False,
        api_key: str = None,
        llm_timeout_sec: int = 40,
        max_original_subtitle_chars: int = 8000,
        max_video_duration_sec: int = 1800,
    ):
        """
        初始化字幕提取器

        Args:
            cookie_path: cookie文件路径，默认为None使用默认路径
            reformat: 是否重新排版，默认为False
            api_key: GLM API密钥，默认为None
        """
        self.cookie_path = cookie_path
        if cookie_path is None:
            from Tools.config import Config
            config = Config()
            cookie_path = config.LOGIN_COOKIE_PATH
        
        self.headers = {
            "User-Agent": useragent().pcChrome,
            "Cookie": bilicookies(path=cookie_path).bilicookie,
            'referer': 'https://www.bilibili.com'
        }

        self.reformat = reformat
        self.api_key = api_key
        self.llm_timeout_sec = llm_timeout_sec
        self.max_original_subtitle_chars = max_original_subtitle_chars
        self.max_video_duration_sec = max_video_duration_sec

    def _select_subtitles(self, subtitles: List[Dict]) -> List[Dict]:
        """
        根据优先级选择字幕

        Args:
            subtitles: 字幕列表

        Returns:
            选中的字幕列表
        """
        # 优先检查原声字幕（非ai开头）
        original_subtitles = [
            sub for sub in subtitles 
            if sub.get('lan', '') and not sub.get('lan', '').startswith('ai-')
        ]
        
        if original_subtitles:
            return original_subtitles
        
        # 如果没有原声字幕，检查ai-zh字幕
        ai_zh_subtitles = [
            sub for sub in subtitles 
            if sub.get('lan', '') == 'ai-zh'
        ]
        
        if ai_zh_subtitles:
            return ai_zh_subtitles
        
        # 如果都没有，返回空列表（表示错误）
        return []

    def _fetch_subtitle_content(self, subtitle_url: str) -> Optional[Dict]:
        """
        获取字幕内容

        Args:
            subtitle_url: 字幕URL

        Returns:
            字幕内容（JSON格式），失败返回None
        """
        try:
            # 如果URL以//开头，需要添加https:
            if subtitle_url.startswith('//'):
                subtitle_url = 'https:' + subtitle_url
            
            response = requests.get(subtitle_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # 解析JSON内容
            subtitle_content = response.json()
            return subtitle_content
            
        except Exception as e:
            print(f"获取字幕内容失败: {e}")
            return None

    def extract_subtitle_text(self, subtitle_content: Dict) -> str:
        """
        将字幕回复体转换为字幕全文
        
        从回复体中提取所有content字段的内容并拼接起来
        
        Args:
            subtitle_content: 字幕回复体（JSON格式的字典）
        
        Returns:
            拼接后的字幕全文，如果回复体格式不正确则返回空字符串
        """
        if not isinstance(subtitle_content, dict):
            return ""
        
        # 提取body数组
        body = subtitle_content.get('body', [])
        
        if not isinstance(body, list):
            return ""
        
        # 提取所有content字段并拼接
        content_list = []
        for item in body:
            if isinstance(item, dict):
                content = item.get('content', '')
                if content:
                    content_list.append(content)
        
        # 拼接所有content
        full_text = ''.join(content_list)
        return full_text

    def get_video_subtitles(self, video_info: Dict, reformat: bool = False) -> Dict:
        """
        获取单个视频的字幕

        Args:
            video_info: 视频信息字典
            reformat: 是否对字幕进行重新排版，默认为False

        Returns:
            包含字幕信息的字典，如果reformat=True，每个字幕会包含reformatted_content字段
        """
        bv = video_info.get('bv', 'Unknown')
        title = video_info.get('title', 'Unknown')
        
        print(f"正在处理 {bv}: {title}")
        
        # 获取字幕信息
        subtitle_info = video_info.get('subtitle', {})
        subtitles_list = subtitle_info.get('subtitles', [])
        
        if not subtitles_list:
            error_msg = f"{bv} 没有可用的字幕"
            print(f"✗ {error_msg}")
            return {
                "bv": bv,
                "title": title,
                "success": False,
                "error": error_msg,
                "subtitles": [],
                "fetch_time": datetime.now().isoformat()
            }
        
        # 根据优先级选择字幕
        selected_subtitles = self._select_subtitles(subtitles_list)
        
        if not selected_subtitles:
            error_msg = f"{bv} 没有原声字幕或ai-zh字幕"
            print(f"✗ {error_msg}")
            return {
                "bv": bv,
                "title": title,
                "success": False,
                "error": error_msg,
                "subtitles": [],
                "fetch_time": datetime.now().isoformat()
            }
        
        # 如果需要重新排版，初始化重新排版器
        reformatter = None
        if reformat:
            try:
                from reformat_subtitle import SubtitleReformatter
                reformatter = SubtitleReformatter(api_key=self.api_key, llm_timeout_sec=self.llm_timeout_sec)
            except ImportError:
                print("  警告：无法导入 reformat_subtitle 模块，跳过重新排版")
                reformat = False
            except Exception as e:
                print(f"  警告：初始化重新排版器失败: {e}，跳过重新排版")
                reformat = False
        
        # 获取所有选中字幕的内容
        subtitle_results = []
        for sub in selected_subtitles:
            lan = sub.get('lan', '')
            lan_doc = sub.get('lan_doc', '')
            subtitle_url = sub.get('subtitle_url', '')
            
            print(f"  正在获取 {lan} ({lan_doc}) 字幕...")
            
            subtitle_content = self._fetch_subtitle_content(subtitle_url)
            
            if subtitle_content:
                # 提取字幕全文
                subtitle_text = self.extract_subtitle_text(subtitle_content)
                subtitle_item = {
                    "lan": lan,
                    "lan_doc": lan_doc,
                    "subtitle_url": subtitle_url,
                    "content": subtitle_text
                }
                
                # 如果需要重新排版，调用重新排版功能
                if reformat and reformatter:
                    try:
                        # 构造临时数据结构用于重新排版
                        temp_subtitle_data = {
                            "title": title,
                            "subtitles": [{
                                "lan": lan,
                                "content": subtitle_text
                            }]
                        }
                        # 调用重新排版
                        reformatted_data = reformatter.reformat_subtitle_content(temp_subtitle_data)
                        # 提取重新排版后的内容
                        if reformatted_data.get('subtitles') and len(reformatted_data['subtitles']) > 0:
                            reformatted_content = reformatted_data['subtitles'][0].get('reformatted_content', '')
                            subtitle_item['reformatted_content'] = reformatted_content
                        else:
                            subtitle_item['reformatted_content'] = ''
                    except Exception as e:
                        subtitle_item['reformatted_content'] = ''
                else:
                    # 如果不需要重新排版，reformatted_content 字段为空
                    subtitle_item['reformatted_content'] = ''
                
                subtitle_results.append(subtitle_item)
        
        if not subtitle_results:
            error_msg = f"{bv} 字幕内容获取失败"
            print(f"✗ {error_msg}")
            return {
                "bv": bv,
                "title": title,
                "success": False,
                "error": error_msg,
                "subtitles": [],
                "fetch_time": datetime.now().isoformat()
            }
        
        print(f"✓ {bv} 字幕获取成功，共 {len(subtitle_results)} 个字幕")
        
        return {
            "bv": bv,
            "title": title,
            "success": True,
            "error": None,
            "subtitles": subtitle_results,
            "fetch_time": datetime.now().isoformat()
        }

    def get_batch_subtitles(self, video_info_list: List[Dict], delay: float = 1.0, reformat: bool = False) -> List[Dict]:
        """
        批量获取视频字幕

        Args:
            video_info_list: 视频信息列表
            delay: 请求间隔时间（秒），默认为1秒
            reformat: 是否对字幕进行重新排版，默认为False

        Returns:
            字幕信息列表
        """
        results = []
        total = len(video_info_list)
        
        print(f"开始批量获取 {total} 个视频的字幕...")
        
        for i, video_info in enumerate(video_info_list, 1):
            print(f"[{i}/{total}] ", end="")
            
            # 获取单个视频字幕
            subtitle_result = self.get_video_subtitles(video_info, reformat=self.reformat)
            results.append(subtitle_result)
            
            # 添加随机延迟避免请求过快
            if i < total:  # 最后一个不需要延迟
                sleep_time = delay + random.uniform(0, 0.5)
                time.sleep(sleep_time)
        
        print(f"\n批量获取完成，成功: {sum(1 for r in results if r.get('success', False))}，"
              f"失败: {sum(1 for r in results if not r.get('success', True))}")
        
        return results

    def save_results_to_json(self, results: List[Dict], filename: str = None) -> str:
        """
        将结果保存为JSON文件

        Args:
            results: 字幕信息列表
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
            filename = f"subtitle_{timestamp}.json"
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        file_path = os.path.join(output_dir, filename)
        
        # 保存结果
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"结果已保存到: {file_path}")
        return file_path

    def load_video_info_from_json(self, json_path: str) -> List[Dict]:
        """
        从JSON文件加载视频信息

        Args:
            json_path: JSON文件路径

        Returns:
            视频信息列表
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 如果数据是列表，直接返回；如果是字典，包装成列表
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                raise ValueError("JSON文件格式不正确")
        
        except FileNotFoundError:
            print(f"文件不存在: {json_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return []
        except Exception as e:
            print(f"读取文件失败: {e}")
            return []



def main():
    """主函数"""
    
    # 创建字幕提取器
    extractor = SubtitleExtractor()
    
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python get_subtitle.py <json_file>")
        print("  python get_subtitle.py <json_file> --output <output_filename>")
        print("  python get_subtitle.py <json_file> --cookie <cookie_path>")
        print("\n示例:")
        print("  python get_subtitle.py example/bv_info_example.json")
        print("  python get_subtitle.py example/bv_info_example.json --output subtitle_result.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    output_filename = None
    cookie_path = None
    reformat = False
    api_key = None # 重新排版需要提供api_key
    
    # 解析参数
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '--output':
            if i + 1 < len(sys.argv):
                output_filename = sys.argv[i + 1]
                i += 2
            else:
                print("--output 参数需要指定输出文件名")
                sys.exit(1)
        elif arg == '--cookie':
            if i + 1 < len(sys.argv):
                cookie_path = sys.argv[i + 1]
                extractor = SubtitleExtractor(cookie_path=cookie_path, reformat=reformat, api_key=api_key)
                i += 2
            else:
                print("--cookie 参数需要指定cookie路径")
                sys.exit(1)
        else:
            print(f"未知参数: {arg}")
            i += 1
    
    # 加载视频信息
    print(f"正在加载视频信息: {json_path}")
    video_info_list = extractor.load_video_info_from_json(json_path)
    
    if not video_info_list:
        print("未找到有效的视频信息")
        sys.exit(1)
    
    print(f"找到 {len(video_info_list)} 个视频")
    print("-" * 50)
    
    # 获取字幕
    results = extractor.get_batch_subtitles(video_info_list, delay=1.0, reformat=True)
    
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
