# AGENTS.md

## 项目

`p000_0000_media` — AI 自媒体内容生产中台。Python 共享能力层 + 多条业务生产线（视频、小说、公众号、书评）。

## 先读什么

1. [README.md](README.md) — 全仓地图与 CLI
2. [docs/INDEX.md](docs/INDEX.md) — 文档总索引
3. [docs/DIRECTORY_STANDARD.md](docs/DIRECTORY_STANDARD.md) — 目录分层约定
4. [ARCHITECTURE.md](ARCHITECTURE.md) — core / dashboard / CLI 细节

改某条业务线时，再读该线入口 README（见 README「业务线入口」表）。

## 目录约定（物理结构）

| 业务线 | 过程文档 | 正文/分析 | 说明/技能 | 素材与媒体 |
|--------|----------|-----------|-----------|------------|
| `hello_novel` | `novels/<书>/process/` | `novels/<书>/chapters/` | `CLAUDE.md`、`.claude/` | `source/`、`scripts/` |
| `hello_doubao_video` | `docs/` | — | `README.md` | `assets/`、`media/` |
| `hello_weixin_book` | — | `analyses/*.html` | `README.md`、`INDEX.md` | `assets/` |
| `hello_feishu` | `CLAUDE.md` | `output/`、`articles/` | `README.md` | `videos/`、`models/` |
| `hello_webchat_*` | skills / config | `drafts/`、`output/` | 各自 `README.md` / `CLAUDE.md` | 封面图等 |

平台层代码与数据：

- 能力：`core/`
- 看板：`dashboard/`
- 统一存储/DB：`storage/`（由 `.env` 的 `STORAGE_*` 配置，默认 `storage/`）
- 模型缓存：`models/`
- CLI：`media-cli.py`

## 写作与修改规则

- 中文技术文档：定位 → 目录地图 → 常用命令/流程 → 文档索引 → 状态与已知问题。
- 更新结构时同步改：根 `README.md`、`docs/INDEX.md`、对应业务线 README。
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

## 状态快照（整理时）

- `time_rift`《时间裂隙：2089》：600 章正文已完结，工作重心是修订；详见 `hello_novel/novels/time_rift/AGENTS.md`
- `cangyuantu` 沧元图续写：300 章正文在 `chapters/`
- `diff_life` 平凡人生：300 章正文在 `chapters/`
- `little_man` 普通人的一生：完整版 + 分章
