# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Project Overview

教学视频分析与飞书知识库发布系统 — a Python pipeline that processes educational videos into structured Markdown articles and publishes them to a Feishu (飞书) wiki space.

**Pipeline stages:** `videos/` → FFmpeg (keyframes + audio) → ASR transcription (小米 mimo-v2.5 audio-understanding API or local `faster-whisper`) → LLM article generation (小米 mimo-v2.5 chat API) → Feishu publishing (via `lark-cli` driven by Node.js helper)

## Common Commands

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the full pipeline (video → frames/audio → ASR → article)
python main.py

# Run individual module tests (each takes a video path or uses the first file in the input dir)
python test_video.py
python test_asr.py            # cloud ASR (小米)
python test_asr_local.py      # local ASR (faster-whisper; auto-installs on first run)
python test_llm.py            # LLM article generation
python test_feishu.py         # publish a generated .md to Feishu

# Regenerate an article for already-processed video data (skips video/ASR)
python generate_article_single.py

# Batch publish all videos under output/<series>/ to Feishu wiki
python scripts/publish_to_feishu.py
# P2–P13 batch script (从0到1设计一台计算机 series)
python scripts/batch_process.py
```

There is no test framework / linter / build step. The `test_*.py` files at the repo root are smoke-test scripts that exercise one module at a time. Each takes an optional CLI arg (audio path, video name, article path) and prints progress.

## Configuration (`config.py` + `.env`)

`config.py` is a `Config` class that reads `.env` via `python-dotenv`. All paths are resolved relative to `BASE_DIR = os.path.dirname(__file__)`. Required env groups:

- **Feishu**: `FEISHU_APP_ID`, `FEISHU_APP_SECRET` (used by `lark-cli` auth, not by Python directly)
- **LLM** (小米): `LLM_API_KEY`, `LLM_API_URL` (default `https://token-plan-cn.xiaomimimo.com/v1/chat/completions`), `LLM_MODEL` (default `mimo-v2.5`)
- **ASR cloud** (小米 audio understanding): `ASR_API_KEY`, `ASR_API_URL`, `ASR_MODEL` — note the current `.env` reuses the LLM chat-completions endpoint with `mimo-v2.5` and the audio sent as base64 `input_audio` content
- **ASR local** (faster-whisper): `ASR_LOCAL_ENABLED`, `ASR_LOCAL_MODEL_SIZE`, `ASR_LOCAL_MODEL_PATH`, `ASR_LOCAL_DEVICE`, `ASR_LOCAL_COMPUTE_TYPE`, `ASR_LOCAL_BEAM_SIZE`, `ASR_LOCAL_DOWNLOAD_ROOT` (default `./models`)
- **Video**: `FFMPEG_PATH`, `FRAME_INTERVAL` (sec), `OUTPUT_QUALITY`
- **Paths**: `INPUT_VIDEO_DIR`, `OUTPUT_BASE_DIR` (both relative to `BASE_DIR`)

`.env.example` is referenced in the README but does not exist in the repo — copy from `.env` or README. The committed `.env` contains real-looking API keys; treat as secrets and never commit new ones.

## Architecture

### Entry points

- **`main.py`** — Orchestrates the full pipeline. Recursively walks `INPUT_VIDEO_DIR` for `*.mp4/*.avi/*.mov/*.mkv/*.wmv/*.flv`, then for each video runs FFmpeg (frames + audio), Xiaomi ASR, and Xiaomi LLM article generation. **Idempotent**: each stage checks for existing outputs in `output/<video_name>/{frames,audio,audio_txt,articles}/` and skips when present.
- **`generate_article_single.py`** — Re-runs only the LLM article stage for a hard-coded video (`飞天闪客/2024-12-29 23-33-38_你管这破玩意叫网络___video`). Edit the `video_relative_path` variable to target a different video.
- **`scripts/publish_to_feishu.py`** — For each subdirectory under `BASE_DIR`, reads the article `.md` + keyframes, interweaves images into sections by markdown header, then drives `lark-cli` to: `drive +import` → `docs +media-insert` (with `--selection-with-ellipsis` anchor) → `wiki +move` into a target `SPACE_ID`. Uses a `_published.json` log to skip already-published videos.
- **`scripts/batch_process.py`** / **`scripts/fast_process.py`** — P2–P13 batch publish for the `从0到1设计一台计算机` series. Each `process_*` script hard-codes its own directory list.

### Core modules (`modules/`)

- **`video_processor.py`** — `VideoProcessor` wraps `subprocess` calls to FFmpeg. Methods: `get_video_info`, `extract_key_frames` (uses `select=eq(pict_type\,I)` for I-frames), `extract_audio` (mp3, libmp3lame, 128k), `extract_frames` (interval-based, 1 frame per `FRAME_INTERVAL` seconds). `get_video_info` has a regex fallback when JSON parsing of ffmpeg `-show_entries` output fails. All return `{success, ...}` dicts.
- **`asr_processor.py`** — `ASRProcessor` has two backends sharing the same `{success, text, segments}` return shape:
  - Cloud (`transcribe`): POSTs the audio as a base64 `data:` URL inside the user message of a `mimo-v2.5` chat-completions call. **Hard 50 MB limit** (raises before sending).
  - Local (`transcribe_local`): lazily imports `faster_whisper` (auto-pip-installs on first call), picks CUDA if available else CPU, returns segments with timestamps.
  - `save_transcript_to_file` / `save_local_transcript` write `.txt` (and `.srt` if segments are present) under `output/<video_name>/audio_txt/`.
  - `batch_transcribe` iterates **sequentially** — no parallelism, no retry.
- **`llm_processor.py`** — `LLMProcessor` calls the 小米 chat-completions API. `generate_full_article_stream` is the pipeline-facing method: it runs three streamed LLM calls (outline → keywords → summary) and a fourth streamed call to write the final article, optionally saving to `output/<video_name>/articles/<base_name>.md`. `batch_generate_articles` is sequential.
- **`feishu_publisher.py`** — `FeishuPublisher` writes the markdown body to a temp file and shells out to `node modules/lark_helper.js` (NOT to `lark-cli` directly). Two actions: `create-doc` (calls `lark-cli docs +create`) and `insert-image` (calls `lark-cli docs +media-insert` from the image's own directory so the filename resolves). Also exports `get_video_frames` / `generate_article_images` helpers and a hard-coded `__main__` demo article. **Note**: the file contains a leftover, unused `_run_command` method (subprocess shell-string variant) that is dead code.
- **`lark_helper.js`** — Node.js bridge. Hard-codes `C:\Program Files\nodejs\node_modules\@larksuite\cli\scripts\run.js` as the lark-cli entry point — will break if Node is installed elsewhere. `runLarkCli` uses `spawnSync` and exits with the lark-cli status code.

### Output directory layout

```
output/<video_relative_path_without_ext>/
  frames/        # <video_name>_keyframe_NNNN.jpg  (I-frames from FFmpeg)
  audio/         # <video_name>.mp3
  audio_txt/     # <video_name>.txt and optionally <video_name>.srt
  articles/      # <video_name>.md
```

`video_name` in `main.py` is the **relative path without extension** of the input video — so a video at `videos/从0到1设计一台计算机/P2/foo.mp4` produces `output/从0到1设计一台计算机/P2/foo/{...}`. Several scripts under `scripts/` and `generate_article_single.py` rely on this layout and have hard-coded `BASE_DIR` paths that point at specific series (e.g. `D:\ai_coder\p000_llm_video_ark\output\从0到1设计一台计算机`).

## Key Patterns

- **Return shape**: every processor method returns `{'success': bool, ...}`. Always check `.get('success')` before reading other fields.
- **Idempotency**: `main.py` checks for `output/<video_name>/{frames/*, audio/<name>.mp3, audio_txt/<name>.txt, articles/<name>.md}` and skips each stage whose artifact already exists. Safe to re-run on the same input directory.
- **Naming convention**: `<base_name>` (used everywhere in `main.py`) is `Path(video_name).name` — the last path component, not the full relative path. This means a video at `series/sub/file.mp4` and `series/sub2/file.mp4` would collide on disk. The current inputs avoid this by keeping each series in its own subdirectory at the top level.
- **Unicode / Windows encoding**: `feishu_publisher.py` and `scripts/publish_to_feishu.py` set `PYTHONIOENCODING=utf-8` / `PYTHONUTF8=1` and re-decode subprocess output as utf-8 (falling back to gbk). The repo assumes Windows.
- **Temp files**: `feishu_publisher.create_document` writes the markdown body to `tempfile.gettempdir()/feishu_doc_content.md` and deletes it in a `finally` block. `scripts/publish_to_feishu.py` uses a per-base-dir `_publish_temp/` subdir and a `_published.json` log of `{video_dir_name: {title, published_at, enhanced_md}}`.
- **Streaming LLM**: the four-call LLM flow (outline, keywords, summary, article) all use streaming. `llm_processor._stream_llm` parses `data: ...` SSE lines, accumulates `delta.content`, and prints live.
- **Image anchoring in Feishu**: `publish_to_feishu.py` distributes frames evenly across article H2/H3 headings, then `docs +media-insert`s with `--selection-with-ellipsis <first 60 chars of heading>` and `--before` (in reverse order to avoid position drift). Frames that don't fit an anchor are appended without an anchor.

## External Dependencies

- **FFmpeg** — must be on `PATH` (or set `FFMPEG_PATH` env var)
- **Node.js + `@larksuite/cli`** — `npm install -g @larksuite/cli`. `modules/lark_helper.js` hard-codes `C:\Program Files\nodejs\node_modules\@larksuite\cli\scripts\run.js` — change that path if Node is installed elsewhere. `lark-cli` itself must be authenticated (run `lark-cli doctor` to check) before any `publish_to_feishu` step.
- **faster-whisper** — optional. Only used when `ASR_LOCAL_ENABLED=true`; auto-installed on first call to `transcribe_local`. Models download to `ASR_LOCAL_DOWNLOAD_ROOT` (default `./models`).
- **小米 mimo API** — both LLM and ASR cloud paths hit `https://token-plan-cn.xiaomimimo.com/v1/chat/completions` with the same `LLM_API_KEY` / `ASR_API_KEY` in the current `.env`.

## What NOT to break

- The `output/<relative-path-without-ext>/` layout — `main.py` and all the `scripts/*.py` batch publishers assume it. Renaming the `output` subfolders (`frames`, `audio`, `audio_txt`, `articles`) will break everything.
- The `lark_helper.js` hard-coded Node path — Windows + default Node install only.
- The `idempotent re-run` behavior of `main.py` — if you add caching, key it by `video_name` (which is the relative path without extension) and don't reuse the same `output` subdir for two different videos.
