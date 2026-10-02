# -*- coding: utf-8 -*-
from pathlib import Path
import re
CH = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters')
NOTES = Path(r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\writing-notes.md')

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

# before from task pool (A=asset light)
BEFORE = {
524:3462,502:3464,487:3479,522:3495,501:3508,486:3515,490:3518,503:3522,
537:3524,516:3534,507:3539,523:3544,515:3549,529:3570,498:3578,514:3582,
492:3584,543:3594,493:3595,533:3601,578:3603,535:3605,575:3613,539:3619,
536:3622,504:3641,530:3643,513:3646,518:3658,534:3679,509:3683,544:3700,
577:3707,511:3708,574:3721,545:3725,580:3767,489:3775,525:3783,538:3791,
}
ASSET = set(range(530,541))
POOL = list(BEFORE.keys())

rows = []
for n in POOL:
    raw = (CH / ('chapter-%03d.md' % n)).read_text(encoding='utf-8')
    cjk, dash = body_cjk(raw)
    title = ''
    for line in raw.splitlines():
        if line.startswith('#'):
            title = line.strip().lstrip('#').strip()
            break
    mark = 'A' if n in ASSET else ''
    rows.append((n, BEFORE[n], cjk, dash, mark, title))

# also cont batch extras in 481-540
EXTRA = [484,488,491,495,496,500,505,506,508,510,512,517,519,520,526,527,528,531,540]
extra_rows = []
for n in EXTRA:
    raw = (CH / ('chapter-%03d.md' % n)).read_text(encoding='utf-8')
    cjk, dash = body_cjk(raw)
    title = ''
    for line in raw.splitlines():
        if line.startswith('#'):
            title = line.strip().lstrip('#').strip()
            break
    extra_rows.append((n, cjk, dash, title))

# verify 481-540
bad = []
for n in range(481,541):
    raw = (CH / ('chapter-%03d.md' % n)).read_text(encoding='utf-8')
    cjk, dash = body_cjk(raw)
    if cjk < 5000 or dash > 8:
        bad.append((n,cjk,dash))

table_lines = []
table_lines.append('| 章 | 前CJK | 后CJK | dash | 标记 | 章名 |')
table_lines.append('|----|-------|-------|------|------|------|')
for n,b,a,d,m,t in rows:
    table_lines.append('| %d | %d | **%d** | %d | %s | %s |' % (n,b,a,d,m,t[:20]))

table_lines.append('')
table_lines.append('**续扫扩写（481–540 池外短章，后CJK/dash）**：')
table_lines.append('')
table_lines.append('| 章 | 后CJK | dash | 章名 |')
table_lines.append('|----|-------|------|------|')
for n,c,d,t in extra_rows:
    table_lines.append('| %d | %d | %d | %s |' % (n,c,d,t[:20]))

record = '''
### P6 施工记录 · 批次1（2026-07-07 · 最短优先池 + 481–540 续扫）

**范围**：P6 后期卷门禁批次1。就地扩写，情节结论不变；资产章 530–540 只补场景/对白/物件/城市锚点，**不掏空**情感峰值与主题收束（530融合核/531追悼/534传承/538中心/539起源终结/540继续存在）。

**门禁口径**：正文汉字 CJK≥5000（去 BOM/标题/页脚 `**本章关键点：**`）；正文 dash≤8；页脚齐；禁同文公文尾。

**扩写配方（后期卷）**：可拍场景（时光倒流打烊/19层手写表/47区观察窗/林晓实验室/追悼会物件/保管区巡检签/时间之海感官）+ 潜台词对白 + 城市锚点 + 章末未付账。**不是**再堆宇宙哲学。

**目标池（最短优先，40 章，A=资产轻量）**：

%s

**池外 481–540 续扫**：

%s

**机械核（本批结束时）**：
- 目标池 40/40：正文 CJK≥5000、dash≤8、页脚齐
- **481–540 全段** body CJK<5000 = **0**；dash>8 = **0**
- 535 dash 17→**2**；487 dash 9→**8**；489 dash 13→**2**
- 禁用名：正文 张远/赵远航/陈远桥 = 0（ch531 市长 **陈远桥→陈维远**）；ch594「初心咖啡」仅页脚口径说明（P5 既有，非正文场景）
- ch530–540/资产：只轻触/加场景物件，融合核、追悼、情感峰、结尾节奏保留

**Canon 锁（本批未破坏）**：
- 李明 2051/2075毕业+意愿/**2078入所**/七年/ch530融合/2099逝48；机械臂 2085 后约四年多
- 幽灵=**赵远山**在押；禁张远/赵远航/陈远桥
- 时光倒流=中层**23层**；首遇=**2089循环**（非2082咖啡馆）
- 陈明远（在任）/ **陈维远（ch531追悼）** / 陈志明（交通）
- 苏婉清非保险丝；市民禁「梦/海」→结构发现/老部件新读数
- 民生三件套：23层/19层周晚晴/47区观察窗；失败账=失败点→修正→验证
- ch600=时间之海/回望，**非**物理同行（本批未改600）
- ARIA瞳孔=融合态（银主蓝辅/紫）

**资产章扩写要点（只加不掏）**：
- 530：保管区吴管理员三支笔/白瓷碗磕痕/巡检签沿用手写表格式/「空着也是账」；融合核心句未删
- 531：陈维远让电单/花束楼层条「等也是工作」；追悼节奏保留
- 533：陈悦第七格/清单空格与日期/「合并了就只剩一个问题」
- 534：2078入所便签/十四支铅笔/验证栏「教给了下一个人」/边界三条
- 535：感恩墙/食堂过塑采购协议/「空着也是账」类人话；黄金时代非指标样本
- 536：舱边软垫「手是她的」/人话库/登记本「垫。」；源头梦核未掏空
- 537：孙美娟横格本/小赵「像有人在数东西」/一毫米改版；永恒=有人愿意添一行
- 538：中心人话梯度/旁听席一号→买菜的王；中心感知核保留
- 539：绿萝换水/老何待复核/走廊灯往返；起源终结主题句保留，结尾改为「有灯」
- 540：茶水间跳盖壶/周晚晴代换水「顺手进记忆」；继续存在节奏保留

**脚本（可删）**：`review/_p6_scan_pool.py`、`_p6_wave1_expand.py`、`_p6_wave1_topup.py`、`_p6_wave2_expand.py`、`_p6_wave2_topup.py`、`_p6_wave2_topup2.py`、`_p6_wave3_expand.py`、`_p6_wave3_topup.py`、`_p6_wave3_topup2.py`、`_p6_wave4_expand.py`、`_p6_wave4_topup.py`、`_p6_wave5_expand.py`、`_p6_final_topup.py`、`_p6_gate_close.py`、`_p6_verify_batch1.py`、`_p6_inspect.py`、`_p6_inspect2.py`、`_p6_repair_close.py`、`_p6_close_492_536.py`、`_p6_cont_expand.py`、`_p6_final_scan.py`、`_p6_last7.py`、`_p6_last4_canon.py`、`_p6_pocket_fix.py`、`_p6_pocket2.py`

**残余/可选后续**：
- 481–540 长度门本批已关闭；**541–600 仍有短章/dash>8 章**（542/546/555/558/561/562/566/567/571–573/576/579/582–593/595/597–599 等）待后续批次
- 全书 61–600 机械核复扫（P6 父项）未在本批执行
- Dialog/K 文学密度（P5 残余）未重开
- ch594 页脚「初心咖啡不再出现」为口径说明，可口吻化但非正文禁用词

''' % ('\n'.join(table_lines[:2+len(rows)]), '\n'.join(table_lines[2+len(rows):]))

# insert record into writing-notes after P6 施工记录 placeholder
notes = NOTES.read_text(encoding='utf-8')
anchor = '### P6 施工记录\n\n（批次完成后追加）\n'
if anchor in notes:
    notes = notes.replace(anchor, '### P6 施工记录\n' + record, 1)
    NOTES.write_text(notes, encoding='utf-8')
    print('writing-notes updated at P6 施工记录')
else:
    # append near P6 section
    if '### P6 施工记录' in notes:
        notes = notes.replace('### P6 施工记录', '### P6 施工记录\n' + record, 1)
        NOTES.write_text(notes, encoding='utf-8')
        print('writing-notes updated (alt)')
    else:
        notes = notes.rstrip() + '\n\n### P6 施工记录 · 批次1\n' + record
        NOTES.write_text(notes, encoding='utf-8')
        print('writing-notes appended at end')

print('481-540 bad:', bad if bad else 'NONE')
print('pool rows', len(rows), 'extra rows', len(extra_rows))
print('--- sample ---')
for line in table_lines[:12]:
    print(line)
