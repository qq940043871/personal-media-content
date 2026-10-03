"""Provider 注册表解析测试（monkeypatch 隔离真实 .env）"""

import pytest

from core.providers.registry import (
    ModelCredentials, ProviderError, list_providers, resolve, try_resolve,
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """清掉真实环境中的注册表/旧键，保证用例确定性"""
    import os
    for key in list(os.environ):
        if key.startswith('PROVIDER_') or key in (
            'LLM_PROVIDER', 'ASR_PROVIDER', 'IMAGE_PROVIDER',
            'LLM_API_KEY', 'LLM_API_URL', 'LLM_MODEL',
            'ASR_API_KEY', 'ASR_API_URL', 'ASR_MODEL',
        ):
            monkeypatch.delenv(key, raising=False)


def test_list_providers_parses_fields():
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv('PROVIDER_MIMO_API_KEY', 'k1')
    monkeypatch.setenv('PROVIDER_MIMO_BASE_URL', 'https://x/v1')
    monkeypatch.setenv('PROVIDER_MIMO_CHAT_MODEL', 'm1')
    monkeypatch.setenv('PROVIDER_MY_BOX_IMAGE_URL', 'https://y/images')
    p = list_providers()
    assert p['mimo'] == {'api_key': 'k1', 'base_url': 'https://x/v1', 'chat_model': 'm1'}
    assert p['my_box'] == {'image_url': 'https://y/images'}


def test_resolve_selected_provider(monkeypatch):
    monkeypatch.setenv('PROVIDER_T1_API_KEY', 'kk')
    monkeypatch.setenv('PROVIDER_T1_BASE_URL', 'https://t1/v1')
    monkeypatch.setenv('PROVIDER_T1_CHAT_MODEL', 't1-chat')
    monkeypatch.setenv('LLM_PROVIDER', 't1')
    c = resolve('chat')
    assert isinstance(c, ModelCredentials)
    assert (c.provider, c.task, c.api_key, c.base_url, c.model) == (
        't1', 'chat', 'kk', 'https://t1/v1', 't1-chat')


def test_resolve_image_url_override(monkeypatch):
    monkeypatch.setenv('PROVIDER_T1_API_KEY', 'kk')
    monkeypatch.setenv('PROVIDER_T1_BASE_URL', 'https://t1/v1')
    monkeypatch.setenv('PROVIDER_T1_IMAGE_MODEL', 'img-1')
    monkeypatch.setenv('PROVIDER_T1_IMAGE_URL', 'https://t1/v1/images/generations')
    monkeypatch.setenv('IMAGE_PROVIDER', 't1')
    c = resolve('image')
    assert c.base_url == 'https://t1/v1/images/generations'
    assert c.model == 'img-1'


def test_resolve_legacy_fallback(monkeypatch):
    monkeypatch.setenv('LLM_API_KEY', 'lk')
    monkeypatch.setenv('LLM_API_URL', 'https://legacy/v1/chat/completions')
    monkeypatch.setenv('LLM_MODEL', 'legacy-model')
    c = resolve('chat')
    assert c.provider == 'legacy'
    assert c.model == 'legacy-model'


def test_resolve_missing_raises_with_hint():
    with pytest.raises(ProviderError) as ei:
        resolve('chat')
    assert 'LLM_PROVIDER' in str(ei.value)


def test_resolve_unknown_selection_raises(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'ghost')
    with pytest.raises(ProviderError) as ei:
        resolve('chat')
    assert 'ghost' in str(ei.value)


def test_resolve_missing_model_raises(monkeypatch):
    monkeypatch.setenv('PROVIDER_T1_API_KEY', 'kk')
    monkeypatch.setenv('PROVIDER_T1_BASE_URL', 'https://t1/v1')
    monkeypatch.setenv('ASR_PROVIDER', 't1')
    with pytest.raises(ProviderError) as ei:
        resolve('asr')
    assert 'ASR_MODEL' in str(ei.value)


def test_try_resolve_never_raises():
    assert try_resolve('chat') is None  # 空环境下返回 None 而非抛错


def test_invalid_task():
    with pytest.raises(ProviderError):
        resolve('tts')
