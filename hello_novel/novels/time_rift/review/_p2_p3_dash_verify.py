# -*- coding: utf-8 -*-
import re
from pathlib import Path

CHAPTERS = Path(__file__).resolve().parents[1] / "novel" / "chapters"

print("=== FINAL 340-480 dash>=10 ===")
any_ge10 = False
for i in range(340, 481):
    p = CHAPTERS / f"chapter-{i:03d}.md"
    if not p.exists():
        continue
    n = len(re.findall("——", p.read_text(encoding="utf-8")))
    if n >= 10:
        print(i, n)
        any_ge10 = True
if not any_ge10:
    print("(none)")

print("\n=== polished final ===")
total_b = 0
total_a = 0
# before values from task scan
before = {346:10,347:14,363:14,365:15,369:13,393:10,397:10,398:11,400:12,420:14,444:11,454:13,457:10,459:12,475:10}
for i in sorted(before):
    n = len(re.findall("——", (CHAPTERS / f"chapter-{i:03d}.md").read_text(encoding="utf-8")))
    total_b += before[i]
    total_a += n
    print(f"  {i}: {before[i]} -> {n}")
print(f"  TOTAL: {total_b} -> {total_a}")

print("\n=== mechanical residual book-wide ===")
all_ch = list(CHAPTERS.glob("chapter-*.md"))


def scan(label, fn):
    hits = []
    for p in all_ch:
        t = p.read_text(encoding="utf-8")
        c = fn(t)
        if c:
            hits.append((p.name, c))
    print(f"{label}: {hits if hits else 'CLEAN'}")


scan("bs1", lambda t: len(re.findall(r"\\1", t)))
scan("yqsn_or_brsn", lambda t: t.count("与其说那是") + t.count("不如说那是"))
scan("zhyh", lambda t: t.count("赵远航"))
scan("aria_sp", lambda t: len(re.findall(r"AR\s+IA|A\s+RIA", t)))
scan("ysdd", lambda t: t.count("意识的的问题"))
scan(
    "jsg_nonneg",
    lambda t: sum(
        1
        for m in re.finditer(r".{0,6}旧时光", t)
        if not re.search(r"不是|并非|非", m.group(0))
    ),
)

print("\n=== excluded chapters dash ===")
for i in [316,340,342,350,351,352,383,386,411,412,415,417,418,424,443,448,433,429,437,469,479,462,419,464,465,431]:
    p = CHAPTERS / f"chapter-{i:03d}.md"
    if p.exists():
        n = len(re.findall("——", p.read_text(encoding="utf-8")))
        print(f"  {i}: {n}")
