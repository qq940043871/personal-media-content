# -*- coding: utf-8 -*-
import re
from pathlib import Path

ROOT = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
FOOTER_RE = re.compile(r"\n---\s*\n\*\*本章关键点[：:]\*\*", re.M)
TITLE_RE = re.compile(r"^# 第(\d+)章\s*(.*)")

GENERIC = {
    "裂隙": "裂隙线推进；宇宙悬念与地面责任并行",
    "循环": "循环机制相关推进；注意记忆规则与公共事实",
    "虚空": "虚空线推进；禁止用宇宙危机取消民生排班",
    "联盟": "联盟线推进；连接与可问责并重",
    "时间": "时间结构线推进；结论须可被地面核对",
}


def make_footer(title: str) -> str:
    gist = None
    for k, v in GENERIC.items():
        if k in title:
            gist = v
            break
    if not gist:
        gist = "章节情节推进；保持既有结论与城市钩子"
    return (
        "---\n"
        "**本章关键点：**\n"
        f"- {title}\n"
        f"- {gist}\n"
        "- 幽灵=赵远山；ARIA ch60+禁纯蓝当前态（银主蓝辅/融合态）\n"
        "- 咖啡馆「时光倒流」中层23层；城市账与听证线可并行\n"
        "- dash 保持低位；正文不作同文公文尾\n"
        "- 本批 C 类加厚不改本章既有情节结论\n"
    )


def main() -> None:
    changed = []
    for n in range(61, 121):
        p = ROOT / f"chapter-{n:03d}.md"
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8-sig")
        m = FOOTER_RE.search(t)
        bullets = len(re.findall(r"^- ", t[m.start() :], re.M)) if m else 0
        if bullets >= 2:
            continue
        first = t.splitlines()[0].lstrip("\ufeff") if t else ""
        tm = TITLE_RE.search(first)
        if tm:
            title = f"第{tm.group(1)}章 {tm.group(2).strip()}".strip()
        else:
            title = first[:40]
        foot = make_footer(title)
        if m:
            t = t[: m.start()] + foot
        else:
            t = t.rstrip() + "\n\n" + foot
        p.write_text(t, encoding="utf-8")
        changed.append(n)
    print("footers filled:", changed)
    print("count", len(changed))


if __name__ == "__main__":
    main()
