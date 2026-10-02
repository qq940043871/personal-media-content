# -*- coding: utf-8 -*-
import re
from pathlib import Path

CH = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
CJK = re.compile(r"[\u4e00-\u9fff]")

def body_cjk(text):
    lines = []
    for ln in text.splitlines():
        if re.match(r"^#\s*第\d+章", ln):
            continue
        if "本章关键点" in ln:
            break
        lines.append(ln)
    return len(CJK.findall("\n".join(lines)))

def split(text):
    t = text.lstrip("\ufeff")
    m = re.match(r"^(#\s*第\d+章[^\n]*)\n([\s\S]*)$", t)
    title, rest = m.group(1), m.group(2)
    idx = rest.find("**本章关键点")
    body = rest[:idx]
    body = re.sub(r"\n---\s*$", "", body.rstrip()) + "\n"
    footer = rest[idx:]
    return title, body, footer

ADD = {
271: """
收束前，ARIA把今日全部读数整理成一张给监察的薄表：

结构起源取样：两道纹路已读，第三道未入。
意识本底：稳定在可继续区间，无豁免。
李明新臂噪声：未触自设红线，但第三次深触后回升，备注「不宜连夜加班」。
对地回执：已投市政与监察双份，人话版同步19层与23层。
未决项：纹路若与现行修复方案冲突，冲突清单七日内提交，禁止现场改宪章。

李明在薄表末尾签字，签完把笔（意识里的笔）放回原处。

「为什么连笔都要放回去？」ARIA问。

「放回去，」他说，「下一个人来，才知道这里是有人用过的桌子，不是神坛。」

混沌依旧没有方向。

但表格有日期，签字有名字，未决项有期限。

这就是探索与幻觉的分界线。
""",
296: """
离开档案室前，存档员追出来问了一个技术问题：

「私人材料摘要若日后被引用，要不要注明『作者拒绝当场消化第二十枚』？」

ARIA回答：「要。拒绝也是事实的一部分。删掉拒绝，就只剩英雄。」

年轻人记下，字迹很用力。

李明在旁边看着，忽然明白苏婉清那些医院铅笔字为什么重要。

不是因为悲情。

是因为有人在账单旁边写字，证明制度再冷，仍有人愿意留一道缝，让后来的人能钻进去问一句：你当时疼不疼？

缝不是答案。
缝是答案还允许被追问的形状。

第十九枚在档案袋里。
第二十枚在膜后。
评估草案在锁里。
店长的围裙味道还留在地下二层的空气里。

城市记忆真正的敌人，从来不是遗忘。

是被写得太满，满到没有人还能塞进一句：这一笔，先不还。
"""
}

for ch, add in ADD.items():
    p = CH / f"chapter-{ch:03d}.md"
    raw = p.read_text(encoding="utf-8")
    title, body, footer = split(raw)
    before = body_cjk(raw)
    body = body.rstrip() + "\n" + add
    new = title + "\n" + body.rstrip() + "\n" + footer
    if not new.endswith("\n"):
        new += "\n"
    p.write_text(new, encoding="utf-8")
    after = body_cjk(new)
    dash = len(re.findall(r"——", re.sub(r"^\s*---\s*$", "", new[:new.find("**本章关键点")], flags=re.M)))
    print(f"ch{ch} {before}->{after} dash={dash} {'OK' if after>=5000 and dash<=8 else 'NEED'}")
