# -*- coding: utf-8 -*-
from pathlib import Path
import re
CH = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')

def body_cjk(raw):
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    lines = raw.splitlines()
    body=[]; in_f=False
    for i,l in enumerate(lines):
        if i==0 and l.strip().startswith('#'): continue
        if '本章关键点' in l: in_f=True
        if in_f: continue
        body.append(l)
    b='\n'.join(body)
    return len(re.findall(r'[\u4e00-\u9fff]', b)), b.count('——')

# final gate summary
POOL=[524,502,487,522,501,486,490,503,537,516,507,523,515,529,498,514,492,543,493,533,578,535,575,539,536,504,530,513,518,534,509,544,577,511,574,545,580,489,525,538]
ok=0
for n in POOL:
    raw=(CH/('chapter-%03d.md'%n)).read_text(encoding='utf-8')
    cjk,dash=body_cjk(raw)
    assert cjk>=5000 and dash<=8 and '本章关键点' in raw, (n,cjk,dash)
    ok+=1
print('pool asserts passed', ok)

# 481-540
for n in range(481,541):
    raw=(CH/('chapter-%03d.md'%n)).read_text(encoding='utf-8')
    cjk,dash=body_cjk(raw)
    assert cjk>=5000 and dash<=8, (n,cjk,dash)
print('481-540 asserts passed')

# asset peaks still present
checks={
530:['时间之海','白瓷碗','永远记得'],
531:['陈维远','追悼','让电'],
534:['2078','传承','验证栏'],
538:['中心','当下'],
539:['起源','终结'],
540:['继续存在','跳盖'],
}
for n,words in checks.items():
    raw=(CH/('chapter-%03d.md'%n)).read_text(encoding='utf-8')
    missing=[w for w in words if w not in raw]
    print('asset',n,'missing',missing if missing else 'none')

# banned in body 481-540
for n in range(481,541):
    raw=(CH/('chapter-%03d.md'%n)).read_text(encoding='utf-8')
    if raw.startswith('\ufeff'): raw=raw[1:]
    lines=raw.splitlines(); body=[]; in_f=False
    for i,l in enumerate(lines):
        if i==0 and l.strip().startswith('#'): continue
        if '本章关键点' in l: in_f=True
        if in_f: continue
        body.append(l)
    b='\n'.join(body)
    for w in ['张远','赵远航','陈远桥']:
        if w in b:
            print('BANNED BODY', n, w)
print('all final checks done')
