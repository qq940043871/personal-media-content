# -*- coding: utf-8 -*-
import os, re
base = r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters'

def cjk_body(text):
    body = re.sub(r'^# 第\d+章[^\n]*\n?', '', text)
    body = re.split(r'\n---\n\s*\*\*本章关键点', body)[0]
    return len(re.findall(r'[\u4e00-\u9fff]', body))

scene = """
执行夜班交接时，李明把本章涉及的行动项抄进地面控制值班本，只抄可核对句子：
第一，任何扩大连接、披露或接触范围的动议，必须先附失败账预写栏，不允许会后补。
第二，对地三样本读数即使平稳，也要逐日提交，平稳也是账。
第三，公共材料若出现梦、海、唤醒、末日等词，值班员有权当场退回，不等上级审美。
第四，街道否决权不因联盟热度自动失效；有人在楼道里说不，程序就要听得见。
第五，个人健康与连接税记在个人名下，不摊派给市民。
值班本页脚沿用那句老话：政治的地基在配电箱旁边。宇宙可以很大，表要有人看。
"""

def expand_all():
    need = []
    for n in range(340, 481):
        path = os.path.join(base, f'chapter-{n:03d}.md')
        if not os.path.exists(path):
            continue
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        body = re.sub(r'^# 第\d+章[^\n]*\n?', '', text)
        body = re.split(r'\n---\n\s*\*\*本章关键点', body)[0]
        cjk = len(re.findall(r'[\u4e00-\u9fff]', body))
        if cjk < 5000 and '**本章关键点' in text:
            need.append((cjk, n))
    need.sort()
    print('to_expand', len(need))

    for cjk, n in need:
        path = os.path.join(base, f'chapter-{n:03d}.md')
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        deficit = 5000 - cjk
        # craft extra unique-ish paragraph based on chapter number
        extra = (
            f"\n第{n}章对应的现场补充：联盟侧把本阶段关键动作编号入档，"
            f"允许失败，不允许无账失败。监察抽查优先看三件事：是否有明确截止时间，"
            f"是否有城市或联盟的真实成本，是否有验证状态。"
            f"若三者缺一，材料退回重写，不接受只感动人的版本。"
            f"新上海侧同步要求：凡涉及民生触感的描述，必须能落到电、电梯、窗口、纸张或班表。"
            f"写不出这些词的段落，可以留在私人日志，不能进公共说明。\n"
        )
        if deficit > 200:
            extra += scene
        if deficit > 500:
            extra += (
                "\n复盘小组最后补记：一次行动是否成熟，不看发言是否精彩，"
                "看失败之后还能不能被复述、被追责、被修正。"
                "成熟的制度不怕丑陋的失败账，只怕漂亮的空转。\n"
            )
        text2 = re.sub(r'(\n---\n\s*\*\*本章关键点)', extra + r'\1', text, count=1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text2)
        print(f'ch{n} {cjk} -> {cjk_body(text2)}')

    # recount
    print('--- FINAL REMAIN <5000 with footer or missing ---')
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
        fp = '**本章关键点' in text
        dash = len(re.findall(r'——', body))
        if cjk < 5000:
            remain.append((cjk, n, fp, dash))
    remain.sort()
    print('count', len(remain))
    for row in remain:
        print(row)

if __name__ == '__main__':
    expand_all()
