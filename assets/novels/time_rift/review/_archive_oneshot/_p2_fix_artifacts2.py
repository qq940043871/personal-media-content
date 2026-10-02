# -*- coding: utf-8 -*-
"""Correct over-eager 关键不在是否因为; fix 不如说那是 / 关键不在因为 in Vol1 1-60."""
from pathlib import Path
import re

root = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

print("=== fix Vol1 artifacts ===")
log = []
for n in range(1, 61):
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    orig = t
    # repair bad 是否因为 inserts (3 places we introduced)
    t = t.replace("关键不在是否因为", "关键不在因为")
    # natural: 不如说那是 → 不如说是
    t = t.replace("不如说那是", "不如说是")
    # natural: 关键不在因为X，而在因为Y → 关键不在X，而在Y
    t = re.sub(r"关键不在因为([^，。！？\n]{1,24})，而在因为", r"关键不在\1，而在", t)
    t = re.sub(r"关键不在因为([^，。！？\n]{1,24})，不是因为([^，。！？\n]{1,24})，而在因为", r"关键不在\1，也不是\2，而在", t)
    if t != orig:
        notes = []
        if "关键不在是否因为" in orig:
            notes.append("revert-是否因为")
        if "不如说那是" in orig:
            notes.append(f"不如说那是x{orig.count('不如说那是')}")
        if re.search(r"关键不在因为", orig):
            notes.append(f"关键不在因为x{len(re.findall(r'关键不在因为', orig))}")
        p.write_text(t, encoding="utf-8")
        log.append((n, notes))
print("changed:", log)

print("\n=== re-verify trial 1-15 mechanical ===")
for n in range(1, 16):
    p = root / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    body = t.split("本章关键点")[0]
    issues = []
    for pat, name in [
        ("与其说那是", "与其说那是"),
        ("不如说那是", "不如说那是"),
        ("关键不在是否因为", "是否因为"),
        ("如果话", "如果话"),
        ("，，", "双逗号"),
        ("赵远航", "赵远航"),
        ("AR IA", "ARIA"),
    ]:
        if pat in t:
            issues.append(name)
    print(f"  {n:03d}: dash={body.count('——')} log={'循环日志' in t} {issues or 'OK'}")

print("\n=== final dash table ===")
print("trial 1-15:")
vals = []
for n in range(1, 16):
    p = root / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    body = t.split("本章关键点")[0]
    d = body.count("——")
    vals.append(f"{n:03d}:{d}")
print(" ".join(vals))
print("340-480 top8:")
vals2 = []
for n in [472, 466, 414, 478, 450, 396, 392, 385]:
    p = root / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    body = t.split("本章关键点")[0]
    d = body.count("——")
    vals2.append(f"{n:03d}:{d}")
print(" ".join(vals2))

print("\n=== Vol1 residual after this pass ===")
patterns = {
    "与其说那是": "与其说那是",
    "不如说那是": "不如说那是",
    "关键不在因为": "关键不在因为",
    "目的外的的": r"(?<!目)的的",
    "赵远航": "赵远航",
    "旧时光": "旧时光",
    "AR IA": r"AR\s+IA|A\s+RIA",
    "meta章": r"在第\s*[0-9一二三四五六七八九十百千]+\s*章",
}
for n in range(1, 61):
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    for name, pat in patterns.items():
        if name in ("目的外的的", "AR IA", "meta章"):
            if re.search(pat, t):
                print(f"  ch{n:03d} {name}: {re.findall(pat, t)[:3]}")
        else:
            c = t.count(pat)
            if c:
                print(f"  ch{n:03d} {name}: {c}")
print("done")
