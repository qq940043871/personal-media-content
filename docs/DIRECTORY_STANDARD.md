# 目录与文档规范

适用于本仓库所有业务线，保证「过程 / 内容 / 说明 / 素材」可分离、可检索。

## 1. 分层定义

| 层 | 含义 | 典型文件 | 是否进版本管理 |
|----|------|----------|----------------|
| **process** | 过程稿：选题、设定、大纲、审核报告、日志 | `1-选题.txt`、`审核报告-*.txt`、`outline.md` | 是 |
| **chapters / analyses** | 内容本体：章节正文、分析稿 | `8-续写-第N章.txt`、`*分析.html` | 是 |
| **docs** | 说明与规范：README、方案、索引 | `README.md`、`分镜提示词大全.md` | 是 |
| **skills / .claude** | Agent 技能与项目指令 | `SKILL.md`、`CLAUDE.md`、`AGENTS.md` | 是 |
| **assets / media** | 图片、视频、封面等二进制 | `*.mp4`、`*.png` | 视体积 |
| **output / drafts** | 流水线产出或待发稿件 | `article.md`、转写 txt | 视业务 |
| **scripts** | 上传/批处理等辅助脚本 | `upload_*.sh` | 是 |
| **source** | 外部原著或合并终稿 | `沧元图.txt`、`*.epub` | 是 |

## 2. 业务线落地结构

### hello_novel

```
hello_novel/
├── README.md
├── guides/                      # 通用方法与技巧（原 自媒体成长之路）
└── novels/
    └── <book_id>/
        ├── README.md            # 作品入口
        ├── CLAUDE.md / .claude/ # 技能与约定（若有）
        ├── process/             # 选题、设定、大纲、审核
        ├── chapters/            # 章节正文
        ├── review/              # 连贯性/质量审查（若有）
        ├── source/              # 原著与合集
        ├── scripts/             # 上传等脚本
        └── meta/                # 总结与杂项
```

### hello_doubao_video

```
hello_doubao_video/
├── README.md
├── docs/          # 提示词大全、合并方案
├── scripts/       # 去水印、合并 bat/py
├── assets/        # 帧图、去水印图
└── media/         # 成片与分段 mp4、merge_list.txt
```

### hello_weixin_book

```
hello_weixin_book/
├── README.md
├── INDEX.md       # 作品分析清单
├── analyses/      # *分析.html
└── assets/        # generated-images、outputs、.workbuddy
```

### hello_webchat_* / hello_feishu

代码流水线目录保持程序可运行结构，仅约定：

- 入口说明必须有 `README.md`（或等价 `CLAUDE.md`，并在根索引登记）
- 技能集中在 `.claude/skills/`（或 `skills_self/`）
- 生成稿进 `drafts/` 或 `output/`，不与技能配置混放

## 3. 文档写法（中文技术文档）

统一骨架：

1. **标题 + 一句话定位**
2. **目录地图**（树或表）
3. **常用命令 / 流程**
4. **文档索引**（链到子文档）
5. **状态与已知问题**

原则：

- 路径写**整理后的现行路径**，禁止继续写已废弃的 `8-正文/`、仓库根平铺章节路径
- 命令可复制粘贴；相对路径以仓库根或业务线根说明基准
- 过程文档不替代入口 README：入口只导航，细节下沉

## 4. 命名约定

| 对象 | 约定 | 示例 |
|------|------|------|
| 小说目录 | 英文 slug | `cangyuantu`、`time_rift` |
| 章节正文 | 带步骤或章号前缀 | `8-续写-第1章.txt`、`chapter-001.md` |
| 过程稿 | 数字步骤前缀 | `1-选题.txt`、`6-第1-5章-分章大纲.txt` |
| 分析 HTML | 中文书名 + 类型 | `盘龙分析.html` |
| 入口文档 | `README.md` / `INDEX.md` | 每目录至多一个 README |

## 5. 变更检查清单

搬迁或新增文件后：

- [ ] 更新所属业务线 `README.md` 目录地图
- [ ] 更新 [INDEX.md](INDEX.md)
- [ ] 更新根 [../README.md](../README.md) / [../AGENTS.md](../AGENTS.md) 中的路径示例
- [ ] 检查 `media-cli.py`、`core/*.py` 注释中的示例路径
- [ ] 检查 `.claude/skills/**/*.md`、`CLAUDE.md` 中的路径与命名
- [ ] 遗留脚本（如旧绝对路径 shell）在 README「已知问题」中标注
