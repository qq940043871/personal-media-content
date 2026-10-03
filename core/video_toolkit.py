"""
视频处理工具包 — FFmpeg 封装

提供：
- 视频信息获取
- 关键帧/普通帧提取
- 音频提取
- 视频合并
- 格式转换

使用方式：
    from core.video_toolkit import VideoToolkit
    vt = VideoToolkit()
    info = vt.get_info('video.mp4')
    frames = vt.extract_key_frames('video.mp4', 'output/frames/')
    audio = vt.extract_audio('video.mp4', 'output/audio/')
    merged = vt.concat(['v1.mp4', 'v2.mp4'], 'output/full.mp4')
"""

import os
import subprocess
import json
import re
from pathlib import Path
from .config import config


class VideoToolkit:
    """FFmpeg 视频处理工具集"""

    def __init__(self, ffmpeg_path=None):
        self.ffmpeg_path = ffmpeg_path or config.FFMPEG_PATH

    # ===== 视频信息 =====

    def get_info(self, video_path):
        """
        获取视频基本信息

        Returns:
            dict: {'duration': float, 'width': int, 'height': int, 'fps': float}
            失败返回 None
        """
        ffprobe = self._ffprobe_path()
        if ffprobe:
            info = self._get_info_ffprobe(ffprobe, video_path)
            if info:
                return info
        return self._get_info_fallback(video_path)

    def _ffprobe_path(self):
        """返回可用的 ffprobe 路径（与 ffmpeg 同目录优先，结果缓存）；找不到返回 None"""
        if hasattr(self, '_ffprobe_resolved'):
            return self._ffprobe_resolved or None
        candidates = ['ffprobe']
        ffmpeg_dir = os.path.dirname(self.ffmpeg_path)
        if ffmpeg_dir:
            candidates.insert(0, os.path.join(ffmpeg_dir, 'ffprobe'))
        resolved = None
        for c in candidates:
            try:
                subprocess.run([c, '-version'], stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, check=True)
                resolved = c
                break
            except (OSError, subprocess.CalledProcessError):
                continue
        self._ffprobe_resolved = resolved or ''
        return resolved

    def _get_info_ffprobe(self, ffprobe, video_path):
        """ffprobe 结构化 JSON 解析（-show_entries 是 ffprobe 参数，ffmpeg 不认）"""
        try:
            cmd = [
                ffprobe, '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,r_frame_rate:format=duration',
                '-of', 'json', video_path,
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = self._decode_output(result.stdout)
            if not output:
                return None
            info = json.loads(output)
            stream = next(iter(info.get('streams', [])), None)
            if not stream:
                return None

            duration = float(info.get('format', {}).get('duration', 0))
            width = int(stream.get('width', 0))
            height = int(stream.get('height', 0))

            r_frame_rate = stream.get('r_frame_rate', '30/1')
            if '/' in r_frame_rate:
                num, den = map(int, r_frame_rate.split('/'))
                fps = num / den if den != 0 else 30
            else:
                fps = float(r_frame_rate)

            return {'duration': duration, 'width': width, 'height': height, 'fps': fps}
        except (OSError, ValueError, json.JSONDecodeError) as e:
            print(f"[Video] ffprobe 解析失败: {e}")
            return None

    def _get_info_fallback(self, video_path):
        """正则解析 ffmpeg -i 输出的备用方案（只在 Video 流行内找分辨率/帧率，
        流 ID 的十六进制形如 [0x1]、0x31637661 会误匹配裸的 \\d+x\\d+）"""
        try:
            cmd = [self.ffmpeg_path, '-i', video_path]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output = self._decode_output(result.stdout)

            duration = 0
            dm = re.search(r'Duration:\s*(\d+):(\d+):(\d+\.?\d*)', output)
            if dm:
                duration = int(dm.group(1)) * 3600 + int(dm.group(2)) * 60 + float(dm.group(3))

            width, height, fps = 0, 0, 30
            video_line = next((ln for ln in output.splitlines() if 'Video:' in ln), '')
            if video_line:
                sm = re.search(r'(\d{2,5})x(\d{2,5})', video_line)
                if sm:
                    width, height = int(sm.group(1)), int(sm.group(2))
                fm = re.search(r'([\d.]+)\s*fps', video_line)
                if fm:
                    fps = float(fm.group(1))

            return {'duration': duration, 'width': width, 'height': height, 'fps': fps}
        except Exception as e:
            print(f"[Video] 备用方案也失败: {e}")
            return None

    # ===== 帧提取 =====

    def extract_frames(self, video_path, output_dir, interval=None, scale_width=1920):
        """
        按固定间隔提取普通帧

        Args:
            video_path: 视频路径
            output_dir: 输出目录
            interval: 抽帧间隔（秒），默认取配置
            scale_width: 缩放宽度（高度自适应）

        Returns:
            dict: {'success': bool, 'frame_count': int, 'frames': list}
        """
        if interval is None:
            interval = config.FRAME_INTERVAL

        os.makedirs(output_dir, exist_ok=True)
        video_name = Path(video_path).stem
        frame_pattern = os.path.join(output_dir, f"{video_name}_%04d.jpg")

        cmd = [
            self.ffmpeg_path, '-i', video_path,
            '-vf', f'fps=1/{interval},scale={scale_width}:-1',
            '-q:v', str(config.OUTPUT_QUALITY),
            frame_pattern,
            '-hide_banner'
        ]

        return self._run_ffmpeg_frame_extract(cmd, output_dir, video_name, '')

    def extract_key_frames(self, video_path, output_dir):
        """
        提取 I 帧（关键帧）

        Returns:
            dict: {'success': bool, 'frame_count': int, 'frames': list}
        """
        os.makedirs(output_dir, exist_ok=True)
        video_name = Path(video_path).stem
        frame_pattern = os.path.join(output_dir, f"{video_name}_keyframe_%04d.jpg")

        cmd = [
            self.ffmpeg_path, '-i', video_path,
            '-vf', 'select=eq(pict_type\\,I)',
            '-vsync', 'vfr',
            '-q:v', str(config.OUTPUT_QUALITY),
            frame_pattern,
            '-hide_banner'
        ]

        return self._run_ffmpeg_frame_extract(cmd, output_dir, video_name, '_keyframe_')

    def _run_ffmpeg_frame_extract(self, cmd, output_dir, video_name, name_filter):
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                error_msg = self._decode_output(result.stdout)
                raise Exception(f"FFmpeg错误: {error_msg[:500]}")

            frame_files = sorted([
                f for f in os.listdir(output_dir)
                if video_name + name_filter in f and f.endswith('.jpg')
            ])
            return {
                'success': True,
                'frame_count': len(frame_files),
                'frames': [os.path.join(output_dir, f) for f in frame_files]
            }
        except Exception as e:
            print(f"[Video] 提取帧失败: {e}")
            return {'success': False, 'error': str(e)}

    # ===== 音频提取 =====

    def extract_audio(self, video_path, output_dir, bitrate='128k'):
        """
        从视频中提取 MP3 音频

        Returns:
            dict: {'success': bool, 'audio_path': str}
        """
        os.makedirs(output_dir, exist_ok=True)
        video_name = Path(video_path).stem
        audio_path = os.path.join(output_dir, f"{video_name}.mp3")

        cmd = [
            self.ffmpeg_path, '-i', video_path,
            '-vn', '-acodec', 'libmp3lame',
            '-ab', bitrate,
            audio_path,
            '-hide_banner'
        ]

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                error_msg = self._decode_output(result.stdout)
                raise Exception(f"FFmpeg错误: {error_msg[:500]}")

            if not os.path.exists(audio_path):
                raise Exception("音频文件未生成")

            return {'success': True, 'audio_path': audio_path}
        except Exception as e:
            print(f"[Video] 提取音频失败: {e}")
            return {'success': False, 'error': str(e)}

    # ===== 视频合并 =====

    def concat(self, video_paths, output_path, lossless=True):
        """
        合并多个视频片段

        Args:
            video_paths: 视频路径列表（按顺序）
            output_path: 输出路径
            lossless: 是否无损合并（True 用 concat demuxer，速度快）

        Returns:
            dict: {'success': bool, 'output_path': str}
        """
        if not video_paths:
            return {'success': False, 'error': '没有输入视频'}

        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

        if lossless:
            # 无损合并：使用 concat demuxer + list 文件
            list_file = output_path + '.merge_list.txt'
            with open(list_file, 'w', encoding='utf-8') as f:
                for vp in video_paths:
                    # 路径中的单引号需要转义
                    safe_path = os.path.abspath(vp).replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")

            cmd = [
                self.ffmpeg_path, '-f', 'concat', '-safe', '0',
                '-i', list_file, '-c', 'copy',
                output_path, '-hide_banner'
            ]

            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if result.returncode != 0:
                    error_msg = self._decode_output(result.stdout)
                    raise Exception(f"FFmpeg错误: {error_msg[:500]}")
                return {'success': True, 'output_path': output_path}
            except Exception as e:
                print(f"[Video] 合并失败: {e}")
                return {'success': False, 'error': str(e)}
            finally:
                if os.path.exists(list_file):
                    os.remove(list_file)
        else:
            # 重新编码合并（兼容性好，但慢）
            inputs = []
            for vp in video_paths:
                inputs.extend(['-i', vp])
            filter_parts = []
            for i in range(len(video_paths)):
                filter_parts.append(f'[{i}:v][{i}:a]')
            filter_str = ''.join(filter_parts) + f'concat=n={len(video_paths)}:v=1:a=1[v][a]'

            cmd = [
                self.ffmpeg_path, *inputs,
                '-filter_complex', filter_str,
                '-map', '[v]', '-map', '[a]',
                '-c:v', 'libx264', '-c:a', 'aac',
                output_path, '-hide_banner'
            ]

            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if result.returncode != 0:
                    error_msg = self._decode_output(result.stdout)
                    raise Exception(f"FFmpeg错误: {error_msg[:500]}")
                return {'success': True, 'output_path': output_path}
            except Exception as e:
                print(f"[Video] 合并失败: {e}")
                return {'success': False, 'error': str(e)}

    def concat_with_fade(self, video_paths, output_path, fade_duration=0.5):
        """
        合并视频并添加淡入淡出转场效果

        Args:
            video_paths: 视频路径列表
            output_path: 输出路径
            fade_duration: 转场时长（秒）

        Returns:
            dict: {'success': bool, 'output_path': str}
        """
        if len(video_paths) < 2:
            if len(video_paths) == 1:
                import shutil
                shutil.copy(video_paths[0], output_path)
                return {'success': True, 'output_path': output_path}
            return {'success': False, 'error': '至少需要1个视频'}

        # 获取每个视频的时长
        durations = []
        for vp in video_paths:
            info = self.get_info(vp)
            if info:
                durations.append(info['duration'])
            else:
                return {'success': False, 'error': f'无法获取视频时长: {vp}'}

        # 构建 xfade filter complex
        inputs = []
        for vp in video_paths:
            inputs.extend(['-i', vp])

        filter_complex_parts = []
        current_label = '0:v'
        offset = durations[0] - fade_duration

        for i in range(1, len(video_paths)):
            next_label = f'{i}:v'
            out_label = f'v{i}' if i < len(video_paths) - 1 else 'vout'
            if i == len(video_paths) - 1:
                out_label = 'vout'
            filter_complex_parts.append(
                f'[{current_label}][{next_label}]xfade=transition=fade:'
                f'duration={fade_duration}:offset={offset:.3f}[{out_label}]'
            )
            offset += durations[i] - fade_duration
            current_label = out_label

        filter_complex = ';'.join(filter_complex_parts)

        cmd = [
            self.ffmpeg_path, *inputs,
            '-filter_complex', filter_complex,
            '-map', '[vout]',
            '-pix_fmt', 'yuv420p',
            output_path,
            '-hide_banner'
        ]

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                error_msg = self._decode_output(result.stdout)
                raise Exception(f"FFmpeg错误: {error_msg[:500]}")
            return {'success': True, 'output_path': output_path}
        except Exception as e:
            print(f"[Video] 转场合并失败: {e}")
            return {'success': False, 'error': str(e)}

    # ===== 格式转换 =====

    def to_mp4(self, input_path, output_path=None):
        """转换为 MP4 格式（H.264 + AAC）"""
        if output_path is None:
            output_path = os.path.splitext(input_path)[0] + '.mp4'

        cmd = [
            self.ffmpeg_path, '-i', input_path,
            '-c:v', 'libx264', '-c:a', 'aac',
            '-y', output_path, '-hide_banner'
        ]

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode != 0:
                error_msg = self._decode_output(result.stdout)
                raise Exception(f"FFmpeg错误: {error_msg[:500]}")
            return {'success': True, 'output_path': output_path}
        except Exception as e:
            print(f"[Video] 格式转换失败: {e}")
            return {'success': False, 'error': str(e)}

    # ===== 批量处理 =====

    def list_videos(self, directory, recursive=True):
        """列出目录下所有视频文件"""
        video_exts = ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm')
        videos = []

        if recursive:
            for root, dirs, files in os.walk(directory):
                for f in files:
                    if f.lower().endswith(video_exts):
                        videos.append(os.path.join(root, f))
        else:
            for f in os.listdir(directory):
                if f.lower().endswith(video_exts):
                    videos.append(os.path.join(directory, f))

        return sorted(videos)

    # ===== 工具方法 =====

    @staticmethod
    def _decode_output(raw_bytes):
        """解码 ffmpeg 输出（优先 utf-8，失败回退 gbk）"""
        try:
            return raw_bytes.decode('utf-8', errors='ignore').strip()
        except:
            return raw_bytes.decode('gbk', errors='ignore').strip()
