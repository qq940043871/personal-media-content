# -*- coding: utf-8 -*-
"""P5: extract body signals for NEEDS chapters to drive footer rewrites."""
from pathlib import Path
import re
import json

CHDIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
SCAN = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review\_p5_needs_scan.json")

NAMED_POOL = [
    "老周", "周晚晴", "老何", "配电箱", "店长", "林晓", "陈明远", "陈维远",
    "赵远山", "苏婉清", "李博士", "伊瑟拉", "阿宁", "周岚", "监察署",
    "黎明号", "守钥", "线脉", "影种", "灰紫", "市民频道", "班表", "回访",
    "反对者", "家属", "观测窗", "观察窗", "楼道", "值班站", "联防",
    "公告栏", "账单", "配额", "杂货店", "咖啡馆", "虚空之心", "共鸣者",
    "铁壁", "织网", "概念生命", "轮回", "时间之心", "希望", "纯粹运动",
    "觉醒者", "监察", "听证", "市政", "新上海", "联盟", "ARIA", "李明",
    "苏雨晴", "Nexus", "第七区", "47", "23层", "19层", "37", "143",
]

# Already-specific cost indicators → skip rewrite
SKIP_IF_COST_HAS = [
    r"\+\d+(\.\d+)?h",
    r"\d+(\.\d+)?h 当量",
    r"\d+(\.\d+)?Hz",
    r"\d+(\.\d+)?%",
    r"老周", "店长", "林晓", "陈明远", "配电箱", "冰柜", "铜牌",
    r"票", r"名单第", r"截止",
]

# Deep surgery known-good chapters (from writing-notes P4)
DEEP_OK = {143, 145, 148, 152, 144, 177, 219, 236, 237, 291, 316, 340}


def extract(text):
    m = re.search(r"\*\*本章关键点[：:]?\*\*\s*\n([\s\S]+)$", text)
    if not m:
        return None
    pre = text[: m.start()]
    title = ""
    for line in pre.splitlines():
        if line.startswith("#"):
            title = line.strip()
            break
    body = pre
    # strip title line
    body_lines = [ln for ln in body.splitlines() if not ln.startswith("#")]
    body_txt = "\n".join(body_lines).strip()
    footer = m.group(1).strip()
    bullets = []
    for line in footer.splitlines():
        s = line.strip()
        if s.startswith("-") or s.startswith("*") or s.startswith("·"):
            bullets.append(s.lstrip("-*· "))
        elif s:
            bullets.append(s)
    return title, body_txt, bullets, m.start()


def body_signals(body_txt):
    named = [n for n in NAMED_POOL if n in body_txt]
    nums = re.findall(r"\d+(?:\.\d+)?(?:%|％|小时|分钟|层|区|票|号|℃|条|页|字|Hz|h|次|人|项|%)", body_txt)
    # last non-empty paragraphs
    paras = [p.strip() for p in body_txt.split("\n") if p.strip()]
    opening = paras[0][:200] if paras else ""
    ending = " | ".join(p[:120] for p in paras[-2:]) if paras else ""
    mid_sample = paras[len(paras)//2][:160] if paras else ""
    # quotes
    quotes = re.findall(r"[「\"“]([^」\"”]{4,40})[」\"”]", body_txt)[:6]
    return {
        "named": named[:20],
        "nums": nums[:25],
        "opening": opening,
        "ending": ending,
        "mid": mid_sample,
        "quotes": quotes,
        "cjk_len": len(re.findall(r"[\u4e00-\u9fff]", body_txt)),
    }


def should_skip(ch_n, bullets):
    if ch_n in DEEP_OK:
        return True, "deep_ok"
    all_b = "\n".join(bullets)
    for pat in SKIP_IF_COST_HAS:
        if re.search(pat, all_b):
            # if cost line has chapter-specific number/name, skip
            for b in bullets:
                if any(k in b for k in ["代价", "连接税", "机械臂", "风险"]):
                    if re.search(pat, b):
                        return True, f"cost_specific:{pat}"
    return False, ""


def main():
    scan = json.loads(SCAN.read_text(encoding="utf-8"))
    needs = [r for r in scan if r.get("status") == "NEEDS"]
    out = []
    skip_list = []
    for r in needs:
        p = Path(r["path"])
        text = p.read_text(encoding="utf-8", errors="replace")
        ext = extract(text)
        if not ext:
            continue
        title, body_txt, bullets, _ = ext
        sk, why = should_skip(r["n"], bullets)
        sig = body_signals(body_txt)
        entry = {
            "n": r["n"],
            "path": str(p),
            "title": title,
            "bullets": bullets,
            "skip": sk,
            "skip_why": why,
            "signals": sig,
        }
        if sk:
            skip_list.append(entry)
        else:
            out.append(entry)

    print(f"needs_total={len(needs)} to_rewrite={len(out)} skipped={len(skip_list)}")
    print("SKIPPED:")
    for e in skip_list:
        print(f"  {e['n']:03d} {e['skip_why']} | {e['bullets'][:2]}")
    print("\nTO REWRITE (with signals):")
    for e in out:
        s = e["signals"]
        print(f"\n{e['n']:03d} {e['title']}")
        print(f"  named={s['named'][:12]}")
        print(f"  nums={s['nums'][:12]}")
        print(f"  quotes={s['quotes']}")
        print(f"  open={s['opening'][:100]}")
        print(f"  end={s['ending'][:140]}")
        print(f"  cur_cost_hook={[b for b in e['bullets'] if any(k in b for k in ['代价','钩子','连接税','机械臂','城市锚点'])][:3]}")

    Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\review\_p5_rewrite_targets.json").write_text(
        json.dumps({"rewrite": out, "skip": skip_list}, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
