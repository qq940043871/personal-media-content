# -*- coding: utf-8 -*-
"""生成博客种子文章的导入数据（JSONL），供 exec_sql parameters 使用"""
import base64
import json
import os

ROOT = r"D:\ai_person\p000_0000_it"
OUT = os.path.join(ROOT, "blog", "_seed", "seed_posts.jsonl")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# (文件路径, 标题, 摘要, 标签, emoji, hue, 节选长度(None=全文))
POSTS = [
    ("knowledge-base/pages/00_overview/advanced-dev-questions.md",
     "高级开发核心技术问题清单",
     "从计算机启动流程到系统就绪——一份覆盖底层原理与工程实践的高级开发进阶问题清单。",
     ["进阶成长", "底层原理"], "🧭", 265, None),
    ("knowledge-base/pages/05_system_architect/distributed/distributed-overview.md",
     "分布式系统入门：架构师视角的全景笔记",
     "从单体到分布式的演进逻辑、核心挑战与经典解决方案，架构师学习路线的第一块拼图。",
     ["架构", "分布式"], "🌐", 220, None),
    ("knowledge-base/pages/05_system_architect/distributed/microservices.md",
     "微服务架构笔记：拆分、治理与边界",
     "微服务不是银弹：什么时候该拆、怎么拆、拆完之后如何治理，一篇讲清楚服务化架构的骨架。",
     ["架构", "微服务"], "🧩", 200, None),
    ("knowledge-base/pages/05_system_architect/high-concurrency/high-concurrency-overview.md",
     "高并发系统设计总览",
     "缓存、限流、降级、异步——高并发三板斧背后的设计思想与落地路径。",
     ["架构", "高并发"], "⚡", 45, None),
    ("knowledge-base/pages/05_system_architect/database/database-overview.md",
     "数据库架构概览：从单库到分库分表",
     "读写分离、垂直拆分、水平分片——数据库在业务增长下的架构演进路线图。",
     ["架构", "数据库"], "🗄️", 190, None),
    ("knowledge-base/pages/05_system_architect/devops/devops-overview.md",
     "DevOps 概览：让交付流水线跑起来",
     "CI/CD、自动化测试、监控告警——DevOps 文化的工程化落地入门笔记。",
     ["DevOps", "架构"], "🛠️", 160, None),
    ("knowledge-base/pages/04_java_developer/01_syntax/java-collections.md",
     "Java 集合框架全景：架构师学习笔记",
     "List、Map、Set 背后的统一架构：接口设计、典型实现与选型思路一次理清。",
     ["Java", "集合框架"], "☕", 30, None),
    ("interview-kit/banks/MySQL面试题深度整理.md",
     "MySQL 面试题深度整理（精选）",
     "索引、事务、锁、日志链路——MySQL 高频面试题的深度追问与原理拆解。",
     ["MySQL", "面试"], "🐬", 210, 4000),
    ("interview-kit/banks/Redis面试题深度整理.md",
     "Redis 面试题深度整理（精选）",
     "数据结构、持久化、主从与哨兵、缓存三兄弟——Redis 核心考点逐个击破。",
     ["Redis", "面试"], "🧱", 5, 4000),
    ("interview-kit/banks/Java深度八股文.md",
     "Java 深度八股文（精选）",
     "JVM、并发、集合——从「是什么」到「为什么」的 Java 深度追问链。",
     ["Java", "面试"], "☕", 255, 4000),
]

def smart_cut(text: str, limit: int) -> str:
    """截断到 limit 附近，回退到最近的标题/段落边界，补节选提示"""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    # 回退到最近的二级标题或空行边界
    for pat in ("\n## ", "\n### ", "\n\n"):
        pos = cut.rfind(pat)
        if pos > limit * 0.5:
            return cut[:pos].rstrip() + "\n\n> 📎 本文为节选，完整版见博主的知识库。后续章节将陆续发布。\n"
    return cut.rstrip() + "\n\n> 📎 本文为节选，完整版见博主的知识库。\n"

rows = []
for idx, (rel, title, summary, tags, emoji, hue, cutlen) in enumerate(POSTS, 1):
    with open(os.path.join(ROOT, rel), "r", encoding="utf-8") as f:
        text = f.read().strip()
    if cutlen:
        text = smart_cut(text, cutlen)
    b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    # b64 拆成 76 字符/行的多行文件，规避 Read 工具单行 2000 字符截断
    b64_file = os.path.join(os.path.dirname(OUT), f"post_{idx:02d}.b64")
    with open(b64_file, "w", encoding="ascii") as f:
        for i in range(0, len(b64), 76):
            f.write(b64[i:i + 76] + "\n")
    rows.append({
        "idx": idx, "title": title, "summary": summary, "tags": tags,
        "emoji": emoji, "hue": hue, "b64_lines": (len(b64) + 75) // 76,
        "b64_len": len(b64), "chars": len(text), "file": b64_file,
    })

with open(OUT, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"OK {len(rows)} posts -> {os.path.dirname(OUT)}")
for r in rows:
    print(f"  #{r['idx']} {r['title'][:24]:<26} {r['chars']:>6} chars  b64={r['b64_len']:>6} ({r['b64_lines']} lines)")
