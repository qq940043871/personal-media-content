# -*- coding: utf-8 -*-
"""Convert P5-added corner brackets to ASCII quotes in 481-600; report stats."""
import re
from pathlib import Path

dirp = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
changed = []
for n in range(481, 601):
    f = dirp / f"chapter-{n:03d}.md"
    text = f.read_text(encoding="utf-8")
    # Only convert full-width corner quotes that wrap dialogue-like spans
    new = re.sub(r"「([^」]+)」", r'"\1"', text)
    if new != text:
        f.write_text(new, encoding="utf-8")
        changed.append(n)
print("quote_converted", len(changed))
print(changed)
