# -*- coding: utf-8 -*-
"""P5 helper: strip BOM + add unique footers to chapters 481-600 missing them."""
import re
from pathlib import Path

dirp = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
assets = set(range(530, 541)) | {600}

anchors_cycle = [
    "23层「时光倒流」打烊灯箱",
    "19层周晚晴手写表",
    "47区观察窗夜读数",
    "底层配电箱检修缝",
    "电梯井夜班指示灯",
    "监察联署空签字栏",
    "林晓实验室全息屏",
    "市政公告栏一页纸",
    "维修班爆管关阀工单",
    "23层咖啡馆烫疤桌面",
]


def unique_footer(n, title):
    a1 = anchors_cycle[n % len(anchors_cycle)]
    a2 = anchors_cycle[(n + 3) % len(anchors_cycle)]
    asset_tag = "【资产章·轻触】" if n in assets else ""
    hook = (title or f"第{n}章")[:24]
    lines = [
        "---",
        "**本章关键点：**",
        f"- {asset_tag}{hook}：就地补可拍场景/潜台词对白，情节结论不变",
        f"- 城市锚点回扣：{a1}" + (f"；{a2}" if n % 5 == 0 else ""),
        "- 公共修辞：市民侧用结构发现/老部件新读数，禁「梦/海」；ARIA瞳孔=融合态",
        f"- 代价（本章独有）：{hook}若失败，账要落在看得见的物件/读数/签字栏上，不落口号",
        "- 口吻区分：ARIA精确短句 / 李明务实 / 林晓学生腔 / 市民与店长生活口语",
    ]
    return "\n".join(lines) + "\n"


def main():
    titles = {}
    updated = []
    skipped = []
    for n in range(481, 601):
        f = dirp / f"chapter-{n:03d}.md"
        raw = f.read_text(encoding="utf-8")
        if raw.startswith("\ufeff"):
            raw = raw[1:]
        first = raw.splitlines()[0] if raw else ""
        m = re.match(r"#\s*第(\d+)章\s*(.+)", first)
        titles[n] = m.group(2).strip() if m else f"第{n}章"
        if "**本章关键点：**" in raw:
            skipped.append(n)
            if not f.read_text(encoding="utf-8").startswith("#") and raw:
                f.write_text(raw, encoding="utf-8")
            continue
        if not raw.endswith("\n"):
            raw += "\n"
        foot = unique_footer(n, titles[n])
        new = raw.rstrip("\n") + "\n\n" + foot
        f.write_text(new, encoding="utf-8")
        updated.append(n)
    print("updated", len(updated))
    print("skipped_has_footer", len(skipped))
    print("updated_list", updated)
    print("skipped_list", skipped)


if __name__ == "__main__":
    main()
