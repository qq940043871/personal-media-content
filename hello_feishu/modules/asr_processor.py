"""
ASR 处理器 — 兼容层：在 core.ASRClient 基础上保持旧接口

旧代码 `from modules.asr_processor import ASRProcessor` 仍然可用。
新代码建议直接使用 `from core.asr_client import ASRClient`。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.asr_client import ASRClient
from config import config


class ASRProcessor:
    """ASR 处理器 — 兼容旧接口，内部委托给 core.ASRClient"""

    def __init__(self):
        self._client = ASRClient()
        self.api_key = config.ASR_API_KEY
        self.api_url = config.ASR_API_URL
        self.model = config.ASR_MODEL
        self._local_model = None
        self._local_model_initialized = False

    # ---- 云端转写 ----

    def transcribe(self, audio_path):
        """云端转写"""
        return self._client.transcribe(audio_path)

    def batch_transcribe(self, audio_paths):
        """批量转写"""
        return self._client.batch_transcribe(audio_paths, use_local=False)

    def format_transcript(self, transcript):
        """格式化转写结果"""
        if not transcript or not transcript.get('text'):
            return ''
        return transcript['text']

    def transcribe_with_timestamp(self, audio_path):
        """带时间戳的转写（小米API暂不支持时间戳）"""
        return self.transcribe(audio_path)

    def save_transcript_to_file(self, audio_path, transcript, output_dir=None, video_name=None):
        """保存转写结果到文件"""
        if not transcript or not transcript.get('success'):
            return None

        if output_dir is None:
            if video_name:
                output_dir = config.get_video_audio_txt_dir(video_name)
            else:
                output_dir = config.OUTPUT_AUDIO_TXT_DIR if hasattr(config, 'OUTPUT_AUDIO_TXT_DIR') else os.path.join(os.path.dirname(audio_path), 'audio_txt')

        os.makedirs(output_dir, exist_ok=True)

        audio_filename = os.path.splitext(os.path.basename(audio_path))[0]
        output_path = os.path.join(output_dir, f"{audio_filename}.txt")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript.get('text', ''))

        print(f"转写结果已保存: {output_path}")
        return output_path

    # ---- 本地转写 ----

    def transcribe_local(self, audio_path, language=None):
        """本地 Whisper 转写"""
        return self._client.transcribe_local(audio_path, language)

    def transcribe_local_with_srt(self, audio_path, output_path=None, language=None):
        """本地转写 + SRT 字幕"""
        return self._client.transcribe_with_srt(audio_path, output_path, language)

    def save_local_transcript(self, audio_path, result, output_dir=None, video_name=None):
        """保存本地转写结果"""
        if not result or not result.get('success'):
            return None

        if output_dir is None:
            if video_name:
                output_dir = config.get_video_audio_txt_dir(video_name)
            else:
                output_dir = config.OUTPUT_AUDIO_TXT_DIR if hasattr(config, 'OUTPUT_AUDIO_TXT_DIR') else os.path.join(os.path.dirname(audio_path), 'audio_txt')

        os.makedirs(output_dir, exist_ok=True)
        audio_filename = os.path.splitext(os.path.basename(audio_path))[0]

        txt_path = os.path.join(output_dir, f"{audio_filename}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(result.get('text', ''))
        print(f"转写文本已保存: {txt_path}")

        if result.get('segments'):
            srt_path = os.path.join(output_dir, f"{audio_filename}.srt")
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, seg in enumerate(result.get('segments', []), 1):
                    from core.asr_client import ASRClient
                    start_time = ASRClient._format_srt_time(seg.get('start', 0))
                    end_time = ASRClient._format_srt_time(seg.get('end', 0))
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{seg.get('text', '')}\n\n")
            print(f"SRT字幕已保存: {srt_path}")
            return {'txt_path': txt_path, 'srt_path': srt_path}

        return {'txt_path': txt_path}
