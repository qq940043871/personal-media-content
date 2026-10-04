# -*- coding: utf-8 -*-
"""P5 cleanup: strip process notes from specific footers; fix ch127 leftover."""
from pathlib import Path
import re

CHDIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

# strip trailing process phrases from otherwise-specific footers
STRIP_PATTERNS = [
    r"[；;]\s*破折号压低[^。\n]*",
    r"^\s*-\s*破折号压低[^\n]*\n?",
    r"[；;]\s*dash 保持低位[^。\n]*",
    r"[；;]\s*正文不作同文公文尾[^。\n]*",
]

FOOTER_127 = [
    "事件：联盟空间中心文明共鸣现象发生；编号78/412/1023文明「准备好连接」",
    "代价：共鸣改变时间网络格局的同时，地面班表与对地成本账不能被宇宙叙事冲掉",
    "钩子：为什么是同时共鸣——准备好的判据尚未对市民可核对",
    "城市锚点：联盟会场对地译法 / 底层街区对照样本 / 时间网络侧读数译文",
]


def main():
    # 1) strip process notes
    cleaned = []
    for p in sorted(CHDIR.glob("chapter-*.md")):
        text = p.read_text(encoding="utf-8")
        m = re.search(r"((?:\n---\s*\n)?\*\*本章关键点[：:]?\*\*\s*\n)([\s\S]+)$", text)
        if not m:
            continue
        head, body = m.group(1), m.group(2)
        new_body = body
        for pat in STRIP_PATTERNS:
            new_body = re.sub(pat, "", new_body)
        # drop empty bullets
        lines = []
        for ln in new_body.splitlines():
            s = ln.strip()
            if not s:
                continue
            if s in ("-", "- ", "*", "* "):
                continue
            if re.match(r"^[-*·]\s*$", s):
                continue
            # drop bullets that are only process residue
            core = re.sub(r"^[-*·\s]+", "", s)
            if core in ("破折号压低", "dash 保持低位", "正文不作同文公文尾", "本批 C 类加厚不改本章既有情节结论"):
                continue
            lines.append(ln if ln.startswith("-") or ln.startswith("*") else ln)
        new_body = "\n".join(lines)
        if not new_body.endswith("\n"):
            new_body += "\n"
        if new_body != body:
            p.write_text(text[: m.start()] + head + new_body, encoding="utf-8")
            cleaned.append(p.name)

    print(f"stripped process notes from {len(cleaned)} files")
    for name in cleaned[:20]:
        print(" ", name)

    # 2) force ch127
    p = CHDIR / "chapter-127.md"
    text = p.read_text(encoding="utf-8")
    m = re.search(r"((?:\n---\s*\n)?\*\*本章关键点[：:]?\*\*\s*\n)([\s\S]+)$", text)
    assert m
    new_text = text[: m.start()] + m.group(1) + "\n".join(f"- {b}" for b in FOOTER_127) + "\n"
    p.write_text(new_text, encoding="utf-8")
    print("\nch127 rewritten:")
    print(p.read_text(encoding="utf-8")[-350:])


if __name__ == "__main__":
    main()
