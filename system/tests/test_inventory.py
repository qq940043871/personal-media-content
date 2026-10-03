"""内容资产盘点测试（tmp 假结构，不依赖仓库真实数据）"""

import json

import pytest

from core.inventory import ContentInventory


@pytest.fixture
def fake_repo(tmp_path):
    """搭一套最小的仓库结构：小说两本 + 文章 + 分析 + 短视频稿 + 成片 + 发布记录"""
    base = tmp_path / 'repo'
    storage = base / 'storage'

    # 小说 a：老布局 chapters/*.txt（README 不计入）
    a_chapters = base / 'assets' / 'novels' / 'book_a' / 'chapters'
    a_chapters.mkdir(parents=True)
    (a_chapters / '第1章.txt').write_text('一' * 100, encoding='utf-8')
    (a_chapters / '第2章.txt').write_text('二' * 150, encoding='utf-8')
    (a_chapters / 'README.md').write_text('说明文件', encoding='utf-8')

    # 小说 b：新布局 novel/chapters/*.md
    b_chapters = base / 'assets' / 'novels' / 'book_b' / 'novel' / 'chapters'
    b_chapters.mkdir(parents=True)
    (b_chapters / 'chapter-001.md').write_text('三' * 2000, encoding='utf-8')

    # 书评分析
    analyses = base / 'hello_weixin_book' / 'analyses'
    analyses.mkdir(parents=True)
    (analyses / 'x.html').write_text('<html></html>', encoding='utf-8')
    (analyses / 'y.html').write_text('<html></html>', encoding='utf-8')

    # 主题/文集：assets/novels/<主题>/（无章节目录，含 .md）
    for theme, n in (('母亲的灶台', 2), ('父亲的手', 1)):
        tdir = base / 'assets' / 'novels' / theme
        tdir.mkdir(parents=True)
        for i in range(n):
            (tdir / f'稿{i}.md').write_text('稿', encoding='utf-8')

    # 成片：两个项目子目录
    for vid in ('v1', 'v2'):
        (storage / 'videos_output' / vid).mkdir(parents=True)

    # 飞书批量发布幂等记录（list 形态）
    db_dir = storage / 'db'
    db_dir.mkdir()
    (db_dir / 'feishu_published.json').write_text(
        json.dumps([{'key': 1}, {'key': 2}, {'key': 3}]), encoding='utf-8')

    return base, storage


def test_scan_novels_two_layouts_and_skip_readme(fake_repo):
    base, _ = fake_repo
    inv = ContentInventory(base_dir=str(base), storage_base=str(base / 'storage'))
    novels = inv.scan_novels()
    assert novels['total_books'] == 2
    assert novels['total_chapters'] == 3
    assert novels['total_words'] == 100 + 150 + 2000

    by_book = {b['book']: b for b in novels['books']}
    assert by_book['book_a']['chapters'] == 2      # README.md 不计
    assert by_book['book_b']['chapters'] == 1      # novel/chapters 新布局
    assert novels['books'][0]['book'] == 'book_b'  # 按字数倒序


def test_scan_assets_statuses_meta_and_project(fake_repo):
    """资产盘点：新布局散文件 + <篇名>/ 工作区文件夹 + 旧平铺兼容 + 按工程聚合"""
    base, _ = fake_repo
    assets = base / 'assets'

    # 新布局：articles/<工程>/drafts/ 下的散文件与技能线 <篇名>/ 工作区
    wd = assets / 'articles' / '公众号' / 'drafts'
    wd.mkdir(parents=True)
    (wd / '单文件稿.md').write_text('x' * 10, encoding='utf-8')
    ws = wd / '20260620-A2'
    ws.mkdir()
    (ws / 'article.md').write_text('正' * 100, encoding='utf-8')
    (ws / 'article.yaml').write_text('title: x', encoding='utf-8')          # 非 md/txt 不计字数
    (ws / 'imgs').mkdir()
    (ws / 'imgs' / 'cover_prompt.md').write_text('c' * 5, encoding='utf-8')  # 夹内嵌套 md 计字数
    yaml_only = wd / '20260624-A5'
    yaml_only.mkdir()
    (yaml_only / 'article.yaml').write_text('title: y', encoding='utf-8')   # 仅配置也算 1 篇工作区
    empty = wd / '20260699-empty'
    empty.mkdir()
    (empty / '.gitkeep').write_text('', encoding='utf-8')                   # 仅隐藏文件不计

    pd = assets / 'articles' / '公众号' / 'published'
    pd.mkdir()
    (pd / '已发.md').write_text('y' * 20, encoding='utf-8')
    (pd / '已发.md.meta.json').write_text('{}', encoding='utf-8')           # sidecar 不计

    # 旧平铺布局：wechat|douyin/<状态>/文件（无工程名）、feishu/<库>/<状态>/文件
    (assets / 'wechat' / 'drafts').mkdir(parents=True)
    (assets / 'wechat' / 'drafts' / 'a.md').write_text('w', encoding='utf-8')
    (assets / 'douyin' / 'published').mkdir(parents=True)
    (assets / 'douyin' / 'published' / 'v.mp4').write_text('v', encoding='utf-8')
    fd = assets / 'feishu' / '我的知识库' / 'drafts'
    fd.mkdir(parents=True)
    (fd / 'c.md').write_text('z' * 30, encoding='utf-8')

    inv = ContentInventory(base_dir=str(base), storage_base=str(base / 'storage'),
                           assets_base=str(base / 'assets'))
    a = inv.scan_assets()
    # 计数：公众号散文件1 + 工作区3 + wechat平铺1 = 5 篇草稿；已发 1 + douyin平铺 1 = 2
    assert a['drafts'] == 5
    assert a['published'] == 2
    assert a['total'] == 7
    # 创作域归并：旧平铺 wechat→articles、douyin→videos、feishu→wikis
    assert a['types']['articles'] == {'drafts': 4, 'published': 1}
    assert a['types']['videos'] == {'drafts': 0, 'published': 1}
    assert a['types']['wikis'] == {'drafts': 1, 'published': 0}

    # 工程聚合：有工程名的进表，公众号 = 散文件1 + 工作区2 草稿（空夹不计）/ 1 已发
    proj = {(p['type'], p['project']): p for p in a['projects']}
    gz = proj[('articles', '公众号')]
    assert gz['drafts'] == 3 and gz['published'] == 1
    assert gz['words'] == 10 + 105 + 20          # 散文件 + 工作区(100+5) + 已发
    assert proj[('wikis', '我的知识库')]['drafts'] == 1
    assert all(p['project'] is not None for p in a['projects'])  # 旧平铺（无工程名）不进工程表

    # 明细：工作区以 <篇名>/<主文件> 呈现；旧平铺无工程名
    files = [i['file'] for i in a['items']]
    assert '20260620-A2/article.md' in files
    assert '20260624-A5/' in files
    assert all('20260699-empty' not in f for f in files)
    feishu = [i for i in a['items'] if i['type'] == 'wikis'][0]
    assert feishu['project'] == '我的知识库' and feishu['status'] == 'drafts'
    wechat = [i for i in a['items'] if i['file'] == 'a.md'][0]
    assert wechat['type'] == 'articles' and wechat['project'] is None


def test_analyses_family_videos(fake_repo):
    base, _ = fake_repo
    inv = ContentInventory(base_dir=str(base), storage_base=str(base / 'storage'))
    family = inv.scan_family_scripts()
    assert inv.count_analyses() == 2
    assert family['themes'] == 2
    assert family['files'] == 3
    assert inv.count_videos() == 2


def test_publish_summary_counts_json_and_records(fake_repo):
    base, storage = fake_repo
    from core.project_manager import ProjectManager
    pm = ProjectManager(db_path=str(storage / 'db' / 'projects.db'))
    rid = pm.start_publish(pm.create_project('文章A', 'article')['id'], 'feishu')
    pm.finish_publish(rid, 'success')

    inv = ContentInventory(base_dir=str(base), storage_base=str(storage),
                           project_manager=pm)
    pub = inv.publish_summary()
    assert pub['feishu_published'] == 3
    assert pub['records']['success'] == 1
    assert pub['records']['total'] == 1


def test_summary_shape_and_missing_dirs(tmp_path):
    # 空仓库：目录全缺也不崩，各项归零
    inv = ContentInventory(base_dir=str(tmp_path), storage_base=str(tmp_path),
                           assets_base=str(tmp_path / 'none'),
                           videos_output_dir=str(tmp_path / 'none'))
    s = inv.summary()
    assert s['novels']['total_books'] == 0
    assert s['assets']['total'] == 0
    assert s['analyses_count'] == 0
    assert s['family']['themes'] == 0
    assert s['videos_output'] == 0
    assert s['publish']['feishu_published'] == 0
    assert s['generated_at_str']


def test_stat_cache_reuses_until_signature_changes(fake_repo):
    base, _ = fake_repo
    inv = ContentInventory(base_dir=str(base), storage_base=str(base / 'storage'))
    first = inv.scan_novels()
    again = inv.scan_novels()
    assert again == first          # 签名未变 → 缓存命中（结果一致）

    # 新增章节 → mtime 签名变化 → 字数增长
    chapter = base / 'assets' / 'novels' / 'book_a' / 'chapters' / '第3章.txt'
    chapter.write_text('新' * 400, encoding='utf-8')
    grown = inv.scan_novels()
    assert grown['total_chapters'] == 4
    assert grown['total_words'] == first['total_words'] + 400
