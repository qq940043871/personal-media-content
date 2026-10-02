"""
兼容 shim — 实现已迁移至 core/providers/asr.py

旧导入 `from core.asr_client import ASRClient` 继续有效。
新代码建议 `from core.providers.asr import ASRClient`。
"""

from .providers.asr import ASRClient

__all__ = ['ASRClient']
