# -*- coding: utf-8 -*-
"""Compare dash counting methods for trial 1-15."""
from pathlib import Path
import re

root = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

print(f"{'ch':>4} {'body——':>7} {'full——':>7} {'body—':>6} {'full—':>6} {'body-':>6} {'——lines':>8}")
for n in range(1, 16):
    p = root / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    body = t.split("本章关键点")[0] if "本章关键点" in t else t
    b2 = body.count("——")
    f2 = t.count("——")
    b1 = body.count("—")  # all em-dashes
    f1 = t.count("—")
    # single hyphen-minus in body (excl. markdown --- separators maybe)
    bh = len(re.findall(r"(?<!—)—(?!—)", body))
    # lines containing ——
    lines = sum(1 for line in body.splitlines() if "——" in line)
    print(f"{n:03d} {b2:7} {f2:7} {b1:6} {f1:6} {bh:6} {lines:8}")

# show sample of dash contexts for high-baseline chapters
print("\n=== sample dash contexts (body) ===")
for n in [3, 5, 7, 8, 9, 12, 13, 14]:
    p = root / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    body = t.split("本章关键点")[0]
    hits = []
    for m in re.finditer(r".{0,12}——.{0,20}", body):
        hits.append(m.group(0).replace("\n", " "))
    print(f"\nch{n:03d} count={body.count('——')} hits={len(hits)}")
    for h in hits[:8]:
        print("  |", h)
