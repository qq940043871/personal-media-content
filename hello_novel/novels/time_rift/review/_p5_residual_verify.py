# -*- coding: utf-8 -*-
from pathlib import Path
import re

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
missing = []
ghost = []
flags = []
for p in sorted(base.glob("chapter-*.md")):
    t = p.read_text(encoding="utf-8")
    if "**本章关键点：**" not in t:
        missing.append(p.name)
    if "张远" in t or "赵远航" in t:
        ghost.append(p.name)
    for i, line in enumerate(t.splitlines(), 1):
        if "2082" in line and any(k in line for k in ["咖啡", "初遇", "首遇", "见面"]):
            flags.append((p.name, i, line[:100]))

print("missing_footer", len(missing), missing)
print("ghost", ghost)
print("2082_cafe_flags", flags)

# sample footer
t1 = (base / "chapter-001.md").read_text(encoding="utf-8")
print("--- ch001 footer ---")
idx = t1.find("**本章关键点：**")
print(t1[idx:idx+400] if idx>=0 else "MISSING")

t301 = (base / "chapter-301.md").read_text(encoding="utf-8")
idx = t301.find("**本章关键点：**")
print("--- ch301 footer ---")
print(t301[idx:idx+300] if idx>=0 else "MISSING")

# Dialog/K 481-600
low = []
for p in sorted(base.glob("chapter-*.md")):
    m = re.search(r"chapter-(\d+)", p.name)
    if not m:
        continue
    n = int(m.group(1))
    if not (481 <= n <= 600):
        continue
    t = p.read_text(encoding="utf-8")
    body = re.sub(r"(?s)\n---\n\*\*本章关键点：\*\*.*$", "", t)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
    dq = body.count('"')
    dk = (dq / 2) / max(cjk, 1) * 1000 if cjk else 0
    if dk < 4:
        low.append((n, round(dk, 2), cjk, dq))

print("low_dialog_count", len(low))
for row in low:
    print(row)

# asset chapters not hollowed: check key phrases still present
asset_checks = {
    528: ["李明", "时间"],
    530: ["时间之海", "融合"],
    531: ["陈维远"],
    555: ["时间之海"],
    600: ["时光倒流"],
}
for n, keys in asset_checks.items():
    p = base / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    print(f"ch{n}", {k: (k in t) for k in keys}, "footer", "**本章关键点：**" in t)

# ch594 key locks
t594 = (base / "chapter-594.md").read_text(encoding="utf-8")
print("ch594 时光倒流", "时光倒流" in t594)
print("ch594 初心咖啡 body", "初心咖啡" in re.sub(r"(?s)\n---\n.*$", "", t594))
print("ch594 2089首遇", "2089" in t594 and "首遇" in t594)
print("ch594 2082年的事", "那是2082年的事" in t594)
