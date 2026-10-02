# -*- coding: utf-8 -*-
"""P5 scan: Dialog/K and City/K for chapters 121-300."""
from __future__ import annotations
import re
from pathlib import Path

CH_DIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

CITY_WORDS = [
    "19层", "十九层", "23层", "二十三层", "47区", "四十七区", "47层", "四十七层",
    "时光倒流", "店长", "周晚晴", "老何", "楼道", "街区", "第23层", "第19层",
    "市民", "地面", "底层", "中层", "配电箱", "冰柜", "电梯", "走廊",
    "观察窗", "传单", "纯粹运动", "监察署", "连接税", "失败账", "民生",
    "新上海", "听证", "值班", "窗口", "店门", "楼", "层",
]

# tighter city anchors for the "民生三件套 / streetscape" metric
CITY_CORE = [
    "19层", "十九层", "23层", "二十三层", "第23层", "第19层", "47区", "四十七区",
    "47层", "四十七层", "时光倒流", "店长", "周晚晴", "老何",
    "观察窗", "传单", "楼道", "配电箱", "冰柜", "听证", "监察署",
    "连接税", "失败账", "纯粹运动", "值班员", "店门",
]

DIALOG_RE = re.compile(r'^[「『"\u201c]')


def body_only(text: str) -> str:
    # strip footer 本章关键点 block
    m = re.split(r"\n---\s*\n\s*\*\*本章关键点", text, maxsplit=1)
    body = m[0]
    # strip title line
    lines = body.splitlines()
    if lines and lines[0].startswith("#"):
        lines = lines[1:]
    return "\n".join(lines)


def count_cjk(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def count_dialogs(body: str) -> int:
    n = 0
    for line in body.splitlines():
        t = line.strip()
        if not t:
            continue
        if DIALOG_RE.match(t):
            n += 1
            continue
        # mid-line dialogue quotes 「...」 count as one per pair start
        n += len(re.findall(r"「", t))
    return n


def count_city(body: str, words: list[str]) -> int:
    n = 0
    for w in words:
        n += body.count(w)
    return n


def main() -> None:
    rows = []
    for ch in range(121, 301):
        p = CH_DIR / f"chapter-{ch:03d}.md"
        if not p.exists():
            rows.append((ch, None, None, None, None, None, "MISSING"))
            continue
        text = p.read_text(encoding="utf-8")
        body = body_only(text)
        cjk = count_cjk(body)
        dlg = count_dialogs(body)
        city = count_city(body, CITY_CORE)
        dash = len(re.findall(r"——", body))  # em-dash pairs approx
        if cjk == 0:
            rows.append((ch, 0, 0, 0, 0, 0, "EMPTY"))
            continue
        dk = dlg / (cjk / 1000)
        ck = city / (cjk / 1000)
        rows.append((ch, cjk, dlg, round(dk, 2), city, round(ck, 2), "ok"))

    # priority: 10k+ CJK, Dialog/K < 6, City/K < 0.5
    print("=== ALL 121-300 (ch, cjk, dlg, D/K, city, C/K) ===")
    for r in rows:
        ch, cjk, dlg, dk, city, ck, st = r
        if st != "ok":
            print(f"{ch:03d} {st}")
            continue
        print(f"{ch:03d} cjk={cjk} dlg={dlg} D/K={dk} city={city} C/K={ck}")

    print("\n=== PRIORITY (cjk>=10000, D/K<6, C/K<0.5) ===")
    pri = []
    for r in rows:
        ch, cjk, dlg, dk, city, ck, st = r
        if st == "ok" and cjk >= 10000 and dk < 6 and ck < 0.5:
            pri.append((dk, ck, -cjk, ch, cjk, dlg, city))
    pri.sort()
    for dk, ck, _, ch, cjk, dlg, city in pri:
        print(f"{ch:03d} cjk={cjk} dlg={dlg} D/K={dk} city={city} C/K={ck}")

    print("\n=== LOW Dialog/K (<6) regardless of city ===")
    low = []
    for r in rows:
        ch, cjk, dlg, dk, city, ck, st = r
        if st == "ok" and dk < 6:
            low.append((dk, -cjk, ch, cjk, dlg, city, ck))
    low.sort()
    for dk, _, ch, cjk, dlg, city, ck in low:
        print(f"{ch:03d} cjk={cjk} dlg={dlg} D/K={dk} city={city} C/K={ck}")

    print("\n=== LOW City/K (<0.5) with D/K>=6 or otherwise interesting ===")
    lowc = []
    for r in rows:
        ch, cjk, dlg, dk, city, ck, st = r
        if st == "ok" and ck < 0.5 and cjk >= 8000:
            lowc.append((ck, -cjk, ch, cjk, dlg, city, dk))
    lowc.sort()
    for ck, _, ch, cjk, dlg, city, dk in lowc:
        print(f"{ch:03d} cjk={cjk} dlg={dlg} D/K={dk} city={city} C/K={ck}")

    # named priority list from task
    named = [168, 142, 125, 225, 244, 217, 167, 147, 159, 226, 127, 238, 203, 231, 208]
    print("\n=== NAMED PRIORITY ===")
    for ch in named:
        for r in rows:
            if r[0] == ch:
                ch, cjk, dlg, dk, city, ck, st = r
                if st == "ok":
                    print(f"{ch:03d} cjk={cjk} dlg={dlg} D/K={dk} city={city} C/K={ck}")
                else:
                    print(f"{ch:03d} {st}")


if __name__ == "__main__":
    main()
