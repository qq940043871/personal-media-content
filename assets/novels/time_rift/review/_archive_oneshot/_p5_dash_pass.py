# -*- coding: utf-8 -*-
"""P5 body dash literary pass for chapters 301-340.
Converts explanatory —— to sentence punctuation; keeps <=3 dramatic ones.
Does not touch footer after --- that starts 本章关键点.
Does not change plot.
"""
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
TARGET_CHS = [301, 302, 304, 305, 307, 313, 314, 317, 321, 323, 324, 331, 332, 335, 336, 337, 338]

# Keep max dramatic dashes in body
KEEP_MAX = 3


def split_file(raw):
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    lines = raw.splitlines()
    footer_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^---\s*$", line):
            after = "\n".join(lines[i + 1 :])
            if "本章关键点" in after or "本章围绕" in after:
                footer_idx = i
    if footer_idx is None:
        return raw, ""
    return "\n".join(lines[:footer_idx]), "\n".join(lines[footer_idx:])


def is_dramatic(before, after):
    """Keep if dialogue interruption / truncated speech / key reveal."""
    b = before[-30:] if before else ""
    a = after[:40] if after else ""
    # truncated dialogue: ends mid-word inside quotes
    if re.search(r'[「"\'"]?[^「」"\']{0,12}$', b):
        # if dash is inside quotes (count quotes in before odd number of open)
        open_q = before.count('"') + before.count('"') + before.count('"') + before.count("「")
        close_q = before.count('"') + before.count('"') + before.count('"') + before.count("」")
        if open_q > close_q:
            # inside dialogue — dramatic if short trailing fragment
            trail = re.search(r'([^「」"\']{1,12})$', before)
            if trail and len(trail.group(1)) <= 8:
                return True
    # explicit dramatic patterns
    patterns = [
        r"它是$",
        r"但$",
        r"因为$",
        r"难是因为$",
        r"而是$",
        r"如果[^。]{0,20}$",
        r"不$",
        r"我$",
        r"为什么$",
        r"两下，三下$",
        r"一下，两下",
        r"「[^」]{0,15}$",
        r'\"[^\"]{0,12}$',
        r'"[^"]{0,12}$',
    ]
    for p in patterns:
        if re.search(p, b):
            return True
    # keep if after is incomplete fragment too (ellipsis style)
    if re.match(r'^["「]?[^\n]{0,6}(算了|不是|而是)', a):
        return False  # still convert these explanatory
    return False


def convert_dash(before, after):
    """Pick replacement punctuation for explanatory dash."""
    b = before[-5:] if before else ""
    a = after[:20] if after else ""
    # list-like after
    if re.match(r"^\s*(第一|首先|有些|有的|包括|那些|比如|例如)", a):
        return "："
    # "不是X——而是Y" / "不是X——Y"
    if re.search(r"(不是|并非|而不|而非)[^。]{0,12}$", b) or re.match(r"^(而是|并非|不是)", a):
        return "，"
    # "X——Y" where Y explains definition
    if re.match(r"^\s*(那|这|一个|所有|任何|它|他|她|我|你|我们)", a):
        return "，"
    # after comma-ish
    if b.endswith("的") or b.endswith("了") or b.endswith("着") or b.endswith("过"):
        return "，"
    # after noun phrase often colon-like when explaining
    if re.match(r"^\s*(是一种|是时间|是所有|是两个|是人类|是宇宙|是选择|是服务|是桥梁)", a):
        return "，"
    # default: comma for flow, period-like if long pause needed
    if len(a) > 0 and a[0] in "但是所以因为":
        return "，"
    # "那就是——" style
    if b.endswith("是"):
        return "，"
    return "，"


def reduce_dashes(body):
    positions = []
    idx = 0
    while True:
        pos = body.find("——", idx)
        if pos < 0:
            break
        positions.append(pos)
        idx = pos + 2

    # score each
    scored = []
    for pos in positions:
        before = body[:pos]
        after = body[pos + 2 :]
        dramatic = is_dramatic(before, after)
        scored.append((pos, dramatic, before, after))

    # keep up to KEEP_MAX dramatic; prefer later/mid dialogue ones if more
    dramatic_idx = [i for i, s in enumerate(scored) if s[1]]
    if len(dramatic_idx) > KEEP_MAX:
        # keep the ones with shortest "before tail" (tightest interruptions)
        dramatic_idx_sorted = sorted(
            dramatic_idx,
            key=lambda i: len(re.findall(r"[^「」\"\"]{0,12}$", scored[i][2])[-1] if re.findall(r"[^「」\"\"]{0,12}$", scored[i][2]) else ""),
        )
        keep_set = set(dramatic_idx_sorted[:KEEP_MAX])
    else:
        keep_set = set(dramatic_idx)

    # rebuild body from end so positions stay valid
    new_body = body
    log = []
    for i in range(len(scored) - 1, -1, -1):
        pos, dramatic, before, after = scored[i]
        if i in keep_set:
            log.append(("KEEP", pos, before[-20:] + "——" + after[:20]))
            continue
        rep = convert_dash(before, after)
        new_body = new_body[:pos] + rep + new_body[pos + 2 :]
        log.append(("CONV", pos, before[-20:] + "→" + rep + "←" + after[:20]))
    return new_body, log


def main():
    results = []
    for n in TARGET_CHS:
        p = base / ("chapter-%d.md" % n)
        raw = p.read_text(encoding="utf-8")
        body, footer = split_file(raw)
        # body may include title line
        lines = body.splitlines()
        title_line = lines[0] if lines and lines[0].startswith("# ") else ""
        body_rest = "\n".join(lines[1:] if title_line else lines)
        count_before = body_rest.count("——")
        if count_before <= 8:
            results.append((n, count_before, count_before, "skip"))
            continue
        new_rest, log = reduce_dashes(body_rest)
        count_after = new_rest.count("——")
        # if still >8, force-convert non-kept more aggressively
        if count_after > KEEP_MAX:
            # convert extra until <= KEEP_MAX
            pos = 0
            while count_after > KEEP_MAX:
                ppos = new_rest.find("——", pos)
                if ppos < 0:
                    break
                # don't convert if would go below 0; just convert first ones
                before = new_rest[:ppos]
                after = new_rest[ppos + 2 :]
                rep = convert_dash(before, after)
                new_rest = new_rest[:ppos] + rep + new_rest[ppos + 2 :]
                count_after = new_rest.count("——")
                pos = ppos + 1
                log.append(("FORCE", ppos, "force"))
        new_body = (title_line + "\n" if title_line else "") + new_rest
        new_raw = new_body + ("\n" if not new_body.endswith("\n") else "") + footer
        if not new_raw.endswith("\n"):
            new_raw += "\n"
        p.write_text(new_raw, encoding="utf-8")
        results.append((n, count_before, count_after, "ok"))
        print("ch%d: %d -> %d  (%s)" % (n, count_before, count_after, "ok"))

    print("\nSUMMARY")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
