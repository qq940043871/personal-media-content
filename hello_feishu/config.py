"""
hello_feishu 配置 — 兼容层：从 core.config 导入，保持旧接口不变

旧代码无需修改，直接 `from config import config` 仍然可用。
所有旧的属性名（INPUT_VIDEO_DIR、OUTPUT_FRAMES_DIR 等）都映射到新版配置。
"""

import sys
import os

# 确保可以导入 core 包（项目根目录）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import config as _core_config, Config as _CoreConfig

# 兼容：如果 hello_feishu 自己的 .env 存在且全局没有，也加载
_local_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(_local_env):
    from dotenv import load_dotenv
    load_dotenv(_local_env)


class _CompatConfig:
    """
    兼容包装器：在 core.config 基础上，追加旧版属性名的别名

    旧代码使用的属性 → 新版对应关系：
    - INPUT_VIDEO_DIR    → STORAGE_VIDEO_INPUT
    - OUTPUT_FRAMES_DIR  → STORAGE_VIDEO_OUTPUT (各子目录)
    - OUTPUT_AUDIO_DIR   → STORAGE_VIDEO_OUTPUT (各子目录)
    - OUTPUT_AUDIO_TXT_DIR → STORAGE_VIDEO_OUTPUT (各子目录)
    - OUTPUT_ARTICLES_DIR → STORAGE_ARTICLES

    方法别名：
    - ensure_directories() → ensure_base_directories() + ensure_video_directories 兼容
    """

    def __getattr__(self, name):
        # 先尝试从 core config 取
        if hasattr(_core_config, name):
            return getattr(_core_config, name)

        # 旧属性名映射
        _aliases = {
            # 输入目录
            'INPUT_VIDEO_DIR': _core_config.STORAGE_VIDEO_INPUT,
            'INPUT_DIR': _core_config.STORAGE_VIDEO_INPUT,

            # 输出根目录（兼容旧代码直接引用）
            'OUTPUT_DIR': _core_config.STORAGE_VIDEO_OUTPUT,
            'OUTPUT_FRAMES_DIR': _core_config.STORAGE_VIDEO_OUTPUT,
            'OUTPUT_AUDIO_DIR': _core_config.STORAGE_VIDEO_OUTPUT,
            'OUTPUT_AUDIO_TXT_DIR': _core_config.STORAGE_VIDEO_OUTPUT,
            'OUTPUT_ARTICLES_DIR': _core_config.STORAGE_ARTICLES,

            # FFmpeg
            'FRAME_INTERVAL': _core_config.FRAME_INTERVAL,
            'OUTPUT_QUALITY': _core_config.OUTPUT_QUALITY,

            # 飞书
            'LARK_CLI_RUN_JS': _core_config.LARK_CLI_RUN_JS,
        }

        if name in _aliases:
            return _aliases[name]

        raise AttributeError(f"'config' object has no attribute '{name}'")

    def __dir__(self):
        return list(set(super().__dir__() + dir(_core_config) + [
            'INPUT_VIDEO_DIR', 'INPUT_DIR',
            'OUTPUT_DIR', 'OUTPUT_FRAMES_DIR', 'OUTPUT_AUDIO_DIR',
            'OUTPUT_AUDIO_TXT_DIR', 'OUTPUT_ARTICLES_DIR',
            'FRAME_INTERVAL', 'OUTPUT_QUALITY',
            'LARK_CLI_RUN_JS',
        ]))

    # ---- 兼容方法 ----

    @staticmethod
    def ensure_directories():
        """旧版方法名 → 新版 ensure_base_directories"""
        _core_config.ensure_base_directories()

    @staticmethod
    def ensure_video_directories(video_name):
        """透传 core config 的方法"""
        _core_config.ensure_video_directories(video_name)

    @staticmethod
    def get_video_output_dir(video_name):
        return _core_config.get_video_output_dir(video_name)

    @staticmethod
    def get_video_frames_dir(video_name):
        return _core_config.get_video_frames_dir(video_name)

    @staticmethod
    def get_video_audio_dir(video_name):
        return _core_config.get_video_audio_dir(video_name)

    @staticmethod
    def get_video_audio_txt_dir(video_name):
        return _core_config.get_video_audio_txt_dir(video_name)

    @staticmethod
    def get_video_articles_dir(video_name):
        return _core_config.get_video_articles_dir(video_name)


# 全局单例（与旧代码保持一致的变量名）
config = _CompatConfig()
