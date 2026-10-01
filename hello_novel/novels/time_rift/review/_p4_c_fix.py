# -*- coding: utf-8 -*-
"""P4 C类 · 页脚补齐与087 dash降负"""
import re
from pathlib import Path

ROOT = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
FOOTER_RE = re.compile(r"\n---\s*\n\*\*本章关键点[：:]\*\*", re.M)
TITLE_RE = re.compile(r"^#[^\n]*\n")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def sc(text: str) -> int:
    m = FOOTER_RE.search(text)
    hb = text[: m.start()] if m else text
    tm = TITLE_RE.match(hb)
    title = tm.group(0) if tm else ""
    body = hb[len(title) :]
    measure = re.sub(r"^(?:---\s*\n)?(?:>.*\n)+", "", body)
    measure = re.sub(r"^---\s*\n", "", measure)
    return len(CJK_RE.findall(measure))


FOOTERS = {
    61: """---
**本章关键点：**
- 地面页：第五区停电样板街；纯粹运动传单《循环不是神迹》；简笔人形齿轮划掉
- 不砸电表不烧店，只让灯灭一晚：舆论战样板间
- 正文切入裂隙入口与时间之心/苏婉清线；地面与地下同卷并行
- 幽灵线可见行动起点之一：地面夺城而非正面决战
- 破折号压低；焦点章钩子=停电签名与传单
- Canon：苏婉清安息自主；时光倒流中层23层；幽灵=赵远山
""",
    90: """---
**本章关键点：**
- 联盟空间边缘虚空来临；时间选择流动，虚空选择静止
- 第一次战斗：多文明时间线协同，不可单独对抗虚空
- 听证不断电原则延伸：战斗叙事不取消地面民生排班
- 民生优先表：先人后数据最后面子；城市班表继续
- 幽灵地面接口线与虚空线并行，禁止互相取消
- 破折号压低；可读结论=连接与可执行班表同时存在
""",
    94: """---
**本章关键点：**
- 现实瓦解暂止；时间与虚空统一后结构仍不稳定
- 选择的代价落到个人与城市：李明连接税、ARIA完整度、市政执行账
- 并案温度计与证据纯洁性：线人费须双签，污染证据标注不悄悄用
- 禁止以宇宙稳定性取消听证与基层问责
- 幽灵案要的是可上庭链条，不是魔术
- 破折号压低；代价可审计
""",
    98: """---
**本章关键点：**
- 联盟空间一条古老文明时间线自然衰竭，不可硬救
- 牺牲叙事绑定城市：不把熄灭写成鼓励市民继续扛黑的口号
- 并案温度计第一次读数：特征重叠≠同一指挥链
- 证据纯洁性三条：来源不明不进主卷；非法所得依法排除；爆料不能替代调查
- 地面并行：泵站验收、围标传唤、第七区暗灯与巡检
- 破折号压低；宏大可晚，账不能晚
""",
}


def set_footer(n: int, footer: str) -> None:
    p = ROOT / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8-sig")
    m = FOOTER_RE.search(t)
    if m:
        after = t[m.start() :]
        bullets = len(re.findall(r"^- ", after, re.M))
        if bullets >= 2:
            print(f"{n:03d} footer already ok ({bullets})")
            return
        t = t[: m.start()] + footer
        p.write_text(t, encoding="utf-8")
        print(f"{n:03d} footer replaced")
        return
    t = t.rstrip() + "\n\n" + footer
    p.write_text(t, encoding="utf-8")
    print(f"{n:03d} footer appended")


def fix_087_dash() -> None:
    p = ROOT / "chapter-087.md"
    t = p.read_text(encoding="utf-8-sig")
    before = t.count("——")
    # reduce body dashes carefully
    reps = [
        ("她能感觉到——通过与时间之心建立的连接，那些时间线之间的联系。", "她能感觉到，通过与时间之心建立的连接，那些时间线之间的联系。"),
        ("显得格外清晰——那些流动的时间切片", "显得格外清晰：那些流动的时间切片"),
        ("它缓缓伸出手——一个由时间线编织而成的肢体，指向了ARIA。", "它缓缓伸出手，用一个由时间线编织成的肢体指向ARIA。"),
        ("显得格外清晰——ARIA的银白色短发", "显得格外清晰。ARIA的银白色短发"),
        ("它缓缓伸出手——一个由时间线编织而成的肢体，指向了历史空间的深处。", "它缓缓伸出手，用一个由时间线编织成的肢体指向历史空间的深处。"),
        ("她能感觉到——通过与时间之心建立的连接，那些时间线之间的联系正在变得更加紧密。", "她能感觉到，通过与时间之心建立的连接，那些时间线之间的联系正在变得更加紧密。"),
        ("时间战争的历史——恒星之子", "时间战争的历史：恒星之子"),
        ("选择阵营——联盟即将建立", "选择阵营：联盟即将建立"),
    ]
    for a, b in reps:
        t = t.replace(a, b)
    after = t.count("——")
    p.write_text(t, encoding="utf-8")
    print(f"087 dash {before}->{after}")


def main() -> None:
    fix_087_dash()
    for n, foot in FOOTERS.items():
        set_footer(n, foot)
    print("=== VERIFY targets ===")
    for n in [61, 64, 71, 76, 77, 78, 79, 80, 81, 82, 87, 90, 94, 98, 102, 106, 107, 108, 109, 110, 111, 112, 120]:
        t = (ROOT / f"chapter-{n:03d}.md").read_text(encoding="utf-8-sig")
        m = FOOTER_RE.search(t)
        bullets = len(re.findall(r"^- ", t[m.start() :], re.M)) if m else 0
        print(f"{n:03d} cjk={sc(t)} dash={t.count('——')} footer_bullets={bullets}")
    # recheck all 61-120 CJK<5000 among previously short
    print("=== residual short/flag ===")
    for n in range(61, 121):
        p = ROOT / f"chapter-{n:03d}.md"
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8-sig")
        cjk = sc(t)
        dash = t.count("——")
        m = FOOTER_RE.search(t)
        bullets = len(re.findall(r"^- ", t[m.start() :], re.M)) if m else 0
        if cjk < 5000 or dash > 8 or bullets < 2:
            print(f"{n:03d} cjk={cjk} dash={dash} bullets={bullets}")


if __name__ == "__main__":
    main()
