# AI 自媒体内容生产中台 — 架构说明

> 版本：v2.1（文档与目录整理版）  
> 更新：2026-09-19  
> 仓库根目录名：`p000_0000_media`

## 一、整体架构

```
p000_0000_media/
│
├── core/                          ← 共享核心能力层
│   ├── config.py                  # 统一配置（.env）
│   ├── llm_client.py              # LLM
│   ├── asr_client.py              # ASR 云端/本地
│   ├── video_toolkit.py           # FFmpeg 封装
│   ├── feishu_publisher.py        # 飞书发布
│   ├── wechat_publisher.py        # 公众号发布
│   ├── publisher_base.py          # 多平台统一发布
│   ├── story_to_script.py         # 小说→分镜
│   ├── story_to_article.py        # 小说→文章
│   ├── novel_publisher.py         # 小说批量飞书发布
│   ├── asset_manager.py           # 素材资产（SQLite）
│   ├── task_manager.py            # 任务调度（SQLite）
│   ├── storage.py                 # 路径与存储工具
│   └── lark_helper.js             # lark-cli 桥接
│
├── dashboard/                     ← Web 看板（Flask）
├── media-cli.py                   ← 统一 CLI
├── models/                        ← 模型缓存
├── storage/                       ← 统一产物/数据库根
├── docs/                          ← 文档索引与目录规范
│   ├── INDEX.md
│   └── DIRECTORY_STANDARD.md
│
├── hello_doubao_video/            ← 短视频线（docs/scripts/assets/media）
├── hello_feishu/                  ← 教学视频→飞书流水线
├── hello_novel/                   ← 小说线（novels/<book>/process|chapters/…）
├── hello_webchat_official/        ← 公众号技能流水线（drafts/）
├── hello_webchat_solo/            ← 公众号独立写作程序
└── hello_weixin_book/             ← 网文分析（analyses/）
```

业务线物理分层规范见 [docs/DIRECTORY_STANDARD.md](docs/DIRECTORY_STANDARD.md)。

## 二、核心能力层

### 2.1 config.py

全局一次加载根目录 `.env`。`BASE_DIR` 为仓库根。存储默认：

| 配置键 | 默认相对路径 |
|--------|----------------|
| `STORAGE_BASE` | `storage/` |
| `STORAGE_VIDEO_INPUT` | `storage/videos_input` |
| `STORAGE_VIDEO_OUTPUT` | `storage/videos_output` |
| `STORAGE_ARTICLES` | `storage/articles` |
| `STORAGE_NOVELS` | `storage/novels` |

说明：平台素材库 `storage/novels` **独立于** 业务线正文目录 `hello_novel/novels/`。扫描入库时用 `--dir` 指向业务线 `chapters/`。

### 2.2 llm_client.py

`chat` / `chat_stream` / `chat_messages` / `summarize` / `extract_keywords` / `generate_outline`。

### 2.3 asr_client.py

云端（小米 mimo）与本地 faster-whisper；支持 SRT 与批量。

### 2.4 video_toolkit.py

信息、抽帧、抽音、无损合并、淡入淡出合并、格式转换。

### 2.5–2.7 发布

- 飞书：`feishu_publisher.py` + `lark_helper.js`
- 公众号：`wechat_publisher.py`（token、素材、草稿、发布、MD→HTML）
- 多平台：`publisher_base.py` 的 `MultiPlatformPublisher.publish_all`

### 2.8–2.10 小说转化

- `story_to_script.py`：6 种风格分镜 + AI 提示词
- `story_to_article.py`：deep / summary / character / worldview / feature
- `novel_publisher.py`：幂等批量发飞书

输入章节请使用现行路径，例如：

`hello_novel/novels/cangyuantu/chapters/8-续写-第1章.txt`

### 2.11–2.13 资产与任务

- `asset_manager.py`：标签、关联、扫描章节目录
- `task_manager.py`：pending → running → done/failed/skipped，重试与日志
- `storage.py`：路径快捷与幂等检查

## 三、Web 数据看板

```bash
python media-cli.py dashboard start --port 5000
```

| 页面 | 路径 | 功能 |
|------|------|------|
| 总览 | `/` | 任务/素材统计、最近任务 |
| 任务中心 | `/tasks` | 筛选、详情、重试 |
| 素材库 | `/assets` | 标签与检索 |

技术栈：Flask + 纯前端。

## 四、统一 CLI

```
status / video / asr / llm / feishu / wechat / story
asset / task / dashboard / publish / storage
```

示例（路径已按重排后结构）：

```bash
python media-cli.py asset scan novel --project 沧元图 \
  --dir ./hello_novel/novels/cangyuantu/chapters/

python media-cli.py story article \
  "hello_novel/novels/cangyuantu/chapters/8-续写-第1章.txt" --type deep -o article.md
```

## 五、内容转化链路

```
hello_novel/novels/*/chapters
    ├─ story_to_script  → 分镜 + 提示词 → 视频生成
    ├─ story_to_article → 公众号/飞书文章
    └─ novel_publisher  → 飞书知识库

hello_feishu/videos → 抽帧/ASR/LLM → 飞书文章
hello_weixin_book/analyses → 阅读与选题素材
hello_webchat_* → 公众号成稿（技能线 drafts / 程序线 output）
```

## 六、业务线与平台边界

| 业务线 | 是否依赖 core | 说明 |
|--------|---------------|------|
| hello_doubao_video | 可选 | 可用 `media-cli.py video`；保留本地脚本 |
| hello_feishu | 是（兼容层） | `config.py` 从 core 导入 |
| hello_novel | 转化时 | 创作目录自治；发布/改写走 CLI |
| hello_webchat_official | 可选 | 技能包为主，可复用 wechat 发布 |
| hello_webchat_solo | 独立 | 自带 config/src |
| hello_weixin_book | 否 | 纯内容资产 |

## 七、兼容与迁移

- 业务线 **顶层目录名**（`hello_*`）保持不变，`media-cli.py status` 仍按这些名字探测。
- 小说正文已从仓库根平铺迁至 `hello_novel/novels/<book>/chapters/`。
- 旧文档中的 `hello_novel/cangyuantu/8-正文/`、`p000_0000_self_media` 等命名已废弃。
- `hello_feishu` 对外接口保持兼容。

## 八、相关文档

- [README.md](README.md)
- [AGENTS.md](AGENTS.md)
- [docs/INDEX.md](docs/INDEX.md)
- [docs/DIRECTORY_STANDARD.md](docs/DIRECTORY_STANDARD.md)
