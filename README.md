# AI 自媒体内容生产中台

> 一站式 AI 内容生产：短视频 + 图文发布 + 长篇小说创作 + 书评分析  
> 本仓库是「自媒体域」正本，2026-10 从个人工作台 `p000_0000_it` 三域分家而来（工作台保有 it/money 两域与《工作台手册》）  
> 架构与协作约定见根目录 [ARCHITECTURE.md](ARCHITECTURE.md) / [AGENTS.md](AGENTS.md)

> **运行时目录说明**：`system/models/`、`system/storage/` 运行子目录、各业务线 `output/`、`videos/`、素材原件（mp4/模型缓存）等**不入库**，首次运行自动生成或需从本地磁盘同步（见 [.gitignore](.gitignore)）。下表标注「运行时」的目录在全新 clone 中不存在，属正常现象。

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
| `core/` | 对内能力层：配置、providers（模型注册表）、内容转化、素材、任务、项目、盘点（三平面共用底座） |
| `creation/` | 写平面·创作：AI agent 内容生产（`wechat_agent/` LangGraph 写作智能体）；技能包在 `.claude/skills/`（宿主约定路径） |
| `publishing/` | 写平面·出海：发布工具（飞书/公众号/抖音/小说批量），skill 化预备（见 publishing/README.md） |
| `cli/` | 命令实现包（`media-cli.py` 为薄入口；统一入口横跨三平面） |
| `workbench/` | 读平面：Web 数据看板 + 项目工作台（Flask，默认仅绑 127.0.0.1；首页创作统计，`/workbench` 工作台） |
| `media-cli.py` | 统一命令行入口 |
| `system/tests/` | 平台层 pytest（`pip install -r requirements-dev.txt` 后运行） |
| `system/models/` | 本地 ASR 等模型缓存（运行时生成，不入库） |
| `system/storage/` | 统一素材/任务数据库与产物根目录（`db/` 为本地运行库，不入库，可由 asset scan 重建） |
| `assets/` | **创作资产库**：按作品建工程、按平台做动作——`novels/`（小说工程）、`articles/`（图文→公众号）、`videos/`（短视频→抖音）、`wikis/`（知识库→飞书），工程内 drafts→published 状态流转（见 [assets/README.md](assets/README.md)）；也是 publishing/ 的数据契约 |
| `.claude/skills/` | 项目技能库：公众号官方文章技能线（15 个技能包，见其 README） |

业务线内部统一采用 **process（过程）/ chapters·analyses（内容）/ docs（说明）/ assets·media（素材）** 分层。

## 统一 CLI

```bash
# 启动器（双击 start.bat 出菜单；带参数则原样透传给 media-cli.py）
start.bat                # Windows：交互式菜单（自检/看板/资产库/发布/装依赖/测试）
start.bat doctor --live  # 透传：等价于 python media-cli.py doctor --live
./start.sh status        # Git Bash 同款菜单/透传

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
python media-cli.py douyin login        # 首次：扫码保存抖音登录态（Playwright）
python media-cli.py douyin publish --video-file video.mp4 --title "标题" --tags 生活 vlog
python media-cli.py douyin publish --video-file v.mp4 --title "标题" --draft  # 存草稿箱，App 内再发布
python media-cli.py publish --title "标题" --content-file article.md \
    --platforms feishu wechat
python media-cli.py publish --title "标题" --video video.mp4 \
    --platforms douyin

# 发布工具层（可独立运行，skill 化预备；资产发布成功自动归档）
python -m publishing.wechat publish --asset assets/articles/公众号/drafts/x.md --json
python -m publishing.feishu publish --asset "assets/wikis/我的知识库/drafts/x.md" --json
python -m publishing.douyin publish --asset assets/videos/douyin/drafts/v.mp4 --json
python media-cli.py asset init                          # 建齐资产库骨架（创作域×drafts/published）
python media-cli.py asset ls --type articles            # 待发布资产清单
python media-cli.py asset publish --file assets/articles/我的专栏/drafts/x.md
python media-cli.py video html2video src.html -o out.mp4  # HTML 动画页 → 视频（科普线，源稿在 assets/videos/kepu/source/）
python media-cli.py asset spaces                        # 飞书知识库映射

# 小说转化（章节正文在各作品 chapters/ 下）
python media-cli.py story script "assets/novels/沧元图续写/chapters/8-续写-第1章.txt" \
    -s 玄幻 -n 8 -o script.md
python media-cli.py story merge assets/novels/平凡人生/chapters \n    -o assets/novels/平凡人生/chapters-番茄版 --per 8 --target 2200  # 短章并长（单元边界优先）
python media-cli.py story article "assets/novels/沧元图续写/chapters/8-续写-第1章.txt" \
    --type deep -o article.md

# 素材 / 任务 / 看板 / 工作台
python media-cli.py asset scan novel --project 沧元图 \
    --dir ./assets/novels/沧元图续写/chapters/
python media-cli.py task stats
python media-cli.py dashboard start --port 5000
#   浏览器打开 http://localhost:5000/workbench → 新建/管理项目、编辑正文、发布三平台
```

## 内容资产转化链路

```
小说章节 (assets/novels/*/chapters)
    ├─→ story_to_script  → 分镜脚本 + AI 提示词 → 短视频
    ├─→ story_to_article → 深度解读/速读/人物 → 公众号 + 飞书
    └─→ novel_publisher  → 批量发布飞书知识库

教学视频 (system/storage/videos_input，media-cli.py pipeline video-article)
    └─→ 抽帧+抽音+ASR → 结构化文章 → 飞书

网文分析 → 已迁出至 personal-read-book 仓库（analyses/），本仓不再产出
```

## 业务线入口

| 业务线/资产 | 入口文档 | 一句话 |
|--------|----------|--------|
| 创作资产库 | [assets/README.md](assets/README.md) | 小说书目（novels/）、短视频线（douyin/）、发布资产与状态流转 |
| 视频→文章流水线 | `python media-cli.py pipeline video-article`（实现 [core/video_to_article.py](core/video_to_article.py)） | 教学视频抽帧/转写/成文 |
| 公众号技能线 | [.claude/skills/README.md](.claude/skills/README.md) | 选题→写作→配图→审稿→发布（技能包） |
| 公众号写作智能体 | [creation/wechat_agent/CLAUDE.md](creation/wechat_agent/CLAUDE.md) | LangGraph 智能体（`wechat compose`） |

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
| `FEISHU_WIKI_SPACES` | 飞书知识库映射（名称:space_id,...），资产按名移入对应知识库 | 飞书知识库发布 |
| `ASSETS_BASE` | 待发布资产库根目录（默认 `assets`） | 资产库 |
| `DOUYIN_COOKIES_FILE` / `DOUYIN_HEADLESS` / `DOUYIN_UPLOAD_TIMEOUT` | 抖音登录态与自动化参数（需先 `douyin login` 扫码；依赖 playwright） | 抖音发布 |
| `FFMPEG_PATH` | FFmpeg 路径 | 默认 `ffmpeg` |
| `ASR_LOCAL_ENABLED` | 本地 Whisper | 默认 false |

详见 [.env.example](.env.example) 与 [ARCHITECTURE.md](ARCHITECTURE.md) 第二节。官方号技能线凭据单独放在仓库根 `aws.env`（不入库，约定见 .claude/skills/README.md）。

## 更多文档

- [架构说明 ARCHITECTURE.md](ARCHITECTURE.md)
- [Agent 导航 AGENTS.md](AGENTS.md)
- 《工作台手册》：位于上游工作台 `D:\ai_person\p000_0000_it\it\knowledge-base\pages\00_overview\工作台手册.md`（三域归属决策表、发布流程、Git 约定；跨仓文档，不在本仓库）
