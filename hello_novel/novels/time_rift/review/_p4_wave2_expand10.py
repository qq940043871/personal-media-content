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

def reduce_dashes(body, cap=6):
    while len(re.findall(r"——", body)) > cap:
        idx = body.rfind("——")
        if idx < 0:
            break
        body = body[:idx] + "，" + body[idx+2:]
    return body

ADD = {
275: """
听译伦理试行满月，水晶文明发来一段更长的振动。

不是讲ARIA。

是讲它们自己：如何在高压与黑暗里，用缓慢的应力波交换「今天还好吗」。

「还好吗」没有敬语，没有史诗腔。

李明听完，对ARIA说：「它们终于开始讲自己了。」

「不是终于。」ARIA说，「是我们终于等到不必由我们开题的时刻。」

工作簿追加一行：

「当对方主动自述，记录者降级为抄写员，不得升格为解说员。」

抄写页下方，签字栏只有两个位置：记录人、在场见证人。

没有「意义评定人」。

地表公告更新：

结构层声学样本持续收录；不对市民征收听译配合义务；窗口不解释甲烷修辞。

19层有人问：「海底在说话吗？」

值班员答：「在说话。我们只负责别抢答。」

抢答冲动还在。
账本先按住冲动。
""",
232: """
对照表公示后第三日，有一个小文明提交修订。

左栏意义从「理解永恒」改成「把今天过完」。

右栏动作从空，变成：修了一个自己的节点、拒绝了一次无效会议、给同伴留了静息窗。

修订说明写：

「我们以前把意义写得很大，因为小的写出来怕被笑。」

ARIA在修订旁批：

「不怕被笑的写法，才开始有意义。」

李明把这句送给19层，做成窗口便签：

「意义可以写小。小，才贴得上墙。」

便签旁边，手写表照常。

有人签了名，有人画了勾。

勾不是投票。

勾是「我还在」的意思。

存在异议谁来说？

先由画勾的人，用今天说了算。
""",
157: """
可被店长纠正抽样推广后，联盟决议质量指标里多了一项「土条文占比」。

土条文占比太低，说明决议在飘。

某次关于共鸣网络升级的决议里，店长的纠正只有一句：

「升级能不能别在打烊时间响？」

决议加了静音时段。

静音时段生效那天，23层营业额微升。

有人嘲笑：宇宙级决议被营业时间绑架。

李明回：「被真实生活绑架，好过被概念绑到失联。」

成长速率表第四项（是否还愿意被普通人纠正）当月得分上升。

不是因为联盟更虚心。

是因为普通人敢开口了。

敢开口，是系统成长里最贵的指标。

比参数更难刷。
""",
124: """
裂隙扩张监测进入第二周，维修班负荷触到阈值。

按任务书：先保民生派单，再保论文数据。

论文侧的数据缺口被记为：

「因优先派单导致样本缺口X小时。原因：人比曲线重要。」

监察抽核时没有退回这条。

批注是：

「同意优先级。请在缺口说明旁附派单完成表，防止『人比曲线重要』变成偷懒口号。」

派单完成表附上后，说明闭合。

ARIA说：「你看，连优先级都要被验收。」

「不然优先级会变成免检金牌。」李明说。

19层灯在派单完成后亮起。

有人在手写表画了一个勾，又在勾旁边点了个点。

点不是错别字。

点表示：亮了，已看见。

裂隙仍在扩张。

看见亮灯的人也在增加。

两件事都记账时，城市才没有在宏大里失联。
""",
186: """
传承最小包公示满十日，收到市民意见二十三条。

最多的一条是：

「纸笔备份谁掏钱？」

预算会开得很短。

结论：市政基础办公列支，不走联盟英雄基金。

第二多的一条：

「店长可拒绝的边界，会不会被上层拿来当不作为借口？」

答复：

可拒绝边界针对不合理接待与超时占用，不针对基本安全配合。区分标准写入手册首页。

李明把这两条意见放进展传承包附录。

附录标题：

《交接不是交情，是有人会来问价》。

问价的人让传承更结实。

只鼓掌的交接，通常在第三个月漏水。

漏水不是诅咒。

是提醒：门轴油还没排进预算。
""",
222: """
发现报告第五格被监察定为必填后，出现了一批敷衍答复：

「与市民有关。详见后续。」

「后续」被要求再填预计日期。

敷衍于是变少。

有一份报告第五格写得很长，像投诉：

「与你何干我不知道。我只知道我们采样时有人在窗口骂电梯。所以第五格我写了：若你的研究需要安静，请先确认邻居的电梯是否在修。」

监察把这份报告设为范本。

范本标题：

《先听见骂声，再谈发现》。

李明抄在控制台：

「探索不是把耳朵伸向宇宙的同时关掉楼道。」

臂端读数：稳定。
连接税：个人账。

发现仍会来。

来的时候，请自带第五格。

没有第五格的发现，像没有地址的快递：只能堆在驿站，堆久了会被当成垃圾。
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
    if add.strip()[:8] in body:
        print("skip marker", ch)
        continue
    body = body.rstrip() + "\n" + add
    body = reduce_dashes(body, 6)
    new = title + "\n" + body.rstrip() + "\n" + footer
    if not new.endswith("\n"):
        new += "\n"
    p.write_text(new, encoding="utf-8")
    after = body_cjk(new)
    dash = len(re.findall(r"——", re.sub(r"^\s*---\s*$", "", new[:new.find("**本章关键点")], flags=re.M)))
    print(f"ch{ch} {before}->{after} dash={dash} {'OK' if after>=5000 and dash<=8 else 'NEED'}")
