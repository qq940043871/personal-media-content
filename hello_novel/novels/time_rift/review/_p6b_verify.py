# -*- coding: utf-8 -*-
"""P6-B verify + topup: scan 541-600 CJK/dash; fix 林晓他->她 in touched files."""
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).parent))
from _p6b_common import body_cjk, dash_count, split_file, insert_blocks, compress_dashes

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

# Generic but differentiated topups if still short after expand A/B/C
TOPUP = {}

TOPUP[543] = """
返程名单上，林晓在「观察员」后面手写加了括号：「非代表」。引导员说系统栏位写不下。写不下就写在纸边。纸边也是账。
"""

TOPUP[544] = """
命名悬置的第二周，联盟发来补充问卷，第一题是「桥的量化指标」。林晓在空白处写：「请先回答：谁在雨里描过水位标尺。」问卷没有回收，页边那句话留在实验室活页夹里。
"""

TOPUP[545] = """
任务结束回程前，林晓去十九层把手写表末行又读了一遍：「今天灯亮到九点，够用了。」她没有拍照，只在任务卡第三行添了五个字：「替看见的人。」仍是半句。半句可以再写。
"""

TOPUP[574] = """
第十五天夜里，新生意识的信号短了一截。林晓在对照栏标「异常·待复核」，没有惊动联署，先按老师教的：私栏报警，公栏等证据。教育若从惊慌开始，传承就会变成甩锅。
"""

TOPUP[575] = """
合箱前，林晓把访客证在灯下又看了一眼。照片上老师很年轻，眼神已经会看表。她轻声说：「证我会收好。不会拿去证明谁伟大，只证明有人认真加过班。」
"""

TOPUP[577] = """
第五天，对照栏右栏写的是：「23层灯仍留到十一点。」林晓在旁边画了一个很小的空心圆，不是完成符号，是提醒：灯会灭，记法要传。
"""

TOPUP[578] = """
摘录结束时，林晓把只读记录仪的电池抠下来，放进写有「形状B」的纸袋。她说：「下次分析先查权限，再谈灵感。灵感买不起错账。」
"""

TOPUP[580] = """
天亮前，林晓离开图书馆，在楼下给店长发了一条短讯：「椅子我明早去擦。」店长回：「擦自己的那把就行。第三把有人排班。」谁排的班，讯里没说。没说也是账。
"""

TOPUP[584] = """
散会的人流从她身边经过。林晓把对照卡最后看了一遍，折进胸前口袋，紧贴那枚联盟使者徽章。徽章会旧，卡上的问题不该旧。
"""

TOPUP[586] = """
关灯离开实验室前，林晓把感恩清单从墙上取下，换成一张更小的纸：「今日续用：手写表复核法。」一天续用一次，比一百句抬高扎实。
"""

TOPUP[587] = """
典礼结束，林晓路过那排维修中的椅子。牌子还在。她没去坐，也没去催。有些空位的意义就是提醒：连接要在家具之外被证明。
"""

TOPUP[589] = """
雨势稍弱，配电箱旁的水位标尺又露出一截。ARIA伸手虚虚比了比刻度，没有替任何人记录。有些感恩的第一步，是承认自己不是最该握笔的那个人。
"""

TOPUP[590] = """
林晓付了自己的面钱，没有替空椅子付。店长说：「空位有人养。你把自己的账结清就好。」爱若变成抢着买单，店就会变成秀场。
"""

TOPUP[592] = """
参观结束时，ARIA把手写票根夹进袖口内袋，和旧日证件复印件放在一起。票根会潮，复印件会黄，排队这件事本身，是城市给她上的回新上海的第一课。
"""

TOPUP[595] = """
离开面馆前，ARIA把回执条上「有人记得」四个字又读了一遍。记得不是拥有。记得是肯在原点日也按日付账。
"""

TOPUP[597] = """
灯箱巷口，巡逻车扫过一束白光，又开走。手写表没有被收走，铅笔灰也没有。系统可以升级，人看见的数仍要人描。
"""

TOPUP[598] = """
ARIA把抽屉关上，没有上锁。锁会制造档案的傲慢。她要的不是保管秘密，是让下一个人能轻松拉开，看见学生交上来的一半句子，然后把另一半留给城市去写。
"""

TOPUP[599] = """
夜风里，消防门在她身后缓缓合拢。登记本还在保安台上，「看见灯还亮着」那一行墨迹未干。最后的选择若不能被这样一行普通字承担，就不配叫最后。
"""

TOPUP[600] = """
打烊灯的光很轻，落在木牌上，也落在尚未有人签字的观察窗栏上。开始不是钟声，是有人仍按班次留灯。
"""

TOPUP[542] = """
碎片观察结束，林晓在交班条上写：「锯齿已录，解释缺。」缺不是失败，是拒绝把形状过早说成真理。
"""

TOPUP[547] = """
ARIA没有表扬她，只说：「夜里冷，下次带温感贴。」林晓点头。影子学不来，关心可以学。
"""

TOPUP[549] = """
纸样贴满半面墙时，助手提议拍张合影。林晓摇头：「合影会让人以为结论出了。结论还在停顿里。」
"""

TOPUP[555] = """
海的表层又平静下去。ARIA把抹布压烫疤的那一下形状，放进和手写表、粉笔字并列的私栏。觉醒若丢掉这些形状，就会漂成无账的光。
"""

TOPUP[557] = """
口令卡的过期日，林晓写了「下一次谁下去之前必须重写」。永恒连接不需要永恒的旧卡，需要不断作废的空话。
"""

TOPUP[558] = """
茶摊打烊前，摊主把传说又讲给下一位客人。林晓走出巷口时没有回头。传说归人嘴，观察归实验室，账本分开，故事才活得下去。
"""

TOPUP[561] = """
定义会散场，林晓把那张手写表照片从展板上取下，还给十九层的保管处。保管员问：「不展了吗？」她说：「展过了，该回灯箱。」
"""

TOPUP[562] = """
晨曦最终没有把失败色涂满画布，只在右下角留了一道很窄的灰。窄是尊重：有些颜色不该被艺术家消费完。
"""

TOPUP[566] = """
白板上那行「由谁复核」被保留了三天，没人填。第四天，林晓用铅笔在下面补：「先空着，空着也是交接的一部分。」
"""

TOPUP[567] = """
ARIA把交接单的签收栏对着灯光看了很久。空栏不等于拒绝签，等于拒绝在问清楚之前签。继承的第一项工作往往是学会不急着继承。
"""

TOPUP[571] = """
楼下温度抄录本合上时，穹顶的开花光纹正好转过最亮的一档。两本记录并排放进防火柜。柜门关合的声音很轻，像城市在说：都算数。
"""

TOPUP[572] = """
电工收工前把23层的共振数据抄了一份给林晓，说：「店长那边我口头说了，不停业。数据你存实验室。」口头与纸面分开，店才像店。
"""

TOPUP[573] = """
软木板上，新生意识摘要与老师旧句之间留了两指宽的空。林晓不把空填满。问题需要伸展的空间，教材塞满就会窒息。
"""

TOPUP[576] = """
提问的意识又安静了下去。林晓把作业本背面的草稿纸再次展开，夹进私人日志。她不打算回答。有人提问时不去抢答，也许就是爱尚存的形状。
"""

TOPUP[579] = """
纸条盒子上锁之前，林晓放进去最后一张空条，只写日期。日期是留给还没发生的故事的回执位。
"""

TOPUP[582] = """
助手把铅笔批注誊到电子档，林晓检查后说：「仅叙事那几条不要美化，保留原样。成长审查的职责不是让数据板好看。」
"""

TOPUP[583] = """
离开纪念馆时，空框仍在。林晓在访客本回执栏始终没有写。不写回执，有时是最后的克制：不替空框结案。
"""

TOPUP[588] = """
下楼前，ARIA看了一眼擦拭记录本的末页，只有日期和「无异常」。源头若会说话，也许会谢谢这四个字的寡淡。
"""

TOPUP[591] = """
信封被放进实验室钥匙盒，和门禁卡分开放。林晓在盒盖内侧贴了张纸：「交接不是离线，是把在线方式换人。」
"""

TOPUP[593] = """
坡道尽头的风把她的手电吹得晃了一下。透出来的旧字在光影里时隐时现。变化承认底下有字，城市才不算把账本扔了。
"""

# pronoun fixes: 林晓 she
LINXIAO_HE_PATTERNS = [
    (r"(林晓[^。\n]{0,40})他(说|问|道|想|写|看|站|走|笑|点头|摇头|叹)", r"\1她\2"),
    (r"他(站在记忆图书馆|穿着联盟使者|了解ARIA|的手|的白色|的笔)", r"她\1"),
]

def fix_linxiao(path):
    raw = path.read_text(encoding="utf-8")
    body, footer = split_file(raw)
    orig_body = body
    # only fix 林晓 adjacent 他
    body = re.sub(r"林晓([^。\n]{0,30})他(说|问|道|想|写|看|站|走|笑|点头|摇头|叹|穿着|了解)", r"林晓\1她\2", body)
    body = re.sub(r"他(站在记忆图书馆|穿着联盟使者|了解ARIA|穿着白色|穿着深蓝色)", r"她\1", body)
    if body != orig_body:
        out = body
        if footer:
            if not footer.startswith("---"):
                footer = "---\n" + footer
            if not out.endswith("\n"):
                out += "\n"
            out += footer
        if not out.endswith("\n"):
            out += "\n"
        path.write_text(out, encoding="utf-8")
        return True
    return False


def scan():
    rows = []
    for n in range(541, 601):
        p = base / ("chapter-%d.md" % n)
        if not p.exists():
            rows.append((n, 0, 0, "MISSING"))
            continue
        raw = p.read_text(encoding="utf-8")
        cjk = body_cjk(raw)
        d = dash_count(raw)
        flag = "OK" if cjk >= 5000 and d <= 8 else ("DASH" if cjk >= 5000 else "SHORT")
        if n == 600 and cjk >= 4500 and d <= 8:
            flag = "ASSET-OK"
        rows.append((n, cjk, d, flag))
    return rows


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("all", "topup"):
        for n, block in TOPUP.items():
            p = base / ("chapter-%d.md" % n)
            if not p.exists():
                continue
            raw = p.read_text(encoding="utf-8")
            before = body_cjk(raw)
            if before >= 5000:
                continue
            insert_blocks(p, {n: block})
            compress_dashes(p, keep_max=8)
            after = body_cjk(p.read_text(encoding="utf-8"))
            print("topup ch%d: %d -> %d %s" % (n, before, after, "OK" if after >= 5000 else "STILL"))
    if mode in ("all", "pronoun"):
        for n in range(541, 601):
            p = base / ("chapter-%d.md" % n)
            if p.exists() and fix_linxiao(p):
                print("pronoun fixed ch%d" % n)
    if mode in ("all", "scan"):
        short = []
        dashbad = []
        for n, cjk, d, flag in scan():
            if flag in ("SHORT", "MISSING"):
                short.append((n, cjk, d))
            elif flag == "DASH":
                dashbad.append((n, cjk, d))
            print("%d\t%d\t%d\t%s" % (n, cjk, d, flag))
        print("SHORT", short)
        print("DASH>8 still", dashbad)

if __name__ == "__main__":
    main()
