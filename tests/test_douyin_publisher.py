"""抖音发布器测试（不触网、不启浏览器：只测契约/校验/注册表逻辑）"""

import json

import pytest

from core.config import config
from tools.douyin_publisher import DouyinPublisher, _clean_tags, _format_tags
from tools.publisher_base import KNOWN_PLATFORMS, MultiPlatformPublisher, _load_publisher


@pytest.fixture
def stub_playwright_ok(monkeypatch):
    """桩掉 playwright 依赖检测（契约测试不真装 playwright）"""
    import tools.douyin_publisher as m
    monkeypatch.setattr(m, '_playwright_available', lambda: (True, ''))


@pytest.fixture
def fake_cookies(tmp_path, monkeypatch):
    """一份合法的抖音登录态文件 + 指向它的配置"""
    path = tmp_path / 'cookies.json'
    path.write_text(json.dumps({'cookies': [
        {'name': 'sessionid', 'value': 'abc123', 'domain': '.douyin.com'},
        {'name': 'ttwid', 'value': 'x', 'domain': '.douyin.com'},
        {'name': 'other', 'value': 'y', 'domain': '.example.com'},
    ]}), encoding='utf-8')
    monkeypatch.setattr(config, 'DOUYIN_COOKIES_FILE', str(path))
    return str(path)


def test_registry_contains_douyin():
    assert 'douyin' in KNOWN_PLATFORMS
    assert _load_publisher('douyin') is DouyinPublisher


def test_implements_contract(stub_playwright_ok, fake_cookies):
    pub = DouyinPublisher()
    assert callable(pub.publish_markdown)
    assert callable(pub.health_check)
    assert callable(pub.check_config)


def test_publish_requires_video_option():
    pub = DouyinPublisher()
    r = pub.publish_markdown('标题', '正文', options={})
    assert r.success is False
    assert 'video' in r.error
    assert r.platform == 'douyin'


def test_publish_missing_video_file(stub_playwright_ok, fake_cookies):
    pub = DouyinPublisher()
    r = pub.publish_markdown('标题', '', options={'video': 'Z:/no/such.mp4'})
    assert r.success is False
    assert '不存在' in r.error


def test_clean_tags_variants():
    assert _clean_tags(['生活', '#记录 ', '']) == ['生活', '记录']
    assert _clean_tags('a, b　c、d') == ['a', 'b', 'c', 'd']
    assert _clean_tags(None) == []
    assert _clean_tags([]) == []


def test_format_tags_variants():
    assert _format_tags(['生活', 'vlog']) == '#生活 #vlog '
    assert _format_tags('a b') == '#a #b '
    assert _format_tags(None) == ''


def test_check_config_needs_playwright(monkeypatch, tmp_path):
    import tools.douyin_publisher as m
    monkeypatch.setattr(m, '_playwright_available', lambda: (False, '未安装 playwright'))
    monkeypatch.setattr(config, 'DOUYIN_COOKIES_FILE', str(tmp_path / 'none.json'))
    ok, reason = DouyinPublisher().check_config()
    assert ok is False
    assert 'playwright' in reason


def test_check_config_needs_cookies(stub_playwright_ok, monkeypatch, tmp_path):
    monkeypatch.setattr(config, 'DOUYIN_COOKIES_FILE', str(tmp_path / 'none.json'))
    ok, reason = DouyinPublisher().check_config()
    assert ok is False
    assert 'douyin login' in reason


def test_check_config_needs_sessionid(stub_playwright_ok, monkeypatch, tmp_path):
    path = tmp_path / 'cookies.json'
    path.write_text(json.dumps(
        {'cookies': [{'name': 'ttwid', 'value': 'x', 'domain': '.douyin.com'}]}),
        encoding='utf-8')
    monkeypatch.setattr(config, 'DOUYIN_COOKIES_FILE', str(path))
    ok, reason = DouyinPublisher().check_config()
    assert ok is False
    assert 'sessionid' in reason


def test_check_config_ok(stub_playwright_ok, fake_cookies):
    ok, reason = DouyinPublisher().check_config()
    assert ok is True, reason


def test_read_cookies_filters_domain(stub_playwright_ok, fake_cookies):
    cookies = DouyinPublisher()._read_cookies()
    assert cookies.get('sessionid') == 'abc123'
    assert 'other' not in cookies


def test_health_check_unconfigured(monkeypatch, tmp_path):
    # 无 playwright / 无登录态 → health_check 走 check_config 前置校验直接失败
    monkeypatch.setattr(config, 'DOUYIN_COOKIES_FILE', str(tmp_path / 'none.json'))
    r = DouyinPublisher().health_check()
    assert r.success is False
    assert r.error


def test_multi_platform_skips_douyin_when_unconfigured(monkeypatch, tmp_path):
    # 未配置登录态 → 初始化时记入 init_errors 而不是崩溃
    import tools.douyin_publisher as m
    monkeypatch.setattr(m, '_playwright_available', lambda: (False, '未安装 playwright'))
    monkeypatch.setattr(config, 'DOUYIN_COOKIES_FILE', str(tmp_path / 'none.json'))
    mp = MultiPlatformPublisher()
    assert 'douyin' not in mp.available_platforms()
    assert 'douyin' in mp.init_errors


def test_multi_platform_publish_without_video_fails_cleanly(stub_playwright_ok, fake_cookies):
    # 平台可用但发布缺视频 → 返回失败结果而不是异常
    mp = MultiPlatformPublisher(platforms=['douyin'])
    assert 'douyin' in mp.available_platforms()
    r = mp.publish('douyin', '标题', '正文')
    assert r.success is False
    assert 'video' in r.error
