# -*- coding: utf-8 -*-
"""P4 wave3 expand helper: insert narrative before footer + replace footer."""
import re
import sys
from pathlib import Path

CH_DIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")


def expand_chapter(n: int, insert: str, footer: str) -> str:
    path = CH_DIR / f"chapter-{n:03d}.md"
    text = path.read_text(encoding="utf-8-sig")
    # strip BOM if present in content
    if text.startswith("\ufeff"):
        text = text[1:]
    m = re.search(r"\n---\s*\n\*\*本章关键点", text)
    if not m:
        m = re.search(r"\n\*\*本章关键点", text)
    if not m:
        raise SystemExit(f"ch{n}: footer not found")
    head = text[: m.start()].rstrip()
    new_text = head + "\n\n" + insert.strip() + "\n\n---\n\n**本章关键点：**\n" + footer.strip() + "\n"
    path.write_text(new_text, encoding="utf-8")
    # verify CJK
    lines = new_text.splitlines()
    body = []
    for line in lines:
        if line.strip().startswith("#"):
            continue
        if re.search(r"\*\*本章关键点", line):
            break
        body.append(line)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", "\n".join(body)))
    dash = len(re.findall(r"——", "\n".join(body)))
    print(f"ch{n}: CJK={cjk} dash={dash} ok={cjk>=5000}")
    return new_text


if __name__ == "__main__":
    # demo empty
    pass
