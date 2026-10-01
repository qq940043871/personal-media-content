# -*- coding: utf-8 -*-
"""Human-style polish for chapters with residual dash density.
Fixes awkward auto-rewrites and converts remaining —— into readable prose.
"""
from pathlib import Path
import re

root = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

# 1) Restore natural Chinese for botched "不是A而是B" rewrites
PHRASE_FIX = [
    # 不止于X，不是Y，更在于Z
    (r"不止于([^，。\n]{1,20})，不是([^，。\n]{1,20})，更在于", r"不只是\1，也不是\2，而是"),
    (r"不止于([^，。\n]{1,20})，而在于", r"不只是\1，更在于"),
    (r"不止于([^，。\n]{1,24})，更在于", r"不只是\1，更在于"),
    (r"不止于([^，。\n]{1,24})，不是([^，。\n]{1,24})", r"不只是\1，也不是\2"),
    (r"关键不在([^，。\n]{1,24})，而在", r"关键不在\1，而在"),
    (r"关键落在([^，。\n]{1,24})", r"关键落在\1"),
    (r"与其纠结是不是([^，。\n]{1,20})，不如说在于", r"与其说那是\1，不如说那是"),
    (r"与其说([^，。\n]{1,20})，不如说在于", r"与其说\1，不如说"),
    (r"与其说([^，。\n]{1,20})，不如看作", r"与其说\1，不如看作"),
    (r"不能只当作([^，。\n]{1,20})；更像", r"不能只当作\1，更像"),
    (r"并非([^，。\n]{1,20})，倒像", r"并非\1，倒像"),
    (r"事情不止于([^，。\n]{1,20})，关键落在", r"事情不止于\1，关键落在"),
    (r"把焦点从([^，。\n]{1,20})移开，真正起作用的是", r"把焦点从\1移开，真正起作用的是"),
    (r"更准确地看，([^，。\n]{1,20})这层不够，关键在", r"更准确地说，\1还不够，关键在"),
    # "是，X" leftovers
    (r"是，(某种|进化|一种|感受|连接)", r"是\1"),
    (r"意识是，", "意识是"),
    # double punctuation
    (r"，，+", "，"),
    (r"。。+", "。"),
]

# 2) Convert remaining explanatory —— into commas/periods when safe
DASH_RULES = [
    (r"——每一条", "。每一条"),
    (r"——所有", "。所有"),
    (r"——无数", "。无数"),
    (r"——一种", "，一种"),
    (r"——某种", "，某种"),
    (r"——那个", "，那个"),
    (r"——这个", "，这个"),
    (r"——那些", "。那些"),
    (r"——这些", "。这些"),
    (r"——一个是", "：一个是"),
    (r"——另一个是", "；另一个是"),
    (r"——冰冷的", "，冰冷的"),
    (r"——温暖的", "，温暖的"),
    (r"——正在", "。正在"),
    (r"——开始", "。开始"),
    (r"——突然", "。突然"),
    (r"——然后", "。然后"),
    (r"——接着", "。接着"),
    (r"——于是", "。于是"),
    (r"——直到", "，直到"),
    (r"——当", "，当"),
    (r"——如果", "，如果"),
    (r"——除非", "，除非"),
    (r"——仿佛", "，仿佛"),
    (r"——像是", "，像是"),
    (r"——如同", "，如同"),
    (r"——好像", "，好像"),
    (r"——因为", "。因为"),
    (r"——但是", "。但是"),
    (r"——可是", "。可是"),
    (r"——然而", "。然而"),
    (r"——所以", "，所以"),
    (r"——因此", "，因此"),
    (r"——而且", "，而且"),
    (r"——并且", "，并且"),
    (r"——甚至", "，甚至"),
    (r"——包括", "，包括"),
    (r"——以及", "，以及"),
    (r"——比如", "，比如"),
    (r"——例如", "，例如"),
    (r"——也就是说", "，也就是说"),
    (r"——或者说", "，或者说"),
    (r"——更准确地说", "，更准确地说"),
    (r"——不是([^，。\n]{1,18})，而是", "：不是\1，而是"),
    (r"——不是([^，。\n]{1,18})而是", "：不是\1，而是"),
]

# Keep at most KEEP dashes per chapter (dramatic only)
KEEP = 3


def polish_text(body: str) -> str:
    out = body
    for a, b in PHRASE_FIX:
        out = re.sub(a, b, out)
    for a, b in DASH_RULES:
        out = re.sub(a, b, out)

    # Fix remaining —— before quotes / mid-speech tags
    out = re.sub(r"——\"|——“", "，“", out)
    out = re.sub(r"\"——|”——", "”，", out)

    # Parenthetical ——X，Y—— or ——X——
    out = re.sub(r"——([^——\n]{1,35}?)——", r"（\1）", out)

    # —— at line end (trailing thought)
    out = re.sub(r"——\s*$", "。", out, flags=re.M)

    # ——X。 remaining
    out = re.sub(r"——([^——\n]{1,30}?)。", r"，\1。", out)
    out = re.sub(r"——([^——\n]{1,30}?)；", r"，\1；", out)

    # If still many dashes, convert lowest-value ones: —— followed by space/punct
    out = re.sub(r"——\s+", "，", out)

    # punctuation hygiene
    out = re.sub(r"，，+", "，", out)
    out = re.sub(r"。。+", "。", out)
    out = re.sub(r"，。", "。", out)
    out = re.sub(r"。，", "。", out)
    out = re.sub(r"（\s+）", "", out)
    out = re.sub(r"AR IA|A RIA", "ARIA", out)
    out = out.replace("如果话，", "如果可以这样说，")
    return out


def enforce_keep(body: str, keep: int = KEEP) -> str:
    """If still more than `keep` dashes, convert the rest (prefer mid-sentence)."""
    if body.count("——") <= keep:
        return body
    parts = body.split("——")
    if len(parts) < 2:
        return body
    out = [parts[0]]
    dash_used = 0
    for i, seg in enumerate(parts[1:], 1):
        prev = parts[i - 1]
        # keep first `keep` dashes that look dramatic (short prev, quote nearby)
        dramatic = dash_used < keep and (
            prev.endswith(("说", "道", "想", "是", "了"))
            or len(prev) < 8
            or "然后" in prev[-6:]
        )
        if dramatic:
            out.append("——")
            dash_used += 1
        else:
            # join with comma unless seg starts with close-punct
            if seg[:1] in "。，；：！？）」』":
                out.append("")
            else:
                out.append("，")
        out.append(seg)
    res = "".join(out)
    res = re.sub(r"，，+", "，", res)
    return res


def hand_fix_chapter(n: int, body: str) -> str:
    """Extra targeted fixes for known problem chapters."""
    replacements = {
        188: [
            ("表面辐射出来的电磁波，而是时间网络自身脉动的副产品——每一条时间线在流动时都会释放出微量的能量，那些能量汇聚在一起，形成了一种均匀的",
             "表面辐射出来的电磁波，而是时间网络自身脉动的副产品。每一条时间线在流动时都会释放出微量的能量，那些能量汇聚在一起，形成了一种均匀的"),
        ],
        282: [
            ("然后——", "然后，"),
            ("意识是，感受。是连接。是爱。", "意识是感受，是连接，是爱。"),
        ],
        15: [
            ("一种尖锐的、穿透性的电子蜂鸣", "那蜂鸣尖锐、穿透，"),
        ],
    }
    for a, b in replacements.get(n, []):
        body = body.replace(a, b)
    return body


target_nums = [188,140,146,440,15,282,176,136,135,246,95,45,449,59,260,150,91,388,180,173,119,89,63,261,207,213,208,70,564,130,66,259,249,247,153,133,104,101,93,340,238,175,151,142,139,113,88,10,559,556,534,258,201,198,196,174,162,75,74,61,35,30,20,551,550,533,477,350,318,225,217,120,117,92,73,60]

changed = 0
before = after = 0
for n in target_nums:
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    head, sep, tail = t.partition("本章关键点")
    d0 = head.count("——")
    nh = polish_text(head)
    nh = hand_fix_chapter(n, nh)
    nh = enforce_keep(nh, KEEP)
    d1 = nh.count("——")
    nt = nh + sep + tail if sep else nh
    if nt != t:
        p.write_text(nt, encoding="utf-8")
        changed += 1
        before += d0
        after += d1
    print(f"ch{n:03d}: {d0} -> {d1}")

print("SUMMARY changed", changed, "dash", before, "->", after)

# quality artifact scan on these chapters
bad = []
for n in target_nums:
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    issues = []
    if "不止于" in t and "更在于" in t:
        issues.append("不止于-更在于")
    if "与其纠结" in t:
        issues.append("与其纠结")
    if "如果话" in t:
        issues.append("如果话")
    if "，，" in t:
        issues.append("双逗号")
    if "AR IA" in t or "A RIA" in t:
        issues.append("ARIA")
    if issues:
        bad.append((n, issues))
print("artifacts", bad)

# final for this set
final = []
for n in target_nums:
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        continue
    d = p.read_text(encoding="utf-8").split("本章关键点")[0].count("——")
    final.append((d, n))
final.sort(reverse=True)
print("max in set", final[:8] if final else None)
print("avg in set", sum(x[0] for x in final) / max(len(final), 1))
print("still>=20", sum(1 for d, _ in final if d >= 20))
print("still>=10", sum(1 for d, _ in final if d >= 10))
