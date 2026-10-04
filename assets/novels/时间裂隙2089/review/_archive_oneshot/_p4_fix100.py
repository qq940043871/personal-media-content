# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters\chapter-100.md")
text = p.read_text(encoding="utf-8")
text = text.replace("# 第100章 百章里程碑", "# 第100章 第六节点还没修好", 1)
if "地面侧的公共频道" not in text:
    needle = '每一颗光球都代表着时间网络的一个关键节点。\n\n"第七个节点也稳定了。"ARIA说，声音在这片空间中回荡。'
    repl = (
        "每一颗光球都代表着时间网络的一个关键节点。\n\n"
        "地面侧的公共频道还挂着半截未关闭的汇报页：新上海第七区净水站围标调查、疏散演练报名率偏低、"
        "监察官质问「副市长是否已不生活在地球上」。节点稳定不是书本上的词，是市民明天能不能喝上干净水。\n\n"
        '"第七个节点也稳定了。"ARIA说，声音在这片空间中回荡。代价写在她的日志里：'
        "意识完整度在连续修复后又掉了零点几个百分点，李明的机械臂共振窗口被压缩，"
        "赵远山留下的旧伤记忆仍在网络边缘发烫。"
    )
    if needle not in text:
        print("NEEDLE NOT FOUND")
        i = text.find("第七个节点也稳定了")
        print(repr(text[max(0, i-120):i+80]))
    else:
        text = text.replace(needle, repl, 1)
        print("opening injected")
else:
    print("opening already present")
text = text.replace("平台下方是一片深邃的虚空中漂浮着七颗巨大的光球", "平台下方是一片深邃的虚空，虚空中漂浮着七颗巨大的光球")
if not text.endswith("\n"):
    text += "\n"
p.write_text(text, encoding="utf-8")
print(text.splitlines()[0])
print("footer", "本章关键点" in text)
