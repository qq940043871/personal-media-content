# -*- coding: utf-8 -*-
"""P4 · 悬崖B：121–300 批量 — 长章补 footer + 高 dash 保守降负。
不改剧情；只补格式与压说明性破折号。短章（CJK<5000）留给人工手术，本脚本跳过正文扩写。
"""
import re
from pathlib import Path

CH = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
CJK = re.compile(r"[\u4e00-\u9fff]")

# 已人工深度手术的章节：本脚本不再改 footer/正文
MANUAL_DONE = {281, 293, 177, 219, 300, 202, 289, 295, 286, 297, 143, 285}

# 资产章：只允许补 footer，不压 dash 正文
ASSET = {280}


def body_cjk(text: str) -> int:
    lines = []
    for ln in text.splitlines():
        if re.match(r"^#\s*第\d+章", ln):
            continue
        if "本章关键点" in ln:
            break
        lines.append(ln)
    return len(CJK.findall("\n".join(lines)))


def split_title_body_footer(text: str):
    m = re.match(r"^(#\s*第\d+章[^\n]*)\n(.*)$", text, re.S)
    if not m:
        return None, text, ""
    title, rest = m.group(1), m.group(2)
    idx = rest.find("**本章关键点")
    if idx >= 0:
        body, footer = rest[:idx], rest[idx:]
        # drop preceding --- from body end
        body = re.sub(r"\n---\s*$", "", body.rstrip()) + "\n"
        return title, body, footer
    return title, rest.rstrip() + "\n", ""


def title_name(title: str) -> str:
    m = re.search(r"第\d+章\s*(.+)", title)
    return (m.group(1).strip() if m else "本章")


def make_footer(ch: int, title: str, body: str) -> str:
    """基于标题与正文关键词生成保守页脚。"""
    name = title_name(title)
    # pull some concrete signals
    has_arm = bool(re.search(r"机械臂|连接税|代偿", body))
    has_city = bool(re.search(r"新上海|23层|23 层|十九层|19层|四十七|47层|底层|时光倒流|咖啡馆|停电|配电|电梯|观察窗", body))
    has_arria = "ARIA" in body or "艾瑞亚" in body
    has_li = "李明" in body
    has_void = bool(re.search(r"虚空|裂隙|时间之心|时间网络", body))
    bullets = []
    bullets.append(f"本章围绕「{name}」推进主线事件，保留原有情节走向与人物状态。")
    pts = []
    if has_arria and has_li:
        pts.append("ARIA与李明在事件中继续协作，决策与代价同步记录")
    elif has_arria:
        pts.append("ARIA承担本章核心判断与行动")
    elif has_li:
        pts.append("李明承担本章核心行动与代价")
    if has_arm:
        pts.append("机械臂/连接税相关读数或代偿代价在场")
    if has_city:
        pts.append("可回扣新上海民生节点（配电/电梯/观察窗/中层街巷等）")
    if has_void:
        pts.append("时间网络/虚空相关结构作为背景约束")
    if pts:
        bullets.append("要点：" + "；".join(pts) + "。")
    else:
        bullets.append("要点：本章事件为银河/虚空扩张段的具体节点，威胁落在可感知后果而非空泛概念。")
    bullets.append("格式核对：保留章号与剧情核；后续批次可继续加厚可失败目标与对地账。")
    return "\n---\n\n**本章关键点：**\n" + "\n".join(f"- {b}" for b in bullets) + "\n"


def reduce_dashes(body: str, cap: int = 6) -> str:
    """保守压 dash：说明性 —— 转句读，保留少量戏剧性。"""
    pairs = list(re.finditer(r"——", body))
    if len(pairs) <= cap:
        return body
    # replace from the end, keep first `cap` occurrences
    keep = cap
    # process matches beyond keep
    out = body
    # replace some patterns first
    replacements = [
        (r"——不是([^——]{1,20})，而是", r"不是\1，而是"),
        (r"关键不在([^——]{1,30})——", r"关键不在\1，"),
        (r"不是([^——]{1,24})——而是", r"不是\1，而是"),
        (r"——", "，"),
    ]
    # count current
    def count(s):
        return len(re.findall(r"——", s))

    # first do specific patterns repeatedly
    for pat, rep in replacements[:-1]:
        out = re.sub(pat, rep, out)
    # if still high, replace trailing —— (those likely explanatory)
    while count(out) > cap:
        # replace the last occurrence
        idx = out.rfind("——")
        if idx < 0:
            break
        out = out[:idx] + "，" + out[idx + 2:]
    return out


def ensure_footer_format(title: str, body: str, footer: str) -> str:
    body = body.rstrip() + "\n"
    if not footer.strip():
        footer = ""  # filled by caller
    if footer:
        if not footer.startswith("\n---"):
            footer = "\n---\n\n" + footer.lstrip()
        return title + "\n" + body + footer
    return title + "\n" + body + "\n---\n\n**本章关键点：**\n- （待补）\n"


report = []
for i in range(121, 301):
    if i in MANUAL_DONE:
        continue
    p = CH / f"chapter-{i:03d}.md"
    if not p.exists():
        continue
    text = p.read_text(encoding="utf-8")
    title, body, footer = split_title_body_footer(text)
    if title is None:
        continue
    cjk = body_cjk(text)
    dash_before = len(re.findall(r"——", re.sub(r"\n---\s*$", "", body, flags=re.M)))

    changed = False
    new_footer = footer

    # dash reduce for high-dash (not asset body rewrite; asset only footer)
    if i not in ASSET and dash_before > 8:
        body2 = reduce_dashes(body, cap=6)
        if body2 != body:
            body = body2
            changed = True

    # footer
    if "本章关键点" not in (footer or ""):
        new_footer = make_footer(i, title, body)
        changed = True
    else:
        # normalize footer header
        if not footer.strip().startswith("**本章关键点"):
            new_footer = re.sub(r"^[\s\S]*?(?=\*\*本章关键点)", "", footer, count=1)
            if not new_footer.strip().startswith("**本章关键点"):
                new_footer = "\n---\n\n**本章关键点：**\n" + footer.strip() + "\n"
            changed = True

    if changed:
        # rebuild
        body_out = body.rstrip() + "\n"
        if new_footer:
            if not new_footer.startswith("\n---"):
                new_footer = "\n---\n\n" + new_footer.lstrip()
            if not new_footer.lstrip().startswith("---"):
                pass
            # ensure --- before footer
            if not re.match(r"^\n---\n", new_footer):
                new_footer = "\n---\n\n" + new_footer.lstrip()
        else:
            new_footer = make_footer(i, title, body_out)
        new_text = title + "\n" + body_out + new_footer
        if not new_text.endswith("\n"):
            new_text += "\n"
        p.write_text(new_text, encoding="utf-8")
        report.append((i, cjk, dash_before, len(re.findall(r"——", body_out)), "footer" if "本章关键点" not in footer else "dash/format"))

print(f"changed {len(report)} chapters")
for row in report[:80]:
    print(f"  ch{row[0]:03d} cjk={row[1]} dash {row[2]}->{row[3]} ({row[4]})")
