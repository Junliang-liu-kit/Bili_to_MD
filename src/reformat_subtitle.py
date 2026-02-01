#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕重新排版模块

使用大模型对 JSON 字幕文件的 content 字段进行重新排版。
提示词存放在 config/prompt.yml，使用 GLM-4.6 模型。
"""

import os
import json
import yaml
import requests
import time
import configparser
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class SubtitleReformatter:
    """字幕重新排版器"""

    def __init__(self, api_key: str, llm_timeout_sec: int = 40):
        """
        初始化字幕重新排版器

        Args:
            api_key: GLM API密钥，必须提供
        """
        if not api_key:
            raise ValueError("必须提供 GLM API Key")
        
        self.api_key = api_key
        self.llm_timeout_sec = llm_timeout_sec

    def _load_prompts_from_yaml(self, yaml_path: Optional[str] = None) -> dict:
        """
        从 YAML 文件加载提示词

        Args:
            yaml_path: YAML 文件路径，如果为 None 则使用默认路径

        Returns:
            包含 system_prompt 和 user_prompt 的字典
        """
        if yaml_path is None:
            # 获取项目根目录
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            yaml_path = project_root / "config" / "prompt.yml"

        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                prompts = yaml.safe_load(f)
            
            return {
                'system_prompt': prompts.get('system_prompt', ''),
                'user_prompt': prompts.get('user_prompt', '')
            }
        except FileNotFoundError:
            raise FileNotFoundError(f"提示词文件不存在: {yaml_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML 文件解析失败: {e}")
        except Exception as e:
            raise RuntimeError(f"加载提示词失败: {e}")

    def _call_glm_api(self, system_prompt: str, user_prompt: str) -> str:
        """
        调用 GLM-4.7 API 进行文本重新排版

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            重新排版后的文本内容
        """
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "glm-4.6",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "thinking": {
                "type": "disabled"
            },
            "temperature": 0.7,
            "stream": False,

        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.llm_timeout_sec)
            response.raise_for_status()
            
            result = response.json()
            
            # 提取返回的内容
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                return content
            else:
                raise ValueError(f"API 返回格式异常: {result}")
                
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"调用 GLM API 失败: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"解析 API 响应失败: {e}")

    def reformat_subtitle_content(self, subtitle_data: Dict) -> Dict:
        """
        使用大模型对字幕文件的 content 字段进行重新排版

        Args:
            subtitle_data: 字幕数据字典，格式与 JSON 文件中的单个元素相同

        Returns:
            重新排版后的字幕数据字典，保持原有结构，只更新 content 字段
        """
        # 加载提示词
        prompts = self._load_prompts_from_yaml()
        system_prompt_template = prompts['system_prompt']
        user_prompt_template = prompts['user_prompt']
        
        # 获取视频标题作为主题
        topic = subtitle_data.get('title', '未知主题')
        
        # 填充系统提示词模板中的占位符
        system_prompt = system_prompt_template.replace('{{Topic}}', topic)
        
        # 处理所有字幕的 content 字段
        reformatted_subtitles = []
        for subtitle in subtitle_data.get('subtitles', []):
            original_content = subtitle.get('content', '')
            
            if not original_content:
                # 如果 content 为空，保持原样
                reformatted_subtitles.append(subtitle)
                continue
            
            # 填充用户提示词模板
            user_prompt = user_prompt_template.replace('{{Topic}}', topic)
            user_prompt = user_prompt.replace('{{contents}}', original_content)
            
            print(f"  正在重新排版 {subtitle.get('lan', 'unknown')} 字幕...")
            
            try:
                # 调用 GLM API
                reformatted_content = self._call_glm_api(system_prompt, user_prompt)
                
                # 创建新的字幕字典，保持原有字段，只更新 content
                new_subtitle = subtitle.copy()
                new_subtitle['reformatted_content'] = reformatted_content
                reformatted_subtitles.append(new_subtitle)
                
                print(f"  ✓ {subtitle.get('lan', 'unknown')} 字幕重新排版成功")
                
            except Exception as e:
                print(f"  ✗ {subtitle.get('lan', 'unknown')} 字幕重新排版失败: {e}")
                # 如果失败，保持原样
                reformatted_subtitles.append(subtitle)
        
        # 创建新的结果字典，保持原有结构
        result = subtitle_data.copy()
        result['subtitles'] = reformatted_subtitles
        result['reformat_time'] = datetime.now().isoformat()
        
        return result

    def reformat_subtitle_json_file(self, json_path: str, output_path: Optional[str] = None) -> str:
        """
        对 JSON 字幕文件中的所有字幕进行重新排版

        Args:
            json_path: 输入的 JSON 字幕文件路径
            output_path: 输出的 JSON 文件路径，如果为None则自动生成

        Returns:
            输出文件路径
        """
        # 加载 JSON 文件
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                subtitle_list = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"文件不存在: {json_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 解析失败: {e}")
        
        if not isinstance(subtitle_list, list):
            raise ValueError("JSON 文件格式不正确，应为列表格式")
        
        # 处理每个字幕数据
        reformatted_results = []
        total = len(subtitle_list)
        
        print(f"开始重新排版 {total} 个字幕文件...")
        
        for i, subtitle_data in enumerate(subtitle_list, 1):
            print(f"[{i}/{total}] 处理 {subtitle_data.get('bv', 'unknown')}: {subtitle_data.get('title', 'unknown')}")
            
            try:
                reformatted_data = self.reformat_subtitle_content(subtitle_data)
                reformatted_results.append(reformatted_data)
                print(f"✓ {subtitle_data.get('bv', 'unknown')} 处理完成")
            except Exception as e:
                print(f"✗ {subtitle_data.get('bv', 'unknown')} 处理失败: {e}")
                # 如果失败，保持原样
                reformatted_results.append(subtitle_data)
            
            # 添加延迟避免请求过快
            if i < total:
                time.sleep(1)
        
        # 生成输出文件路径
        if output_path is None:
            # 确保output文件夹存在
            output_dir = "output"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = Path(json_path).stem
            output_path = os.path.join(output_dir, f"{base_name}_reformatted_{timestamp}.json")
        
        if not output_path.endswith('.json'):
            output_path += '.json'
        
        # 保存结果
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(reformatted_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n结果已保存到: {output_path}")
        return output_path


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python reformat_subtitle.py <json_file>")
        print("  python reformat_subtitle.py <json_file> --output <output_filename>")
        print("\n示例:")
        print("  python reformat_subtitle.py output/subtitle_20260117_163516.json")
        print("  python reformat_subtitle.py output/subtitle_20260117_163516.json --output reformatted_subtitle.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    output_filename = None
    
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
        else:
            print(f"未知参数: {arg}")
            i += 1
    
    try:
        # 从 dev.ini 读取 API key
        api_key = None
        config_path = Path(__file__).parent.parent / "config" / "dev.ini"
        
        if config_path.exists():
            try:
                config = configparser.ConfigParser()
                config.read(config_path, encoding='utf-8')
                
                if 'LLM Parameters' in config:
                    api_key = config['LLM Parameters'].get('GLM_API_KEY', '').strip()
                    if api_key.startswith('"') and api_key.endswith('"'):
                        api_key = api_key[1:-1]
                    api_key = api_key.strip()
            except Exception as e:
                print(f"警告：从 dev.ini 读取 API Key 失败: {e}")
        
        # 如果配置文件中没有，从环境变量读取
        if not api_key:
            api_key = os.getenv('GLM_API_KEY')
        
        if not api_key:
            raise ValueError("未找到 GLM API Key，请设置环境变量 GLM_API_KEY 或在 config/dev.ini 中配置")
        
        # 创建重新排版器
        reformatter = SubtitleReformatter(api_key=api_key)
        
        # 执行重新排版
        output_path = reformatter.reformat_subtitle_json_file(json_path, output_filename)
        
        print("-" * 50)
        print(f"处理完成!")
        print(f"结果已保存到: {output_path}")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
