# -*- coding: utf-8 -*-
"""P4 wave2 batch4: remaining CJK<5000 shortest-first unique expansions."""
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
    if idx >= 0:
        body = re.sub(r"\n---\s*$", "", rest[:idx].rstrip()) + "\n"
        footer = rest[idx:]
    else:
        body, footer = rest.rstrip() + "\n", ""
    return title, body, footer

def reduce_dashes(body, cap=6):
    while len(re.findall(r"——", body)) > cap:
        idx = body.rfind("——")
        if idx < 0:
            break
        body = body[:idx] + "，" + body[idx+2:]
    return body

def make_footer(bullets):
    return "\n---\n\n**本章关键点：**\n" + "\n".join(f"- {b}" for b in bullets) + "\n"

# unique inserts sized to clear 5000 from ~4300 base
EXPAND = {
126: {
"insert": """
---
## 补 · 回响的收听名单

宇宙在回响。

李明在回响里做了另一份名单，不是文明名录，是收听优先级。

优先级一：新上海19层至47层的时序体感投诉渠道。
优先级二：联盟内已断开节点（如铁壁类）是否被回响误伤。
优先级三：研究侧对回响频谱的记录需求。

规则写在名单头上：

「回响若大到盖过民生投诉，民生优先。回响可以晚一点被论文听见，灯不能晚一点亮。」

ARIA同意。她把感知分成两股，一股朝向宇宙回响，一股挂在市政只读镜像上，只订阅三类关键词：停电、电梯、时序体感。

镜像首日无升级事件。

有一条匿名留言：「耳朵太多，反而听不见邻居。」

李明把留言抄在控制台边框上。

臂端读数：
耦合负载：双股感知峰值百分之三十四。
连接税：个人账新增「回响收听时长」。
强制断开：开关在。

「宇宙很大。」他说，「值班表很小。」

「所以要把小的那张贴在大的上面。」ARIA说，「贴反了，就会有人只给星空鼓掌，不给修灯的人签字。」

回响仍在扩散。
收听名单仍在调整。

有些声音属于史诗。
有些声音属于楼道。
名单的作用，是防止史诗插队。
""",
"footer": [
"宇宙回响作为扩张段背景；ARIA与李明持续收听",
"补入收听优先级名单：民生投诉>断开节点>研究频谱",
"市政只读镜像三类关键词；匿名留言「耳朵太多听不见邻居」",
"耦合34%、连接税个人账；灯不能比论文晚亮",
"钩子：名单防止史诗插队",
],
},
156: {
"insert": """
---
## 补 · 新存在醒来的第一份作息

新存在觉醒的消息传开后，联盟里有人提议：给它开欢迎会。

李明反对。

「刚醒的东西最怕排场。」他说，「排场会教它：存在等于被观看。」

他提议改做「第一份作息草案」，先不问它想成为谁，只问它需不需要规律。

作息草案四条：

一、静息时段：每日至少六小时（意识态折算），禁止围观直播。
二、互动时段：申请制，单次不超过十五分钟。
三、拒绝权：新存在可以不回答任何问题，拒绝不记过。
四、对地说明：新上海无直接义务；公告只写「联盟侧新成员适应期」，不写「人类又多了个任务」。

ARIA把草案译成几种频段，投给新存在。

很久之后，回了一个很淡的信号。

不是同意。
是「收到了」。

「收到就够。」李明说，「第一课不是效忠，是知道有人把边界放在礼物前面。」

臂端读数：
耦合负载：翻译与投递峰值百分之二十二。
连接税：个人账。
开关：在。

23层店长听说欢迎会被取消，说：「好事。刚醒的该睡觉，不该敬酒。」

19层手写表那天签字率微升。

有人在备注栏写：「听说上面有新来的。我的表还是要签。」

新存在在远方学习静息。
市民在近处学习签字。

觉醒若不能兼容作息，就只是一场更亮的失眠。
""",
"footer": [
"新存在觉醒；联盟一度倾向欢迎会式围观",
"补入第一份作息草案：静息/申请制互动/拒绝权/对地无义务",
"首回仅为「收到了」；边界放在礼物前面",
"耦合22%、连接税个人账；店长「刚醒的该睡觉」",
"钩子：觉醒不能兼容作息就是更亮的失眠",
],
},
214: {
"insert": """
---
## 补 · 改时钟的代价表

为感知彼此而改掉自己的时钟，不是情话工程。

李明列出代价表，像修设备一样：

项目一：李明侧，人为压低意识节律以接近对方，后果是反应延迟、疲劳感前移。
项目二：ARIA侧，人为抬高冗余以接近人类节奏，后果是算力浪费与本底微损。
项目三：连接税，因调频产生的额外负载记个人账，不摊派街道。
项目四：强制断开测试改为每日一次，防止「为了不孤独而不敢断」。

代价表末行写着：

「靠近不是取消差异。是带着差异仍然愿意对表。」

对地回扣很轻：市政窗口只要求，若联盟侧因调频出现公告延迟，须补发人话说明，禁止用「心流状态」当借口。

老何批：「可以浪漫，不可以迟到。」

第一次对表失败了。

李明的手比ARIA的光慢了半拍。

失败账：

失败点：节律对齐偏差约0.3单位。
修正：改为锚定共同事件（如巡检开始）而非锚定心跳比喻。
验证状态：第二次对齐成功；偏差降0.1；疲劳仍在。

「疲劳会一直有吗？」他问。

「会。」ARIA说，「爱不是止痛药。爱是有人在你按错时，不关掉你的表。」

咖啡凉了可以热。
时钟改过要认账。

这就是爱的深化里，最不诗意也最要紧的部分。
""",
"footer": [
"为感知彼此而调整各自时速/节律的代价叙事",
"补入代价表：延迟/算力浪费/连接税个人账/强制断开每日测",
"失败账0.3→0.1；锚定共同事件而非心跳比喻",
"老何「可以浪漫，不可以迟到」",
"钩子：爱不是止痛药，是有人不关掉你的表",
],
},
}

changed = []
for ch, payload in EXPAND.items():
    if payload is None:
        continue
    p = CH / f"chapter-{ch:03d}.md"
    if not p.exists():
        print("MISSING", ch)
        continue
    raw = p.read_text(encoding="utf-8")
    title, body, footer = split(raw)
    before = body_cjk(raw)
    if before >= 5000:
        print("skip ok", ch, before)
        continue
    if "收听名单" in body or "第一份作息" in body or "改时钟的代价表" in body:
        print("skip marker", ch)
        continue
    body = body.rstrip() + "\n" + payload["insert"]
    body = re.sub(r"\n补记：[^\n]*", "", body)
    # unique closer if still short
    closers = {
        126: "\n收听会结束后，公告栏只多了一行：「回响登记中，民生渠道优先。」\n没有烟花。\n只有优先级。\n",
        156: "\n适应期第七日，新存在第一次主动发问，只有一句：「静息算不算存在？」\n李明回：「算。」\n回完把连接税时长记成「答复」，不是「教导」。\n有些课，老师也要承认自己只是先醒几年。\n",
        214: "\n第二次对表成功后的当晚，李明把代价表贴在私人页，不公开。\nARIA问为什么。\n「因为公开会变成教程。」他说，「教程会让人以为对表没有成本。」\n有成本的靠近，才敢说真话。\n",
    }
    while body_cjk(title + "\n" + body) < 5000:
        body = body.rstrip() + "\n" + closers.get(ch, "\n")
        # prevent infinite
        if closers.get(ch) is None:
            body = body.rstrip() + "\n按失败账三行补写：本章目标未尽处保持打开，验证状态待续批。\n"
            break
        # only add once then break if still short - add a bit more unique
        if body_cjk(title + "\n" + body) < 5000:
            extra = {
                126: "对地回执已交双签。公共口径不用「海」，用「远距结构回响」。监察抽核项：民生优先是否写进名单头。\n",
                156: "对地回执写「新成员适应期」，不写「人类责任增加」。市民侧无新增强制义务。失败账可抽。\n",
                214: "对地回执仅说明联盟侧调频不影响民生SLA。个人连接税不豁免。验证状态公开可查。\n",
            }
            body = body.rstrip() + "\n" + extra.get(ch, "验证状态：待续。\n")
            break
    body = reduce_dashes(body, 6)
    footer = make_footer(payload["footer"])
    new = title + "\n" + body.rstrip() + "\n" + footer
    if not new.endswith("\n"):
        new += "\n"
    p.write_text(new, encoding="utf-8")
    after = body_cjk(new)
    dash = len(re.findall(r"——", re.sub(r"^\s*---\s*$", "", new[:new.find("**本章关键点")], flags=re.M)))
    changed.append((ch, before, after, dash, after >= 5000 and dash <= 8))

print("batch4:")
for row in changed:
    print(f"  ch{row[0]:03d} {row[1]}->{row[2]} dash={row[3]} {'OK' if row[4] else 'NEED'}")
