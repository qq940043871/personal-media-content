# -*- coding: utf-8 -*-
from pathlib import Path
import re

CHDIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
NAMED_POOL = [
    "老周", "周晚晴", "老何", "配电箱", "店长", "林晓", "陈明远", "陈维远",
    "赵远山", "苏婉清", "李博士", "监察署", "黎明号", "咖啡馆", "杂货店",
    "楼道", "观察窗", "公告栏", "账单", "配额", "市民频道", "班表", "回访",
    "阿宁", "周岚", "纯粹运动", "幽灵", "时间之心", "虚空", "Nexus", "听证",
    "铜牌", "电梯", "裂隙", "第六节点", "第七节点", "林若", "底层",
]
meta_pat = re.compile(r"第\d+章|本批|C 类|章节情节推进|正文不作同文|dash 保持|破折号压低")

for n in range(61, 121):
    p = CHDIR / f"chapter-{n:03d}.md"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\*\*本章关键点[：:]?\*\*\s*\n([\s\S]+)$", t)
    if not m:
        continue
    fb = m.group(1)
    if not meta_pat.search(fb):
        continue
    pre = t[: m.start()]
    title = next((ln for ln in t.splitlines() if ln.startswith("#")), "")
    body = "\n".join(ln for ln in pre.splitlines() if not ln.startswith("#"))
    named = [x for x in NAMED_POOL if x in body]
    quotes = re.findall(r"[「\"“]([^」\"”]{4,36})[」\"”]", body)[:4]
    paras = [x.strip() for x in body.split("\n") if x.strip()]
    opening = paras[0][:90] if paras else ""
    ending = " | ".join(x[:70] for x in paras[-2:]) if paras else ""
    print(f"{n:03d} {title}")
    print(f"  named={named[:10]}")
    print(f"  open={opening}")
    print(f"  end={ending}")
    print(f"  quotes={quotes}")
    print(f"  footer={fb.strip()[:160].replace(chr(10),' | ')}")
    print()
