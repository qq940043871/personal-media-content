# -*- coding: utf-8 -*-
from pathlib import Path
import re

CHDIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
fixed = 0
for p in sorted(CHDIR.glob("chapter-*.md")):
    t = p.read_text(encoding="utf-8")
    new = re.sub(r"\n---\s*\n\s*\n---\s*\n(\*\*本章关键点)", r"\n---\n\1", t)
    new = re.sub(r"\n---\s*\n(\*\*本章关键点)", r"\n---\n\1", new)  # normalize
    # collapse any remaining multiple --- immediately before footer
    new = re.sub(r"(?:\n---\s*){2,}\n(\*\*本章关键点)", r"\n---\n\1", new)
    if new != t:
        p.write_text(new, encoding="utf-8")
        fixed += 1
        print("fixed", p.name)
print("total", fixed)

# recheck
for n in [142, 168]:
    t = (CHDIR / f"chapter-{n:03d}.md").read_text(encoding="utf-8")
    print(n, "double_hr" if re.search(r"\n---\s*\n\s*\n---\s*\n\*\*本章关键点", t) else "OK")
    # show footer head
    m = re.search(r".{0,40}\*\*本章关键点[：:]?\*\*", t)
    print(" ", m.group(0).replace("\n", "|") if m else None)
