# AI 自媒体内容生产中台 — 架构说明

> 版本：v3.0（Provider 注册表 + 发布契约 + CLI 包化）  
> 更新：2026-10-02  
> 仓库：`personal-media-content`（自媒体域正本；2026-10 自工作台 `p000_0000_it` 的 `media/` 分家而来）

## 一、整体架构

```
personal-media-content/
│
├── core/                          ← 对内能力层（被 import 的库）
│   ├── config.py                  # 统一配置（根 .env；LLM/ASR 属性由注册表推导，旧键回落）
│   ├── providers/                 # ★ 模型接入层：凭据唯一存放处 + 工厂
│   │   ├── registry.py            #   PROVIDER_* 环境变量解析 → resolve('chat'|'asr'|'image')
│   │   ├── llm.py                 #   LLMClient + get_llm_client（OpenAI 兼容，端点自动补全）
│   │   └── asr.py                 #   ASRClient（云端 input_audio / 本地 faster-whisper）
│   ├── project_manager.py         #   工作台项目模型 + 发布记录（SQLite storage/db/projects.db）
│   ├── inventory.py               #   内容资产盘点：小说/资产/稿件/成片/发布记录统计（创作统计页数据源）
│   ├── story_to_script.py         #   小说→分镜
│   ├── story_to_article.py        #   小说→文章
│   ├── video_to_article.py        #   教学视频→文章流水线（原 hello_feishu；编排/成文/配图/转写落盘）
│   ├── wechat_agent/              #   公众号写作智能体（原 hello_wechat/solo；LangGraph，凭据回落根 .env）
│   ├── asset_manager.py           #   素材资产（SQLite storage/db/assets.db）
│   ├── task_manager.py            #   任务调度（SQLite storage/db/tasks.db）
│   ├── storage.py                 #   路径与存储工具
│   └── video_toolkit.py           #   FFmpeg 封装
│
├── tools/                         ← 对外动作层（发布工具，skill 化预备；接口契约见 tools/README.md）
│   ├── publisher_base.py          # ★ 发布契约：PublishResult + BasePublisher + 按名注册
│   ├── feishu_publisher.py        #   飞书发布（lark_helper.js 桥接；支持按知识库移入）
│   ├── wechat_publisher.py        #   公众号发布（MD→HTML、草稿、发布）
│   ├── douyin_publisher.py        #   抖音发布（Playwright 自动化创作者后台，登录态 Cookie）
│   ├── novel_publisher.py         #   小说批量飞书发布（幂等记录在 storage/db/）
│   ├── asset_store.py             #   资产库读写与状态流转（drafts → published + meta.json）
│   └── lark_helper.js             #   lark-cli 桥接（auth-status / create-doc / insert-image / move-to-wiki）
│
├── assets/                        ← 创作资产库（novels/ 每本小说一个文件夹、douyin/ 视频线、wechat/feishu 发布资产 drafts/published）
│
├── cli/                           ← 命令实现包（media-cli.py 只是薄入口）
│   ├── app.py                     #   解析器组装
│   └── commands/                  #   status / doctor / video / ai / publish / story /
│                                  #   asset / task / storage / dashboard 各域一模块
│
├── dashboard/                     ← Web 看板 + 项目工作台（Flask + templates/*.html；默认仅绑 127.0.0.1）
├── media-cli.py                   ← 统一 CLI 入口
├── tests/                         ← 平台层 pytest（注册表/发布契约/资产库/doctor/CLI/项目工作台）
├── models/                        ← 模型缓存（运行时生成，不入库）
├── storage/                       ← 统一产物/数据库根（db/ 与运行子目录不入库）
├── docs/                          ← 文档索引与目录规范
│
├── .claude/skills/                ← 项目技能库（公众号官方文章技能线 15 个技能包）
（2026-10 收敛：业务线全部并入主工程——内容进 assets/、能力进 core/、技能进 .claude/skills/；
 hello_weixin_book 书评线迁出至上游 personal-read-book；hello_feishu / hello_wechat 归档于 docs/_archive/）
```

业务线物理分层规范见 [docs/DIRECTORY_STANDARD.md](docs/DIRECTORY_STANDARD.md)。

## 二、模型 Provider 注册表（v3 核心变化）

**全仓模型凭据唯一存放在根 `.env` 的 `PROVIDER_*` 段**，换模型只改这一处，所有业务线自动跟随：

```env
PROVIDER_MIMO_API_KEY=...            # 密钥
PROVIDER_MIMO_BASE_URL=https://api.xiaomimimo.com/v1
PROVIDER_MIMO_CHAT_MODEL=mimo-v2.6-pro      # 模型按能力加后缀
PROVIDER_MIMO_ASR_MODEL=mimo-v2.5-asr       #   _CHAT_MODEL / _ASR_MODEL / _IMAGE_MODEL
PROVIDER_ARK_IMAGE_URL=.../images/generations  # 图像端点可单独覆盖

LLM_PROVIDER=mimo    # 对话能力用谁
ASR_PROVIDER=mimo    # 转写能力用谁
IMAGE_PROVIDER=ark   # 生图能力用谁
```

- 解析入口：`core.providers.registry.resolve(task)`，任务 ∈ `chat / asr / image`。
- 旧键（`LLM_API_KEY/URL/MODEL`、`ASR_*`）作为回退保留：注册表缺某能力时生效。
- 消费方：`core/llm_client.py` 与 `core/asr_client.py` 为兼容 shim（实现已在 `core/providers/`）；`core/wechat_agent` 的 Settings 未显式配置时回落注册表。
- 验证：`python media-cli.py doctor --live`（静态检查 + LLM 实调 + 发布平台健康检查）。

新增 provider 步骤：根 `.env` 加一组 `PROVIDER_<ID>_*` 键 → 对应能力 `<X>_PROVIDER=<ID>` → `doctor` 验证。无需改任何代码。

## 三、工具层与发布契约（v3 核心）

- **tools/ = 对外动作层**（发布类工具，每个可独立运行、未来逐个封装成 skills，接口契约见 tools/README.md）；**core/ = 对内能力层**（被 import 的库）。分层方向：tools → core，反向不依赖。
- `tools/publisher_base.py`：`PublishResult`（统一结果对象，兼容 dict 访问）+ `BasePublisher`（子类实现 `publish_markdown(title, content_md, options) -> PublishResult`，可选 `health_check()`/`check_config()`）+ `MultiPlatformPublisher`（按名发现已登记平台，未配置平台记入 `init_errors` 而不崩溃；`health_check_all()` 批量体检，doctor 复用）。
- 已登记平台：`feishu` / `wechat`（API 类）+ `douyin`（Playwright 自动化创作者后台，无个人发布 API；登录态 Cookie 在 `storage/douyin/`，不入库；`options['video']` 传视频，图文契约下 markdown 正文不上传）。
- **资产库（assets/）**：`tools/asset_store.AssetStore` 管理平台 × `drafts/published` 的状态流转——发布成功自动移入 `published/` 并写 `<文件名>.meta.json`；飞书支持 `FEISHU_WIKI_SPACES=名称:space_id,...` 按知识库移入。同篇内容发多平台按目标各放一份。
- 独立命令入口（`--json` + 退出码 0/1，skill 化契约）：`python -m tools.wechat|feishu|douyin publish --asset <路径>`、`python -m tools.asset_store ls|put|publish|spaces`。
- 新增发布平台：实现 `tools.publisher_base.BasePublisher` → 在 `publisher_base._load_publisher` 登记一条 → CLI/doctor 自动纳入（步骤见 tools/README.md）。

## 四、核心能力层（2.x）

### 4.1 config.py

全局一次加载根 `.env`。存储默认：`storage/{videos_input,videos_output,articles,novels}`；`storage/db/` 为 SQLite 运行库（不入库，可重建）。平台素材库 `storage/novels` **独立于** 内容资产库 `assets/novels/`（前者是 SQLite 索引的素材，后者是正文与过程稿）。

### 4.2 内容转化

- `story_to_script.py`：6 种风格分镜 + AI 提示词
- `story_to_article.py`：deep / summary / character / worldview
- `tools/novel_publisher.py`：幂等批量发飞书（发布记录在 `storage/db/feishu_published.json`）

输入章节使用现行路径，如 `assets/novels/cangyuantu/chapters/8-续写-第1章.txt`。

### 4.3 资产与任务

- `asset_manager.py`：标签、关联、扫描章节目录
- `task_manager.py`：pending → running → done/failed/skipped，重试与日志
- `project_manager.py`：工作台项目模型（article/novel/video）+ 发布记录（running → success/failed），SQLite `storage/db/projects.db`
- `inventory.py`：创作统计盘点——扫描 `assets/novels/`（书目按 `chapters/` 与 `novel/chapters/` 两代布局；无章节目录的子目录计为主题/文集）、发布资产 `assets/**/drafts|published`，汇总发布记录；带 mtime 签名缓存
- `storage.py`：路径快捷与幂等检查

### 4.4 video_toolkit.py

信息、抽帧、抽音、无损合并、淡入淡出合并、格式转换。

## 五、统一 CLI

```
status / doctor / video / asr / llm / feishu / wechat / publish
story / asset / task / storage / dashboard
```

`doctor` 是环境自检入口：`.env`/注册表/存储可写/ffmpeg/node/lark-cli/数据库；`--live` 加做 LLM 实调与飞书/微信健康检查（微信 IP 白名单、lark-cli 授权等会给出修复指引）；`--json` 供 Agent 消化。

## 六、Web 数据看板

```bash
python media-cli.py dashboard start --port 5000
```

| 页面 | 路径 | 功能 |
|------|------|------|
| 总览 | `/` | 任务/素材统计、最近任务 |
| 任务中心 | `/tasks` | 筛选、详情、重试 |
| 素材库 | `/assets` | 标签与检索 |

技术栈：Flask + 原生前端（模板在 `dashboard/templates/`）。默认绑定 `127.0.0.1`（可用 `DASHBOARD_HOST` 覆盖），看板无鉴权，勿暴露公网。

## 七、内容转化链路

```
assets/novels/*/chapters
    ├─ story_to_script  → 分镜 + 提示词 → 视频生成
    ├─ story_to_article → 公众号/飞书文章
    └─ novel_publisher  → 飞书知识库

storage/videos_input → pipeline video-article（core/video_to_article）→ 飞书文章
assets/novels/<主题> → 分镜/口播稿 → assets/douyin 成片（规划中）
（书评分析已迁 personal-read-book 仓库）
.claude/skills + core/wechat_agent → 公众号成稿（assets/wechat/drafts/<篇名>/）
```

## 八、业务线与平台边界

| 业务线 | 是否依赖 core | 说明 |
|--------|---------------|------|
| assets/（novels·douyin·主题） | 转化时 | 创作目录自治；发布/改写走 CLI 与 tools/ |
| core/wechat_agent | 共享注册表 | LangGraph 智能体（原 hello_wechat/solo）；LLM/生图/微信凭据回落根 `.env` |
| .claude/skills（公众号技能线） | 可选 | 技能包自治（凭据在根 `aws.env`）；发布可复用 tools/wechat_publisher |

## 九、质量底线

- 平台层单测：`pip install -r requirements-dev.txt && python -m pytest tests/`（注册表解析、发布契约、doctor 结构、CLI 注册）。
- 业务线 `tests/` 为手工冒烟脚本（按各线 README 运行），平台行为回归以根 `tests/` 为准。
- 变更检查清单见 [docs/DIRECTORY_STANDARD.md](docs/DIRECTORY_STANDARD.md)。

## 十、兼容与迁移

- 本仓库 2026-10 自工作台 `p000_0000_it` 的 `media/` 三域分家而来，是自媒体域正本；历史提交信息中的三域叙事以文档现状为准。
- 业务线**顶层目录名**（`hello_*` 等）保持不变。
- v2 → v3 迁移：`blog/` 已删除；模型凭据从各线散置收敛到根 `.env` 注册表（旧键仍可回退）；`core/llm_client.py`、`core/asr_client.py` 变为 shim，旧导入不受影响；`media-cli.py` 拆包为 `cli/`，命令与参数不变。
- 遗留脚本（写死分家前路径）已在文件头与各线 README「已知问题」标注，勿直接运行。

## 十一、相关文档

- [README.md](README.md)
- [AGENTS.md](AGENTS.md)
- [docs/INDEX.md](docs/INDEX.md)
- [docs/DIRECTORY_STANDARD.md](docs/DIRECTORY_STANDARD.md)
