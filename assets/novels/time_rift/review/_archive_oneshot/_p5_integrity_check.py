# -*- coding: utf-8 -*-
from pathlib import Path
import re

CHDIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
samples = [62, 72, 122, 142, 168, 210, 221, 279, 369, 379, 404, 464]
for n in samples:
    p = CHDIR / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    title = t.splitlines()[0] if t.strip() else ""
    m = re.search(r"\*\*本章关键点[：:]?\*\*\s*\n([\s\S]+)$", t)
    fb = m.group(1) if m else ""
    stripped = fb.replace("新上海", "").replace("上海", "")
    issues = []
    if not title.lstrip("\ufeff").startswith("#"):
        issues.append("bad_title")
    if not m:
        issues.append("no_footer")
    if "陈远桥" in fb:
        issues.append("chenyuanqiao")
    if "梦" in fb:
        issues.append("meng")
    if "海" in stripped:
        issues.append("hai")
    if "相关公开口径暂不升格" in fb or "机械臂读数或共振" in fb:
        issues.append("boiler")
    if "本批 C 类" in fb or "破折号压低" in fb:
        issues.append("meta")
    if re.search(r"\n---\s*\n\s*\n---\s*\n\*\*本章关键点", t):
        issues.append("double_hr")
    status = "OK" if not issues else ",".join(issues)
    print(f"{n:03d} {status} | {title[:44]}")

wn = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\writing-notes.md").read_text(encoding="utf-8")
print("P5 checkbox:", "P5 页脚代价句个性化 — **2026-07-07 本批关闭**" in wn)
print("P5 record:", "P5 施工记录 · 页脚个性化" in wn)
print("changelog:", "P5页脚个性化" in wn)
