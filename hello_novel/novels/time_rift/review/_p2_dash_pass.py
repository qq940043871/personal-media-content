# -*- coding: utf-8 -*-
"""P2 residual dash reduction + artifact repair for time_rift chapters."""
from pathlib import Path
import re

root = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

REPS = [
    (r"——或者说——", "，或者说，"),
    (r"——或者说", "，或者说"),
    (r"——更准确地说——", "，更准确地说，"),
    (r"——更准确地说", "，更准确地说"),
    (r"——换句话说——", "，换句话说，"),
    (r"——换句话说", "，换句话说"),
    (r"——不是([^——\n]{1,24})——而是", "，不是\\1，而是"),
    (r"——不是([^——\n]{1,24})——", "。不是\\1。"),
    (r"——一种", "，一种"),
    (r"——某种", "，某种"),
    (r"——像是", "，像是"),
    (r"——仿佛", "，仿佛"),
    (r"——如同", "，如同"),
    (r"——好像", "，好像"),
    (r"——那是", "。那是"),
    (r"——这是", "。这是"),
    (r"——那是([^——\n]{1,20})的", "，那是\\1的"),
    (r"——所有", "，所有"),
    (r"——无数", "，无数"),
    (r"——以及", "，以及"),
    (r"——包括", "，包括"),
    (r"——甚至", "，甚至"),
    (r"——尤其", "，尤其"),
    (r"——至少", "，至少"),
    (r"——大约", "，大约"),
    (r"——几乎", "，几乎"),
    (r"——完全", "，完全"),
    (r"——突然", "。突然"),
    (r"——然后", "。然后"),
    (r"——接着", "。接着"),
    (r"——于是", "。于是"),
    (r"——因此", "，因此"),
    (r"——所以", "，所以"),
    (r"——但是", "。但是"),
    (r"——可是", "。可是"),
    (r"——然而", "。然而"),
    (r"——因为", "。因为"),
    (r"——如果", "，如果"),
    (r"——当([^——\n]{1,16})时", "，当\\1时"),
    (r"——([^——\n]{1,10})——", "，\\1，"),
    (r"——([^——\n]{1,18})，", "，\\1，"),
    (r"，——", "，"),
    (r"。——", "。"),
    (r"——。", "。"),
    (r"——，", "，"),
    (r"——；", "；"),
    (r"：——", "："),
]

ARTIFACT_FIX = [
    (r"如果话，", "如果可以这样说，"),
    (r"是，(某种|进化|一种|一个)", r"是\1"),
    (r"的，的", "的"),
    (r"，，+", "，"),
    (r"。。+", "。"),
    (r"AR IA", "ARIA"),
    (r"A RIA", "ARIA"),
]


def soft_reduce(text: str) -> str:
    out = text
    for a, b in REPS:
        out = re.sub(a, b, out)
    out = re.sub(r"——([^——\n]{1,22}?)。", r"，\1。", out)
    out = re.sub(r"——([^——\n]{1,22}?)；", r"，\1；", out)
    out = re.sub(r"——([^——\n]{1,22}?)！", r"，\1！", out)
    out = re.sub(r"——([^——\n]{1,22}?)？", r"，\1？", out)
    # long parenthetical with comma inside: ——A，B——
    out = re.sub(r"——([^——\n]{1,40}?)——", r"，\1，", out)
    for a, b in ARTIFACT_FIX:
        if isinstance(b, str) and b.startswith("\\"):
            out = re.sub(a, b, out)
        else:
            out = re.sub(a, b, out)
    # residual awkward "，，"
    out = re.sub(r"，，+", "，", out)
    return out


def reduce_not_pattern(text: str, max_keep: int = 4) -> str:
    pat = re.compile(r"不是([^。！？\n]{1,25})而是")
    parts = []
    last = 0
    idx = 0
    for m in pat.finditer(text):
        idx += 1
        s, e = m.span()
        parts.append(text[last:s])
        if idx <= max_keep:
            parts.append(m.group(0))
        else:
            a = m.group(1)
            mode = idx % 3
            if mode == 0:
                parts.append(f"不止于{a}，更在于")
            elif mode == 1:
                parts.append(f"关键不在{a}，而在")
            else:
                parts.append(f"与其纠结是不是{a}，不如说在于")
        last = e
    parts.append(text[last:])
    return "".join(parts)


changed = 0
before_sum = 0
after_sum = 0
for p in sorted(root.glob("chapter-*.md")):
    m = re.search(r"chapter-(\d+)", p.name)
    if not m:
        continue
    if any(x in p.name for x in ["merged", "expanded", "-b"]):
        continue
    t = p.read_text(encoding="utf-8")
    if "本章关键点" in t:
        head, tail = t.split("本章关键点", 1)
    else:
        head, tail = t, ""
    d0 = head.count("——")
    if d0 < 35:
        continue
    before_sum += d0
    nt_head = soft_reduce(head)
    nt_head = reduce_not_pattern(nt_head, max_keep=4)
    d1 = nt_head.count("——")
    nt = nt_head + "本章关键点" + tail if "本章关键点" in t else nt_head
    if d1 < d0:
        p.write_text(nt, encoding="utf-8")
        changed += 1
        after_sum += d1

print(f"changed chapters: {changed}")
print(f"dash sum in processed band: {before_sum} -> {after_sum}")

# artifact scan
bad = []
for p in root.glob("chapter-*.md"):
    t = p.read_text(encoding="utf-8")
    issues = []
    if "如果话" in t:
        issues.append("如果话")
    if re.search(r"是，(某种|进化|一种)", t):
        issues.append("是，X")
    if "AR IA" in t or "A RIA" in t:
        issues.append("ARIA-space")
    if "，，" in t:
        issues.append("double-comma")
    if issues:
        bad.append((p.name, issues))
print("artifacts", bad[:15], "count", len(bad))

# final distribution
rows = []
for p in root.glob("chapter-*.md"):
    m = re.search(r"chapter-(\d+)", p.name)
    if not m:
        continue
    n = int(m.group(1))
    if any(x in p.name for x in ["merged", "expanded", "-b"]):
        continue
    t = p.read_text(encoding="utf-8")
    body = t.split("本章关键点")[0]
    rows.append((body.count("——"), n))
rows.sort(reverse=True)
print("top remaining:")
for d, n in rows[:15]:
    print(f"  ch{n:03d} {d}")
print(">=40", sum(1 for r in rows if r[0] >= 40))
print(">=20", sum(1 for r in rows if r[0] >= 20))
print("avg", sum(r[0] for r in rows) / len(rows))

vols = [(1,1,60),(2,61,120),(3,121,180),(4,181,240),(5,241,300),(6,301,360),(7,361,420),(8,421,480),(9,481,540),(10,541,600)]
print("vol avgs:")
for vi,a,b in vols:
    sub = [r[0] for r in rows if a <= r[1] <= b]
    if sub:
        print(f"  vol{vi}: {sum(sub)/len(sub):.1f}")
