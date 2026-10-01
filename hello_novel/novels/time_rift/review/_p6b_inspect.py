# -*- coding: utf-8 -*-
from pathlib import Path
base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
for n in [543, 544, 545, 574, 575, 577, 578, 580]:
    p = base / ("chapter-%d.md" % n)
    raw = p.read_text(encoding="utf-8")
    lines = raw.splitlines()
    print("=== ch%d lines=%d bytes=%d ===" % (n, len(lines), len(raw.encode('utf-8'))))
    print("HEAD:", raw[:180].replace("\n", " | "))
    print("TAIL:", raw[-250:].replace("\n", " | "))
    print("foot", "**本章关键点：**" in raw, "dash_count_char", raw.count("\u2014"))
    print()
