# -*- coding: utf-8 -*-
"""P5 final verify: boilerplate + process-meta residual in priority ranges."""
from pathlib import Path
import re
import json

CHDIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
BOILER = [
    r"机械臂读数或共振代价写入失败账，不得用「一切正常」盖章",
    r"ARIA 融合瞳孔状态与深层感知同步记账，禁写纯蓝当前态",
    r"相关公开口径暂不升格",
    r"宇宙危机不得取消地面排班",
    r"立边界读数与暂停条件",
    r"写阶段目标与失败线：完成什么、拒绝什么、代价记哪本账",
]
META = [
    r"本批 C 类",
    r"章节情节推进；保持既有结论",
    r"正文不作同文公文尾",
    r"dash 保持低位",
    r"破折号压低",
    r"第\d+章 \S",  # footer bullet starting with 第X章 title as first item is meta
]


def extract(text):
    m = re.search(r"\*\*本章关键点[：:]?\*\*\s*\n([\s\S]+)$", text)
    if not m:
        return None, None, None
    pre = text[: m.start()]
    title = ""
    for line in pre.splitlines():
        if line.startswith("#"):
            title = line.strip()
            break
    footer = m.group(1).strip()
    bullets = [ln.strip() for ln in footer.splitlines() if ln.strip()]
    return title, bullets, footer


def main():
    stats = {}
    issues = []
    for lo, hi, label in [(61, 120, "61-120"), (121, 300, "121-300"), (341, 480, "341-480")]:
        gen = meta = ok = nof = 0
        for n in range(lo, hi + 1):
            p = CHDIR / f"chapter-{n:03d}.md"
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            title, bullets, footer = extract(text)
            if bullets is None:
                nof += 1
                issues.append({"n": n, "kind": "no_footer", "title": title})
                continue
            hits_b = [pat for pat in BOILER if re.search(pat, footer)]
            # meta: process notes, not canon notes
            hits_m = []
            for pat in META:
                if re.search(pat, footer):
                    hits_m.append(pat)
            # chapter-title-as-bullet: first bullet is exactly 第X章 ...
            for b in bullets:
                if re.match(rf"^第{n}章\b", b) or re.match(r"^第\d+章\b", b) and "事件" not in b and "钩子" not in b:
                    # allow if it's part of 事件 line describing content, ban bare "第X章 标题"
                    if re.match(r"^第\d+章\s+\S+$", b) or re.match(r"^第\d+章\s+\S+", b) and len(b) < 20:
                        hits_m.append("chapter_title_bullet")
            if hits_b:
                gen += 1
                issues.append({"n": n, "kind": "boiler", "title": title, "hits": hits_b[:2], "footer": footer[:160]})
            elif hits_m:
                meta += 1
                issues.append({"n": n, "kind": "meta", "title": title, "hits": hits_m[:2], "footer": footer[:160]})
            else:
                ok += 1
        stats[label] = {"ok": ok, "boiler": gen, "meta": meta, "no_footer": nof, "scanned": ok + gen + meta + nof}

    print("FINAL P5 VERIFY:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"\nissues={len(issues)}")
    for i in issues[:30]:
        print(f"  {i['n']:03d} {i['kind']} {i.get('hits','')} | {i.get('title','')[:30]} | {i.get('footer','')[:100]}")

    # full book core residual
    full = 0
    for p in sorted(CHDIR.glob("chapter-*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        _, _, footer = extract(text)
        if not footer:
            continue
        if any(re.search(pat, footer) for pat in BOILER[:3]):
            full += 1
    print(f"full-book core-boiler residual={full}")

    Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review\_p5_final_verify.json").write_text(
        json.dumps({"stats": stats, "issues": issues, "full_boiler": full}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
