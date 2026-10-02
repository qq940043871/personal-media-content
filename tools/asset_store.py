"""
资产库（AssetStore）— tools 发布工具的共享数据契约

回答两个问题：**有什么待发**（list drafts）、**发去哪了**（published + meta.json）。
所有发布类 skills 的输入输出都落在 assets/，技能之间无隐藏状态。

目录结构（根默认 <仓库>/assets，可用 .env 的 ASSETS_BASE 覆盖）：

    assets/
      wechat/{drafts,published}/          # 公众号
      douyin/{drafts,published}/          # 抖音
      feishu/<知识库名>/{drafts,published}/  # 按知识库分（名称来自 FEISHU_WIKI_SPACES）
      novels/<书名>/{drafts,published}/      # 每本小说一个资产文件夹（衍生资产）

状态流转：
    drafts/ → 发布成功 → published/ + 同名 <文件名>.meta.json
    （meta: platform/space/title/url/id/published_at/source）

用法：
    from tools.asset_store import AssetStore
    store = AssetStore()

    store.put('wechat', '文章标题.md', content='# 正文')     # 写入 drafts
    store.list(platform='wechat')                            # 资产清单（含状态）
    store.parse_asset(path)                                  # {'platform','space','status','file'}
    store.mark_published(path, url='...', asset_id='...')    # 归档 + sidecar
    store.ensure_layout()                                    # 幂等建齐目录骨架 + .gitkeep

独立命令行：
    python -m tools.asset_store init                         # 建齐骨架（feishu 按知识库、novels 按书名）
    python -m tools.asset_store ls [--platform wechat] [--status drafts] [--json]
    python -m tools.asset_store put --platform wechat --name x.md --content-file y.md
    python -m tools.asset_store spaces --json                # FEISHU_WIKI_SPACES 解析结果
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

# 平台 → 资产文件夹（feishu/novels 下还有一层 space/书名）
PLATFORM_DIRS = ('wechat', 'douyin', 'feishu', 'novels')
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

    def put(self, platform, name, content=None, src=None,
            space=None, status=STATUS_DRAFT):
        """
        写入一个资产（正文内容或源文件拷贝）

        Args:
            platform: wechat / douyin / feishu / novels
            name: 资产文件名（如 '文章标题.md' 或 '成片.mp4'）
            content: 文本内容（与 src 二选一）
            src: 源文件路径（拷贝进资产库，如视频/图片）
            space: 二级文件夹（feishu 的知识库名 / novels 的书名）
            status: drafts（默认）或 published

        Returns:
            dict: {'success', 'path', 'platform', 'space', 'status'}
        """
        try:
            target_dir = self._dir(platform, space, status, create=True)
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
                'platform': platform, 'space': space, 'status': status}

    # ===== 查询 =====

    def list(self, platform=None, space=None, status=None):
        """
        资产清单（含 meta 信息）；platform/space/status 均可作过滤

        状态目录可能直接在平台下（wechat/douyin），也可能隔一层
        知识库/书名文件夹（feishu/<库>/、novels/<书>/），两种布局都遍历。

        Returns:
            list[dict]: {'platform','space','status','file','path','size',
                         'updated_at_str', 'meta'(已发布的带)}
        """
        platforms = [platform] if platform else list(PLATFORM_DIRS)
        statuses = [status] if status else list(STATUS)
        items = []
        for pf in platforms:
            pf_dir = os.path.join(self.root, pf)
            if not os.path.isdir(pf_dir):
                continue
            for name in sorted(os.listdir(pf_dir)):
                full = os.path.join(pf_dir, name)
                if not os.path.isdir(full):
                    continue
                if name in STATUS:
                    self._collect(pf, None, name, full, statuses, items)
                elif space is None or name == space:
                    # 隔一层知识库/书名文件夹的布局
                    for sub in sorted(os.listdir(full)):
                        subfull = os.path.join(full, sub)
                        if os.path.isdir(subfull) and sub in STATUS:
                            self._collect(pf, name, sub, subfull, statuses, items)
        return items

    def _collect(self, platform, space, status, status_dir, statuses, items):
        if status not in statuses:
            return
        for name in sorted(os.listdir(status_dir)):
            path = os.path.join(status_dir, name)
            if (not os.path.isfile(path) or name.startswith('.')
                    or name.endswith(META_SUFFIX)):
                continue
            item = {
                'platform': platform,
                'space': space,
                'status': status,
                'file': name,
                'path': path,
                'size': os.path.getsize(path),
                'updated_at_str': datetime.fromtimestamp(
                    os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M'),
            }
            if status == STATUS_PUBLISHED:
                item['meta'] = self._read_meta(path)
            items.append(item)

    def parse_asset(self, path):
        """
        解析资产路径 → {'platform','space','status','file','rel'}

        识别两种布局：platform/space/status/file（feishu、novels）
        与 platform/status/file（wechat、douyin）；
        不在资产库内时 platform=''、status=''、space=None。
        """
        abs_path = os.path.abspath(path)
        try:
            rel = os.path.relpath(abs_path, self.root)
        except ValueError:
            rel = abs_path
        norm = rel.replace('\\', '/')
        parts = norm.split('/')
        info = {'platform': '', 'space': None, 'status': '',
                'file': os.path.basename(abs_path), 'rel': norm}

        if parts[0] in PLATFORM_DIRS and len(parts) >= 2:
            info['platform'] = parts[0]
            rest = parts[1:]                       # [space?, status, file] 或 [status, file]
            if len(rest) >= 2 and rest[-2] in STATUS:
                info['status'] = rest[-2]
                if len(rest) == 3:
                    info['space'] = rest[0]
                elif len(rest) > 3:
                    info['space'] = '/'.join(rest[:-2])
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
        if info['status'] == STATUS_PUBLISHED:
            return {'success': False, 'error': f'资产已是发布状态: {src}'}

        try:
            target_dir = self._dir(info['platform'], info['space'],
                                   STATUS_PUBLISHED, create=True)
        except AssetError as e:
            return {'success': False, 'error': str(e)}

        target = os.path.join(target_dir, info['file'])
        if os.path.exists(target):
            return {'success': False, 'error': f'已发布区同名文件冲突: {target}'}

        shutil.move(src, target)

        meta = {
            'platform': info['platform'] or '',
            'space': info['space'],
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
        建齐资产库骨架：平台 × 状态目录（feishu 按知识库、novels 按书名多一层）

        - wechat / douyin：各一个资产文件夹，下分 drafts/ published/
        - feishu：FEISHU_WIKI_SPACES 里每个知识库名一个文件夹；未配置时回落一个占位目录
        - novels：每本小说（含 chapters/ 的目录）一个文件夹，下分 drafts/ published/

        Args:
            gitkeep: 空目录写 .gitkeep（git 不跟踪空目录；.gitkeep 不参与资产清单）
            spaces: 覆盖知识库名列表（默认读 FEISHU_WIKI_SPACES）
            books: 覆盖书目列表（默认自动识别）

        Returns:
            dict: {'root', 'created': [...], 'existing': [...]}（相对资产库根的路径）
        """
        created, existing = [], []
        for pf in PLATFORM_DIRS:
            if pf == 'feishu':
                names = spaces if spaces is not None else \
                    ([s['name'] for s in self.spaces()] or [DEFAULT_FEISHU_SPACE])
            elif pf == 'novels':
                names = books if books is not None else self.books()
            else:
                names = [None]

            for space in names:
                for status in STATUS:
                    directory = self._dir(pf, space, status, create=False)
                    rel = os.path.relpath(directory, self.root).replace('\\', '/')
                    existed = os.path.isdir(directory)
                    os.makedirs(directory, exist_ok=True)
                    (existing if existed else created).append(rel)
                    if gitkeep:
                        keep = os.path.join(directory, GITKEEP)
                        if not os.path.exists(keep):
                            with open(keep, 'w', encoding='utf-8') as f:
                                f.write('')
        return {'root': self.root, 'created': created, 'existing': existing}

    # ===== 内部 =====

    def _dir(self, platform, space, status, create=False):
        if platform not in PLATFORM_DIRS:
            raise AssetError(f'未知平台文件夹: {platform}（可选: {", ".join(PLATFORM_DIRS)}）')
        if status not in STATUS:
            raise AssetError(f'未知状态: {status}（可选: {", ".join(STATUS)}）')
        path = os.path.join(self.root, platform)
        if space:
            path = os.path.join(path, space)
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
        prog='python -m tools.asset_store', description='待发布资产库管理')
    parser.add_argument('--root', help='资产库根目录（默认 <仓库>/assets）')
    sub = parser.add_subparsers(dest='action', required=True)

    p_ls = sub.add_parser('ls', parents=[common], help='资产清单')
    p_ls.add_argument('--platform', choices=PLATFORM_DIRS, help='按平台过滤')
    p_ls.add_argument('--space', help='按知识库/书名过滤')
    p_ls.add_argument('--status', choices=STATUS, help='按状态过滤')

    p_put = sub.add_parser('put', parents=[common], help='写入资产（默认进 drafts）')
    p_put.add_argument('--platform', choices=PLATFORM_DIRS, required=True)
    p_put.add_argument('--name', required=True, help='资产文件名')
    p_put.add_argument('--content', help='文本内容')
    p_put.add_argument('--content-file', help='从文件读取内容')
    p_put.add_argument('--src', help='源文件路径（视频/图片等直接拷贝）')
    p_put.add_argument('--space', help='二级文件夹（feishu 知识库名 / novels 书名）')
    p_put.add_argument('--status', choices=STATUS, default=STATUS_DRAFT)

    p_pub = sub.add_parser('publish', parents=[common], help='发布一个 drafts 资产（调对应平台发布器，成功自动归档）')
    p_pub.add_argument('--file', required=True, help='资产文件路径')
    p_pub.add_argument('--platform', choices=('feishu', 'wechat', 'douyin'),
                       help='目标平台（默认从路径推断）')
    p_pub.add_argument('--space', help='飞书目标知识库名（默认从路径推断）')
    p_pub.add_argument('--title', help='标题（默认取文件名）')
    p_pub.add_argument('--tags', nargs='*', help='抖音话题标签')
    p_pub.add_argument('--cover', help='公众号封面图路径')

    p_init = sub.add_parser('init', parents=[common], help='建齐资产库目录骨架（平台×草稿/已发布）')
    p_init.add_argument('--no-gitkeep', action='store_true', help='不写 .gitkeep 占位文件')

    sub.add_parser('spaces', parents=[common], help='列出 FEISHU_WIKI_SPACES 解析结果')

    args = parser.parse_args()
    store = AssetStore(root=args.root)
    ok = True

    if args.action == 'ls':
        items = store.list(platform=args.platform, space=args.space, status=args.status)
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
                print(f"  [{it['status']:<9}] {it['platform']}"
                      + (f"/{it['space']}" if it.get('space') else '')
                      + f"  {rel}{extra}")
        ok = True

    elif args.action == 'put':
        content = args.content
        if args.content_file:
            with open(args.content_file, 'r', encoding='utf-8') as f:
                content = f.read()
        r = store.put(args.platform, args.name, content=content, src=args.src,
                      space=args.space, status=args.status)
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
    """ls/put/publish 共用：按平台调对应发布器并归档"""
    from tools.publisher_base import _load_publisher

    path = os.path.abspath(args.file)
    info = store.parse_asset(path)
    platform = args.platform or info['platform']
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
    space = args.space or info['space']

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
