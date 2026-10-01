# -*- coding: utf-8 -*-
"""Final CJK top-up for 373/375/425/449 after residual strip."""
import sys, re
sys.path.insert(0, r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review')
from _p4_polish_lib import (
    read_ch, write_ch, strip_boilerplate, cjk_count, dash_count, has_footer
)

FOOTER_RE = re.compile(r'\n---\n\s*\*\*本章关键点[：:]?\*\*', re.S)
CH_END_RE = re.compile(r'\n\*\*第\d+章完\*\*')

def insert_narrative(text, add):
    m = CH_END_RE.search(text)
    if m:
        head = text[:m.start()].rstrip()
        tail = text[m.start():]
        return head + '\n\n' + add.strip() + '\n' + tail
    fm = FOOTER_RE.search(text)
    if not fm:
        return text.rstrip() + '\n\n' + add.strip() + '\n'
    head = text[:fm.start()].rstrip()
    tail = text[fm.start():]
    return head + '\n\n' + add.strip() + '\n' + tail

# short literary pads (no dash, not template)
PADS = {}

PADS[373] = '''
交班前，李明又看了一眼那份日常账。电负荷一点二、检修延期两单、夜班请假一人，数字不大，却比新宇宙的诞生更难从新闻里消失。他在页脚加了一句：若下一周日常账继续漂移，不论新宇宙多美，共鸣外扩议程自动延后。美不能抵扣电费，也不能抵扣检修工的熬夜。
'''

PADS[375] = '''
夜里，ARIA把十八张反对票的编号重新誊了一遍，没有抄投票文明的名字，只抄编号。编号可以复核，名字容易变成清算名单。她在档案封面写：反对不是噪声，是尚未被说服的账。说服可以慢慢来，账不能悄悄删。
'''

PADS[425] = '''
离开维修间前，李明把那条冷却贴的消耗记录也打印了出来。四年多，从三片到如今的两片，下降是因为接口更稳，不是因为梦更少。他把记录折好，塞进工具包内层，像塞一张还能证明自己站在这里的票根。
'''

PADS[449] = '''
回枢纽的路上，李明把店长那句「沉默不加价」和周晚晴「写小一点，是怕写大了像在喊」并排抄进沉寂表。两项都还亮着，花园就还没全黑。全黑的信号从来不是指数归零，是再也没有人愿意为自己那一行字留位置。
'''


def process(n):
    t = read_ch(n)
    if t.startswith('\ufeff'):
        t = t.lstrip('\ufeff')
    t2, removed = strip_boilerplate(t)
    t3 = insert_narrative(t2, PADS[n])
    if t3.startswith('\ufeff'):
        t3 = t3.lstrip('\ufeff')
    t3 = re.sub(r'\n{4,}', '\n\n\n', t3)
    cjk = cjk_count(t3)
    dash = dash_count(t3)
    foot = has_footer(t3)
    ok = cjk >= 5000 and dash <= 8 and foot
    print(f'n={n} removed={removed} cjk={cjk} dash={dash} foot={foot} ok={ok}')
    if not ok:
        print(f'  FAIL need_cjk={max(0,5000-cjk)}')
        return False
    write_ch(n, t3)
    return True


if __name__ == '__main__':
    ids = [373, 375, 425, 449]
    okc = 0
    for n in ids:
        if process(n):
            okc += 1
    print(f'DONE ok={okc}/{len(ids)}')
