"""
统一配置管理 — 全局只加载一次 .env，所有业务线共用

使用方式：
    from core.config import config
    print(config.LLM_API_KEY)

配置优先级：
    1. 环境变量（已设置的优先）
    2. 项目根目录的 .env 文件
    3. 默认值
"""

import os
from dotenv import load_dotenv

# 项目根目录（core 目录的上一级）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 加载根目录 .env（全局配置）
_env_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(_env_path):
    load_dotenv(_env_path)
else:
    # 兼容旧版：如果根目录没有 .env，尝试各子项目内的 .env
    load_dotenv()


class Config:
    """全局配置类 — 所有业务线共享"""

    # ===== 基础路径 =====
    BASE_DIR = BASE_DIR

    # ===== LLM 大模型配置（小米 mimo）=====
    LLM_API_KEY = os.getenv('LLM_API_KEY', '')
    LLM_API_URL = os.getenv('LLM_API_URL', 'https://api.mimirobot.cn/api/text/chat')
    LLM_MODEL = os.getenv('LLM_MODEL', 'mimi-3.5')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.7'))
    LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '4096'))

    # ===== ASR 语音转写配置（云端：小米 mimo）=====
    ASR_API_KEY = os.getenv('ASR_API_KEY', '')
    ASR_API_URL = os.getenv('ASR_API_URL', 'https://api.mimirobot.cn/api/audio/transcript')
    ASR_MODEL = os.getenv('ASR_MODEL', 'mimi-audio')
    ASR_LANGUAGE = os.getenv('ASR_LANGUAGE', 'zh')

    # ===== 本地 ASR 配置（faster-whisper）=====
    ASR_LOCAL_ENABLED = os.getenv('ASR_LOCAL_ENABLED', 'false').lower() == 'true'
    ASR_LOCAL_MODEL_SIZE = os.getenv('ASR_LOCAL_MODEL_SIZE', 'base')
    ASR_LOCAL_MODEL_PATH = os.getenv('ASR_LOCAL_MODEL_PATH', '')
    ASR_LOCAL_DEVICE = os.getenv('ASR_LOCAL_DEVICE', 'auto')
    ASR_LOCAL_COMPUTE_TYPE = os.getenv('ASR_LOCAL_COMPUTE_TYPE', 'auto')
    ASR_LOCAL_BEAM_SIZE = int(os.getenv('ASR_LOCAL_BEAM_SIZE', '5'))
    ASR_LOCAL_DOWNLOAD_ROOT = os.path.join(BASE_DIR, os.getenv('ASR_LOCAL_DOWNLOAD_ROOT', 'models/asr'))

    # ===== 视频处理配置（FFmpeg）=====
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', 'ffmpeg')
    FRAME_INTERVAL = int(os.getenv('FRAME_INTERVAL', '10'))
    OUTPUT_QUALITY = int(os.getenv('OUTPUT_QUALITY', '2'))

    # ===== 飞书配置 =====
    FEISHU_APP_ID = os.getenv('FEISHU_APP_ID', '')
    FEISHU_APP_SECRET = os.getenv('FEISHU_APP_SECRET', '')
    # lark-cli 的 Node 脚本路径（Windows 默认安装位置）
    LARK_CLI_RUN_JS = os.getenv('LARK_CLI_RUN_JS',
        r'C:\Program Files\nodejs\node_modules\@larksuite\cli\scripts\run.js')

    # ===== 微信公众号配置 =====
    WECHAT_APP_ID = os.getenv('WECHAT_APP_ID', '')
    WECHAT_APP_SECRET = os.getenv('WECHAT_APP_SECRET', '')
    # 默认作者名（可选）
    WECHAT_DEFAULT_AUTHOR = os.getenv('WECHAT_DEFAULT_AUTHOR', '')
    # 是否默认打开评论
    WECHAT_OPEN_COMMENT = os.getenv('WECHAT_OPEN_COMMENT', '0')

    # ===== 存储路径配置 =====
    # 统一素材/产物根目录
    STORAGE_BASE = os.path.join(BASE_DIR, os.getenv('STORAGE_BASE', 'storage'))

    # 视频相关
    STORAGE_VIDEO_INPUT = os.path.join(BASE_DIR, os.getenv('STORAGE_VIDEO_INPUT', 'storage/videos_input'))
    STORAGE_VIDEO_OUTPUT = os.path.join(BASE_DIR, os.getenv('STORAGE_VIDEO_OUTPUT', 'storage/videos_output'))

    # 文章相关
    STORAGE_ARTICLES = os.path.join(BASE_DIR, os.getenv('STORAGE_ARTICLES', 'storage/articles'))

    # 小说相关
    STORAGE_NOVELS = os.path.join(BASE_DIR, os.getenv('STORAGE_NOVELS', 'storage/novels'))

    @classmethod
    def ensure_base_directories(cls):
        """确保所有基础存储目录存在"""
        dirs = [
            cls.STORAGE_BASE,
            cls.STORAGE_VIDEO_INPUT,
            cls.STORAGE_VIDEO_OUTPUT,
            cls.STORAGE_ARTICLES,
            cls.STORAGE_NOVELS,
            cls.ASR_LOCAL_DOWNLOAD_ROOT,
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    @classmethod
    def get_video_output_dir(cls, video_name):
        """获取指定视频的输出目录（视频产品线专用）"""
        return os.path.join(cls.STORAGE_VIDEO_OUTPUT, video_name)

    @classmethod
    def get_video_frames_dir(cls, video_name):
        return os.path.join(cls.get_video_output_dir(video_name), 'frames')

    @classmethod
    def get_video_audio_dir(cls, video_name):
        return os.path.join(cls.get_video_output_dir(video_name), 'audio')

    @classmethod
    def get_video_audio_txt_dir(cls, video_name):
        return os.path.join(cls.get_video_output_dir(video_name), 'audio_txt')

    @classmethod
    def get_video_articles_dir(cls, video_name):
        return os.path.join(cls.get_video_output_dir(video_name), 'articles')

    @classmethod
    def ensure_video_directories(cls, video_name):
        """确保指定视频的所有输出目录都存在"""
        os.makedirs(cls.get_video_output_dir(video_name), exist_ok=True)
        os.makedirs(cls.get_video_frames_dir(video_name), exist_ok=True)
        os.makedirs(cls.get_video_audio_dir(video_name), exist_ok=True)
        os.makedirs(cls.get_video_articles_dir(video_name), exist_ok=True)
        os.makedirs(cls.get_video_audio_txt_dir(video_name), exist_ok=True)


# 全局单例
config = Config()
