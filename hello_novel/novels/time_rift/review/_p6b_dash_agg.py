# -*- coding: utf-8 -*-
"""Aggressive body dash pass for P6-B touched 541-600 chapters."""
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).parent))
from _p6b_common import strip_bom, _footer_index, body_cjk, dash_count

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")


def aggressive_dash(path, keep_max=6):
    raw = strip_bom(path.read_text(encoding="utf-8"))
    lines = raw.splitlines()
    footer_idx = _footer_index(lines)
    if footer_idx is None:
        body_lines = lines[:]
        footer_lines = []
    else:
        body_lines = lines[:footer_idx]
        footer_lines = lines[footer_idx:]
    title = ""
    content_lines = []
    for i, line in enumerate(body_lines):
        if i == 0 and line.startswith("# "):
            title = line
        else:
            content_lines.append(line)
    text = "\n".join(content_lines)
    # Find all dash occurrences (treat —— as one unit first)
    matches = []
    i = 0
    while i < len(text):
        if text.startswith("\u2014\u2014", i):
            matches.append((i, i + 2, "db"))
            i += 2
        elif text[i] == "\u2014":
            matches.append((i, i + 1, "sb"))
            i += 1
        else:
            i += 1
    if len(matches) <= keep_max:
        return dash_count(path.read_text(encoding="utf-8"))
    # Classify keep vs replace
    keep = set()
    for idx, (s, e, kind) in enumerate(matches):
        before = text[max(0, s - 30):s]
        after = text[e:e + 30]
        # keep truncated dialogue
        if re.search(r'["「][^」"]{0,15}$', before) and len(keep) < keep_max:
            keep.add(idx)
            continue
        # keep short dramatic single dash before key word
        if kind == "sb" and re.search(r"(是|不|而|却|他|她|我)$", before) and len(keep) < keep_max:
            keep.add(idx)
            continue
    # Replace all others
    out_chars = list(text)
    # Work with replacements on original indices via sentinel
    pieces = []
    last = 0
    for idx, (s, e, kind) in enumerate(matches):
        pieces.append(text[last:s])
        if idx in keep:
            pieces.append(text[s:e])
        else:
            before = text[max(0, s - 15):s]
            after = text[e:e + 15]
            # dialogue-adjacent punctuation already?
            if before and before[-1] in "，。；：？！、":
                pieces.append("")
            elif after and after[:1] in "，。；：？！、":
                pieces.append("")
            elif re.search(r"是$|为$|像$|非$|叫$|称$", before):
                pieces.append("，")
            else:
                pieces.append("，")
        last = e
    pieces.append(text[last:])
    new_text = "".join(pieces)
    # clean double punctuation
    new_text = re.sub(r"，{2,}", "，", new_text)
    new_text = re.sub(r"，([。；：？！、])", r"\1", new_text)
    new_text = re.sub(r"([。\？\！])，", r"\1", new_text)
    new_body = []
    if title:
        new_body.append(title)
    new_body.extend(new_text.splitlines())
    out = "\n".join(new_body).rstrip() + "\n"
    if footer_lines:
        footer = "\n".join(footer_lines)
        if not footer.startswith("---"):
            footer = "---\n" + footer
        out += footer
    if not out.endswith("\n"):
        out += "\n"
    path.write_text(out, encoding="utf-8")
    return dash_count(out)


def main():
    targets = list(range(541, 601))
    for n in targets:
        p = base / ("chapter-%d.md" % n)
        if not p.exists():
            continue
        before = dash_count(p.read_text(encoding="utf-8"))
        if before <= 8:
            continue
        after = aggressive_dash(p, keep_max=6)
        cjk = body_cjk(p.read_text(encoding="utf-8"))
        print("dash ch%d: %d -> %d cjk=%d" % (n, before, after, cjk))

if __name__ == "__main__":
    main()
