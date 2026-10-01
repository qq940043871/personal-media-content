# -*- coding: utf-8 -*-
"""Count Chinese body chars for P3 batch4 chapters."""
import re
from pathlib import Path

CHAPTERS = Path(__file__).resolve().parents[1] / "novel" / "chapters"
TARGETS = [
    343, 353, 356, 360, 366, 367, 369, 372, 390, 393, 395,
    402, 403, 406, 407, 409, 422, 423, 430, 439, 441, 458, 466, 476,
]


def body_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8-sig")
    # Cut footer: from last '**本章关键点' or '**第X章完**' backwards
    for marker in ("**本章关键点", "**第"):
        idx = raw.rfind(marker)
        if idx != -1:
            raw = raw[:idx]
            break
    lines = raw.splitlines()
    body_lines = []
    started = False
    for line in lines:
        if not started:
            if line.startswith("# 第"):
                started = True
            continue
        body_lines.append(line)
    return "\n".join(body_lines)


def cn_count(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def main():
    rows = []
    for n in TARGETS:
        p = CHAPTERS / f"chapter-{n:03d}.md"
        if not p.exists():
            rows.append((n, None, "MISSING"))
            continue
        raw = p.read_text(encoding="utf-8-sig")
        body = body_text(p)
        cn = cn_count(body)
        has_footer = "**本章关键点" in raw
        dashes = len(re.findall(r"—{2}", raw))
        notA = len(re.findall(r"不是[^。！？\n]{1,20}——", raw)) + len(
            re.findall(r"关键不在[^。！？\n]{1,20}，而在", raw)
        )
        rows.append((n, cn, f"footer={has_footer} dash2={dashes} notA~{notA}"))
    for n, cn, note in rows:
        mark = "OK" if cn and cn >= 5000 else "LOW"
        print(f"{n:3d}  cn={cn}  {mark}  {note}")


if __name__ == "__main__":
    main()
