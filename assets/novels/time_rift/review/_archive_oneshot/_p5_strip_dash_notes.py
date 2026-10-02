# -*- coding: utf-8 -*-
from pathlib import Path
import re

CHDIR = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift\novel\chapters")

# rewrite the process bullet into narrative form (keep substantive tail)
REPL = {
    r"^- 破折号压低；焦点章钩子=停电签名与传单$": "- 钩子：停电签名与传单未结；焦点章地面页与地下线并行",
    r"^- 破折号压低；场景加厚落到市场晚饭与值班核对$": "- 场景落点：市场晚饭与值班核对；幻影不得取消今日电表",
    r"^- 破折号压低；可读结论=连接与可执行班表同时存在$": "- 可读结论：连接与可执行班表同时存在",
    r"^- 破折号压低；代价可审计$": "- 代价可审计；听证与基层问责不被宇宙稳定性取消",
    r"^- 破折号压低；宏大可晚，账不能晚$": "- 可读结论：宏大可晚，账不能晚",
    r"^- 破折号压低；每段冲突对应可投票/可拨款的选项$": "- 可读结论：每段冲突对应可投票/可拨款的选项",
    r"^- 破折号压低；每段哲学对应可执行动作$": "- 可读结论：每段哲学对应可执行动作",
    r"^- 破折号压低；对话带拒绝与条件$": "- 可读结论：对话带拒绝与条件",
    r"^- 破折号压低；真相阅读姿势=能引用、能质询、能修泵$": "- 可读结论：真相阅读姿势=能引用、能质询、能修泵",
}

def main():
    n_fixed = 0
    for p in sorted(CHDIR.glob("chapter-*.md")):
        text = p.read_text(encoding="utf-8")
        m = re.search(r"((?:\n---\s*\n)?\*\*本章关键点[：:]?\*\*\s*\n)([\s\S]+)$", text)
        if not m:
            continue
        head, body = m.group(1), m.group(2)
        new_body = body
        for pat, rep in REPL.items():
            new_body = re.sub(pat, rep, new_body, flags=re.M)
        # drop any remaining pure process bullets
        lines = []
        for ln in new_body.splitlines():
            if re.search(r"破折号压低|dash 保持低位|本批 C 类|正文不作同文公文尾", ln):
                continue
            lines.append(ln)
        new_body = "\n".join(lines)
        if not new_body.endswith("\n"):
            new_body += "\n"
        if new_body != body:
            p.write_text(text[: m.start()] + head + new_body, encoding="utf-8")
            n_fixed += 1
            print("fixed", p.name)
    print("total", n_fixed)

if __name__ == "__main__":
    main()
