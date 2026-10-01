# -*- coding: utf-8 -*-
import os, re
base = r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters'
focus = [378,379,380,381,382,384,385,387,389,391,394,397,398,399,401,404,408,410,421,432,436,438,444,445,447,451,455,461,463,467,468,472,473,477,478]
deepish = [413,414,453,466,475,476]
boiler_markers = [
    '本章后续执行按',
    '对地镜像与失败账制度继续有效',
    '对应的现场补充',
    '执行夜班交接时',
    '复盘小组最后补记',
    '补充验收段落',
    '数字台账',
    '结尾钩子保持打开',
]
print('ch  cjk  boil dash fp  title')
for n in focus + deepish:
    p = os.path.join(base, 'chapter-%03d.md' % n)
    if not os.path.exists(p):
        print(n, 'MISSING')
        continue
    t = open(p, encoding='utf-8').read()
    body = re.sub(r'^# 第\d+章[^\n]*\n?', '', t)
    body_main = re.split(r'\n---\n\s*\*\*本章关键点', body)[0]
    cjk = len(re.findall(r'[\u4e00-\u9fff]', body_main))
    dash = body_main.count('——')
    fp = '**本章关键点' in t
    boil = sum(1 for m in boiler_markers if m in t)
    m = re.search(r'^# 第\d+章\s*(.+)$', t, re.M)
    title = m.group(1) if m else '?'
    print('%3d %5d %4d %4d %s  %s' % (n, cjk, boil, dash, 'Y' if fp else 'N', title))
