"""WechatPublisher 回归：_request 必须按 UTF-8 解析微信响应

历史缺陷：微信 API 响应 Content-Type 为 text/plain 且不带 charset，
requests 的 response.json() 会按 ISO-8859-1 误读 UTF-8 字节，
草稿标题等中文全部乱码。
"""

import json

import publishing.wechat_publisher as wp
from publishing.wechat_publisher import WechatPublisher


class _FakeResponse:
    """模拟微信 text/plain 无 charset 响应；.json() 复现 requests 的 ISO-8859-1 误读"""

    def __init__(self, payload):
        self.content = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.headers = {'Content-Type': 'text/plain'}

    def json(self):
        return json.loads(self.content.decode('iso-8859-1'))


def _patch_token(monkeypatch):
    monkeypatch.setattr(WechatPublisher, 'get_access_token', lambda self, **kw: 'tok')


def test_request_decodes_utf8_without_charset(monkeypatch):
    payload = {
        'errcode': 0,
        'total_count': 1,
        'item': [{'media_id': 'm-1',
                  'content': {'news_item': [{'title': '微调完全指南：原理 + 代码'}]}}],
    }
    monkeypatch.setattr(wp.requests, 'request',
                        lambda method, url, timeout=None, **kw: _FakeResponse(payload))
    _patch_token(monkeypatch)

    pub = WechatPublisher()
    data = pub._request('POST', '/draft/batchget', json={'offset': 0, 'count': 20})

    title = data['item'][0]['content']['news_item'][0]['title']
    assert title == '微调完全指南：原理 + 代码'


def test_request_retries_once_on_expired_token(monkeypatch):
    expired = {'errcode': 40001, 'errmsg': 'invalid credential'}
    ok = {'errcode': 0, 'total_count': 0, 'item': []}
    responses = [_FakeResponse(expired), _FakeResponse(ok)]
    refreshed = []

    monkeypatch.setattr(wp.requests, 'request',
                        lambda method, url, timeout=None, **kw: responses.pop(0))

    def fake_refresh(self, force_refresh=False):
        refreshed.append(force_refresh)
        return 'tok2'

    monkeypatch.setattr(WechatPublisher, 'get_access_token', fake_refresh)

    pub = WechatPublisher()
    data = pub._request('GET', '/draft/count')

    assert data['errcode'] == 0
    assert True in refreshed  # 重试分支触发过一次强制刷新
    assert responses == []  # 恰好重试一次


def test_request_sends_utf8_body_without_unicode_escapes(monkeypatch):
    """微信后端不解码 JSON 的 \\uXXXX 转义，中文必须以 UTF-8 原文发送"""
    seen = {}

    class _CapResponse:
        content = b'{"errcode": 0}'

        def json(self):
            return json.loads(self.content.decode('utf-8'))

    def fake_request(method, url, timeout=None, **kw):
        seen['data'] = kw.get('data')
        seen['headers'] = kw.get('headers')
        return _CapResponse()

    monkeypatch.setattr(wp.requests, 'request', fake_request)
    _patch_token(monkeypatch)

    pub = WechatPublisher()
    pub._request('POST', '/draft/add', json={'title': '资产库链路验证'})

    body = seen['data']
    assert isinstance(body, bytes)
    assert '资产库链路验证'.encode('utf-8') in body  # UTF-8 原文
    assert b'\\u' not in body                        # 无 \uXXXX 字面转义
    assert seen['headers']['Content-Type'] == 'application/json; charset=utf-8'
