# -*- coding: utf-8 -*-
"""Apply surgical P4 polish: strip boilerplate + insert literary ending before footer."""
import sys, re
sys.path.insert(0, r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review')
from _p4_polish_lib import (
    read_ch, write_ch, strip_boilerplate, verify, ensure_before_footer, cjk_count
)

# n -> literary ending replacement (replaces everything from weak close through footer)
# If key 'replace_from' present, cut narrative from that string to footer and insert ending.
POLISH = {}

def apply_one(n, ending, replace_from=None):
    t = read_ch(n)
    t, removed = strip_boilerplate(t)
    if replace_from:
        idx = t.find(replace_from)
        if idx == -1:
            print('WARN ch%s replace_from not found' % n)
        else:
            fm = re.search(r'\n---\n\s*\*\*本章关键点', t)
            t = t[:idx].rstrip() + '\n\n' + ending.strip() + '\n' + t[fm.start():]
    else:
        t = ensure_before_footer(t, ending)
    write_ch(n, t)
    v = verify(n)
    print('ch%s removed_boiler=%d cjk=%s dash=%s footer=%s ok=%s' % (
        n, removed, v['cjk'], v['dash'], v['footer'], v['ok']))
    return v

if __name__ == '__main__':
    # filled by caller via import or exec
    pass
