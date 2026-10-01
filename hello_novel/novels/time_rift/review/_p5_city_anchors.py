# -*- coding: utf-8 -*-
"""P5: insert natural city-anchor scene into chapters with CityK=0 among 481-600."""
import re
from pathlib import Path

dirp = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
assets = set(range(530, 541)) | {600}

# pool of short filmable city-anchor inserts (vary by chapter index)
inserts = [
    (
        "走廊布告栏的灯箱还亮着。玻璃后面钉着一页手写巡检条：「23层「时光倒流」——打烊后门轴上油，灯留到十一点。」旁边有人用铅笔补：「桌子自己擦。」",
        "「布告栏那张，」路过的维修工说，「机器存档里没有。人钉上去的才算数。」\n\n「那就让它继续钉着。」ARIA说。",
    ),
    (
        "楼梯转角的配电箱门虚掩着，箱盖内侧粉笔字还清楚：「19层手写表——今晚灯到九点，够用。」字迹歪，笔画用力。",
        "「表是谁写的？」她问。\n\n夜班电工把安全帽往上推了推。「住家自己抄的。机器说正常，人说灭过四十分钟。以谁的为准？」\n\n「以描过的那张。」",
    ),
    (
        "公告栏玻璃反着光。里面一页复印件标题被红笔圈过：「47区观察窗——夜读数已抄，空签字栏还在。」",
        "「签字栏为什么空着？」\n\n值班员摇头。「监察说等复核。复核没来，表先写着。空着也是账。」",
    ),
    (
        "电梯口的检修单夹在门缝里：「井道夜班指示灯第7盏已换；23层让电，打烊顺延。」",
        "「让电给谁？」\n\n保安把单子抽出来看了一眼。「纪念广场那场。店长说，灯可以晚点，人不能误点。」",
    ),
    (
        "小巷深处的木牌在风里轻晃，字迹褪色仍可辨：「时光倒流」。门框边钉着楼层牌：二十三层。",
        "「还在开？」\n\n店长头也不抬地擦桌子。「机器算得再准，人总要有个地方坐下来。」",
    ),
    (
        "墙上的观察窗标记旁贴着手写表，铅笔一行行往下排：「本层自己数的日子。」末行：「今天灯亮到九点，够用了。」",
        "「为什么不用系统报表？」\n\n邻居把菜篮换了个手。「系统说正常，楼道黑了四十分钟。表上写的是人看见的数。」",
    ),
    (
        "林晓实验室的全息屏还亮着，频谱基线图旁边贴着便签：「观察窗读数抄在手写表背面了，勿并入公共档案。」",
        "「为什么不并档？」\n\n林晓捏了捏笔帽。「老师说过，私人日志和公共账要分开。混了，以后谁说得清。」",
    ),
    (
        "监察联署的空白签字栏摊在桌上，墨水笔搁在旁边，像等人来补一笔。",
        "「这栏还能空多久？」\n\n文书耸肩。「空着也是账。有人签字，才算结。」",
    ),
]


def cjk_count(s):
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def city_hits(body):
    keys = ["时光倒流", "19层", "周晚晴", "47区", "观察窗", "配电箱", "电梯", "监察", "手写表", "林晓实验室", "打烊"]
    return sum(body.count(k) for k in keys)


def main():
    updated = []
    skipped = []
    for n in range(481, 601):
        f = dirp / f"chapter-{n:03d}.md"
        text = f.read_text(encoding="utf-8")
        if text.startswith("\ufeff"):
            text = text[1:]
            f.write_text(text, encoding="utf-8")
        body = re.sub(r"(?s)^#.*\n", "", text)
        body = re.sub(r"(?s)---\s*\*\*本章关键点：\*\*.*$", "", body)
        if city_hits(body) >= 1:
            skipped.append((n, "has_anchor"))
            continue
        # asset chapters: only if still zero, use lightest insert
        scene, dial = inserts[n % len(inserts)]
        if n in assets:
            scene = scene.split("。")[0] + "。"
            dial = ""
        block = "\n" + scene + "\n"
        if dial:
            block += "\n" + dial + "\n"
        # insert before footer
        if "---\n**本章关键点：**" in text:
            text2 = text.replace("---\n**本章关键点：**", block + "\n---\n**本章关键点：**", 1)
        elif "---\r\n**本章关键点：**" in text:
            text2 = text.replace("---\r\n**本章关键点：**", block + "\n---\r\n**本章关键点：**", 1)
        else:
            text2 = text.rstrip("\n") + "\n" + block
        f.write_text(text2, encoding="utf-8")
        updated.append(n)
    print("city_anchor_updated", len(updated))
    print("skipped", len(skipped))
    print("updated", updated)


if __name__ == "__main__":
    main()
