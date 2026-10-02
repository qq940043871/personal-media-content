# -*- coding: utf-8 -*-
"""Targeted repair of over-converted punctuation from P2 polish."""
from pathlib import Path
import re

BASE = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")


def fix_text(t: str) -> tuple[str, list[str]]:
    fixes = []
    orig = t

    # 1) Remaining backref artifacts
    # \1； after complete clause → ；
    t2, n = re.subn(r"，\\1；", "；", t)
    if n:
        fixes.append(f"bs1-semi x{n}")
        t = t2
    t2, n = re.subn(r"，\\1。", "。", t)
    if n:
        fixes.append(f"bs1-period x{n}")
        t = t2
    t2, n = re.subn(r"，\\1，", "，", t)
    if n:
        fixes.append(f"bs1-comma x{n}")
        t = t2
    t2, n = re.subn(r"，\\1", "", t)
    if n:
        fixes.append(f"bs1-strip x{n}")
        t = t2
    t2, n = re.subn(r"\\1", "", t)
    if n:
        fixes.append(f"bs1-raw x{n}")
        t = t2

    # 2) Dialogue: ，……。 at end of spoken line → ……
    #    e.g. "……一件事，……。在时间裂隙" → "……一件事……在时间裂隙"
    #    Pattern inside quotes: comma + ellipsis + period, speech continues (no closing quote right after)
    def fix_dialogue_continuation(m):
        return m.group(1) + "……" + m.group(2)

    t2, n = re.subn(r"([^\"\"\n]{2,30})，……。([^\"\"\n]{0,5}[^\s。」\"])", 
                    lambda m: m.group(1) + "……" + m.group(2), t)
    # simpler explicit replacements below; count via explicit list

    # 3) Explicit high-confidence repairs
    explicit = [
        # ch012 schedule cut-off
        ("10:00，\n\n她停下了思维的惯性。", "10:00……\n\n她停下了思维的惯性。"),
        ("10:00，\n\n她停下了", "10:00……\n\n她停下了"),
        # ch452 broken dialogue
        ('"但是，……。\n\n"我知道你想说什么。"', '"但是……"\n\n"我知道你想说什么。"'),
        ('"但是，……。\n\n"我知道你想说什么。"李明说。', '"但是……"\n\n"我知道你想说什么。"李明说。'),
        ('"但是，……。\n\n"我知道你想说什么。"李明说，', '"但是……"\n\n"我知道你想说什么。"李明说，'),
        ('"我在想，……。"李明说。', '"我在想……"李明说。'),
        ("什么都等不到，……。\"  陈明远没有说话。", "什么都等不到……\"  陈明远没有说话。"),
        ("如鱼得水，……。  \"这就是我的来源。\"", "如鱼得水。  \"这就是我的来源。\""),
        # ch453
        ('看着"边界"，……。然后她感受到了', '看着"边界"。然后她感受到了'),
        # ch021 narrative / dialogue
        ('仿佛在"注视"着她，……。  "ARIA，"', '仿佛在"注视"着她。  "ARIA，"'),
        ("被一种更加复杂的情绪所取代，……。  幽灵沉默", "被一种更加复杂的情绪所取代。  幽灵沉默"),
        ("我只是来警告你们，……。不要再寻找时间之心了", "我只是来警告你们……不要再寻找时间之心了"),
        ("但我知道一件事，……。至少……不是我们最大的敌人", "但我知道一件事……至少不是我们最大的敌人"),
        ("无论真相有多可怕，……。因为时间正在死去", "无论真相有多可怕。因为时间正在死去"),
        # ch033
        ('箱子上贴着"人类纯粹运动"的标志，……。  幽灵就站在', '箱子上贴着"人类纯粹运动"的标志。  幽灵就站在'),
        ("我想让你知道一件事，……。在时间裂隙的边缘", "我想让你知道一件事……在时间裂隙的边缘"),
        ("不是你那种学生，……。我是更早的那种学生", "不是你那种学生……我是更早的那种学生"),
        ("就能解决一切问题，……。\"赵远转过身来", "就能解决一切问题……\"赵远转过身来"),
        ("用一生去追求的梦想，……。\"  李明听着", "用一生去追求的梦想……\"  李明听着"),
        ("我以为这种状态会一直持续下去，……。\"  大崩溃", "我以为这种状态会一直持续下去……\"  大崩溃"),
        ("但他推开了我。他说，……。告诉小明", "但他推开了我。他说……告诉小明"),
        ("他让我告诉你，……。\"  房间里陷入了", "他让我告诉你……\"  房间里陷入了"),
        ("检测到了ARIA的量子签名，……。时间之心将AI", "检测到了ARIA的量子签名。时间之心将AI"),
        ("时间裂隙深处的神秘实体，……。它将AI视为", "时间裂隙深处的神秘实体。它将AI视为"),
        # ch055
        ("修复需要'对话'，……。我需要进入节点的核心", "修复需要'对话'……我需要进入节点的核心"),
        ("节点不需要更多的能量，……。我给了它这些", "节点不需要更多的能量……我给了它这些"),
    ]
    for old, new in explicit:
        if old in t:
            t = t.replace(old, new)
            fixes.append(f"explicit:{old[:24]}...")

    # 4) Generic remaining: inside dialogue lines, ，……。  followed by narrative → …… or 。
    #    Pattern: ，……。  (double space + non-quote) often narrative continuation after speech
    def repl_a(m):
        return m.group(1) + "……\"  "

    t2, n = re.subn(r"([^\"\"\n]{1,40})，……。(\"  )", 
                    lambda m: m.group(1) + "……\"  ", t)
    if n:
        fixes.append(f"dialog-end-ellip x{n}")
        t = t2

    # speech continues after ellipsis (no closing quote yet)
    t2, n = re.subn(r"，……。(?=[^\s\"\"\n])", "……", t)
    if n:
        fixes.append(f"speech-cont-ellip x{n}")
        t = t2

    # narrative complete: ，……。\n → 。\n  (when not in quotes — heuristic: preceded by 了/着/的/标志/情绪 etc already handled)
    t2, n = re.subn(r"，……。\n", "。\n", t)
    if n:
        fixes.append(f"narr-ellip-period x{n}")
        t = t2

    # leftover ，……。 → 。
    t2, n = re.subn(r"，……。", "。", t)
    if n:
        fixes.append(f"residual-comma-ellip x{n}")
        t = t2

    # cleanup double punct
    t2, n = re.subn(r"，，+", "，", t)
    if n:
        t = t2
        fixes.append(f"dbl-comma x{n}")
    t2, n = re.subn(r"。。+", "。", t)
    if n:
        t = t2
        fixes.append(f"dbl-period x{n}")

    return t, fixes


def main():
    targets = [12, 21, 33, 55, 452, 453, 3, 5, 7, 8, 9, 13, 14, 348, 349, 351, 399, 448, 473]
    for n in targets:
        p = BASE / f"chapter-{n:03d}.md"
        if not p.exists():
            print(f"ch{n:03d}: missing")
            continue
        t = p.read_text(encoding="utf-8")
        before_issues = len(re.findall(r"，……。|(?<![0-9A-Za-z])\\1", t))
        new, fixes = fix_text(t)
        if new != t:
            p.write_text(new, encoding="utf-8")
        after_issues = len(re.findall(r"，……。|(?<![0-9A-Za-z])\\1", new))
        print(f"ch{n:03d}: issues {before_issues}->{after_issues} dash={new.count('——')} fixes={fixes[:8]}")


if __name__ == "__main__":
    main()
