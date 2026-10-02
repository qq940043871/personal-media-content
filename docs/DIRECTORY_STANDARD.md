# 目录与文档规范

适用于本仓库所有业务线与平台层，保证「过程 / 内容 / 说明 / 素材」可分离、可检索。

## 0. 平台层结构（core / tools / cli / tests / dashboard / assets）

平台层代码与业务线分离，约定：

```
core/                # 对内能力层（被 import 的库）
├── providers/       # 模型接入（registry 解析 + llm/asr 客户端）——新模型能力放这里
└── （storage/task/asset/project/inventory/video/story 等域模块平铺）
tools/               # 对外动作层（发布工具，可独立运行；skill 化契约见 tools/README.md）
├── publisher_base.py + feishu/wechat/douyin_publisher.py + novel_publisher.py
└── asset_store.py   # 待发布资产库（状态流转）+ lark_helper.js
assets/              # 待发布资产库：平台 × drafts/published（tools 的数据契约，入库）
cli/commands/        # media-cli 的命令域，一域一模块，含 register(subparsers)
tests/               # 平台层 pytest；业务线手工冒烟脚本仍留在各线 tests/
dashboard/templates/ # 看板 HTML 模板（与 app.py 分离）
```

平台层变更规则：

- 新模型 provider：只改根 `.env` 注册表（见 `.env.example`），不改代码；新「能力类型」（如 tts）才动 `core/providers/registry.py`
- 新发布平台：实现 `tools/publisher_base.BasePublisher` 并在 `_load_publisher` 登记（完整步骤见 tools/README.md）
- 新 CLI 命令：在 `cli/commands/` 对应域模块加 `cmd_*` + `register()`；顶层入口 `media-cli.py` 不加业务逻辑
- 平台行为回归：`python -m pytest tests/`（依赖 `requirements-dev.txt`）

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

### assets/novels（创作资产：每本小说/主题一个文件夹）

```
assets/novels/
├── README.md
├── guides/                      # 通用方法与技巧（文集）
└── <book_id>/                   # 小说书目（含 chapters/ 或 novel/chapters/）
    ├── README.md                # 作品入口
    ├── CLAUDE.md / .claude/     # 技能与约定（若有）
    ├── process/                 # 选题、设定、大纲、审核
    ├── chapters/                # 章节正文（time_rift 为 novel/chapters/）
    ├── review/                  # 连贯性/质量审查（若有）
    ├── source/                  # 原著与合集
    ├── scripts/                 # 上传等脚本
    └── meta/                    # 总结与杂项
（无章节目录的子目录为主题/文集，如 人物特稿/、母亲的灶台/：短视频脚本与分镜稿）
```

### assets/douyin

```
assets/douyin/
├── README.md
├── docs/          # 提示词大全、合并方案
├── scripts/       # 去水印、合并 bat/py
├── assets/        # 帧图、去水印图（运行时生成，不入库）
└── media/         # merge_list.txt 入库；mp4 原件不入库
```

### hello_weixin_book（已迁出）

书评分析线已于 2026-10 整体迁出至上游 `personal-read-book` 仓库（含 analyses/*.html），
本仓不再维护该结构。

### .claude/skills 与 core（原 hello_wechat / hello_feishu，2026-10 并入）

- 技能包集中在根 `.claude/skills/<技能名>/`（含 SKILL.md 与自带脚本），入口见 `.claude/skills/README.md`
- 程序能力进 `core/`（如 `core/wechat_agent/`、`core/video_to_article.py`），生成稿进 `assets/` 或 `storage/`
- 凭据（`aws.env`、`.aws-article/config.yaml`）在仓库根，永不入库

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
