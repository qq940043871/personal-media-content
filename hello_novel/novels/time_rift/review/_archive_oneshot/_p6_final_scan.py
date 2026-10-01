# -*- coding: utf-8 -*-
from pathlib import Path
import re
CH = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')

def body_cjk(raw):
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    lines = raw.splitlines()
    body = []
    in_f = False
    for i, l in enumerate(lines):
        if i == 0 and l.strip().startswith('#'):
            continue
        if '本章关键点' in l:
            in_f = True
        if in_f:
            continue
        body.append(l)
    b = '\n'.join(body)
    return len(re.findall(r'[\u4e00-\u9fff]', b)), b.count('——')

print('=== 481-540 body gate ===')
shorts = []
for n in range(481, 541):
    p = CH / f'chapter-{n:03d}.md'
    if not p.exists():
        print(f'ch{n} MISSING')
        continue
    raw = p.read_text(encoding='utf-8')
    cjk, dash = body_cjk(raw)
    foot = '本章关键点' in raw
    if cjk < 5000 or dash > 8 or not foot:
        shorts.append((n, cjk, dash, foot))
        print(f'ch{n}: CJK={cjk} dash={dash} foot={foot}')
print(f'total need work: {len(shorts)}')

print('\n=== POOL 40 final ===')
POOL = [524,502,487,522,501,486,490,503,537,516,507,523,515,529,498,514,492,543,493,533,578,535,575,539,536,504,530,513,518,534,509,544,577,511,574,545,580,489,525,538]
ok=0
for n in POOL:
    raw = (CH / f'chapter-{n:03d}.md').read_text(encoding='utf-8')
    cjk, dash = body_cjk(raw)
    good = cjk>=5000 and dash<=8 and '本章关键点' in raw
    if good: ok+=1
    else: print(f'  FAIL ch{n}: {cjk}/{dash}')
print(f'pool ok {ok}/{len(POOL)}')

print('\n=== 541-600 pool extras ===')
for n in [578,575,535,539,536,544,577,511,574,545,580,489,525,538,543,545]:
    raw = (CH / f'chapter-{n:03d}.md').read_text(encoding='utf-8')
    cjk, dash = body_cjk(raw)
    print(f'ch{n}: {cjk}/{dash}')
