# -*- coding: utf-8 -*-
"""章节去重扫描工具 —— 检测小说正文中"整章/整段逐字复制"问题。

用法（在仓库根或任意位置运行）:
    python assets/novels/沧元图续写/scripts/dedup_scan.py [chapters_dir]

不传参数时默认扫描 ../chapters/（即本书正文目录）。

输出两部分:
  1. 跨章复制对: 两章之间 10 字滑窗 shingle 的 Jaccard 相似度 >= 阈值即判定,
     按相似度降序输出 (J>=0.9 视为整章复制, 0.5-0.9 为大段复制, 0.35-0.5 为可疑)
  2. 章内复读句: 同一章内出现 >=2 次的长句 (>=14 字), 列出高频复读

纯标准库实现, 无第三方依赖。
"""

import csv
import os
import re
import sys
from collections import Counter, defaultdict

SHINGLE_SIZE = 10
SHINGLE_STRIDE = 4
PAIR_THRESHOLD = 0.35      # Jaccard 判定阈值
MIN_SENT_LEN = 14          # 章内复读句最短长度
TOP_N = 40                 # 跨章复制对最多输出条数


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def normalize(text):
    """去掉标题行与全部空白, 只留正文连贯文本。"""
    lines = text.splitlines()
    if lines and re.match(r"^第.{1,7}章", lines[0].strip()):
        lines = lines[1:]
    body = "".join(lines)
    return re.sub(r"\s+", "", body)


def shingles(text):
    return {text[i:i + SHINGLE_SIZE]
            for i in range(0, max(0, len(text) - SHINGLE_SIZE + 1), SHINGLE_STRIDE)}


def sentences(text):
    return [s for s in re.split(r"[。！？\n]+", text) if len(s) >= MIN_SENT_LEN]


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    chapters_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.normpath(
        os.path.join(root, "..", "chapters"))
    if not os.path.isdir(chapters_dir):
        print(f"目录不存在: {chapters_dir}")
        sys.exit(1)

    files = sorted(
        (f for f in os.listdir(chapters_dir)
         if re.match(r"^8-续写-第\d+章\.txt$", f)),
        key=lambda f: int(re.search(r"(\d+)", f).group(1)),
    )
    if not files:
        print("未找到章节文件 (8-续写-第N章.txt)")
        sys.exit(1)

    print(f"扫描目录: {chapters_dir}")
    print(f"章节数:   {len(files)}\n")

    texts, shingle_sets = {}, {}
    for name in files:
        body = normalize(read_text(os.path.join(chapters_dir, name)))
        texts[name] = body
        shingle_sets[name] = shingles(body)

    # ---------- 跨章复制对 (倒排索引 + 共享 shingle 计数) ----------
    inverted = defaultdict(set)
    for name, sset in shingle_sets.items():
        for sh in sset:
            inverted[sh].add(name)

    pair_shared = Counter()
    for _, names in inverted.items():
        if len(names) < 2 or len(names) > len(files) // 2:
            continue  # 过于常见的 shingle (如重复的过渡句) 不参与
        names = sorted(names)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                pair_shared[(names[i], names[j])] += 1

    results = []
    for (a, b), shared in pair_shared.items():
        union = len(shingle_sets[a]) + len(shingle_sets[b]) - shared
        j = shared / union if union else 0.0
        if j >= PAIR_THRESHOLD:
            results.append((j, shared, a, b))
    results.sort(reverse=True)

    # 全量结果落盘 CSV (供后续批修使用)
    csv_path = os.path.normpath(os.path.join(root, "..", "review", "dedup_pairs.csv"))
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["相似度J", "共享片段数", "章节A", "章节B", "判定"])
        for j, shared, a, b in results:
            level = "整章复制" if j >= 0.9 else ("大段复制" if j >= 0.5 else "可疑")
            w.writerow([f"{j:.2f}", shared, a, b, level])
    print(f"全量复制对已写入: {csv_path} (共 {len(results)} 对)\n")

    # J>=0.9 的整章复制做并查集聚类, 给出"哪些章互为复制"的簇
    parent = {f: f for f in files}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for j, _, a, b in results:
        if j >= 0.9:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

    clusters = defaultdict(list)
    for f in files:
        clusters[find(f)].append(f)
    dup_clusters = [sorted(c, key=lambda x: int(re.search(r"(\d+)", x).group(1)))
                    for c in clusters.values() if len(c) > 1]
    dup_clusters.sort(key=lambda c: int(re.search(r"(\d+)", c[0]).group(1)))

    print("=" * 72)
    print("〇、整章复制簇 (J>=0.9 并查集聚类, 每行=一组互为复制的章节)")
    print("=" * 72)
    if not dup_clusters:
        print("  无")
    for c in dup_clusters:
        nums = ",".join(re.search(r"第(\d+)章", x).group(1) for x in c)
        print(f"  簇({len(c)}章): 第{nums}章")
    print(f"\n  整章复制簇共 {len(dup_clusters)} 组, 涉及 {sum(len(c) for c in dup_clusters)} 章\n")

    print("=" * 72)
    print("一、跨章复制对 (Jaccard 相似度降序)")
    print("=" * 72)
    if not results:
        print("  未发现达到阈值的跨章复制对。")
    for j, shared, a, b in results[:TOP_N]:
        level = "整章复制" if j >= 0.9 else ("大段复制" if j >= 0.5 else "可疑")
        print(f"  [{level}] J={j:.2f}  共享片段 {shared} 处")
        print(f"      {a}  <->  {b}")
    if len(results) > TOP_N:
        print(f"  ... 另有 {len(results) - TOP_N} 对未列出")

    dup_files = sorted({f for r in results for f in (r[2], r[3])})
    print(f"\n  涉及章节数: {len(dup_files)}")

    # ---------- 章内复读句 ----------
    print()
    print("=" * 72)
    print("二、章内复读句 (同一句 >=2 次且 >=14 字, 仅列复读次数 >=3 的)")
    print("=" * 72)
    total_bad = 0
    for name in files:
        counter = Counter(sentences(texts[name]))
        repeats = [(s, c) for s, c in counter.items() if c >= 3]
        if repeats:
            total_bad += 1
            print(f"\n  {name}:")
            for s, c in sorted(repeats, key=lambda x: -x[1])[:6]:
                print(f"    x{c}  {s[:40]}{'...' if len(s) > 40 else ''}")
    if not total_bad:
        print("  未发现高频复读句。")

    print("\n扫描完成。")


if __name__ == "__main__":
    main()
