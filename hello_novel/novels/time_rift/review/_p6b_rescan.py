# -*- coding: utf-8 -*-
from pathlib import Path
import sys
sys.path.insert(0, r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review")
from _p6b_common import body_cjk, dash_count

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
short = []
dashbad = []
ok = 0
asset_ok = []
for n in range(541, 601):
    p = base / ("chapter-%d.md" % n)
    if not p.exists():
        print("%d\tMISSING" % n)
        continue
    raw = p.read_text(encoding="utf-8")
    cjk = body_cjk(raw)
    d = dash_count(raw)
    if n == 600:
        flag = "ASSET" + ("-OK" if cjk >= 4500 and d <= 8 else "-SOFT")
        if cjk >= 4500 and d <= 8:
            asset_ok.append(n)
        elif cjk < 4500:
            short.append((n, cjk, d))
        if d > 8:
            dashbad.append((n, cjk, d))
    elif cjk >= 5000 and d <= 8:
        flag = "OK"
        ok += 1
    elif cjk >= 5000:
        flag = "DASH"
        dashbad.append((n, cjk, d))
    else:
        flag = "SHORT"
        short.append((n, cjk, d))
        if d > 8:
            dashbad.append((n, cjk, d))
    print("%d\t%d\t%d\t%s" % (n, cjk, d, flag))
print("OK count", ok)
print("SHORT", short)
print("DASH>8", dashbad)
