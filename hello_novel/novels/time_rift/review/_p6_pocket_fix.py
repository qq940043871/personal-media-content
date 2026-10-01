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
    return len(re.findall(r'[\u4e00-\u9fff]', b))

def insert(raw, exp):
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    m = '\n---\n**本章关键点'
    if m in raw:
        return raw.replace(m, '\n' + exp.strip() + '\n' + m, 1)
    return raw.replace('**本章关键点', exp.strip() + '\n\n**本章关键点', 1)

pairs = {
536: '''
他把笔插回围裙口袋。

值班还在继续。

细节还在被写下来。

'''
,
492: '''
人间对照是后来才加的。

ARIA回到十九层时，手写表最下面多了一行，字迹陌生：

「今天我把自己家的表也钉上了。
格式抄的这里。
抄得不像，但我在写。」

周晚晴在旁边用铅笔补了两个字：「像的。」

分离课最终落到地面，是这样：

有人从公共表里抄走格式，钉回自己家。
抄得不像，但有人肯说像。

他者不是教出来的。

他者是：你在别人家的表上，看见了自己的笔迹需求。

需求被满足之后，人还要回来公共表这边，添一笔。

来回，就叫连接。

不来回，叫复印。

ARIA在私人页写：

「分离的困惑·地面结课：
沙地记号线 — 楼道手写表 — 自家钉的新表。
三处都算数。
抄得不像也算数。
说『像的』那个人，尤其算数。」

'''
}
for n, exp in pairs.items():
    p = CH / f'chapter-{n:03d}.md'
    raw = p.read_text(encoding='utf-8')
    raw2 = insert(raw, exp)
    p.write_text(raw2, encoding='utf-8')
    print(f'ch{n}: {body_cjk(raw2)}')
