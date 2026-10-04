# -*- coding: utf-8 -*-
"""Final verification for P5 301-340 mechanical gates."""
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
forbidden = ["张远", "赵远航", "陈远桥", "初心咖啡", "2082咖啡馆"]
generic_footer = [
    "机械臂读数或共振代价写入失败账",
    "相关公开口径暂不升格",
    "本章围绕",
    "禁写纯蓝当前态",
]

def analyze(p):
    raw = p.read_text(encoding="utf-8")
    bom = raw.startswith("\ufeff")
    if bom:
        raw = raw[1:]
    lines = raw.splitlines()
    footer_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^---\s*$", line):
            after = "\n".join(lines[i + 1 :])
            if "本章关键点" in after or "本章围绕" in after:
                footer_idx = i
    body_lines = []
    for i, line in enumerate(lines):
        if footer_idx is not None and i >= footer_idx:
            break
        if i == 0 and line.startswith("# "):
            continue
        body_lines.append(line)
    body = "\n".join(body_lines)
    footer = "\n".join(lines[footer_idx:]) if footer_idx is not None else ""
    dash = body.count("——")
    cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
    has_kd = "**本章关键点：**" in raw
    nofoot = 0 if has_kd else 1
    forb = [f for f in forbidden if f in raw]
    gen = [g for g in generic_footer if g in raw]
    return {
        "bom": bom,
        "dash": dash,
        "cjk": cjk,
        "has_kd": has_kd,
        "nofoot": nofoot,
        "forb": forb,
        "gen": gen,
        "footer": footer,
    }

dash_gt8 = []
cjk_lt5000 = []
nofoot = []
forb_hits = []
gen_hits = []
bom_hits = []
print("CH | DASH | CJK  | KD | FORB | GEN")
for n in range(301, 341):
    p = base / ("chapter-%d.md" % n)
    if not p.exists():
        print("%3d MISSING" % n)
        continue
    r = analyze(p)
    if r["dash"] > 8:
        dash_gt8.append(n)
    if r["cjk"] < 5000:
        cjk_lt5000.append((n, r["cjk"]))
    if r["nofoot"]:
        nofoot.append(n)
    if r["forb"]:
        forb_hits.append((n, r["forb"]))
    if r["gen"]:
        gen_hits.append((n, r["gen"]))
    if r["bom"]:
        bom_hits.append(n)
    flag = ""
    if r["dash"] > 8:
        flag += " DASH!"
    if r["cjk"] < 5000:
        flag += " SHORT!"
    if r["nofoot"]:
        flag += " NOFOOT!"
    if r["forb"]:
        flag += " FORB!"
    print("%3d | %4d | %4d | %d  | %s | %s%s" % (
        n, r["dash"], r["cjk"], int(r["has_kd"]),
        ",".join(r["forb"]) or "-",
        ",".join(r["gen"]) or "-",
        flag,
    ))

print()
print("VERIFY GATES")
print("301-340 body dash>8 =", len(dash_gt8), dash_gt8)
print("301-340 CJK<5000 =", len(cjk_lt5000), cjk_lt5000)
print("301-340 nofoot =", len(nofoot), nofoot)
print("forbidden in 301-340 =", forb_hits)
print("generic footer residual =", gen_hits)
print("BOM =", bom_hits)

# full-book 初心咖啡 residual
print()
print("FULL-BOOK 初心咖啡 in chapters:")
count = 0
for p in sorted(base.glob("chapter-*.md")):
    t = p.read_text(encoding="utf-8")
    if "初心咖啡" in t:
        count += 1
        for i, line in enumerate(t.splitlines(), 1):
            if "初心咖啡" in line:
                print("  %s:%d %s" % (p.name, i, line.strip()[:120]))
print("count=", count)

# forbidden full-book residual in chapters only
print()
print("FULL-BOOK forbidden in chapters (张远/赵远航/陈远桥/2082咖啡馆):")
for f in ["张远", "赵远航", "陈远桥", "2082咖啡馆"]:
    hits = []
    for p in sorted(base.glob("chapter-*.md")):
        t = p.read_text(encoding="utf-8")
        if f in t:
            hits.append(p.name)
    print("  %s: %s" % (f, hits or "0"))
