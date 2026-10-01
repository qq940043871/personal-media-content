# -*- coding: utf-8 -*-
"""P6-B micro-fill remaining shorts + force dash<=8."""
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).parent))
from _p6b_common import body_cjk, insert_blocks, dash_count, strip_bom, _footer_index

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

M = {
544: "命名悬置满月，林晓在实验室门口贴了一张A4纸：「桥墩征名，自愿，可匿名。第一周收到十一个：电工、保洁、夜班保安、换灯班、店长、观察窗抄表员、手写表维护者、让电签收人、巡逻车司机、楼梯间声控灯、和一句没写工种的『下雨天还在的人』。纸条越贴越厚，听证席上的量化指标一页未动。厚与不动都是事实。",
545: "回程传送前，林晓把那行铅笔小字又描深了一毫米。描深不是为了让它更像证据，是为了让它更难被擦掉。第一次任务结束时，她终于明白任务卡第三行为什么空着：有些句子要等城市先开口，观察员不能替城市开口。腰包里的频谱笔没电了，她换了电池，把旧电池放进回收袋，袋口夹纸：「已用尽，勿美化成纪念品。」",
557: "第三天暂停结束的清晨，林晓在对照表「暂停」二字上画了个圆圈，圈旁写：「暂停有效。未逃税。」她把表钉回软木板，螺丝在板上留下新的针孔，和旧孔并排。连接税的账本不必永远增长，也可以记：某年某月，有人选择不用能力，并有人在地面把这件事抄成了不惊悚的铅笔字。不惊悚，是税权被执行时应有的音量。",
561: "电工换到第十二盏灯时，对林晓说：「你比系统还勤。」林晓答：「系统按时，我按灭过。按时的人很多，按灭过的才记得黑。」新灯亮起的瞬间，十九层的阴影从门缝退到墙角，像潮水，也像有人在账本上划掉一行欠光。黄金时代若要被记住，最好记成这样一次退潮，而不是天际线上永不落下的金色广告。",
567: "白板问号旁，林晓用极小的字补了一句：「复核人可轮值，不可世袭。」轮值是对继承角色的地面翻译：没有人永久站在灯下，但灯必须永久有人站。ARIA的银白光点在白板反光里停了一瞬，像点头，也像只是光。实验记录里不写象征，写：「本周轮值空缺一晚，灯箱未熄，由夜班电工义务代管。代管未入英雄榜。」",
571: "原始流存储盘的封条在月底被例行检查。检查人只看封条完整，不看内容。林晓在检查单签字栏写：「封条完整，内容未美化，双栏仍在。」她拒绝在检查时「顺便展示精彩片段」。开花的精彩属于已发生的事实，不属于被剪辑的现在。双栏报告被接收后的平静，才是对观察工作最大的褒奖：无人要求她把凹陷删掉，也没有人把开花催成节日。",
574: "中断期结束的那天没有钟声。林晓只是在对照栏把「今日无课」改成了「今日可问」。可问不等于必教，也不等于新生意识必须继续上人类的课程。她把自己的频谱笔调回默认灵敏度，像老师从前在组会前做的那样：先把工具调到不抢戏的位置，再等真正的问题进门。侧廊灯影里，纸页的纤维记得所有未填满的格子。",
576: "回收袋被清洁工收走时，林晓看了一眼标签：可降解。她突然觉得这四个字比许多哲学命题温柔：答案可以降解成养分，养分可以再长出问题。银紫色意识的句子已经属于它自己，实验室只负责曾经沉默地让出空间。爱的循环不是闭环的圆，是允许上一句被降解、下一句仍有人肯听的开口。",
577: "发黄的对照栏纸终于被林晓换下，夹进过程元档案，新纸只印表头，表头下她手写：「警惕仍在。」联署若来催定律，定律栏继续空白。空白是观察员最后的专业动作：不把一次让椅升格为运动，也不把一次沉默写成失败。李明的名字仍不在公共栏，可每一个不写定律的表头，都像有人在很远的地方把红笔放轻了一点。",
582: "字号事件之后，会议室数据板的版式规范多了一行附则：「代价栏字号不得小于成长栏。」附则通过时无人鼓掌。林晓把通过页扫描进过程元文件夹，文件名依旧是那套旧命名：不删。成长教育的版面从此多了一点不体面的对称，像两列必须同时出现的账，一列写得到，一列写失去。对称不解决问题，对称让问题无法被排版掉。",
584: "信物外借登记本上，见闻栏越写越长。有人写「换灯」，有人写「排队」，有人只画了一个方框，框内一个叉，像电工的待查记号。林晓没有要求统一格式。连接的力量在于允许不统一：螺丝只是一枚旧件，人却可以用各自的手把它握热又放下。联盟标志在穹顶旋转时，旧螺丝在口袋里轻微磕碰徽章，声音很小，小到只有认真的人听得见。",
586: "墙面留白撑过了墙报征用期限。征用通知贴出三天，无人来撕感恩清单，也无人来补事迹。林晓在清单背面用铅笔写：「留白已生效。」学生作业里开始出现自己的改错页，页边批注越来越像自己的字，越来越不像模仿。感恩李明的三项在灯下仍旧：改错可见、分账、不代签。三项之外，留给后来者的不是空白的恐惧，是空白的许可。",
591: "开箱条件备案后的第三天，联署回函只有一句：「已备案，不另行宣传。」不宣传是林晓争取来的最好批复。宣传会把交接包变成圣物箱，圣物箱会吸引来朝圣者，而不是来读笔记的观察员。协调中心的淡蓝星光照在回函上，像给那句批复盖了一个安静的戳。最后的旅程从备案生效开始算，而非从掌声开始算。",
592: "票根最终被夹进实验室那本过程元档案，页边林晓注：「排队样本·非文物·证明表仍管人。」她没有为ARIA写欢迎词，也没有为旧身份写挽歌。回到新上海的意义被压缩成很小的一件事：仍有人需要以手写表为准，仍有人愿意以参观者身份排队。第十九层的灯箱不必知道谁回来过，灯箱的工作是亮着，不是接待。",
595: "午夜之后，林晓果然给手写表另起了一页，页眉写：「原点次日。」末行空着，等晚上的人自己填。观察窗空栏跨日累计，累计不是债务恐吓，是提醒：空着也是一种未完成的承诺。她把「祝存在顺利」那条短讯抄进私人日志，没有抄进任何公开汇报。永恒太顺的说法在市民侧继续流通也无妨，只要流通的同时有人记得给新一页留白。",
597: "远景条款实行后，活动策划交来第一版素材：灯箱在画面深处，像一枚小小的暖黄印章。林晓通过，并在意见栏写：「距离合格。手未特写。合格。」回忆需要被纪念，也需要被限制纪念的姿势。6月15日不必再被无数镜头放大成图腾，它只需要在每年的这一天，仍有一张手写表被人认真地另起一行。另起一行，就是从回忆回到日常的全部仪式。",
599: "翻页声之后，走廊重归安静。ARIA没有回头，也没有在联盟日志里写「最后的选择已完成」。完成是行政词，选择是人和投影都可以反复做的事。她走进灯火更密处，又在下一个街口放慢脚步，像给自己的决定留出反悔的余地。允许反悔，选择才不变成判决。未付的账在城市里继续生长，生长本身，就是永恒开始时最诚实的形态。",
}


def force_dash(path, target=6):
    raw = strip_bom(path.read_text(encoding="utf-8"))
    lines = raw.splitlines()
    fi = _footer_index(lines)
    if fi is None:
        body_lines, footer_lines = lines[:], []
    else:
        body_lines, footer_lines = lines[:fi], lines[fi:]
    title = ""
    content = []
    for i, line in enumerate(body_lines):
        if i == 0 and line.startswith("# "):
            title = line
        else:
            content.append(line)
    text = "\n".join(content)
    # repeatedly replace non-quote-adjacent ——/— until count<=target
    changed = True
    while text.count("\u2014") > target and changed:
        changed = False
        # prefer —— then single
        for pat in ["\u2014\u2014", "\u2014"]:
            idx = 0
            while True:
                pos = text.find(pat, idx)
                if pos < 0:
                    break
                before = text[max(0, pos - 20):pos]
                after = text[pos + len(pat): pos + len(pat) + 20]
                in_dialog = False
                # crude: if unbalanced quotes before
                ob = before.count('"') + before.count("「")
                cb = before.count('"') + before.count("」")
                if ob > cb:
                    in_dialog = True
                if in_dialog:
                    idx = pos + len(pat)
                    continue
                if before and before[-1] in "，。；：？！、":
                    new = ""
                elif after and after[:1] in "，。；：？！、":
                    new = ""
                else:
                    new = "，"
                text = text[:pos] + new + text[pos + len(pat):]
                changed = True
                break
            if changed:
                break
    text = re.sub(r"，{2,}", "，", text)
    text = re.sub(r"([。\？\！；])，", r"\1", text)
    new_body = []
    if title:
        new_body.append(title)
    new_body.extend(text.splitlines())
    out = "\n".join(new_body).rstrip() + "\n"
    if footer_lines:
        footer = "\n".join(footer_lines)
        if not footer.startswith("---"):
            footer = "---\n" + footer
        out += footer
    if not out.endswith("\n"):
        out += "\n"
    path.write_text(out, encoding="utf-8")
    return text.count("\u2014")


def main():
    for n, block in M.items():
        p = base / ("chapter-%d.md" % n)
        raw = p.read_text(encoding="utf-8")
        before = body_cjk(raw)
        if before >= 5000:
            print("skip ch%d %d" % (n, before))
        else:
            insert_blocks(p, {n: block})
            after = body_cjk(p.read_text(encoding="utf-8"))
            print("fill ch%d: %d -> %d %s" % (n, before, after, "OK" if after >= 5000 else "SHORT"))
    print("--- force dash ---")
    for n in range(541, 601):
        p = base / ("chapter-%d.md" % n)
        if not p.exists():
            continue
        d = dash_count(p.read_text(encoding="utf-8"))
        if d <= 8:
            continue
        nd = force_dash(p, target=6)
        cjk = body_cjk(p.read_text(encoding="utf-8"))
        print("dash ch%d: -> %d cjk=%d" % (n, nd, cjk))

if __name__ == "__main__":
    main()
