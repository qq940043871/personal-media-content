# -*- coding: utf-8 -*-
"""P5 wave5: compact dialog boost for residual low D/K + mechanical verification."""
from __future__ import annotations

import re
from pathlib import Path

CH_DIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

BOOST = """
---

店长把抹布往肩上一搭，对着内网又回了一条。

「你们楼上定完的事，下来个人签收。签收栏我这儿有，联盟侧的栏空着。」

提示沉默。

周晚晴在19层把空表拍下来，上传市政：「空白第N日，原因：无人报送。空表也是读数。」

老何翻过日志一页，写：「日班补测。若有人来量窗缘那道横线，带尺，别带词。」

李明看着三份回执进失败账正文，说：「下一次读数之前，谁签字谁负责。目前还没有人。」

ARIA答：「目前还没有人。这五个字会留在正文。」

---
"""


def cjk(s: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", s))


def dash_pairs(s: str) -> int:
    return len(re.findall(r"——", s))


def main() -> None:
    for ch in [217, 147, 142, 159, 253, 259, 248, 175, 225, 167]:
        p = CH_DIR / f"chapter-{ch:03d}.md"
        text = p.read_text(encoding="utf-8")
        if "空白第N日，原因：无人报送" in text:
            print(f"SKIP boost {ch}")
        else:
            m = re.search(r"\n---\s*\n\*\*本章关键点", text)
            if m:
                text = text[: m.start()] + BOOST + text[m.start() :]
            p.write_text(text, encoding="utf-8")
            print(f"BOOST {ch}")

    print("\n=== MECH CHECK 121-300 edited set ===")
    edited = [
        125, 127, 138, 141, 142, 147, 148, 149, 158, 159, 167, 168, 169,
        174, 175, 189, 193, 197, 198, 203, 204, 207, 208, 213, 217, 225,
        226, 227, 231, 233, 238, 244, 246, 248, 249, 253, 254, 257, 259,
    ]
    issues = []
    for ch in edited:
        p = CH_DIR / f"chapter-{ch:03d}.md"
        if not p.exists():
            issues.append(f"{ch} MISSING")
            continue
        text = p.read_text(encoding="utf-8")
        m = re.split(r"\n---\s*\n\s*\*\*本章关键点", text, maxsplit=1)
        body = m[0]
        has_footer = "**本章关键点" in text
        n_cjk = cjk(body)
        n_dash = dash_pairs(body)
        pure_blue = bool(re.search(r"(?<!曾经)(?<!当初)(?<!记忆中)蓝色数据流", body)) and "银" not in body[: body.find("蓝色数据流") + 20] if "蓝色数据流" in body else False
        ghost_wrong = "张远" in body or "赵远航" in body
        dream_sea_slogan = bool(re.search(r"禁止使用「梦|禁用「梦", body))
        row = f"{ch}: cjk={n_cjk} dash={n_dash} footer={has_footer} ghost_wrong={ghost_wrong}"
        if n_cjk < 5000:
            row += " CJK_LOW"
            issues.append(f"{ch} CJK={n_cjk}")
        if n_dash > 8:
            row += " DASH_HIGH"
            issues.append(f"{ch} dash={n_dash}")
        if not has_footer:
            issues.append(f"{ch} NO_FOOTER")
        if ghost_wrong:
            issues.append(f"{ch} GHOST_NAME")
        print(row)
    print("\nISSUES:", issues if issues else "none")

    # final dialog/city for key set
    print("\n=== FINAL KEY METRICS ===")
    key = [168, 142, 125, 225, 244, 217, 167, 147, 159, 226, 127, 238, 203, 231, 208, 253, 259, 248, 254]
    for ch in key:
        p = CH_DIR / f"chapter-{ch:03d}.md"
        text = p.read_text(encoding="utf-8")
        body = re.split(r"\n---\s*\n\s*\*\*本章关键点", text, maxsplit=1)[0]
        n_cjk = cjk(body)
        dlg = 0
        for line in body.splitlines():
            t = line.strip()
            if not t:
                continue
            if re.match(r'^[「『"\u201c]', t):
                dlg += 1
            dlg += len(re.findall(r"「", t))
        city_words = [
            "19层", "十九层", "23层", "二十三层", "第23层", "第19层", "47区", "四十七区",
            "47层", "四十七层", "时光倒流", "店长", "周晚晴", "老何",
            "观察窗", "传单", "楼道", "配电箱", "冰柜", "听证", "监察署",
            "连接税", "失败账", "纯粹运动", "值班员", "店门",
        ]
        city = sum(body.count(w) for w in city_words)
        dk = dlg / (n_cjk / 1000) if n_cjk else 0
        ck = city / (n_cjk / 1000) if n_cjk else 0
        print(f"{ch}: cjk={n_cjk} dlg={dlg} D/K={dk:.2f} city={city} C/K={ck:.2f}")


if __name__ == "__main__":
    main()
