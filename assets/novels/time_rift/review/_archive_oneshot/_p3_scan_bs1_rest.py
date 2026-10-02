#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump remaining \1 contexts not yet sampled."""
import re
from pathlib import Path

BASE = Path(r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/chapters")
TOKEN = "\\1"

def main():
    samples = []
    for f in sorted(BASE.glob("chapter-*.md")):
        t = f.read_text(encoding="utf-8")
        if TOKEN not in t:
            continue
        for m in re.finditer(re.escape(TOKEN), t):
            start = max(0, m.start() - 80)
            end = min(len(t), m.end() + 80)
            ctx = t[start:end].replace("\n", " | ")
            samples.append((f.name, m.start(), ctx))

    print(f"TOTAL samples: {len(samples)}")
    # print from index 80 onward
    for i, (fn, pos, ctx) in enumerate(samples):
        if i < 80:
            continue
        print(f"[{i}] {fn} @{pos}")
        print(f"    {ctx}")

if __name__ == "__main__":
    main()
