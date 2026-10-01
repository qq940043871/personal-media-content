# -*- coding: utf-8 -*-
from pathlib import Path
import re
CH = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')

def body_cjk(raw):
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    lines = raw.splitlines()
    body_lines = []
    in_footer = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip().startswith('#'):
            continue
        if '本章关键点' in line:
            in_footer = True
        if in_footer:
            continue
        body_lines.append(line)
    body = '\n'.join(body_lines)
    return len(re.findall(r'[\u4e00-\u9fff]', body)), body.count('——')

for n in [536, 534, 492, 487, 539, 538, 533, 489, 511, 515, 516, 507, 523, 493]:
    p = CH / f'chapter-{n:03d}.md'
    raw = p.read_text(encoding='utf-8')
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    cjk, dash = body_cjk(raw)
    print('='*50)
    print(f'CH{n} body_cjk={cjk} dash={dash} file={p.stat().st_size}')
    lines = raw.splitlines()
    print('  HEAD:')
    for line in lines[:5]:
        print('   ', line[:90])
    print('  FOOT-MARK:')
    for i, line in enumerate(lines):
        if '本章关键点' in line:
            print(f'   L{i+1}: {line[:80]}')
            if i >= 2:
                print(f'   prev: {lines[i-2][:80]}')
                print(f'   prev: {lines[i-1][:80]}')
    print('  tails:', 
          '公告栏' if '公告栏玻璃反着光' in raw else '-',
          '配电箱' if '配电箱' in raw else '-',
          '林晓' if '林晓实验室' in raw else '-',
          '木牌' if '木巷' in raw or '小巷深处' in raw else '-')
