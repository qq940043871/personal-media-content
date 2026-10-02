"""
飞书发布器 — 兼容层：在 core.FeishuPublisher 基础上保持旧接口

旧代码 `from modules.feishu_publisher import FeishuPublisher` 仍然可用。
新代码建议直接使用 `from core.feishu_publisher import FeishuPublisher`。

视频关键帧配图辅助函数（get_video_frames / generate_article_images）属于
hello_feishu 视频流水线的领域逻辑，原在 core.feishu_publisher 中，已下沉到本模块。
"""

import sys
import os
import io
import glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.feishu_publisher import FeishuPublisher as _CorePublisher
from config import config


class FeishuPublisher(_CorePublisher):
    """飞书发布器 — 继承 core 版本，保持完全兼容"""
    pass


# ===== 视频关键帧配图（hello_feishu 领域逻辑）=====

def get_video_frames(video_name, frames_dir=None, max_frames=5):
    """获取视频关键帧列表（用于文章配图）"""
    if frames_dir is None:
        frames_dir = config.get_video_frames_dir(video_name)

    pattern = os.path.join(frames_dir, f"{video_name}_keyframe_*.jpg")
    frames = sorted(glob.glob(pattern))

    if not frames:
        return []

    if len(frames) <= max_frames:
        return frames

    step = len(frames) // max_frames
    return [frames[i] for i in range(0, len(frames), step)][:max_frames]


def generate_article_images(video_name, frames_dir=None, max_frames=5):
    """生成文章配图数据结构（供 FeishuPublisher.insert_images_batch 使用）"""
    frames = get_video_frames(video_name, frames_dir, max_frames)

    images = []
    for i, frame_path in enumerate(frames):
        images.append({
            'path': frame_path,
            'caption': f"视频关键帧 {i + 1}",
            'selection': None
        })

    return images


__all__ = ['FeishuPublisher', 'get_video_frames', 'generate_article_images']
