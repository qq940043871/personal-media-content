# -*- coding: utf-8 -*-
"""P6-B: dash compress on 541-600 chapters with body dash>8 (length already ok)."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from _p6b_common import body_cjk, dash_count, compress_dashes

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

# long-enough but high dash in 541-600
TARGETS = [541, 546, 548, 553, 554, 560, 563, 565, 568, 569, 570, 585, 594, 596]

def main():
    for n in TARGETS:
        p = base / ("chapter-%d.md" % n)
        if not p.exists():
            print("missing", n)
            continue
        raw = p.read_text(encoding="utf-8")
        before_cjk = body_cjk(raw)
        before_d = dash_count(raw)
        if before_d <= 8:
            print("ch%d skip dash=%d cjk=%d" % (n, before_d, before_cjk))
            continue
        compress_dashes(p, keep_max=8)
        after = p.read_text(encoding="utf-8")
        print("ch%d: dash %d -> %d cjk %d -> %d %s" % (
            n, before_d, dash_count(after), before_cjk, body_cjk(after),
            "OK" if body_cjk(after) >= 5000 else "SHORT"))

if __name__ == "__main__":
    main()
