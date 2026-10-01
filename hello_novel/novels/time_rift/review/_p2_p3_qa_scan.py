# -*- coding: utf-8 -*-
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
chapters = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
    21, 30, 33, 55, 60,
    340, 342, 348, 349, 351, 388, 399, 440, 448, 452, 453, 473,
]
issues_pat = [
    ("bs1", re.compile(r"(?<![0-9A-Za-z])\\1")),
    ("double_punct", re.compile(r"，，|。。|！！|？？")),
    ("dash_comma", re.compile(r"——，")),
    ("zzyh", re.compile("赵远航")),
    ("oldcafe", re.compile("旧时光")),
    ("lele", re.compile("了了")),
    ("chen_ming_bare", re.compile(r"陈明(?!远|志)")),
    ("comma_ellip_period", re.compile(r"，…+。|，……。")),
    ("broken_dialog", re.compile(r'"[^"\n]{0,40}，…+。?')),
]

for n in chapters:
    p = base / f"chapter-{n:03d}.md"
    if not p.exists():
        print(f"ch{n:03d}: MISSING")
        continue
    t = p.read_text(encoding="utf-8")
    d = t.count("——")
    found = []
    for name, pat in issues_pat:
        for m in pat.finditer(t):
            s = max(0, m.start() - 30)
            e = min(len(t), m.end() + 30)
            ctx = t[s:e].replace("\n", " ")
            found.append(f"{name}:{ctx}")
    for i, ln in enumerate(t.splitlines(), 1):
        if re.search(r"[0-9]：[0-9]{2}，\s*$", ln):
            found.append(f"L{i} time-comma:{ln[-50:]}")
        if re.search(r"^\s*\"[^\"]*，…+", ln):
            found.append(f"L{i} broken-dialog:{ln[:70]}")
    print(f"ch{n:03d}: dash={d} issues={len(found)}")
    for f in found[:10]:
        print("   ", f)
