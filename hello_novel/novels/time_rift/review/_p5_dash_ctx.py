# -*- coding: utf-8 -*-
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
dash_chs = [301, 302, 304, 305, 307, 313, 314, 317, 321, 323, 324, 331, 332, 335, 336, 337, 338]
short_chs = [302, 303, 306, 308, 313, 314, 317, 318, 319, 320, 321, 322, 325, 329, 336]

def body_of(raw):
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    lines = raw.splitlines()
    footer_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^---\s*$", line):
            after = "\n".join(lines[i+1:])
            if "本章关键点" in after or "本章围绕" in after:
                footer_idx = i
    body_lines = []
    for i, line in enumerate(lines):
        if footer_idx is not None and i >= footer_idx:
            break
        if i == 0 and line.startswith("# "):
            continue
        body_lines.append(line)
    return "\n".join(body_lines), lines, footer_idx

# dash contexts
print("=" * 60)
print("DASH CONTEXTS")
print("=" * 60)
for n in dash_chs:
    p = base / ("chapter-%d.md" % n)
    raw = p.read_text(encoding="utf-8")
    body, lines, fi = body_of(raw)
    count = body.count("——")
    print("\n### ch%d  dash=%d" % (n, count))
    # split into sentences/segments around ——
    # find all occurrences with context
    idx = 0
    k = 0
    while True:
        pos = body.find("——", idx)
        if pos < 0:
            break
        k += 1
        start = max(0, pos - 40)
        end = min(len(body), pos + 42)
        ctx = body[start:end].replace("\n", "⏎")
        print("  [%02d] %s" % (k, ctx))
        idx = pos + 2

# footer generic check
print("\n" + "=" * 60)
print("FOOTER GENERIC CHECK 301-340")
print("=" * 60)
generic_bits = [
    "机械臂读数", "连接税个人账", "ARIA瞳孔", "禁写纯蓝",
    "相关公开口径暂不升格", "本章围绕", "本批", "破折号",
    "第%d章",
]
for n in range(301, 341):
    p = base / ("chapter-%d.md" % n)
    raw = p.read_text(encoding="utf-8")
    _, lines, fi = body_of(raw)
    footer = "\n".join(lines[fi:]) if fi is not None else ""
    issues = []
    for g in generic_bits[:-1]:
        if g in footer:
            issues.append(g)
    if re.search(r"第\d+章\s+\S+\s*$", footer, re.M):
        issues.append("meta-title")
    if "ARIA" in footer and "机械臂" in footer:
        issues.append("ARIA+机械臂同现")
    if issues:
        print("ch%d: %s" % (n, issues))
        for fl in footer.splitlines():
            if fl.strip():
                print("   " + fl[:120])
print("(scan done)")
