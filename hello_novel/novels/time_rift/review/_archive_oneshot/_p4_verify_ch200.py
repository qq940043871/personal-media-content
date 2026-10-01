# -*- coding: utf-8 -*-
import re
from pathlib import Path

CH = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
CJK = re.compile(r"[\u4e00-\u9fff]")

def body_cjk(text):
    lines = []
    for ln in text.splitlines():
        if re.match(r"^#\s*第\d+章", ln):
            continue
        if "本章关键点" in ln:
            break
        lines.append(ln)
    return len(CJK.findall("\n".join(lines)))

def dash_count(text):
    idx = text.find("**本章关键点")
    body = text[:idx] if idx >= 0 else text
    body = re.sub(r"^\s*---\s*$", "", body, flags=re.M)
    return len(re.findall(r"——", body))

for i in [200]:
    p = CH / f"chapter-{i:03d}.md"
    t = p.read_text(encoding="utf-8")
    print(f"ch{i}: cjk={body_cjk(t)} dash={dash_count(t)} foot={'**本章关键点' in t}")
    print(t.splitlines()[0])
