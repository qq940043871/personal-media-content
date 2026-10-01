# -*- coding: utf-8 -*-
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
cjk = re.compile(r"[\u4e00-\u9fff]")
targets = [530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 600]


def body_of(text):
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines()
    body_lines = []
    skip_title = True
    for i, line in enumerate(lines):
        if skip_title and line.startswith("# "):
            skip_title = False
            continue
        if line.strip() == "---" and any("本章关键点" in l for l in lines[i:]):
            break
        if line.startswith(">"):
            continue
        body_lines.append(line)
    return "\n".join(body_lines)


print("ch | CJK | dash | foot | bom | bad")
for n in targets:
    p = base / f"chapter-{n:03d}.md"
    raw = p.read_text(encoding="utf-8")
    bom = raw.startswith("\ufeff")
    body = body_of(raw)
    c = len(cjk.findall(body))
    d = len(re.findall("——", body))
    foot = "Y" if "**本章关键点：**" in raw else "N"
    bad = []
    for name in ["张远", "赵远航", "陈远桥", "初心咖啡", "2082咖啡馆"]:
        if name in body:
            bad.append(name)
    # footer prohibition typos
    if "禁陈维远" in raw:
        bad.append("FOOTER-TYPO-禁陈维远")
    bad_s = ",".join(bad) if bad else "-"
    print(f"{n} | {c} | {d} | {foot} | {int(bom)} | {bad_s}")
