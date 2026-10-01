# -*- coding: utf-8 -*-
"""P2 residual polish: trial 1-15 + mid dash>=10 sample + \\1 artifact repair."""
from __future__ import annotations

import os
import re
from pathlib import Path

BASE = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
DASH = "——"

TRIAL = [3, 5, 7, 8, 9, 12, 13, 14]
MID_TOP = [348, 351, 453, 452, 349, 399, 473, 448]
VOL1_ARTIFACT = [21, 30, 33, 55, 60]
MID_ARTIFACT = [452, 453, 342, 340, 388]
ALL_EDIT = sorted(set(TRIAL + MID_TOP + VOL1_ARTIFACT + MID_ARTIFACT + [440]))


def read_ch(n: int) -> str:
    return (BASE / f"chapter-{n:03d}.md").read_text(encoding="utf-8")


def write_ch(n: int, text: str) -> None:
    (BASE / f"chapter-{n:03d}.md").write_text(text, encoding="utf-8")


def count_dash(text: str) -> int:
    return text.count(DASH)


# ---------------------------------------------------------------------------
# \1 artifact repair
# ---------------------------------------------------------------------------

# High-confidence exact fixes (morse / known broken phrases)
EXACT_BACKREF = {
    "好，好，\\1。": "好，好，的。",
    "照，顾，自，\\1。": "照，顾，自，己。",
    "照，顾，自，\\1": "照，顾，自，己",
    "好，好，\\1": "好，好，的",
}


def fix_backref_line(line: str) -> str:
    """Repair a single line containing regex backref artifacts \\1."""
    if "\\1" not in line:
        return line

    for old, new in EXACT_BACKREF.items():
        if old in line:
            line = line.replace(old, new)

    if "\\1" not in line:
        return line

    # Dialogue trail-offs: "……，\1   or "……，\1。  or "……，\1，
    # Incomplete speech → ellipsis
    def repl_dialogue(m: re.Match) -> str:
        return m.group(0).replace("\\1", "……")

    line = re.sub(r'"[^"\n]*，\\1[^"\n]*"', repl_dialogue, line)
    line = re.sub(r'"[^"\n]*，\\1', lambda m: m.group(0).replace("\\1", "……"), line)

    if "\\1" not in line:
        return line

    # 而是，\1。 / 而是\1 → 而是这样。
    line = re.sub(r"而是，?\\1。?", "而是这样。", line)
    line = re.sub(r"而是，?\\1，", "而是这样，", line)

    if "\\1" not in line:
        return line

    # 它只是，\1。 → 它只是这样。
    line = re.sub(r"它只是，\\1。?", "它只是这样。", line)

    if "\\1" not in line:
        return line

    # Complete clause + ，\1。 → clause。
    # Complete clause + ，\1， → clause，
    # Complete clause + ，\1 → clause
    line = re.sub(r"，\\1。", "。", line)
    line = re.sub(r"，\\1，", "，", line)
    line = re.sub(r"，\\1(?=[\"'\n]|$)", "", line)
    line = re.sub(r"(?<![，。！？；：])\\1。?", "", line)

    # Cleanup double punctuation introduced by removal
    line = re.sub(r"，，+", "，", line)
    line = re.sub(r"。。+", "。", line)
    line = re.sub(r"，。", "。", line)
    line = re.sub(r"。，", "。", line)
    # trailing bare comma before period already handled
    return line


def repair_backrefs(text: str) -> tuple[str, int]:
    if "\\1" not in text:
        return text, 0
    before = text.count("\\1")
    lines = text.splitlines(keepends=True)
    out = [fix_backref_line(ln) for ln in lines]
    new = "".join(out)
    # second pass for any remaining
    if "\\1" in new:
        out2 = [fix_backref_line(ln) for ln in new.splitlines(keepends=True)]
        new = "".join(out2)
    after = new.count("\\1")
    return new, before - after


# ---------------------------------------------------------------------------
# Literary dash pass
# ---------------------------------------------------------------------------

def dash_score(ctx_before: str, ctx_after: str, full: str, pos: int) -> tuple[int, str]:
    """Score dramatic value of a dash. Higher = keep. Returns (score, kind)."""
    before = ctx_before[-80:]
    after = ctx_after[:80]
    after_l = after.lstrip()
    before_r = before.rstrip()

    # Dialogue cut-off / interruption (keep)
    if before_r.endswith(("——",)) is False:
        pass
    # speech trails off right after dash into quote end or newline+action
    if re.search(r'[」"]\s*$', before_r) or re.search(r'(?<!说)(?<!道)$', before_r):
        pass
    if re.search(r'^[「"]', after_l) and re.search(r'(说|道|问|喊|叫|打断|停顿|沉默)[^。！？]{0,12}$', before_r):
        return 95, "speech_intro"
    if before_r.endswith(("说", "道", "问", "喊", "叫", "道，", "说，")) or re.search(
        r"(说|道|问|喊|叫|打断)——?$", before_r
    ):
        return 90, "speech_attr"
    # trailing dash before closing quote (interrupted speech)
    if re.search(r'[^\s」"]——[」"]?\s*$', before_r + "——"):
        # check if dash is at end of quoted speech
        pass
    if re.search(r'(但是|但|可是|然而|然后|因此|所以|因为|只是|就是|不是)——$', before_r):
        # trailing rhetorical — next starts new sentence or short reveal
        if len(after_l) < 20 or after_l.startswith(("\n", " ", "　")):
            return 88, "rhetorical_trail"
        return 70, "rhetorical"
    # interrupted dialogue: ...——"\n or ...——\n" or ...——"
    if re.search(r'——[」"]\s*$', before + "——") or re.search(r'——[」"]', ctx_before[-5:] + "——" + after[:3]):
        return 92, "interrupt"
    if after_l.startswith(("[」\"]", "」", "\"", "“")):
        return 92, "before_quote"
    # short dramatic reveal after dash + newline or short phrase
    after_strip = after_l
    if after_strip.startswith("\n"):
        nxt = after_strip.strip().splitlines()[0] if after_strip.strip() else ""
        if 0 < len(nxt) <= 25:
            return 85, "dramatic_reveal"
    # "而是——" + short punch
    if re.search(r"而是——$", before_r):
        if len(after_l) <= 20:
            return 84, "bushi_punch"
        return 40, "bushi_explain"
    # 不是A——B explanatory
    if re.search(r"不是[^。！？]{0,30}——$", before_r) or re.search(r"不是[^。！？]{0,30}——", before[-40:]):
        return 25, "bushi_explain"
    # list/apposition: ——A、B、C
    if re.match(r"^[\s\n]*[「\"（(]?", after_l) and re.match(r"^.{0,5}[、，].{0,5}[、，]", after_l):
        return 20, "list"
    # long explanatory after dash
    # measure until sentence end
    exp = re.split(r"[。！？\n]", after_l, maxsplit=1)[0]
    if len(exp) >= 28:
        return 22, "long_explain"
    if 12 <= len(exp) < 28:
        return 35, "mid_explain"
    # short continuation after mid-sentence dash — often dramatic
    if len(exp) < 12 and exp:
        return 75, "short_punch"
    return 30, "default"


def convert_dash(before: str, after: str, kind: str) -> str:
    """Return replacement for the dash itself (and possibly glue)."""
    after_l = after.lstrip("\n")
    before_r = before.rstrip()

    if kind in ("speech_attr", "speech_intro"):
        # 说——"  → 说，"
        return "，"
    if kind in ("interrupt", "before_quote"):
        return "，"  # shouldn't usually convert; if we do, soft pause
    if kind in ("rhetorical_trail", "rhetorical", "dramatic_reveal", "bushi_punch", "short_punch"):
        return "，"
    if kind == "bushi_explain":
        return "，"
    if kind == "list":
        return "："
    if kind == "long_explain":
        # If after starts a new explanatory that can stand alone → period
        # Need to remove glue: if before doesn't end with clause-ending, use 。
        if before_r.endswith(("的", "了", "着", "过", "是", "在", "有", "为", "与", "和")):
            return "，"
        return "。"
    if kind == "mid_explain":
        return "，"
    return "，"


def polish_dashes(text: str, max_keep: int = 3) -> tuple[str, dict]:
    """Reduce dashes to at most max_keep dramatic ones; convert rest."""
    stats = {
        "before": count_dash(text),
        "kept": 0,
        "converted_comma": 0,
        "converted_colon": 0,
        "converted_period": 0,
        "skipped_header": 0,
    }
    if stats["before"] == 0:
        stats["after"] = 0
        return text, stats

    # Protect header block (title + 循环日志 blockquote + first blank)
    lines = text.splitlines(keepends=True)
    header_end = 0
    for i, ln in enumerate(lines[:20]):
        if ln.startswith("# ") or ln.startswith(">"):
            header_end = i + 1
        elif ln.strip() == "" and header_end:
            # allow a couple blanks after header
            if i <= header_end + 2:
                header_end = max(header_end, i + 1)
            else:
                break
        elif header_end and not ln.startswith(">"):
            break
    header = "".join(lines[:header_end])
    body = "".join(lines[header_end:])

    if DASH in header:
        stats["skipped_header"] = header.count(DASH)

    # Collect dash positions in body
    positions = [m.start() for m in re.finditer(re.escape(DASH), body)]
    if not positions:
        stats["after"] = count_dash(text)
        return text, stats

    scored = []
    for pos in positions:
        cb = body[max(0, pos - 100) : pos]
        ca = body[pos + 2 : pos + 2 + 120]
        sc, kind = dash_score(cb, ca, body, pos)
        scored.append((sc, pos, kind, cb, ca))

    # Sort by score desc; keep top max_keep (minus header already protected)
    scored_sorted = sorted(scored, key=lambda x: (-x[0], x[1]))
    keep_set = set()
    for sc, pos, kind, cb, ca in scored_sorted:
        if len(keep_set) >= max_keep:
            break
        # prefer higher scores; also avoid keeping two adjacent dashes
        if any(abs(pos - p) < 40 for p in keep_set):
            continue
        keep_set.add(pos)
        stats["kept"] += 1

    # Convert from the end so positions stay valid
    new_body = body
    for sc, pos, kind, cb, ca in sorted(scored, key=lambda x: -x[1]):
        if pos in keep_set:
            continue
        repl = convert_dash(cb, ca, kind)
        # Period conversion: need to handle following whitespace/newline
        if repl == "。":
            # body[pos:pos+2] is dash; after may start with newline
            rest = new_body[pos + 2 :]
            # if rest begins with newlines + text, keep one newline structure
            new_body = new_body[:pos] + "。" + rest.lstrip("\n")
            # ensure space: if next char is CJK, fine
            stats["converted_period"] += 1
        elif repl == "：":
            new_body = new_body[:pos] + "：" + new_body[pos + 2 :]
            stats["converted_colon"] += 1
        else:
            # comma: collapse following newlines to single flow when explanatory
            rest = new_body[pos + 2 :]
            if kind in ("long_explain", "mid_explain", "bushi_explain", "list", "default"):
                # strip leading newlines so clause continues
                stripped = rest.lstrip("\n")
                # if original had double-newline paragraph break after dash, prefer period already
                new_body = new_body[:pos] + repl + stripped
            else:
                new_body = new_body[:pos] + repl + rest
            stats["converted_comma"] += 1

    # Cleanup: double punctuation, dash-comma hybrids
    new_body = re.sub(r"——，", "，", new_body)
    new_body = re.sub(r"，，+", "，", new_body)
    new_body = re.sub(r"。。+", "。", new_body)
    new_body = re.sub(r"：，", "：", new_body)
    new_body = re.sub(r"，。", "。", new_body)

    result = header + new_body
    stats["after"] = count_dash(result)
    return result, stats


def fix_lele(text: str) -> tuple[str, int]:
    """Fix obvious 了了 typos where second 了 is accidental."""
    n = 0
    # 听到了了一声 → 听到了一声
    new, c = re.subn(r"听到了了一声", "听到了一声", text)
    n += c
    # generic 的的/了了 only when clearly doubled function word — skip legit 的的
    return new, n


def mechanical_typos(text: str) -> tuple[str, list[str]]:
    fixes = []
    orig = text
    reps = [
        (r"赵远航", "赵远山", "赵远航→赵远山"),
        (r"旧时光", "时光倒流", "旧时光→时光倒流"),
        (r"林晓霜", "苏雨晴", "林晓霜→苏雨晴"),
        (r"AR IA", "ARIA", "AR IA→ARIA"),
        (r"听到了了一声", "听到了一声", "了了 typo"),
    ]
    for pat, repl, label in reps:
        new, c = re.subn(pat, repl, text)
        if c:
            text = new
            fixes.append(f"{label} x{c}")

    # double punctuation
    for pat, repl, label in [
        (r"，，+", "，", "double comma"),
        (r"。。+", "。", "double period"),
        (r"！！+", "！", "double bang"),
        (r"？？+", "？", "double qmark"),
    ]:
        new, c = re.subn(pat, repl, text)
        if c:
            text = new
            fixes.append(f"{label} x{c}")

    if text != orig:
        pass
    return text, fixes


def main() -> None:
    report: list[str] = []
    print("=== P2 residual polish run ===")

    # 1) Literary dash pass on trial + mid top
    dash_targets = TRIAL + MID_TOP
    dash_results = []
    for n in dash_targets:
        text = read_ch(n)
        before = count_dash(text)
        # also fix mechanical + backref in these chapters
        text, _ = repair_backrefs(text)
        text, typo_fixes = mechanical_typos(text)
        polished, stats = polish_dashes(text, max_keep=3)
        # safety: if after > before, revert dash part (keep typo fixes)
        if stats["after"] > before + 2:
            polished = text
            stats["after"] = count_dash(text)
            stats["note"] = "reverted_overconvert"
        write_ch(n, polished)
        after = count_dash(read_ch(n))
        dash_results.append((n, before, after, stats, typo_fixes))
        print(f"ch{n:03d}: dash {before} -> {after} | {stats} | typos={typo_fixes}")

    # 2) Vol1 artifact chapters: backref + typo only (no forced dash rewrite unless >=8)
    for n in VOL1_ARTIFACT:
        text = read_ch(n)
        before_d = count_dash(text)
        text, fixed_n = repair_backrefs(text)
        text, typo_fixes = mechanical_typos(text)
        if before_d >= 8:
            text, stats = polish_dashes(text, max_keep=3)
        else:
            stats = {"before": before_d, "after": count_dash(text)}
        write_ch(n, text)
        after_d = count_dash(read_ch(n))
        left = read_ch(n).count("\\1")
        print(f"ch{n:03d}: backref_fixed={fixed_n} left={left} dash {before_d}->{after_d} typos={typo_fixes}")
        dash_results.append((n, before_d, after_d, stats, typo_fixes + [f"backref_fixed={fixed_n}"]))

    # 3) Mid artifact-only chapters not already processed
    for n in MID_ARTIFACT:
        if n in MID_TOP:
            continue
        text = read_ch(n)
        before_d = count_dash(text)
        text, fixed_n = repair_backrefs(text)
        text, typo_fixes = mechanical_typos(text)
        if before_d >= 10:
            text, stats = polish_dashes(text, max_keep=3)
        else:
            stats = {"before": before_d, "after": count_dash(text)}
        write_ch(n, text)
        after_d = count_dash(read_ch(n))
        left = read_ch(n).count("\\1")
        print(f"ch{n:03d}: backref_fixed={fixed_n} left={left} dash {before_d}->{after_d} typos={typo_fixes}")
        dash_results.append((n, before_d, after_d, stats, typo_fixes + [f"backref_fixed={fixed_n}"]))

    # 4) ch440 了了
    text = read_ch(440)
    text, fixed_n = repair_backrefs(text)
    text, typo_fixes = mechanical_typos(text)
    write_ch(440, text)
    print(f"ch440: typos={typo_fixes} backref_fixed={fixed_n}")

    # 5) Full vol1 mechanical sweep (1-60) — record hits, fix clear ones
    vol1_hits = []
    patterns = [
        ("的的", r"的的"),
        ("了了", r"了了"),
        ("地地", r"地地"),
        ("得得", r"得得"),
        ("是是", r"是是"),
        ("，，", r"，，"),
        ("。。", r"。。"),
        ("赵远航", r"赵远航"),
        ("旧时光", r"旧时光"),
        ("林晓霜", r"林晓霜"),
        ("AR IA", r"AR\s+IA"),
        ("backref", r"(?<![0-9])\\1(?![0-9])"),
        ("meta-ch", r"在第[一二三四五六七八九十百千0-9]+章"),
        ("陈明-bare", r"陈明(?!远|志)"),
    ]
    for n in range(1, 61):
        p = BASE / f"chapter-{n:03d}.md"
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        hits = []
        for label, pat in patterns:
            ms = list(re.finditer(pat, text))
            if ms:
                # filter 陈明-bare: only if not part of legit compound — already negative lookahead
                hits.append((label, len(ms)))
        if hits:
            vol1_hits.append((n, hits))
            # fix clear mechanical
            text, typo_fixes = mechanical_typos(text)
            text, bfix = repair_backrefs(text)
            # 了了 only exact known
            if "了了" in text:
                text2, c = fix_lele(text)
                if c:
                    text = text2
                    typo_fixes.append(f"lele x{c}")
            if typo_fixes or bfix:
                p.write_text(text, encoding="utf-8")
            print(f"vol1 ch{n:03d}: hits={hits} fixed={typo_fixes} backref={bfix}")

    # 6) Re-count trial chapters 1-15 for the log
    trial_counts = []
    for n in range(1, 16):
        t = read_ch(n)
        trial_counts.append((n, count_dash(t), "\\1" in t, "循环日志" in t[:500]))

    print("\n=== FINAL trial 1-15 dash counts ===")
    for n, d, b, h in trial_counts:
        print(f"  ch{n:03d}: dash={d} backref={b} cycle_log={h}")

    print("\n=== vol1 hit summary ===")
    for n, hits in vol1_hits:
        print(f"  ch{n:03d}: {hits}")

    # Save machine-readable summary
    summary_path = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review\_p2_p3_polish_summary.txt")
    with summary_path.open("w", encoding="utf-8") as f:
        f.write("dash_results:\n")
        for row in dash_results:
            f.write(repr(row) + "\n")
        f.write("\ntrial_counts:\n")
        for row in trial_counts:
            f.write(repr(row) + "\n")
        f.write("\nvol1_hits:\n")
        for row in vol1_hits:
            f.write(repr(row) + "\n")
    print("summary written", summary_path)


if __name__ == "__main__":
    main()
