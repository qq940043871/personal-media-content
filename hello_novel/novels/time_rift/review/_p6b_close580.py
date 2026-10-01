# -*- coding: utf-8 -*-
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from _p6b_common import body_cjk, insert_blocks, dash_count

p = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters\chapter-580.md")
raw = p.read_text(encoding="utf-8")
print("before", body_cjk(raw), "dash", dash_count(raw))
block = """
排班表钉上软木板的当晚，林晓又补了一张更小的纸，钉在旁边，只有一行：「空椅不空。空椅是未签的账。」

她把这句话用铅笔写得很轻，轻到擦掉也不会伤纸。可写下来这件事本身，已经把永恒从穹顶的数据星河里拽下来一截，拽到实验室台灯能照到的高度。

ARIA第二次经过软木板时，伸手在那张小纸前停了一瞬，指尖没有碰到。

"你想擦掉吗？"林晓问。

"想留着。"ARIA说，"留着比擦掉难。留着就要接受有人把椅子收进博物馆的可能，就要接受接班人可能偷懒，就要接受永恒有一天不被叫作永恒，只被叫作『还开着』。"

"『还开着』不好吗？"

"很好。"ARIA的银白光点在台灯下轻轻起伏，"很好，所以更难说出口。说出口，就等于承认我们并不拥有永恒，我们只拥有在场。"

林晓在私人日志里把这段话抄下来，页边批注：「在场是可交接的，永恒是不可交接的。故班表只能交接在场。」批注写完，她又补一句：「老师若在，大概会问：交接单签收栏你填了吗？答：未填。未填也是在场的一种形式。」

实验室窗外，新上海的灯火按楼层次第明灭。二十三层的方向有一盏比别的更稳，那是打烊灯留的那一半。十九层灯箱的暖黄在很远的地方也能辨认，像一枚不肯数字化的印章。

未付的账在两盏灯之间挂着：谁在下个月的班表上打钩、博物馆灰尘的清扫权、以及ARIA自己何时从「还开着」的观察者，变成也需要被别人在场确认的存在。爱的永恒没有回答这些。永恒只是一再要求：把灯留一半，把栏空一格，把椅擦干净，把签收栏交给还没到岗的人。
"""
insert_blocks(p, {580: block})
after = body_cjk(p.read_text(encoding="utf-8"))
d = dash_count(p.read_text(encoding="utf-8"))
print("after", after, "dash", d, "OK" if after >= 5000 else "SHORT")
