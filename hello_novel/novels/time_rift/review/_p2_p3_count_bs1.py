# -*- coding: utf-8 -*-
from pathlib import Path
import re
base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
total = 0
chs = []
for n in range(1, 601):
    p = base / f"chapter-{n:03d}.md"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    c = len(re.findall(r"(?<![0-9A-Za-z])\\1", t))
    if c:
        total += c
        chs.append((n, c))
print("global remaining \\1:", total, "in", len(chs), "chapters")
print("top:", sorted(chs, key=lambda x: -x[1])[:20])
# also raw count of backslash+1 two-char
raw = 0
raw_chs = []
for n in range(1, 601):
    p = base / f"chapter-{n:03d}.md"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    if "\\1" in t:
        raw += t.count("\\1")
        raw_chs.append(n)
print("raw \\\\1 string count:", raw, "chapters sample:", raw_chs[:20])
