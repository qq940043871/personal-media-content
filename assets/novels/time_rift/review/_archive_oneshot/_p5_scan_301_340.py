# -*- coding: utf-8 -*-
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
forbidden = ["张远", "赵远航", "陈远桥", "初心咖啡", "2082咖啡馆"]
results = []

for n in range(301, 341):
    p = base / ("chapter-%d.md" % n)
    if not p.exists():
        results.append({"ch": n, "missing": True})
        continue
    raw = p.read_text(encoding="utf-8")
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    lines = raw.splitlines()

    # footer: last --- section that contains 本章关键点 or looks like footer
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
        if re.match(r"^---\s*$", line) and footer_idx is not None and i == footer_idx:
            break
        body_lines.append(line)
    body_text = "\n".join(body_lines)
    dash_count = body_text.count("——")
    cjk = len(re.findall(r"[\u4e00-\u9fff]", body_text))
    has_kd = "**本章关键点：**" in raw or "**本章关键点**" in raw
    found_forbidden = [f for f in forbidden if f in raw]
    m = re.search(r"^# (.+)$", raw, re.M)
    title_s = m.group(1) if m else ""
    # footer cost/hook sample
    footer = "\n".join(lines[footer_idx:]) if footer_idx is not None else ""
    results.append(
        {
            "ch": n,
            "title": title_s,
            "dash": dash_count,
            "cjk": cjk,
            "has_kd": has_kd,
            "forbidden": found_forbidden,
            "footer_idx": footer_idx,
            "lines": len(lines),
            "footer": footer,
        }
    )

print("CH | DASH | CJK  | KD | FORB | TITLE")
for r in results:
    if r.get("missing"):
        print("%3d | MISSING" % r["ch"])
        continue
    flag = ""
    if r["dash"] > 8:
        flag += " DASH!"
    if r["cjk"] < 5000:
        flag += " SHORT!"
    if not r["has_kd"]:
        flag += " NOKD!"
    if r["forbidden"]:
        flag += " FORB!"
    forb = ",".join(r["forbidden"]) if r["forbidden"] else "-"
    print(
        "%3d | %4d | %4d | %d  | %s | %s%s"
        % (r["ch"], r["dash"], r["cjk"], int(r["has_kd"]), forb, r["title"][:42], flag)
    )

print()
print("DASH>8:", [r["ch"] for r in results if not r.get("missing") and r["dash"] > 8])
print("CJK<5000:", [r["ch"] for r in results if not r.get("missing") and r["cjk"] < 5000])
print("NOKD:", [r["ch"] for r in results if not r.get("missing") and not r["has_kd"]])
print(
    "FORB:",
    [(r["ch"], r["forbidden"]) for r in results if not r.get("missing") and r["forbidden"]],
)
print("MISSING:", [r["ch"] for r in results if r.get("missing")])
print()
# detail short / dash / nokd
print("=== DETAIL ===")
for r in results:
    if r.get("missing"):
        continue
    if r["dash"] > 8 or r["cjk"] < 5000 or not r["has_kd"] or r["forbidden"]:
        print("--- ch %d  %s" % (r["ch"], r["title"]))
        print("    dash=%d cjk=%d kd=%s forb=%s" % (r["dash"], r["cjk"], r["has_kd"], r["forbidden"]))
        print("    footer:")
        for fl in r["footer"].splitlines()[:12]:
            print("      " + fl[:100])
