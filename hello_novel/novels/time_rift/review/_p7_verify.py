# P7 final residual verification
from pathlib import Path

root = Path(r"D:\ai_person\p000_0000_media\hello_novel\novels\time_rift")

outline = (root / "novel/plot-outline.md").read_text(encoding="utf-8")
old_markers = [
    "百章里程碑", "两百章里程碑", "时间的语言**", "时间的目的**", "意识的本质**",
    "虚空的阴影", "暗影的真相", "共存的可能", "和谐的扩展", "新的篇章**",
    "存在的证明", "收获的喜悦", "新纪元**", "ARIA接受变化",
]
bad_detail = []
for line in outline.splitlines():
    s = line.strip()
    if not s.startswith("- **第"):
        continue
    if not any(x in line for x in old_markers):
        continue
    if any(tag in line for tag in ("旧题", "冲突化", "已去回顾")):
        continue
    bad_detail.append(line)

print("outline residual unannotated old titles:", len(bad_detail))
for b in bad_detail[:10]:
    print(" ", b[:90])

print("outline has alignment block:", "章名冲突化对齐" in outline)
print("outline has144/145:", "第三小时的切断线" in outline and "窗口打开之前，谁签字" in outline)
print("outline milestones tagged:", outline.count("已去回顾") >= 2 and "已冲突化" in outline)

banned = [
    "张远", "赵远航", "陈远桥", "旧时光", "初心咖啡",
    "百章里程碑", "两百章里程碑",
    "25岁", "二十五岁", "2079年", "只有61岁",
]
sb_dir = root / "novel/storyboards"
hits = {k: [] for k in banned}
for p in sb_dir.glob("*.md"):
    t = p.read_text(encoding="utf-8")
    for k in banned:
        if k in t:
            hits[k].append(p.name)
print("--- storyboard residuals ---")
for k, v in hits.items():
    print(f"  {k}: {len(v)} {v[:3]}")

# age anchors present
for fname, needles in {
    "第023章-李明的过去-分镜脚本.md": ["2085年3月15日", "34岁", "38岁", "2075年"],
    "第033章-幽灵的真面目-分镜脚本.md": ["27岁", "34岁", "赵远山"],
    "第037章-时间回溯-分镜脚本.md": ["六十五岁", "34岁"],
    "第052章-幽灵的过去-分镜脚本.md": ["二十七岁", "赵远山", "五十八岁"],
}.items():
    t = (sb_dir / fname).read_text(encoding="utf-8")
    missing = [n for n in needles if n not in t]
    print(f"anchor {fname}: {'OK' if not missing else 'MISS ' + str(missing)}")

files = [
    "review/P7-交付文档交叉引用核对.md",
    "novel/plot-outline.md",
    "novel/writing-notes.md",
    "novel/characters.md",
    "novel/timeline.md",
    "novel/unified-settings.md",
]
for rel in files:
    p = root / rel
    print(rel, "OK" if p.exists() else "MISSING", p.stat().st_size if p.exists() else 0)

wn = (root / "novel/writing-notes.md").read_text(encoding="utf-8")
print("P7 section in writing-notes:", "P7 施工记录 · outline/storyboard" in wn)
print("residual 143/202 noted in notes:", "ch143" in wn and "ch202" in wn)

tl = (root / "novel/timeline.md").read_text(encoding="utf-8")
print("timeline ch500 new title:", "第500章：消融停了，星星回来" in tl)
print("timeline old ch500 title gone:", "第500章：五百章里程碑" not in tl)

ch = (root / "novel/characters.md").read_text(encoding="utf-8")
print("characters ghost name:", "正式姓名：**赵远山**" in ch)
print("characters ghost detained:", "在押" in ch)

# disk residual titles
for num, expect_old in [("143", "牺牲、爱与连接"), ("202", "新的秩序")]:
    first = (root / f"novel/chapters/chapter-{num}.md").read_text(encoding="utf-8").splitlines()[0]
    print(f"ch{num} disk title:", first, "| residual old:", expect_old in first)
