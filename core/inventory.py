"""
内容资产盘点 — 工作台「创作统计」的数据源

回答的问题：创作类多少本小说、编写类多少篇待发/已发资产、多少视频稿、发布过多少次。
纯文件系统 + 本地库读取，不触网、不依赖任何生产线代码。

统计口径（2026-10 内容资产迁入 assets/ 后）：
- 小说：assets/novels/<书>/{chapters, novel/chapters} 下的 .txt/.md 正文
       （两代目录布局都认；README 等说明文件不计）
- 主题/文集：assets/novels/<主题>/ 下的 .md（亲情视频脚本、写作指南等；不含章节目录的子目录）
- 资产：assets/ 待发布资产库，按文件夹内容自动盘点——遍历各创作域下的 <工程>/drafts|published，
       状态目录里散文件各计 1 篇、技能线的 <篇名>/ 工作区文件夹计 1 篇（按主文件计字数）；
       .gitkeep、.meta.json 与隐藏文件不计；兼容旧版平铺（wechat|douyin/<状态>/、feishu/<库>/<状态>/）
       路径规则见 publishing/asset_store.py
- 成片：system/storage/videos_output/<项目> 子目录（成片原件不入库，本机为准）
- 发布：system/storage/db/feishu_published.json（小说批量发飞书幂等记录）
       + projects.db 发布记录（工作台/后续产线写入）

使用方式：
    from core.inventory import ContentInventory
    inv = ContentInventory()
    inv.summary()   # 一次拿全量，dashboard /api/inventory 直接返回
"""

import os
import json
import time
from datetime import datetime

from .config import config

NOVEL_CHAPTER_DIRS = ('chapters', 'novel/chapters')
CHAPTER_EXTS = ('.txt', '.md')
SKIP_PREFIXES = ('README', 'readme')

NOVELS_ROOT = os.path.join('assets', 'novels')
ANALYSES_DIR = os.path.join('hello_weixin_book', 'analyses')  # 2026-10 已迁出（personal-read-book），恒为 0
ASSET_STATUSES = ('drafts', 'published')
ASSET_TEXT_EXTS = ('.md', '.txt')
META_SUFFIX = '.meta.json'
# 旧版平台平铺目录 → 归并到的创作域（2026-10 前布局，兼容读取）
LEGACY_TYPE_DIRS = {'wechat': 'articles', 'douyin': 'videos', 'feishu': 'wikis'}


def _is_chapter_file(name):
    return (name.lower().endswith(CHAPTER_EXTS)
            and not name.upper().startswith(SKIP_PREFIXES))


class ContentInventory:
    """内容资产盘点器（带 mtime 签名缓存，重复刷新不重读大文件）"""

    def __init__(self, base_dir=None, storage_base=None, assets_base=None,
                 videos_output_dir=None, project_manager=None):
        self.base_dir = base_dir or config.BASE_DIR
        self.storage_base = storage_base or config.STORAGE_BASE
        self.assets_base = assets_base or config.ASSETS_BASE
        # 成片目录默认从 storage 根推导（换 storage 根时全部跟随）
        self.videos_output_dir = videos_output_dir or os.path.join(self.storage_base, 'videos_output')
        self._pm = project_manager
        # {目录: (签名, 统计结果)} —— 目录内容没变就复用上次字数统计
        self._dir_cache = {}

    # ===== 对外 =====

    def summary(self):
        return {
            'novels': self.scan_novels(),
            'assets': self.scan_assets(),
            'analyses_count': self.count_analyses(),
            'family': self.scan_family_scripts(),
            'videos_output': self.count_videos(),
            'publish': self.publish_summary(),
            'generated_at_str': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

    # ===== 小说（创作类）=====

    def scan_novels(self):
        root = os.path.join(self.base_dir, NOVELS_ROOT)
        books = []
        if os.path.isdir(root):
            for name in sorted(os.listdir(root)):
                book_dir = os.path.join(root, name)
                if not os.path.isdir(book_dir):
                    continue
                if not any(os.path.isdir(os.path.join(book_dir, sub))
                           for sub in NOVEL_CHAPTER_DIRS):
                    continue  # 无章节目录 = 主题/文集（scan_family_scripts 统计）
                files = []
                for sub in NOVEL_CHAPTER_DIRS:
                    d = os.path.join(book_dir, sub)
                    if os.path.isdir(d):
                        files += [os.path.join(d, f) for f in os.listdir(d)
                                  if _is_chapter_file(f)]
                stats = self._stat_files(files)
                books.append({
                    'book': name,
                    'chapters': stats['count'],
                    'words': stats['words'],
                    'words_wan': round(stats['words'] / 10000, 1),
                    'updated_at': stats['newest_mtime'],
                    'updated_at_str': (datetime.fromtimestamp(stats['newest_mtime'])
                                       .strftime('%Y-%m-%d') if stats['newest_mtime'] else '-'),
                })
        books.sort(key=lambda b: -b['words'])
        return {
            'total_books': len(books),
            'total_chapters': sum(b['chapters'] for b in books),
            'total_words': sum(b['words'] for b in books),
            'total_words_wan': round(sum(b['words'] for b in books) / 10000, 1),
            'books': books,
        }

    # ===== 资产库（编写类：待发/已发）=====

    def scan_assets(self):
        """
        待发布资产库盘点（assets/，创作域/工程 × drafts/published）— 按文件夹内容自动统计

        识别 assets/ 下任意一层 <工程>/<状态>/ 结构（状态目录 = drafts|published）：
        - 状态目录里的散文件各计 1 篇（.meta.json / 隐藏文件不计）
        - 技能线的 <篇名>/ 工作区文件夹计 1 篇，字数取夹内全部 .md/.txt，主文件取
          夹根下最大的 .md/.txt（如 article.md）；仅含 .gitkeep 等隐藏文件的空夹不计
        - 顶层目录名按创作域归并（旧平铺 wechat→articles、douyin→videos、feishu→wikis，
          其余原样作为域）；wechat/douyin 旧平铺无工程名，不进工程表

        Returns:
            {'total', 'drafts', 'published',
             'types': {创作域: {'drafts', 'published'}},
             'projects': [{type, project, drafts, published, words, updated_at_str}] 按域/工程排序,
             'items': 最近 10 篇明细 {type, project, status, file, words, updated_at_str}}
        """
        result = {'total': 0, 'drafts': 0, 'published': 0,
                  'types': {}, 'projects': [], 'items': []}
        if not os.path.isdir(self.assets_base):
            return result

        items = []
        projects = {}  # (创作域, 工程) → 聚合行

        def scan_dir(type_, project, status_dir):
            st = os.path.basename(os.path.normpath(status_dir))
            for name in sorted(os.listdir(status_dir)):
                if name.startswith('.'):
                    continue
                path = os.path.join(status_dir, name)
                if os.path.isdir(path):
                    main, words, mtime = self._workspace_stats(path)
                    if not mtime:
                        continue  # 无任何内容文件（仅 .gitkeep 等隐藏文件）不计
                    file = f'{name}/{main}' if main else f'{name}/'
                elif name.endswith(META_SUFFIX):
                    continue
                else:
                    words = (self._text_size(path)
                             if name.lower().endswith(ASSET_TEXT_EXTS) else 0)
                    mtime = os.path.getmtime(path)
                    file = name
                items.append({
                    'type': type_, 'project': project, 'status': st,
                    'file': file, 'words': words, '_mtime': mtime,
                    'updated_at_str': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M'),
                })
                tstat = result['types'].setdefault(
                    type_, {'drafts': 0, 'published': 0})
                tstat[st] += 1
                if project:
                    row = projects.setdefault(
                        (type_, project),
                        {'type': type_, 'project': project, 'drafts': 0,
                         'published': 0, 'words': 0, '_mtime': 0})
                    row[st] += 1
                    row['words'] += words
                    row['_mtime'] = max(row['_mtime'], mtime)

        for top in sorted(os.listdir(self.assets_base)):
            tdir = os.path.join(self.assets_base, top)
            if not os.path.isdir(tdir) or top.startswith('.'):
                continue
            type_ = LEGACY_TYPE_DIRS.get(top, top)
            for name in sorted(os.listdir(tdir)):
                if name in ASSET_STATUSES:  # 旧平铺：<平台>/<状态>/文件
                    scan_dir(type_, None, os.path.join(tdir, name))
                    continue
                pdir = os.path.join(tdir, name)
                if not os.path.isdir(pdir) or name.startswith('.'):
                    continue
                for st in ASSET_STATUSES:
                    sdir = os.path.join(pdir, st)
                    if os.path.isdir(sdir):
                        scan_dir(type_, name, sdir)

        result['drafts'] = sum(t['drafts'] for t in result['types'].values())
        result['published'] = sum(t['published'] for t in result['types'].values())
        result['total'] = result['drafts'] + result['published']

        rows = sorted(projects.values(), key=lambda r: (r['type'], r['project']))
        for r in rows:
            r['updated_at_str'] = (datetime.fromtimestamp(r.pop('_mtime'))
                                   .strftime('%Y-%m-%d %H:%M') if r['_mtime'] else '-')
        result['projects'] = rows

        items.sort(key=lambda x: -x['_mtime'])
        for it in items:
            it.pop('_mtime')
        result['items'] = items[:10]
        return result

    def count_analyses(self):
        d = os.path.join(self.base_dir, ANALYSES_DIR)
        if not os.path.isdir(d):
            return 0
        return len([f for f in os.listdir(d) if f.lower().endswith('.html')])

    # ===== 主题/文集（短视频脚本、写作指南等）=====

    def scan_family_scripts(self):
        """
        assets/novels/ 下的「主题/文集」子目录：没有章节目录、但含 .md 的子目录
        （亲情视频脚本主题、guides 写作指南等；含 chapters/novel/chapters 的是小说书目）
        """
        root = os.path.join(self.base_dir, NOVELS_ROOT)
        themes = []
        if os.path.isdir(root):
            for name in sorted(os.listdir(root)):
                tdir = os.path.join(root, name)
                if not os.path.isdir(tdir) or name.startswith('.'):
                    continue
                if any(os.path.isdir(os.path.join(tdir, sub))
                       for sub in NOVEL_CHAPTER_DIRS):
                    continue  # 小说书目
                files = []
                for cur, _dirs, names in os.walk(tdir):
                    files += [n for n in names if n.lower().endswith('.md')]
                if files:
                    themes.append({'theme': name, 'files': len(files)})
        return {
            'themes': len(themes),
            'files': sum(t['files'] for t in themes),
            'detail': themes,
        }

    def count_videos(self):
        if not os.path.isdir(self.videos_output_dir):
            return 0
        return len([n for n in os.listdir(self.videos_output_dir)
                    if os.path.isdir(os.path.join(self.videos_output_dir, n))])

    # ===== 发布记录 =====

    def publish_summary(self):
        feishu_published = self._count_feishu_published()
        records = {'total': 0, 'success': 0, 'failed': 0, 'running': 0}
        try:
            pm = self._pm or self._make_pm()
            records.update({k: v for k, v in pm.stats().get('publish', {}).items()
                            if k in records})
        except Exception:
            pass
        return {'feishu_published': feishu_published, 'records': records}

    # ===== 内部 =====

    def _workspace_stats(self, folder):
        """工作区文件夹 → (主文件名, 正文字数, 最新 mtime)；无内容文件返回 ('', 0, 0)"""
        main, main_size, words, newest = '', -1, 0, 0
        for cur, _dirs, files in os.walk(folder):
            for f in files:
                if f.startswith('.') or f.endswith(META_SUFFIX):
                    continue
                fp = os.path.join(cur, f)
                try:
                    mtime = os.path.getmtime(fp)
                except OSError:
                    continue
                newest = max(newest, mtime)
                if f.lower().endswith(ASSET_TEXT_EXTS):
                    size = self._text_size(fp)
                    words += size
                    # 主文件取夹根下最大的 .md/.txt（如 article.md），只看一层
                    if cur == folder and size > main_size:
                        main, main_size = f, size
        return main, words, int(newest)

    def _text_size(self, path):
        return len(self._read(path))

    def _make_pm(self):
        from .project_manager import ProjectManager
        self._pm = ProjectManager()
        return self._pm

    def _count_feishu_published(self):
        """novel_publisher 的幂等记录（JSON：list 或 dict 均按条目数计）"""
        path = os.path.join(self.storage_base, 'db', 'feishu_published.json')
        if not os.path.exists(path):
            return 0
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return len(data) if hasattr(data, '__len__') else 0
        except Exception:
            return 0

    def _stat_files(self, files):
        """带缓存的批量字数统计；签名 = (文件数, 最新 mtime)"""
        existing = [f for f in files if os.path.exists(f)]
        if not existing:
            return {'count': 0, 'words': 0, 'newest_mtime': 0}
        signature = (len(existing), max(os.path.getmtime(f) for f in existing))
        key = os.path.dirname(existing[0]) + ':' + str(len(existing))
        cached = self._dir_cache.get(key)
        if cached and cached[0] == signature:
            return cached[1]
        words = sum(len(self._read(f)) for f in existing)
        result = {'count': len(existing), 'words': words,
                  'newest_mtime': int(signature[1])}
        self._dir_cache[key] = (signature, result)
        return result

    @staticmethod
    def _read(path):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except OSError:
            return ''
