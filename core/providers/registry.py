"""
Provider 注册表 — 从环境变量解析各能力的模型凭据

.env 结构（见根 .env.example 的「模型 Provider 注册表」段）：

    PROVIDER_<ID>_API_KEY      # 鉴权密钥
    PROVIDER_<ID>_BASE_URL     # 服务基址
    PROVIDER_<ID>_CHAT_MODEL   # chat 能力模型（可选）
    PROVIDER_<ID>_ASR_MODEL    # 转写能力模型（可选）
    PROVIDER_<ID>_IMAGE_MODEL  # 生图能力模型（可选）
    PROVIDER_<ID>_IMAGE_URL    # 生图端点（可选，默认 _BASE_URL）

能力 → provider 选择：

    LLM_PROVIDER=mimo     # chat
    ASR_PROVIDER=mimo     # transcribe
    IMAGE_PROVIDER=ark    # 生图

旧键回退：注册表未覆盖某能力时，回落到旧键
（LLM_API_KEY/LLM_API_URL/LLM_MODEL、ASR_API_KEY/ASR_API_URL/ASR_MODEL）。
"""

import os
from pathlib import Path
from typing import NamedTuple, Optional

# 独立导入本模块时也可见根 .env（load_dotenv 不覆盖已有环境变量，幂等）
_ENV_PATH = Path(__file__).resolve().parents[2] / '.env'
if _ENV_PATH.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_ENV_PATH)
    except ImportError:
        pass


class ProviderError(Exception):
    """Provider 配置缺失或指向不存在的注册项"""


class ModelCredentials(NamedTuple):
    """某能力解析出的模型凭据"""
    provider: str
    task: str
    api_key: str
    base_url: str
    model: str


# 能力 → 选择环境变量 / 旧键三元组
_TASK_SELECT_VAR = {
    'chat': 'LLM_PROVIDER',
    'asr': 'ASR_PROVIDER',
    'image': 'IMAGE_PROVIDER',
}
_TASK_LEGACY = {
    'chat': ('LLM_API_KEY', 'LLM_API_URL', 'LLM_MODEL'),
    'asr': ('ASR_API_KEY', 'ASR_API_URL', 'ASR_MODEL'),
}
# PROVIDER_<ID>_ 后可跟的字段（后缀匹配，注意 _IMAGE_URL 要排在 _URL 类字段前无需处理，字段间无互为后缀）
_PROVIDER_FIELDS = ('API_KEY', 'BASE_URL', 'CHAT_MODEL', 'ASR_MODEL', 'IMAGE_MODEL', 'IMAGE_URL')


def list_providers():
    """收集环境中所有 PROVIDER_* 注册项 → {id: {field: value}}"""
    providers = {}
    for key, value in os.environ.items():
        if not key.startswith('PROVIDER_'):
            continue
        rest = key[len('PROVIDER_'):]
        for field in _PROVIDER_FIELDS:
            suffix = '_' + field
            if rest.endswith(suffix):
                pid = rest[:-len(suffix)].lower()
                if pid:
                    providers.setdefault(pid, {})[field.lower()] = value.strip()
                break
    return providers


def resolve(task) -> ModelCredentials:
    """
    解析某能力（chat / asr / image）的模型凭据。

    顺序：LLM/ASR/IMAGE_PROVIDER 指定的注册项 → 旧键回退。
    解析不到抛 ProviderError（带修复指引）。
    """
    if task not in _TASK_SELECT_VAR:
        raise ProviderError(f"未知能力类型: {task}（可选 chat/asr/image）")

    providers = list_providers()
    selected = os.getenv(_TASK_SELECT_VAR[task], '').strip().lower()
    if selected:
        p = providers.get(selected)
        if not p:
            have = ', '.join(sorted(providers)) or '空'
            raise ProviderError(
                f"{_TASK_SELECT_VAR[task]}={selected}，但注册表中没有 PROVIDER_{selected.upper()}_* 配置"
                f"（当前注册项: {have}）。请在 .env 补齐该 provider 的 API_KEY/BASE_URL/模型键")
        if not p.get('api_key'):
            raise ProviderError(f"PROVIDER_{selected.upper()}_API_KEY 未配置")
        base_url = p.get('image_url') if task == 'image' else p.get('base_url')
        if not base_url:
            url_field = 'IMAGE_URL' if task == 'image' else 'BASE_URL'
            raise ProviderError(f"PROVIDER_{selected.upper()}_{url_field} 未配置")
        model = p.get(f'{task}_model')
        if not model:
            raise ProviderError(f"PROVIDER_{selected.upper()}_{task.upper()}_MODEL 未配置（能力 {task}）")
        return ModelCredentials(selected, task, p['api_key'], base_url, model)

    legacy = _TASK_LEGACY.get(task)
    if legacy:
        api_key = os.getenv(legacy[0], '').strip()
        base_url = os.getenv(legacy[1], '').strip()
        model = os.getenv(legacy[2], '').strip()
        if api_key and base_url and model:
            return ModelCredentials('legacy', task, api_key, base_url, model)

    hint = f"，或沿用旧键 {legacy[0]}/{legacy[1]}/{legacy[2]}" if legacy else ""
    raise ProviderError(
        f"模型能力 {task} 未配置：请在 .env 设置 {_TASK_SELECT_VAR[task]} 与对应 PROVIDER_<ID>_* 键{hint}")


def try_resolve(task) -> Optional[ModelCredentials]:
    """resolve() 的不抛错版本，失败返回 None（供状态展示/doctor 收集细节）"""
    try:
        return resolve(task)
    except ProviderError:
        return None
