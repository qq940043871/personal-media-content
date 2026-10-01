# -*- coding: utf-8 -*-
from pathlib import Path
import re
CH = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')

def body_cjk(raw):
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    lines = raw.splitlines()
    body = []
    in_f = False
    for i, l in enumerate(lines):
        if i == 0 and l.strip().startswith('#'):
            continue
        if '本章关键点' in l:
            in_f = True
        if in_f:
            continue
        body.append(l)
    b = '\n'.join(body)
    return len(re.findall(r'[\u4e00-\u9fff]', b)), b.count('——')

def insert(raw, exp):
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    m = '\n---\n**本章关键点'
    if m in raw:
        return raw.replace(m, '\n' + exp.strip() + '\n' + m, 1)
    return raw.replace('**本章关键点', exp.strip() + '\n\n**本章关键点', 1)

# Fix 531 banned name
p = CH / 'chapter-531.md'
raw = p.read_text(encoding='utf-8')
if raw.startswith('\ufeff'):
    raw = raw[1:]
cnt = raw.count('陈远桥')
raw2 = raw.replace('陈远桥', '陈维远')
p.write_text(raw2, encoding='utf-8')
print(f'ch531: 陈远桥 x{cnt} -> 陈维远')

EXP = {
496: '''
核对单被钉上去的第三天，下雨了。

公告栏玻璃起了雾，两张纸隔着雾还能看见字。

一个放学的孩子路过，用手指在玻璃上画了一个小圈，圈住「第六条」那一行。

画完他跑了，圈很快又模糊。

清洁工本来要擦玻璃，看见圈，停了一下，绕开那块地方擦。

绕开擦，也是一种核对。

有人看见了，有人保住了看见的痕迹，有人没有把痕迹当成污渍。

五百章以后的故事，常常只到这一层：

不推翻，不神化，不把湿玻璃擦得太亮。

留一点雾，让下一双眼睛还能画圈。

画圈的人不必知道五百章。

他只需要知道：这里有一行字，值得圈一下。

值得圈，就已经在传承里。

''',
517: '''
和平时期的训练中心，后来真的用了那张空行课程表当招生简章附件。

附件标题很直白：

「我们不保证你变强。
我们保证你有机会发呆。」

报名的人里有退伍的，有刚出院的，有和平年代长大的年轻人。

他们填的「来训理由」五花八门：

「我妈说我该出门。」
「我在家只会刷屏。」
「我想学着不害怕安静。」

第三条被教官用红笔圈了，圈旁边写：

「本条不结课。
只陪练。」

ARIA把这份招生附件存进「和平样本」。

她在私人页写：

「和平不是训练成果展示。
和平是有人敢写：我想学着不害怕安静。
敢写这句的人，比敢上战场的人，更需要被接住。」

训练中心的发呆课后来爆满。

教官不得不排队叫号。

叫号的声音很轻，怕吵到正在发呆的人。

这也许是和平最具体的样子：

叫号都怕吵。

''',
520: '''
终章前夜，市里下了一点雨。

李明没有开伞，站在楼道口看雨落在配电箱的铁皮上。

雨声很密，像有人在很远的地方数数。

「你在听什么？」ARIA问。

「听雨有没有停的意思。」

「有吗？」

「没有。」他说，「那就再站两分钟。」

两分钟之后他上楼，鞋底在台阶上留下一小片湿印，很快干了。

湿印干掉不留档案。

站过的两分钟留。

他在进门时说：「明天照常过，这句我今晚再说一次。」

「说给谁听？」

「说给我自己。」他说，「也说给雨。」

雨不会记账。

人记。

记完了，睡觉。

灯关之前，他把钱包里那张纸又摸了一遍。

纸角有一点毛了，是摸多了。

毛了也认得出来。

铃会响。
人在。
照常过。

三句，够撑过明天。

也够撑过很多个明天。

''',
526: '''
清单执行满一个月时，李明把它从门内侧取下来，重新抄了一份。

旧的那份折好，放进回忆录的纸盒。

新的那份字更小，因为多了一条：

不做了：不把「执行清单」变成自我介绍。
替代：清单是我和自己的事，不必成为别人认识我的方式。

林晓来家里送数据时，看见门内侧的新清单，站着读完了。

「老师，我能抄吗？」

「抄哪条？」

「『不把随便当口头禅』。」她说，「我也有这个毛病。」

「抄。」李明把铅笔递给她，「但别抄我的替代句，写你自己的。」

林晓写的替代句是：

「把『随便』改成『我需要想三十秒』。」

李明看了一眼，说好。

「好在哪里？」

「好在有时间单位。」他说，「三十秒可核对。『认真点』不可核对。」

抄完清单，他们没有再聊清单。

他们聊了下个月失败课的题目。

聊完，林晓把清单收进包里，没有拍照，说拍照会被发到群里，变成打卡。

打卡会让清单死。

纸带回家，清单才活。

一个月，门内侧的字换了一茬。

人没变英雄，变清楚了一点。

清楚，就够继续过日子。

''',
}

for n, exp in EXP.items():
    p = CH / f'chapter-{n:03d}.md'
    raw = p.read_text(encoding='utf-8')
    before, _ = body_cjk(raw)
    raw2 = insert(raw, exp)
    p.write_text(raw2, encoding='utf-8')
    after, dash = body_cjk(raw2)
    flag = 'OK' if after >= 5000 and dash <= 8 else 'FAIL'
    print(f'ch{n}: {before}→{after} dash={dash} {flag}')

print('\n=== 481-540 final ===')
remain = []
for n in range(481, 541):
    raw = (CH / f'chapter-{n:03d}.md').read_text(encoding='utf-8')
    cjk, dash = body_cjk(raw)
    if cjk < 5000 or dash > 8 or '本章关键点' not in raw:
        remain.append((n, cjk, dash))
print('remain', remain if remain else 'NONE')

print('\n=== banned 481-600 ===')
for n in range(481, 601):
    p = CH / f'chapter-{n:03d}.md'
    if not p.exists():
        continue
    raw = p.read_text(encoding='utf-8')
    for w in ['张远', '赵远航', '陈远桥', '初心咖啡']:
        if w in raw:
            print(f'ch{n} {w}')
print('banned scan done')

print('\n=== POOL 40 ===')
POOL = [524,502,487,522,501,486,490,503,537,516,507,523,515,529,498,514,492,543,493,533,578,535,575,539,536,504,530,513,518,534,509,544,577,511,574,545,580,489,525,538]
ok=0
fails=[]
for n in POOL:
    raw = (CH / f'chapter-{n:03d}.md').read_text(encoding='utf-8')
    cjk, dash = body_cjk(raw)
    good = cjk>=5000 and dash<=8 and '本章关键点' in raw
    if good: ok+=1
    else: fails.append((n,cjk,dash))
print(f'pool {ok}/40 fails={fails}')
