# AI 自媒体内容生产中台

> 一站式 AI 内容生产：短视频 + 图文发布 + 长篇小说创作 + 书评分析  
> 本仓库是「自媒体域」正本，2026-10 从个人工作台 `p000_0000_it` 三域分家而来（工作台保有 it/money 两域与《工作台手册》）  
> 文档体系见 [docs/INDEX.md](docs/INDEX.md)

> **运行时目录说明**：`models/`、`storage/` 运行子目录、各业务线 `output/`、`videos/`、素材原件（mp4/模型缓存）等**不入库**，首次运行自动生成或需从本地磁盘同步（见 [.gitignore](.gitignore)）。下表标注「运行时」的目录在全新 clone 中不存在，属正常现象。

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env   # 填入 Provider 注册表（PROVIDER_MIMO_API_KEY 等）
python media-cli.py doctor        # 环境自检：配置/依赖/数据库
python media-cli.py doctor --live # 加做探活：LLM 实调 + 发布平台健康检查
python media-cli.py status
```

## 仓库地图

| 目录 | 角色 |
|------|------|
| `core/` | 共享能力层：配置、providers（模型注册表）、发布契约、素材、任务 |
| `cli/` | 命令实现包（`media-cli.py` 为薄入口） |
| `dashboard/` | Web 数据看板（Flask，默认仅绑 127.0.0.1） |
| `media-cli.py` | 统一命令行入口 |
| `tests/` | 平台层 pytest（`pip install -r requirements-dev.txt` 后运行） |
| `models/` | 本地 ASR 等模型缓存（运行时生成，不入库） |
| `storage/` | 统一素材/任务数据库与产物根目录（`db/` 为本地运行库，不入库，可由 asset scan 重建） |
| `docs/` | 全仓文档索引与规范 |
| `hello_doubao_video/` | 短视频生产线（豆包 + FFmpeg） |
| `hello_feishu/` | 教学视频 → 飞书知识库流水线 |
| `hello_novel/` | 小说创作生产线（多部作品） |
| `hello_webchat_official/` | 公众号官方文章技能流水线 |
| `hello_webchat_solo/` | 公众号智能写作助手（独立程序） |
| `hello_weixin_book/` | 网文/书籍分析 HTML 产出 |
| `family-life-video/` | 家庭亲情短视频内容稿（口播/分镜，纯内容资产） |
| `publish_workbench/` | 发布工作台（公众号/抖音/飞书发布跟踪，单文件 HTML APP） |

业务线内部统一采用 **process（过程）/ chapters·analyses（内容）/ docs（说明）/ assets·media（素材）** 分层，详见 [docs/DIRECTORY_STANDARD.md](docs/DIRECTORY_STANDARD.md)。

## 统一 CLI

```bash
python media-cli.py status
python media-cli.py doctor --live   # 环境自检 + LLM/发布平台探活

# 视频
python media-cli.py video info video.mp4
python media-cli.py video merge v1.mp4 v2.mp4 -o full.mp4 --fade
python media-cli.py video extract frames video.mp4 out/frames/
python media-cli.py video extract audio video.mp4 out/audio/

# 转写 / 大模型
python media-cli.py asr transcribe audio.mp3 --local --srt
python media-cli.py llm chat "写一首关于秋天的诗"

# 发布
python media-cli.py feishu publish --title "标题" --content-file article.md
python media-cli.py wechat publish --title "标题" --content-file article.md
python media-cli.py publish --title "标题" --content-file article.md \
    --platforms feishu wechat

# 小说转化（章节正文在各作品 chapters/ 下）
python media-cli.py story script "hello_novel/novels/cangyuantu/chapters/8-续写-第1章.txt" \
    -s 玄幻 -n 8 -o script.md
python media-cli.py story article "hello_novel/novels/cangyuantu/chapters/8-续写-第1章.txt" \
    --type deep -o article.md

# 素材 / 任务 / 看板
python media-cli.py asset scan novel --project 沧元图 \
    --dir ./hello_novel/novels/cangyuantu/chapters/
python media-cli.py task stats
python media-cli.py dashboard start --port 5000
```

## 内容资产转化链路

```
小说章节 (hello_novel/novels/*/chapters)
    ├─→ story_to_script  → 分镜脚本 + AI 提示词 → 短视频
    ├─→ story_to_article → 深度解读/速读/人物 → 公众号 + 飞书
    └─→ novel_publisher  → 批量发布飞书知识库

教学视频 (hello_feishu/videos)
    └─→ 抽帧+抽音+ASR → 结构化文章 → 飞书

网文分析 (hello_weixin_book/analyses)
    └─→ HTML 深度分析稿（阅读/选题素材）
```

## 业务线入口

| 业务线 | 入口文档 | 一句话 |
|--------|----------|--------|
| 短视频 | [hello_doubao_video/README.md](hello_doubao_video/README.md) | 分镜提示词 + 合并导出 |
| 视频转飞书 | [hello_feishu/README.md](hello_feishu/README.md) | 教学视频流水线 |
| 小说创作 | [hello_novel/README.md](hello_novel/README.md) | 多部小说的过程与正文 |
| 公众号官方 | [hello_webchat_official/README.md](hello_webchat_official/README.md) | 技能驱动写稿 |
| 公众号 Solo | [hello_webchat_solo/README.md](hello_webchat_solo/README.md) | 独立写作程序 |
| 书评分析 | [hello_weixin_book/README.md](hello_weixin_book/README.md) | 网文分析 HTML |
| 亲情短视频稿 | [family-life-video/README.md](family-life-video/README.md) | 人物特稿 + 口播/分镜脚本（内容资产） |
| 发布工作台 | [publish_workbench/README.md](publish_workbench/README.md) | 三平台发布状态跟踪 + 日历 + 清单（本地单文件 APP） |

## 配置

模型凭据统一放在根 `.env` 的 **Provider 注册表**（换模型只改这一处，业务线自动跟随）：

```env
PROVIDER_MIMO_API_KEY=...             # 每个平台一组 PROVIDER_<ID>_*
PROVIDER_MIMO_BASE_URL=https://api.xiaomimimo.com/v1
PROVIDER_MIMO_CHAT_MODEL=mimo-v2.6-pro
PROVIDER_MIMO_ASR_MODEL=mimo-v2.5-asr
LLM_PROVIDER=mimo                     # 各能力指向某个 <ID>
ASR_PROVIDER=mimo
IMAGE_PROVIDER=ark
```

| 配置项 | 说明 | 必填 |
|--------|------|------|
| `PROVIDER_<ID>_*` + `LLM/ASR/IMAGE_PROVIDER` | 模型注册表 | 是（生成能力） |
| `WECHAT_APP_ID` / `WECHAT_APP_SECRET` | 公众号凭证 | 公众号发布 |
| `FEISHU_APP_ID` / `FEISHU_APP_SECRET` | 飞书应用凭证（走 lark-cli 时可不填） | 飞书应用 API |
| `LARK_CLI_RUN_JS` | lark-cli 路径 | 飞书发布 |
| `FFMPEG_PATH` | FFmpeg 路径 | 默认 `ffmpeg` |
| `ASR_LOCAL_ENABLED` | 本地 Whisper | 默认 false |

详见 [.env.example](.env.example) 与 [ARCHITECTURE.md](ARCHITECTURE.md) 第二节。官方号技能线凭据单独放在 `hello_webchat_official/aws.env`（不入库）。

## 更多文档

- [架构说明 ARCHITECTURE.md](ARCHITECTURE.md)
- [Agent 导航 AGENTS.md](AGENTS.md)
- [文档总索引 docs/INDEX.md](docs/INDEX.md)
- [目录规范 docs/DIRECTORY_STANDARD.md](docs/DIRECTORY_STANDARD.md)
- 《工作台手册》：位于上游工作台 `D:\ai_person\p000_0000_it\it\knowledge-base\pages\00_overview\工作台手册.md`（三域归属决策表、发布流程、Git 约定；跨仓文档，不在本仓库）
