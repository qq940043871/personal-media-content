# -*- coding: utf-8 -*-
"""Canon spot-check P6-B 541-600 + residual short 481-540 status."""
from pathlib import Path
import re
import sys
sys.path.insert(0, r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review")
from _p6b_common import body_cjk, dash_count

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
banned = ["张远", "赵远航", "陈远桥", "初心咖啡", "2082咖啡馆"]
print("=== banned names in 541-600 body/footer ===")
for n in range(541, 601):
    p = base / ("chapter-%d.md" % n)
    if not p.exists():
        continue
    raw = p.read_text(encoding="utf-8")
    hits = []
    for b in banned:
        if b in raw:
            # allow prohibition notes in footer
            for line in raw.splitlines():
                if b in line and ("禁" in line or "不再" in line or "勿" in line or "prohibition" in line.lower()):
                    continue
                if b in line:
                    hits.append((b, line[:60]))
    if hits:
        print(n, hits)

print("\n=== 林晓 gender near 574/600 ===")
for n in [574, 600, 545, 558, 571]:
    p = base / ("chapter-%d.md" % n)
    raw = p.read_text(encoding="utf-8")
    # count 他 near 林晓
    for m in re.finditer(r".{0,8}林晓.{0,20}", raw):
        seg = m.group()
        if "他" in seg:
            print(n, "NEAR-HE", seg.replace("\n", " "))
    if "他穿着联盟使者" in raw or "他说。" in raw and "林晓" in raw[:500]:
        print(n, "check opening she")

print("\n=== ch600 keys ===")
p = base / "chapter-600.md"
raw = p.read_text(encoding="utf-8")
for key in ["时光倒流", "打烊", "回望", "非物理", "不在物理", "林晓", "她"]:
    print(key, raw.count(key))
print("cjk", body_cjk(raw), "dash", dash_count(raw))
print("李明 physical walk?", "李明走在" in raw or "李明和ARIA并肩" in raw)

print("\n=== residual short 481-540 (batch1 zone, info only) ===")
short = []
for n in range(481, 541):
    p = base / ("chapter-%d.md" % n)
    if not p.exists():
        continue
    raw = p.read_text(encoding="utf-8")
    cjk = body_cjk(raw)
    d = dash_count(raw)
    if cjk < 5000:
        short.append((n, cjk, d, n in range(530, 541)))
print("count short", len(short))
print("asset 530-540 still short:", [(n,c,d) for n,c,d,a in short if a])
print("non-asset sample:", [(n,c,d) for n,c,d,a in short if not a][:25])
