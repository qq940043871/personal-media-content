# -*- coding: utf-8 -*-
from pathlib import Path
import sys
sys.path.insert(0, r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review")
from _p6b_common import body_cjk, dash_count

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
# sample footers + city anchors
for n in [543, 545, 574, 580, 586, 595, 597, 600]:
    p = base / ("chapter-%d.md" % n)
    raw = p.read_text(encoding="utf-8")
    print("==== ch%d cjk=%d dash=%d ====" % (n, body_cjk(raw), dash_count(raw)))
    # last 12 lines
    lines = raw.splitlines()
    for line in lines[-12:]:
        print(line)
    # city anchors present
    for a in ["时光倒流", "手写表", "观察窗", "林晓", "空着也是账", "打烊"]:
        if a in raw:
            print(" has", a)
    print()
