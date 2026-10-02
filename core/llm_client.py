"""
兼容 shim — 实现已迁移至 core/providers/llm.py

旧导入 `from core.llm_client import LLMClient` 继续有效。
新代码建议 `from core.providers.llm import LLMClient, get_llm_client`。
"""

from .providers.llm import LLMClient, get_llm_client

__all__ = ['LLMClient', 'get_llm_client']
