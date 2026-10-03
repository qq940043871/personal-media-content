"""
配置管理模块
使用 Pydantic Settings 管理环境变量和配置
统一入口：同时加载 config/.env（本线覆盖）和 config/article-writing.yaml（写作约束）

凭据解析优先级：本线 config/.env > 仓库根 .env 的 Provider 注册表 > 内置默认。
模型凭据唯一存放处是仓库根 .env 的 PROVIDER_* 段，本线 .env 一般无需配置。
"""
import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, List


# 定位 .env 文件：config/.env
_ENV_DIR = Path(__file__).resolve().parent
_ENV_FILE = _ENV_DIR / ".env"
_REPO_ROOT = _ENV_DIR.parent.parent


# 读取 .env 文件并设置到环境变量（确保 .env 优先）
def _load_env_file():
    """手动加载 .env 文件，覆盖同名环境变量"""
    if _ENV_FILE.exists():
        with open(_ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if value:
                        os.environ[key] = value


_load_env_file()


class Settings(BaseSettings):
    """应用配置 — 统一管理所有配置项"""

    # ==================== LLM 模型配置（本线覆盖项，留空则回落仓库根注册表） ====================
    ARK_API_KEY: Optional[str] = None
    ARK_BASE_URL: Optional[str] = None
    LLM_MODEL: Optional[str] = None

    # ==================== 图片生成模型配置（本线覆盖项，留空则回落仓库根注册表） ====================
    IMAGE_API_KEY: Optional[str] = None  # 为空则使用 ARK_API_KEY
    IMAGE_BASE_URL: Optional[str] = None  # 为空则使用 ARK_BASE_URL
    IMAGE_MODEL: Optional[str] = None

    # ==================== 微信公众号配置（来自 .env） ====================
    WECHAT_APPID: Optional[str] = None
    WECHAT_APPSECRET: Optional[str] = None

    # ==================== 应用配置（来自 .env） ====================
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ==================== 写作约束（来自 .aws-article/config.yaml） ====================
    # 这些字段在 __init__ 中从 YAML 加载，此处仅声明默认值
    ARTICLE_CATEGORY: str = "AI技术"
    TARGET_READER: str = "对大模型和Agent开发感兴趣的技术人员"
    DEFAULT_AUTHOR: str = "AI技术专栏"
    TONE: str = "专业但不装，有观点但不偏激"
    WRITING_STYLE: str = "口语化短句，像朋友聊天"
    FORBIDDEN_WORDS: List[str] = [
        "在当今社会", "随着科技的发展", "值得一提的是",
        "众所周知", "不言而喻", "浅谈", "论", "之我见"
    ]
    DEFAULT_STRUCTURE: List[str] = ["技术深度解析"]
    DEFAULT_CLOSING_BLOCK: List[str] = ["关注引导"]
    DEFAULT_TITLE_STYLE: List[str] = ["悬念+数字"]
    DEFAULT_FORMAT_PRESET: List[str] = ["default"]
    IMAGE_DENSITY: str = "每节一图"
    PUBLISH_METHOD: str = "draft"
    DRAFTS_ROOT: str = "drafts"
    TARGET_WORD_COUNT: str = "1800-2500"
    TITLE_MAX_LENGTH: str = "15"

    model_config = {
        "env_file": str(_ENV_FILE),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 本线未配置的模型/微信凭据，回落仓库根 Provider 注册表，再回落内置默认
        self._fill_credentials_from_registry()
        # 从 config/article-writing.yaml 加载写作约束，覆盖默认值
        self._merge_article_yaml()

    def _fill_credentials_from_registry(self):
        """凭据解析：本线 config/.env > 仓库根 .env 的 PROVIDER_* 注册表 > 内置默认"""
        try:
            if str(_REPO_ROOT) not in sys.path:
                sys.path.insert(0, str(_REPO_ROOT))
            from core.providers.registry import resolve
            from core.config import config as _root_config
        except Exception:
            return  # 脱离仓库根独立使用时，保持纯本地配置行为

        if not (self.ARK_API_KEY and self.ARK_BASE_URL and self.LLM_MODEL):
            try:
                c = resolve('chat')
                self.ARK_API_KEY = self.ARK_API_KEY or c.api_key
                self.ARK_BASE_URL = self.ARK_BASE_URL or c.base_url
                self.LLM_MODEL = self.LLM_MODEL or c.model
            except Exception:
                pass

        if not (self.IMAGE_API_KEY and self.IMAGE_BASE_URL and self.IMAGE_MODEL):
            try:
                c = resolve('image')
                self.IMAGE_API_KEY = self.IMAGE_API_KEY or c.api_key
                self.IMAGE_BASE_URL = self.IMAGE_BASE_URL or c.base_url
                self.IMAGE_MODEL = self.IMAGE_MODEL or c.model
            except Exception:
                pass

        # 内置默认（注册表也未配置时，保持历史行为可用）
        self.ARK_BASE_URL = self.ARK_BASE_URL or "https://ark.cn-beijing.volces.com/api/v3"
        self.LLM_MODEL = self.LLM_MODEL or "doubao-seed-2-0-pro-260215"
        self.IMAGE_BASE_URL = self.IMAGE_BASE_URL or "https://ark.cn-beijing.volces.com/api/v3/images/generations"
        self.IMAGE_MODEL = self.IMAGE_MODEL or "doubao-seedream-4-5-251128"

        if not (self.WECHAT_APPID and self.WECHAT_APPSECRET):
            self.WECHAT_APPID = self.WECHAT_APPID or _root_config.WECHAT_APP_ID
            self.WECHAT_APPSECRET = self.WECHAT_APPSECRET or _root_config.WECHAT_APP_SECRET

    def _merge_article_yaml(self):
        """从 config/article-writing.yaml 加载写作约束，合并到当前实例"""
        yaml_path = Path(__file__).resolve().parent / "article-writing.yaml"
        if not yaml_path.exists():
            return
        try:
            import yaml
            with open(yaml_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f) or {}

            # YAML 键 → Settings 字段名映射
            KEY_MAP = {
                "article_category": "ARTICLE_CATEGORY",
                "target_reader": "TARGET_READER",
                "default_author": "DEFAULT_AUTHOR",
                "tone": "TONE",
                "writing_style": "WRITING_STYLE",
                "forbidden_words": "FORBIDDEN_WORDS",
                "default_structure": "DEFAULT_STRUCTURE",
                "default_closing_block": "DEFAULT_CLOSING_BLOCK",
                "default_title_style": "DEFAULT_TITLE_STYLE",
                "default_format_preset": "DEFAULT_FORMAT_PRESET",
                "image_density": "IMAGE_DENSITY",
                "publish_method": "PUBLISH_METHOD",
                "drafts_root": "DRAFTS_ROOT",
                "target_word_count": "TARGET_WORD_COUNT",
                "title_max_length": "TITLE_MAX_LENGTH",
            }
            for yaml_key, field_name in KEY_MAP.items():
                if yaml_key in yaml_config:
                    setattr(self, field_name, yaml_config[yaml_key])
        except Exception as e:
            print(f"[WARN] 加载 config/article-writing.yaml 失败: {e}")

    def get_article_config(self) -> dict:
        """返回兼容旧版 load_article_config() 格式的 dict"""
        return {
            "article_category": self.ARTICLE_CATEGORY,
            "target_reader": self.TARGET_READER,
            "default_author": self.DEFAULT_AUTHOR,
            "tone": self.TONE,
            "writing_style": self.WRITING_STYLE,
            "forbidden_words": self.FORBIDDEN_WORDS,
            "default_structure": self.DEFAULT_STRUCTURE,
            "default_closing_block": self.DEFAULT_CLOSING_BLOCK,
            "default_title_style": self.DEFAULT_TITLE_STYLE,
            "default_format_preset": self.DEFAULT_FORMAT_PRESET,
            "image_density": self.IMAGE_DENSITY,
            "publish_method": self.PUBLISH_METHOD,
            "drafts_root": self.DRAFTS_ROOT,
            "target_word_count": self.TARGET_WORD_COUNT,
            "title_max_length": self.TITLE_MAX_LENGTH,
        }


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（缓存）"""
    return Settings()


settings = get_settings()