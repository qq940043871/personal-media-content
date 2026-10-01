# -*- coding: utf-8 -*-
"""P5 refined: detect P4 auto-footer cost/hook boilerplate templates."""
from pathlib import Path
import re
import json

CHDIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

# Named chapter-specific anchors
NAMED = [
    "老周", "周晚晴", "老何", "配电箱", "19层", "十九层", "47区", "四十七区",
    "23层", "二十三层", "铜牌", "电梯", "冰柜", "店长", "林晓", "陈明远",
    "陈维远", "赵远山", "苏婉清", "李博士", "伊瑟拉", "阿宁", "周岚",
    "监察署", "听证", "签字表", "杂货店", "咖啡馆", "黎明号", "守钥",
    "线脉", "影种", "灰紫", "市民频道", "班表", "回访", "反对者", "家属",
    "观测窗", "观察窗", "配电", "楼道", "值班站", "联防", "公告栏",
    "账单", "配额", "名单", "失败账", "第",  # 第 is too broad - handle separately
]
# stricter named list without 第
NAMED_STRICT = [n for n in NAMED if n != "第"]

# Generic city-anchor boilerplate fragments
GENERIC_CITY = [
    "新上海民生节点",
    "时间网络侧读数",
    "地面译文",
    "联盟会场对地译法",
    "市政频道",
    "研究所值班",
    "远征载具窗口与地面留守",
    "底层街区",
    "市政保障",
]

# Exact boilerplate cost lines from P4 auto batch
P4_COST_BOILER = [
    "代价：机械臂读数或共振代价写入失败账，不得用「一切正常」盖章；ARIA 融合瞳孔状态与深层感知同步记账，禁写纯蓝当前态",
    "代价：机械臂读数或共振代价写入失败账，不得用「一切正常」盖章；ARIA融合瞳孔状态与深层感知同步记账，禁写纯蓝当前态",
    "代价：连接税个人账不摊派；对地成本须有数字",
    "代价：连接税加重但对地无影响",
    "代价：机械臂负载与连接税",
    "代价：ARIA意识波动风险",
]

P4_COST_PATTERNS = [
    r"代价[：:].*机械臂读数或共振代价写入失败账.*禁写纯蓝当前态",
    r"代价[：:].*机械臂读数或共振代价写入失败账",
    r"代价[：:]连接税个人账不摊派；对地成本须有数字",
    r"代价[：:].*机械臂负载与连接税$",
    r"代价[：:].*ARIA.{0,6}意识.{0,4}风险$",
    r"代价[：:].*连接税加重但对地无影响",
    r"代价[：:].*时间的代价$",
    r"钩子[：:]章末未结[：:].+——相关公开口径暂不升格$",
    r"钩子[：:].*相关公开口径暂不升格$",
    r"城市锚点[：:].*(新上海民生节点|时间网络侧读数|联盟会场对地译法).*(新上海民生节点|时间网络侧读数|联盟会场对地译法|市政频道|研究所值班)",
]

# Cost/hook that is generic sole boilerplate without named anchors
GENERIC_COST_CORE = [
    "机械臂读数或共振代价写入失败账",
    "连接税个人账",
    "ARIA 融合瞳孔状态",
    "ARIA融合瞳孔状态",
    "禁写纯蓝当前态",
    "对地成本须有数字",
    "相关公开口径暂不升格",
    "宇宙危机不得取消地面排班",
    "机械臂代价",
    "连接税加重",
    "意识完整度风险",
]


def extract_footer(text: str):
    m = re.search(r"\*\*本章关键点[：:]?\*\*\s*\n([\s\S]+)$", text)
    if not m:
        return None, None
    pre = text[: m.start()]
    title_line = ""
    for line in pre.splitlines():
        if line.startswith("#"):
            title_line = line.strip()
            break
    footer = m.group(1).strip()
    bullets = []
    for line in footer.splitlines():
        s = line.strip()
        if s.startswith("-") or s.startswith("*") or s.startswith("·"):
            bullets.append(s.lstrip("-*· "))
        elif s:
            bullets.append(s)
    return title_line, bullets


def bullet_has_named(b: str) -> bool:
    for n in NAMED_STRICT:
        if n in b:
            return True
    # chapter-specific numbers: % hours 票 号 层 区 ℃ with context
    if re.search(r"\d+(\.\d+)?\s*(%|％|小时|层|区|票|号|℃|条|页|分钟|字)", b):
        return True
    if re.search(r"第[一二三四五六七八九十百零\d]+(条|页|号|小时|名|位|批)", b):
        return True
    return False


def is_p4_cost_boiler(b: str) -> bool:
    for pat in P4_COST_PATTERNS:
        if re.search(pat, b):
            return True
    return False


def is_generic_cost_bullet(b: str) -> bool:
    core = b.strip()
    # strip leading labels for residual check but keep full for pattern match
    if is_p4_cost_boiler(core):
        return not bullet_has_named(core)

    # cost/hook bullet that uses only generic tokens
    costish = any(k in core for k in ["代价", "连接税", "机械臂", "ARIA", "意识完整度", "钩子", "风险", "负担"])
    if not costish:
        return False
    if bullet_has_named(core):
        return False
    # if it mentions generic boilerplate cores
    for g in GENERIC_COST_CORE:
        if g in core:
            return True
    # short generic
    residual = core
    for t in ["代价", "连接税", "机械臂", "ARIA", "意识", "完整度", "风险", "负担",
              "共振", "读数", "失败账", "个人账", "融合", "瞳孔", "状态", "波动",
              "加重", "负载", "成本", "对地", "钩子", "章末未结", "口径", "升格",
              "公开", "相关", "禁写", "纯蓝", "当前态", "盖章", "一切正常",
              "摊派", "数字", "不得用", "写入", "同步", "记账"]:
        residual = residual.replace(t, "")
    residual = re.sub(r"[\s，。、：:；;的了和与及是在有伴随由因导致带来付出承受·「」\"\"（）()——\-—]", "", residual)
    if len(residual) <= 6:
        return True
    return False


def classify_footer(bullets):
    """Return (needs_rewrite, reasons, cost_generic_flags)."""
    if not bullets:
        return False, ["no_bullets"], []
    flags = []
    reasons = []
    all_text = "\n".join(bullets)
    for b in bullets:
        flags.append(is_generic_cost_bullet(b))

    generic_cost_flags = flags  # per bullet
    any_generic = any(flags)

    # P4 template cost+hook combo
    has_p4_cost = any(is_p4_cost_boiler(b) and not bullet_has_named(b) for b in bullets)
    # city anchor only generic
    city_bullets = [b for b in bullets if "城市锚点" in b or "民生" in b]
    city_generic_only = False
    if city_bullets:
        cb = city_bullets[0]
        named_in_city = bullet_has_named(cb)
        gen_city_hits = sum(1 for g in GENERIC_CITY if g in cb)
        if gen_city_hits >= 2 and not named_in_city:
            city_generic_only = True

    # overall: needs rewrite if cost/hook bullets are generic boilerplate
    # even if event bullets have some content
    cost_hook_generic = False
    for b, f in zip(bullets, flags):
        label_ok = ("代价" in b or "钩子" in b or "连接税" in b or "机械臂" in b)
        if f and label_ok:
            cost_hook_generic = True
            reasons.append(f"generic:{b[:60]}")
        elif f:
            cost_hook_generic = True
            reasons.append(f"generic_unlabeled:{b[:60]}")

    # Also flag pure-P4-template footers (goal boilerplate + cost boilerplate + hook template)
    goal_boiler = any(re.search(r"目标[：:].*立边界读数与暂停条件", b) for b in bullets)
    hook_template = any(re.search(r"钩子[：:].*相关公开口径暂不升格", b) for b in bullets)
    if goal_boiler and (has_p4_cost or hook_template):
        cost_hook_generic = True
        reasons.append("p4_full_template")

    needs = cost_hook_generic or (any_generic and city_generic_only)
    return needs, reasons, flags


def main():
    ranges = [(121, 300), (61, 120), (341, 480)]
    all_r = []
    for lo, hi in ranges:
        for n in range(lo, hi + 1):
            p = CHDIR / f"chapter-{n:03d}.md"
            if not p.exists():
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            title, bullets = extract_footer(text)
            if bullets is None:
                all_r.append({"n": n, "path": str(p), "title": title, "status": "NO_FOOTER", "bullets": []})
                continue
            needs, reasons, flags = classify_footer(bullets)
            status = "NEEDS" if needs else "OK"
            all_r.append({
                "n": n,
                "path": str(p),
                "title": title,
                "status": status,
                "reasons": reasons[:4],
                "generic_flags": flags,
                "bullets": bullets,
            })

    needs = [r for r in all_r if r["status"] == "NEEDS"]
    ok = [r for r in all_r if r["status"] == "OK"]
    nof = [r for r in all_r if r["status"] == "NO_FOOTER"]
    print(f"scanned={len(all_r)} NEEDS={len(needs)} OK={len(ok)} NO_FOOTER={len(nof)}")

    # breakdown by range
    for lo, hi, label in [(121, 300, "121-300"), (61, 120, "61-120"), (341, 480, "341-480")]:
        sub = [r for r in needs if lo <= r["n"] <= hi]
        print(f"  {label}: NEEDS={len(sub)}")

    print("\n=== NEEDS (all) ===")
    for r in needs:
        gidx = [i for i, f in enumerate(r["generic_flags"]) if f]
        gb = [r["bullets"][i][:70] for i in gidx if i < len(r["bullets"])]
        print(f"{r['n']:03d}\t{r['title'][:36]}\t{gb}")

    print("\n=== OK samples (first 15) ===")
    for r in ok[:15]:
        print(f"{r['n']:03d}\t{r['bullets'][:3]}")

    out = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review\_p5_needs_scan.json")
    out.write_text(json.dumps(all_r, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
