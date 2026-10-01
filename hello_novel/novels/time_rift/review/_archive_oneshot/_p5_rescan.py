# -*- coding: utf-8 -*-
import re
from pathlib import Path

dirp = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
keys = ["时光倒流","19层","周晚晴","47区","观察窗","配电箱","电梯","监察","手写表","林晓实验室","打烊"]
dup_markers = [
    "走廊布告栏的灯箱还亮着",
    "楼梯转角的配电箱门虚掩着",
    "公告栏玻璃反着光",
    "电梯口的检修单夹在门缝里",
    "小巷深处的木牌在风里轻晃",
    "墙上的观察窗旁贴着手写表",
    "林晓实验室的全息屏还亮着",
    "监察联署的空白签字栏摊在桌上",
]

rows = []
for n in range(481, 601):
    f = dirp / f"chapter-{n:03d}.md"
    text = f.read_text(encoding="utf-8")
    body = re.sub(r"^#[^\n]*\n", "", text, count=1)
    body = re.sub(r"(?s)\n---\n\*\*本章关键点：\*\*.*$", "", body)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
    dlg = len(re.findall(r'"[^"]+"', body)) + len(re.findall(r"[\u201c][^\u201d]+[\u201d]", body))
    hits = sum(body.count(k) for k in keys)
    dups = sum(1 for m in dup_markers if m in body)
    DialogK = round(dlg * 1000 / cjk, 2) if cjk else 0
    CityK = round(hits * 1000 / cjk, 2) if cjk else 0
    has_footer = "**本章关键点：**" in text
    asset = "A" if (530 <= n <= 540 or n == 600) else ""
    rows.append((n, cjk, dlg, DialogK, hits, CityK, dups, has_footer, asset))

print("total", len(rows))
print("DialogK<8", sum(1 for r in rows if r[3] < 8))
print("CityK<1", sum(1 for r in rows if r[5] < 1))
print("City hits=0", sum(1 for r in rows if r[4] == 0))
print("dup_insert>=1", sum(1 for r in rows if r[6] >= 1))
print("missing footer", sum(1 for r in rows if not r[7]))
print("--- lowest DialogK ---")
for r in sorted(rows, key=lambda x: x[3])[:30]:
    print(r)
print("--- priority sample ---")
for n in [597, 590, 598, 599, 595, 530, 555, 589, 596, 528, 488, 538, 565, 529, 532, 482, 517, 592, 594, 600, 534, 539]:
    r = next(x for x in rows if x[0] == n)
    print(r)
print("--- CityK>=1 count ---")
print(sum(1 for r in rows if r[5] >= 1))
print("--- DialogK>=8 count ---")
print(sum(1 for r in rows if r[3] >= 8))
