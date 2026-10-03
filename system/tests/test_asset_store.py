"""资产库（AssetStore）测试 — 类型/工程/状态三级契约 + 旧布局兼容（tmp 库，不触网）"""

import os
import types

import pytest

from publishing.asset_store import AssetStore
from publishing.publisher_base import PublishResult


@pytest.fixture
def store(tmp_path):
    return AssetStore(root=str(tmp_path / 'assets'))


def test_put_text_and_list(store):
    r = store.put('articles', '文章A.md', project='我的专栏', content='# 正文')
    assert r['success'] is True
    assert os.path.exists(r['path'])

    items = store.list(type_='articles')
    assert len(items) == 1
    assert items[0]['status'] == 'drafts'
    assert items[0]['file'] == '文章A.md'
    assert items[0]['project'] == '我的专栏'
    assert items[0]['platform'] == 'wechat'  # 类型默认平台


def test_put_validation(store, tmp_path):
    src = tmp_path / 'v.mp4'
    src.write_bytes(b'\x00\x01')
    assert store.put('videos', '成片.mp4', project='系列A', src=str(src))['success'] is True

    # 未知创作域 / 工程名缺失 / 非法文件名 / 源不存在 / content 与 src 都缺
    assert store.put('podcast', 'x.md', content='x')['success'] is False
    assert store.put('articles', 'x.md', content='x')['success'] is False  # 缺 project
    assert store.put('videos', '.hidden', project='A', content='x')['success'] is False
    assert store.put('videos', 'y.mp4', project='A', src=str(tmp_path / 'nope.mp4'))['success'] is False
    assert store.put('videos', 'z.mp4', project='A')['success'] is False

    # wikis 可省略 project → 回落占位知识库
    r = store.put('wikis', 'w.md', content='x')
    assert r['success'] is True and r['project'] == '默认知识库'


def test_parse_asset_variants(store):
    # 新布局：articles / novels / wikis
    r = store.put('articles', 'x.md', project='专栏A', content='c')
    info = store.parse_asset(r['path'])
    assert (info['type'], info['project'], info['status'], info['platform']) == \
        ('articles', '专栏A', 'drafts', 'wechat')
    assert info['legacy'] is False

    info = store.parse_asset(os.path.join(
        store.root, 'novels', '甲书', 'drafts', 'n.md'))
    assert (info['type'], info['project'], info['status']) == ('novels', '甲书', 'drafts')

    info = store.parse_asset(os.path.join(
        store.root, 'wikis', '我的知识库', 'published', 'w.md'))
    assert (info['type'], info['project'], info['status'], info['platform']) == \
        ('wikis', '我的知识库', 'published', 'feishu')

    # 旧布局兼容：wechat/douyin 平铺、feishu/<库>/ 两级
    legacy = store.parse_asset(os.path.join(
        store.root, 'wechat', 'drafts', 'y.md'))
    assert (legacy['type'], legacy['project'], legacy['status'], legacy['platform']) == \
        ('articles', None, 'drafts', 'wechat')
    assert legacy['legacy'] is True

    legacy = store.parse_asset(os.path.join(
        store.root, 'feishu', '我的知识库', 'drafts', 'y.md'))
    assert (legacy['type'], legacy['project'], legacy['status'], legacy['platform']) == \
        ('wikis', '我的知识库', 'drafts', 'feishu')
    assert legacy['legacy'] is True

    # 库外路径
    outside = store.parse_asset('D:/somewhere/else.md')
    assert outside['type'] == '' and outside['status'] == ''


def test_list_covers_legacy_layout(store):
    """旧平铺目录里的文件仍应出现在清单（兼容读取）"""
    legacy_dir = os.path.join(store.root, 'wechat', 'drafts')
    os.makedirs(legacy_dir, exist_ok=True)
    with open(os.path.join(legacy_dir, '旧稿.md'), 'w', encoding='utf-8') as f:
        f.write('# 旧')

    items = store.list()
    assert len(items) == 1
    assert (items[0]['type'], items[0]['project'], items[0]['file']) == \
        ('articles', None, '旧稿.md')


def test_mark_published_moves_and_writes_meta(store):
    r = store.put('articles', '文章A.md', project='我的专栏', content='# 正文')
    m = store.mark_published(r['path'], url='', asset_id='media123', title='文章A')
    assert m['success'] is True
    assert os.path.exists(m['meta_path'])

    published = store.list(type_='articles', status='published')
    assert len(published) == 1
    assert store.list(type_='articles', status='drafts') == []

    meta = published[0]['meta']
    assert meta['id'] == 'media123'
    assert meta['type'] == 'articles'
    assert meta['project'] == '我的专栏'
    assert meta['platform'] == 'wechat'
    assert meta['published_at']

    # 同一路径再归档 → 拒绝
    assert store.mark_published(r['path'])['success'] is False


def test_mark_published_legacy_layout_roundtrips(store):
    """旧布局归档按原样回流：wechat/drafts → wechat/published"""
    legacy_draft = os.path.join(store.root, 'wechat', 'drafts')
    os.makedirs(legacy_draft, exist_ok=True)
    path = os.path.join(legacy_draft, '旧稿.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# 旧')

    m = store.mark_published(path, asset_id='m1')
    assert m['success'] is True
    assert os.path.exists(os.path.join(store.root, 'wechat', 'published', '旧稿.md'))
    assert not os.path.exists(os.path.join(store.root, 'articles'))
    assert m['meta']['platform'] == 'wechat'

    items = store.list()
    assert len(items) == 1 and items[0]['status'] == 'published'


def test_mark_published_name_conflict(store):
    r1 = store.put('articles', 'a.md', project='专栏', content='1')
    store.mark_published(r1['path'])
    r2 = store.put('articles', 'a.md', project='专栏', content='2')
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


def test_publish_one_archives_into_project(store, monkeypatch):
    """发布链路：桩掉发布器，验证按类型推断平台 + 成功后归档进本工程"""
    import publishing.publisher_base as pb
    import publishing.asset_store as m

    r = store.put('articles', '文章B.md', project='专栏A', content='# 正文')
    path = r['path']

    captured = {}

    class FakeWechat:
        platform_id = 'wechat'
        platform_name = '微信公众号'

        def publish_markdown(self, title, content_md, options=None):
            captured['platform'] = self.platform_id
            return PublishResult(success=True, platform='wechat',
                                 title=title, id='media_1', url='')

    monkeypatch.setattr(pb, '_load_publisher', lambda pf: FakeWechat)
    args = types.SimpleNamespace(file=path, platform=None, space=None,
                                 title=None, tags=None, cover=None)
    out = m._publish_one(store, args)
    assert out['success'] is True
    assert captured['platform'] == 'wechat'  # articles → wechat 自动推断

    published = store.list(type_='articles', status='published')
    assert len(published) == 1
    assert published[0]['project'] == '专栏A'
    assert published[0]['meta']['id'] == 'media_1'


def test_publish_one_wikis_space_from_project(store, monkeypatch):
    """wikis 工程 → 平台推断 feishu，知识库名默认取工程名"""
    import publishing.publisher_base as pb
    import publishing.asset_store as m

    r = store.put('wikis', 'x.md', project='产品Wiki', content='c')

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
    assert captured['wiki_space'] == '产品Wiki'
    # 失败不归档
    assert store.list(type_='wikis', status='drafts')

    # 库外且未指定平台 → 报错
    bad = types.SimpleNamespace(file='D:/nowhere/a.md', platform=None, space=None,
                                title=None, tags=None, cover=None)
    assert m._publish_one(store, bad)['success'] is False


def test_books_detection(store):
    """书目识别：目录含 chapters/ 或 novel/chapters/ 才算一本小说"""
    for book, layout in (('甲书', 'chapters'), ('乙书', 'novel/chapters')):
        os.makedirs(os.path.join(store.root, 'novels', book, layout), exist_ok=True)
    # 主题文集（无正文目录）不应被识别成书目
    os.makedirs(os.path.join(store.root, 'novels', '主题A'), exist_ok=True)
    with open(os.path.join(store.root, 'novels', '主题A', '短视频脚本.md'),
              'w', encoding='utf-8') as f:
        f.write('# 脚本')

    assert store.books() == ['乙书', '甲书'] or store.books() == ['甲书', '乙书']


def test_ensure_layout_creates_domain_wikis_and_books(store, monkeypatch):
    """init 骨架：articles/videos 域目录 + wikis 按知识库 + novels 按书名"""
    monkeypatch.setattr(type(store), 'spaces',
                        lambda self: [{'name': '产品Wiki', 'space_id': '123'}])
    os.makedirs(os.path.join(store.root, 'novels', '甲书', 'chapters'), exist_ok=True)

    r = store.ensure_layout()
    rel = set(r['created'])

    assert {'articles', 'videos',
            'wikis/产品Wiki/drafts', 'wikis/产品Wiki/published',
            'novels/甲书/drafts', 'novels/甲书/published'} <= rel
    for d in rel:
        assert os.path.isdir(os.path.join(store.root, d))
        assert os.path.exists(os.path.join(store.root, d, '.gitkeep'))

    # 幂等：再跑一次没有新增，.gitkeep 也不进资产清单
    again = store.ensure_layout()
    assert again['created'] == []
    assert store.list() == []


def test_ensure_layout_wikis_fallback(store, monkeypatch):
    """未配置 FEISHU_WIKI_SPACES → 回落一个占位知识库目录"""
    import publishing.asset_store as m

    monkeypatch.setattr(type(store), 'spaces', lambda self: [])

    r = store.ensure_layout()
    assert f'wikis/{m.DEFAULT_FEISHU_SPACE}/drafts' in r['created']
    assert f'wikis/{m.DEFAULT_FEISHU_SPACE}/published' in r['created']
