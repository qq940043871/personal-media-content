#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan chapters for literal backslash-1 placeholders."""
import re
from pathlib import Path
from collections import Counter

BASE = Path(r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/chapters")
TOKEN = "\\1"  # literal \1 two chars

def main():
    counts = {}
    samples = []
    total = 0
    for f in sorted(BASE.glob("chapter-*.md")):
        t = f.read_text(encoding="utf-8")
        n = t.count(TOKEN)
        if n:
            counts[f.name] = n
            total += n
            for m in re.finditer(re.escape(TOKEN), t):
                start = max(0, m.start() - 60)
                end = min(len(t), m.end() + 60)
                ctx = t[start:end].replace("\n", " ")
                before = t[max(0, m.start()-8):m.start()]
                after = t[m.end():min(len(t), m.end()+8)]
                samples.append((f.name, m.start(), before, after, ctx))

    print(f"TOTAL: {total}")
    print(f"CHAPTERS: {len(counts)}")
    print("--- per chapter ---")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"{k}: {v}")

    print("\n--- pattern analysis ---")
    pat = Counter()
    for fn, pos, before, after, ctx in samples:
        key = (before[-4:] if before else "", after[:4] if after else "")
        pat[key] += 1
    for k, v in pat.most_common(50):
        print(f"{v:4d}  before={repr(k[0])} after={repr(k[1])}")

    print("\n--- sample contexts (up to 80) ---")
    for i, (fn, pos, before, after, ctx) in enumerate(samples[:80]):
        print(f"[{i}] {fn} @{pos}")
        print(f"    {ctx}")

if __name__ == "__main__":
    main()
