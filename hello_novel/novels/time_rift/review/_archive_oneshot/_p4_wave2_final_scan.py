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

def title_of(text):
    t = text.lstrip("\ufeff")
    m = re.search(r"^#\s*第(\d+)章\s*(.+)$", t, re.M)
    return m.group(2).strip() if m else "?"

forbidden = ["本章后续执行按", "对地镜像", "夜班交接五条", "数字台账", "本章围绕"]

short = []
dashbad = []
nofoot = []
forb = []
for i in range(121, 301):
    p = CH / f"chapter-{i:03d}.md"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    cjk = body_cjk(t)
    d = dash_count(t)
    foot = "**本章关键点" in t
    if cjk < 5000:
        short.append((i, cjk, title_of(t), d))
    if d > 8:
        dashbad.append((i, cjk, d))
    if not foot:
        nofoot.append(i)
    for f in forbidden:
        if f in t:
            forb.append((i, f))
            break

short.sort(key=lambda x: x[1])
print(f"SHORT<5000 count={len(short)}")
for row in short:
    print(f"  {row[0]:3d} cjk={row[1]:4d} dash={row[3]} {row[2]}")
print(f"DASH>8: {dashbad}")
print(f"NOFOOT: {nofoot}")
print(f"FORBIDDEN_TAIL: {forb}")
print(f"ch200 cjk={body_cjk((CH/'chapter-200.md').read_text(encoding='utf-8'))}")
