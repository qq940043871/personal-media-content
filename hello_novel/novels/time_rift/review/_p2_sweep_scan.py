# -*- coding: utf-8 -*-
"""Vol1 (1-60) mechanical sweep + typo scan + remaining dash contexts."""
from pathlib import Path
import re

root = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

PATTERNS = {
    "的的(非目的的)": re.compile(r"(?<!目)的的"),
    "目的的": re.compile(r"目的的"),
    "意识的的问题": re.compile(r"意识的的问题"),
    "意识的的": re.compile(r"意识的的"),
    "赵远航": re.compile(r"赵远航"),
    "旧时光": re.compile(r"旧时光"),
    "AR IA/A RIA": re.compile(r"AR\s+IA|A\s+RIA"),
    "meta在第X章": re.compile(r"在第\s*[0-9一二三四五六七八九十百千]+\s*章"),
    "如果话": re.compile(r"如果话"),
    "了了": re.compile(r"(?<!了)了了(?!了)"),
    "双逗号": re.compile(r"，，"),
    "双句号": re.compile(r"。。"),
    "是，某种/一种": re.compile(r"是，(某种|一种|一个|进化)"),
    "不止于": re.compile(r"不止于"),
    "与其纠结": re.compile(r"与其纠结"),
    "林晓霜": re.compile(r"林晓霜"),
    "陈志明": re.compile(r"陈志明"),
}

print("=== Vol1 1-60 pattern scan ===")
findings = {k: [] for k in PATTERNS}
for n in range(1, 61):
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    for name, pat in PATTERNS.items():
        hits = list(pat.finditer(t))
        if hits:
            for h in hits[:5]:
                start = max(0, h.start()-20)
                end = min(len(t), h.end()+20)
                ctx = t[start:end].replace("\n", " ")
                findings[name].append((n, ctx))

for name, items in findings.items():
    if not items:
        print(f"  {name}: CLEAN")
        continue
    print(f"  {name}: {len(items)} hits")
    for n, ctx in items[:8]:
        print(f"    ch{n:03d}: ...{ctx}...")

print("\n=== ch1-15 body dash contexts (full) ===")
for n in range(1, 16):
    p = root / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    body = t.split("本章关键点")[0]
    hits = list(re.finditer(r".{0,15}——.{0,25}", body))
    print(f"\nch{n:03d} count={body.count('——')}")
    for h in hits:
        print("  |", h.group(0).replace("\n"," "))

print("\n=== 340-480 top8 dash contexts ===")
for n in [472, 466, 414, 478, 450, 396, 392, 385]:
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        print(f"ch{n}: MISSING")
        continue
    t = p.read_text(encoding="utf-8")
    body = t.split("本章关键点")[0]
    hits = list(re.finditer(r".{0,12}——.{0,22}", body))
    print(f"\nch{n:03d} count={body.count('——')}")
    for h in hits:
        print("  |", h.group(0).replace("\n"," "))
