# hello_novel — 小说创作生产线

多部长篇的过程稿、正文与衍生素材（分镜/视频脚本/审查）。

## 目录地图

```
hello_novel/
├── README.md
├── guides/                         # 通用方法（原 自媒体成长之路）
│   ├── 豆包AI视频生成技巧.md
│   ├── 短视频剧情连贯性指南.md
│   └── 一个普通人的35年.md
└── novels/
    ├── cangyuantu/                 # 《沧元图》续写
    ├── diff_life/                  # 《平凡人生》
    ├── little_man/                 # 《普通人的一生》
    └── time_rift/                  # 《时间裂隙：2089》
```

单部作品标准结构：

```
novels/<book>/
├── README.md
├── process/     # 选题、设定、大纲、审核
├── chapters/    # 章节正文
├── review/      # 连贯性/质量审查（如有）
├── source/      # 原著与合集（如有）
├── scripts/     # 上传等脚本（如有）
└── meta/        # 总结与杂项
```

`time_rift` 保持其自带系统结构（`novel/chapters|storyboards|video_scripts`、`review/`、`memory/`），入口见其 README / AGENTS.md。

## 作品一览

| 目录 | 作品 | 正文位置 | 状态 |
|------|------|----------|------|
| [cangyuantu](novels/cangyuantu/README.md) | 沧元图续写 | `chapters/8-续写-第N章.txt`（约 300） | 过程稿完整 |
| [diff_life](novels/diff_life/README.md) | 平凡人生 | `chapters/8-正文-第N章.txt`（约 300） | 含审核报告 |
| [little_man](novels/little_man/README.md) | 普通人的一生 | `chapters/` + 完整版 md | 短篇 |
| [time_rift](novels/time_rift/README.md) | 时间裂隙：2089 | `novel/chapters/`（约 600） | 已完结，待修订 |

## 与平台 CLI 的衔接

章节在 `chapters/` 下，可用中台做内容转化：

```bash
python media-cli.py story script \
  "hello_novel/novels/cangyuantu/chapters/8-续写-第1章.txt" -s 玄幻 -n 8 -o script.md

python media-cli.py story article \
  "hello_novel/novels/diff_life/chapters/8-正文-第1章.txt" --type deep -o article.md

python media-cli.py asset scan novel --project 沧元图 \
  --dir ./hello_novel/novels/cangyuantu/chapters/
```

## 文档

- 各作品入口：`novels/*/README.md`
- 时间裂隙系统：`novels/time_rift/README.md`、`novels/time_rift/AGENTS.md`
- 通用技巧：`guides/`
- 目录规范：[../docs/DIRECTORY_STANDARD.md](../docs/DIRECTORY_STANDARD.md)

## 已知问题

- **路径已重排**：旧路径 `hello_novel/cangyuantu/8-续写-*.txt`、`8-正文/` 已改为 `novels/<book>/chapters/`。
- `cangyuantu/scripts/*.sh` 仍写死 `D:/ai_coder/p000_000_cangyuantu`，属遗留，运行前须改路径。
- 部分技能文档曾描述 `8-正文-第X章.txt` 命名，与沧元图实际 `8-续写-第X章.txt` 不一致，以各作品 README 为准。
