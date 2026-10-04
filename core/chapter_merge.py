"""
章节合并 — 把短章并成平台连载规格的长章（番茄等平台单章常规 2000-3000 字）

分组规则：
1. 优先按剧情单元边界分组（从 process/5-第N卷-剧情单元.txt 解析【单元N：第X-Y章 主题】），
   绝不跨单元；整单元一组时标题取单元主题
2. 单元内切组：--target 字数目标 > 0 时按字数贪婪累积（凑满即成章，适合源章字数
   不均匀的书）；否则按 ceil(章数/per) 均衡切分
3. 无单元覆盖的章节按固定 per 章兜底分组，标题取组内首章标题
4. 源章的标题行（第N章 xxx）从正文剥离，正文按序拼接；原稿只读不动

用法：
    from core.chapter_merge import merge_chapters
    stats = merge_chapters('assets/novels/平凡人生/chapters',
                           'assets/novels/平凡人生/chapters-番茄版', per=5)

CLI：
    python media-cli.py story merge assets/novels/平凡人生/chapters \
        -o assets/novels/平凡人生/chapters-番茄版 --per 5 [--dry-run]
"""

import glob
import re
from datetime import datetime
from pathlib import Path

UNIT_RE = re.compile(r'【单元(\d+)：第(\d+)-(\d+)章\s*[-—–]*\s*([^\】]*)】')
CH_NUM_RE = re.compile(r'第(\d+)章')
TITLE_LINE_RE = re.compile(r'^第\d+章[\s:：]*')
ILLEGAL_FN_RE = re.compile(r'[\\/:*?"<>|\s]')

DEFAULT_UNIT_GLOB = '5-第*卷-剧情单元.txt'


def merge_chapters(source_dir, out_dir, per=4, target=0, unit_glob=None, dry_run=False):
    """
    合并章节目录（原稿只读）。

    Args:
        source_dir: 源章节目录（文件名含 第N章，.txt/.md）
        out_dir: 输出目录（自动创建）
        per: 每个合并章最多包含的源章数（target 模式下作为章数上限防超长）
        target: 单章字数目标 > 0 时按字数贪婪累积分组（源章字数不均匀时用）
        unit_glob: 剧情单元文件 glob（默认自动找 <source_dir>/../process/ 下的
                   5-第*卷-剧情单元.txt；找不到则退化为固定 per 分组）
        dry_run: 只算分组不写文件

    Returns:
        {'groups': [{num, title, sources, chars}], 'total_chars', 'out_dir'}
    """
    source_dir, out_dir = Path(source_dir), Path(out_dir)
    if not source_dir.is_dir():
        raise FileNotFoundError(f'源章节目录不存在: {source_dir}')
    if per < 1:
        raise ValueError(f'per 须 ≥ 1，收到 {per}')

    # 1. 读源章（章号 → (标题, 正文, 文件名)）；章号优先取文件名，其次正文首行
    chapters = {}
    for f in sorted(list(source_dir.glob('*.txt')) + list(source_dir.glob('*.md'))):
        num, title, body = _read_chapter(f)
        if num is None:
            continue
        if num in chapters:
            raise ValueError(f'章号冲突: 第{num}章 同时来自 '
                             f'{chapters[num][2]} 与 {f.name}')
        chapters[num] = (title, body, f.name)
    if not chapters:
        raise FileNotFoundError(f'{source_dir} 下没有可识别章号（第N章）的章节文件')
    nums = sorted(chapters)

    # 2. 分组：单元内按 target 贪婪或按 per 均衡切分 → 兜底固定 per
    groups = []
    covered = set()
    for start, end, theme in _parse_units(source_dir, unit_glob):
        unit_nums = [n for n in nums if start <= n <= end and n not in covered]
        if not unit_nums:
            continue
        split = (_greedy_split(unit_nums, target, per, chapters) if target > 0
                 else _balanced_split(unit_nums, per))
        for grp in split:
            groups.append({'nums': grp, 'theme': theme if len(split) == 1 else None})
            covered.update(grp)
    rest = [n for n in nums if n not in covered]
    for i in range(0, len(rest), per):
        groups.append({'nums': rest[i:i + per], 'theme': None})

    # 3. 生成合并章
    result = []
    for new_num, grp in enumerate(groups, 1):
        first_title = chapters[grp['nums'][0]][0]
        title = grp['theme'] or first_title or f'第{new_num}章'
        body = '\n\n'.join(chapters[n][1] for n in grp['nums'])
        chars = sum(len(chapters[n][1]) for n in grp['nums'])
        result.append({'num': new_num, 'title': title,
                       'sources': grp['nums'], 'chars': chars,
                       'content': f'第{new_num}章 {title}\n\n{body}\n'})

    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        for r in result:
            fname = f"第{r['num']:03d}章-{ILLEGAL_FN_RE.sub('', r['title'])[:40]}.txt"
            (out_dir / fname).write_text(r['content'], encoding='utf-8')
            r['file'] = fname
        _write_manifest(out_dir, result, source_dir, per)
    return {'groups': result,
            'total_chars': sum(r['chars'] for r in result),
            'out_dir': str(out_dir)}


# ===== 内部 =====

def _read_chapter(path):
    """读一章 → (章号, 标题, 正文)；章号优先取文件名，其次正文首行 第N章 前缀"""
    text = path.read_text(encoding='utf-8').strip()
    lines = text.splitlines()
    num = None
    title = ''
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip():
            first = line.strip()
            m = CH_NUM_RE.search(first)
            if m:
                num = int(m.group(1))
                title = TITLE_LINE_RE.sub('', first)
            else:
                title = first
            body_start = i + 1
            break
    body = '\n'.join(lines[body_start:]).strip()
    m = CH_NUM_RE.search(path.name)
    if m:
        num = int(m.group(1))
    return num, title, body


def _parse_units(source_dir, unit_glob):
    """解析剧情单元 → [(start, end, 主题)]；无 unit 文件返回 []"""
    if unit_glob is None:
        probe = source_dir.parent / 'process'
        unit_glob = str(probe / DEFAULT_UNIT_GLOB) if probe.is_dir() else ''
    if not unit_glob:
        return []
    units = []
    for f in sorted(glob.glob(unit_glob)):
        for m in UNIT_RE.finditer(Path(f).read_text(encoding='utf-8')):
            start, end = int(m.group(2)), int(m.group(3))
            theme = m.group(4).strip(' -—–') or f'单元{m.group(1)}'
            units.append((start, end, theme))
    units.sort()
    # 单元重叠校验（同一章被两个单元认领会产生重复分组）
    seen = set()
    for start, end, theme in units:
        dup = seen.intersection(range(start, end + 1))
        if dup:
            raise ValueError(f'剧情单元范围重叠: {theme} 与已覆盖章节 {sorted(dup)[:5]}')
        seen.update(range(start, end + 1))
    return units


def _balanced_split(nums, per):
    """把有序章号切成每组 ≤ per 章且组数最少、组间尽量均衡的分法"""
    g = -(-len(nums) // per)  # ceil
    base, extra = divmod(len(nums), g)
    out, idx = [], 0
    for i in range(g):
        size = base + (1 if i < extra else 0)
        out.append(nums[idx:idx + size])
        idx += size
    return out


def _greedy_split(nums, target, max_per, chapters):
    """字数贪婪分组：累计凑满 target 即成章（末组保底）；max_per 限制单组章数"""
    out, cur, cur_chars = [], [], 0
    for n in nums:
        cur.append(n)
        cur_chars += len(chapters[n][1])
        if len(cur) >= max_per or cur_chars >= target:
            out.append(cur)
            cur, cur_chars = [], 0
    if cur:
        # 尾组太短且能并入前组（不超上限两倍）则回并，避免碎章
        if out and len(out[-1]) + len(cur) <= max_per * 2:
            out[-1].extend(cur)
        else:
            out.append(cur)
    return out


def _write_manifest(out_dir, result, source_dir, per):
    """写合并对照表（新章号 ↔ 源章号，可追溯）"""
    lines = [
        '# 章节合并对照表', '',
        f'- 源目录：`{source_dir}`',
        f'- 生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}',
        f'- 分组规则：剧情单元边界优先，每组 ≤ {per} 章',
        f'- 共 {len(result)} 章 / {sum(r["chars"] for r in result)} 字', '',
        '| 新章 | 标题 | 源章 | 字数 |', '|---|---|---|---|',
    ]
    for r in result:
        lines.append(f"| 第{r['num']}章 | {r['title']} | "
                     f"{r['sources'][0]}-{r['sources'][-1]}（{len(r['sources'])} 章）| "
                     f"{r['chars']} |")
    (out_dir / '合并对照.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
