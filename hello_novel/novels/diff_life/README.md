# 平凡人生（diff_life）

都市/人生题材长篇：选题 → 核心设定 → 大纲 → 剧情单元 → 分章大纲 → 正文。

## 目录地图

```
diff_life/
├── README.md
├── CLAUDE.md
├── process/                 # 1-选题 … 7-封面提示词、5/6 大纲与单元
├── chapters/                # 8-正文-第N章.txt（约 300）
└── review/                  # 审核报告-第N章.txt、剧情单元审核报告
```

## 命名

| 阶段 | 路径 |
|------|------|
| 选题/设定/简介/分卷 | `process/1-选题.txt` … `process/4-分卷大纲.txt` |
| 剧情单元 | `process/5-第N卷-剧情单元.txt` |
| 分章大纲 | `process/6-第N-M章-分章大纲.txt` |
| 封面提示词 | `process/7-封面提示词.txt` |
| 正文 | `chapters/8-正文-第N章.txt` |
| 审核 | `review/审核报告-*.txt`、`review/剧情单元审核报告-*.txt` |

## 常用

```bash
python media-cli.py story article \
  "hello_novel/novels/diff_life/chapters/8-正文-第1章.txt" --type summary -o article.md
```

## 状态

- 约 300 章正文；过程与审核报告保留完整
