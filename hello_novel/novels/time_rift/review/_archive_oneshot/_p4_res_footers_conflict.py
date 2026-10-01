# -*- coding: utf-8 -*-
"""P4 residual: rewrite conservative 本章围绕 footers in 121-300 to conflict style.

Only footer is rewritten. Body untouched.
Style: 目标/代价/钩子/城市锚点 — 3-5 bullets, unique per chapter, no 同文公文尾.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
FOOTER_RE = re.compile(r"\n---\s*\n\*\*本章关键点[：:]\*\*[\s\S]*$", re.M)
CONSERVATIVE = re.compile(r"本章围绕|本章讲述|本章描写了|本章介绍了|本章主要")

CITY_RE = re.compile(
    r"(第?19层|第十九层|第?23层|第二十三层|第?47层|第四十七层|37街区|第三十七街区|"
    r"店长|老何|时光倒流|观察窗|电梯|配电|楼梯|黑板|手写表|夜班|值班|"
    r"黄浦江|底层区?|中层|新上海|市政大楼|市政府|咖啡馆|病房|医院|"
    r"联盟空间|时间网络|虚空之心|织网|议会|听证|档案馆|研究所|黎明号)"
)
NUM_RE = re.compile(
    r"(\d+(?:\.\d+)?(?:%|小时|分钟|天|人次|人|条|层|次|票|户|周|个月|"
    r"当量|Hz|度|米|公里|个文明|条时间线|条枝条))"
)
DIALOG_RE = re.compile(r"[「「]([^」」]{6,36})[」」]|\"([^\"]{6,36})\"")

# plot keywords → cost/hook flavor
COST_KEYS = [
    ("连接税", "连接税/机械臂负荷入个人账，禁止摊派街道"),
    ("机械臂", "机械臂读数或共振代价写入失败账，不得用「一切正常」盖章"),
    ("代偿", "代偿负荷超线须可切断，切断权不交给表决"),
    ("本底", "ARIA 意识本底波动入监察页，禁止口号化"),
    ("瞳孔", "ARIA 融合瞳孔状态与深层感知同步记账，禁写纯蓝当前态"),
    ("牺牲", "任何「牺牲很美」句式作废；不可逆损伤必须写失败账"),
    ("伤亡", "伤亡/中断须点名可查，禁止并入「事故统计」"),
    ("风暴", "风暴/冲击相关中断回执时限写进公告，不等市民追问"),
    ("虚空", "虚空侧现象若落到地面，必须有对应监测点与暂停条件"),
    ("联盟", "联盟决议若不能翻译成楼道语言，则不升格公开口径"),
    ("信任", "信任建立以可中止协议为验收，不以情绪为验收"),
    ("平衡", "平衡若不可核对，则只算临时状态，不算结论"),
    ("爱", "「爱」不能单独作为验收词；须绑定边界与可拒条款"),
    ("希望", "希望类表述须附一条可失败的地面对照，禁只写宇宙侧"),
    ("永恒", "「永恒」类结论降级为观察期，观察期结束前不发贺电"),
    ("文明", "新文明/他者事项若影响地面，提前公告接口税与休眠窗口"),
    ("战争", "战争/冲突代价入点名账：谁中断、谁值守、谁签字"),
    ("重建", "重建进度用设施语言写：灯、电梯、窗、班表，不用「向好」"),
    ("记忆", "记忆/故事类操作禁止代笔美化；抽核须讲述者本人签字"),
    ("维度", "维度/深层试验先写失败线与回程补位，再谈突破"),
]

GOAL_THEMES = [
    (["虚空", "暗影", "深渊", "侵蚀", "威胁", "裂缝", "背叛"], "边界与暂停"),
    (["联盟", "合作", "调解", "秩序", "挑战", "考验", "裂痕", "会议", "议会"], "可失败处置包"),
    (["爱", "希望", "和平", "信任", "和谐", "平衡", "温暖", "奇迹", "伙伴"], "可拒可撤条款"),
    (["探索", "旅程", "发现", "新的", "成长", "学习", "传承", "训练", "准备"], "阶段目标与失败线"),
    (["战争", "反击", "崩溃", "风暴", "代价", "牺牲", "选择", "冲击", "阴影"], "点名账与未结项"),
    (["永恒", "存在", "意识", "维度", "时间", "生命", "答案", "真相", "源头", "轮回"], "可验收试验"),
    (["重生", "重建", "复苏", "创造", "秩序", "科技", "进化"], "工期与验收表"),
]


def cjk_count(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def body_of(text: str) -> str:
    m = FOOTER_RE.search(text)
    body = text[: m.start()] if m else text
    lines = []
    for ln in body.splitlines():
        if ln.strip().startswith("#"):
            continue
        if ln.strip().startswith(">"):
            continue
        lines.append(ln)
    return "\n".join(lines)


def extract_title(text: str) -> str:
    m = re.search(r"^#\s*第(\d+)章\s*(.+)$", text, re.M)
    if m:
        return m.group(2).strip()
    first = text.lstrip("\ufeff").splitlines()[0] if text else ""
    return re.sub(r"^#\s*", "", first).strip()[:40]


def first_sents(body: str, n: int = 4) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    out = []
    for p in paras[:10]:
        for s in re.split(r"[。！？；]", p):
            s = s.strip()
            if 10 <= cjk_count(s) <= 55:
                out.append(s)
            if len(out) >= n:
                return out
    return out


def last_sents(body: str, n: int = 6) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    out = []
    for p in paras[-10:]:
        for s in re.split(r"[。！？；]", p):
            s = s.strip()
            if 8 <= cjk_count(s) <= 60:
                out.append(s)
    return out[-n:]


def pick_nums(body: str, k: int = 4) -> list[str]:
    found = []
    for m in NUM_RE.finditer(body):
        v = m.group(0)
        if re.fullmatch(r"\d+章", v):
            continue
        if v not in found:
            found.append(v)
        if len(found) >= k:
            break
    return found


def pick_city(body: str, k: int = 6) -> list[str]:
    found = []
    for m in CITY_RE.finditer(body):
        v = m.group(0)
        if v not in found:
            found.append(v)
        if len(found) >= k:
            break
    return found


def pick_dialog(body: str, k: int = 3) -> list[str]:
    found = []
    for m in DIALOG_RE.finditer(body):
        v = (m.group(1) or m.group(2) or "").strip()
        v = re.sub(r"^[，。、：；…\s]+|[，。、：；…\s]+$", "", v)
        # skip incomplete / low-info fragments
        if cjk_count(v) < 8:
            continue
        if v.endswith(("的", "了", "着", "在", "和", "与", "或")) and cjk_count(v) < 12:
            continue
        if v in found:
            continue
        found.append(v)
        if len(found) >= k:
            break
    return found


def short(s: str, limit: int = 26) -> str:
    s = re.sub(r"\s+", "", s)
    s = s.strip("。，、；：「」\"'")
    return s[:limit] + ("…" if len(s) > limit else "")


def goal_for(title: str, opens: list[str], nums: list[str]) -> str:
    theme = None
    for keys, th in GOAL_THEMES:
        if any(k in title for k in keys):
            theme = th
            break
    if opens:
        core = short(opens[0], 20)
    else:
        core = title

    if theme == "边界与暂停":
        base = f"为「{title}」立边界读数与暂停条件"
        if nums:
            base += f"（正文线索：{nums[0]}等）"
        return base + "；宇宙危机不得取消地面排班"
    if theme == "可失败处置包":
        return f"时限内产出「{title}」可失败处置包：谁喊停、如何验收、地表对照三条"
    if theme == "可拒可撤条款":
        return f"「{title}」须写成可拒/可撤/可核对的市民条款，口号不能代替回执"
    if theme == "阶段目标与失败线":
        return f"为「{title}」写阶段目标与失败线：完成什么、拒绝什么、代价记哪本账；开篇线索：{core}"
    if theme == "点名账与未结项":
        return f"「{title}」窗口内完成点名账：中断/伤亡/未结项可查，禁止并入「总体稳定」"
    if theme == "可验收试验":
        return f"把「{title}」压成一次可验收试验：读数、时限、失败后的地面口径"
    if theme == "工期与验收表":
        return f"「{title}」给出工期与验收表：灯/电梯/窗/班表谁签字，禁用「向好」结案"
    return f"推进「{title}」并留下可失败目标（起手：{core}），完成后须有对地回执"


def cost_for(title: str, body: str, nums: list[str]) -> str:
    bits = []
    for key, line in COST_KEYS:
        if key in body or key in title:
            bits.append(line)
            if len(bits) >= 2:
                break
    if nums and len(bits) < 2:
        bits.append("正文读数：" + "、".join(nums[:3]))
    if not bits:
        # thematic fallback by title, still conflict-shaped
        if any(k in title for k in ["爱", "希望", "和平", "温暖", "奇迹"]):
            bits.append("情感结论不得免账：对照节点若无人签字，则本章「实现」降级为观察中")
        elif any(k in title for k in ["永恒", "存在", "维度", "时间", "意识"]):
            bits.append("深层/概念结论以地面可核对读数为代价门槛，否则只记假设")
        else:
            bits.append("本章行动代价入失败账：谁承担、承担多久、能否中止")
    return "；".join(bits[:2])


def hook_for(title: str, ends: list[str], opens: list[str], dialogs: list[str], body: str) -> str:
    # prefer end sentences that carry unfinished pressure
    pressure_words = [
        "还", "未", "等待", "空白", "不知道", "没有", "拒绝", "失败", "代价",
        "裂", "恐惧", "问题", "吗", "？", "会不会", "能不能", "不能", "禁止",
        "下一次", "如果", "也许", "仍然", "继续", "尚未", "不要", "别",
    ]
    candidates = []
    for s in ends:
        if any(w in s for w in pressure_words):
            candidates.append(s)
    if not candidates:
        for s in ends:
            if cjk_count(s) >= 10:
                candidates.append(s)
    if candidates:
        s = candidates[-1]
        return f"章末未结：{short(s, 28)}——相关公开口径暂不升格"
    if dialogs:
        return f"未验收对白：「{short(dialogs[0], 22)}」——能否被执行仍待地面核对"
    if opens:
        return f"起手压力未回收：{short(opens[0], 24)}；下一步签字人未写死"
    return f"「{title}」在市民可自述变化前不升格为贺电口径"


def city_for(body: str, city: list[str], title: str) -> str:
    mapping = [
        ("第十九层", "19层"),
        ("19层", "19层"),
        ("手写表", "19层手写表"),
        ("楼梯", "19层楼梯/照明"),
        ("第二十三层", "23层店长"),
        ("23层", "23层店长"),
        ("店长", "23层店长"),
        ("时光倒流", "时光倒流（中层23层）"),
        ("咖啡馆", "23层时光倒流"),
        ("第四十七层", "47层观察窗"),
        ("47层", "47层观察窗"),
        ("老何", "47层老何"),
        ("观察窗", "观察窗台账"),
        ("37街区", "37街区"),
        ("电梯", "电梯回执"),
        ("黑板", "楼道黑板"),
        ("夜班", "夜班值守表"),
        ("值班", "值班转接"),
        ("市政", "市政频道"),
        ("市政府", "市政大楼"),
        ("医院", "医院/病房观察"),
        ("底层", "底层街区"),
        ("中层", "中层街巷"),
        ("新上海", "新上海民生节点"),
        ("联盟空间", "联盟会场对地译法"),
        ("时间网络", "时间网络侧读数→地面译文"),
        ("虚空之心", "虚空边界监测点"),
        ("织网", "织网深层读数"),
        ("议会", "联盟议会表决与地表对照"),
        ("听证", "公开听证/回执"),
        ("档案馆", "档案馆抽核"),
        ("研究所", "研究所值班"),
        ("黎明号", "远征载具窗口与地面留守"),
    ]
    anchors = []
    used = set()
    for c in city:
        for key, label in mapping:
            if key in c and label not in used:
                anchors.append(label)
                used.add(label)
        if len(anchors) >= 4:
            break
    if not anchors:
        # thematic, not fake chapter content
        if any(k in title for k in ["虚空", "维度", "永恒", "存在", "时间", "源头", "轮回"]):
            anchors = ["深层结论对地译法待补", "19/23/47层观察位续批点名"]
        elif any(k in title for k in ["联盟", "秩序", "会议", "调解", "挑战"]):
            anchors = ["联盟决议→楼道语言译法", "市政频道回执时限"]
        else:
            anchors = ["新上海对地节点（照明/电梯/观察窗）", "市民可核对回执"]
    return " / ".join(anchors[:4])


def make_footer(title: str, body: str) -> str:
    opens = first_sents(body, 4)
    ends = last_sents(body, 6)
    nums = pick_nums(body, 4)
    city = pick_city(body, 6)
    dialogs = pick_dialog(body, 3)

    lines = [
        "---",
        "**本章关键点：**",
        f"- 目标：{goal_for(title, opens, nums)}",
        f"- 代价：{cost_for(title, body, nums)}",
        f"- 钩子：{hook_for(title, ends, opens, dialogs, body)}",
        f"- 城市锚点：{city_for(body, city, title)}",
    ]
    if dialogs:
        d = dialogs[0]
        # avoid ending mid-clause if possible
        if "，" in d and cjk_count(d) > 18:
            d = d.split("，")[0]
        lines.append(f"- 人话锚：「{short(d, 22)}」——公共修辞禁「梦/海」，只用可核对的数")
    return "\n".join(lines) + "\n"


def is_conservative(foot_block: str) -> bool:
    return bool(CONSERVATIVE.search(foot_block))


def process(range_start: int = 121, range_end: int = 300, dry: bool = False) -> list[int]:
    changed = []
    for n in range(range_start, range_end + 1):
        p = ROOT / f"chapter-{n:03d}.md"
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        m = FOOTER_RE.search(text)
        if not m:
            continue
        foot_block = text[m.start() :]
        if not is_conservative(foot_block):
            continue
        body = body_of(text)
        title = extract_title(text)
        title = re.sub(r"^第\d+章\s*", "", title)
        new_foot = make_footer(title, body)
        new_text = text[: m.start()] + "\n" + new_foot
        if not dry:
            p.write_text(new_text, encoding="utf-8")
        changed.append(n)
    return changed


if __name__ == "__main__":
    import sys

    dry = "--dry" in sys.argv
    changed = process(dry=dry)
    print(f"{'DRY ' if dry else ''}rewritten footers: {len(changed)}")
    print(changed)
