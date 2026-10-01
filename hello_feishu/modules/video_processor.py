"""
视频处理器 — 兼容层：在 core.VideoToolkit 基础上保持旧接口

旧代码 `from modules.video_processor import VideoProcessor` 仍然可用。
新代码建议直接使用 `from core.video_toolkit import VideoToolkit`。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.video_toolkit import VideoToolkit
from config import config


class VideoProcessor:
    """视频处理器 — 兼容旧接口，内部委托给 core.VideoToolkit"""

    def __init__(self):
        self._toolkit = VideoToolkit()
        self.ffmpeg_path = config.FFMPEG_PATH
        self.frame_interval = config.FRAME_INTERVAL
        self.output_quality = config.OUTPUT_QUALITY

    def get_video_info(self, video_path):
        """获取视频信息"""
        return self._toolkit.get_info(video_path)

    def extract_frames(self, video_path, output_dir):
        """按间隔提取普通帧"""
        return self._toolkit.extract_frames(video_path, output_dir, self.frame_interval)

    def extract_key_frames(self, video_path, output_dir):
        """提取 I 帧（关键帧）"""
        return self._toolkit.extract_key_frames(video_path, output_dir)

    def extract_audio(self, video_path, output_dir):
        """提取音频"""
        return self._toolkit.extract_audio(video_path, output_dir)

    def process_video(self, video_path):
        """
        完整处理一个视频：获取信息 + 提取关键帧 + 提取音频
        结果写入 config 配置的目录结构
        """
        from pathlib import Path
        video_name = Path(video_path).stem

        config.ensure_video_directories(video_name)

        frames_dir = config.get_video_frames_dir(video_name)
        audio_dir = config.get_video_audio_dir(video_name)

        video_info = self.get_video_info(video_path)
        frames_result = self.extract_key_frames(video_path, frames_dir)
        audio_result = self.extract_audio(video_path, audio_dir)

        return {
            'video_path': video_path,
            'video_name': video_name,
            'video_info': video_info,
            'frames': frames_result.get('frames', []),
            'frame_count': frames_result.get('frame_count', 0),
            'audio_path': audio_result.get('audio_path'),
            'success': frames_result.get('success') and audio_result.get('success')
        }

    def process_all_videos(self, input_dir):
        """批量处理目录下所有视频"""
        if not os.path.exists(input_dir):
            raise ValueError(f"输入目录不存在: {input_dir}")

        video_files = self._toolkit.list_videos(input_dir, recursive=False)

        results = []
        for video_file in video_files:
            print(f"\n处理视频: {video_file}")
            try:
                result = self.process_video(video_file)
                results.append(result)
                if result.get('success'):
                    print(f"成功处理: {video_file}")
                else:
                    print(f"处理失败: {video_file}")
            except Exception as e:
                print(f"处理失败: {video_file} - {e}")
                results.append({
                    'video_path': video_file,
                    'success': False,
                    'error': str(e)
                })

        return results
