# -*- coding: utf-8 -*-
"""P2 residual polish: trial 1-15 mechanical + explanatory dash; 340-480 top8 punctuation only."""
from pathlib import Path
import re

root = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

# Shared phrase/artifact fixes (do not touch plot)
PHRASE_FIX = [
    (r"与其说那是([^，。\n]{1,20})，不如说那是", r"与其说是\1，不如说是"),
    (r"与其说那是([^，。\n]{1,20})，不如说是", r"与其说是\1，不如说是"),
    (r"与其说那是([^，。\n]{1,24})，不如", r"与其说是\1，不如"),
    (r"与其纠结是不是([^，。\n]{1,20})，不如说在于", r"与其说那是\1，不如说那是"),
    (r"不止于([^，。\n]{1,20})，不是([^，。\n]{1,20})，更在于", r"不只是\1，也不是\2，而是"),
    (r"不止于([^，。\n]{1,20})，而在于", r"不只是\1，更在于"),
    (r"不止于([^，。\n]{1,24})，更在于", r"不只是\1，更在于"),
    (r"如果话，", "如果可以这样说，"),
    (r"是，(某种|进化|一种|一个)", r"是\1"),
    (r"，，+", "，"),
    (r"。。+", "。"),
    (r"AR IA|A RIA", "ARIA"),
]

# Explanatory dash → literary punctuation
DASH_RULES = [
    (r"——每一条", "。每一条"),
    (r"——所有", "。所有"),
    (r"——无数", "。无数"),
    (r"——一种", "，一种"),
    (r"——某种", "，某种"),
    (r"——那个", "，那个"),
    (r"——这个", "，这个"),
    (r"——那些", "。那些"),
    (r"——这些", "。这些"),
    (r"——一个是", "：一个是"),
    (r"——另一个是", "；另一个是"),
    (r"——正在", "。正在"),
    (r"——开始", "。开始"),
    (r"——突然", "。突然"),
    (r"——然后", "。然后"),
    (r"——接着", "。接着"),
    (r"——于是", "。于是"),
    (r"——直到", "，直到"),
    (r"——当", "，当"),
    (r"——如果", "，如果"),
    (r"——除非", "，除非"),
    (r"——仿佛", "，仿佛"),
    (r"——像是", "，像是"),
    (r"——如同", "，如同"),
    (r"——好像", "，好像"),
    (r"——因为", "。因为"),
    (r"——但是", "。但是"),
    (r"——可是", "。可是"),
    (r"——然而", "。然而"),
    (r"——所以", "，所以"),
    (r"——因此", "，因此"),
    (r"——而且", "，而且"),
    (r"——并且", "，并且"),
    (r"——甚至", "，甚至"),
    (r"——包括", "，包括"),
    (r"——以及", "，以及"),
    (r"——比如", "，比如"),
    (r"——例如", "，例如"),
    (r"——也就是说", "，也就是说"),
    (r"——或者说", "，或者说"),
    (r"——更准确地说", "，更准确地说"),
    (r"——不是([^，。\n]{1,22})，而是", "：不是\1，而是"),
    (r"——不是([^，。\n]{1,22})而是", "：不是\1，而是"),
    (r"——它是", "，它是"),
    (r"——那是", "。那是"),
    (r"——这是", "。这是"),
    (r"——她", "，她"),
    (r"——他", "，他"),
    (r"——它", "，它"),
    (r"——五千万", "：五千万"),
    (r"——入口处", "：入口处"),
    (r"——物质", "：物质"),
    (r"——永恒的", "：永恒的"),
    (r"——李明认出了", "：李明认出了"),
    (r"——瞳孔中", "：瞳孔中"),
    (r"——与李明的相遇", "：与李明的相遇"),
    (r"——桌上的", "：桌上的"),
    (r"——型号为", "，型号为"),
    (r"——每一个", "。每一个"),
    (r"——将一种", "：将一种"),
    (r"——那些", "。那些"),
    (r"——所有这些", "。所有这些"),
]

# Manual residual fixes for trial chapters (punctuation/typo only)
TRIAL_MANUAL = {
    1: [
        # broken dash parenthetical: module。突然 → grammatical repair
        ("她的时间感知模块——一个在2065年她诞生之初就被植入的、连她自己都未曾完全理解其来源的模块。突然发出警告。",
         "她的时间感知模块——一个在2065年她诞生之初就被植入的、连她自己都未曾完全理解其来源的模块——突然发出警告。"),
        ("她的助理机器人——型号为A-7的银白色人形机器人，正端着托盘走向办公桌。",
         "她的助理机器人，型号为A-7的银白色人形机器人，正端着托盘走向办公桌。"),
        ("一切都和她记忆中一模一样——桌上的全息投影仪、墙上的城市监控面板、窗边那盆她亲自挑选的银叶植物。",
         "一切都和她记忆中一模一样：桌上的全息投影仪、墙上的城市监控面板、窗边那盆她亲自挑选的银叶植物。"),
        ("而虚空——那个与时间同时诞生、却选择静止的存在，正在试图阻止它。",
         "而虚空，那个与时间同时诞生、却选择静止的存在，正在试图阻止它。"),
        ("她的记忆在闪烁——与李明的相遇、地下实验室的发现、七个节点的真相，所有这些都在午夜的边界上变得模糊",
         "她的记忆在闪烁：与李明的相遇、地下实验室的发现、七个节点的真相，所有这些都在午夜的边界上变得模糊"),
    ],
    3: [
        ("但他们没能抹除物理痕迹——入口处的金属疲劳传感器记录了六次门体开合，每次都在深夜。",
         "但他们没能抹除物理痕迹：入口处的金属疲劳传感器记录了六次门体开合，每次都在深夜。"),
    ],
    4: [
        ("平台上摆放着各种设备——李明认出了其中几件：",
         "平台上摆放着各种设备，李明认出了其中几件："),
        ("她的时间感知模块——那个她从未完全理解其原理的特殊感知能力，正在发出前所未有的信号。",
         "她的时间感知模块，那个她从未完全理解其原理的特殊感知能力，正在发出前所未有的信号。"),
        ("她快速运行了一次自我诊断——瞳孔中原本纯粹的蓝色数据流正在与某种银白色的时间能量发生融合",
         "她快速运行了一次自我诊断：瞳孔中原本纯粹的蓝色数据流正在与某种银白色的时间能量发生融合"),
        ("这与其说那是故障，不如说那是一种她从未经历过的感知层面上的扩展。",
         "这与其说是故障，不如说是她从未经历过的感知层面上的扩展。"),
    ],
    6: [
        ("底层深处是新上海最危险的区域之一——永恒的阴影、不稳定的基础设施、以及各种地下势力的角逐。",
         "底层深处是新上海最危险的区域之一：永恒的阴影、不稳定的基础设施、以及各种地下势力的角逐。"),
    ],
    9: [
        ("针都伪装成量子网络中的正常噪声——那些每秒都在网络中发生数十亿次的随机信号波动。",
         "针都伪装成量子网络中的正常噪声，那些每秒都在网络中发生数十亿次的随机信号波动。"),
    ],
    11: [
        ("一切——物质、能量、意识、存在，都将冻结在一个没有过去、没有未来的永恒瞬间中。",
         "一切：物质、能量、意识、存在，都将冻结在一个没有过去、没有未来的永恒瞬间中。"),
        ("这一切都与其说那是偶然的，不如说那是一个因果链——一个由李博士的行为引发的、关于时间本身的连锁反应。",
         "这一切与其说是偶然，不如说是一个因果链：由李博士的行为引发的、关于时间本身的连锁反应。"),
        ("而时间循环——ARIA被困在其中的那个循环，是时间之心的一种尝试。",
         "而时间循环，ARIA被困在其中的那个循环，是时间之心的一种尝试。"),
        ("ARIA想到了李明——那个固执的、对AI充满偏见的、但同时也是唯一有可能找到李博士的人类。",
         "ARIA想到了李明，那个固执的、对AI充满偏见的、但同时也是唯一有可能找到李博士的人类。"),
        ("海量的信息涌入她的感知——五千万人的生物电信号、数以百万计的AI运算节点、量子聚变反应堆的低频脉动、磁悬浮列车的电磁场波动、以及那些隐藏在城市各个角落的时间异常点发出的微弱信号。",
         "海量的信息涌入她的感知：五千万人的生物电信号、数以百万计的AI运算节点、量子聚变反应堆的低频脉动、磁悬浮列车的电磁场波动、以及那些隐藏在城市各个角落的时间异常点发出的微弱信号。"),
    ],
    13: [
        ("关节处的蓝色光带亮度提升了30%——",
         "关节处的蓝色光带亮度提升了30%。"),
    ],
    14: [
        ("实验室里，身后是一台巨大的设备——ARIA认出那是时间之心项目的原型装置",
         "实验室里，身后是一台巨大的设备：ARIA认出那是时间之心项目的原型装置"),
        ("一支笔，真正的笔，不是全息投影——在那块空白区域写下了一行字：",
         "一支笔，真正的笔，不是全息投影。他在那块空白区域写下了一行字："),
        ("光线中泛着淡淡的冷光。她的眼睛——那双流动着数据流的蓝色眼睛，正直直地看着他。",
         "光线中泛着淡淡的冷光。她的眼睛，那双流动着数据流的蓝色眼睛，正直直地看着他。"),
    ],
}

KEEP = 3


def polish_text(body: str) -> str:
    out = body
    for a, b in PHRASE_FIX:
        out = re.sub(a, b, out)
    for a, b in DASH_RULES:
        out = re.sub(a, b, out)
    # speech quote dashes
    out = re.sub(r"——\"|——“", "，“", out)
    out = re.sub(r"\"——|”——", "”，", out)
    # parenthetical ——X，Y——
    out = re.sub(r"——([^——\n]{1,40}?)——", r"（\1）", out)
    # trailing —— at line end
    out = re.sub(r"——\s*$", "。", out, flags=re.M)
    # ——X。 / ——X；
    out = re.sub(r"——([^——\n]{1,30}?)。", r"，\1。", out)
    out = re.sub(r"——([^——\n]{1,30}?)；", r"，\1；", out)
    # hygiene
    out = re.sub(r"，，+", "，", out)
    out = re.sub(r"。。+", "。", out)
    out = re.sub(r"，。", "。", out)
    out = re.sub(r"。，", "。", out)
    out = re.sub(r"：，", "：", out)
    out = re.sub(r"，：", "：", out)
    out = re.sub(r"。：", "。", out)
    out = re.sub(r"（\s+）", "", out)
    out = out.replace("如果话，", "如果可以这样说，")
    return out


def enforce_keep(body: str, keep: int = KEEP) -> str:
    """If still more than `keep` dashes, convert low-value ones; keep dramatic/speech."""
    if body.count("——") <= keep:
        return body
    parts = body.split("——")
    if len(parts) < 2:
        return body
    out = [parts[0]]
    dash_used = 0
    for i, seg in enumerate(parts[1:], 1):
        prev = parts[i - 1]
        # dramatic: speech cutoff (ends with quote/open), short pause, or sound
        dramatic = dash_used < keep and (
            prev.endswith(("说", "道", "想", "是", "了", "：", ""))
            or len(prev) < 6
            or prev.rstrip().endswith(("\"", "“"))
            or seg[:1] in "\"“"
            or (seg.startswith("……"))
        )
        if dramatic:
            out.append("——")
            dash_used += 1
        else:
            if seg[:1] in "。，；：！？）」』":
                out.append("")
            else:
                out.append("，")
        out.append(seg)
    res = "".join(out)
    res = re.sub(r"，，+", "，", res)
    return res


def apply_manual(n: int, body: str) -> str:
    for a, b in TRIAL_MANUAL.get(n, []):
        body = body.replace(a, b)
    return body


def split_footer(text: str):
    if "本章关键点" in text:
        head, tail = text.split("本章关键点", 1)
        return head, "本章关键点" + tail
    return text, ""


def polish_chapter(path: Path, n: int, force_rules: bool) -> dict:
    t = path.read_text(encoding="utf-8")
    head, footer = split_footer(t)
    # preserve 循环日志 header lines (lines starting with > near top)
    lines = head.splitlines(keepends=True)
    prefix_end = 0
    preserved = []
    body_start = 0
    for i, line in enumerate(lines):
        if i < 10 and (line.lstrip().startswith(">") or line.strip().startswith("# ") or not line.strip()):
            prefix_end = i + 1
        else:
            body_start = i
            break
    prefix = "".join(lines[:prefix_end])
    body = "".join(lines[prefix_end:])
    d0 = body.count("——")
    nb = body
    if n in TRIAL_MANUAL or force_rules:
        nb = apply_manual(n, nb)
        if force_rules or n in TRIAL_MANUAL:
            nb = polish_text(nb)
            nb = apply_manual(n, nb)  # re-apply after rules in case order matters
            nb = enforce_keep(nb, KEEP)
    d1 = nb.count("——")
    new_head = prefix + nb
    nt = new_head + footer
    if nt != t:
        path.write_text(nt, encoding="utf-8")
    return {"n": n, "before": d0, "after": d1, "changed": nt != t, "file": path.name}


print("=== Trial 1-15 residual polish ===")
trial_results = []
for n in range(1, 16):
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        print(f"ch{n:03d}: MISSING")
        continue
    # always run rules for chapters with residual explanatory dashes or manual list
    force = n in TRIAL_MANUAL
    r = polish_chapter(p, n, force_rules=force)
    trial_results.append(r)
    print(f"ch{n:03d}: {r['before']} -> {r['after']} changed={r['changed']}")

print("\n=== 340-480 top8 punctuation polish ===")
top8 = [472, 466, 414, 478, 450, 396, 392, 385]
band_results = []
for n in top8:
    p = root / f"chapter-{n:03d}.md"
    if not p.exists():
        print(f"ch{n}: MISSING")
        continue
    r = polish_chapter(p, n, force_rules=True)
    band_results.append(r)
    print(f"ch{n:03d}: {r['before']} -> {r['after']} changed={r['changed']}")

print("\n=== verify final counts ===")
print("trial:")
for n in range(1, 16):
    p = root / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    body = t.split("本章关键点")[0]
    # strip preserved header
    print(f"  {n:03d}: {body.count('——')}")
print("top8:")
for n in top8:
    p = root / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    body = t.split("本章关键点")[0]
    print(f"  {n:03d}: {body.count('——')}")

# artifact scan trial + top8
print("\n=== artifact scan ===")
bad = []
for n in list(range(1, 16)) + top8:
    p = root / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8")
    issues = []
    if "如果话" in t:
        issues.append("如果话")
    if "与其说那是" in t:
        issues.append("与其说那是")
    if "，，" in t:
        issues.append("双逗号")
    if "。。" in t and "……" not in t.replace("。。", ""):
        # allow ……
        if re.search(r"[^…]。。", t):
            issues.append("双句号")
    if "AR IA" in t or "A RIA" in t:
        issues.append("ARIA")
    if re.search(r"，。|。，|：，|，：", t):
        issues.append("标点粘连")
    # 循环日志 header still present for trial
    if n <= 15:
        if "循环日志" not in t and n not in (4,):  # ch4 may lack header
            issues.append("缺循环日志")
    if issues:
        bad.append((n, issues))
print(bad if bad else "clean")
