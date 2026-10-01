# -*- coding: utf-8 -*-
"""P4 literary-density helpers: boilerplate strip + CJK verify."""
import os, re

BASE = r'D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters'

BOILER_START = re.compile(
    r'\n(本章后续执行按|对地镜像与失败账制度继续有效|第\d+章对应的现场补充|'
    r'执行夜班交接时|复盘小组最后补记|补充验收段落|数字台账：|结尾钩子保持打开)'
)

def path(n):
    return os.path.join(BASE, 'chapter-%03d.md' % n)

def read_ch(n):
    with open(path(n), 'r', encoding='utf-8') as f:
        return f.read()

def write_ch(n, text):
    with open(path(n), 'w', encoding='utf-8') as f:
        f.write(text)

def cjk_count(text):
    body = re.sub(r'^# 第\d+章[^\n]*\n?', '', text.lstrip('\ufeff'))
    body = re.split(r'\n---\n\s*\*\*本章关键点', body)[0]
    return len(re.findall(r'[\u4e00-\u9fff]', body))

def dash_count(text):
    body = re.sub(r'^# 第\d+章[^\n]*\n?', '', text.lstrip('\ufeff'))
    body = re.split(r'\n---\n\s*\*\*本章关键点', body)[0]
    return body.count('——')

def has_footer(text):
    return '**本章关键点：**' in text or '**本章关键点**' in text

def strip_boilerplate(text):
    """Remove identical script-expansion appendix blocks before footer."""
    # Keep everything up to first boiler marker that sits before --- footer
    m = BOILER_START.search(text)
    if not m:
        return text, 0
    # find footer
    fm = re.search(r'\n---\n\s*\*\*本章关键点', text)
    if not fm:
        return text, 0
    if m.start() >= fm.start():
        return text, 0
    # also remove any trailing blank lines before marker, keep narrative
    head = text[:m.start()].rstrip() + '\n\n'
    tail = text[fm.start():]
    removed = len(re.findall(r'[\u4e00-\u9fff]', text[m.start():fm.start()]))
    return head + tail, removed

def verify(n, text=None):
    t = text if text is not None else read_ch(n)
    return {
        'n': n,
        'cjk': cjk_count(t),
        'dash': dash_count(t),
        'footer': has_footer(t),
        'ok': cjk_count(t) >= 5000 and dash_count(t) <= 8 and has_footer(t),
    }

def ensure_before_footer(text, narrative_add):
    """Insert narrative_add just before the --- footer block."""
    fm = re.search(r'\n---\n\s*\*\*本章关键点', text)
    if not fm:
        return text
    head = text[:fm.start()].rstrip()
    tail = text[fm.start():]
    return head + '\n\n' + narrative_add.strip() + '\n' + tail
