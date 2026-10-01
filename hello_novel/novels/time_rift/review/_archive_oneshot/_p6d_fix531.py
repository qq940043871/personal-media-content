# -*- coding: utf-8 -*-
from pathlib import Path
import re

p = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters\chapter-531.md")
t = p.read_text(encoding="utf-8")

print("before 人群", t.count("人群散得很慢"))
print("before 离开广场", t.count("离开广场时，二十三层"))
print("before 留言桌", t.count("市民留言桌"))

first = t.find("人群散得很慢")
second = t.find("人群散得很慢", first + 1)
if second < 0:
    raise SystemExit("no second crowd block")
t = t[:first] + t[second:]

exit_dup = (
    "离开广场时，二十三层商业街的方向传来短暂的断电又恢复。灯箱闪了两下，重新亮起「时光倒流」。\n\n"
    "有人在店里说：「让电让过了，牌子还亮着。」\n\n"
    "这句话进不了追悼会主稿。\n\n"
    "但它进得了这一天的账。\n\n"
    "离开广场时，二十三层商业街的方向传来短暂的断电又恢复。灯箱闪了两下，重新亮起「时光倒流」。\n\n"
    "有人在店里说：「让电让过了，牌子还亮着。」\n\n"
    "这句话进不了追悼会主稿。\n\n"
    "但它进得了这一天的账。\n"
)
exit_once = (
    "离开广场时，二十三层商业街的方向传来短暂的断电又恢复。灯箱闪了两下，重新亮起「时光倒流」。\n\n"
    "有人在店里说：「让电让过了，牌子还亮着。」\n\n"
    "这句话进不了追悼会主稿。\n\n"
    "但它进得了这一天的账。\n"
)
if exit_dup not in t:
    raise SystemExit("exit dup not found:\n" + repr(t[t.find("离开广场时") : t.find("离开广场时") + 350]))
t = t.replace(exit_dup, exit_once, 1)
t = t.replace("禁陈维远）", "禁陈远桥）", 1)

line = "- 市民留言桌：「事不要改」；三则原文入私人日志；23层让电后灯箱复亮\n"
while t.count(line) >= 2:
    first_i = t.find(line)
    second_i = t.find(line, first_i + 1)
    t = t[:second_i] + t[second_i + len(line) :]

p.write_text(t, encoding="utf-8")
print("after 人群", t.count("人群散得很慢"))
print("after 离开广场", t.count("离开广场时，二十三层"))
print("after 留言桌", t.count("市民留言桌"))
print("禁陈远桥", "禁陈远桥" in t)
print("禁陈维远", "禁陈维远" in t)
