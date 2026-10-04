# -*- coding: utf-8 -*-
import re
from pathlib import Path
base = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')
targets = [355,370,376,377,405,416,426,427,428,434]
done = {316,340,342,350,351,352,383,386,411,412,415,417,418,424,443,448,
433,429,469,437,479,462,419,464,465,431,
343,353,356,360,366,367,369,372,390,393,395,402,403,406,407,409,422,423,430,439,441,458,466,476}

def body_of(t):
    parts = re.split(r'\n---\n\s*\*\*本章关键点', t, maxsplit=1)
    body = parts[0]
    bl = body.split('\n')
    if bl and bl[0].startswith('#'):
        body = '\n'.join(bl[1:])
    return body

print('=== TARGET VERIFY ===')
for n in targets:
    p = base / f'chapter-{n:03d}.md'
    t = p.read_text(encoding='utf-8')
    title = t.splitlines()[0]
    footer = '**本章关键点：**' in t
    body = body_of(t)
    cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
    dash_pairs = len(re.findall(r'——', body))
    nab = len(re.findall(r'不是[^。\n]{0,30}——而[是像]', body))
    meta = re.findall(r'第[一二三四五六七八九十百零\d]+章', t)
    # meta in title ok; body meta not
    body_meta = re.findall(r'第[一二三四五六七八九十百零\d]+章', body)
    issues = []
    if not title.startswith(f'# 第{n}章'): issues.append('title')
    if not footer: issues.append('no_footer')
    if cjk < 5000: issues.append(f'cjk={cjk}')
    if dash_pairs > 8: issues.append(f'dash={dash_pairs}')
    if nab > 2: issues.append(f'nab={nab}')
    if body_meta: issues.append(f'meta={body_meta}')
    if '赵远航' in t: issues.append('ghost_name')
    if '旧时光' in t: issues.append('old_cafe')
    if '十九年' in body: issues.append('19y')
    if '预期寿命' in body: issues.append('life_exp')
    print(f'{n}: {title[:30]} cjk={cjk} dash={dash_pairs} nab={nab} issues={issues or ["OK"]}')

print()
print('=== REMAINING <5000 not in done/target ===')
remain = []
for n in range(340, 481):
    if n in done or n in targets:
        continue
    p = base / f'chapter-{n:03d}.md'
    if not p.exists():
        continue
    t = p.read_text(encoding='utf-8')
    body = body_of(t)
    cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
    if cjk < 5000:
        remain.append((n, cjk))
remain.sort(key=lambda x: x[1])
for n, c in remain:
    print(f'{n}: {c}')
print('count', len(remain))
