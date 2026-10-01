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

def insert(raw, exp):
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    m = '\n---\n**本章关键点'
    if m in raw:
        return raw.replace(m, '\n' + exp.strip() + '\n' + m, 1)
    return raw.replace('**本章关键点', exp.strip() + '\n\n**本章关键点', 1)

raw = (CH / 'chapter-594.md').read_text(encoding='utf-8')
if raw.startswith('\ufeff'):
    raw = raw[1:]
for i, l in enumerate(raw.splitlines()):
    if '初心咖啡' in l:
        print('594 L%d: %s' % (i + 1, l[:120]))

exp496 = '''
单页后来被人翻拍传到市民群里。

群里有人问：这是官方通稿吗？

回答的人说：不是。是有人钉的。

又有人问：谁钉的？

回答：不知道。钉子比作者重要。

ARIA没有认领作者身份。

认领会把「谁钉的」变成新闻点。

不认领，钉子才是钉子。

五百章之后，城市不需要更多作者。

城市需要更多不署名也肯钉的人。

钉完转身，把名字留给路。

'''
exp517 = '''
发呆课结束那天，教官没有总结发言。

他只发了一张空白明信片，说：写给一个月后的自己。

可以写，也可以不写。

交上来的明信片里，有一半是空的。

空的那半，教官也收进箱子，写了标签：

「空也是回复。」

箱子放在训练中心储物间，不展示。

展示会让空变得有压力。

不展示，空才真的是空。

和平的尾巴，常常是一只不展示的箱子。

箱子里有字，也有空。

两种都在，才算完整。

'''
for n, exp in [(496, exp496), (517, exp517)]:
    p = CH / 'chapter-%03d.md' % n
    raw = p.read_text(encoding='utf-8')
    raw2 = insert(raw, exp)
    p.write_text(raw2, encoding='utf-8')
    cjk, dash = body_cjk(raw2)
    flag = 'OK' if cjk >= 5000 and dash <= 8 else 'FAIL'
    print('ch%d: %d/%d %s' % (n, cjk, dash, flag))

print('---481-540---')
bad = []
for n in range(481, 541):
    raw = (CH / 'chapter-%03d.md' % n).read_text(encoding='utf-8')
    cjk, dash = body_cjk(raw)
    if cjk < 5000 or dash > 8:
        bad.append((n, cjk, dash))
print('bad', bad if bad else 'NONE')

print('---pool---')
POOL = [524,502,487,522,501,486,490,503,537,516,507,523,515,529,498,514,492,543,493,533,578,535,575,539,536,504,530,513,518,534,509,544,577,511,574,545,580,489,525,538]
ok = 0
fails = []
for n in POOL:
    raw = (CH / 'chapter-%03d.md' % n).read_text(encoding='utf-8')
    cjk, dash = body_cjk(raw)
    if cjk >= 5000 and dash <= 8 and '本章关键点' in raw:
        ok += 1
    else:
        fails.append((n, cjk, dash))
print('pool %d/40 fails=%s' % (ok, fails))
