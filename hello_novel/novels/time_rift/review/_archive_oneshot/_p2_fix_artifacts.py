# -*- coding: utf-8 -*-
"""Fix mechanical artifact 与其说那是 → 与其说是 in trial 1-15 and Vol1 1-60.
Also scan trial for other mechanical residuals.
"""
from pathlib import Path
import re

root = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

ARTIFACTS = [
    ("与其说那是", "与其说是"),
    ("如果说那是", "如果说是"),
    ("关键不在因为", "关键不在是否因为"),
]

print("=== fix 与其说那是 in trial 1-15 + Vol1 1-60 ===")
changed = []
for n in range(1, 61):
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    orig = t
    for a, b in ARTIFACTS:
        t = t.replace(a, b)
    if t != orig:
        # count occurrences fixed
        for a, b in ARTIFACTS:
            c = orig.count(a)
            if c:
                changed.append((n, a, c))
        p.write_text(t, encoding="utf-8")
print("fixed:", changed)

print("\n=== residual artifact scan trial 1-15 ===")
for n in range(1, 16):
    p = root / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    issues = []
    if "与其说那是" in t:
        issues.append("与其说那是")
    if "如果话" in t:
        issues.append("如果话")
    if "，，" in t:
        issues.append("双逗号")
    if re.search(r"[^…]。。", t):
        issues.append("双句号")
    if "AR IA" in t or "A RIA" in t:
        issues.append("ARIA-space")
    if re.search(r"(?<!目)的的", t):
        issues.append("的的")
    if "赵远航" in t:
        issues.append("赵远航")
    if re.search(r"旧时光", t) and "不是旧时光" not in t:
        issues.append("旧时光")
    if re.search(r"在第\s*[0-9一二三四五六七八九十百千]+\s*章", t):
        issues.append("meta在第X章")
    # punctuation glue
    if re.search(r"，。|。，|：，|，：|；，", t):
        issues.append("标点粘连")
    # 循环日志
    has_log = "循环日志" in t
    body = t.split("本章关键点")[0]
    dashes = body.count("——")
    flag = "OK" if not issues else issues
    print(f"  {n:03d}: dash={dashes} log={has_log} {flag}")

print("\n=== spot-check sentences around edits ===")
checks = [
    (1, "她的助理机器人"),
    (1, "时间感知模块"),
    (3, "物理痕迹"),
    (4, "自我诊断"),
    (4, "与其说"),
    (11, "因果链"),
    (13, "蓝色光带亮度"),
    (14, "全息投影。在那块"),
    (472, "源头的信号不是用来"),
    (392, "第一潮"),
]
for n, needle in checks:
    p = root / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    if needle not in t:
        print(f"ch{n:03d} MISSING needle: {needle}")
        continue
    i = t.index(needle)
    print(f"ch{n:03d}: ...{t[max(0,i-30):i+80].replace(chr(10),' ')}...")
