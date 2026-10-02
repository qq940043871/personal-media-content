"""资产库（AssetStore）测试 — put/list/parse/归档/spaces/发布链路（tmp 库，不触网）"""

import os
import types

import pytest

from tools.asset_store import AssetStore
from tools.publisher_base import PublishResult


@pytest.fixture
def store(tmp_path):
    return AssetStore(root=str(tmp_path / 'assets'))


def test_put_text_and_list(store):
    r = store.put('wechat', '文章A.md', content='# 正文')
    assert r['success'] is True
    assert os.path.exists(r['path'])

    items = store.list(platform='wechat')
    assert len(items) == 1
    assert items[0]['status'] == 'drafts'
    assert items[0]['file'] == '文章A.md'


def test_put_copy_src_and_validation(store, tmp_path):
    src = tmp_path / 'v.mp4'
    src.write_bytes(b'\x00\x01')
    assert store.put('douyin', '成片.mp4', src=str(src))['success'] is True

    # 非法平台 / 非法文件名 / 源不存在 / content 与 src 都缺
    assert store.put('podcast', 'x.md', content='x')['success'] is False
    assert store.put('douyin', '.hidden', content='x')['success'] is False
    assert store.put('douyin', 'y.mp4', src=str(tmp_path / 'nope.mp4'))['success'] is False
    assert store.put('douyin', 'z.mp4')['success'] is False


def test_parse_asset_variants(store):
    r = store.put('feishu', 'x.md', content='c', space='我的知识库')
    info = store.parse_asset(r['path'])
    assert info['platform'] == 'feishu'
    assert info['space'] == '我的知识库'
    assert info['status'] == 'drafts'
    assert info['file'] == 'x.md'

    # 无 space 的平台（两级布局）与库外路径
    r2 = store.put('wechat', 'y.md', content='c')
    info2 = store.parse_asset(r2['path'])
    assert info2['space'] is None and info2['status'] == 'drafts'

    outside = store.parse_asset('D:/somewhere/else.md')
    assert outside['platform'] == '' and outside['status'] == ''


def test_mark_published_moves_and_writes_meta(store):
    r = store.put('wechat', '文章A.md', content='# 正文')
    m = store.mark_published(r['path'], url='', asset_id='media123', title='文章A')
    assert m['success'] is True
    assert os.path.exists(m['meta_path'])

    published = store.list(platform='wechat', status='published')
    assert len(published) == 1
    assert store.list(platform='wechat', status='drafts') == []

    meta = published[0]['meta']
    assert meta['id'] == 'media123'
    assert meta['platform'] == 'wechat'
    assert meta['published_at']

    # 同一路径再归档 → 拒绝
    assert store.mark_published(r['path'])['success'] is False


def test_mark_published_name_conflict(store):
    r1 = store.put('wechat', 'a.md', content='1')
    store.mark_published(r1['path'])
    r2 = store.put('wechat', 'a.md', content='2')
    m = store.mark_published(r2['path'])
    assert m['success'] is False
    assert '冲突' in m['error']


def test_feishu_spaces_mapping(store, monkeypatch):
    from core.config import config
    monkeypatch.setattr(config, 'FEISHU_WIKI_SPACES',
                        ' 我的知识库: abc123 , 第二库:def456 , 空项:')
    assert store.spaces() == [
        {'name': '我的知识库', 'space_id': 'abc123'},
        {'name': '第二库', 'space_id': 'def456'},
    ]
    assert store.space_id('第二库') == 'def456'
    assert store.space_id('不存在') is None


def test_publish_one_wechat_archives(store, monkeypatch):
    """发布链路：桩掉发布器，验证发布成功后自动归档 + meta"""
    import tools.publisher_base as pb
    import tools.asset_store as m

    r = store.put('wechat', '文章B.md', content='# 正文')
    path = r['path']

    class FakeWechat:
        platform_id = 'wechat'
        platform_name = '微信公众号'

        def publish_markdown(self, title, content_md, options=None):
            return PublishResult(success=True, platform='wechat',
                                 title=title, id='media_1', url='')

    monkeypatch.setattr(pb, '_load_publisher', lambda pf: FakeWechat)
    args = types.SimpleNamespace(file=path, platform=None, space=None,
                                 title=None, tags=None, cover=None)
    out = m._publish_one(store, args)
    assert out['success'] is True

    published = store.list(platform='wechat', status='published')
    assert len(published) == 1
    assert published[0]['file'] == '文章B.md'
    assert published[0]['meta']['id'] == 'media_1'


def test_publish_one_platform_inference_and_missing_file(store, monkeypatch):
    import tools.publisher_base as pb
    import tools.asset_store as m

    # 平台从路径推断（feishu/<知识库>/drafts）
    r = store.put('feishu', 'x.md', content='c', space='我的知识库')

    captured = {}

    class FakeFeishu:
        platform_id = 'feishu'
        platform_name = '飞书文档'

        def publish_markdown(self, title, content_md, options=None):
            captured['wiki_space'] = (options or {}).get('wiki_space')
            return PublishResult(success=False, platform='feishu',
                                 title=title, error='不触网，故意失败')

    monkeypatch.setattr(pb, '_load_publisher', lambda pf: FakeFeishu)
    args = types.SimpleNamespace(file=r['path'], platform=None, space=None,
                                 title=None, tags=None, cover=None)
    out = m._publish_one(store, args)
    assert out['success'] is False
    assert captured['wiki_space'] == '我的知识库'
    # 失败不归档
    assert store.list(platform='feishu', status='drafts')

    # 库外且未指定平台 → 报错
    bad = types.SimpleNamespace(file='D:/nowhere/a.md', platform=None, space=None,
                                title=None, tags=None, cover=None)
    assert m._publish_one(store, bad)['success'] is False


def test_books_detection(store):
    """书目识别：目录含 chapters/ 或 novel/chapters/ 才算一本小说"""
    import os

    for book, layout in (('甲书', 'chapters'), ('乙书', 'novel/chapters')):
        os.makedirs(os.path.join(store.root, 'novels', book, layout), exist_ok=True)
    # 主题文集（无正文目录）不应被识别成书目
    os.makedirs(os.path.join(store.root, 'novels', '主题A'), exist_ok=True)
    with open(os.path.join(store.root, 'novels', '主题A', '短视频脚本.md'),
              'w', encoding='utf-8') as f:
        f.write('# 脚本')

    assert store.books() == ['乙书', '甲书'] or store.books() == ['甲书', '乙书']


def test_ensure_layout_creates_platform_and_book_dirs(store, monkeypatch):
    """init 骨架：wechat/douyin 各一个，feishu 按知识库，novels 按书名"""
    import os
    import tools.asset_store as m

    monkeypatch.setattr(type(store), 'spaces',
                        lambda self: [{'name': '产品Wiki', 'space_id': '123'}])
    os.makedirs(os.path.join(store.root, 'novels', '甲书', 'chapters'), exist_ok=True)

    r = store.ensure_layout()
    rel = set(r['created'])

    assert {'wechat/drafts', 'wechat/published',
            'douyin/drafts', 'douyin/published',
            'feishu/产品Wiki/drafts', 'feishu/产品Wiki/published',
            'novels/甲书/drafts', 'novels/甲书/published'} <= rel
    for d in rel:
        assert os.path.isdir(os.path.join(store.root, d))
        assert os.path.exists(os.path.join(store.root, d, '.gitkeep'))

    # 幂等：再跑一次没有新增，.gitkeep 也不进资产清单
    again = store.ensure_layout()
    assert again['created'] == []
    assert store.list() == []


def test_ensure_layout_feishu_fallback(store, monkeypatch):
    """未配置 FEISHU_WIKI_SPACES → 回落一个占位知识库目录"""
    import tools.asset_store as m

    monkeypatch.setattr(type(store), 'spaces', lambda self: [])

    r = store.ensure_layout()
    assert f'feishu/{m.DEFAULT_FEISHU_SPACE}/drafts' in r['created']
    assert f'feishu/{m.DEFAULT_FEISHU_SPACE}/published' in r['created']
