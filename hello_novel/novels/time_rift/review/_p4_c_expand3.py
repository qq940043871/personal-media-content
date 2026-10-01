# -*- coding: utf-8 -*-
"""P4 C类 · 未达5000章节补量"""
import re
from pathlib import Path

ROOT = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
FOOTER_RE = re.compile(r"\n---\s*\n\*\*本章关键点[：:]\*\*", re.M)
TITLE_RE = re.compile(r"^#[^\n]*\n")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def sc(text: str) -> int:
    m = FOOTER_RE.search(text)
    hb = text[: m.start()] if m else text
    tm = TITLE_RE.match(hb)
    title = tm.group(0) if tm else ""
    body = hb[len(title) :]
    measure = re.sub(r"^(?:---\s*\n)?(?:>.*\n)+", "", body)
    measure = re.sub(r"^---\s*\n", "", measure)
    return len(CJK_RE.findall(measure))


B = {
    82: """
---

## 补场：承诺书与检修公告

市场管理处把李明与 ARIA 的公开承诺抄进公告栏，标题不叫誓言，叫《使用前须知》。

须知最后一行：

> 说不清对谁负责的动作，先别做。

有人把须知撕了一角。

第二天管理处重贴，不追查撕纸的人，只加一句：

> 撕了可以再贴。程序不怕撕，怕没人贴。

李明在泵站教工人看检修公告三件套：时刻、编号、负责人。

三条齐，先按检修理解。

三条缺，再怀疑。

怀疑分级，比一律相信或一律不信，更接近成年人的信息生活。

当晚电压曲线平稳。

语法伤没有发作。

不是能力突然变温柔，是城市多了一次点名机会。

点名簿很短。

短簿比长诗更会保护夜班的人。
""",
    102: """
---

## 补场：投票日后的小巷灯

三读通过后的第一个周末，第五区样板街又补了一盏灯。

不是剪彩灯，是小巷转角那盏。

电工拧最后一圈螺丝时，有个放学的孩子站在旁边看。

孩子问：「这是条例点的灯吗？」

「是很多人点的灯。」电工说，「条例只是把名单写清楚。」

孩子把「名单」两个字抄在手心。

母亲来接人，看见手心的字，没有升华。

她说：回家吃饭，名单也要吃饱。

李明把这一幕记进条例执行观察：

> 尊严条款禁止施舍表演。
> 灯亮是权利兑现，不是恩情直播。

上层选区仍有人批评优先底层是收买。

ARIA 的公开答复不热：

> 收买是给人好处换忠诚。
> 条例是把已付的税变回可验收的服务。
> 忠诚不在验收表里。
> 电压在。

中层商会合同执行第二周，夜间最低安全照明全部到位。

商户投诉从「被绑架」转成「补贴什么时候到」。

投诉转向，说明争论落到账期。

账期比立场更难被传单改写。

炸弹威胁仍在案卷里。

恐袭定性与编制预算写在同一条款下。

条款很干。

干条款能在雨夜给巡逻队发加班费。

加班费到账时，第七区不开灯路段从峰值 5 条降到 2 条。

数字不说和平。

数字说：有人还在班上。
""",
    108: """
---

## 补场：120块到账后的夜班

加班费补发到账那晚，值班员把银行短信截给同事看。

同事说：「这下你该感动了吧。」

值班员说：「我先把下个月排班表看完。」

感动不是目的。

目的是排班不再乱、复核不再空、下次少算的 120 不会再出现。

市政人事把「目的问题」工作坊产出贴在招工信息栏旁边。

两栏并排：

左边是求职与防诈骗清单。

右边是培训与投诉渠道。

中间有一行小字：

> 不知道时间的目的，也可以知道这月工资该发多少。
> 算得清工资的人，才谈得上选择未来。

失业青年有人仍交白卷。

白卷被允许存在。

不允许存在的是：白卷被当成青年自己的错。

ARIA 在市政端确认：该巷路灯列入下一检修批次，编号公开。

学生作文变成编号时，教室里没有人鼓掌。

教师只说：很好，下一位。

目的哲学在课堂上是提问，在市政端是编号。

提问与编号都是教育。

教育的终点不是让人爱上大词。

教育的终点是让人敢在会上问：这一条，谁签字。
""",
    109: """
---

## 补场：隐私拒绝之后的市场清晨

拒绝交出失败样本的第二天，第四区市场没有变得更哲学。

广播员照旧念三问。

老陈照旧进货。

卖蛋白的大姐把三问卡片擦了一遍，说：

「副市长不肯把别人的难看事交出去，我赞成。难看事可以自己消化，不能拿去展览。」

李明在旁边补：「展览多了，下次谁还敢求助。」

求助热线接线员培训同步更新：

> 接线不评判隐私。
> 记录最小必要信息。
> 涉及自伤伤人风险，优先人身安全。
> 禁止把通话内容做成宣传素材。

意识完整度反武器化生效后，保险公司投诉过一次「无法核保」。

答复很硬：

> 风险核保可以使用依法可得的精算数据。
> 禁止把市民的意识损伤曲线当自动拒赔开关。
> 开关若存在，就是歧视，不是精算。

李明的医疗单与维修单放在同一个文件夹。

他说：都是维护人类这台还会疼的机器。

ARIA 的负载管理不公开精确曲线，只公开：

> 已轮班。
> 未把痛苦当抵押品。
> 城市不要求英雄永不崩溃。

市场清晨的光很普通。

普通光里，隐私仍被当成权利。

权利不保证不受伤。

权利保证受伤时，不必先把自己变成展品才能被接住。

接住人的，先是电话与社工，其次才是任何关于连接的哲学。

哲学排队。

电话优先。
""",
}


def apply_block(n: int, block: str) -> tuple[int, int]:
    p = ROOT / f"chapter-{n:03d}.md"
    t = p.read_text(encoding="utf-8-sig")
    before = sc(t)
    fp = None
    for line in block.splitlines():
        s = line.strip()
        if s.startswith("## ") and len(s) >= 5:
            fp = s
            break
    if fp and fp in t:
        return before, before
    m = FOOTER_RE.search(t)
    if not m:
        t = t.rstrip() + "\n" + block + "\n\n---\n**本章关键点：**\n"
        p.write_text(t, encoding="utf-8")
        return before, sc(p.read_text(encoding="utf-8-sig"))
    t = t[: m.start()] + block + t[m.start() :]
    p.write_text(t, encoding="utf-8")
    return before, sc(p.read_text(encoding="utf-8-sig"))


def main() -> None:
    for n, block in B.items():
        a, b = apply_block(n, block)
        print(f"{n:03d} {a}->{b}")
    print("=== FULL SCAN 61-120 CJK<5000 ===")
    shorts = []
    for n in range(61, 121):
        p = ROOT / f"chapter-{n:03d}.md"
        if not p.exists():
            shorts.append((n, -1, -1))
            continue
        t = p.read_text(encoding="utf-8-sig")
        cjk = sc(t)
        dash = t.count("——")
        hasf = bool(FOOTER_RE.search(t))
        if cjk < 5000 or dash > 8 or not hasf:
            shorts.append((n, cjk, dash, hasf))
    for x in shorts:
        print(x)
    print("count", len(shorts))
    # forbidden template check
    bad_pat = re.compile(r"本章后续执行按|对地镜像|数字台账")
    for n in range(61, 121):
        t = (ROOT / f"chapter-{n:03d}.md").read_text(encoding="utf-8-sig")
        if bad_pat.search(t):
            print("FORBIDDEN", n)
    # pure blue current-state heuristic in focus
    for n in (61, 71, 83, 84, 89, 96, 105, 107, 109, 110, 112, 120):
        t = (ROOT / f"chapter-{n:03d}.md").read_text(encoding="utf-8-sig")
        if re.search(r"瞳孔[^。\n]{0,20}蓝色数据流", t) and "银" not in t and "紫" not in t:
            print("POSSIBLE_BLUE", n)


if __name__ == "__main__":
    main()
