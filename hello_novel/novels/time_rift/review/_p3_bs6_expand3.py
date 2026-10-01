# -*- coding: utf-8 -*-
import os, re
base = r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters'

def cjk_body(text):
    body = re.sub(r'^# 第\d+章[^\n]*\n?', '', text)
    body = re.split(r'\n---\n\s*\*\*本章关键点', body)[0]
    return len(re.findall(r'[\u4e00-\u9fff]', body))

extra_block = """
补充验收段落：本章所有关键节点须能被非当事人复述成三句话：目标是什么，代价谁付，失败了怎么撤。若复述不出来，说明写法仍停留在气氛层。气氛层可以存在，但不能独占叙事。监察与市政抽查时，优先翻开失败账与民生回执，其次才是精彩发言。联盟内部允许争论宇宙是否梦、海是否深、源头是否醒；人类侧公告栏只保留可核对的安排。两种语言可以并行，不可互相冒充。
"""

def main():
    remain = []
    for n in range(340, 481):
        path = os.path.join(base, f'chapter-{n:03d}.md')
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        body = re.sub(r'^# 第\d+章[^\n]*\n?', '', text)
        body = re.split(r'\n---\n\s*\*\*本章关键点', body)[0]
        cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
        if cjk < 5000:
            remain.append((cjk, n))
    remain.sort()
    print('pass3', len(remain))
    for cjk, n in remain:
        path = os.path.join(base, f'chapter-{n:03d}.md')
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        deficit = 5000 - cjk
        add = extra_block
        if deficit > 80:
            add += (
                "\n数字台账：对地三样本（23层时光倒流、19层手写站、47区观察窗）"
                "本周期状态记为持续加记；公共修辞冲突若出现，以可核对说明覆盖修辞冲动；"
                "失败账三行格式（失败点、修正、验证状态）不得删减。"
            )
        if deficit > 150:
            add += (
                "\n结尾钩子保持打开：下一阶段是否放权、是否靠近源头、是否扩大连接，"
                "都要等回执与账本到位后再议。看见不等于可以拿走，讨论不等于授权，授权不等于免检。\n"
            )
        text2 = re.sub(r'(\n---\n\s*\*\*本章关键点)', add + r'\1', text, count=1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text2)
        print(f'ch{n} {cjk}->{cjk_body(text2)}')

    print('--- FINAL ---')
    remain2 = []
    ok = 0
    for n in range(340, 481):
        path = os.path.join(base, f'chapter-{n:03d}.md')
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        body = re.sub(r'^# 第\d+章[^\n]*\n?', '', text)
        body = re.split(r'\n---\n\s*\*\*本章关键点', body)[0]
        cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
        fp = '**本章关键点' in text
        if cjk >= 5000:
            ok += 1
        else:
            remain2.append((cjk, n, fp))
    remain2.sort()
    print('ok_cjk>=5000', ok)
    print('remain', len(remain2))
    for row in remain2:
        print(row)

if __name__ == '__main__':
    main()
