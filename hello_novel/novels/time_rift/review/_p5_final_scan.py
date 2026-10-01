# -*- coding: utf-8 -*-
import re
from pathlib import Path

dirp = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
keys = ["时光倒流","19层","周晚晴","47区","观察窗","配电箱","电梯","监察","手写表","林晓实验室","打烊"]

# BEFORE baseline (from first correct scan)
before = {
597:0.85,590:1.14,598:1.39,599:1.95,595:1.96,530:2.27,555:2.49,589:2.49,596:3.28,
528:3.91,488:3.92,565:4.09,529:4.24,532:4.66,531:5.74,538:5.20,482:16.11,517:6.91,
592:5.19,594:7.39,600:11.72,534:12.45,539:18.54,
}

rows=[]
for n in range(481,601):
    f=dirp/f"chapter-{n:03d}.md"
    text=f.read_text(encoding="utf-8")
    body=re.sub(r"^#[^\n]*\n","",text,count=1)
    body=re.sub(r"(?s)\n---\n\*\*本章关键点：\*\*.*$","",body)
    # also strip trailing 全书完 markers
    body=re.sub(r"\n---\n（全书完）.*$","",body,flags=re.S)
    cjk=len(re.findall(r"[\u4e00-\u9fff]",body))
    dlg=len(re.findall(r'"[^"]+"',body))
    hits=sum(body.count(k) for k in keys)
    DialogK=round(dlg*1000/cjk,2) if cjk else 0
    CityK=round(hits*1000/cjk,2) if cjk else 0
    asset='ASSET' if (530<=n<=540 or n==600) else ''
    rows.append(dict(n=n,cjk=cjk,dlg=dlg,DialogK=DialogK,hits=hits,CityK=CityK,asset=asset,
                     before=before.get(n)))

print("=== SUMMARY 481-600 AFTER P5 ===")
print("DialogK>=8:", sum(1 for r in rows if r['DialogK']>=8), "/120")
print("DialogK<8:", sum(1 for r in rows if r['DialogK']<8))
print("City hits>=1:", sum(1 for r in rows if r['hits']>=1), "/120")
print("CityK>=1:", sum(1 for r in rows if r['CityK']>=1))
print("missing footer:", sum(1 for n in range(481,601) if "**本章关键点：**" not in (dirp/f"chapter-{n:03d}.md").read_text(encoding='utf-8')))
print()
print("=== PRIORITY BEFORE/AFTER Dialog/K ===")
print(f"{'Ch':>4} {'Before':>8} {'After':>8} {'CJK':>6} {'Dlg':>4} {'CityH':>6} {'CityK':>7} Asset")
for n in [597,590,598,595,530,555,599,589,596,528,488,538,565,529,532,482,517,592,594,600,531,534,539]:
    r=next(x for x in rows if x['n']==n)
    b=r['before'] if r['before'] is not None else float('nan')
    print(f"{n:4d} {b:8.2f} {r['DialogK']:8.2f} {r['cjk']:6d} {r['dlg']:4d} {r['hits']:6d} {r['CityK']:7.2f} {r['asset']}")
print()
print("=== STILL DialogK<8 (lowest 20) ===")
for r in sorted(rows,key=lambda x:x['DialogK'])[:20]:
    print(f"  ch{r['n']}: DialogK={r['DialogK']} dlg={r['dlg']} cjk={r['cjk']} city={r['hits']} {r['asset']}")
print()
print("=== ASSET/END ===")
for r in rows:
    if r['asset']:
        print(f"  ch{r['n']}: DialogK={r['DialogK']} city={r['hits']} before={r['before']}")
