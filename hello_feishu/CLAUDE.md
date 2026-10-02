# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

教学视频分析与飞书知识库发布系统 — a pipeline that processes educational videos into structured articles and publishes them to Feishu (飞书) knowledge base.

**Pipeline stages:** Video → FFmpeg (frames + audio) → ASR transcription (小米/Xiaomi API or local faster-whisper) → LLM article generation (小米 API) → Feishu publishing (via lark-cli)

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the full pipeline
python main.py

# Run individual test modules (from hello_feishu/, scripts live in tests/)
python tests/test_video.py    # Test video processing
python tests/test_asr.py      # Test ASR transcription
python tests/test_llm.py      # Test LLM article generation
python tests/test_feishu.py   # Test Feishu publishing

# Local ASR test (requires faster-whisper)
python tests/test_asr_local.py

# Batch publish to Feishu
python scripts/batch_process.py
```

## Architecture

### Core Modules (`modules/`)

- **video_processor.py** — `VideoProcessor` class wraps FFmpeg subprocess calls for extracting keyframes (`extract_key_frames` using I-frame selection), audio (`extract_audio` as mp3 128k), and video info (`get_video_info`). All methods return `{success, ...}` dicts.
- **asr_processor.py** — `ASRProcessor` class handles both cloud ASR and local ASR (`faster-whisper`). Cloud ASR sends audio as base64 `input_audio` in a chat-completions request (same endpoint as LLM), with a **50 MB hard limit**. Local ASR auto-installs `faster-whisper` on first use. `batch_transcribe()` iterates sequentially — no parallelism, no retry.
- **llm_processor.py** — `LLMProcessor` generates articles via 小米 LLM API. The pipeline uses `generate_full_article_stream` which makes **4 streamed LLM calls**: outline → keywords → summary → final article. `batch_generate_articles()` processes sequentially.
- **feishu_publisher.py** — `FeishuPublisher` delegates to `core/lark_helper.js` which calls `lark-cli` commands. Writes markdown to a temp file for document creation; uses `--selection-with-ellipsis` anchoring for image insertion.
- **lark_helper.js** — 已上收至 `core/lark_helper.js`（含 `auth-status` / `move-to-wiki` 动作）；lark-cli 路径可用 `LARK_CLI_RUN_JS` 覆盖，不再硬编码。

### Configuration (`config.py`)

`Config` class reads from `.env` via `python-dotenv`. All paths are relative to `BASE_DIR`. Key config groups:
- Feishu: `FEISHU_APP_ID`, `FEISHU_APP_SECRET`
- LLM: `LLM_API_KEY`, `LLM_API_URL`, `LLM_MODEL` (default: `mimo-v2.6-pro`，接口 `https://api.xiaomimimo.com/v1/chat/completions`)
- ASR cloud: `ASR_API_KEY`, `ASR_API_URL`
- ASR local: `ASR_LOCAL_ENABLED`, `ASR_LOCAL_MODEL_SIZE`, `ASR_LOCAL_DEVICE`, `ASR_LOCAL_COMPUTE_TYPE`
- Video: `FFMPEG_PATH`, `FRAME_INTERVAL`, `OUTPUT_QUALITY`

### Output Directory Structure

Each video gets its own subdirectory under `output/`:
```
output/<video_name>/
  frames/     — extracted keyframes (.jpg)
  audio/      — extracted audio (.mp3)
  audio_txt/  — transcription text (.txt) and SRT subtitles
  articles/   — generated markdown articles (.md)
```

### Key Patterns

- All processor methods return `{success: bool, ...}` dicts — check `.get('success')` before accessing other fields.
- Video names use relative paths (without extension) matching the `output/` subdirectory structure. `video_name` is the relative path without extension (e.g. `系列/P2/foo`), while `base_name` is `Path(video_name).name` (just `foo`). Two videos with the same `base_name` in different directories would collide on output filenames.
- The `main.py` pipeline skips already-processed steps (idempotent — frames, audio, transcripts, articles can be re-run safely).
- `core/lark_helper.js` is invoked via `subprocess.run(['node', LARK_HELPER_JS, action, ...args])` — requires Node.js in PATH.
- The `test_*.py` files are smoke-test scripts (not a test framework) — each exercises one module with a real or first-found video.
- Windows encoding: `feishu_publisher.py` and `scripts/publish_to_feishu.py` force `PYTHONIOENCODING=utf-8` and decode subprocess output as utf-8 with gbk fallback.
- Feishu publishing: frames are distributed across H2/H3 headings, inserted in reverse order via `docs +media-insert` with `--selection-with-ellipsis` to avoid position drift. A `_published.json` log tracks what's already been published.

## External Dependencies

- **FFmpeg** — must be in system PATH (or set `FFMPEG_PATH`)
- **Node.js + lark-cli** — for Feishu publishing (`npm install -g @larksuite/cli`)
- **faster-whisper** (optional) — for local ASR, installed on first use if `ASR_LOCAL_ENABLED=true`
