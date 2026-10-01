# -*- coding: utf-8 -*-
"""Scan 340-480 for template marker residual (2+ markers)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from _p4_polish_lib import BASE, path, read_ch, cjk_count, dash_count, has_footer, BOILER_START

MARKERS = [
    '本章后续执行按',
    '对地镜像与失败账制度继续有效',
    '夜班交接五条',
    '执行夜班交接时',
    '数字台账',
    '补充验收段落',
    '结尾钩子保持打开',
    '复盘小组',
]

def marker_hits(text):
    hits = []
    for m in MARKERS:
        c = text.count(m)
        if c:
            hits.append((m, c))
    return hits

def is_boiler_block_line(line):
    # line is residual if it's the appendix-style long template
    boiler_phrases = [
        '纪律收束：',
        '与失败账制度继续有效：',
        '三样本保持只读加记',
        '公共修辞对市民禁用无法核对的大词',
        '目标是什么，代价谁付，失败了怎么撤',
        '对地三样本（23层时光倒流、19层手写站、47区观察窗）本周期状态记为持续加记',
        '成熟的制度不怕丑陋的失败账',
        '下一阶段是否放权、是否靠近源头、是否扩大连接',
        '不看发言是否精彩，看失败之后还能不能被复述',
    ]
    return any(p in line for p in boiler_phrases)

def residual_score(text):
    """Count distinct template markers that appear in boiler-like lines."""
    lines = text.splitlines()
    score = 0
    found = []
    for line in lines:
        if not is_boiler_block_line(line):
            continue
        for m in MARKERS:
            if m in line or any(m in line for _ in [1]):
                # map line to markers via phrase association
                pass
        # classify by line content
        if '本章后续执行按' in line or '纪律收束：' in line:
            found.append('本章后续执行按')
            score += 1
        if '对地镜像与失败账制度继续有效' in line or ('对地镜像' in line and '失败账制度' in line):
            found.append('对地镜像制度')
            score += 1
        if '夜班交接' in line:
            found.append('夜班交接')
            score += 1
        if '数字台账' in line or ('对地三样本' in line and '本周期状态' in line):
            found.append('数字台账')
            score += 1
        if '补充验收段落' in line or '目标是什么，代价谁付' in line:
            found.append('补充验收段落')
            score += 1
        if '结尾钩子保持打开' in line:
            found.append('结尾钩子保持打开')
            score += 1
        if '复盘小组' in line:
            found.append('复盘小组')
            score += 1
    # also raw count for known boiler phrases
    raw = 0
    for phrase in [
        '本章后续执行按',
        '对地镜像与失败账制度继续有效',
        '补充验收段落：',
        '数字台账：',
        '结尾钩子保持打开：',
        '复盘小组最后补记',
        '执行夜班交接时',
        '夜班交接五条',
    ]:
        raw += text.count(phrase)
    return raw, found

print('=== RESIDUAL SCAN 340-480 (raw boiler phrase counts) ===')
residual = []
for n in range(340, 481):
    p = path(n)
    if not os.path.exists(p):
        continue
    t = read_ch(n)
    raw, found = residual_score(t)
    cjk = cjk_count(t)
    dash = dash_count(t)
    foot = has_footer(t)
    if raw >= 2 or len(found) >= 2:
        residual.append((n, raw, found, cjk, dash, foot))
        print(f'n={n} raw={raw} found={found} cjk={cjk} dash={dash} foot={foot}')
    elif raw == 1:
        print(f'n={n} raw=1 found={found} cjk={cjk} (borderline)')

print()
print('=== ALL chapters with ANY raw boiler phrase ===')
any_raw = []
for n in range(340, 481):
    p = path(n)
    if not os.path.exists(p):
        continue
    t = read_ch(n)
    raw, found = residual_score(t)
    if raw:
        any_raw.append(n)
        print(f'n={n} raw={raw} found={found} cjk={cjk_count(t)}')
print('residual_ids=', [n for n,_,_,_,_,_ in residual])
print('any_raw_ids=', any_raw)

# known candidates check
known = [345,354,357,359,361,368,370,371,373,374,375,403,405,406,409,425,431,441,449,453,466]
print('\n=== KNOWN CANDIDATES DETAIL ===')
for n in known:
    p = path(n)
    if not os.path.exists(p):
        print(f'n={n} MISSING')
        continue
    t = read_ch(n)
    raw, found = residual_score(t)
    print(f'n={n} raw={raw} found={found} cjk={cjk_count(t)} dash={dash_count(t)} foot={has_footer(t)}')
