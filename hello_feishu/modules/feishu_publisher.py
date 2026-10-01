"""
飞书发布器 — 兼容层：在 core.FeishuPublisher 基础上保持旧接口

旧代码 `from modules.feishu_publisher import FeishuPublisher` 仍然可用。
新代码建议直接使用 `from core.feishu_publisher import FeishuPublisher`。
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.feishu_publisher import FeishuPublisher as _CorePublisher, get_video_frames, generate_article_images
from config import config


class FeishuPublisher(_CorePublisher):
    """飞书发布器 — 继承 core 版本，保持完全兼容"""
    pass


# 保留模块级函数（旧代码可能直接导入）
__all__ = ['FeishuPublisher', 'get_video_frames', 'generate_article_images']
