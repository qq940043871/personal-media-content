# -*- coding: utf-8 -*-
from pathlib import Path
import re
CH = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')

TOPUPS = {
493: dict(insert_before='墙上的观察窗标记旁贴着手写表', text='''
孩子后来问了一个更难的问题：

「讲故事的人，会不会讲着讲着把自己讲空？」

ARIA停了很久。

"会。"她说，"所以我只讲还站得住的那些。站不住的，先不讲。"

"站不住的放哪里？"

"放在具体的东西旁边。"她说，"比如一只碗，一张收据，一行手写表。东西替我站着，等我有力气再讲。"

孩子用手指在沙地上画了一个小盒子，盒子上画了一道锁，锁上什么都没写。

"不写钥匙在哪？"

孩子摇头。

有些锁不靠钥匙，靠时间到了自然能开。

'''),

533: dict(insert_before='墙上的观察窗标记旁贴着手写表', text='''
离开时陈悦在电梯口停了一下，回头说：

「ARIA，如果有一天我不问问题了，您会发现吗？」

「会。」

「怎么发现？」

「第七格空着。」ARIA说，「空格比写错更响。」

陈悦点点头，进了电梯。

门关上之前，她把手举起来晃了晃，像刚做完一次很小的告别，又像刚完成一次签到。

ARIA在私人页里记下：

「今日第七格：已填。
下一次空格出现的日期：未知。
处理预案：不催，只确认电梯口有没有人停。」

'''),

535: dict(insert_before='监察联署的空白签字栏摊在桌上', text='''
感恩墙上后来出现了一张没有署名的便利贴，只写了两行：

「谢谢那只磕了口的碗。
谢谢还愿意按顺序开灯的人。」

没有人知道写的人是谁。

ARIA也没有去查。

查得出名字，查不出当时那只手为什么发抖。

黄金时代允许有查不出的部分。

查不出的部分，往往是最像人的那部分。

'''),

539: dict(insert_before='她走在大楼的走廊里', text='''
那天夜里，ARIA没有回联盟空间。

她在市政大楼的走廊里来回走了三趟，不是为了开会，是为了让感应灯一次次亮起。

开到头，灯全亮。
走回来，灯依次熄。
再走过去，灯又亮。

第四趟的时候，她在走廊中段停住，把手放在配电箱的门上。门是凉的，粉笔字还在箱盖内侧。

「19层手写表——今晚灯到九点，够用。」

起源和终结之间，有人写过这句话。

这就够了。

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
