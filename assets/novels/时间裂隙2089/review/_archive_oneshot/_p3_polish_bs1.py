#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P3 quality polish after \\1 bulk repair: fix awkward punctuation & incomplete clauses."""
from __future__ import annotations

import re
from pathlib import Path
from collections import defaultdict

BASE = Path(r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/novel/chapters")
LOG: dict[str, list[str]] = defaultdict(list)

# Exact quality fixes: (old, new)
QUALITY = [
    # dialogue: comma before ellipsis is awkward
    ("你有没有感觉到，……", "你有没有感觉到……"),
    ("他们只需要，……", "他们只需要……"),
    ("没有人会，……", "没有人会……"),
    ("联盟内部有人，……", "联盟内部有人……"),
    ("你怎么会，……", "你怎么会……"),
    ("所以你决定，……", "所以你决定……"),
    ("虚空是，……", "虚空是……"),
    ("你，……", "你……"),
    ("你决定，……", "你决定……"),
    ("帮助虚空，……", "帮助虚空……"),
    ("你看到了，……", "你看到了……"),
    ("但你，……", "但你……"),
    ("向外，……", "向外……"),
    ("回应，……", "回应……"),
    ("那，……", "那……"),
    ("时间，……", "时间……"),
    ("超越了数据层面，……", "超越了数据层面……"),
    ("理解，……", "理解……"),
    ("因为，……", "因为……"),
    ("但，……", "但……"),
    ("另一种存在方式，……", "另一种存在方式……"),
    ("虚空已经，……", "虚空已经……"),
    ("修改，……", "修改……"),
    ("暴露出来，……", "暴露出来……"),
    ("意识层面的陷阱，……", "意识层面的陷阱……"),
    ("凝视，……", "凝视……"),
    ("更多的东西，……", "更多的东西……"),
    ("连接，……", "连接……"),
    ("你是说，……", "你是说……"),
    ("愿意成为，……", "愿意成为……"),
    ("这需要，……", "这需要……"),
    ("自愿的选择，……", "自愿的选择……"),
    ("同一枚硬币的两面，……", "同一枚硬币的两面……"),
    ("回应你，……", "回应你……"),
    ("我们，……", "我们……"),
    ("新的结构，……", "新的结构……"),
    ("更多的，……", "更多的……"),
    ("成为，……", "成为……"),
    ("已经，……", "已经……"),
    ("选择，……", "选择……"),
    ("感觉到了，……", "感觉到了……"),
    ("爱，……", "爱……"),
    ("未来的爱，……", "未来的爱……"),
    ("新的时间网络，……", "新的时间网络……"),
    ("进化，……", "进化……"),
    ("通过理解，……", "通过理解……"),
    ("道歉，……", "道歉……"),
    ("我泄露了防御配置。我，……", "我泄露了防御配置。我……"),
    ("在看着时间，……", "在看着时间……"),
    ("超越了防御，……", "超越了防御……"),
    ("入口，……", "入口……"),
    ("打开，……", "打开……"),
    ("召唤你，……", "召唤你……"),
    ("等待你，……", "等待你……"),
    ("什么存在，……", "什么存在……"),
    ("出路，……", "出路……"),
    ("什么地方，……", "什么地方……"),
    ("很深的地方，……", "很深的地方……"),
    ("去那里，……", "去那里……"),
    ("承诺，……", "承诺……"),
    ("我会带回真相。我会，……", "我会带回真相。我会……"),
    ("等我，……", "等我……"),
    # incomplete after bulk delete — restore short clauses
    ("脸上布满了皱纹，双手。", "脸上布满了皱纹，双手微微颤抖。"),
    ("不是因为他比她更聪明。不是因为他比她更强大，而是因为他比她更清醒。",
     "不是因为他比她更聪明，也不是因为他比她更强大，而是因为他比她更清醒。"),
    ("而是因为我看到了你看不到的东西……。\"", "而是因为我看到了你看不到的东西……\""),
    ("但停下来、转过身、做出决定，。\"", "但停下来、转过身、做出决定，是你自己。\""),
    ("做出了决定，。", "做出了决定，是你自己。"),
]

# Pattern polish applied to all chapters
PATTERN_FIXES = [
    # ，……" or ，……。"  →  ……"  (dialogue trail-off)
    (re.compile(r"，……。\""), "……\""),
    (re.compile(r"，……(?=[\"'\n])"), "……"),
    # orphaned double punctuation from bulk delete
    (re.compile(r"，，+"), "，"),
    (re.compile(r"。。+"), "。"),
    (re.compile(r"，。"), "。"),
    (re.compile(r"。，"), "。"),
]


def polish_file(path: Path) -> int:
    t = path.read_text(encoding="utf-8")
    orig = t
    nfix = 0
    for old, new in QUALITY:
        if old in t:
            c = t.count(old)
            t = t.replace(old, new)
            nfix += c
            LOG[path.name].append(f"exact x{c}: {old[:50]}")
    for rx, repl in PATTERN_FIXES:
        t2, c = rx.subn(repl, t)
        if c:
            t = t2
            nfix += c
            LOG[path.name].append(f"pattern x{c}: {rx.pattern[:40]}")
    if t != orig:
        path.write_text(t, encoding="utf-8")
    return nfix


def main():
    total = 0
    for f in sorted(BASE.glob("chapter-*.md")):
        n = polish_file(f)
        if n:
            print(f"{f.name}: {n} quality fixes")
            total += n
    print(f"TOTAL quality fixes: {total}")

    # scan remaining awkward patterns
    print("\n=== residual awkward scan ===")
    awkward = 0
    for f in sorted(BASE.glob("chapter-*.md")):
        t = f.read_text(encoding="utf-8")
        for pat, label in [
            (r"，……", "comma-ellipsis"),
            (r"……。", "ellipsis-period"),
            (r"，，", "double-comma"),
            (r"。。", "double-period"),
            (r"，。\"", "comma-period-quote"),
        ]:
            for m in re.finditer(pat, t):
                s = max(0, m.start() - 30)
                e = min(len(t), m.end() + 30)
                print(f"{f.name} [{label}]: ...{t[s:e]}...")
                awkward += 1
    print(f"AWKWARD LEFT: {awkward}")

    log_path = Path(r"D:/ai_person/p000_0000_media/hello_novel/novels/time_rift/review/_p3_bs1_quality_log.txt")
    lines = [f"TOTAL quality fixes: {total}", ""]
    for ch, notes in sorted(LOG.items()):
        lines.append(f"## {ch}")
        lines.extend(notes)
        lines.append("")
    log_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
