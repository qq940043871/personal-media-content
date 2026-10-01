# -*- coding: utf-8 -*-
from pathlib import Path
import re

base = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')
targets = [355, 370, 376, 377, 405, 416, 426, 427, 428, 434]
print('=== BATCH5 FINAL ===')
all_ok = True
for n in targets:
    t = (base / f'chapter-{n:03d}.md').read_text(encoding='utf-8')
    parts = re.split(r'\n---\n\s*\*\*本章关键点', t, maxsplit=1)
    body = parts[0]
    bl = body.split('\n')
    if bl and bl[0].startswith('#'):
        body = '\n'.join(bl[1:])
    cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
    dash = len(re.findall(r'——', body))
    nab = len(re.findall(r'不是[^。\n]{0,30}——而[是像]', body))
    title = t.splitlines()[0]
    footer = '**本章关键点：**' in t
    issues = []
    if cjk < 5000:
        issues.append('cjk=%s' % cjk)
        all_ok = False
    if dash > 8:
        issues.append('dash=%s' % dash)
    if nab > 2:
        issues.append('nab=%s' % nab)
    if not title.startswith('# 第%d章' % n):
        issues.append('title')
        all_ok = False
    if not footer:
        issues.append('footer')
        all_ok = False
    if '赵远航' in t:
        issues.append('ghost')
    if '旧时光' in t:
        issues.append('cafe')
    if re.search(r'第[一二三四五六七八九十百零\d]+章', body):
        issues.append('meta')
    if '预期寿命' in body:
        issues.append('life')
    label = issues[0] if issues else 'OK'
    print(n, title[:24], 'cjk=%s dash=%s' % (cjk, dash), label)

print('all_ok', all_ok)

t426 = (base / 'chapter-426.md').read_text(encoding='utf-8')
for m in re.finditer(r'.{0,15}十九年.{0,15}', t426):
    print('426 arm:', m.group())

t416 = (base / 'chapter-416.md').read_text(encoding='utf-8')
for m in re.finditer(r'.{0,15}十九年.{0,15}', t416):
    print('416 arm:', m.group())
