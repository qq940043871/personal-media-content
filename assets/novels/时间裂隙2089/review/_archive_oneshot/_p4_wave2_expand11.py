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
月度对地回执附页：

声学样本：持续收录。
民生影响：无已确认项。
市民义务：无。
听译员连接税：个人账，明细不公开。
未决：水晶文明自述命名权；预计窗口：不设死期，设「对方主动提出日」。

不设死期，是怕把对方的时间感翻译成我们的KPI。

KPI会催熟。

有些名字，要等它们自己长熟才好摘。
""",
232: """
对照表季度回顾里，多了一行不是数据的观察：

有文明把左栏意义改了三次，右栏动作反而更稳。

ARIA写：「意义爱改口，动作较懒惰。这可能是健康状态。」

李明补：「如果意义从不改口，可能只是没人敢反对。」

季度回执不进公告栏，进档案。

档案存在的意义之一：让未来的改口，不被当成耻辱。
""",
157: """
成长课程结束那天，没有结业仪式。

店长被请来做了十分钟不讲座的讲话：

「我不会讲成长。我只会说：桌子擦完要晾干，门轴油别太多，客人走了灯别全关。」

「为什么别全关？」

「全关像没人管了。」店长说，「留一盏，是告诉夜班：你不是最后一个。」

李明把「留一盏」写进传承最小包注释。

不是制度。

是温度控制。

制度管下限。
温度管人愿不愿意继续来。
""",
124: """
扩张报告的封面被李明改了。

原标题：《时间裂隙扩张态势》。
改后：《时间裂隙扩张态势与地表派单对照》。

有人说多此一举。

他说：「只写扩张，读者会怕。写对照，读者会看。怕和看，引导出的城市动作不一样。」

怕会催生抢购与谣言。
看会催生排队与提问。

市政窗口最近的提问仍是：

「今天电梯修不修？」

这是好事。

说明还有人把日子放在宇宙前面，认真地过。
""",
186: """
交接演练第一次，失败了。

失败点：电子化名单权限过大，夜班新人能改历史记录。
修正：分权，历史只读，当日可写。
验证状态：第二次演练通过；第三次待约。

失败账贴在市政中心走廊，没有美化。

有人路过说：「连交接都会失败，真丢人。」

老何听见，回：「演练失败才丢人，真出事丢的是人命。先把丢人的机会用完。」

走廊安静了几秒。

然后有人把失败账拍下来，发进了工作群。

拍下来，比藏起来，更像传承。
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
