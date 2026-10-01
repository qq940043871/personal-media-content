# -*- coding: utf-8 -*-
"""P6 batch1 verify: full pool + 481-540 remaining shorts + dash + canon."""
from pathlib import Path
import re

CH = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')

POOL = [524,502,487,522,501,486,490,503,537,516,507,523,515,529,498,514,492,543,493,533,578,535,575,539,536,504,530,513,518,534,509,544,577,511,574,545,580,489,525,538]
ASSET = set(range(530, 541)) | {600}

def metrics(n):
    p = CH / f'chapter-{n:03d}.md'
    if not p.exists():
        return None
    raw = p.read_text(encoding='utf-8')
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    lines = raw.splitlines()
    body_lines = []
    in_footer = False
    title = lines[0] if lines else ''
    for i, line in enumerate(lines):
        if i == 0 and line.strip().startswith('#'):
            continue
        if '本章关键点' in line:
            in_footer = True
        if in_footer:
            continue
        body_lines.append(line)
    body = '\n'.join(body_lines)
    cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
    dash = body.count('——')
    has_footer = '本章关键点' in raw
    banned = []
    for w in ['张远', '赵远航', '陈远桥', '初心咖啡']:
        if w in body:
            banned.append(w)
    # 2082 cafe first-meet (allow non-cafe 2082)
    if '2082' in body and ('咖啡' in body or '时光倒流' in body):
        if re.search(r'2082[^。\n]{0,20}(遇|初|咖啡|见面)', body):
            banned.append('2082-cafe')
    return dict(ch=n, cjk=cjk, dash=dash, footer=has_footer, banned=banned, title=title[:40])

print('=== POOL GATE ===')
pool_short = []
pool_dash = []
pool_banned = []
pool_ok = 0
for n in POOL:
    m = metrics(n)
    if not m:
        print(f'ch{n} MISSING')
        continue
    flags = []
    if m['cjk'] < 5000:
        flags.append('SHORT')
        pool_short.append((n, m['cjk']))
    if m['dash'] > 8:
        flags.append('DASH')
        pool_dash.append((n, m['dash']))
    if m['banned']:
        flags.append('BAN:'+','.join(m['banned']))
        pool_banned.append((n, m['banned']))
    if not m['footer']:
        flags.append('NOFOOT')
    if m['cjk'] >= 5000 and m['dash'] <= 8 and m['footer'] and not m['banned']:
        pool_ok += 1
        status = 'OK'
    else:
        status = ' '.join(flags) if flags else '?'
    mark = '*' if n in ASSET else ' '
    print(f"{mark}ch{n}: CJK={m['cjk']} dash={m['dash']} {status} {m['title']}")

print(f'\nPool gate ok: {pool_ok}/{len(POOL)}')
print(f'Pool short: {pool_short}')
print(f'Pool dash>8: {pool_dash}')
print(f'Pool banned: {pool_banned}')

print('\n=== 481-540 remaining CJK<5000 ===')
remain = []
for n in range(481, 541):
    m = metrics(n)
    if m and m['cjk'] < 5000:
        remain.append((n, m['cjk'], m['dash'], m['title']))
print(f'count={len(remain)}')
for n,c,d,t in remain:
    print(f'  ch{n}: CJK={c} dash={d} {t}')

print('\n=== 481-540 dash>8 ===')
for n in range(481, 541):
    m = metrics(n)
    if m and m['dash'] > 8:
        print(f'  ch{n}: dash={m["dash"]} CJK={m["cjk"]} {m["title"]}')

print('\n=== 541-600 pool-related ===')
for n in [578,575,535,539,536,544,577,511,574,545,580]:
    m = metrics(n)
    print(f"  ch{n}: CJK={m['cjk']} dash={m['dash']} {m['title']}")
