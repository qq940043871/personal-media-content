# -*- coding: utf-8 -*-
"""P6 repair: fix 536 footer overflow, close body-CJK gaps, fix 487 dash, expand 492."""
from pathlib import Path
import re

CH = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')

def body_stats(raw):
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    lines = raw.splitlines()
    body_lines = []
    in_footer = False
    for i, line in enumerate(lines):
        if i == 0 and line.strip().startswith('#'):
            continue
        if '本章关键点' in line:
            in_footer = True
        if in_footer:
            continue
        body_lines.append(line)
    body = '\n'.join(body_lines)
    return len(re.findall(r'[\u4e00-\u9fff]', body)), body.count('——'), raw

def write_ch(n, raw):
    p = CH / f'chapter-{n:03d}.md'
    p.write_text(raw, encoding='utf-8')
    cjk, dash, _ = body_stats(raw)
    print(f'ch{n}: body_cjk={cjk} dash={dash} {"OK" if cjk>=5000 and dash<=8 else "FAIL"}')
    return cjk, dash

def insert_before_footer(raw, exp):
    """Insert expansion immediately before ---\\n**本章关键点** footer."""
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    marker = '\n---\n**本章关键点'
    if marker in raw:
        return raw.replace(marker, '\n' + exp.strip() + '\n' + marker, 1)
    if '**本章关键点' in raw:
        return raw.replace('**本章关键点', exp.strip() + '\n\n**本章关键点', 1)
    return raw.rstrip() + '\n' + exp

# ---------- repair 536: move post-footer prose into body ----------
p = CH / 'chapter-536.md'
raw = p.read_text(encoding='utf-8')
if raw.startswith('\ufeff'):
    raw = raw[1:]
lines = raw.splitlines()
# find first footer marker
foot_i = None
for i, line in enumerate(lines):
    if line.strip().startswith('**本章关键点'):
        foot_i = i
        break
if foot_i is not None:
    # rebuild: keep title+body before any stray content, collect footer bullets, move mid-expansions to body
    # Strategy: find the real footer bullets (lines starting with '- ' near end or after foot_i that look like footers)
    # Simpler: take everything before first '**本章关键点', plus any prose that appears AFTER footer but BEFORE footer-looking bullets
    head = lines[:foot_i]
    rest = lines[foot_i:]
    # rest[0] is **本章关键点：**
    footer_bullets = []
    mid_prose = []
    for line in rest:
        s = line.strip()
        if s.startswith('**本章关键点') or s.startswith('- '):
            footer_bullets.append(line)
        elif s.startswith('---') or s.startswith('林晓实验室'):
            # footer-ish anchor / separator — if it's the city anchor line keep in footer
            if '林晓实验室' in s and not footer_bullets:
                footer_bullets.append(line)  # shouldn't happen
            elif '林晓实验室' in s:
                footer_bullets.append(line)
            else:
                footer_bullets.append(line)
        elif s == '':
            if footer_bullets and not mid_prose:
                footer_bullets.append(line)
            elif mid_prose:
                mid_prose.append(line)
        else:
            # if we haven't finished collecting footer yet and this doesn't look like footer, it's prose
            if not any(x.strip().startswith('- ') for x in rest[1:]) :
                mid_prose.append(line)
            elif any(b.strip().startswith('- ') for b in footer_bullets) and s.startswith('-'):
                footer_bullets.append(line)
            else:
                # prose that leaked after footer start — if footer already has bullets, this is mid_prose that was wrongly placed
                # Actually in 536: structure is head_body, **footer**, then LEAKED expansions, then "林晓实验室" fragment, then footer bullets without header
                mid_prose.append(line)
    # Rebuild cleanly from known good pattern
    # Read again and reconstruct manually for 536
    text = raw
    # Split at first 本章关键点
    idx = text.find('**本章关键点')
    # Also there may be a second cluster of footer bullets after expansions
    # Find all '- ' footer-like lines at the end
    all_lines = text.splitlines()
    # Collect canonical footer from the END
    end_footer = []
    i = len(all_lines) - 1
    while i >= 0:
        s = all_lines[i].strip()
        if s.startswith('- ') or s.startswith('**本章关键点') or s.startswith('---') or s == '' or s.startswith('林晓实验室'):
            end_footer.insert(0, all_lines[i])
            i -= 1
        else:
            break
    # Body = everything before first 本章关键点 OR before the leaked expansions, whichever...
    # Better: body = lines[0:first footer OR first line of leaked expansion that we know]
    # Find where original body ends: first occurrence of footer marker OR first line of our expansions
    body_end = None
    for i, line in enumerate(all_lines):
        if line.strip().startswith('**本章关键点'):
            body_end = i
            break
    if body_end is None:
        body_end = 0
    body_part = all_lines[:body_end]
    # Everything between body_end and end_footer that is NOT footer-looking is leaked expansion
    mid = all_lines[body_end:len(all_lines) - len(end_footer)]
    leaked = []
    for line in mid:
        s = line.strip()
        if s.startswith('**本章关键点') or s.startswith('- ') or s.startswith('---') or s == '':
            continue
        if s.startswith('林晓实验室') and '全息' in s:
            continue  # city anchor fragment belongs to footer conceptually
        leaked.append(line)
    # Also capture expansion paragraphs that appear in end_footer region if they look like prose (long Chinese lines not starting with -)
    for line in end_footer:
        s = line.strip()
        if s and not s.startswith('-') and not s.startswith('**') and not s.startswith('---') and '林晓实验室' not in s and len(s) > 20:
            leaked.append(line)
    # Canonical footer bullets (dedupe from end)
    fb = []
    seen = set()
    for line in all_lines:
        s = line.strip()
        if s.startswith('- ') and s not in seen and any(k in s for k in ['代价', '公共修辞', '口吻', '城市锚点', '资产', '事件', '钩子', '轻补', '情感']):
            # only take footer-like after we're in footer zone — take the LAST set
            pass
    # Simpler footer reconstruction from end_footer bullets
    bullets = []
    for line in end_footer:
        s = line.strip()
        if s.startswith('- '):
            bullets.append(s)
    # unique preserve order from the end
    ub = []
    for b in reversed(bullets):
        if b not in ub:
            ub.append(b)
    ub = list(reversed(ub))
    if not ub:
        ub = [
            '- 【资产章·轻触】源头的梦：场景/对白/物件补充，情感核保留',
            '- 城市锚点：终端舱软垫、人话库条目、登记本「细节：舱边软垫」',
            '- 公共修辞禁「梦/海」；ARIA瞳孔=融合态；页脚个性化',
            '- 代价（本章独有）：细节比职务难造假；软垫属于「手是她的」那条人话',
            '- 口吻区分：ARIA精确短句 / 李明务实 / 林晓学生腔 / 市民与店长生活口语',
        ]
    new_body = body_part
    if leaked:
        new_body = new_body + [''] + leaked
    # ensure trailing structure
    out_lines = new_body + ['', '---', '**本章关键点：**'] + ub + ['']
    new_raw = '\n'.join(out_lines)
    write_ch(536, new_raw)

# ---------- 487 dash compress ----------
p = CH / 'chapter-487.md'
raw = p.read_text(encoding='utf-8')
if raw.startswith('\ufeff'):
    raw = raw[1:]
cjk, dash, _ = body_stats(raw)
if dash > 8:
    # compress one explanatory dash in body
    parts = raw.split('**本章关键点')
    body = parts[0]
    tail = '**本章关键点' + parts[1] if len(parts) > 1 else ''
    # replace a safe pattern
    body2 = body.replace('每一层的维度、密度、能量特征、以及人类意识在其中的存活概率',
                         '每一层的维度、密度、能量特征，以及人类意识在其中的存活概率')
    # also generic one dash
    if body2.count('——') > 8:
        # find body dashes and replace first non-critical
        body2 = body2.replace('——它是承诺', '：它是承诺')
        body2 = body2.replace('——它是', '：它是', 1)
    if body2.count('——') > 8:
        body2 = body2.replace('不是压力，而是意义', '不是压力，而是意义')  # noop
        # last resort: replace '——' after '样子' patterns
        body2 = re.sub(r'——([^—\n]{1,12})', r'，\1', body2, count=1)
    write_ch(487, body2 + tail)

# ---------- body topups for near-miss chapters ----------
TOPUPS = {
492: '''
孩子开始害怕「分开了的东西还是不是原来那个」。

它把小圆里的两个点分开得更远，远到几乎看不见彼此，然后紧张地盯着，像怕它们突然变样。

ARIA蹲在旁边。

「距离会改形状。」她说，「但不一定改本质。」

「如果改了呢？」

「改了就改了。」她说，「你还是可以认。认，比不变重要。」

孩子用手指在两个点之间轻轻划了一道很淡的线。

线不是绳子，拉不断它，也绑不住谁。

线只是记号：这里曾经挨着。

「记号有用吗？」

「记号不阻止分离。」ARIA说，「记号让分离以后还能被讲述。」

「讲述给谁？」

「讲述给以后还会害怕的人。」

孩子想了很久，把那道线加粗了一点，又没有加到变成墙。

中间仍然可以走人。

这很像楼道里的手写表：不锁门，只留痕。

也像苏婉清曾经留给她的那种距离：不追，不弃，把位置空出来。

分离的困惑最后没有被「解决」。

它只是被画在沙地上，变成可以被看见的东西。

看得见的困惑，比看不见的恐惧好相处。

''',
516: '''
离开医疗中心前，李明在门口的留言墙上贴了一张很小的便签。

不是感谢信，是一句提醒：

「若有人替你做决定，记得问：签字栏在哪。」

字很小，贴在角落。

第二天他听说有人在那句话下面又贴了一张：

「签字栏在我自己手里。」

第三张：「也在。」

三张便签没有署名。

ARIA没有把它们录入系统。

系统会问「有效留言」的定义。

这三张便签的有效性，就在于没被定义。

''',
507: '''
周建国出院那天，李明去送了一趟。

不是医疗安排，是他自己要去。他带了一块很小的磨刀石，放在周建国的工具袋旁边。

「工地用得上。」

「我又不磨刀。」

「磨别的。」李明说，「感觉钝了的时候，找个具体的东西，动手磨一磨。」

周建国把磨刀石收好。

「你那条等人的账，后来结了吗？」

「结了，也没结。」李明说，「人回来了，等待的形状还在我身上。」

「那算好还是不好？」

「算活过。」他说，「活过的事不需要结清，需要被认领。」

周建国点点头，背着工具袋走进新上海的太阳里。

李明在医院门口站了一会儿，看他的背影变小。

认领比结清更难，也更长久。

''',
523: '''
回忆录写到某个雨夜，李明停了笔。

不是写不下去，是他听见楼上有人在练琴，弹得很生，同一个段落反复错。

他把笔放下，听了很久。

ARIA问：「你要下楼去说吗？」

「说什么？」

「说他们吵到你了。」

「没有吵到。」他说，「他们在练。练的意思就是还会错。」

楼上又错了一次。

「我写回忆录也是这个意思。」他重新拿起笔，「不是要写成完美版，是要留下有人练过的证据。」

那天他写得很短，只有一行：

「雨夜。楼上有人练琴。我也是。」

写完他关了灯。

窗外的雨把城市洗得很轻。

练琴声还在，错的那个音也在。

都在，就好。

''',
515: '''
清单第六条「完整是还能让人坐下」写完之后，李明把它念给ARIA听。

「这句像广告。」她说。

「哪里像？」

「太顺了。」她说，「顺得像印出来的。」

李明想了想，把「还」字划掉，又在旁边补了一个：

「完整是能让人坐下。有时候，完整也只是想坐下的冲动还没被掐死。」

「这句好一点。」ARIA说，「因为它不稳。」

「不稳才是人写的。」

他把本子合上。

完整如果只剩漂亮话，那也是一种不完整。

''',
493: '''
故事讲到最后，孩子问：「有没有你不讲的？」

「有。」

「为什么不讲？」

「讲了会变小。」ARIA说，「有些事大到只能说：我不讲。」

孩子点点头，像接受了这个语法。

它在沙地上写了一个空括号：（）

括号里什么都没有。

「这是什么？」

「我不讲的地方。」孩子用那种接近语言的波说，「我给你留的。」

ARIA看着那个空括号，忽然明白：最高级的故事语法，是知道哪里停。

她把空括号扫描进核心页，标签：

「不讲之位。
谁来谁坐。
坐了也不必讲。」

''',
533: '''
林晓走后，陈悦多留了十分钟。

她问ARIA：「我第七格问怕不怕替代，是不是冒犯？」

「不是。」ARIA说，「第七格的价值就是敢问。」

「那林晓老师的格子呢？」

「她的格子是她的。」ARIA说，「不要合并。合并了，两个人只剩一个问题。」

「两个问题会不会互相矛盾？」

「会。」ARIA说，「矛盾好。矛盾说明还有两个人。」

陈悦把这句话写进自己的笔记本，写得很慢。

写完她在页角画了两个并排的空方框，没有填字。

两个框并排，就证明还有两个人在场。

''',
539: '''
出市政大楼时，天已经全黑。

四十七区观察窗那点光比平时清楚，像有人专门擦过玻璃。

ARIA没有上楼去核对是谁擦的。

她只在私人页写：

「今日可核对：
绿萝水已换。
老何的待复核还在。
走廊灯按顺序亮过。
起源与终结之间，还有人擦玻璃。

未核对：
擦玻璃的人是谁。
先不核对。」

先不核对，也是一种尊重。

有些好意查得太清，会变成任务。

让它匿名着，城市反而更松。

''',
534: '''
整理结束前一周，ARIA把三本「我们在整理时想的事」收了上来，又原样还了回去。

「不存档吗？」陈悦问。

「不存。」ARIA说，「存了就变成第四份遗物。遗物已经够了。」

「那我们写这些是为了什么？」

「为了让整理的过程有人认领。」她说，「过程不在箱子里，在写的人手里。」

林晓把自己的本子抱在胸前。

「我可以继续写吗？」

「可以。」ARIA说，「想写就写，想停就停。箱子封了，笔不用封。」

箱子在那天下午被重新封条。

双签：市政与研究所。

ARIA签的是「记录移交完成」，不是「遗忘开始」。

移交完成的意思是：东西找到了该在的位置。

遗忘开始的意思是：没有人再去那个位置。

这两件事，差一整条楼道的灯。

''',
511: '''
民间第2期观察报告在一个雪天被塞进市政信箱。

封面只有一句：

「第2期。写的人多了三个。」

内文最短的一条来自一个中学生：

「观察：安静角不是没人说话，是有人说话声音更小。
小声也算发言吗？」

ARIA在页边批了一个字：

「算。」

批完她把报告复印了三份，分别钉在十九层、二十三层、四十七区。

钉的时候她用了和上次一样的斜钉法。

不是故意做旧，是顺手。

顺手的动作会被下一个人模仿。

模仿久了，就会变成传统。

''',
489: '''
慢光里的两个点，后来ARIA只跟店长提过一次。

她说得很轻：「有一种诞生，是把东西放好就退开。」

店长正在给门轴上油，头也不抬：

「开店也是。东西摆好，人退到柜台后。客人进来看见的是货，不是你。」

「那你会失落吗？」

「会。」店长把油布叠好，「但失落不耽误开门。」

ARIA把这句写进人话库。

人话库新条目：

「诞生与开店：
摆好，退开。
失落不耽误开门。」

写完她看了一眼二十三层的木牌。

字迹还是褪的。

擦的人还是每天在。

诞生还在继续。

开门也是。

''',
538: '''
离开值班室之前，ARIA做了一个很小的动作。

她把旁听席登记本翻到今天那页，在自己签名「旁听者·一号」下面，又添了一行：

「二号栏：留给下次来的市民。不预约，不筛选，来了就签。」

登记员第二天早上看到这行字，没有擦。

他只是在二号栏旁边画了一个很小的圆圈，像在说：收到。

一周后，二号栏真的有人签了。

签名是：「买菜的·王。」

备注写着：「路过。看了一眼待复核。签个名证明来过。」

ARIA在私人页记：

「旁听席001闭环。
不是我的闭环。
是买菜的王的。

中心不在宇宙中心。
中心在有人路过，愿意签一笔。」

''',
}

# also compress 487 if still high after earlier attempt - handled above

for n, exp in TOPUPS.items():
    p = CH / f'chapter-{n:03d}.md'
    raw = p.read_text(encoding='utf-8')
    if raw.startswith('\ufeff'):
        raw = raw[1:]
    raw2 = insert_before_footer(raw, exp)
    write_ch(n, raw2)

print('\n=== RECHECK POOL SHORTS + 487 ===')
POOL = [524,502,487,522,501,486,490,503,537,516,507,523,515,529,498,514,492,543,493,533,578,535,575,539,536,504,530,513,518,534,509,544,577,511,574,545,580,489,525,538]
ok = 0
fails = []
for n in POOL:
    p = CH / f'chapter-{n:03d}.md'
    raw = p.read_text(encoding='utf-8')
    cjk, dash, _ = body_stats(raw)
    foot = '本章关键点' in raw
    good = cjk >= 5000 and dash <= 8 and foot
    if good:
        ok += 1
    else:
        fails.append((n, cjk, dash, foot))
print(f'pool ok {ok}/{len(POOL)}')
print('fails:', fails)
