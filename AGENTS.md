# AGENTS.md

## 项目

`personal-media-content` — AI 自媒体内容生产中台（自媒体域正本仓库）。Python 共享能力层 + 多条业务生产线（视频、小说、公众号、书评）。2026-10-02 起平台层完成架构升级：模型凭据收敛为根 `.env` 的 **Provider 注册表**、发布器统一为 **BasePublisher 契约**、CLI 拆包为 `cli/` 并新增 `doctor` 环境自检；同日重构为 **core（能力库）/ tools（发布工具，skill 化预备）/ assets（待发布资产库）** 三层（详见 [ARCHITECTURE.md](ARCHITECTURE.md)）。

## 仓库关系

- 本仓库是 media 域**正本**，2026-10 自工作台 `D:\ai_person\p000_0000_it` 的 `media/` 三域分家而来；此后工作台 `media/` 不再是正本（工作台目录已重组，原名不存在）。
- 上游工作台保有 `it/`（行业）、`money/`（投资）两域与《工作台手册》，本仓库选题/素材取材可回溯工作台。
- 历史 git 提交信息沿用分家前工作台叙事（提及 it/media/money、《工作台手册》），以本文档与 README 现状为准，勿据提交信息推测目录。
- `blog/` 业务线已于 2026-10 删除，相关文档引用已清理。

## 先读什么

1. [README.md](README.md) — 全仓地图与 CLI
2. [ARCHITECTURE.md](ARCHITECTURE.md) — 平台架构：Provider 注册表 / 发布契约 / CLI 细节

改某条业务线时，再读该线入口 README（见 README「业务线入口」表）。

## 目录约定（物理结构）

| 业务线/资产 | 过程文档 | 正文/分析 | 说明/技能 | 素材与媒体 |
|--------|----------|-----------|-----------|------------|
| `assets/novels/<书>` | `<书>/process/`、`review/` | `<书>/chapters/`（time_rift 为 `novel/chapters/`） | `CLAUDE.md`、`.claude/` | `source/`、`scripts/`、`meta/` |
| `assets/novels/<主题>` | — | `<主题>/短视频脚本.md`、`视频分镜脚本.md` | — | 亲情视频主题与 guides 文集 |
| `assets/<类型>/<工程>` | `drafts/` | `published/`（+meta.json） | assets/README.md | 类型 = novels/articles/videos/wikis |
| `assets/videos/douyin` | `docs/`、`scripts/` | — | `README.md` | `media/`（成片原件不入库）；`assets/` 运行时生成 |
| `.claude/skills/`（公众号技能线） | — | `assets/articles/公众号/drafts/<篇名>/` | 各技能 `SKILL.md` | `aws.env`、`.aws-article/` 在仓库根（不入库） |

> 书评分析线（hello_weixin_book）已于 2026-10 整体迁出至上游 `personal-read-book` 仓库，本仓不再维护。

平台层代码与数据（概念分层：**读平面看板 / 写平面创作与发布 / 共用能力底座与数据**）：

- 能力：`core/`（对内能力层，被 import 的库：模型接入在 `core/providers/`、转化/存储/任务/项目/盘点——三平面共用底座）
- 创作：`creation/`（写平面·AI agent 内容生产：`creation/wechat_agent` 写作智能体；技能包在 `.claude/skills/`——物理位置受 Agent 宿主约定固定，逻辑上属创作平面）
- 发布：`publishing/`（写平面·出海：发布契约在 `publishing/publisher_base.py`，三个平台发布器 + 小说批量发布 + 资产库 `asset_store.py`；skill 化契约见 publishing/README.md）
- 资产库：`assets/`（创作域/工程 × drafts/published 状态流转；发布成功自动归档 + meta.json；结构见 assets/README.md）
- 命令：`cli/commands/`（`media-cli.py` 只是薄入口；统一入口横跨三平面，不按概念拆）
- 看板与工作台：`workbench/`（读平面：模板在 `workbench/templates/`；默认仅绑 127.0.0.1；首页为创作统计 `/api/inventory` 盘点小说/资产/稿件，`/workbench` 项目工作台，项目数据在 `system/storage/db/projects.db`）
- 启动器：`start.bat`（Windows 双击出菜单）/ `start.sh`（Git Bash）；带参数时原样透传给 `media-cli.py`；两者都会自动挑「能 import dotenv」的解释器（本机 `python` 指向缺依赖的托管版，实际依赖在 anaconda）
- 单测：`system/tests/`（平台层 pytest，依赖 `requirements-dev.txt`）
- 统一存储/DB：`system/storage/`（由 `.env` 的 `STORAGE_*` 配置，默认 `system/storage/`；`db/` 与运行子目录不入库）
- 模型缓存：`system/models/`（运行时生成，不入库）

## 写作与修改规则

- 中文技术文档：定位 → 目录地图 → 常用命令/流程 → 文档索引 → 状态与已知问题。
- 更新结构时同步改：根 `README.md`、`ARCHITECTURE.md`、对应业务线 README。
- 文档中「运行时生成」的目录不手工创建、不提交；新的大文件类型（视频/模型/压缩包）先补 `.gitignore` 规则。
- 小说正文路径已重排为 `assets/novels/<book>/chapters/`；旧文档中的 `8-正文/`、仓库根平铺 `8-续写-*.txt` 均已过时。
- 遗留脚本（写死分家前路径，如 `cangyuantu/scripts/*.sh`）文件头已有退役横幅，勿直接运行。
- 不要把密钥写进文档；模型凭据统一走根 `.env` 的 `PROVIDER_*` 注册表，官方号技能线走其 `aws.env`（均不入库）。

## 扩展清单（改架构时照此走）

**新增模型 provider**（换模型无需改代码）：
1. 根 `.env` 加一组 `PROVIDER_<ID>_API_KEY / _BASE_URL / _CHAT_MODEL(等能力后缀)`（同步 `.env.example`，键名写模板值、密钥留本地）
2. 能力指向：`LLM_PROVIDER / ASR_PROVIDER / IMAGE_PROVIDER = <ID>`
3. 验证：`python media-cli.py doctor --live`

**新增发布平台**：实现 `publishing/publisher_base.BasePublisher`（`publish_markdown` + 建议 `health_check`/`check_config`）→ 在 `publishing/publisher_base._load_publisher` 登记 → `doctor` 自动纳入体检；创作域与默认平台约定见 `publishing/asset_store.ASSET_TYPES` / `TYPE_PLATFORM`（完整步骤见 publishing/README.md）。

**新增 CLI 命令**：在 `cli/commands/` 对应域模块加 `cmd_*` 与 `register()`；命令帮助同步 `cli/app.py` epilog 与 README。

**新增能力/技能**：能力进 `core/`（库）或 `publishing/`（可运行工具，按其接口契约）；技能包放 `.claude/skills/`；内容资产进 `assets/`。若确需新业务线目录才登记 `cli/commands/status.py` 的 `BUSINESS_LINES`；文档同步根 README、`ARCHITECTURE.md`、本文件。

## 常用命令

```bash
start.bat                                  # Windows 启动器：双击出菜单，带参数则透传 media-cli.py
./start.sh status                          # Git Bash 启动器（同款菜单/透传）
pip install -r requirements.txt            # 运行依赖
pip install -r requirements-dev.txt        # 测试依赖（pytest）
python media-cli.py doctor --live          # 环境自检 + 探活（接入/排障第一步）
python media-cli.py status
python media-cli.py dashboard start --port 5000
python media-cli.py asset scan novel --project 沧元图 \
  --dir ./assets/novels/cangyuantu/chapters/
python media-cli.py asset init               # 建齐资产库骨架（wechat/douyin 各一个、feishu 按知识库、novels 按书名）
python media-cli.py asset ls --json          # 待发布资产库清单
python media-cli.py asset publish --file assets/articles/我的专栏/drafts/x.md   # 发布并自动归档
python -m pytest system/tests/                    # 平台层回归
```

## 状态快照（2026-10 梳理）

- 平台层：v3 架构（Provider 注册表 / 发布契约 / cli 包 / doctor）；模型全线小米 MiMo `mimo-v2.6-pro`（ASR `mimo-v2.5-asr`），已端到端验证
- `time_rift`《时间裂隙：2089》：600 章正文已完结，工作重心是修订；详见 `assets/novels/time_rift/AGENTS.md`；修订期一次性脚本已归档至 `review/_archive_oneshot/`（勿运行）
- `cangyuantu` 沧元图续写：300 章正文在 `chapters/`
- `diff_life` 平凡人生：300 章正文在 `chapters/`
- `little_man` 普通人的一生：完整版 + 分章
- 已知外部依赖项：飞书发布需 `lark-cli auth login` 的 user 授权；公众号 API 需在后台把出口 IP 加入白名单；抖音发布为 Playwright 自动化（`pip install playwright && playwright install chromium` + `media-cli.py douyin login` 扫码，登录态 Cookie 在 `system/storage/douyin/` 不入库，发布时默认弹出浏览器窗口）（`doctor` 会给出精确指引）
