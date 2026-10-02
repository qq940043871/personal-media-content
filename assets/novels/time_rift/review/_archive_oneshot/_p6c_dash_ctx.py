# -*- coding: utf-8 -*-
"""Extract dash contexts from chapters 481-600 with body dash>8."""
import re
from pathlib import Path

CHAPTERS = Path(__file__).resolve().parents[1] / "novel" / "chapters"
FOOTER_MARK = "**本章关键点"

def body_text(t: str) -> str:
    t = t.lstrip("\ufeff")
    idx = t.find(FOOTER_MARK)
    if idx >= 0:
        # walk back to ---
        chunk = t[:idx]
        m = re.search(r"\n---\s*$", chunk)
        if m:
            return chunk[: m.start()]
        return chunk
    return t

over = [481,483,485,488,489,491,494,497,512,521,528,531,532,535,
        541,542,546,553,555,560,563,565,568,569,570,573,579,
        584,585,586,587,594,595,596,599]

out_lines = []
for i in over:
    p = CHAPTERS / f"chapter-{i:03d}.md"
    body = body_text(p.read_text(encoding="utf-8"))
    positions = []
    idx = 0
    while True:
        pos = body.find("——", idx)
        if pos < 0:
            break
        positions.append(pos)
        idx = pos + 2
    out_lines.append(f"\n{'='*60}")
    out_lines.append(f"CH {i}  dash={len(positions)}")
    for n, pos in enumerate(positions, 1):
        before = body[max(0, pos-28):pos]
        after = body[pos+2:pos+2+32]
        out_lines.append(f"  [{n:02d}] …{before}——{after}…")

print("\n".join(out_lines))
