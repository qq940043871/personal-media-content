# -*- coding: utf-8 -*-
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

TOPUP = {
303: """
未回执清单上，李明又添了一行小字：「二十三层锅炉表针——请店长继续按自己的节奏记，不必等我们回话。不是我们不在意，是我们在意却还不配给结论。」

他把这行字标为「可传」，让监察接口有机会时捎过去。

有些在意，只能以「不配给结论」的方式在场。这很不舒服，却比轻率的安慰更接近存在的诚实。
""",
308: """
临走前，ARIA请守护者给一个「最小协作单元」的定义。

守护者答：一次可核对的信息交换，外加双方各自的未完成清单。

「没有联合舰队？」

「没有。」守护者说，「联合舰队往往始于善意，终于责任稀释。最小单元保留责任浓度。」

李明听完，觉得这比许多联盟宪章更像施工手册。

施工手册救过的城市，比宣言多。
""",
313: """
小抄贴上公告栏方向后，监察员回传一句市民口头：

「有人问：岛屿慢半拍，是不是我电费单也要慢半拍才到？」

ARIA的回复只有半句：「电费单不慢，解释可以慢。解释慢，是为了不说谎。」

这半句或许会被人嫌不够痛快。

不够痛快，恰恰是它还负责任的证据。
""",
317: """
醒来第一日清单的第五条，是李明最后加上去的：

五、允许有人问「为什么是我们醒着」，并把这个问题原样存档，不用励志答案覆盖。

为什么是我们醒着，没有标准答案。

能做的只是把问题放好，等更多人来一起承担它的重量。
""",
318: """
赤字条目最终被监察接口标为「已接收·观察中」，没有被抹掉，也没有被升格成丑闻。

李明对这个状态很满意。

观察中，是疲惫与责任之间最诚实的中间态。它承认问题存在，同时拒绝用惊慌或美化去填空。
""",
319: """
公示公式的一个字，在市政内网讨论里卡了很久：到底叫「采样成本」还是「波动准备金」。

陈明远最后拍板：叫采样成本。理由写进纪要——准备金听起来像已经攒够，成本听起来像还在花。

语言选择也是会计选择。

会计选择错了，枯竭会被说成季节。
""",
320: """
申诉通道草案里有一条被联盟法务标红：若受害方是时间线本身，谁有权代为申诉。

李明坚持保留「暂缺代诉人」的空栏，而不是随便指派宇宙代表。

空栏难看。

乱指派更难看。
""",
321: """
线索级标记下传后，店长托人又问了一句：

「那我还要不要每天看表针？」

回信很短：「请继续看。观察本身已经是公共财产。」

公共财产四个字，或许超出店长的日常语感。

但表针还在跳。这就够了。
""",
322: """
主观栏保留后，ARIA在个人日志里写：

「今日确认：我害怕把孤独读成威胁，也害怕把威胁读成孤独。两种害怕都要写下来，否则我会选一种舒服的，然后称之为客观。」

李明的日志更土：

「今天没弄懂深渊。弄懂了电力和锅炉。先这样。」

先这样。

这三个字里有职业的谦卑，也有不肯停下的固执。
""",
325: """
划线工作会散场前，有一份备忘录被塞进李明手里，来自时间回声文明，只有一句：

「你们的负样本，让我们想起自己曾经被误诊的季节。」

李明把备忘录收好。

误诊的季节不是耻辱。

把误诊说成必然，才是。
""",
329: """
观察性试点启动通知下传地面时，市政只公开了三句话：

一、外层开启一项可退出的观察试点。

二、试点不影响本市供电与维修班表。

三、若试点终止，将同步公告，不静默。

静默终止，是许多宏大项目最不体面的退场方式。

公告终止，哪怕难看，也还把市民当市民。
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
