# -*- coding: utf-8 -*-
"""P6-C scan body dash for chapters 481-600 (exclude footer after 本章关键点)."""
import re
from pathlib import Path

CHAPTERS = Path(__file__).resolve().parents[1] / "novel" / "chapters"
FOOTER_MARK = "**本章关键点：**"
FOOTER_MARK2 = "**本章关键点**"

def body_text(t: str) -> str:
    t = t.lstrip("\ufeff")
    for mark in (FOOTER_MARK, FOOTER_MARK2, "---\n**本章关键点"):
        idx = t.find(mark)
        if idx >= 0:
            return t[:idx]
    # also try splitting on ---\n\n**
    m = re.search(r"\n---\s*\n\*\*本章", t)
    if m:
        return t[: m.start()]
    return t

def dash_count(t: str) -> int:
    return len(re.findall("——", t))

results = {}
for i in range(481, 601):
    p = CHAPTERS / f"chapter-{i:03d}.md"
    if not p.exists():
        print(f"{i}: MISSING")
        continue
    raw = p.read_text(encoding="utf-8")
    body = body_text(raw)
    n = dash_count(body)
    results[i] = n
    if n > 8:
        print(f"{i}: {n}  BODY_DASH>8")
    elif n > 0:
        pass  # quiet for <=8

print("\n=== ALL >8 sorted ===")
over = sorted([(n, i) for i, n in results.items() if n > 8], reverse=True)
for n, i in over:
    print(f"{i}({n})", end=",")
print()
print(f"\nTotal chapters scanned: {len(results)}")
print(f"dash>8 count: {len(over)}")
print(f"dash>0 count: {sum(1 for n in results.values() if n > 0)}")
print(f"sum dash: {sum(results.values())}")

print("\n=== baseline comparison (listed in task) ===")
baseline = {
    585:20,542:18,587:18,494:17,568:17,535:17,491:17,497:16,485:15,553:15,
    579:14,569:14,565:13,512:13,489:13,594:13,528:13,531:13,521:13,596:12,
    563:12,570:12,560:12,541:11,488:11,481:11,532:11,546:11,586:10,584:10,
    555:10,599:9,573:9,483:9
}
print("baseline listed | current | status")
for i, b in sorted(baseline.items()):
    c = results.get(i, -1)
    status = "OVER" if c > 8 else "ok"
    print(f"  {i}: baseline={b} current={c} {status}")
