# -*- coding: utf-8 -*-
"""Fix awkward punctuation introduced by dash→period conversion."""
from pathlib import Path
import re

BASE = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

# Targeted replacements for known awkward conversions (context-unique)
EXPLICIT = [
    # ch005
    (
        "因为他记得，在最初的几次循环中。在他还不确定时间是否真的在重复的那些日子里，他曾经来过这里。",
        "因为他记得，在最初的几次循环中，在他还不确定时间是否真的在重复的那些日子里，他曾经来过这里。",
    ),
    # ch009
    (
        "他的右手无名指。那个戴着金色市徽戒指的手指，在桌面下方轻轻敲击了三次",
        "他的右手无名指，那个戴着金色市徽戒指的手指，在桌面下方轻轻敲击了三次",
    ),
    # ch348
    ("那是，真实的情感反应。", "那是真实的情感反应。"),
    ("她是在，感受生命。", "她是在感受生命。"),
    ("你试图承受，无数个文明的无数个一生。", "你试图承受无数个文明的无数个一生。"),
]

# Generic patterns: period + apposition starter that should be comma
# Only when clearly same-sentence apposition (那/这/一个/某个 after 。)
GENERIC = [
    # 。那个/。这个/。这些/。那些 → ，那个 etc when previous word is noun-like
    (r"(无名指|手指|眼睛|瞳孔|声音|表情|动作|痕迹|光点|数据|设备|装置|结构|存在|文明|记忆|问题|答案|选择|时刻|瞬间|地方|区域|房间|空间)。(那个|这个|这些|那些|一种|一个|某种)",
     r"\1，\2"),
    # 是，X where X is short predicate — 是X
    (r"那是，([^，。]{2,12}。)", r"那是\1"),
    (r"她是在，([^，。]{2,8}。)", r"她是在\1"),
    (r"他是在，([^，。]{2,8}。)", r"他是在\1"),
    (r"我是在，([^，。]{2,8}。)", r"我是在\1"),
    # 。正/。像/。如同 mid-description often should be comma when short
    (r"(颤抖|流动|闪烁|脉动|发光|延伸|展开|出现)。(正|像|如同)([^，。]{4,20}[，。])",
     r"\1，\2\3"),
]

TARGETS = list(range(1, 16)) + [21, 33, 55, 342, 348, 349, 351, 388, 399, 440, 448, 452, 453, 473]


def fix_chapter(n: int) -> list[str]:
    p = BASE / f"chapter-{n:03d}.md"
    if not p.exists():
        return [f"ch{n:03d}: missing"]
    t = p.read_text(encoding="utf-8")
    orig = t
    notes = []
    for old, new in EXPLICIT:
        if old in t:
            t = t.replace(old, new)
            notes.append(f"explicit:{old[:20]}")
    for pat, repl in GENERIC:
        t2, c = re.subn(pat, repl, t)
        if c:
            notes.append(f"generic:{pat[:24]} x{c}")
            t = t2
    # Fix "中。在" pattern when 在 continues same thought (not new paragraph)
    t2, c = re.subn(r"(循环中|过程中|实验中|沉默中|思考中|观察中|扫描中|分析中|修复中|探索中|等待中)。(在[^。\n]{6,40}[，。])",
                    r"\1，\2", t)
    if c:
        notes.append(f"zhong-zai x{c}")
        t = t2
    if t != orig:
        p.write_text(t, encoding="utf-8")
        return [f"ch{n:03d}: fixed {notes}"]
    return [f"ch{n:03d}: clean"]


def main():
    for n in TARGETS:
        for line in fix_chapter(n):
            print(line)

    # re-verify trial dash counts + a few awkward patterns
    print("\n--- verify ---")
    for n in range(1, 16):
        t = (BASE / f"chapter-{n:03d}.md").read_text(encoding="utf-8")
        awkward = []
        if "中。在" in t:
            awkward.append("zhong-zai")
        if re.search(r"无名指。那个", t):
            awkward.append("finger")
        if re.search(r"那是，真实", t):
            awkward.append("shi-comma")
        if re.search(r"(?<![0-9A-Za-z])\\1", t):
            awkward.append("bs1")
        print(f"ch{n:03d}: dash={t.count('——')} awkward={awkward} cycle={'循环日志' in t[:300]}")


if __name__ == "__main__":
    main()
