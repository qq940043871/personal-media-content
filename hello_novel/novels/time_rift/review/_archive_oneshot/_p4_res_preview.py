# -*- coding: utf-8 -*-
"""Show residual chapter structure: title, last 80 lines before boiler, boiler size, footer."""
import sys, re, os
sys.path.insert(0, r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review')
from _p4_polish_lib import read_ch, cjk_count, dash_count, has_footer, BOILER_START

IDS = [345, 354, 357, 359, 361, 368, 371, 373, 374, 375, 425, 449]

for n in IDS:
    t = read_ch(n)
    lines = t.splitlines()
    title = lines[0] if lines else '?'
    m = BOILER_START.search(t)
    fm = re.search(r'\n---\n\s*\*\*本章关键点', t)
    print('=' * 70)
    print(f'n={n} {title}')
    print(f'cjk={cjk_count(t)} dash={dash_count(t)} foot={has_footer(t)}')
    if m and fm:
        boiler_cjk = len(re.findall(r'[\u4e00-\u9fff]', t[m.start():fm.start()]))
        print(f'boiler_chars={boiler_cjk} boiler_lines={t[m.start():fm.start()].count(chr(10))+1}')
        head = t[:m.start()].rstrip()
        head_lines = head.splitlines()
        print('--- LAST 25 LINES BEFORE BOILER ---')
        for line in head_lines[-25:]:
            print(line)
        print('--- BOILER FIRST 3 LINES ---')
        for line in t[m.start():fm.start()].splitlines()[:3]:
            print(line[:120])
        print('--- FOOTER ---')
        print(t[fm.start():fm.start()+400])
    else:
        print(f'NO_BOILER m={bool(m)} fm={bool(fm)}')
        print('--- LAST 15 LINES ---')
        for line in lines[-15:]:
            print(line[:120])
    print()
