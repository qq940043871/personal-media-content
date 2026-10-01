# -*- coding: utf-8 -*-
"""P4 wave3: CJK count for chapters 121-300, targets, footers, dash."""
import re
from pathlib import Path

CH_DIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
TARGETS = [236, 199, 233, 237, 169, 194, 158, 205, 299, 148,
           152, 182, 276, 154, 274, 272, 270, 160]

BANNED_FOOTER = ["本章围绕", "本章后续执行按", "对地镜像", "数字台账", "夜班交接五条"]


def analyze(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    body_lines = []
    footer_idx = None
    for i, line in enumerate(lines):
        if re.search(r"\*\*本章关键点", line):
            footer_idx = i
            break
        if line.strip().startswith("#"):
            continue
        body_lines.append(line)
    body = "\n".join(body_lines)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
    dash = len(re.findall(r"——", body))  # em-dash pairs
    has_footer = footer_idx is not None
    foot = "\n".join(lines[footer_idx:footer_idx + 8]) if footer_idx is not None else ""
    banned = [b for b in BANNED_FOOTER if b in foot or b in text[-800:]]
    title = lines[0] if lines else "?"
    return {
        "cjk": cjk,
        "dash": dash,
        "has_footer": has_footer,
        "foot": foot,
        "banned": banned,
        "title": title,
    }


def main():
    residual = []
    print("=== TARGETS ===")
    for n in sorted(TARGETS):
        p = CH_DIR / f"chapter-{n:03d}.md"
        if not p.exists():
            print(f"ch{n}: MISSING")
            continue
        a = analyze(p)
        print(f"ch{n} CJK={a['cjk']} dash={a['dash']} footer={a['has_footer']} banned={a['banned']}")
        print(f"  {a['title']}")
        print(f"  FOOT: {a['foot'][:220].replace(chr(10), ' | ')}")
        print()

    print("=== 121-300 residual CJK<5000 ===")
    for p in sorted(CH_DIR.glob("chapter-*.md")):
        m = re.match(r"chapter-(\d+)\.md", p.name)
        if not m:
            continue
        n = int(m.group(1))
        if not (121 <= n <= 300):
            continue
        a = analyze(p)
        if a["cjk"] < 5000:
            residual.append((n, a["cjk"], a["title"], a["dash"], a["has_footer"]))
    print(f"COUNT={len(residual)}")
    for r in residual:
        print(r)


if __name__ == "__main__":
    main()
