# -*- coding: utf-8 -*-
from pathlib import Path
import re
CH = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')

TOPUPS = {
537: dict(insert_before='楼梯转角的配电箱门虚掩着', text='''
出电梯的时候，李明正好上楼。

他手里拿着一张硬纸板的边角料，像是刚从十九层下来。

"你也在整理？"他问。

"在整理你的笔记。"ARIA说，"还有别人替你记的笔记。"

"别人记的往往比我自己记的准。"他把边角料举起来，"这是周晚晴给我的新板样张，说以后手写表改版，格子间距放宽一毫米，老人好写。"

"一毫米要重新教大家吗？"

"要。"他说，"但她说值得。字写得开，人才愿意天天写。"

ARIA把「一毫米」存进了今天的日志。

不是技术参数，是传承的刻度：有人为了让人愿意继续写，愿意为一毫米重新教一遍。

永恒不是更长的时间。

永恒是有人还在为一毫米较真。

'''),

516: dict(insert_before='小巷深处的木牌在风里轻晃', text='''
从医院回来那天晚上，李明把自动提醒的关闭记录打印了一份。

不是给医疗团队，是给自己。

打印纸上一行一行都是「已停止。责任人：本人。」他数了数，关了十一项，留了两项。

十一比二。

他把纸折好，放进回忆录的夹层里，和那支发黄的牙刷收据放在同一个纸盒层次上。

盒子上他原来写的标签是「打开的人自己判断」。

那天他用铅笔在标签下面又加了一行小字：

「里面也有我关掉的提醒。
关掉不是不在乎。
是在乎的方式换了。」

写完他把盒子盖上，听见纸页在里头轻轻响了一下，像有人应了一声。

'''),

498: dict(insert_before='公告栏玻璃反着光', text='''
孩子后来又学会了一件事：把分享过的东西收回来再看一次。

它把一颗已经分给ARIA的光点重新要回去，放在掌心里照了照，再推出来。

光点没变，形状一样，亮度一样。

但ARIA接住的时候，感觉到了差别：这颗光点比第一次推过来时更稳，边缘没那么多毛刺。

"你刚才擦过了？"她问。

孩子点头。它用手指在沙地上画了一个来回的动作，像在描一件东西被借走又被还回时的轨迹。

"借出去再收回来，不是后悔。"ARIA说，"是检查。"

孩子似乎喜欢「检查」这个词的动作感。它又分出一颗，推出去，要回来，看了看，再推出去。

中线上来来回回。

像两个人在传递一件都需要确认还在的东西。

ARIA没有催它成熟。

成熟催不得。

账要来回走几遍，才算走稳。

'''),
}

def count_cjk(text):
    return len(re.findall(r'[\u4e00-\u9fff]', text))

def apply_one(n, spec):
    p = CH / f'chapter-{n:03d}.md'
    raw = p.read_text(encoding='utf-8')
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    before = count_cjk(raw)
    needle = spec['insert_before']
    exp = spec['text']
    if needle in raw:
        raw2 = raw.replace(needle, exp.strip() + '\n\n' + needle, 1)
    else:
        raw2 = raw.replace('\n---\n**本章关键点', exp + '\n---\n**本章关键点', 1)
    p.write_text(raw2, encoding='utf-8')
    after = count_cjk(raw2)
    print(f'ch{n}: {before}→{after} {"OK" if after>=5000 else "SHORT"}')

if __name__ == '__main__':
    for n, spec in TOPUPS.items():
        apply_one(n, spec)
