# -*- coding: utf-8 -*-
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

fixes = {
    "177": ("永恒的存在", "永恒是什么，我不知道", [
        "和平降临第100天，ARIA 追问永恒",
        "旧宇宙永恒=无限时间；新宇宙答案缺失",
        "李明机械臂进入平静代偿期",
    ]),
    "219": ("故事的力量", "故事会不会改写现实", [
        "力量空间：每个光点=一个故事可能性",
        "故事被相信/体验后改变现实结构",
        "人类文明史即被讲述塑造的现实",
    ]),
}

for ch, (old, new, points) in fixes.items():
    p = base / f"chapter-{ch}.md"
    raw = p.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8")
    if bom:
        text = text[3:] if text.startswith("\ufeff") else text
    lines = text.splitlines()
    print("before:", repr(lines[0]))
    lines[0] = f"# 第{int(ch)}章 {new}"
    body = "\n".join(lines[1:])
    if "本章关键点" not in body:
        body = body.rstrip() + "\n\n---\n\n**本章关键点：**\n" + "\n".join(f"- {x}" for x in points) + "\n"
    out = lines[0] + body
    if not out.endswith("\n"):
        out += "\n"
    data = out.encode("utf-8")
    if bom:
        data = b"\xef\xbb\xbf" + data
    p.write_bytes(data)
    check = p.read_text(encoding="utf-8-sig").splitlines()[0]
    print("after:", check)
    print("footer:", "本章关键点" in p.read_text(encoding="utf-8-sig"))
