# -*- coding: utf-8 -*-
import re, pathlib
base = pathlib.Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
files = ["chapter-342.md","chapter-350.md","chapter-383.md","chapter-386.md","chapter-443.md","chapter-448.md"]
for f in files:
    p = base/f
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()
    body_lines = []
    in_key = False
    for ln in lines:
        if ln.startswith("# "):
            continue
        if "**本章关键点" in ln:
            in_key = True
        if in_key:
            continue
        if ln.strip() == "---":
            continue
        body_lines.append(ln)
    body = "\n".join(body_lines)
    cn = len(re.findall(r"[\u4e00-\u9fff]", body))
    cn_all = len(re.findall(r"[\u4e00-\u9fff]", text))
    dashes = text.count("——")
    pat = re.findall(r"不是[^。！？\n]{1,40}——不是[^。！？\n]{1,40}——而是", text)
    pat2 = re.findall(r"不是[^。！?\n]{1,30}——[^。！?\n]{1,30}——而是", text)
    meta = re.findall(r"第[〇一二三四五六七八九十百千0-9]+[章卷]", text)
    pure_blue = re.findall(r"纯蓝色数据流|蓝色数据流加速", text)
    has_key = "本章关键点" in text
    has_title = text.startswith("# 第")
    print(f"{f}: body_cn={cn} all_cn={cn_all} dash={dashes} notABC={len(pat)+len(pat2)} meta={meta} pureblue={pure_blue} key={has_key} title={has_title}")
