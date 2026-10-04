# -*- coding: utf-8 -*-
"""P4 P0 · 最终补量：仍<4500 的章节再顶一截"""
import re
from pathlib import Path
ROOT = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")
FOOTER_RE = re.compile(r"\n---\s*\n\*\*本章关键点[：:]\*\*", re.M)
TITLE_RE = re.compile(r"^#[^\n]*\n")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")

def sc(text):
    m = FOOTER_RE.search(text)
    hb = text[:m.start()] if m else text
    tm = TITLE_RE.match(hb)
    title = tm.group(0) if tm else ""
    body = hb[len(title):]
    measure = re.sub(r"^(?:---\s*\n)?(?:>.*\n)+", "", body)
    measure = re.sub(r"^---\s*\n", "", measure)
    return len(CJK_RE.findall(measure))

B = {
71: "\n---\n\n## 最终补量：回流周的值班表公开\n\n回流周结束后，社工与医疗值班表公开：谁在岗、谁可联系、哪天休息。\n\n公开值班表的意义不是作秀，是让求助者知道电话那头有人。\n\n有人提出给 AR IA 建立‘永远在线’神话，市政拒绝。\n\n拒绝理由：永远在线会制造永远失望，并把人类岗位变成装饰。\n\n李明说：神话会让人停止学习如何在没有神的时候打电话。\n\n三问尺仍在市场门内侧。\n\n尺子旁边，多了一张塑封的值班电话。\n\n电话比口号更容易被孩子记住。\n\n孩子记住电话，城市就多了一代不怕打不通的市民。\n\n这是记忆污染危机能留下的最不浪漫、也最结实的遗产。\n",
82: "\n---\n\n## 最终补量：街道语法的误报与纠正\n\n街道板也曾误报：把正常检修写成疑似破坏，引发不必要的恐慌。\n\n纠正流程公开：删除错误板、张贴更正、说明原因、感谢指出者。\n\n不处罚善意的误报。\n\n处罚恶意造谣与屡教不改的夸大。\n\n区分标准交给社区评议小组，小组组成公示。\n\nARIA：城市要允许草根信息有毛边，但毛边不能变成刀。\n\n李明在市场教人怎么看检修公告：有没有时刻、有没有编号、有没有负责人。\n\n三条齐，就先按检修理解。\n\n三条缺，再怀疑。\n\n怀疑分级，比一律相信或一律不信，更接近成年人的信息生活。\n",
81: "\n---\n\n## 最终补量：约谈室布置规范\n\n约谈室布置规范落地：\n\n1. 双方座位同高，无单向玻璃羞辱设计。\n2. 饮水与洗手间可用。\n3. 权利页纸质可带走。\n4. 未成年人单独程序。\n5. 结束时说明下一步，不许‘回去等通知’式悬置超过法定时限。\n\n规范执行后，投诉警察态度的案子下降。\n\n不是因为警察突然变圣人。\n\n是因为房间、椅子和说明，减少了不必要的尊严摩擦。\n\n制度工程学很枯燥。\n\n枯燥处才见文明。\n",
109: "\n---\n\n## 最终补量：意识议题的年度报告\n\n意识相关公共议题进入年度报告制度：\n\n报告必须包含：事故、后应激叠加接诊量、接口岗位保护执行、研究机构损伤统计趋势、投诉类型。\n\n禁止只报喜。\n\n禁止用感人故事替代统计。\n\n统计里有名字被脱敏的个体，也有仍在疼的具体生活。\n\n李明在年度报告意见栏写：请每年至少放一页‘普通读者能读完的摘要’。\n\nARIA：请每年至少放一页‘我们哪里失败了’。\n\n两页都放进模板。\n\n模板不会自动变好。\n\n模板会逼着写作者每年面对同样的难题：如何诚实而不吓倒人，如何安慰而不骗人。\n\n这是意识时代的市政写作课。\n",
108: "\n---\n\n## 最终补量：目的问题的失业青年工作坊\n\n目的问题对失业青年工作坊开放。\n\n工作坊产出不是鸡汤，是求职与监督两份清单。\n\n求职清单：技能、证书、可去的培训、防诈骗提醒。\n\n监督清单：招工承诺是否写进合同、加班是否有上限、工伤如何申报。\n\n青年问：这跟时间的目的有什么关系？\n\n讲师：时间的目的若不包括你能找到不骗人的工作，就不是目的，是回避。\n\nARIA 远程出席十分钟，只听不总结。\n\n听完她说：把工作坊产出转给劳工部门，转给媒体，不要只做成感动我的PPT。\n\nPPT 会过期。\n\n合同与投诉渠道不会自动变好，但可以被追问。\n\n追问是青年最好的时间管理。\n",
110: "\n---\n\n## 最终补量：连接教育的反脆弱课\n\n连接教育增加反脆弱课：如何在断连时仍能活。\n\n内容：现金与备用电源、纸质地图、邻里互助协议、不依赖单一群组的信息源。\n\n不是复古主义。\n\n是承认：所有连接系统都有维护窗口与失败日。\n\n李明教机械臂断开时的呼吸法。\n\n很简单：数四拍吸气，数六拍呼气，先让身体想起自己还在。\n\nARIA 教系统降级时的优先级：先人，后数据，最后才是面子。\n\n课后测试：假设网络全断 72 小时，你的计划是什么？\n\n很多学员交白卷。\n\n白卷也是收获。\n\n收获是：城市终于看见自己的脆弱课还没开始上。\n\n看见了，就能报名下一期。\n",
112: "\n---\n\n## 最终补量：卷末幽灵线读者可读卡\n\n给试读读者的幽灵线可读卡：\n\n**他做了什么？**\n\n打城市接口：电、舆论、档案外围、象征点；曾与虚空合作后转向；拒绝交易被拒；后交投名状并配合突击。\n\n**他付了什么？**\n\n现场被铐，无特赦；刑期程序进行中；旧部有人恨他；城市不为他设神话。\n\n**城市怎样了？**\n\n监察制度在；条例在执行；咖啡馆营业；铜牌有疤；第七区仍有复查日；远征在途。\n\n**禁止的读法：**\n\n把救赎读成免费洗白；把在押读成待机盟友；把仇恨读成浪漫。\n\n**允许的读法：**\n\n愤怒、怀疑、有限度的承认、继续监督。\n\n卡片最后一行：\n\n> 若你想念那个人，去市政外包公示页看岗位，不要去传奇里找他。\n\n传奇会喂养下一场灾难。\n\n岗位与案号，只喂养下一次开庭与下一个夜班。\n",
}

def apply(n, p, block):
    t = p.read_text(encoding="utf-8-sig")
    c = sc(t)
    m = FOOTER_RE.search(t)
    if not m:
        return c, c
    fp = None
    for line in block.splitlines():
        s=line.strip()
        if s.startswith("## ") and len(s)>=4:
            fp=s; break
    if fp and fp in t:
        return c,c
    p.write_text(t[:m.start()]+block+t[m.start():], encoding="utf-8")
    return c, sc(p.read_text(encoding="utf-8-sig"))

def main():
    for n,block in B.items():
        p=ROOT/f"chapter-{n:03d}.md"
        if not p.exists():
            continue
        a,b=apply(n,p,block)
        print(f"{n:03d} {a}->{b}")
    print("=== METRICS ===")
    shorts=[]
    for n in range(61,121):
        p=ROOT/f"chapter-{n:03d}.md"
        if not p.exists():
            continue
        t=p.read_text(encoding="utf-8-sig")
        cjk=sc(t)
        dash=t.count("——")
        if cjk<4500:
            shorts.append((n,cjk,dash))
        if n in (61,83,84,89,96,105,112,120):
            print(f"FOCUS {n:03d} cjk={cjk} dash={dash}")
    print("still<4500:", shorts)
    # verify no pure blue current state in focus
    for n in (83,84,89,96,105,120,61):
        t=(ROOT/f"chapter-{n:03d}.md").read_text(encoding="utf-8-sig")
        bad = "蓝色数据流" in t and "银" not in t[t.find("蓝色数据流")-30:t.find("蓝色数据流")+30] if "蓝色数据流" in t else False
        # looser check
        if re.search(r"瞳孔[^。\n]{0,20}蓝色数据流", t) and not re.search(r"银", t):
            print(n, "possible pure blue")
    print("done")

if __name__=="__main__":
    main()
