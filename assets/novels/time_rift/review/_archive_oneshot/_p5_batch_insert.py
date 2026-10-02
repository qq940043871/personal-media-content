# -*- coding: utf-8 -*-
"""P5 batch: insert city/dialogue scenes + rewrite footers for remaining priority chapters."""
from __future__ import annotations

import re
from pathlib import Path

CH_DIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

# chapter -> (title_hint, scene_block, footer_block)
# scene_block: inserted before footer or at first ## after body start
# footer_block: replaces everything from --- **本章关键点

BATCH = {}

def scene(title: str, theme: str, hook: str) -> str:
    return f"""
---

同一时刻，新上海地面侧。

第23层，「时光倒流」的店门虚掩着。店长把抹布拧到第三遍，对着内网小窗回了一句：

「{theme}再大，桌子还是要擦。你们楼上定完的事，下来个人签收。」

提示没有回答。他在订单备注里写：「按原单。若改道，改道的人签字。」

---

第19层，楼道公告栏。

周晚晴把本周手写表贴上去，电、电梯、窗口三栏空着。她在表头加了一行小字：

「宇宙侧若有变化，请附地面对照栏。没有对照栏的表，我继续空着。」

路过的人看了一眼。「你这表越来越像监察署的了。」

「监察署的表有人填。」她说，「我的表没人填，才更要写清楚该填什么。」

---

第47区，观察窗。

老何把日志翻到新的一页。窗上的雾纹比昨天多了一道断口，像被人用指甲轻轻划过。

他写：「今日窗稳。雾纹断口+1。不写『已恢复』。」

写完他又补一行：

「{hook}」

---
"""


def footer(goal: str, cost: str, hook: str, city: str, voice: str) -> str:
    return f"""---
**本章关键点：**
- 目标：{goal}
- 代价：{cost}
- 钩子：{hook}
- 城市锚点：{city}
- 人话锚：{voice}
"""


BATCH[167] = {
    "insert_before_footer": scene(
        "167", "和谐/共存类结论", "若楼上在定『共存』，楼下得有人写宽度。谁签字，谁付下一次读数的账。"
    ),
    "footer": footer(
        "宇宙侧结论须译成地表可核对项；三节点宽度未齐前公开口径不升格",
        "店长订单备注「若改道，改道的人签字」无回执；周晚晴手写表三栏空；老何雾纹断口+1且拒写「已恢复」",
        "谁签字放行本章公开稿；下一次读数挂在19/23/47哪一处动作上",
        "23层「时光倒流」抹布/订单备注；19层楼道手写表三栏；47区观察窗雾纹断口",
        "店长「下来个人签收」；周晚晴「没有对照栏的表，我继续空着」",
    ),
}

BATCH[226] = {
    "insert_before_footer": scene(
        "226", "传播/融合类观测", "传播若落到这扇窗，先出数，再出词。词不能当回执。"
    ),
    "footer": footer(
        "宇宙侧「传播/融合」降级为观测中；灯/门/窗/班表四样对照齐全前不用大词",
        "19层对照栏空白；23层店长自签验收、联盟侧验收栏空；观测成本不摊街道",
        "谁填联盟侧验收栏；下一次传播读数挂在哪一样设施动作上",
        "23层「时光倒流」验收便签；19层楼道对照栏；47区观察窗「先出数再出词」",
        "老何「词不能当回执」；店长「改道的人签字」",
    ),
}

BATCH[127] = {
    "insert_before_footer": scene(
        "127", "边界/觉醒类读数", "觉醒不是贺电，是交接本。谁签字关闭工单，谁付下一次读数的账。"
    ),
    "footer": footer(
        "边界读数与暂停条件落地；宇宙危机不得取消地面排班；异议文本进可查账",
        "三节点观测继续但回执未齐；在押异议传单若涉及本章结论须进失败账附件；公共修辞禁「梦/海」",
        "谁签字放行公开口径；下一次边界读数的值班人尚未具名",
        "19层电梯/楼道表；23层店门；47区观察窗雾纹；监察署文本流转",
        "李明「空白比错误更贵」；店长「改道的人签字」",
    ),
}

BATCH[238] = {
    "insert_before_footer": scene(
        "238", "深层观测/结构变化", "结构变化四个字扔下来，楼下得有人写宽度。宽度没写出来之前，不叫结论。"
    ),
    "footer": footer(
        "深层观测须出地表译文；结构变化公开稿附三节点宽度；无宽度不升格",
        "机械臂/接口读数入失败账不得写「一切正常」；地面三节点回执时限写进公告；连接税个人账不摊街道",
        "谁签字放行结构变化公开稿；下一次深层读数的地面值班表空着",
        "19层手写表；23层店门与订单备注；47区观察窗雾纹；监察署费用栏",
        "老何「宽度没写出来之前，不叫结论」；周晚晴「空的不算正常，算没人看过」",
    ),
}

BATCH[203] = {
    "insert_before_footer": scene(
        "203", "希望/延续类结论", "希望若真在延续，先延到这张表上。表没人填，就是没延到。"
    ),
    "footer": footer(
        "希望/延续类结论须附可失败的地面对照页；口号不能代替回执",
        "19层手写表空栏未闭环；23层便签「产成人话」无签复；宇宙侧观测成本入联盟账不摊街区",
        "谁在交接本签「已复核」；下一次希望侧读数的译文由谁出具",
        "19层维修工交接本/手写表；23层「时光倒流」便签；夜班日志",
        "李明「谁要看希望，去看他的交接本」；店长「口号没人看」",
    ),
}

BATCH[231] = {
    "insert_before_footer": scene(
        "231", "连接/代价类窗口", "连接税是个人账。窗口再大，也不能替住户签字摊派。"
    ),
    "footer": footer(
        "连接/代价窗口内点名账可查；中断/未结项禁止并入「总体稳定」",
        "连接税个人账不摊街道；切断权在ARIA；店长登记表背面「不怕账，怕没人报账」未获签复；老何拒写「已恢复」",
        "监察署费用栏仍空；下一次连接窗口的预扣与审批人未定",
        "23层登记表背面；19层电梯回执；47层观察窗日志",
        "店长「我们不怕账，怕没人报账」；老何「看不懂就先写下来，不命名」",
    ),
}

BATCH[208] = {
    "insert_before_footer": scene(
        "208", "宏大叙事/宇宙侧结论", "宇宙侧可以慢慢讲，地面侧不能慢慢停摆。灯、门、窗、班表，四样里有一样没变化，就先别用大词。"
    ),
    "footer": footer(
        "宏大结论降级为可验收观测：灯/门/窗/班表；未达标前公开口径用「观测中」",
        "19层电梯/窗口对照未齐；23层店长自签、联盟侧验收栏空；连接税不摊街道；禁「梦/海」作当前态口号",
        "谁填联盟侧验收栏；下一次宏大读数挂在哪一样设施动作上",
        "19层楼道手写表；23层「时光倒流」黑板/便签；47区观察窗；陈明远市政侧若涉听证须具名",
        "李明「词太大，地面上没人签收」；店长「验收人：我」",
    ),
}

BATCH[149] = {
    "insert_before_footer": scene(
        "149", "探索/发现类结论", "发现不是通稿，是工单。工单没有签字人，就不算发现落地。"
    ),
    "footer": footer(
        "探索结论须附地面对照与失败线；无签字人不算落地",
        "三节点回执未齐；连接税个人账；老何/店长日常登记继续；公共修辞禁「梦/海」",
        "谁签字关闭本章工单；下一次探索读数的地面译文由谁出具",
        "19层手写表；23层店门；47区观察窗；研究所值班",
        "店长「改道的人签字」；老何「先出数，再出词」",
    ),
}

BATCH[174] = {
    "insert_before_footer": scene(
        "174", "希望/美好类收束", "美好若不能签收，就别叫美好，叫通知。通知没人看。"
    ),
    "footer": footer(
        "美好/希望类结论须可拒可撤可核对；口号不能代替回执",
        "19层对照栏空；23层店长便签未获签复；观测成本不摊街区",
        "谁签字放行公开稿；下一次读数挂在谁的动作上",
        "19层楼道表；23层「时光倒流」便签；47区观察窗",
        "店长「美好若不能签收，就别叫美好，叫通知」",
    ),
}

BATCH[141] = {
    "insert_before_footer": scene(
        "141", "深层变化/结构读数", "结构变化读数要贴到楼道字号。字太大没人看，字太小没人填。"
    ),
    "footer": footer(
        "深层结构变化须出楼道字号的市民说明；无说明不升格",
        "机械臂/接口代价入失败账；三节点回执时限写进公告；连接税个人账",
        "谁签字放行市民说明；下一次结构读数的值班人未具名",
        "19层公告栏字号；23层店门；47区观察窗；监察署",
        "李明「字太大没人看，字太小没人填」",
    ),
}


def body_and_footer(text: str) -> tuple[str, str | None]:
    m = re.search(r"\n---\s*\n\*\*本章关键点", text)
    if m:
        return text[: m.start()], text[m.start() :]
    return text, None


def main() -> None:
    for ch, payload in BATCH.items():
        p = CH_DIR / f"chapter-{ch:03d}.md"
        if not p.exists():
            print(f"MISSING {ch}")
            continue
        text = p.read_text(encoding="utf-8")
        body, old_footer = body_and_footer(text)
        scene_block = payload["insert_before_footer"]
        # avoid double-insert
        if "同一时刻，新上海地面侧" in body:
            print(f"SKIP scene (already present) {ch}")
        else:
            body = body.rstrip() + "\n" + scene_block
        new_text = body.rstrip() + "\n" + payload["footer"]
        if not new_text.endswith("\n"):
            new_text += "\n"
        p.write_text(new_text, encoding="utf-8")
        print(f"OK {ch} cjk_body~{len(re.findall(r'[\u4e00-\u9fff]', body))}")


if __name__ == "__main__":
    main()
