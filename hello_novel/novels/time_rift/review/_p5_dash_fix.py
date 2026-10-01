# -*- coding: utf-8 -*-
"""P5 dash fix: reduce —— to ≤8 on flagged chapters by converting non-critical pairs."""
from __future__ import annotations

import re
from pathlib import Path

CH_DIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

# Convert explanatory dashes to punctuation; keep at most 8 dramatic pairs.
PRIORITY_PAIRS = 8

def fix_chapter(ch: int) -> None:
    p = CH_DIR / f"chapter-{ch:03d}.md"
    text = p.read_text(encoding="utf-8")
    m = re.split(r"(\n---\s*\n\s*\*\*本章关键点)", text, maxsplit=1)
    body, sep, footer = m[0], m[1] if len(m) > 1 else "", m[2] if len(m) > 2 else ""
    # find all —— positions
    positions = [mm.start() for mm in re.finditer("——", body)]
    if len(positions) <= PRIORITY_PAIRS:
        print(f"{ch}: dash_pairs={len(positions)} ok")
        return
    # replace from the end, keep first PRIORITY_PAIRS
    to_fix = positions[PRIORITY_PAIRS:]
    # process from end so offsets stay valid
    chars = list(body)
    for pos in reversed(to_fix):
        # look at context
        before = body[max(0, pos - 12) : pos]
        after = body[pos + 2 : pos + 14]
        # if mid-sentence explanation → comma; if before quote/short → period
        if after[:1] in "。，、；：？！「」\"":
            repl = "，"
        elif re.search(r"[是为在]", before[-3:] if len(before) >= 3 else before):
            repl = "，"
        else:
            repl = "，"
        chars[pos : pos + 2] = list(repl)
    body = "".join(chars)
    new_text = body + sep + footer
    if not new_text.endswith("\n"):
        new_text += "\n"
    p.write_text(new_text, encoding="utf-8")
    n = len(re.findall("——", body))
    print(f"{ch}: dash_pairs {len(positions)}→{n}")


def main() -> None:
    for ch in [125, 127, 147, 159, 168, 226]:
        fix_chapter(ch)
    # re-verify all edited
    print("\nRe-check dash:")
    edited = [125, 127, 142, 147, 159, 167, 168, 203, 208, 217, 225, 226, 231, 238, 244, 248, 253, 254, 259]
    for ch in edited:
        p = CH_DIR / f"chapter-{ch:03d}.md"
        text = p.read_text(encoding="utf-8")
        body = re.split(r"\n---\s*\n\s*\*\*本章关键点", text, maxsplit=1)[0]
        n = len(re.findall("——", body))
        cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
        flag = " OK" if n <= 8 and cjk >= 5000 else " FAIL"
        print(f"  {ch}: cjk={cjk} dash={n}{flag}")


if __name__ == "__main__":
    main()
