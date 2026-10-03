"""
资产库（AssetStore）— publishing 发布工具的共享数据契约

回答两个问题：**有什么待发**（list drafts）、**发去哪了**（published + meta.json）。
所有发布类 skills 的输入输出都落在 assets/，技能之间无隐藏状态。

目录结构（根默认 <仓库>/assets，可用 .env 的 ASSETS_BASE 覆盖）：

    assets/
      novels/<书名>/{drafts,published}/       # 小说工程（衍生资产；正文 chapters/ 等不在状态区内）
      articles/<工程名>/{drafts,published}/   # 图文工程 → 默认发公众号
      videos/<工程名>/{drafts,published}/     # 短视频工程 → 默认发抖音
      wikis/<知识库名>/{drafts,published}/    # 知识库工程 → 默认发飞书（名称来自 FEISHU_WIKI_SPACES）

原则：**按作品建工程、按平台做动作**——工程（type/project）是创作空间，
发布平台由类型默认（TYPE_PLATFORM）或 --platform 指定，发布成功后归档回本工程。

状态流转：
    drafts/ → 发布成功 → published/ + 同名 <文件名>.meta.json
    （meta: type/project/platform/title/url/id/published_at）

兼容读取：旧版平台平铺布局（wechat|douyin/<状态>/文件、feishu/<库>/<状态>/文件）
仍可 parse/list/publish，但新工程一律建在新布局。

用法：
    from publishing.asset_store import AssetStore
    store = AssetStore()

    store.put('articles', '文章标题.md', project='我的专栏', content='# 正文')
    store.list(type='articles')                              # 资产清单（含状态）
    store.parse_asset(path)                                  # {'type','project','status','file',...}
    store.mark_published(path, url='...', asset_id='...')    # 归档 + sidecar
    store.ensure_layout()                                    # 幂等建齐目录骨架 + .gitkeep

独立命令行：
    python -m publishing.asset_store init                         # 建齐骨架（wikis 按知识库、novels 按书名）
    python -m publishing.asset_store ls [--type articles] [--status drafts] [--json]
    python -m publishing.asset_store put --type articles --project 专栏A --name x.md --content-file y.md
    python -m publishing.asset_store spaces --json                # FEISHU_WIKI_SPACES 解析结果
"""

import os
import sys
import json
import shutil
from datetime import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.config import config

# 创作域（资产库顶层目录）→ 默认发布平台
ASSET_TYPES = ('novels', 'articles', 'videos', 'wikis')
TYPE_PLATFORM = {'novels': 'feishu', 'articles': 'wechat',
                 'videos': 'douyin', 'wikis': 'feishu'}
# 发布器平台（publishing/publisher_base 注册表键）
PUBLISH_PLATFORMS = ('feishu', 'wechat', 'douyin')
# 旧版平台平铺目录（2026-10 前布局，兼容读取：wechat|douyin/<状态>/文件、feishu/<库>/<状态>/文件）
LEGACY_FLAT = ('wechat', 'douyin')

STATUS_DRAFT = 'drafts'
STATUS_PUBLISHED = 'published'
STATUS = (STATUS_DRAFT, STATUS_PUBLISHED)

META_SUFFIX = '.meta.json'
GITKEEP = '.gitkeep'
# 飞书未配置 FEISHU_WIKI_SPACES 时的占位知识库文件夹（配置映射后重跑 init 会自动补齐真实目录）
DEFAULT_FEISHU_SPACE = '默认知识库'


class AssetError(ValueError):
    """资产库参数/状态错误"""


class AssetStore:
    """待发布资产库：写入草稿、列出清单、发布成功后归档"""

    def __init__(self, root=None):
        self.root = os.path.abspath(root) if root else os.path.abspath(config.ASSETS_BASE)

    # ===== 写入 =====

    def put(self, type_, name, content=None, src=None,
            project=None, status=STATUS_DRAFT):
        """
        写入一个资产（正文内容或源文件拷贝）

        Args:
            type_: 创作域 novels / articles / videos / wikis
            name: 资产文件名（如 '文章标题.md' 或 '成片.mp4'）
            content: 文本内容（与 src 二选一）
            src: 源文件路径（拷贝进资产库，如视频/图片）
            project: 工程名（书名/专栏/系列/知识库）；wikis 缺省取首个知识库或占位库
            status: drafts（默认）或 published

        Returns:
            dict: {'success', 'path', 'type', 'project', 'status'}
        """
        try:
            project = self._resolve_project(type_, project)
            target_dir = self._dir(type_, project, status, create=True)
        except AssetError as e:
            return {'success': False, 'error': str(e)}

        name = os.path.basename(name)
        if not name or name.startswith('.'):
            return {'success': False, 'error': f'非法资产文件名: {name!r}'}
        target = os.path.join(target_dir, name)

        try:
            if src:
                if not os.path.exists(src):
                    return {'success': False, 'error': f'源文件不存在: {src}'}
                shutil.copyfile(src, target)
            else:
                if content is None:
                    return {'success': False, 'error': 'content 与 src 至少提供一个'}
                with open(target, 'w', encoding='utf-8', newline='') as f:
                    f.write(content)
        except OSError as e:
            return {'success': False, 'error': f'写入失败: {e}'}

        print(f"[Asset] 已入库: {os.path.relpath(target, self.root)}")
        return {'success': True, 'path': target,
                'type': type_, 'project': project, 'status': status}

    # ===== 查询 =====

    def list(self, type_=None, project=None, status=None):
        """
        资产清单（含 meta 信息）；type/project/status 均可作过滤

        遍历新布局 <类型>/<工程>/<状态>/，同时兼容旧版平铺
        （wechat|douyin/<状态>/、feishu/<库>/<状态>/——技能线/旧文档可能仍产出）。
        只收单文件；工程内的子文件夹（如技能线的 <篇名>/ 目录）不进清单。

        Returns:
            list[dict]: {'type','project','platform','status','file','path','size',
                         'updated_at_str', 'meta'(已发布的带)}
        """
        types = [type_] if type_ else list(ASSET_TYPES)
        statuses = [status] if status else list(STATUS)
        items = []

        def scan_status_dir(td, proj, status_dir):
            st = os.path.basename(status_dir)
            if st not in statuses:
                return
            for name in sorted(os.listdir(status_dir)):
                path = os.path.join(status_dir, name)
                if not os.path.isfile(path) or name.startswith('.'):
                    continue
                self._collect(td, proj, st, path, items)

        for td in types:
            tdir = os.path.join(self.root, td)
            if not os.path.isdir(tdir):
                continue
            for name in sorted(os.listdir(tdir)):
                full = os.path.join(tdir, name)
                if not os.path.isdir(full) or name.startswith('.'):
                    continue
                if project and name != project:
                    continue
                for st in STATUS:
                    status_dir = os.path.join(full, st)
                    if os.path.isdir(status_dir):
                        scan_status_dir(td, name, status_dir)

        # 旧版平铺布局兼容（wechat|douyin/<状态>/、feishu/<库>/<状态>/）
        for lf in LEGACY_FLAT:
            ldir = os.path.join(self.root, lf)
            if not os.path.isdir(ldir):
                continue
            legacy_type = 'articles' if lf == 'wechat' else 'videos'
            for name in sorted(os.listdir(ldir)):
                full = os.path.join(ldir, name)
                if not os.path.isdir(full):
                    continue
                if name in STATUS:
                    scan_status_dir(legacy_type, None, full)
                else:
                    for st in STATUS:
                        status_dir = os.path.join(full, st)
                        if os.path.isdir(status_dir):
                            scan_status_dir(legacy_type, name, status_dir)
        return items

    def _collect(self, type_, project, status, path, items):
        name = os.path.basename(path)
        if name.startswith('.') or name.endswith(META_SUFFIX):
            return
        meta = self._read_meta(path) if status == STATUS_PUBLISHED else None
        items.append({
            'type': type_,
            'project': project,
            'platform': (meta or {}).get('platform') or TYPE_PLATFORM.get(type_, ''),
            'status': status,
            'file': name,
            'path': path,
            'size': os.path.getsize(path),
            'updated_at_str': datetime.fromtimestamp(
                os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M'),
            **({'meta': meta} if meta else {}),
        })

    def parse_asset(self, path):
        """
        解析资产路径 → {'type','project','status','file','platform','legacy','rel'}

        识别新布局 type/project/status/file（novels、articles、videos、wikis），
        兼容旧版 wechat|douyin/status/file 与 feishu/space/status/file（legacy=True，
        归档时按原布局回流）；不在资产库内或结构不符时 type=''、status=''。
        """
        abs_path = os.path.abspath(path)
        try:
            rel = os.path.relpath(abs_path, self.root)
        except ValueError:
            rel = abs_path
        norm = rel.replace('\\', '/')
        parts = norm.split('/')
        info = {'type': '', 'project': None, 'status': '', 'legacy': False,
                'file': os.path.basename(abs_path), 'platform': '', 'rel': norm}

        rest = parts[1:]
        if parts[0] in ASSET_TYPES and len(rest) >= 3 and rest[-2] in STATUS:
            info['type'] = parts[0]
            info['project'] = '/'.join(rest[:-2])
            info['status'] = rest[-2]
            info['platform'] = TYPE_PLATFORM[parts[0]]
        elif parts[0] in LEGACY_FLAT and len(rest) == 2 and rest[0] in STATUS:
            info['type'] = 'articles' if parts[0] == 'wechat' else 'videos'
            info['status'] = rest[0]
            info['platform'] = parts[0]
            info['legacy'] = True
        elif parts[0] == 'feishu' and len(rest) >= 3 and rest[-2] in STATUS:
            info['type'] = 'wikis'
            info['project'] = '/'.join(rest[:-2])
            info['status'] = rest[-2]
            info['platform'] = 'feishu'
            info['legacy'] = True
        return info

    # ===== 状态流转 =====

    def mark_published(self, path, url='', asset_id='', title=''):
        """
        发布成功后归档：drafts/ → published/，并写 <文件名>.meta.json

        Args:
            path: 资产文件路径（须在资产库内）
            url: 发布产物链接（飞书 doc_url / 公众号无 / 抖音无）
            asset_id: 平台产物 ID（media_id / doc_id 等）
            title: 发布用标题（默认取文件名）

        Returns:
            dict: {'success','published_path','meta_path'}
        """
        info = self.parse_asset(path)
        src = os.path.abspath(path)
        if not os.path.exists(src):
            return {'success': False, 'error': f'资产不存在: {src}'}
        if not info['type'] or info['status'] != STATUS_DRAFT:
            return {'success': False, 'error': f'不是可归档的 drafts 资产: {src}'}

        try:
            if info['legacy']:
                # 旧布局按原样回流：wechat|douyin/published、feishu/<库>/published
                target_dir = os.path.join(self.root, info['platform'])
                if info['project']:
                    target_dir = os.path.join(target_dir, info['project'])
                target_dir = os.path.join(target_dir, STATUS_PUBLISHED)
                os.makedirs(target_dir, exist_ok=True)
            else:
                target_dir = self._dir(info['type'], info['project'],
                                       STATUS_PUBLISHED, create=True)
        except AssetError as e:
            return {'success': False, 'error': str(e)}

        target = os.path.join(target_dir, info['file'])
        if os.path.exists(target):
            return {'success': False, 'error': f'已发布区同名文件冲突: {target}'}

        shutil.move(src, target)

        meta = {
            'type': info['type'],
            'project': info['project'],
            'platform': info['platform'],
            'title': title or os.path.splitext(info['file'])[0],
            'url': url or '',
            'id': asset_id or '',
            'published_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        meta_path = target + META_SUFFIX
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        print(f"[Asset] 已归档: {os.path.relpath(target, self.root)}"
              + (f" → {meta['url']}" if meta['url'] else ''))
        return {'success': True, 'published_path': target, 'meta_path': meta_path,
                'meta': meta}

    # ===== 飞书知识库映射 =====

    def spaces(self):
        """解析 FEISHU_WIKI_SPACES → [{'name','space_id'}]"""
        result = []
        for pair in (config.FEISHU_WIKI_SPACES or '').split(','):
            pair = pair.strip()
            if not pair or ':' not in pair:
                continue
            name, _, space_id = pair.partition(':')
            if name.strip() and space_id.strip():
                result.append({'name': name.strip(), 'space_id': space_id.strip()})
        return result

    def space_id(self, name):
        """知识库名 → space_id；未配置返回 None"""
        for s in self.spaces():
            if s['name'] == name:
                return s['space_id']
        return None

    # ===== 目录骨架 =====

    def books(self):
        """
        资产库里的小说书目（assets/novels/<书名>/）

        判定依据：书目目录下存在 chapters/ 或 novel/chapters/（主题文集目录没有正文目录，跳过）。
        """
        novels_dir = os.path.join(self.root, 'novels')
        if not os.path.isdir(novels_dir):
            return []
        books = []
        for name in sorted(os.listdir(novels_dir)):
            if name.startswith('.'):
                continue
            full = os.path.join(novels_dir, name)
            if not os.path.isdir(full):
                continue
            if (os.path.isdir(os.path.join(full, 'chapters'))
                    or os.path.isdir(os.path.join(full, 'novel', 'chapters'))):
                books.append(name)
        return books

    def ensure_layout(self, gitkeep=True, spaces=None, books=None):
        """
        建齐资产库骨架（幂等）：

        - articles / videos：创作域目录本身（工程由创建者自建，init 不预造空工程）
        - wikis：FEISHU_WIKI_SPACES 里每个知识库名一个工程；未配置时回落占位目录
        - novels：每本小说（含 chapters/ 的目录）一个工程，下分 drafts/ published/

        Args:
            gitkeep: 空目录写 .gitkeep（git 不跟踪空目录；.gitkeep 不参与资产清单）
            spaces: 覆盖知识库名列表（默认读 FEISHU_WIKI_SPACES）
            books: 覆盖书目列表（默认自动识别）

        Returns:
            dict: {'root', 'created': [...], 'existing': [...]}（相对资产库根的路径）
        """
        created, existing = [], []

        def ensure(directory):
            rel = os.path.relpath(directory, self.root).replace('\\', '/')
            existed = os.path.isdir(directory)
            os.makedirs(directory, exist_ok=True)
            (existing if existed else created).append(rel)
            if gitkeep:
                keep = os.path.join(directory, GITKEEP)
                if not os.path.exists(keep):
                    with open(keep, 'w', encoding='utf-8') as f:
                        f.write('')

        for td in ('articles', 'videos'):
            ensure(os.path.join(self.root, td))

        for s in (spaces if spaces is not None
                  else ([x['name'] for x in self.spaces()] or [DEFAULT_FEISHU_SPACE])):
            for status in STATUS:
                ensure(self._dir('wikis', s, status, create=False))

        for book in (books if books is not None else self.books()):
            for status in STATUS:
                ensure(self._dir('novels', book, status, create=False))

        return {'root': self.root, 'created': created, 'existing': existing}

    # ===== 内部 =====

    def _resolve_project(self, type_, project):
        if type_ not in ASSET_TYPES:
            raise AssetError(f'未知创作域: {type_}（可选: {", ".join(ASSET_TYPES)}）')
        if project:
            return project
        if type_ == 'wikis':
            return next(iter([s['name'] for s in self.spaces()]), DEFAULT_FEISHU_SPACE)
        raise AssetError(f'{type_} 需要指定工程名（--project，如书名/专栏/系列）')

    def _dir(self, type_, project, status, create=False):
        if type_ not in ASSET_TYPES:
            raise AssetError(f'未知创作域: {type_}（可选: {", ".join(ASSET_TYPES)}）')
        if status not in STATUS:
            raise AssetError(f'未知状态: {status}（可选: {", ".join(STATUS)}）')
        path = os.path.join(self.root, type_)
        if project:
            path = os.path.join(path, project)
        path = os.path.join(path, status)
        if create:
            os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def _read_meta(published_path):
        try:
            with open(published_path + META_SUFFIX, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None


# ===== 独立命令行入口（skill 化契约：--json 输出 / 退出码 0=成功 1=失败）=====

def main():
    import argparse

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--json', action='store_true', help='输出 JSON 结果')
    parser = argparse.ArgumentParser(
        prog='python -m publishing.asset_store', description='待发布资产库管理')
    parser.add_argument('--root', help='资产库根目录（默认 <仓库>/assets）')
    sub = parser.add_subparsers(dest='action', required=True)

    p_ls = sub.add_parser('ls', parents=[common], help='资产清单')
    p_ls.add_argument('--type', choices=ASSET_TYPES, dest='type_', help='按创作域过滤')
    p_ls.add_argument('--project', help='按工程过滤')
    p_ls.add_argument('--status', choices=STATUS, help='按状态过滤')

    p_put = sub.add_parser('put', parents=[common], help='写入资产（默认进 drafts）')
    p_put.add_argument('--type', choices=ASSET_TYPES, dest='type_', required=True)
    p_put.add_argument('--project', help='工程名（书名/专栏/系列/知识库）')
    p_put.add_argument('--name', required=True, help='资产文件名')
    p_put.add_argument('--content', help='文本内容')
    p_put.add_argument('--content-file', help='从文件读取内容')
    p_put.add_argument('--src', help='源文件路径（视频/图片等直接拷贝）')
    p_put.add_argument('--status', choices=STATUS, default=STATUS_DRAFT)

    p_pub = sub.add_parser('publish', parents=[common], help='发布一个 drafts 资产（调对应平台发布器，成功自动归档）')
    p_pub.add_argument('--file', required=True, help='资产文件路径')
    p_pub.add_argument('--platform', choices=PUBLISH_PLATFORMS,
                       help='目标平台（默认按创作域推断，可覆盖）')
    p_pub.add_argument('--space', help='飞书目标知识库名（wikis 默认取工程名）')
    p_pub.add_argument('--title', help='标题（默认取文件名）')
    p_pub.add_argument('--tags', nargs='*', help='抖音话题标签')
    p_pub.add_argument('--cover', help='公众号封面图路径')

    p_init = sub.add_parser('init', parents=[common], help='建齐资产库目录骨架')
    p_init.add_argument('--no-gitkeep', action='store_true', help='不写 .gitkeep 占位文件')

    sub.add_parser('spaces', parents=[common], help='列出 FEISHU_WIKI_SPACES 解析结果')

    args = parser.parse_args()
    store = AssetStore(root=args.root)
    ok = True

    if args.action == 'ls':
        items = store.list(type_=args.type_, project=args.project, status=args.status)
        if args.json:
            print(json.dumps({'assets': items, 'total': len(items)},
                             ensure_ascii=False, indent=2))
        else:
            if not items:
                print('资产库为空')
            for it in items:
                rel = os.path.relpath(it['path'], store.root)
                meta = it.get('meta')
                extra = f" → {meta['url']}" if meta and meta.get('url') else ''
                print(f"  [{it['status']:<9}] {it['type']}"
                      + (f"/{it['project']}" if it.get('project') else '')
                      + f"  {rel}{extra}")
        ok = True

    elif args.action == 'put':
        content = args.content
        if args.content_file:
            with open(args.content_file, 'r', encoding='utf-8') as f:
                content = f.read()
        r = store.put(args.type_, args.name, content=content, src=args.src,
                      project=args.project, status=args.status)
        ok = r['success']
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        elif not ok:
            print(f"❌ {r['error']}")

    elif args.action == 'publish':
        r = _publish_one(store, args)
        ok = r['success']
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        else:
            print(f"✅ 发布成功: {r.get('url', '')}" if ok else f"❌ {r.get('error')}")

    elif args.action == 'init':
        r = store.ensure_layout(gitkeep=not args.no_gitkeep)
        if args.json:
            print(json.dumps(r, ensure_ascii=False, indent=2))
        elif not r['created']:
            print(f"资产库骨架已就绪（{len(r['existing'])} 个目录，无事可做）")
        else:
            print(f"✅ 新建 {len(r['created'])} 个目录：")
            for rel in r['created']:
                print(f"   + {rel}")
            if r['existing']:
                print(f"   （已有 {len(r['existing'])} 个目录保持不变）")
        ok = True

    elif args.action == 'spaces':
        spaces = store.spaces()
        if args.json:
            print(json.dumps({'spaces': spaces}, ensure_ascii=False, indent=2))
        else:
            print('（FEISHU_WIKI_SPACES 未配置）' if not spaces else
                  '\n'.join(f"  {s['name']} → {s['space_id']}" for s in spaces))

    raise SystemExit(0 if ok else 1)


def _publish_one(store, args):
    """发布共用：解析资产 → 按平台调发布器 → 成功自动归档"""
    from publishing.publisher_base import _load_publisher

    path = os.path.abspath(args.file)
    info = store.parse_asset(path)
    platform = getattr(args, 'platform', None) or info['platform']
    if not platform:
        return {'success': False,
                'error': '无法从路径推断平台，请用 --platform 指定'}
    if not os.path.exists(path):
        return {'success': False, 'error': f'资产不存在: {path}'}

    factory = _load_publisher(platform)
    if not factory:
        return {'success': False, 'error': f'未知平台: {platform}'}
    publisher = factory()

    title = args.title or os.path.splitext(os.path.basename(path))[0]
    space = getattr(args, 'space', None) or (
        info['project'] if info['type'] == 'wikis' else None)

    if platform == 'douyin':
        result = publisher.publish_markdown(
            title, '', options={'video': path, 'tags': args.tags or []})
    else:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        options = {}
        if platform == 'feishu':
            if space:
                options['wiki_space'] = space
        if platform == 'wechat':
            options['cover_image'] = args.cover
        result = publisher.publish_markdown(title, content, options=options)

    if result.success:
        store.mark_published(path, url=result.url, asset_id=result.id, title=title)
    return result.to_dict()


if __name__ == '__main__':
    main()
