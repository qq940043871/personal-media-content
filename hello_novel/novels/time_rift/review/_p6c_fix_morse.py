# -*- coding: utf-8 -*-
"""Restore Morse/letter-by-letter dialogue dashes damaged by auto polish.
Scan 481-600 for quote-internal single-char+comma patterns.
"""
import re
from pathlib import Path

CHAPTERS = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

# Explicit restore for ch528 Morse deathbed taps
p528 = CHAPTERS / "chapter-528.md"
raw = p528.read_text(encoding="utf-8")
pairs = [
    ('"看——日，出。"', '"看——日——出。"'),
    ('"想，看，开，始。"', '"想——看——开——始。"'),
    ('"你——好，的。"', '"你——好——的。"'),
    ('"我——也，好。"', '"我——也——好。"'),
    ('"太，阳，真，美。"', '"太——阳——真——美。"'),
    ('"太——阳，真，美。"', '"太——阳——真——美。"'),
    ('"太——阳——真，美。"', '"太——阳——真——美。"'),
]
fixed528 = []
for a, b in pairs:
    if a in raw:
        raw = raw.replace(a, b)
        fixed528.append((a, b))
p528.write_text(raw, encoding="utf-8")
print("528 fixed:", fixed528)

# Scan for suspicious short-char comma speech that may be damaged Morse
print("\n=== suspicious quote patterns 481-600 ===")
pat = re.compile(r"[「\"']([^\n「」\"']{0,20}[,，][^\n「」\"']{0,20})[」\"']")
for i in range(481, 601):
    p = CHAPTERS / f"chapter-{i:03d}.md"
    if not p.exists():
        continue
    t = p.read_text(encoding="utf-8")
    for m in pat.finditer(t):
        s = m.group(1)
        # short fragments with single CJK chars separated by commas
        if re.match(r"^[^\w]{0,2}([\u4e00-\u9fff][,，]){1,6}[\u4e00-\u9fff]。?$", s.strip()):
            print(f"  {i}: {s!r}")

# Count body dash for 528 after restore
def split_rest(raw):
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    lines = raw.splitlines()
    footer_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^---\s*$", line):
            after = "\n".join(lines[i + 1 :])
            if "本章关键点" in after:
                footer_idx = i
                break
    body = "\n".join(lines[:footer_idx] if footer_idx is not None else lines)
    bl = body.splitlines()
    rest = "\n".join(bl[1:] if bl and bl[0].startswith("# ") else bl)
    return rest

rest = split_rest(p528.read_text(encoding="utf-8"))
print(f"\n528 body dash after Morse restore: {rest.count('——')}")
# show remaining dash contexts
idx = 0
n = 0
while True:
    pos = rest.find("——", idx)
    if pos < 0:
        break
    n += 1
    print(f"  [{n}] …{rest[max(0,pos-20):pos]}——{rest[pos+2:pos+22]}…")
    idx = pos + 2
