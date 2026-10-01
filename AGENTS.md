# AGENTS.md

## 项目

`personal-media-content` — AI 自媒体内容生产中台（自媒体域正本仓库）。Python 共享能力层 + 多条业务生产线（视频、小说、公众号、书评）+ 个人博客。

## 仓库关系

- 本仓库是 media 域**正本**，2026-10 自工作台 `D:\ai_person\p000_0000_it` 的 `media/` 三域分家而来；此后工作台 `media/` 不再是正本。
- 上游工作台保有 `it/`（行业）、`money/`（投资）两域与《工作台手册》（位于 `it/knowledge-base/pages/00_overview/工作台手册.md`），本仓库选题/素材取材可回溯工作台。
- `blog/_seed/` 生成脚本依赖工作台知识库路径（可用环境变量 `KB_ROOT` 覆盖），在全新 clone 中需先配置。
- 历史 git 提交信息沿用分家前工作台叙事（提及 it/media/money、《工作台手册》），以本文档与 README 现状为准，勿据提交信息推测目录。

## 先读什么

1. [README.md](README.md) — 全仓地图与 CLI
2. [docs/INDEX.md](docs/INDEX.md) — 文档总索引
3. [docs/DIRECTORY_STANDARD.md](docs/DIRECTORY_STANDARD.md) — 目录分层约定
4. [ARCHITECTURE.md](ARCHITECTURE.md) — core / dashboard / CLI 细节

改某条业务线时，再读该线入口 README（见 README「业务线入口」表）。

## 目录约定（物理结构）

| 业务线 | 过程文档 | 正文/分析 | 说明/技能 | 素材与媒体 |
|--------|----------|-----------|-----------|------------|
| `hello_novel` | `novels/<书>/process/` | `novels/<书>/chapters/`（time_rift 为 `novel/chapters/`） | `CLAUDE.md`、`.claude/` | `source/`、`scripts/` |
| `hello_doubao_video` | `docs/` | — | `README.md` | `media/`（成片原件不入库）；`assets/` 运行时生成 |
| `hello_weixin_book` | — | `analyses/*.html` | `README.md`、`INDEX.md` | `assets/` |
| `hello_feishu` | `CLAUDE.md` | `articles/` | `README.md` | `videos/`、`output/`、`models/` 均为运行时生成，不入库 |
| `hello_webchat_*` | skills / config | `drafts/`、`output/`（output 运行时生成） | 各自 `README.md` / `CLAUDE.md` | 封面图等 |

平台层代码与数据：

- 能力：`core/`
- 看板：`dashboard/`
- 统一存储/DB：`storage/`（由 `.env` 的 `STORAGE_*` 配置，默认 `storage/`；`db/` 与运行子目录不入库）
- 模型缓存：`models/`（运行时生成，不入库）
- CLI：`media-cli.py`

## 写作与修改规则

- 中文技术文档：定位 → 目录地图 → 常用命令/流程 → 文档索引 → 状态与已知问题。
- 更新结构时同步改：根 `README.md`、`docs/INDEX.md`、对应业务线 README。
- 文档中「运行时生成」的目录不手工创建、不提交；新的大文件类型（视频/模型/压缩包）先补 `.gitignore` 规则。
- 小说正文路径已重排为 `hello_novel/novels/<book>/chapters/`；旧文档中的 `8-正文/`、仓库根平铺 `8-续写-*.txt` 均已过时。
- `cangyuantu/scripts/*.sh` 仍指向历史路径 `D:/ai_coder/p000_000_cangyuantu`，属遗留脚本，使用前需改路径。
- 不要把密钥写进文档；配置走 `.env`（已有 `.env.example`）。

## 常用命令

```bash
pip install -r requirements.txt
python media-cli.py status
python media-cli.py dashboard start --port 5000
python media-cli.py asset scan novel --project 沧元图 \
  --dir ./hello_novel/novels/cangyuantu/chapters/
```

## 状态快照（2026-10 梳理）

- `time_rift`《时间裂隙：2089》：600 章正文已完结，工作重心是修订；详见 `hello_novel/novels/time_rift/AGENTS.md`；修订期一次性脚本已归档至 `review/_archive_oneshot/`（勿运行）
- `cangyuantu` 沧元图续写：300 章正文在 `chapters/`
- `diff_life` 平凡人生：300 章正文在 `chapters/`
- `little_man` 普通人的一生：完整版 + 分章
