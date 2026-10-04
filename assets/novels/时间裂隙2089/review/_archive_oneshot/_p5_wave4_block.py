# -*- coding: utf-8 -*-
"""P5 wave4: one more dialogue block per named priority + residual secondary."""
from __future__ import annotations

import re
from pathlib import Path

CH_DIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

BLOCK = """
---

第47区观察窗前，李明和ARIA把公开稿的三栏又过了一遍。

「变化栏。」李明说。

「结构观测中，未命名完成。」ARIA答。

「对照栏。」

「19层电梯：无新异常。23层：店长登记『拉花歪了』已入表，未获签复。47层：老何『窗稳，雾纹断口加一，不写已恢复』。」

「签字人栏。」

ARIA沉默了一下。「暂空。七日内由监察署值班官代签并公示。」

「好。」李明用机械臂在窗台的雾气上画了一道短短的横线，「这道线算宽度记录。谁签字说和谐/觉醒/传播/爱已经落地，谁就得先解释这道线为什么还在。」

老何从值班室探出头。「你们在我窗上画什么？」

「宽度。」李明说。

「宽度用尺量，不用臂画。」老何把日志本递过来，「写上：李明到访，窗缘手绘横线一道，不作正式读数。正式读数明日日班补。」

「要不要我签名？」

「要。」老何说，「签名栏在这。空着的账不是账，是涂鸦。」

李明签了名。ARIA把这一页同步进失败账正文，备注：宇宙侧结论暂不升格，以地面三节点宽度为准。

---
"""


def footer_add() -> str:
    return (
        "\n- 施工补记（P5）：公开稿三栏再核——变化/对照/签字人；签字人栏七日内监察值班官代签并公示；"
        "47区窗缘手绘横线不作正式读数，正式读数日班补；店长/老何/周晚晴日常回执继续\n"
    )


def main() -> None:
    targets = [
        168, 142, 125, 225, 244, 217, 167, 147, 159, 226, 127, 238, 203, 231, 208,
        175, 253, 259, 248, 254, 141, 149, 174,
    ]
    for ch in targets:
        p = CH_DIR / f"chapter-{ch:03d}.md"
        if not p.exists():
            print(f"MISSING {ch}")
            continue
        text = p.read_text(encoding="utf-8")
        if "窗台的雾气上画了一道短短的横线" in text:
            print(f"SKIP {ch}")
            continue
        m = re.search(r"\n---\s*\n\*\*本章关键点", text)
        if m:
            text = text[: m.start()] + BLOCK + text[m.start() :]
        else:
            text = text.rstrip() + "\n" + BLOCK
        if "施工补记（P5）" not in text:
            m2 = re.search(r"\n---\s*\n\*\*本章关键点[\s\S]*$", text)
            if m2:
                text = text[: m2.end()] + footer_add() + "\n"
        p.write_text(text, encoding="utf-8")
        print(f"OK {ch}")


if __name__ == "__main__":
    main()
