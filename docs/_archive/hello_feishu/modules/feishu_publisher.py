"""
飞书发布器 — 配图领域逻辑 + 发布器转发

视频关键帧配图辅助函数（get_video_frames / generate_article_images）是
hello_feishu 视频流水线的领域逻辑。FeishuPublisher 直接转发 tools 的实现
（发布能力在 tools/feishu_publisher.py，本模块不再包装子类）。
"""

import sys
import os
import io
import glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 仓库根（modules/ 的上两级）加入 sys.path，供 from tools.feishu_publisher 导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.feishu_publisher import FeishuPublisher
from config import config


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
