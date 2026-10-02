# AGENTS.md

## 项目

`personal-media-content` — AI 自媒体内容生产中台（自媒体域正本仓库）。Python 共享能力层 + 多条业务生产线（视频、小说、公众号、书评）。2026-10-02 起平台层完成架构升级：模型凭据收敛为根 `.env` 的 **Provider 注册表**、发布器统一为 **BasePublisher 契约**、CLI 拆包为 `cli/` 并新增 `doctor` 环境自检（详见 [ARCHITECTURE.md](ARCHITECTURE.md)）。

## 仓库关系

- 本仓库是 media 域**正本**，2026-10 自工作台 `D:\ai_person\p000_0000_it` 的 `media/` 三域分家而来；此后工作台 `media/` 不再是正本（工作台目录已重组，原名不存在）。
- 上游工作台保有 `it/`（行业）、`money/`（投资）两域与《工作台手册》，本仓库选题/素材取材可回溯工作台。
- 历史 git 提交信息沿用分家前工作台叙事（提及 it/media/money、《工作台手册》），以本文档与 README 现状为准，勿据提交信息推测目录。
- `blog/` 业务线已于 2026-10 删除，相关文档引用已清理。

## 先读什么

1. [README.md](README.md) — 全仓地图与 CLI
2. [docs/INDEX.md](docs/INDEX.md) — 文档总索引
3. [docs/DIRECTORY_STANDARD.md](docs/DIRECTORY_STANDARD.md) — 目录分层约定（含平台层结构）
4. [ARCHITECTURE.md](ARCHITECTURE.md) — Provider 注册表 / 发布契约 / CLI 细节

改某条业务线时，再读该线入口 README（见 README「业务线入口」表）。

## 目录约定（物理结构）

| 业务线 | 过程文档 | 正文/分析 | 说明/技能 | 素材与媒体 |
|--------|----------|-----------|-----------|------------|
| `hello_novel` | `novels/<书>/process/` | `novels/<书>/chapters/`（time_rift 为 `novel/chapters/`） | `CLAUDE.md`、`.claude/` | `source/`、`scripts/` |
| `hello_doubao_video` | `docs/` | — | `README.md` | `media/`（成片原件不入库）；`assets/` 运行时生成 |
| `hello_weixin_book` | — | `analyses/*.html` | `README.md`、`INDEX.md` | `assets/` |
| `hello_feishu` | `CLAUDE.md` | `articles/` | `README.md` | `videos/`、`output/`、`models/` 均为运行时生成，不入库 |
| `hello_webchat_*` | skills / config | `drafts/`、`output/`（output 运行时生成） | 各自 `README.md` / `CLAUDE.md` | 封面图等 |
| `family-life-video` | `人物特稿/` | `<主题>/短视频脚本.md`、`视频分镜脚本.md` | `README.md` | —（纯内容稿，无代码） |
| `publish_workbench` | — | — | `README.md` | `index.html` 单文件 APP（数据存浏览器 localStorage） |

平台层代码与数据：

- 能力：`core/`（模型接入在 `core/providers/`，发布契约在 `publisher_base.py`）
- 命令：`cli/commands/`（`media-cli.py` 只是薄入口）
- 看板：`dashboard/`（模板在 `dashboard/templates/`；默认仅绑 127.0.0.1）
- 单测：`tests/`（平台层 pytest，依赖 `requirements-dev.txt`）
- 统一存储/DB：`storage/`（由 `.env` 的 `STORAGE_*` 配置，默认 `storage/`；`db/` 与运行子目录不入库）
- 模型缓存：`models/`（运行时生成，不入库）

## 写作与修改规则

- 中文技术文档：定位 → 目录地图 → 常用命令/流程 → 文档索引 → 状态与已知问题。
- 更新结构时同步改：根 `README.md`、`docs/INDEX.md`、对应业务线 README。
- 文档中「运行时生成」的目录不手工创建、不提交；新的大文件类型（视频/模型/压缩包）先补 `.gitignore` 规则。
- 小说正文路径已重排为 `hello_novel/novels/<book>/chapters/`；旧文档中的 `8-正文/`、仓库根平铺 `8-续写-*.txt` 均已过时。
- 遗留脚本（写死分家前路径，如 `cangyuantu/scripts/*.sh`、`hello_feishu/scripts/batch_process.py`）文件头已有退役横幅，勿直接运行。
- 不要把密钥写进文档；模型凭据统一走根 `.env` 的 `PROVIDER_*` 注册表，官方号技能线走其 `aws.env`（均不入库）。

## 扩展清单（改架构时照此走）

**新增模型 provider**（换模型无需改代码）：
1. 根 `.env` 加一组 `PROVIDER_<ID>_API_KEY / _BASE_URL / _CHAT_MODEL(等能力后缀)`（同步 `.env.example`，键名写模板值、密钥留本地）
2. 能力指向：`LLM_PROVIDER / ASR_PROVIDER / IMAGE_PROVIDER = <ID>`
3. 验证：`python media-cli.py doctor --live`

**新增发布平台**：实现 `core/publisher_base.BasePublisher`（`publish_markdown` + 建议 `health_check`/`check_config`）→ 在 `publisher_base._load_publisher` 登记 → `doctor` 自动纳入体检。

**新增 CLI 命令**：在 `cli/commands/` 对应域模块加 `cmd_*` 与 `register()`；命令帮助同步 `cli/app.py` epilog 与 README。

**新增业务线**：建目录 + 入口 `README.md`（按 DIRECTORY_STANDARD 骨架）→ 登记 `cli/commands/status.py` 的 `BUSINESS_LINES` → 更新根 README 仓库地图/业务线表、`docs/INDEX.md`、`ARCHITECTURE.md` 目录树与依赖矩阵、本文件目录约定表。

## 常用命令

```bash
pip install -r requirements.txt            # 运行依赖
pip install -r requirements-dev.txt        # 测试依赖（pytest）
python media-cli.py doctor --live          # 环境自检 + 探活（接入/排障第一步）
python media-cli.py status
python media-cli.py dashboard start --port 5000
python media-cli.py asset scan novel --project 沧元图 \
  --dir ./hello_novel/novels/cangyuantu/chapters/
python -m pytest tests/                    # 平台层回归
```

## 状态快照（2026-10 梳理）

- 平台层：v3 架构（Provider 注册表 / 发布契约 / cli 包 / doctor）；模型全线小米 MiMo `mimo-v2.6-pro`（ASR `mimo-v2.5-asr`），已端到端验证
- `time_rift`《时间裂隙：2089》：600 章正文已完结，工作重心是修订；详见 `hello_novel/novels/time_rift/AGENTS.md`；修订期一次性脚本已归档至 `review/_archive_oneshot/`（勿运行）
- `cangyuantu` 沧元图续写：300 章正文在 `chapters/`
- `diff_life` 平凡人生：300 章正文在 `chapters/`
- `little_man` 普通人的一生：完整版 + 分章
- 已知外部依赖项：飞书发布需 `lark-cli auth login` 的 user 授权；公众号 API 需在后台把出口 IP 加入白名单（`doctor` 会给出精确指引）
