# 教学视频分析与飞书知识库发布系统

把教学视频批量化处理成结构化 Markdown 文章，并发布到飞书 Wiki。

## 运行流程总览

```
videos/*.mp4
    │
    ▼
┌─────────────────────┐
│  1. FFmpeg 视频处理   │  提取关键帧(I帧) + 提取音频(mp3 128k)
│     video_processor  │
└─────────┬───────────┘
          │  output/<name>/frames/*.jpg
          │  output/<name>/audio/<name>.mp3
          ▼
┌─────────────────────┐
│  2. ASR 语音转写      │  小米 mimo API (云端) 或 faster-whisper (本地)
│     asr_processor    │
└─────────┬───────────┘
          │  output/<name>/audio_txt/<name>.txt
          ▼
┌─────────────────────┐
│  3. LLM 文章生成      │  4 次流式调用: 大纲→关键词→摘要→正文
│     llm_processor    │
└─────────┬───────────┘
          │  output/<name>/articles/<name>.md
          ▼
┌─────────────────────┐
│  4. 飞书发布 (可选)    │  lark-cli 创建文档 + 插入关键帧图片
│     feishu_publisher │
└─────────────────────┘
```

`main.py` 执行步骤 1-3，步骤 4 通过 `scripts/publish_to_feishu.py` 单独执行。

**每一步都是幂等的**：已存在的产物（帧、音频、转写文本、文章）会自动跳过，可放心重跑。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 `.env`

复制 `.env.example` 或手动创建 `.env`：

```env
# === LLM (小米 MiMo，OpenAI 兼容) ===
LLM_API_KEY=你的key
LLM_API_URL=https://api.xiaomimimo.com/v1/chat/completions
LLM_MODEL=mimo-v2.6-pro

# === 云端 ASR (mimo-v2.5-asr，走 chat/completions + input_audio) ===
ASR_API_KEY=你的key
ASR_API_URL=https://api.xiaomimimo.com/v1/chat/completions
ASR_MODEL=mimo-v2.5-asr

# === 本地 ASR (可选, faster-whisper) ===
ASR_LOCAL_ENABLED=false
ASR_LOCAL_MODEL_SIZE=base          # tiny/base/small/medium/large-v3
ASR_LOCAL_DEVICE=auto              # auto/cuda/cpu

# === 视频处理 ===
FFMPEG_PATH=ffmpeg                 # ffmpeg 可执行文件路径
FRAME_INTERVAL=10                  # 普通抽帧间隔(秒), 关键帧不受此控制

# === 路径 ===
INPUT_VIDEO_DIR=./videos           # 视频输入目录
OUTPUT_BASE_DIR=./output           # 产物输出目录
```

### 3. 放入视频

把 `.mp4` / `.avi` / `.mov` / `.mkv` / `.wmv` / `.flv` 文件放到 `videos/` 目录下，支持子目录：

```
videos/
├── 系列A/
│   ├── P1.mp4
│   └── P2.mp4
└── 单独视频.mp4
```

### 4. 运行

```bash
python main.py
```

输出进度：

```
=== 教学视频分析与飞书知识库发布系统 ===

1/3 开始处理视频...
提取帧: 系列A/P1
提取音频: 系列A/P1
跳过已提取帧: 系列A/P2        ← 已处理过的自动跳过

2/3 开始语音转写...
正在转写: .../系列A/P1.mp3
转写完成: .../系列A/P1.mp3

3/3 开始生成文章...
[1/4] 正在生成大纲...
[2/4] 正在提取关键词...
[3/4] 正在生成摘要...
[4/4] 正在生成文章（流式输出）...

=== 处理流程全部完成 ===
```

## 各模块详解

### 模块 1: 视频处理 (`modules/video_processor.py`)

| 方法 | 功能 | 产物 |
|------|------|------|
| `extract_key_frames()` | 提取 I 帧关键帧 | `frames/<name>_keyframe_NNNN.jpg` |
| `extract_audio()` | 提取音频 | `audio/<name>.mp3` |
| `get_video_info()` | 获取视频元信息 | 返回时长/分辨率/帧率 |

### 模块 2: 语音转写 (`modules/asr_processor.py`)

**云端 ASR** (默认): 把音频 base64 编码后通过 `input_audio` 字段发给小米 mimo API。有 **50 MB 硬限制**。

**本地 ASR**: 使用 `faster-whisper`，设置 `ASR_LOCAL_ENABLED=true` 启用。首次调用自动 `pip install faster-whisper`，模型下载到 `./models/`。

### 模块 3: 文章生成 (`modules/llm_processor.py`)

`generate_full_article_stream()` 执行 4 次流式 LLM 调用：

1. **大纲** — 根据转写文本生成结构化课程大纲
2. **关键词** — 提取 10 个核心关键词
3. **摘要** — 300 字以内的精简总结
4. **正文** — 结合大纲+关键词+摘要+转写全文，生成完整教学文章

### 模块 4: 飞书发布 (`modules/feishu_publisher.py`)

通过 `modules/lark_helper.js` 调用 `@larksuite/cli` 命令行工具：

1. `docs +create` — 创建飞书文档
2. `docs +media-insert` — 倒序插入关键帧图片（用 `--selection-with-ellipsis` 锚定标题，避免位置偏移）
3. `wiki +move` — 移动到目标知识空间

> **注意**: `lark_helper.js` 硬编码了 Node 路径 `C:\Program Files\nodejs\node_modules\@larksuite\cli\scripts\run.js`，如果 Node 装在其他位置需要修改。

## 单独测试各模块

```bash
python tests/test_video.py       # 测试视频处理（抽帧+音频）
python tests/test_asr.py         # 测试云端 ASR
python tests/test_asr_local.py   # 测试本地 ASR（首次会自动装 faster-whisper）
python tests/test_llm.py         # 测试 LLM 文章生成
python tests/test_feishu.py      # 测试飞书发布
```

每个测试脚本会自动在 `videos/` 目录下找第一个视频文件来测试。

## 飞书发布

```bash
python scripts/publish_to_feishu.py
```

扫描 `OUTPUT_BASE_DIR` 下的子目录，把 `.md` 文章 + 关键帧图片混排后上传到飞书知识空间。

已发布过的视频会记录在 `_published.json` 中自动跳过。

## 输出目录结构

```
output/
├── 系列A/
│   ├── P1/
│   │   ├── frames/              # P1_keyframe_0001.jpg, P1_keyframe_0002.jpg, ...
│   │   ├── audio/               # P1.mp3
│   │   ├── audio_txt/           # P1.txt (转写文本), P1.srt (字幕, 本地ASR才有)
│   │   └── articles/            # P1.md (生成的文章)
│   └── P2/
│       └── ...
└── 单独视频/
    └── ...
```

`video_name` 是**相对于 `videos/` 的路径去掉扩展名**，例如 `videos/系列A/P1.mp4` → `video_name = "系列A/P1"`，输出到 `output/系列A/P1/`。

> **注意**: 不同子目录下同名文件会冲突（`base_name` 相同），建议每个系列放在独立子目录。

## 项目结构

```
.
├── main.py                    # 全流程入口 (步骤 1-3)
├── config.py                  # .env 配置加载
├── requirements.txt
├── .env                       # API Key 等配置 (不要提交到 git)
│
├── modules/
│   ├── video_processor.py     # FFmpeg 封装 (抽帧/抽音/视频信息)
│   ├── asr_processor.py       # 云端/本地 ASR 转写
│   ├── llm_processor.py       # LLM 流式文章生成
│   ├── feishu_publisher.py    # 飞书文档创建+图片插入
│   └── lark_helper.js         # lark-cli Node.js 桥接
│
├── scripts/
│   └── publish_to_feishu.py   # 批量发布到飞书知识库
│
├── tests/
│   ├── test_video.py          # 视频处理测试
│   ├── test_asr.py            # 云端 ASR 测试
│   ├── test_asr_local.py      # 本地 ASR 测试
│   ├── test_llm.py            # LLM 文章生成测试
│   └── test_feishu.py         # 飞书发布测试
│
├── videos/                    # 输入视频 (按系列分子目录；原件不入库)
├── output/                    # 处理产物 (按 video_name 分目录；不入库)
└── models/                    # faster-whisper 本地模型缓存（不入库）
```

> `videos/`、`output/`、`models/` 与 `.env` 为运行时目录/本地文件，全新 clone 中不存在；放入视频或运行后自动生成。

## 外部依赖

| 依赖 | 用途 | 是否必须 |
|------|------|----------|
| FFmpeg | 抽帧/抽音频 | 是 |
| Python `requests`, `Pillow`, `python-dotenv` | HTTP 请求/图片/配置 | 是 |
| 小米 mimo API (LLM + ASR) | 文章生成 + 语音转写 | 是 |
| `faster-whisper` | 本地 ASR | 仅 `ASR_LOCAL_ENABLED=true` 时 |
| Node.js + `@larksuite/cli` | 飞书发布 | 仅发布功能需要 |

## 关键约定

- **返回结构**: 所有 processor 方法返回 `{'success': bool, ...}`，先检查 `.get('success')` 再读其他字段
- **编码**: Windows 下强制 `utf-8`，subprocess 输出按 `utf-8` 解码（`gbk` 兜底）
- **幂等**: `main.py` 每一步都检查产物是否存在，存在就跳过
- **流式输出**: LLM 4 次调用都走 SSE，实时打印 `delta.content`

## 相关文档

- 程序架构：[CLAUDE.md](CLAUDE.md)
- 历史协作说明：[docs/legacy/CODEBUDDY.md](docs/legacy/CODEBUDDY.md)

