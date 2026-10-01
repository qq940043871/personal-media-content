# -*- coding: utf-8 -*-
"""Count dashes in trial package 1-15 and 340-480."""
from pathlib import Path
import re

root = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

def dash_count(p: Path) -> int:
    t = p.read_text(encoding="utf-8")
    body = t.split("本章关键点")[0] if "本章关键点" in t else t
    return body.count("——")

print("=== trial 1-15 ===")
for n in range(1, 16):
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        print(f"{n:03d}: MISSING")
        continue
    d = dash_count(p)
    print(f"{n:03d}: {d}")

print("\n=== 340-480 dash>=10 (excluding 316/340) ===")
rows = []
for n in range(340, 481):
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        continue
    if n in (316, 340):
        d = dash_count(p)
        print(f"  skip ch{n}: {d}")
        continue
    d = dash_count(p)
    if d >= 10:
        rows.append((d, n))
rows.sort(reverse=True)
for d, n in rows:
    print(f"  ch{n:03d}: {d}")
print(f"total >=10 in 340-480: {len(rows)}")
print(f"top8: {rows[:8]}")
