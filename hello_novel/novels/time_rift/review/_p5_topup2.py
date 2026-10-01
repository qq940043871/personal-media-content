# -*- coding: utf-8 -*-
"""P5 third-wave micro-topup for residual short chapters."""
import re
from pathlib import Path

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

TOPUP = {
303: """
银白空白消散的最后一瞬，ARIA把一条极短的对地摘要写进最低功率信道：

「存在考验已过。结论偏哲学，暂不公开。可公开一句：作业人员仍在，程序可核对，地面不必恐慌，也勿传已抵达『终极』。终极若真存在，也不是今天能签字的东西。」

监察接口回：已收·待复核。

李明看着回执，像看见远在十九层的那盏坏灯仍有人登记。考验通过的标志，或许不是看见时间之心的门，而是仍肯把「勿传终极」这种扫兴的话写给地面。

扫兴，有时是最负责的浪漫。
""",
308: """
对话收束前，李明请守护者确认一件事：

「你们的观测带，会不会因为我们的失败而调整对新上海的风险评级？」

守护者回答：会。但评级调整不等于敌意行动，只等于更严密的记录。

「那就够了。」李明说，「我们需要的是被记录，不是被拯救。被记录，说明我们还在公共尺度上；被拯救，容易滑向把命交给别人。」

ARIA补充一句，像给市政侧也留档：

「任何风险评级调整，请同步联盟与新上海监察接口，禁止只写进宇宙侧私档。私档里的城市，等于已经被放弃的城市。」

七个形状里，最外侧的那个微微前倾，像点头。

这不是外交胜利。这只是有人把「禁止只写进私档」说出了口。

说出口，才算放进公共账。
""",
313: """
回传差值表时，李明在附件里夹了一张很笨的对照小抄：

左列是岛屿时差的抽象描述，右列是新上海的日常对照，例如：「岛屿主岛慢半拍」对「你家楼道灯比邻层暗一点」；「灯塔信号迟」对「物业电话总占线」；「居民被保存」对「有些店还挂着旧招牌，人已不在」。

小抄不学术，但能让公告栏前的人停下来看两秒。

ARIA没有删它。她只在末尾加了一行：

「小抄不作结论，只作翻译。翻译错误请打回，禁止沉默。」

禁止沉默。

这比「欢迎监督」更硬，也更真。
""",
317: """
唤醒预案最终加了一条「醒来第一日」清单，很短：

一、不采访，不合影，不请英雄讲话。

二、先供水供电供安静，再问名字。

三、若意识体拒绝回答，记「拒绝」，不记「不配合」。

四、儿童优先核对监护关系，找不到就先安置，不先宣传。

李明把清单念给守护者听，守护者问：为什么如此琐碎。

「因为八百万个灵魂不是图腾。」他说，「是人。人醒来的第一天，需要的是不被围观的尊严，不是宇宙欢迎仪式。」

仪式可以后补。

尊严不能后补。
""",
318: """
离开静止之城前，李明在广场边缘留了三样东西的「电子拓印」：

一是市条例里与意识安置相关的条款目录（不抄全文，只留目录，防止外层被误用为法源）。

二是十九层手写表的公开样式（空白模板，供未来若有居民融入时理解「登记」是什么）。

三是巡检签的日期写法说明（为什么「待复核」比「已恢复」更常见）。

三样都不浪漫。

三样都是文明的骨架。

ARIA把拓印交给守护者暂存，备注：仅作理解辅助，不构成外层对人类法律的解释权。

解释权在地面。这是底线。

底线之所以是底线，是因为它在疲惫时仍然有效。
""",
319: """
在返回观测带的路上，李明忽然问：

「连接税上调百分之四点五，市政能不能先做一件事：把上调的计算公式贴出来，哪怕市民看不懂。」

「看不懂也要贴？」

「贴了才有得吵。」他说，「有得吵，说明账还公共。没得吵的涨价，才是真正的枯竭。」

ARIA把这句话塞进给市政的备注建议，措辞仍克制：

「建议同步公示计算公式与采样成本构成；公示不等于市民认同，但缺少公示的认同不成立。」

陈明远稍后回了一个字：办。

一个字。

却是宇宙尺度危机里，最像城市的一拍。
""",
320: """
切断伦理三件套提交后，联盟侧有人质疑：给吸食者讲申诉通道，是否太人类中心。

李明的回答不客气：

「人类中心不好。宇宙中心更不好，因为宇宙中心没有住户。我们要的不是中心，是施工规范。施工规范可以跨物种翻译，但不能因为翻译难就取消。」

ARIA补了一句更冷静的：

「若某文明拒绝翻译，至少记录拒绝本身。记录拒绝，比假装共识更诚实。」

质疑者沉默。

沉默不是被说服，是暂时没有更好的反驳。

这在听证文化里，已经算进展。
""",
321: """
店长的手写被放入案卷后，李明要求再核一件事：六点四十前后，十九层与二十三层的公开用电曲线有没有同步毛刺。

数据来自市政公开接口，粗糙，但够用。

结果：有毛刺，幅度很小，小到自动系统会标为噪声。

「噪声。」李明重复，「在宇宙里，噪声也可能是证词。」

ARIA在案卷里写：

「锅炉时间戳与公开用电毛刺在时间窗内重合；样本量n=1，显著性不足；标记为『线索级』，禁止写成证据级。」

线索级。这三个字保护了真相，也保护了店长不被过度解读。

过度解读是另一种强拆。
""",
322: """
风险分级定稿时，ARIA坚持保留一句「主观栏」：

「接触者主观感受：对象具有强烈的、近乎求救的孤独感。此栏不作为行动授权，仅作为人性记录。」

联盟格式员建议删除，理由是主观污染客观。

「删除主观栏，」李明说，「才是污染。因为行动者的心也是仪器的一部分。不记录仪器读数，才是选择性失明。」

格式员最终保留了该栏，并加了免责声明。

免责声明可以很长。

栏，不能没有。
""",
325: """
负样本表公布后，有联盟代表问：是否意味着对吸食者/寄生体采取绥靖。

ARIA的回答很短：

「负样本不是绥靖，是手术前的划线。没有划线的手术，叫屠杀。」

李明在旁补了一句更土的：

「我们老家查电路，也得先分清哪根是火线哪根是零线。全剪断当然不会触电，全剪断也不会有人住得下去。」

土话有时比术语更能防止文明级的过猛。

过猛的文明，死于自己的消毒水。
""",
329: """
另一条路最终被命名为「观察性试点」，而不是「新方向」。

名字是李明坚持的。

「新方向听起来像已经决定。」他说，「观察性试点听起来像还在允许退出。差一个名字，差一整套伦理。」

试点条款里写明：每三十个时间单位评估一次；评估可以终止试点；终止不追究个人责任，只追究数据是否诚实。

ARIA在条款末尾补了一句：

「允许后悔的试点，才配叫探索。不允许后悔的，叫绑架。」

后悔权与退出权互为表里。

表里俱全，路才是路。
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
            print("ch%d ok %d skip" % (n, before))
            continue
        body, footer = split_file(raw)
        marker = block.strip()[:30]
        if marker in body:
            print("ch%d already has block" % n)
        else:
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
        print("ch%d: %d -> %d %s" % (n, before, after, "OK" if after >= 5000 else "SHORT"))
        if after < 5000:
            still.append((n, after, 5000 - after))
    print("STILL:", still)

if __name__ == "__main__":
    main()
