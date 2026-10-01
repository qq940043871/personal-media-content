# -*- coding: utf-8 -*-
from pathlib import Path
import re
CH = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')

def show(n, keywords):
    p = CH / f'chapter-{n:03d}.md'
    raw = p.read_text(encoding='utf-8')
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    lines = raw.splitlines()
    print('='*40, n)
    foot_idx = [i for i,l in enumerate(lines) if '本章关键点' in l]
    print('footer lines:', [i+1 for i in foot_idx])
    print('total lines', len(lines), 'file bytes', p.stat().st_size)
    for kw in keywords:
        idxs = [i+1 for i,l in enumerate(lines) if kw in l]
        print(f'  {kw!r} at lines', idxs[:8])
    # print last 25 lines
    print('TAIL:')
    for l in lines[-25:]:
        print('  ', l[:90])
    print('AFTER first footer?')
    if foot_idx:
        after = lines[foot_idx[0]:]
        cjk = len(re.findall(r'[\u4e00-\u9fff]', '\n'.join(after)))
        print('  CJK after first footer marker', cjk)

for n, kws in [
    (536, ['服务员', '记账', '烤箱', '镇流器', '擦坏角', '人话库', '手套', '舱盖']),
    (534, ['铅笔', '2078', '验证栏', '边界', '三代', '火种']),
    (492, ['店长', '他者', '分离', '小圆']),
    (539, ['绿萝', '观察窗', '老何', '灯']),
    (538, ['陈悦', '值班', '刘师傅', '旁听']),
    (489, ['周晚晴', '慢光', '镇流器', '退开']),
    (533, ['陈悦', '第七格', '清单']),
]:
    show(n, kws)
