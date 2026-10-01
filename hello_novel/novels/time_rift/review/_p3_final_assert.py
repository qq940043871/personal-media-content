# -*- coding: utf-8 -*-
import re, pathlib
base = pathlib.Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
for f in ["chapter-342.md","chapter-350.md","chapter-383.md","chapter-386.md","chapter-443.md","chapter-448.md"]:
    t = (base/f).read_text(encoding="utf-8")
    assert t.startswith("# 第"), f
    assert "本章关键点" in t, f
print("format ok")
wn = pathlib.Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\writing-notes.md").read_text(encoding="utf-8")
print("notes has batch1:", "批次1具象化手术完成" in wn)
t448 = (base/"chapter-448.md").read_text(encoding="utf-8")
print("448 meta chapter no:", "第四百四十八章" in t448)
for m in re.finditer(r"ARIA.{0,40}机械臂|机械臂.{0,40}ARIA", t448):
    print(" risk:", m.group()[:70])
print("done")
