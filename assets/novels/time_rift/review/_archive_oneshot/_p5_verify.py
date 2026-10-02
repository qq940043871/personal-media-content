# -*- coding: utf-8 -*-
"""P5 verification: recount generic cost footers after rewrite."""
from pathlib import Path
import re
import json

CHDIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

BOILER_COST = [
    r"机械臂读数或共振代价写入失败账，不得用「一切正常」盖章",
    r"ARIA 融合瞳孔状态与深层感知同步记账，禁写纯蓝当前态",
    r"相关公开口径暂不升格",
    r"宇宙危机不得取消地面排班",
    r"立边界读数与暂停条件",
    r"写阶段目标与失败线：完成什么、拒绝什么、代价记哪本账",
]
NAMED_STRICT = [
    "老周", "周晚晴", "老何", "配电箱", "店长", "林晓", "陈明远", "陈维远",
    "赵远山", "苏婉清", "李博士", "伊瑟拉", "阿宁", "周岚", "监察署",
    "黎明号", "守钥", "线脉", "影种", "灰紫", "市民频道", "班表", "回访",
    "反对者", "家属", "观测窗", "观察窗", "楼道", "值班站", "联防",
    "公告栏", "账单", "配额", "杂货店", "咖啡馆", "王阿姨", "CUR-221",
]


def extract(text):
    m = re.search(r"\*\*本章关键点[：:]?\*\*\s*\n([\s\S]+)$", text)
    if not m:
        return None, None
    pre = text[: m.start()]
    title = ""
    for line in pre.splitlines():
        if line.startswith("#"):
            title = line.strip()
            break
    footer = m.group(1).strip()
    bullets = []
    for line in footer.splitlines():
        s = line.strip()
        if s.startswith("-") or s.startswith("*"):
            bullets.append(s.lstrip("-* "))
        elif s:
            bullets.append(s)
    return title, bullets


def is_still_generic(n, title, bullets):
    all_b = "\n".join(bullets)
    hits = []
    for pat in BOILER_COST:
        if re.search(pat, all_b):
            hits.append(pat[:24])
    if not hits:
        return False, hits, all_b
    # if also has named anchors / specific numbers, treat as mixed (report but lower priority)
    has_named = any(x in all_b for x in NAMED_STRICT)
    has_num = bool(re.search(r"\d+(\.\d+)?\s*(%|％|小时|层|区|票|号|℃|Hz|h|条|页)", all_b))
    return True, hits, all_b


def main():
    ranges = [(61, 120, "61-120"), (121, 300, "121-300"), (341, 480, "341-480")]
    stats = {}
    remaining = []
    samples_before_after = []
    for lo, hi, label in ranges:
        gen = ok = nof = 0
        for n in range(lo, hi + 1):
            p = CHDIR / f"chapter-{n:03d}.md"
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            title, bullets = extract(text)
            if bullets is None:
                nof += 1
                continue
            g, hits, all_b = is_still_generic(n, title, bullets)
            if g:
                gen += 1
                remaining.append({"n": n, "label": label, "title": title, "hits": hits[:3], "footer": all_b[:200]})
            else:
                ok += 1
        stats[label] = {"generic": gen, "ok": ok, "no_footer": nof, "scanned": gen + ok + nof}

    print("AFTER P5 stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"\nRemaining generic/p4-boiler footers in priority ranges: {len(remaining)}")
    for r in remaining[:40]:
        print(f"  {r['n']:03d} [{r['label']}] {r['title'][:30]} hits={r['hits']}")
        print(f"       {r['footer'][:120]}")

    # also full-book residual of key boilerplate
    full_gen = 0
    full_examples = []
    for p in sorted(CHDIR.glob("chapter-*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        title, bullets = extract(text)
        if not bullets:
            continue
        all_b = "\n".join(bullets)
        if any(re.search(pat, all_b) for pat in BOILER_COST[:3]):  # core three
            full_gen += 1
            if len(full_examples) < 15:
                full_examples.append((p.name, title, all_b[:100]))
    print(f"\nFull-book residual core-boiler footers: {full_gen}")
    for e in full_examples:
        print(f"  {e[0]} {e[1][:30]} | {e[2]}")

    Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review\_p5_verify.json").write_text(
        json.dumps({"stats": stats, "remaining": remaining, "full_gen": full_gen}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
