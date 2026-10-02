# -*- coding: utf-8 -*-
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).parent))
from _p6b_common import body_cjk, dash_count

base = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

def fix_file(n):
    p = base / ("chapter-%d.md" % n)
    raw = p.read_text(encoding="utf-8")
    orig = raw
    # 林晓 as subject with 他
    raw = re.sub(r"(林晓[^。\n]{0,25})他(说|问|道|想|写|看|站|走|笑|点头|摇头|叹|没有|开口|的|在)", r"\1她\2", raw)
    raw = re.sub(r"「林晓。」她叫他。", "「林晓。」她叫她。", raw)
    raw = re.sub(r"她叫他。", "她叫她。", raw)
    # specific known
    raw = raw.replace("他知道苏婉清对ARIA意味着", "她知道苏婉清对ARIA意味着")
    raw = raw.replace('"教育是……传递。"他说，', '"教育是……传递。"她说，')
    raw = raw.replace("林晓问。他的语气", "林晓问。她的语气")
    raw = raw.replace("林晓说。他看着", "林晓说。她看着")
    raw = raw.replace("林晓问。他的声音", "林晓问。她的声音")
    raw = raw.replace("林晓的声音把她拉回现实。他的语气", "林晓的声音把她拉回现实。她的语气")
    raw = raw.replace("ARIA从未在他身", "ARIA从未在她身")
    raw = raw.replace("ARIA能听到他在通讯频道", "ARIA能听到她在通讯频道")
    raw = raw.replace("林晓的声音再次从通讯频道传来。他的语气", "林晓的声音再次从通讯频道传来。她的语气")
    raw = raw.replace("林晓开口了，声音里含着一种", "林晓开口了，声音里含着一种")
    if raw != orig:
        p.write_text(raw, encoding="utf-8")
        print("fixed", n, "cjk", body_cjk(raw), "dash", dash_count(raw))
        return True
    print("nochange", n)
    return False

for n in [545, 547, 571, 574, 580, 600, 558, 555, 567]:
    if (base / ("chapter-%d.md" % n)).exists():
        fix_file(n)

# verify 600 他 near 林晓
raw = (base / "chapter-600.md").read_text(encoding="utf-8")
print("\n600 remaining 林晓+他:")
for m in re.finditer(r".{0,10}林晓.{0,25}", raw):
    if "他" in m.group():
        print(repr(m.group()[:50]))
print("600 cjk", body_cjk(raw))
