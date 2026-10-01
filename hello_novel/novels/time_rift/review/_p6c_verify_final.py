# -*- coding: utf-8 -*-
"""Final verify body dash 481-600 (exclude title + footer)."""
import re
from pathlib import Path

CHAPTERS = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

def split_rest(raw):
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    lines = raw.splitlines()
    footer_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^---\s*$", line):
            after = "\n".join(lines[i + 1 :])
            if "本章关键点" in after or "本章围绕" in after:
                footer_idx = i
                break
    body = "\n".join(lines[:footer_idx] if footer_idx is not None else lines)
    bl = body.splitlines()
    title = bl[0] if bl and bl[0].startswith("# ") else ""
    rest = "\n".join(bl[1:] if title else bl)
    return title, rest

over = []
all_counts = {}
for i in range(481, 601):
    p = CHAPTERS / f"chapter-{i:03d}.md"
    if not p.exists():
        print(f"{i}: MISSING")
        continue
    title, rest = split_rest(p.read_text(encoding="utf-8"))
    n = rest.count("——")
    all_counts[i] = n
    if n > 8:
        over.append((i, n))

print("=== FINAL body dash>8 (title+footer excluded) ===")
print(over if over else "NONE — gate PASS (0 chapters >8)")
print(f"max={max(all_counts.values())}  sum={sum(all_counts.values())}  >0={sum(1 for v in all_counts.values() if v>0)}")
print("at threshold 8:", sorted([i for i,v in all_counts.items() if v==8]))
print("ch528:", all_counts.get(528))
print("ch527:", all_counts.get(527))
print("asset 530-540,600:", {i: all_counts.get(i) for i in list(range(530,541))+[600]})
