# AI 自媒体内容生产中台 — 架构说明

> 版本：v3.0（Provider 注册表 + 发布契约 + CLI 包化）  
> 更新：2026-10-02  
> 仓库：`personal-media-content`（自媒体域正本；2026-10 自工作台 `p000_0000_it` 的 `media/` 分家而来）

## 一、整体架构

```
personal-media-content/
│
├── core/                          ← 共享核心能力层（内部分层）
│   ├── config.py                  # 统一配置（根 .env；LLM/ASR 属性由注册表推导，旧键回落）
│   ├── providers/                 # ★ 模型接入层：凭据唯一存放处 + 工厂
│   │   ├── registry.py            #   PROVIDER_* 环境变量解析 → resolve('chat'|'asr'|'image')
│   │   ├── llm.py                 #   LLMClient + get_llm_client（OpenAI 兼容，端点自动补全）
│   │   └── asr.py                 #   ASRClient（云端 input_audio / 本地 faster-whisper）
│   ├── publisher_base.py          # ★ 发布契约：PublishResult + BasePublisher + 按名注册
│   ├── feishu_publisher.py        #   飞书发布（实现契约；lark-cli 桥接见 lark_helper.js）
│   ├── wechat_publisher.py        #   公众号发布（实现契约；MD→HTML、草稿、发布）
│   ├── story_to_script.py         #   小说→分镜
│   ├── story_to_article.py        #   小说→文章
│   ├── novel_publisher.py         #   小说批量飞书发布（幂等记录在 storage/db/）
│   ├── asset_manager.py           #   素材资产（SQLite storage/db/assets.db）
│   ├── task_manager.py            #   任务调度（SQLite storage/db/tasks.db）
│   ├── storage.py                 #   路径与存储工具
│   ├── video_toolkit.py           #   FFmpeg 封装
│   └── lark_helper.js             #   lark-cli 桥接（auth-status / create-doc / insert-image / move-to-wiki）
│
├── cli/                           ← 命令实现包（media-cli.py 只是薄入口）
│   ├── app.py                     #   解析器组装
│   └── commands/                  #   status / doctor / video / ai / publish / story /
│                                  #   asset / task / storage / dashboard 各域一模块
│
├── dashboard/                     ← Web 看板（Flask + templates/*.html；默认仅绑 127.0.0.1）
├── media-cli.py                   ← 统一 CLI 入口
├── tests/                         ← 平台层 pytest（注册表/发布契约/doctor/CLI）
├── models/                        ← 模型缓存（运行时生成，不入库）
├── storage/                       ← 统一产物/数据库根（db/ 与运行子目录不入库）
├── docs/                          ← 文档索引与目录规范
│
├── hello_doubao_video/            ← 短视频线（docs/scripts/media；assets 运行时生成）
├── hello_feishu/                  ← 教学视频→飞书流水线（兼容层桥接 core）
├── hello_novel/                   ← 小说线（novels/<book>/process|chapters/…）
├── hello_webchat_official/        ← 公众号技能流水线（drafts/；凭据在其 aws.env）
├── hello_webchat_solo/            ← 公众号独立写作程序（模型凭据走根注册表）
├── hello_weixin_book/             ← 网文分析（analyses/，纯内容资产）
├── family-life-video/             ← 家庭亲情短视频内容稿（纯内容资产）
└── publish_workbench/             ← 发布工作台（单文件 HTML APP，localStorage）
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
- 消费方：`core/llm_client.py` 与 `core/asr_client.py` 为兼容 shim（实现已在 `core/providers/`）；`hello_webchat_solo` 的 Settings 未显式配置时回落注册表。
- 验证：`python media-cli.py doctor --live`（静态检查 + LLM 实调 + 发布平台健康检查）。

新增 provider 步骤：根 `.env` 加一组 `PROVIDER_<ID>_*` 键 → 对应能力 `<X>_PROVIDER=<ID>` → `doctor` 验证。无需改任何代码。

## 三、发布契约（v3 核心变化）

- `PublishResult`：统一结果对象（success/platform/url/id/error/raw），兼容 dict 访问。
- `BasePublisher`：真 ABC——子类实现 `publish_markdown(title, content_md, options) -> PublishResult`，可选 `health_check()`（平台连通性）与 `check_config()`（配置完整性）。
- `MultiPlatformPublisher`：按名发现已登记平台（`_load_publisher`），未配置平台记入 `init_errors` 而不崩溃；`health_check_all()` 批量体检（doctor 复用）。
- 新增发布平台：实现 `BasePublisher` → 在 `publisher_base._load_publisher` 登记一条 → CLI/doctor 自动纳入。

## 四、核心能力层（2.x）

### 4.1 config.py

全局一次加载根 `.env`。存储默认：`storage/{videos_input,videos_output,articles,novels}`；`storage/db/` 为 SQLite 运行库（不入库，可重建）。平台素材库 `storage/novels` **独立于** 业务线正文目录 `hello_novel/novels/`。

### 4.2 内容转化

- `story_to_script.py`：6 种风格分镜 + AI 提示词
- `story_to_article.py`：deep / summary / character / worldview
- `novel_publisher.py`：幂等批量发飞书（发布记录在 `storage/db/feishu_published.json`）

输入章节使用现行路径，如 `hello_novel/novels/cangyuantu/chapters/8-续写-第1章.txt`。

### 4.3 资产与任务

- `asset_manager.py`：标签、关联、扫描章节目录
- `task_manager.py`：pending → running → done/failed/skipped，重试与日志
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
hello_novel/novels/*/chapters
    ├─ story_to_script  → 分镜 + 提示词 → 视频生成
    ├─ story_to_article → 公众号/飞书文章
    └─ novel_publisher  → 飞书知识库

hello_feishu/videos → 抽帧/ASR/LLM → 飞书文章
hello_weixin_book/analyses → 阅读与选题素材
family-life-video/<主题> → 分镜/口播稿 → hello_doubao_video 成片（规划中）
hello_webchat_* → 公众号成稿（技能线 drafts / 程序线 output）
```

## 八、业务线与平台边界

| 业务线 | 是否依赖 core | 说明 |
|--------|---------------|------|
| hello_doubao_video | 可选 | 可用 `media-cli.py video`；保留本地脚本 |
| hello_feishu | 是（兼容层） | `config.py`/`modules/*` 委托 core；模型凭据走根注册表 |
| hello_novel | 转化时 | 创作目录自治；发布/改写走 CLI |
| hello_webchat_official | 可选 | 技能包自治（凭据在其 `aws.env`）；发布可复用 wechat_publisher |
| hello_webchat_solo | 共享注册表 | LangGraph 程序自治；LLM/生图/微信凭据回落根 `.env` |
| hello_weixin_book | 否 | 纯内容资产 |
| family-life-video | 否 | 纯内容稿（分镜/口播），上游供 doubao_video |
| publish_workbench | 否 | 单文件 HTML 发布跟踪 APP |

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
