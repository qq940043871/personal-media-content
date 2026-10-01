# -*- coding: utf-8 -*-
"""P6-C residual: fix Morse over-conversion + re-polish chapters still body>8.

Body口径 = exclude title line + footer (本章关键点).
"""
import re
from pathlib import Path

CHAPTERS = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
KEEP_MAX_DRAMATIC = 3
KEEP_MAX_BUER = 2
TARGET = 8


def split_body_footer_title(raw: str):
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
        body_all = "\n".join(lines)
        footer = ""
    else:
        body_all = "\n".join(lines[:footer_idx])
        footer = "\n".join(lines[footer_idx:])
    blines = body_all.splitlines()
    title = blines[0] if blines and blines[0].startswith("# ") else ""
    rest = "\n".join(blines[1:] if title else blines)
    return title, rest, footer


def body_dash(title, rest, footer) -> int:
    return rest.count("——")


def is_dramatic(before: str, after: str) -> bool:
    b = before[-40:] if before else ""
    a = after[:40] if after else ""
    # Morse / letter speech
    if re.search(r"[「\"『]?[^\n「」\"』]{1,4}$", b) and re.match(r"^[^\n「」\"』]{1,4}[」\"』。,，]", a):
        left_m = re.findall(r"([^\n「」\"』]{1,4})$", b)
        left = left_m[-1] if left_m else "xxxx"
        right_m = re.match(r"^([^\n「」\"』]{1,4})", a)
        right = right_m.group(1) if right_m else "xxxx"
        if len(left) <= 4 and len(right) <= 4 and re.search(r"[「\"『]", b[-20:]):
            return True
    open_q = b.count("「") + b.count('"') + b.count('"') + b.count("『")
    close_q = b.count("」") + b.count('"') + b.count('"') + b.count("』")
    if open_q > close_q:
        trail_m = re.search(r"([^「」\"』]{0,10})$", b)
        if trail_m and len(trail_m.group(1)) <= 8:
            return True
    strong = [
        r"它是$", r"但$", r"因为$", r"而是$", r"只是$", r"不$", r"我$", r"为什么$",
        r"可$", r"却$", r"那声音$", r"一种$", r"东西$", r"馈赠$", r"实验$",
        r"沉默$", r"开始$", r"整体$", r"意义$", r"存在$", r"选择$", r"的话$",
    ]
    for p in strong:
        if re.search(p, b):
            return True
    if re.match(r"^(ARIA|李明|林晓|苏婉清|不确定|存在|认知)", a) and re.search(
        r"(东西|存在|自由|名字|时刻|选择|本质|事实)$", b
    ):
        return True
    return False


def is_bu_er(before: str, after: str) -> bool:
    b = before[-20:] if before else ""
    a = after[:16] if after else ""
    if re.search(r"(不是|并非|而不|而非)[^。]{0,14}$", b):
        return True
    if re.match(r"^(而是|并非|不是|而非)", a):
        return True
    return False


def convert_dash(before: str, after: str) -> str:
    b = before[-8:] if before else ""
    a = after[:24] if after else ""
    if re.search(r"(手写表|时光倒流|观察窗|配电箱|巡检条|回执|地砖|机械臂接口|复印件|纸条|卡片)[^」\"'\n]{0,6}$", b):
        return "："
    if re.match(r"^\s*(有些|有的|包括|那些|比如|例如|温度|气压|蓝、|紫|从最|从一)", a):
        return "："
    if re.match(r"^(那|这|一个|所有|任何|它|他|她|我|你|我们)", a):
        return "，"
    if re.match(r"^(一种|是指|意味着|代表)", a):
        return "，"
    if b and b[-1] in "了着过的地得":
        return "，"
    if b.endswith("是") or b.endswith("就是"):
        return "，"
    if a and a[0] in "但是所以因为而且如果":
        return "，"
    return "，"


def reduce_rest(rest: str, target: int = 3):
    positions = []
    idx = 0
    while True:
        pos = rest.find("——", idx)
        if pos < 0:
            break
        positions.append(pos)
        idx = pos + 2
    if not positions:
        return rest, 0
    scored = []
    for pos in positions:
        before = rest[:pos]
        after = rest[pos + 2 :]
        scored.append(
            {
                "pos": pos,
                "dramatic": is_dramatic(before, after),
                "bu_er": is_bu_er(before, after),
                "before": before,
                "after": after,
            }
        )
    dramatic_idx = [i for i, s in enumerate(scored) if s["dramatic"]]

    def score_keep(i):
        m = re.findall(r"([^\n「」\"』]{1,4})$", scored[i]["before"])
        return len(m[-1]) if m else 99

    if len(dramatic_idx) > KEEP_MAX_DRAMATIC:
        keep_dramatic = set(sorted(dramatic_idx, key=score_keep)[:KEEP_MAX_DRAMATIC])
    else:
        keep_dramatic = set(dramatic_idx)
    buer_idx = [i for i, s in enumerate(scored) if s["bu_er"] and i not in keep_dramatic]
    room = max(0, 3 - len(keep_dramatic))
    keep_buer = set(buer_idx[: min(KEEP_MAX_BUER, room)])
    keep_set = keep_dramatic | keep_buer

    new_rest = rest
    for i in range(len(scored) - 1, -1, -1):
        s = scored[i]
        if i in keep_set:
            continue
        rep = convert_dash(s["before"], s["after"])
        new_rest = new_rest[: s["pos"]] + rep + new_rest[s["pos"] + 2 :]
    # force down to target if needed
    guard = 0
    while new_rest.count("——") > max(target, 3) and guard < 50:
        p = new_rest.find("——")
        if p < 0:
            break
        before = new_rest[:p]
        after = new_rest[p + 2 :]
        if is_dramatic(before, after) and new_rest.count("——") <= 4:
            # skip this one; try next
            p2 = new_rest.find("——", p + 2)
            if p2 < 0:
                break
            p = p2
            before = new_rest[:p]
            after = new_rest[p + 2 :]
        rep = convert_dash(before, after)
        new_rest = new_rest[:p] + rep + new_rest[p + 2 :]
        guard += 1
    return new_rest, new_rest.count("——")


def fix_morse_528():
    """Restore letter-by-letter Morse dashes damaged by auto-conversion."""
    p = CHAPTERS / "chapter-528.md"
    raw = p.read_text(encoding="utf-8")
    replacements = [
        ('"看——日，出。"', '"看——日——出。"'),
        ('"想，看，开，始。"', '"想——看——开——始。"'),
        ('"你——好，的。"', '"你——好——的。"'),
        ('"我——也，好。"', '"我——也——好。"'),
        ('"太——阳，真，美。"', '"太——阳——真——美。"'),
        ('"太，阳，真，美。"', '"太——阳——真——美。"'),
        ("「看——日，出。」", "「看——日——出。」"),
    ]
    changed = []
    for a, b in replacements:
        if a in raw:
            raw = raw.replace(a, b)
            changed.append((a, b))
    # also generic: inside quotes short Morse patterns that got mid-commas
    # "X——Y，Z。" where X/Y/Z are 1-char — restore if clearly Morse scene context
    p.write_text(raw, encoding="utf-8")
    return changed


def polish_residual(chs):
    results = []
    for n in chs:
        p = CHAPTERS / f"chapter-{n:03d}.md"
        if not p.exists():
            results.append((n, None, None, "missing"))
            continue
        raw = p.read_text(encoding="utf-8")
        title, rest, footer = split_body_footer_title(raw)
        before = rest.count("——")
        if before <= TARGET:
            results.append((n, before, before, "skip"))
            continue
        new_rest, after = reduce_rest(rest, target=3)
        if after > TARGET:
            new_rest, after = reduce_rest(new_rest, target=TARGET)
        new_raw = ""
        if title:
            new_raw += title + "\n"
        new_raw += new_rest
        if not new_raw.endswith("\n"):
            new_raw += "\n"
        new_raw += footer
        if not new_raw.endswith("\n"):
            new_raw += "\n"
        p.write_text(new_raw, encoding="utf-8")
        results.append((n, before, after, "ok"))
        print(f"ch{n}: body {before} -> {after}")
    return results


def verify_all():
    print("\n=== VERIFY body dash (exclude title+footer) 481-600 ===")
    over = []
    max_info = []
    for i in range(481, 601):
        p = CHAPTERS / f"chapter-{i:03d}.md"
        if not p.exists():
            print(f"{i}: MISSING")
            continue
        title, rest, footer = split_body_footer_title(p.read_text(encoding="utf-8"))
        n = rest.count("——")
        if n > 8:
            over.append((i, n))
        if n > 0:
            max_info.append((n, i))
    print("body dash>8:", over if over else "NONE (=0)")
    max_info.sort(reverse=True)
    print("top residual:", max_info[:15])
    print(f"count body>8: {len(over)}")


if __name__ == "__main__":
    print("=== FIX MORSE 528 ===")
    ch = fix_morse_528()
    print(ch if ch else "(no morse replacements matched)")
    # re-scan to find residual >8
    residual = []
    for i in range(481, 601):
        p = CHAPTERS / f"chapter-{i:03d}.md"
        if not p.exists():
            continue
        title, rest, footer = split_body_footer_title(p.read_text(encoding="utf-8"))
        n = rest.count("——")
        if n > 8:
            residual.append(i)
    print("residual body>8 before re-polish:", residual)
    polish_residual(residual)
    verify_all()
