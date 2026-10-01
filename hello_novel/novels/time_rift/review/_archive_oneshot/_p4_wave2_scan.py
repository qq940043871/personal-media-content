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

def title_of(text):
    t = text.lstrip("\ufeff")
    m = re.search(r"^#\s*第(\d+)章\s*(.+)$", t, re.M)
    if m:
        return m.group(0).strip(), m.group(2).strip()
    m = re.search(r"第(\d+)章[^\n]*", t)
    return (m.group(0).strip() if m else "?"), (m.group(0) if m else "?")

targets = [
    200, 271, 296, 267, 273, 216, 241, 178, 221, 210, 215, 161, 284,
    121, 126, 156, 214, 279, 287, 128, 291, 134, 172, 229, 228, 123,
    232, 157, 124, 186, 222, 236, 199, 233, 237, 169, 194, 158, 205,
    299, 148, 280,
]

for i in targets:
    p = CH / f"chapter-{i:03d}.md"
    if not p.exists():
        print(f"{i}: MISSING")
        continue
    raw = p.read_text(encoding="utf-8")
    t = raw.lstrip("\ufeff")
    title, name = title_of(t)
    cjk = body_cjk(raw)
    idx = t.find("**本章关键点")
    body_src = t[:idx] if idx >= 0 else t
    body_src = re.sub(r"^\s*---\s*$", "", body_src, flags=re.M)
    dash = len(re.findall(r"——", body_src))
    body = []
    for ln in t.splitlines():
        if re.match(r"^#\s*第\d+章", ln):
            continue
        if "本章关键点" in ln:
            break
        if ln.strip():
            body.append(ln.strip()[:70])
        if len(body) >= 2:
            break
    print(f"{i:3d} cjk={cjk:4d} dash={dash} | {title}")
    print(f"     {body[0] if body else '(empty)'}")
