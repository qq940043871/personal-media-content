# -*- coding: utf-8 -*-
"""P6-C body dash literary punctuation pass for chapters 481-600.

Rules:
- Explanatory —— → 逗号/句号/冒号
- Keep ≤3 dramatic per chapter (dialogue interruption / Morse / key reveal)
- 「不是A——而是B」≤2 (rest → comma)
- Do not change plot; footer untouched
- Asset chapters 530-540 / 600: punctuation only (same as all)
"""
import re
from pathlib import Path

CHAPTERS = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
KEEP_MAX_DRAMATIC = 3
KEEP_MAX_BUER = 2  # 不是A——而是B
TARGET_FLOOR = 8   # must end ≤ this; script aims ≤3


def split_file(raw: str):
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    lines = raw.splitlines()
    footer_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^---\s*$", line):
            after = "\n".join(lines[i + 1 :])
            if "本章关键点" in after or "本章围绕" in after:
                footer_idx = i
                break
    if footer_idx is None:
        return raw, ""
    body = "\n".join(lines[:footer_idx])
    footer = "\n".join(lines[footer_idx:])
    return body, footer


def is_dramatic(before: str, after: str, full_before: str) -> bool:
    """Keep as dramatic: dialogue truncation, Morse, sudden reveal, title-ish."""
    b = before[-40:] if before else ""
    a = after[:40] if after else ""

    # Morse / letter-by-letter speech: look at recent quotes with short CJK fragments
    # e.g. "看——日——出。"  "太——阳——真——美。"
    if re.search(r"[「\"『]?[^\n「」\"』]{1,4}$", b) and re.match(
        r"^[^\n「」\"』]{1,4}[」\"』。]", a
    ):
        # both sides short → letter-by-letter dramatic
        left = re.findall(r"([^\n「」\"』]{1,4})$", b)[-1]
        right = re.match(r"^([^\n「」\"』]{1,4})", a)
        if right and len(left) <= 4 and len(right.group(1)) <= 4:
            # avoid converting ordinary mid-sentence short tails
            if re.search(r"[「\"『]", b[-15:]):
                return True

    # mid-dialogue interruption: open quote unclosed and short trail
    open_q = b.count("「") + b.count('"') + b.count('"') + b.count("『")
    close_q = b.count("」") + b.count('"') + b.count('"') + b.count("』")
    if open_q > close_q:
        trail_m = re.search(r"([^「」\"』]{0,10})$", b)
        if trail_m and len(trail_m.group(1)) <= 8:
            return True

    # explicit dramatic tails
    dramatic_tail = [
        r"它是$",
        r"但$",
        r"因为$",
        r"而是$",
        r"只是$",
        r"如果[^。]{0,18}$",
        r"不$",
        r"我$",
        r"为什么$",
        r"可$",
        r"却$",
        r"那个选择$",
        r"意义$",
        r"那声音$",
        r"一种$",
        r"东西$",
        r"开始$",
        r"馈赠$",
        r"存在$",
        r"整体$",
        r"实验$",
        r"沉默$",
        r"惯$",
        r"了$",
        r"是$",
    ]
    # only keep a subset as truly dramatic (not every 的/了)
    strong = [
        r"它是$",
        r"但$",
        r"因为$",
        r"而是$",
        r"只是$",
        r"不$",
        r"我$",
        r"为什么$",
        r"可$",
        r"却$",
        r"那声音$",
        r"一种$",
        r"东西$",
        r"馈赠$",
        r"实验$",
        r"沉默$",
        r"开始$",
        r"整体$",
        r"意义$",
        r"存在$",
        r"选择$",
    ]
    for p in strong:
        if re.search(p, b):
            return True

    # paired parenthetical: "——如果……的话——"  keep the PAIR only if very literary
    if re.search(r"——[^。\n]{0,25}$", b) and re.match(r"^", a):
        pass

    # "如果能称之为声音的话——" style parenthetical close — dramatic
    if re.search(r"的话——?$", b) or b.endswith("的话"):
        return True
    if re.match(r"^如果", a) and "的话" in a[:20]:
        return True

    # key reveal after short tail in narrative (e.g. 不确定。/ ARIA。)
    if re.match(r"^(ARIA|李明|林晓|苏婉清|不确定|存在|认知)", a) and re.search(
        r"(东西|存在|自由|名字|时刻|选择|本质|事实)$", b
    ):
        return True

    return False


def is_bu_er(before: str, after: str) -> bool:
    """不是A——而是B pattern."""
    b = before[-20:] if before else ""
    a = after[:16] if after else ""
    if re.search(r"(不是|并非|而不|而非)[^。]{0,14}$", b):
        return True
    if re.match(r"^(而是|并非|不是|而非)", a):
        return True
    return False


def convert_dash(before: str, after: str, keep_buer: int) -> str:
    b = before[-8:] if before else ""
    a = after[:24] if after else ""

    # city-anchor chalk / label:content → 冒号
    # e.g. "19层手写表——今晚灯到九点" / "23层时光倒流——打烊后" / "47区观察窗——夜读数"
    if re.search(r"(手写表|时光倒流|观察窗|配电箱|巡检条|回执|地砖|机械臂接口|页复印件|纸条|卡片)[^」\"'\n]{0,6}$", b):
        return "："
    if re.search(r"(层「?[^\n」]{0,8}|区[^\n」]{0,6})$", b) and re.match(
        r"^(今晚|打烊|夜读|已|电表|冷却|23|19|47)", a
    ):
        return "："

    # list after → 冒号
    if re.match(
        r"^\s*(第一|首先|有些|有的|包括|那些|比如|例如|温度|气压|蓝、|紫|从|不是|是|有|有的)",
        a,
    ):
        if re.match(r"^\s*(有些|有的|包括|那些|比如|例如|温度|气压|蓝、|紫)", a):
            return "："
        if re.match(r"^\s*从(最|一|原)", a):
            return "："

    # 不是A——而是B → ， (keep only limited)
    if keep_buer <= 0 and is_bu_er(before, after):
        return "，"

    # definition after "是" / "那是" / "这意味着" → ，
    if re.match(r"^(那|这|一个|所有|任何|它|他|她|我|你|我们|她|他)", a):
        return "，"
    if re.match(r"^(一种|一个是|是指|意味着|代表)", a):
        return "，"

    # after 了/着/过/的/地/得 → ，
    if b and b[-1] in "了着过的地得":
        return "，"

    # "X是——Y" explanation
    if b.endswith("是") or b.endswith("就是"):
        return "，"

    # conjunction start after dash
    if a and a[0] in "但是所以因为而且如果":
        return "，"

    # long explanatory after → 。
    # if after is a full independent clause with clear subject+predicate, comma still fine
    # default literary: 逗号 for flow; period if before already ends a thought
    if b and b[-1] in "。！？":
        return ""

    # "因为数据记录了——但她不会" style mid-clause
    return "，"


def reduce_dashes(body: str):
    """Convert explanatory dashes; keep limited dramatic + 不是A而是B."""
    positions = []
    idx = 0
    while True:
        pos = body.find("——", idx)
        if pos < 0:
            break
        positions.append(pos)
        idx = pos + 2
    if not positions:
        return body, [], 0, 0

    scored = []
    for pos in positions:
        before = body[:pos]
        after = body[pos + 2 :]
        d = is_dramatic(before, after, before)
        b = is_bu_er(before, after)
        scored.append({"pos": pos, "dramatic": d, "bu_er": b, "before": before, "after": after})

    # prioritize keeping dramatic ones (up to KEEP_MAX_DRAMATIC)
    dramatic_idx = [i for i, s in enumerate(scored) if s["dramatic"]]
    if len(dramatic_idx) > KEEP_MAX_DRAMATIC:
        # keep Morse / dialogue ones first: shortest "before tail inside quotes"
        def score_keep(i):
            s = scored[i]
            b = s["before"]
            # Morse-like if last fragment short and quoted
            m = re.findall(r"([^\n「」\"』]{1,4})$", b)
            left = m[-1] if m else "xx" * 10
            return len(left)

        keep_dramatic = set(sorted(dramatic_idx, key=score_keep)[:KEEP_MAX_DRAMATIC])
    else:
        keep_dramatic = set(dramatic_idx)

    # 不是A——而是B keep up to 2 among non-dramatic
    buer_idx = [i for i, s in enumerate(scored) if s["bu_er"] and i not in keep_dramatic]
    keep_buer = set(buer_idx[:KEEP_MAX_BUER])

    # if total would still be >3, drop non-dramatic buer keeps too
    total_keep_est = len(keep_dramatic) + len(keep_buer)
    if total_keep_est > 3:
        # keep dramatic first, then at most (3 - dramatic) buer
        room = max(0, 3 - len(keep_dramatic))
        keep_buer = set(list(keep_buer)[:room])

    keep_set = keep_dramatic | keep_buer
    buer_budget = KEEP_MAX_BUER - len(keep_buer)

    new_body = body
    log = []
    # rebuild from end
    for i in range(len(scored) - 1, -1, -1):
        s = scored[i]
        pos = s["pos"]
        if i in keep_set:
            kind = "DRAMATIC" if i in keep_dramatic else "BUER"
            log.append((kind, s["before"][-18:] + "——" + s["after"][:18]))
            continue
        rep = convert_dash(s["before"], s["after"], buer_budget)
        if s["bu_er"] and buer_budget > 0:
            # already in keep_set normally; if not, still convert
            pass
        if rep == "":
            # shouldn't happen
            rep = "，"
        new_body = new_body[:pos] + rep + new_body[pos + 2 :]
        log.append(("CONV", s["before"][-18:] + f"→{rep}←" + s["after"][:18]))

    return new_body, log, len(positions), new_body.count("——")


def force_to_target(body: str, target: int = 3) -> str:
    """If still above target, force-convert remaining explanatory dashes."""
    n = body.count("——")
    if n <= target:
        return body
    # find positions, convert from start those that are not Morse
    pos = 0
    while body.count("——") > target:
        p = body.find("——", pos)
        if p < 0:
            break
        before = body[:p]
        after = body[p + 2 :]
        # skip Morse
        if is_dramatic(before, after, before) and body.count("——") <= target + 2:
            pos = p + 2
            continue
        rep = convert_dash(before, after, 0)
        body = body[:p] + rep + body[p + 2 :]
        pos = p + 1
    return body


def process_chapter(n: int, dry_run: bool = False):
    p = CHAPTERS / f"chapter-{n:03d}.md"
    if not p.exists():
        return n, None, None, "missing"
    raw = p.read_text(encoding="utf-8")
    body, footer = split_file(raw)
    lines = body.splitlines()
    title_line = lines[0] if lines and lines[0].startswith("# ") else ""
    rest = "\n".join(lines[1:] if title_line else lines)
    # count body excluding title
    count_before = rest.count("——")
    if count_before <= TARGET_FLOOR:
        return n, count_before, count_before, "skip"

    new_rest, log, raw_n, after_n = reduce_dashes(rest)
    if after_n > 3:
        new_rest = force_to_target(new_rest, 3)
        after_n = new_rest.count("——")
    # if still >8 after aim-for-3, force harder
    if after_n > TARGET_FLOOR:
        new_rest = force_to_target(new_rest, TARGET_FLOOR)
        after_n = new_rest.count("——")

    if dry_run:
        return n, count_before, after_n, "dry"

    new_body = (title_line + "\n" if title_line else "") + new_rest
    if not new_body.endswith("\n"):
        new_body += "\n"
    new_raw = new_body + footer
    if not new_raw.endswith("\n"):
        new_raw += "\n"
    p.write_text(new_raw, encoding="utf-8")
    return n, count_before, after_n, "ok"


def main():
    over = [
        481, 483, 485, 488, 489, 491, 494, 497, 512, 521, 528, 531, 532, 535,
        541, 542, 546, 553, 555, 560, 563, 565, 568, 569, 570, 573, 579,
        584, 585, 586, 587, 594, 595, 596, 599,
    ]
    results = []
    for n in over:
        r = process_chapter(n, dry_run=False)
        results.append(r)
        print(f"ch{r[0]}: {r[1]} -> {r[2]}  ({r[3]})")
    print("\nSUMMARY")
    print(f"{'ch':>6} {'before':>8} {'after':>8}")
    tb = ta = 0
    for n, b, a, s in results:
        if b is None:
            continue
        tb += b
        ta += a
        print(f"{n:6d} {b:8d} {a:8d}  {s}")
    print(f"TOTAL  {tb:8d} {ta:8d}")
    still = [(n, a) for n, b, a, s in results if a is not None and a > 8]
    print("still>8:", still if still else "NONE")


if __name__ == "__main__":
    main()
