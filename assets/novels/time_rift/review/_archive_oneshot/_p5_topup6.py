# -*- coding: utf-8 -*-
from pathlib import Path
import re

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

add = {
319: """
公式贴出后，李明在自己的缓存首页写了一句给未来的核查者：「若你发现我把宇宙的轻，说轻了城市的贵，请直接改我的稿。稿可以改，账不能装看不见。」
""",
322: """
「人还在」四个字发出后，监察接口难得回了一句带人味的：「收到。今晚也有人在地面值夜。彼此。」
彼此。这个词在深渊边上轻轻落地，像一盏功率很小的灯。
""",
}

def split_file(raw):
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    lines = raw.splitlines()
    footer_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^---\s*$", line):
            after = "\n".join(lines[i + 1 :])
            if "本章关键点" in after or "本章围绕" in after:
                footer_idx = i
    if footer_idx is None:
        return raw.rstrip() + "\n", ""
    return "\n".join(lines[:footer_idx]).rstrip() + "\n", "\n".join(lines[footer_idx:])

def body_cjk(text):
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines()
    footer_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^---\s*$", line):
            after = "\n".join(lines[i + 1 :])
            if "本章关键点" in after or "本章围绕" in after:
                footer_idx = i
    body_lines = []
    for i, line in enumerate(lines):
        if footer_idx is not None and i >= footer_idx:
            break
        if i == 0 and line.startswith("# "):
            continue
        body_lines.append(line)
    return len(re.findall(r"[\u4e00-\u9fff]", "\n".join(body_lines)))

for n, block in add.items():
    p = base / ("chapter-%d.md" % n)
    raw = p.read_text(encoding="utf-8")
    before = body_cjk(raw)
    body, footer = split_file(raw)
    if block.strip()[:20] not in body:
        body = body.rstrip() + "\n\n" + block.strip() + "\n\n"
        out = body
        if footer:
            if not out.endswith("\n"):
                out += "\n"
            out += footer if footer.startswith("---") else "---\n" + footer
        if not out.endswith("\n"):
            out += "\n"
        p.write_text(out, encoding="utf-8")
    after = body_cjk(p.read_text(encoding="utf-8"))
    print("ch%d: %d -> %d %s" % (n, before, after, "OK" if after >= 5000 else "SHORT"))
