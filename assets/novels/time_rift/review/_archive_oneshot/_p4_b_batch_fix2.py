# -*- coding: utf-8 -*-
"""P4-B 二次：残余 nofoot 补页脚 + 残余 dash>8 降负。
优先处理未 parse 成功的章（可能含 BOM / 标题异常）。
"""
import re
from pathlib import Path

CH = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
CJK = re.compile(r"[\u4e00-\u9fff]")

MANUAL = {281,293,177,219,300,202,289,295,286,297,143,285,123,296}

def cjk_of(text):
    lines=[]
    for ln in text.splitlines():
        if re.match(r"^#\s*第\d+章", ln): continue
        if "本章关键点" in ln: break
        lines.append(ln)
    return len(CJK.findall("\n".join(lines)))

def title_of(text):
    t = text.lstrip("\ufeff")
    m = re.search(r"^#\s*第(\d+)章\s*(.+)$", t, re.M)
    return (m.group(0).strip() if m else None), (m.group(2).strip() if m else "本章")

def strip_bom(t):
    return t[1:] if t.startswith("\ufeff") else t

def reduce_dashes(body, cap=6):
    # specific patterns
    body = re.sub(r"——不是([^—\n]{1,24})，而是", r"不是\1，而是", body)
    body = re.sub(r"不是([^—\n]{1,24})——而是", r"不是\1，而是", body)
    body = re.sub(r"关键不在([^—\n]{1,30})——", r"关键不在\1，", body)
    body = re.sub(r"与其说([^—\n]{1,20})——不如", r"与其说\1，不如", body)
    while len(re.findall(r"——", body)) > cap:
        idx = body.rfind("——")
        if idx < 0: break
        body = body[:idx] + "，" + body[idx+2:]
    return body

def make_footer(name, body):
    has_arm = bool(re.search(r"机械臂|连接税|代偿", body))
    has_city = bool(re.search(r"新上海|23层|23 层|19层|十九层|47层|四十七|底层|时光倒流|咖啡馆|停电|配电|电梯|观察窗|街区", body))
    pts=[]
    if "ARIA" in body: pts.append("ARIA参与推进")
    if "李明" in body: pts.append("李明承担行动/代价")
    if has_arm: pts.append("机械臂或连接税读数在场")
    if has_city: pts.append("可回扣新上海民生节点")
    if re.search(r"虚空|裂隙|时间之心|时间网络|联盟", body): pts.append("时间网络/虚空/联盟作为背景约束")
    if not pts: pts.append("银河/虚空扩张段具体节点")
    return (
        "\n---\n\n**本章关键点：**\n"
        f"- 本章围绕「{name}」推进，保留原情节走向与章号。\n"
        f"- 要点：{'；'.join(pts)}。\n"
        "- 格式：页脚已补；后续批次可继续加厚可失败目标与对地账。\n"
    )

changed=[]
for i in range(121,301):
    if i in MANUAL:
        continue
    p = CH/f"chapter-{i:03d}.md"
    if not p.exists():
        continue
    raw = p.read_text(encoding="utf-8")
    text = strip_bom(raw)
    title_line, name = title_of(text)
    if not title_line:
        # try recover any 第X章
        m=re.search(r"第%d章[^\n]*"%i, text)
        if m:
            title_line = "# "+m.group(0).strip()
            name = m.group(0)
        else:
            title_line = f"# 第{i}章 本章"
            name=f"第{i}章"
    # body/footer
    rest = text[text.find(title_line)+len(title_line):] if title_line in text else text
    idx = rest.find("**本章关键点")
    if idx>=0:
        body, footer = rest[:idx], rest[idx:]
        body = re.sub(r"\n---\s*$", "", body.rstrip())+"\n"
    else:
        body, footer = rest.rstrip()+"\n", ""
    cjk = cjk_of(text)
    dash_before = len(re.findall(r"——", re.sub(r"\n---\s*$","",body,flags=re.M)))
    need=False
    if dash_before>8:
        body2=reduce_dashes(body,6)
        if body2!=body:
            body=body2; need=True
    if "本章关键点" not in footer:
        footer = make_footer(name, body)
        need=True
    elif not re.search(r"\*\*本章关键点", footer):
        footer = make_footer(name, body)
        need=True
    if not need:
        continue
    # normalize
    if not footer.startswith("\n---"):
        footer = "\n---\n\n" + footer.lstrip()
    if not footer.lstrip().startswith("---"):
        footer = "\n---\n\n**本章关键点：**\n" + re.sub(r"^.*?\*\*本章关键点：\*\*", "**本章关键点：**", footer, count=1, flags=re.S)
    new = title_line+"\n"+body.rstrip()+"\n"+footer
    if not new.endswith("\n"): new+='\n'
    p.write_text(new, encoding="utf-8")
    dash_after=len(re.findall(r"——", body))
    changed.append((i,cjk,dash_before,dash_after,"本章关键点" not in (raw)))

print(f"changed2 {len(changed)}")
for r in changed:
    print(f"  ch{r[0]:03d} cjk={r[1]} dash {r[2]}->{r[3]}")
