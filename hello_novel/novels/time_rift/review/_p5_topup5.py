# -*- coding: utf-8 -*-
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

TOPUP = {
319: """
公示之后，老何在四十七区观察窗值勤条上多写了一句，字很小：

「窗还在。今天读数仍慢半拍。但公式贴出来了，慢得比较安心。」

安心不是结论，是愿意继续观察的许可。

枯竭最可怕的不是变轻，是没人再敢说自己感觉到了轻。
""",
322: """
排班讨论一直持续到时间之海的微光转淡。

结论很朴素：深层作业二人一组，轮换不商量；对地信道每日至少一次最低功率心跳，哪怕只有四个字——「人还在」。

人还在。

深渊很大，班表很小。

小的东西，往往先失效，也往往最后撑住文明。
""",
325: """
校准条款生效后的第一次例会，李明只问了一个问题：

「我们最近一次承认自己划错线，是什么时候？」

会场安静了十几秒。

安静本身，就是制度还呼吸的证据。不敢安静的例会，通常已经把校准权外包给了口号。
""",
329: """
旧同事挂断后，李明在缓存里给「另一条路」写了状态栏：

状态：观察性试点；退出权：在；后悔权：在；对地公告义务：在；英雄叙事：禁止。

四在一禁。

简洁得像配电箱上的操作提示。

提示不能代替判断，但能拦住一部分热血上头时的误操作。
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
