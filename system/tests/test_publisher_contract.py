"""发布器契约测试（不触网：只测结构/注册/校验逻辑）"""

import pytest

from publishing.publisher_base import (
    BasePublisher, MultiPlatformPublisher, PublishResult, _load_publisher,
)
from publishing.feishu_publisher import FeishuPublisher
from publishing.wechat_publisher import WechatPublisher


def test_publish_result_dict_compat():
    r = PublishResult(success=True, platform='feishu', url='http://x')
    assert r['success'] is True
    assert r.get('url') == 'http://x'
    assert r.get('missing', 'd') == 'd'
    assert r.to_dict()['platform'] == 'feishu'
    with pytest.raises(KeyError):
        r['no_such_key']


def test_publish_result_publish_id_from_raw():
    r = PublishResult(success=True, raw={'publish_id': 'p-1'})
    assert r.get('publish_id') == 'p-1'


def test_both_publishers_implement_contract():
    for cls in (FeishuPublisher, WechatPublisher):
        assert issubclass(cls, BasePublisher)
        assert cls.platform_id and cls.platform_name
        pub = cls()
        assert callable(pub.publish_markdown)
        assert callable(pub.health_check)
        assert callable(pub.check_config)


def test_wechat_check_config_unconfigured(monkeypatch):
    from core.config import config
    monkeypatch.setattr(config, 'WECHAT_APP_ID', '')
    monkeypatch.setattr(config, 'WECHAT_APP_SECRET', '')
    pub = WechatPublisher()
    ok, reason = pub.check_config()
    assert ok is False
    assert 'WECHAT_APP_ID' in reason


def test_feishu_check_config_missing_cli(monkeypatch):
    from publishing.feishu_publisher import FeishuPublisher
    pub = FeishuPublisher()
    monkeypatch.setattr(type(pub).__mro__[0], 'health_check', pub.health_check, raising=False)
    # 直接构造一个指向不存在路径的发布器
    pub2 = FeishuPublisher()
    from core.config import config
    monkeypatch.setattr(config, 'LARK_CLI_RUN_JS', r'Z:\definitely\not\there\run.js')
    ok, reason = pub2.check_config()
    assert ok is False
    assert 'lark-cli' in reason


def test_registry_loads_known_platforms():
    assert _load_publisher('feishu') is FeishuPublisher
    assert _load_publisher('wechat') is WechatPublisher
    assert _load_publisher('nope') is None


def test_multi_platform_unknown_platform_result():
    mp = MultiPlatformPublisher(platforms=['feishu'])
    r = mp.publish('unknown-platform', 't', 'c')
    assert r.success is False
    assert 'unknown-platform' in r.error


def test_multi_platform_skips_unconfigured(monkeypatch, tmp_path):
    # 微信凭据清空 → 初始化时应记入 init_errors 而不是崩溃
    from core.config import config
    monkeypatch.setattr(config, 'WECHAT_APP_ID', '')
    monkeypatch.setattr(config, 'WECHAT_APP_SECRET', '')
    mp = MultiPlatformPublisher()
    assert 'wechat' not in mp.available_platforms()
    assert '未配置' in mp.init_errors.get('wechat', '')
    assert 'feishu' in mp.available_platforms()


def test_base_publisher_default_publish_alias():
    class Dummy(BasePublisher):
        platform_id = 'dummy'
        platform_name = 'Dummy'

        def publish_markdown(self, title, content_md, options=None):
            return PublishResult(success=True, platform='dummy', title=title)

    d = Dummy()
    assert d.publish('t', 'c').success is True
    assert d.health_check().success is False  # 默认未实现
