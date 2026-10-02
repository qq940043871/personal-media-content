# -*- coding: utf-8 -*-
"""Shared helpers for P6-B batch2 expansion scripts."""
from pathlib import Path
import re

FOOTER_MARK = "本章关键点"


def strip_bom(raw):
    if raw.startswith("\ufeff"):
        return raw[1:]
    return raw


def _footer_index(lines):
    """Return index of the `---` line that introduces the chapter footer.

    Chapters may contain mid-body `---` scene breaks. The true footer is the
    last `---` immediately followed (within a few lines) by 本章关键点/本章围绕.
    """
    footer_idx = None
    for i, line in enumerate(lines):
        if not re.match(r"^---\s*$", line):
            continue
        # look ahead a short window for the footer marker
        window = "\n".join(lines[i + 1 : i + 8])
        if FOOTER_MARK in window or "本章围绕" in window:
            footer_idx = i
    return footer_idx


def split_file(raw):
    raw = strip_bom(raw)
    lines = raw.splitlines()
    footer_idx = _footer_index(lines)
    if footer_idx is None:
        return raw.rstrip() + "\n", ""
    body = "\n".join(lines[:footer_idx]).rstrip() + "\n"
    footer = "\n".join(lines[footer_idx:])
    return body, footer


def body_cjk(text):
    raw = strip_bom(text)
    # direct: cut at real footer mark
    lines = strip_bom(text).splitlines()
    footer_idx = _footer_index(lines)
    if footer_idx is None:
        # fallback: cut at marker
        body_text = raw
        m = re.search(r"^---\s*$[\s\S]*?\*\*本章关键点", raw, re.M)
        if m:
            body_text = raw[: m.start()]
    else:
        body_text = "\n".join(lines[:footer_idx])
    body_lines = []
    for i, line in enumerate(body_text.splitlines()):
        if i == 0 and line.startswith("# "):
            continue
        body_lines.append(line)
    return len(re.findall(r"[\u4e00-\u9fff]", "\n".join(body_lines)))


def body_dash_count(text):
    raw = strip_bom(text)
    lines = raw.splitlines()
    footer_idx = _footer_index(lines)
    if footer_idx is None:
        body_text = raw
        m = re.search(r"^---\s*$[\s\S]*?\*\*本章关键点", raw, re.M)
        if m:
            body_text = raw[: m.start()]
    else:
        body_text = "\n".join(lines[:footer_idx])
    body_lines = []
    for i, line in enumerate(body_text.splitlines()):
        if i == 0 and line.startswith("# "):
            continue
        body_lines.append(line)
    return len(re.findall(r"\u2014", "\n".join(body_lines)))


def dash_count(text):
    return body_dash_count(text)


def insert_blocks(path, expand_map):
    """Insert scene blocks before footer for chapters in expand_map."""
    n = None
    for k in expand_map:
        n = k
        break
    raw = path.read_text(encoding="utf-8")
    body, footer = split_file(raw)
    block = expand_map[n].strip()
    marker = block[:40]
    if marker and marker in body:
        out = body
    else:
        out = body.rstrip() + "\n\n" + block + "\n\n"
    if footer:
        if not out.endswith("\n"):
            out += "\n"
        if not footer.startswith("---"):
            footer = "---\n" + footer
        out += footer
    if not out.endswith("\n"):
        out += "\n"
    path.write_text(out, encoding="utf-8")
    return out


def is_dramatic_dash(before, after):
    b = before[-24:] if before else ""
    a = after[:30] if after else ""
    # truncated dialogue
    if re.search(r'["「][^」"]{0,12}$', b):
        return True
    if re.search(r"(是|但|因为|不|我|你|他|她|它|却|而)$", b) and len(a) > 0:
        return True
    # A——不是B pattern keep limited handled outside
    return False


def compress_dashes(path, keep_max=8):
    """Rewrite explanatory em-dashes in body to punctuation; keep <= keep_max dramatic."""
    raw = strip_bom(path.read_text(encoding="utf-8"))
    body, footer = split_file(raw)
    lines = body.splitlines()
    title_line = ""
    body_only = []
    for i, line in enumerate(lines):
        if i == 0 and line.startswith("# "):
            title_line = line
        else:
            body_only.append(line)
    text = "\n".join(body_only)
    # Count current
    dashes = [(m.start(), m.group()) for m in re.finditer(r"\u2014\u2014|\u2014", text)]
    if len(dashes) <= keep_max:
        return raw
    # Process from end so offsets stay valid
    kept = 0
    chars = list(text)
    # First pass: classify
    replacements = []  # (start, end, newstr)
    for pos, g in dashes:
        end = pos + len(g)
        before = text[:pos]
        after = text[end:]
        dramatic = is_dramatic_dash(before, after)
        # not A——but B pattern: convert first of pair sometimes keep one
        if dramatic and kept < keep_max:
            kept += 1
            continue
        # choose replacement
        b = before[-20:] if before else ""
        a = after[:20] if after else ""
        if re.search(r"[，。；：？！]$", b) or (a.startswith(" ") or a[:1] in "，。"):
            new = ""
        elif re.search(r"是$|为$|叫$|称$|做$|像$|非$", b):
            new = "，"
        elif a[:1] and re.search(r"^[一-鿿]", a) and len(b) > 2:
            new = "，"
        else:
            new = "，"
        # avoid double punctuation
        if new:
            if b and b[-1] in "，。；：？！、":
                new = ""
            if a and a[:1] in "，。；：？！、":
                new = ""
        replacements.append((pos, end, new))
    # apply from end
    for start, end, new in sorted(replacements, key=lambda x: -x[0]):
        # remove entire —— or —
        text = text[:start] + new + text[end:]
    new_body_lines = []
    if title_line:
        new_body_lines.append(title_line)
    new_body_lines.extend(text.splitlines())
    new_body = "\n".join(new_body_lines).rstrip() + "\n"
    out = new_body
    if footer:
        if not footer.startswith("---"):
            footer = "---\n" + footer
        if not out.endswith("\n"):
            out += "\n"
        out += footer
    if not out.endswith("\n"):
        out += "\n"
    path.write_text(out, encoding="utf-8")
    return out


def personalize_footer(path, new_footer_lines):
    """Replace footer content after --- with new conflict-oriented bullets."""
    raw = strip_bom(path.read_text(encoding="utf-8"))
    body, footer = split_file(raw)
    lines = ["---", "**本章关键点：**"] + list(new_footer_lines)
    out = body.rstrip() + "\n\n" + "\n".join(lines) + "\n"
    path.write_text(out, encoding="utf-8")
    return out
