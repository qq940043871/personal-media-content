# -*- coding: utf-8 -*-
"""分块生成种子文章导入数据：每块 = 独立合法的 b64（按字符切，保证 UTF-8 边界安全）"""
import base64
import json
import os

ROOT = r"D:\ai_person\p000_0000_it"
SEED = os.path.join(ROOT, "media", "blog", "_seed")
META = os.path.join(SEED, "meta.json")
BLOCKS = os.path.join(SEED, "blocks.jsonl")
CHUNK = 400  # 最坏情况（全中文）：400×3字节→1600 b64，JSON 行 <1700，安全

# (文件, 标题, 摘要, 标签, emoji, hue, 节选)
POSTS = [
    ("it/knowledge-base/pages/00_overview/advanced-dev-questions.md",
     "高级开发核心技术问题清单",
     "从计算机启动流程到系统就绪——一份覆盖底层原理与工程实践的高级开发进阶问题清单。",
     ["进阶成长", "底层原理"], "🧭", 265, None),
    ("it/knowledge-base/pages/05_system_architect/distributed/distributed-overview.md",
     "分布式系统入门：架构师视角的全景笔记",
     "从单体到分布式的演进逻辑、核心挑战与经典解决方案，架构师学习路线的第一块拼图。",
     ["架构", "分布式"], "🌐", 220, None),
    ("it/knowledge-base/pages/05_system_architect/distributed/microservices.md",
     "微服务架构笔记：拆分、治理与边界",
     "微服务不是银弹：什么时候该拆、怎么拆、拆完之后如何治理，一篇讲清楚服务化架构的骨架。",
     ["架构", "微服务"], "🧩", 200, None),
    ("it/knowledge-base/pages/05_system_architect/high-concurrency/high-concurrency-overview.md",
     "高并发系统设计总览",
     "缓存、限流、降级、异步——高并发三板斧背后的设计思想与落地路径。",
     ["架构", "高并发"], "⚡", 45, None),
    ("it/knowledge-base/pages/05_system_architect/database/database-overview.md",
     "数据库架构概览：从单库到分库分表",
     "读写分离、垂直拆分、水平分片——数据库在业务增长下的架构演进路线图。",
     ["架构", "数据库"], "🗄️", 190, None),
    ("it/knowledge-base/pages/05_system_architect/devops/devops-overview.md",
     "DevOps 概览：让交付流水线跑起来",
     "CI/CD、自动化测试、监控告警——DevOps 文化的工程化落地入门笔记。",
     ["DevOps", "架构"], "🛠️", 160, None),
    ("it/knowledge-base/pages/04_java_developer/01_syntax/java-collections.md",
     "Java 集合框架全景：架构师学习笔记",
     "List、Map、Set 背后的统一架构：接口设计、典型实现与选型思路一次理清。",
     ["Java", "集合框架"], "☕", 30, None),
    ("it/interview-kit/banks/MySQL面试题深度整理.md",
     "MySQL 面试题深度整理（精选）",
     "索引、事务、锁、日志链路——MySQL 高频面试题的深度追问与原理拆解。",
     ["MySQL", "面试"], "🐬", 210, 4000),
    ("it/interview-kit/banks/Redis面试题深度整理.md",
     "Redis 面试题深度整理（精选）",
     "数据结构、持久化、主从与哨兵、缓存三兄弟——Redis 核心考点逐个击破。",
     ["Redis", "面试"], "🧱", 5, 4000),
    ("it/interview-kit/banks/Java深度八股文.md",
     "Java 深度八股文（精选）",
     "JVM、并发、集合——从「是什么」到「为什么」的 Java 深度追问链。",
     ["Java", "面试"], "☕", 255, 4000),
]

def smart_cut(text, limit):
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for pat in ("\n## ", "\n### ", "\n\n"):
        pos = cut.rfind(pat)
        if pos > limit * 0.5:
            return cut[:pos].rstrip() + "\n\n> 📎 本文为节选，完整版见博主的知识库，后续章节陆续发布。\n"
    return cut.rstrip() + "\n\n> 📎 本文为节选，完整版见博主的知识库。\n"

meta = []
blocks = []
for idx, (rel, title, summary, tags, emoji, hue, cutlen) in enumerate(POSTS, 1):
    with open(os.path.join(ROOT, rel), "r", encoding="utf-8") as f:
        text = f.read().strip()
    if cutlen:
        text = smart_cut(text, cutlen)
    # 按字符切块，每块独立 b64（合法、可独立解码、顺序拼接无损）
    chunks = [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)]
    for seq, ch in enumerate(chunks, 1):
        blocks.append({"post": idx, "seq": seq,
                       "b64": base64.b64encode(ch.encode("utf-8")).decode("ascii")})
    meta.append({"idx": idx, "title": title, "summary": summary, "tags": tags,
                 "emoji": emoji, "hue": hue, "chars": len(text), "chunks": len(chunks)})

with open(META, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)
with open(BLOCKS, "w", encoding="ascii") as f:
    for b in blocks:
        f.write(json.dumps(b) + "\n")

total_blocks = len(blocks)
max_line = max(len(json.dumps(b)) for b in blocks)
print(f"OK {len(meta)} posts, {total_blocks} blocks, max json line = {max_line} chars")
