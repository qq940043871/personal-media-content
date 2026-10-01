# -*- coding: utf-8 -*-
"""P4 · 悬崖B：121–300 章 CJK / dash 扫描（修正：footer 只认 本章关键点）"""
import re
from pathlib import Path

CH = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
CJK = re.compile(r"[\u4e00-\u9fff]")

def body_cjk(text: str) -> int:
    lines = text.splitlines()
    body_lines = []
    for ln in lines:
        # skip title
        if re.match(r"^#\s*第\d+章", ln):
            continue
        # footer starts at 本章关键点
        if "本章关键点" in ln:
            break
        body_lines.append(ln)
    return len(CJK.findall("\n".join(body_lines)))

def dash_count(text: str) -> int:
    # only count —— in body (not --- separators); strip footer
    idx = text.find("**本章关键点")
    body = text[:idx] if idx >= 0 else text
    # remove markdown --- lines
    body = re.sub(r"^\s*---\s*$", "", body, flags=re.M)
    return len(re.findall(r"——", body))

def title_of(text: str) -> str:
    m = re.search(r"^#\s*第(\d+)章\s*(.+)$", text, re.M)
    return m.group(2).strip() if m else "?"

rows = []
for i in range(121, 301):
    p = CH / f"chapter-{i:03d}.md"
    if not p.exists():
        rows.append((i, -1, -1, "MISSING", False))
        continue
    t = p.read_text(encoding="utf-8")
    cjk = body_cjk(t)
    d = dash_count(t)
    foot = "**本章关键点" in t
    rows.append((i, cjk, d, title_of(t), foot))

rows.sort(key=lambda r: r[1] if r[1] >= 0 else 99999)
print(f"{'ch':>4} {'cjk':>5} {'dash':>4}  foot title")
for i, cjk, d, title, foot in rows:
    flag = ""
    if cjk >= 0 and cjk < 5000:
        flag += " SHORT"
    if d > 8:
        flag += " DASH"
    if not foot:
        flag += " NOFOOT"
    print(f"{i:4d} {cjk:5d} {d:4d}  {'Y' if foot else 'N'} {title}{flag}")

short = [(i,cjk,d,title,foot) for i,cjk,d,title,foot in rows if 0 <= cjk < 5000]
print(f"\n--- SHORT (<5000) count={len(short)} ---")
# parent priority list
prio = [281,177,293,300,289,219,202,286,295,143,296,271,267,297,285,241,221,210,215,216,
222,228,229,232,233,236,237,126,123,121,124,128,134,148,156,157,158,161,169,172,178,186,194,199,205,214,273,275,279,284,287,291,299]
print("parent prio counts:")
for i in prio:
    r = next((r for r in rows if r[0]==i), None)
    if r:
        print(f"  {i}: cjk={r[1]} dash={r[2]} foot={r[4]} {r[3]}")

print("\nshortest 30:")
for i,cjk,d,title,foot in short[:30]:
    print(f"  {i:4d} {cjk:5d} dash={d} {title}")

print("\n--- DASH>8 ---")
for i,cjk,d,title,foot in rows:
    if d > 8:
        print(f"  {i:4d} {cjk:5d} dash={d} {title}")
