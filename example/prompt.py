#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提示词加载模块

从 YAML 文件中加载提示词，保持向后兼容性。
"""

import os
import yaml
from pathlib import Path


def load_prompts_from_yaml(yaml_path: str = None) -> dict:
    """
    从 YAML 文件加载提示词

    Args:
        yaml_path: YAML 文件路径，如果为 None 则使用默认路径

    Returns:
        包含 system_prompt 和 user_prompt 的字典
    """
    if yaml_path is None:
        # 获取当前文件所在目录
        current_dir = Path(__file__).parent
        yaml_path = current_dir / "prompt.yml"

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


# 从 YAML 文件加载提示词
try:
    prompts = load_prompts_from_yaml()
    system_prompt = prompts['system_prompt']
    user_prompt = prompts['user_prompt']
except Exception as e:
    # 如果加载失败，使用默认值（向后兼容）
    import warnings
    warnings.warn(f"无法从 YAML 文件加载提示词，使用默认值: {e}")
