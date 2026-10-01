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

exp536 = '''
登记本的备注栏不够宽，管理员把「细节：舱边软垫」写成了两行。

第二行只剩一个字：「垫。」

垫。

一个字的备注，比半页报告更像人在值班。

ARIA没有让他改成标准句。

标准句留给需要归档的人。

值班的人只需要记下：今晚有一双手，垫着开了舱盖。

'''
exp492 = '''
ARIA在撤出源梦空间之前，教了孩子一个很笨的办法。

「下次你分不清『分开了』还是『变样了』的时候，」她说，「不要一直盯着它们看。看久了，你会把自己的害怕投进去。」

「那看什么？」

「看你还愿不愿意再画一道记号线。」

孩子低头看了看沙地上那道淡线。

「如果不愿意呢？」

「那说明你已经准备让它们走。」ARIA说，「走也是答案。」

「如果愿意呢？」

「愿意，就说明你还把它们放在心上。」她说，「放在心上不等于必须绑住。」

孩子把这句话消化了很久。它用手指在两个点之间又轻轻描了一次线，描完之后做了一件新的事：在线的中点放了一粒很小的沙。

沙不是桥，不是锁。

沙只是：这里我停过。

「停过？」孩子用波问。

「对。」ARIA说，「路过和停过不一样。路过是擦肩，停过是承认这段距离值得被标一下。」

她撤出源梦空间的时候，孩子还在沙地上做记号。

一个点，一道线，一粒沙。

重复了很多次。

像有人在反复练习：怎样分开，才不算丢。

回到物理层之后，李明问她这一趟教了什么。

「教它害怕的时候先看自己还愿不愿意画线。」

「这不解决分离。」

「不解决。」她说，「分离不需要被解决。分离需要被标记得体面一点。」

「体面给谁看？」

「给以后回看的人。」她说，「也给正在分开的两边。」

李明点点头，没有再问。

有些课不产生结论。

有些课只产生：有人在沙地上停过一回。

停过，就不算白怕。

'''
for n, exp in [(536, exp536), (492, exp492)]:
    p = CH / f'chapter-{n:03d}.md'
    raw = p.read_text(encoding='utf-8')
    raw2 = insert(raw, exp)
    p.write_text(raw2, encoding='utf-8')
    cjk, dash = body_cjk(raw2)
    flag = 'OK' if cjk >= 5000 and dash <= 8 else 'FAIL'
    print(f'ch{n}: {cjk} dash={dash} {flag}')
