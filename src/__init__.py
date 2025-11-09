#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BiliTools 源代码包

该包包含以下主要模块：
- get_favorite: 获取收藏夹信息
- get_bv_info: 获取视频详细信息
- data_sync: 数据同步管理
- Tools: Bilibili API 工具库
"""

from .get_favorite import get_favorite_info
from .get_bv_info import BVInfoExtractor
from .data_sync import DataSyncManager

__all__ = [
    'get_favorite_info',
    'BVInfoExtractor',
    'DataSyncManager'
]

__version__ = '1.0.0'
__author__ = 'BiliTools'