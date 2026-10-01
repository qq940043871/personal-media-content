# -*- coding: utf-8 -*-
"""P7: scan live chapter titles + body dash for trial pack refresh (1-120)."""
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
banned = re.compile(r"张远|赵远航|陈远桥")
results = []

for i in range(1, 121):
    p = base / f"chapter-{i:03d}.md"
    if not p.exists():
        results.append((i, "MISSING", 0, 0, False, False))
        continue
    text = p.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    title = ""
    body_start = 0
    for idx, line in enumerate(lines[:8]):
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            body_start = idx + 1
            break
    footer_idx = None
    for idx in range(len(lines) - 1, body_start - 1, -1):
        if "**本章关键点" in lines[idx] or "本章关键点" in lines[idx]:
            footer_idx = idx
            break
    if footer_idx is not None:
        end = footer_idx
        for j in range(footer_idx, body_start - 1, -1):
            if lines[j].strip() == "---":
                end = j
                break
        body_lines = lines[body_start:end]
    else:
        body_lines = lines[body_start:]
    body = "\n".join(body_lines)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
    dash = body.count("——")
    has_footer = footer_idx is not None
    banned_hit = bool(banned.search(text))
    results.append((i, title, cjk, dash, has_footer, banned_hit))

out = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review\_p7_scan_result.txt")
with out.open("w", encoding="utf-8") as f:
    f.write("=== 1-60 titles ===\n")
    for i, t, cjk, d, fb, b in results[:60]:
        f.write(f"{i:03d}|{t}|cjk={cjk}|dash={d}|foot={fb}|banned={b}\n")
    f.write("\n=== 61-120 titles ===\n")
    for i, t, cjk, d, fb, b in results[60:120]:
        f.write(f"{i:03d}|{t}|cjk={cjk}|dash={d}|foot={fb}|banned={b}\n")
    f.write("\n=== vol1 dash table 1-15 ===\n")
    f.write(" ".join(f"{i:03d}:{results[i-1][3]}" for i in range(1, 16)) + "\n")
    f.write("\n=== vol2 gate ===\n")
    d8 = [(r[0], r[3]) for r in results[60:120] if r[1] != "MISSING" and r[3] > 8]
    s5 = [(r[0], r[2], r[1]) for r in results[60:120] if r[1] != "MISSING" and r[2] < 5000]
    nf = [r[0] for r in results[60:120] if r[1] != "MISSING" and not r[4]]
    bn = [(r[0], r[1]) for r in results[60:120] if r[5]]
    miss = [r[0] for r in results if r[1] == "MISSING"]
    f.write(f"dash>8: {d8}\n")
    f.write(f"cjk<5000: {s5}\n")
    f.write(f"nofoot: {nf}\n")
    f.write(f"banned: {bn}\n")
    f.write(f"missing: {miss}\n")
    f.write("\n=== key chapters ===\n")
    for key in [8, 12, 71, 75, 82, 83, 84, 96, 100, 102, 105, 108, 109, 112, 120]:
        r = results[key - 1]
        f.write(f"{r[0]:03d} {r[1]} cjk={r[2]} dash={r[3]} foot={r[4]}\n")
    f.write("\n=== vol1 1-60 gate ===\n")
    f.write(f"banned 1-60: {[(r[0], r[1]) for r in results[:60] if r[5]]}\n")
    f.write(f"nofoot 1-60: {[r[0] for r in results[:60] if r[1] != 'MISSING' and not r[4]]}\n")
    f.write(f"dash>3 1-15: {[(r[0], r[3]) for r in results[:15] if r[3] > 3]}\n")
    f.write("\n=== content checks ===\n")
    for i in [1, 3, 5, 8, 10, 12, 75, 112, 120]:
        p = base / f"chapter-{i:03d}.md"
        t = p.read_text(encoding="utf-8-sig")
        f.write(
            f"ch{i:03d} 幽灵={t.count('幽灵')} 赵远山={t.count('赵远山')} "
            f"楚辞={t.count('楚辞')} 时光倒流={t.count('时光倒流')} "
            f"张远={t.count('张远')} 赵远航={t.count('赵远航')} 陈远桥={t.count('陈远桥')}\n"
        )
print(out.read_text(encoding="utf-8"))
