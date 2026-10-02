# -*- coding: utf-8 -*-
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

TOPUP = {
313: """
差值表回传后的当晚，李明在缓存里给主岛写了一行私人备注：「你慢半拍。地面也常慢半拍。慢，不自动等于错；但慢必须可解释。不可解释的慢，才是事故前兆。」

他没有把私人备注提交接口。

有些话只适合先跟自己对质，对质完，再决定要不要变成公共条文。
""",
317: """
清单第五条存档后，ARIA在日志补记：「允许提问，不等于必须立刻回答。回答的义务与被提问的权利同时存在，缺一，对话就会变成审讯或布道。」

李明只在边上画了一个很小的电路符号，表示「回路仍在，未短路」。

符号比宣言省墨，却不一定省责任。
""",
318: """
观察中状态生效后，监察员私下问李明：要不要把赤字条目包装成「外层奋斗证明」以利舆论。

李明拒绝了。

「奋斗证明会让赤字变荣誉。」他说，「荣誉一旦可消费，就没人愿意真正结清。」

账的尊严在于它保持账的样子，不急着变成勋章。
""",
319: """
采样成本公示生效后的第三日，十九层手写表旁多了一行圆珠笔：

「今天灯还闪，但我知道为什么闪了。知道了，就还能再等一天。」

周晚晴把这行拍下，托监察接口转给外层。

ARIA收下后没有回复恭喜，只回了四个字：「继续登记。」

继续登记，是枯竭年代里最朴素的抵抗。
""",
320: """
空栏保留决议通过后，联盟法务附了一段短释：「空栏不是漏洞，是主权未确认状态的诚实展示。」

李明把这段短释抄给市政侧参考。

市政回信仍很短：「收到。空栏比乱填体面。」

体面，在工程语言里，有时就是「不制造二次事故」。
""",
322: """
日志写完那一夜，李明在时间之海边缘站了很久，像在老家阳台听雨。

他没再问深渊是什么。他问的是：明天的班，谁上。

深渊也许永远问不完。

班表必须明天就开始排。
""",
325: """
备忘录收好之后，李明在负样本表空白处补了一句给未来审阅者：

「若你发现我们划错了线，请划回来。划回来不算失败，算校准。」

校准二字，是科学，也是伦理。

把校准机会写进制度，制度才呼吸得动。
""",
329: """
试点公告发出后，有旧同事打趣李明：你们现在连「后悔」都要写进条款。

李明答：「不写后悔的条款，往往最需要后悔。」

旧同事在那头笑骂了一句，挂断。

笑声留在信道杂讯里，像一种遥远的接地。
""",
}

def split_file(raw):
    if raw.startswith("\ufeff"):
        raw = raw[1:]
    lines = raw.splitlines()
    footer_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^---\s*$", line):
            after = "\n".join(lines[i + 1 :])
            if "本章关键点" in after or "本章围绕" in after:
                footer_idx = i
    if footer_idx is None:
        return raw.rstrip() + "\n", ""
    return "\n".join(lines[:footer_idx]).rstrip() + "\n", "\n".join(lines[footer_idx:])

def body_cjk(text):
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines()
    footer_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^---\s*$", line):
            after = "\n".join(lines[i + 1 :])
            if "本章关键点" in after or "本章围绕" in after:
                footer_idx = i
    body_lines = []
    for i, line in enumerate(lines):
        if footer_idx is not None and i >= footer_idx:
            break
        if i == 0 and line.startswith("# "):
            continue
        body_lines.append(line)
    return len(re.findall(r"[\u4e00-\u9fff]", "\n".join(body_lines)))

def main():
    still = []
    for n, block in sorted(TOPUP.items()):
        p = base / ("chapter-%d.md" % n)
        raw = p.read_text(encoding="utf-8")
        before = body_cjk(raw)
        if before >= 5000:
            print("ch%d %d skip" % (n, before))
            continue
        body, footer = split_file(raw)
        marker = block.strip()[:25]
        if marker not in body:
            body = body.rstrip() + "\n\n" + block.strip() + "\n\n"
            out = body
            if footer:
                if not out.endswith("\n"):
                    out += "\n"
                out += footer if footer.startswith("---") else "---\n" + footer
            if not out.endswith("\n"):
                out += "\n"
            p.write_text(out, encoding="utf-8")
        after = body_cjk(p.read_text(encoding="utf-8"))
        print("ch%d: %d -> %d %s" % (n, before, after, "OK" if after >= 5000 else "SHORT+%d" % (5000 - after)))
        if after < 5000:
            still.append((n, after))
    print("STILL:", still)

if __name__ == "__main__":
    main()
