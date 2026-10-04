# 沧元图（续写）

《沧元图》AI 续写项目：8 步创作法过程稿 + 约 300 章正文。

## 目录地图

```
沧元图续写/
├── README.md
├── CLAUDE.md
├── .claude/skills/          # novel-* 技能
├── process/                 # 选题→大纲→剧情单元等过程稿
├── chapters/                # 8-续写-第N章.txt（约 300）
├── source/                  # 沧元图.txt、合集、epub
├── scripts/                 # 历史上传脚本（路径已过时）
└── meta/                    # 续写完成总结等
```

## 正文命名

- 过程步骤文件：`process/1-…` … `process/7-…`、`process/5-续写-第N卷-剧情单元.txt`、`process/6-续写-…分章大纲.txt`
- 章节：`chapters/8-续写-第N章.txt`（注意是 **续写**，不是 `8-正文`）

## 常用

```bash
# 从仓库根扫描入库
python media-cli.py asset scan novel --project 沧元图 \
  --dir ./assets/novels/沧元图续写/chapters/

# 单章转文章/分镜
python media-cli.py story article \
  "assets/novels/沧元图续写/chapters/8-续写-第1章.txt" --type deep -o article.md
```

## 状态

- 正文约 300 章，过程稿（卷剧情单元、分章大纲）完整
- 技能：`CLAUDE.md` + `.claude/skills/novel-*`

## 已知问题

- `scripts/*.sh` 指向历史目录 `D:/ai_coder/p000_000_cangyuantu`，不能直接跑
- 技能说明中的章节命名可能仍写 `8-正文-第X章.txt`，实际文件为 `8-续写-第X章.txt`
