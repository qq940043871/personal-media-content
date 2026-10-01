# -*- coding: utf-8 -*-
"""Fix residual body dash>8 in 303/308/325 and strip BOM in 301-340."""
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

def split_file(raw):
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    lines = raw.splitlines()
    footer_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^---\s*$", line):
            after = "\n".join(lines[i + 1 :])
            if "本章关键点" in after or "本章围绕" in after:
                footer_idx = i
    if footer_idx is None:
        return raw.rstrip() + "\n", ""
    return "\n".join(lines[:footer_idx]).rstrip() + "\n", "\n".join(lines[footer_idx:])

def body_part(body):
    lines = body.splitlines()
    if lines and lines[0].startswith("# "):
        return "\n".join(lines[1:])
    return body

def convert_dash(before, after):
    b = before[-8:] if before else ""
    a = after[:20] if after else ""
    if re.search(r"(不是|并非|而不|而非)[^。]{0,12}$", b) or re.match(r"^(而是|并非|不是)", a):
        return "，"
    if re.match(r"^\s*(那|这|一个|所有|任何|它|他|她|我|你|我们|不是)", a):
        return "，"
    return "，"

def reduce_to(body, keep_max=3, target_max=8):
    rest = body_part(body)
    count = rest.count("——")
    if count <= target_max:
        return body, count, count
    # convert until <= target_max, preferring to keep at most keep_max dramatic
    # simple: convert from the left until count <= target_max, but skip obvious dialogue interruptions
    pos_list = []
    idx = 0
    while True:
        p = rest.find("——", idx)
        if p < 0:
            break
        pos_list.append(p)
        idx = p + 2
    # classify dramatic
    def is_dram(p):
        before = rest[:p]
        after = rest[p+2:]
        b = before[-12:] if before else ""
        open_q = before.count('"') + before.count('"') + before.count('"') + before.count("「")
        close_q = before.count('"') + before.count('"') + before.count('"') + before.count("」")
        if open_q > close_q:
            trail = re.search(r'([^「」\"\']{1,8})$', before)
            if trail and len(trail.group(1)) <= 6:
                return True
        return bool(re.search(r"(它是|但|因为|不|我|为什么|一下|两下|三下)$", b))

    keeps = [p for p in pos_list if is_dram(p)][:keep_max]
    # convert non-keeps from the end
    new_rest = rest
    for p in reversed(pos_list):
        if new_rest.count("——") <= target_max:
            break
        if p in keeps:
            continue
        # find current position of this dash in new_rest - safer rebuild by converting all non-keep
    # rebuild all at once
    out = []
    last = 0
    kept = 0
    for p in pos_list:
        out.append(rest[last:p])
        if p in keeps and kept < keep_max and rest.count("——") > target_max:
            # only keep if we still need to reduce; actually keep all in keeps until under target
            if sum(1 for q in pos_list if q in keeps and q >= p) + rest[p:].count("——") - rest[p+2:].count("——") :
                pass
            if (rest[:p].count("——") + (1 if p in keeps else 0) + rest[p+2:].count("——")) :
                pass
        # simpler decision
        if p in keeps:
            # keep if total after keeping this would still allow eventual <= target? just keep up to keep_max
            if kept < keep_max:
                out.append("——")
                kept += 1
                last = p + 2
                continue
        rep = convert_dash(rest[:p], rest[p+2:])
        out.append(rep)
        last = p + 2
    out.append(rest[last:])
    new_rest = "".join(out)
    # if still > target, force convert leftmost non-needed
    while new_rest.count("——") > target_max:
        p = new_rest.find("——")
        if p < 0:
            break
        new_rest = new_rest[:p] + "，" + new_rest[p+2:]
    title = ""
    lines = body.splitlines()
    if lines and lines[0].startswith("# "):
        title = lines[0]
        new_body = title + "\n" + new_rest
    else:
        new_body = new_rest
    return new_body, count, new_rest.count("——")

# BOM strip all 301-340 + fix dash chapters
for n in range(301, 341):
    p = base / ("chapter-%d.md" % n)
    raw = p.read_bytes()
    text = raw.decode("utf-8")
    had_bom = text.startswith("\ufeff")
    if had_bom:
        text = text[1:]
    body, footer = split_file(text)
    before = body_part(body).count("——")
    if before > 8 or had_bom:
        new_body, b2, a2 = reduce_to(body, 3, 8)
        out = new_body
        if not out.endswith("\n"):
            out += "\n"
        if footer:
            out += footer if footer.startswith("---") else "---\n" + footer
            if not out.endswith("\n"):
                out += "\n"
        p.write_text(out, encoding="utf-8")
        print("ch%d: dash %d->%d bom=%s" % (n, b2, a2, had_bom))
    elif had_bom:
        p.write_text(text, encoding="utf-8")
        print("ch%d: bom stripped" % n)

# re-check 303/308/325
print("\nrecheck:")
for n in [303, 308, 325]:
    p = base / ("chapter-%d.md" % n)
    text = p.read_text(encoding="utf-8")
    if text.startswith("\ufeff"):
        text = text[1:]
    body, footer = split_file(text)
    print("ch%d dash=%d cjk_will_check" % (n, body_part(body).count("——")))
