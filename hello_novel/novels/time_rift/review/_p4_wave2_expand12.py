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
    body = re.sub(r"\n---\s*$", "", rest[:idx].rstrip()) + "\n"
    footer = rest[idx:]
    return title, body, footer

ADD = {
275: """
记录员轮换表贴在工作台边。

轮换原则：连续听译不得超过两日，防止把对方的频率听成自己的心跳。

下一位记录员签名栏空着。

空着不是缺人。

是还没到该签字的那天。

到那天，名字会自己出现，像对方的名字一样，不靠我们代填。
""",
232: """
有人问ARIA：若意义永远吵不完呢？

她说：「吵不完也得修灯。意义讨论可以无限，市政派单要有限时。」

「有限时的意义呢？」

「有限时的意义通常叫任务。」她说，「任务完成要交回执。回执交完，再回去吵。」

吵与交回执，可以是同一天的两件事。

不冲突。

冲突的是只准选一样。
""",
157: """
店长讲话结束后，有人鼓掌。

店长说：「别鼓掌。去检查门轴。」

检查结果当晚贴出：两处需上油，一处螺钉松动。

上油单签字人：店长。
复核人：李明。

成长课没有证书。

上油单就是证书。

纸会旧。

油痕不会先旧。
""",
222: """
报告五格制度满月，监察统计：

第五格空着的：0。
敷衍的：下降。
范本被引用次数：上升。

引用次数不是荣誉。

是更多探索者开始练习说人话。

人话写多了，会变难。

难的是：承认有些发现暂时与你无关，却不把「无关」写成傲慢。

范本里那句「不带着惊喜突袭」，被抄进了多份报告。

抄得多了，就快成了探索界的门轴上油。

每天做一点。
不靠史诗。
"""
}

for ch, add in ADD.items():
    p = CH / f"chapter-{ch:03d}.md"
    raw = p.read_text(encoding="utf-8")
    title, body, footer = split(raw)
    before = body_cjk(raw)
    if before >= 5000:
        print("skip", ch, before)
        continue
    if add.strip()[:6] in body:
        print("skip m", ch)
        continue
    body = body.rstrip() + "\n" + add
    new = title + "\n" + body.rstrip() + "\n" + footer
    if not new.endswith("\n"):
        new += "\n"
    p.write_text(new, encoding="utf-8")
    after = body_cjk(new)
    dash = len(re.findall(r"——", re.sub(r"^\s*---\s*$", "", new[:new.find("**本章关键点")], flags=re.M)))
    print(f"ch{ch} {before}->{after} dash={dash} {'OK' if after>=5000 and dash<=8 else 'NEED'}")
