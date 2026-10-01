#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import re

base = Path(r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/chapters")
TOKEN = "\\1"
total = 0
for f in sorted(base.glob("chapter-*.md")):
    n = f.read_text(encoding="utf-8").count(TOKEN)
    if n:
        print("RESIDUAL", f.name, n)
        total += n
print("FINAL RESIDUAL", total)

checks = [
    r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/timeline.md",
    r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/storyboards/第001章-时间的囚徒-分镜脚本.md",
    r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/storyboards/第044章-信任的考验-分镜脚本.md",
    r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/chapters/chapter-398.md",
]
for p in checks:
    t = Path(p).read_text(encoding="utf-8")
    name = Path(p).name
    for pat in ["32岁", "38岁", "2078", "2075"]:
        for m in re.finditer(pat, t):
            s = max(0, m.start() - 25)
            e = min(len(t), m.end() + 25)
            ctx = t[s:e].replace("\n", " ")
            print(f"{name} [{pat}]: ...{ctx}...")

# quality spot-checks
spots = [
    (r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/chapters/chapter-527.md",
     ["别，哭", "照，顾"]),
    (r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/chapters/chapter-184.md",
     ["你有没有感觉到", "他们只需要", "我是说", "刀锋一样"]),
    (r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/chapters/chapter-070.md",
     ["周围环境的参数"]),
    (r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/chapters/chapter-119.md",
     ["双手"]),
    (r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/chapters/chapter-291.md",
     ["对我们来说"]),
]
print("\n=== SPOT CHECKS ===")
for p, pats in spots:
    t = Path(p).read_text(encoding="utf-8")
    name = Path(p).name
    for pat in pats:
        for m in re.finditer(re.escape(pat), t):
            s = max(0, m.start() - 20)
            e = min(len(t), m.end() + 50)
            print(f"{name}: ...{t[s:e].replace(chr(10),' ')}...")
            break
