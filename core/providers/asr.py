"""
ASR 语音转写客户端 — 支持云端（小米 mimo）和本地（faster-whisper）双模式

使用方式：
    from core.asr_client import ASRClient   # 兼容旧路径
    asr = ASRClient()

    # 云端转写（默认，凭据来自注册表 ASR_PROVIDER）
    result = asr.transcribe('path/to/audio.mp3')
    print(result['text'])

    # 本地转写（需 faster-whisper）
    result = asr.transcribe_local('path/to/audio.mp3')

    # 本地转写 + 生成 SRT 字幕
    result = asr.transcribe_with_srt('path/to/audio.mp3')
"""

import os
import requests
import base64
from ..config import config
from .llm import _ensure_chat_endpoint


class ASRClient:
    """ASR 语音转写客户端 — 云端/本地双模式"""

    def __init__(self, api_key=None, api_url=None, model=None):
        self.api_key = api_key or config.ASR_API_KEY
        self.api_url = _ensure_chat_endpoint(api_url or config.ASR_API_URL)
        self.model = model or config.ASR_MODEL
        self._local_model = None
        self._local_model_initialized = False

    # ===== 云端 ASR（小米 mimo API）=====

    def transcribe(self, audio_path):
        """
        使用云端 API 进行语音转写（Base64 方式，50MB 限制）

        Returns:
            dict: {'success': bool, 'text': str, 'error': str}
        """
        if not os.path.exists(audio_path):
            return {'success': False, 'error': f"音频文件不存在: {audio_path}"}

        try:
            audio_size = os.path.getsize(audio_path)
            print(f"[ASR] 正在调用云端API转写: {audio_path}")
            print(f"[ASR] 音频大小: {audio_size / 1024 / 1024:.2f}MB")

            if audio_size > 50 * 1024 * 1024:
                return {
                    'success': False,
                    'error': f"音频文件过大({audio_size / 1024 / 1024:.2f}MB)，云端Base64方式不能超过50MB"
                }

            audio_b64, audio_format = self._load_audio_b64(audio_path)

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'input_audio',
                                'input_audio': {'data': audio_b64, 'format': audio_format}
                            }
                        ]
                    }
                ],
                'max_tokens': 4096
            }

            response = requests.post(self.api_url, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()

            return self._parse_cloud_response(result)

        except requests.exceptions.RequestException as e:
            error_msg = f"云端ASR转写失败: {e}"
            print(f"[ASR] {error_msg}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"[ASR] 响应内容: {e.response.text[:500]}")
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"处理音频时出错: {e}"
            print(f"[ASR] {error_msg}")
            return {'success': False, 'error': error_msg}

    def _load_audio_b64(self, audio_path):
        """读取音频为 Base64，并返回 OpenAI input_audio 需要的格式名"""
        ext = os.path.splitext(audio_path)[1].lower().lstrip('.')
        format_map = {
            'mp3': 'mp3', 'wav': 'wav', 'flac': 'flac',
            'm4a': 'm4a', 'ogg': 'ogg', 'aac': 'aac'
        }
        audio_format = format_map.get(ext, 'mp3')

        with open(audio_path, 'rb') as f:
            audio_base64 = base64.b64encode(f.read()).decode('utf-8')

        return audio_base64, audio_format

    def _parse_cloud_response(self, result):
        """解析云端 API 响应"""
        try:
            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0].get('message', {})
                content = message.get('content', '')
                reasoning = message.get('reasoning_content', '')
                text = content if content else reasoning
                return {
                    'success': True,
                    'text': text,
                    'segments': [],
                    'raw_response': result
                }
            if 'response' in result:
                return {'success': True, 'text': result['response'], 'segments': [], 'raw_response': result}
            if 'result' in result:
                return {'success': True, 'text': result['result'], 'segments': [], 'raw_response': result}

            error_msg = (result.get('error', {}).get('message', '')
                        or result.get('msg', '') or '未知响应格式')
            return {'success': False, 'error': f"API错误: {error_msg}", 'raw_response': result}
        except Exception as e:
            return {'success': False, 'error': f"解析响应失败: {e}", 'raw_response': result}

    # ===== 本地 ASR（faster-whisper）=====

    def transcribe_local(self, audio_path, language=None):
        """
        使用本地 faster-whisper 模型转写

        Returns:
            dict: {'success': bool, 'text': str, 'segments': list, 'error': str}
        """
        if not os.path.exists(audio_path):
            return {'success': False, 'error': f"音频文件不存在: {audio_path}"}

        try:
            audio_size = os.path.getsize(audio_path)
            print(f"[ASR] 正在使用本地Whisper模型转写: {audio_path}")
            print(f"[ASR] 音频大小: {audio_size / 1024 / 1024:.2f}MB")

            if not self._init_local_model():
                return {'success': False, 'error': "本地模型初始化失败"}

            if language is None:
                language = config.ASR_LANGUAGE
            if language == 'auto':
                language = None

            print(f"[ASR] 开始转写，语言: {language or '自动检测'}...")

            segments, info = self._local_model.transcribe(
                audio_path,
                language=language,
                beam_size=config.ASR_LOCAL_BEAM_SIZE,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            full_text_parts = []
            segment_list = []

            for segment in segments:
                text = segment.text.strip()
                full_text_parts.append(text)
                segment_list.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': text
                })

            full_text = ''.join(full_text_parts)

            print(f"[ASR] 转写完成! 检测到语言: {info.language} (概率: {info.language_probability:.2%})")
            print(f"[ASR] 转写文本长度: {len(full_text)}字符")

            return {
                'success': True,
                'text': full_text,
                'segments': segment_list,
                'raw_response': {
                    'language': info.language,
                    'language_probability': info.language_probability,
                    'segments': segment_list
                }
            }

        except Exception as e:
            error_msg = f"本地ASR转写失败: {e}"
            print(f"[ASR] {error_msg}")
            return {'success': False, 'error': error_msg}

    def transcribe_with_srt(self, audio_path, output_path=None, language=None):
        """
        本地转写并生成 SRT 字幕文件

        Returns:
            dict: 增加 'srt_path' 字段
        """
        if not os.path.exists(audio_path):
            return {'success': False, 'error': f"音频文件不存在: {audio_path}"}

        result = self.transcribe_local(audio_path, language)
        if not result.get('success'):
            return result

        if output_path is None:
            audio_filename = os.path.splitext(os.path.basename(audio_path))[0]
            output_path = os.path.join(os.path.dirname(audio_path), f"{audio_filename}.srt")

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, seg in enumerate(result['segments'], 1):
                    start_time = self._format_srt_time(seg['start'])
                    end_time = self._format_srt_time(seg['end'])
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{seg['text']}\n\n")

            print(f"[ASR] SRT字幕已保存: {output_path}")
            result['srt_path'] = output_path
        except Exception as e:
            print(f"[ASR] 生成SRT文件失败: {e}")
            result['srt_error'] = str(e)

        return result

    def _init_local_model(self):
        """初始化本地 Whisper 模型（懒加载）"""
        if self._local_model_initialized:
            return True

        try:
            from faster_whisper import WhisperModel
        except ImportError:
            print("[ASR] faster-whisper未安装，正在安装...")
            os.system("pip install faster-whisper")
            from faster_whisper import WhisperModel

        model_path = config.ASR_LOCAL_MODEL_PATH
        model_size = config.ASR_LOCAL_MODEL_SIZE
        device = config.ASR_LOCAL_DEVICE
        compute_type = config.ASR_LOCAL_COMPUTE_TYPE
        download_root = config.ASR_LOCAL_DOWNLOAD_ROOT

        if device == 'auto':
            try:
                import torch
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
            except ImportError:
                device = 'cpu'

        if compute_type == 'auto':
            compute_type = 'float16' if device == 'cuda' else 'int8'

        print(f"[ASR] 正在加载本地Whisper模型: {model_size} (设备: {device}, 计算类型: {compute_type})")
        print(f"[ASR] 模型下载目录: {download_root}")

        if model_path and os.path.exists(model_path):
            self._local_model = WhisperModel(model_path, device=device, compute_type=compute_type)
        else:
            self._local_model = WhisperModel(
                model_size, device=device, compute_type=compute_type,
                download_root=download_root
            )

        self._local_model_initialized = True
        print("[ASR] 本地Whisper模型加载完成")
        return True

    # ===== 工具方法 =====

    @staticmethod
    def _format_srt_time(seconds):
        """将秒数格式化为 SRT 时间格式 (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def save_transcript(self, audio_path, result, output_dir=None):
        """
        保存转写结果到文件（.txt 和 .srt，如果有的话）

        Returns:
            dict: {'txt_path': str, 'srt_path': str (可选)}
        """
        if not result or not result.get('success'):
            return None

        if output_dir is None:
            output_dir = os.path.dirname(audio_path)

        os.makedirs(output_dir, exist_ok=True)
        audio_filename = os.path.splitext(os.path.basename(audio_path))[0]

        txt_path = os.path.join(output_dir, f"{audio_filename}.txt")
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(result.get('text', ''))
        print(f"[ASR] 转写文本已保存: {txt_path}")

        paths = {'txt_path': txt_path}

        if result.get('segments'):
            srt_path = os.path.join(output_dir, f"{audio_filename}.srt")
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, seg in enumerate(result.get('segments', []), 1):
                    start_time = self._format_srt_time(seg.get('start', 0))
                    end_time = self._format_srt_time(seg.get('end', 0))
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{seg.get('text', '')}\n\n")
            print(f"[ASR] SRT字幕已保存: {srt_path}")
            paths['srt_path'] = srt_path

        return paths

    def batch_transcribe(self, audio_paths, use_local=False):
        """批量转写音频文件"""
        results = []
        for audio_path in audio_paths:
            print(f"\n[ASR] 正在转写: {audio_path}")
            try:
                if use_local:
                    result = self.transcribe_local(audio_path)
                else:
                    result = self.transcribe(audio_path)

                results.append({'audio_path': audio_path, **result})
                if result.get('success'):
                    print(f"[ASR] 转写完成: {audio_path}")
                    print(f"[ASR] 转写文本: {result.get('text', '')[:100]}...")
                else:
                    print(f"[ASR] 转写失败: {result.get('error', '未知错误')}")
            except Exception as e:
                print(f"[ASR] 转写失败: {audio_path} - {e}")
                results.append({'audio_path': audio_path, 'success': False, 'error': str(e)})

        return results
