# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

微信公众号智能写作助手 — an AI-powered WeChat article writing agent that generates technical articles on LLM/Agent topics. The pipeline goes from topic → outline → full article → cover image → WeChat draft.

## Commands

### Setup

```bash
pip install -r requirements.txt
cp config/.env.example config/.env   # then edit to fill API keys
```

### Run

```bash
# Interactive mode
python main.py

# CLI mode — generate article from a topic
python main.py "LangGraph 多智能体开发实战"

# CLI mode — generate and save to file
python main.py "Transformer 注意力机制" -o article.md

# CLI mode — generate and publish to WeChat drafts
python main.py "RAG 系统架构设计" -p

# Run the agent directly (alternative entry point)
python -m src.agents.agent "文章标题"
```

### Testing

```bash
# Run the image generation test
python tests/test_image_gen.py

# There is no formal test runner (pytest is not configured).
```

## Architecture

```
main.py                     # CLI entry point (argparse-based, interactive + command-line modes)
├── config/
│   ├── settings.py         # Pydantic Settings — loads .env + article-writing.yaml
│   ├── .env                # API keys (secrets)
│   ├── .env.example        # Template — copy to .env and fill real values
│   ├── article-writing.yaml  # Writing constraints (reader profile, tone, presets)
│   └── presets/              # Preset templates (formatting, cover, structure, etc.)
├── output/                 # Generated articles (agent pipeline + standalone)
├── src/
│   ├── agents/
│   │   ├── agent.py        # Thin coordinator: WeChatArticleAgent class + workflow builder + CLI
│   │   ├── state.py        # ArticleState TypedDict
│   │   ├── config.py       # .aws-article/config.yaml loading + article.yaml metadata
│   │   ├── utils.py        # File I/O, path helpers, logging
│   │   └── nodes.py        # 7 LangGraph node functions (outline → publish)
│   └── tools/
│       ├── doubao_llm.py       # Doubao LLM client (streaming/retry/failover via 火山方舟 API)
│       ├── generate_image.py   # SeeDream image generation client
│       ├── wechat_themes.py    # Dataclass-based theme system (5 presets)
│       ├── html_converter.py   # Markdown → WeChat-compatible HTML converter
│       ├── cover_generator.py  # PIL-based cover image generation
│       ├── wechat_api.py       # WeChat API functions (token, upload, draft)
│       └── publish_draft.py    # Standalone script: publish Markdown file to WeChat drafts
└── tests/
    └── test_image_gen.py   # Standalone image generation test
```

### Module Responsibilities

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `agents/agent.py` | ~120 | Coordinator — builds LangGraph graph, `WeChatArticleAgent` class, CLI |
| `agents/state.py` | ~50 | `ArticleState` TypedDict |
| `agents/config.py` | ~30 | Delegates to `Settings.get_article_config()`, saves `article.yaml` metadata |
| `agents/utils.py` | ~100 | `sanitize_filename`, `get_article_dir`, `save_text_to_file`, `save_image`, `log_llm_response` |
| `agents/nodes.py` | ~360 | All 7 LangGraph nodes + `should_continue` + `insert_images_into_html` |
| `tools/html_converter.py` | ~340 | `markdown_to_wechat_html` with 4 inline themes |
| `tools/cover_generator.py` | ~95 | `_build_default_cover_bytes`, `_resolve_cover_image_bytes`, `_load_cn_font` |
| `tools/wechat_api.py` | ~100 | `get_wechat_access_token`, `upload_image_to_wechat`, `upload_thumb_media`, `add_wechat_draft` |

### Agent Workflow (LangGraph StateGraph)

The agent in `src/agents/agent.py` defines a 7-node linear pipeline with `ArticleState` as the shared typed dict, **参考 skills 系统设计**：

1. **`generate_outline`** — calls Doubao LLM to produce a chapter outline based on structure-template.md, saves to `article/YYYYMMDD_HHMMSS_title/outline.md` and `article.yaml`
2. **`write_article`** — calls Doubao LLM with config-driven prompts (target_reader, tone, writing_style, forbidden_words) to write the full Markdown article with image placeholders
3. **`review_article`** — **NEW**: content review checking forbidden words, paragraph length, image markers, and title conventions; outputs `review.md`
4. **`convert_html`** — converts Markdown to WeChat-compatible inline-style HTML
5. **`generate_cover`** — renders a default gradient cover image using PIL, saves as `cover.jpg`
6. **`generate_article_images`** — optionally generates inline images via SeeDream and uploads them to WeChat's image CDN
7. **`publish_draft`** — uploads cover to WeChat material library, creates a draft via the WeChat Draft API

The workflow is linear with no conditional branching except an error path that stops execution.

### Configuration System

**统一配置入口：`config/settings.py` → `Settings` 类**

配置数据来自两个文件，`Settings` 类自动合并：

| 文件 | 用途 | 加载方式 |
|------|------|----------|
| `config/.env` | API 密钥、模型名称、微信凭证 | Pydantic Settings 自动加载 |
| `config/article-writing.yaml` | 写作约束（读者画像、调性、禁用词、主题等） | `Settings.__init__` 中调用 `_merge_article_yaml()` 合并 |

**API 密钥配置** (`config/.env`)：

| 配置项 | 必填 | 说明 |
|--------|------|------|
| `ARK_API_KEY` | ✅ | LLM 大语言模型 API 密钥 |
| `ARK_BASE_URL` | ✅ | LLM API 地址 |
| `LLM_MODEL` | ❌ | LLM 模型名称 |
| `IMAGE_API_KEY` | ❌ | 图片生成模型 API 密钥（为空则使用 ARK_API_KEY） |
| `IMAGE_BASE_URL` | ❌ | 图片生成模型 API 地址（为空则使用 ARK_BASE_URL） |
| `IMAGE_MODEL` | ❌ | 图片生成模型名称 |
| `WECHAT_APPID` | ❌ | 微信公众号 AppID |
| `WECHAT_APPSECRET` | ❌ | 微信公众号 AppSecret |
| `DEBUG` | ❌ | 调试模式开关 (`true`/`false`) |
| `LOG_LEVEL` | ❌ | 日志级别 (`INFO`, `DEBUG`, `WARNING`) |

**写作约束** (`config/article-writing.yaml`)：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `article_category` | 账号领域 | AI技术 |
| `target_reader` | 目标读者 | 对大模型和Agent开发感兴趣的技术人员 |
| `tone` | 调性 | 专业但不装，有观点但不偏激 |
| `writing_style` | 写作风格 | 口语化短句，像朋友聊天 |
| `forbidden_words` | 禁用词列表 | 在当今社会、随着科技的发展等 |
| `default_format_preset` | 默认排版主题 | default |
| `image_density` | 配图密度 | 每节一图 |
| `publish_method` | 发布方式 | draft |
| `drafts_root` | 输出根目录 | output |
| `target_word_count` | 目标字数 | 1800-2500 |
| `title_max_length` | 标题最大长度 | 15 |

**配置优先级**（从高到低）：
1. 命令行参数
2. `config/.env`（API 密钥、模型名称）
3. `config/article-writing.yaml`（写作约束）
4. `Settings` 类中的 Python 默认值

**Settings ↔ YAML 映射**：定义在 `settings.py` 的 `_merge_article_yaml()` 方法中。新增字段时两端同步添加即可。

### Key Dependencies

- **LangGraph** (`StateGraph`) — orchestrates the article generation pipeline
- **豆包 Seed 2.0 Pro** (`doubao-seed-2-0-pro-260215`) — LLM for text generation via 火山方舟 OpenAPI-compatible endpoint (`/chat/completions`)
- **SeeDream v5.0** (`doubao-seedream-5-0-260128`) — image generation via 火山方舟 (`/images/generations`)
- **Pydantic Settings** — manages all configuration from `config/.env`
- **PIL (Pillow)** — generates default cover images (not in requirements.txt, but used at runtime)
- **requests** — all HTTP calls to 火山方舟 and WeChat APIs

### Theme System (`src/tools/wechat_themes.py`)

The WeChat article formatting uses a dataclass-based theme system with **5 preset themes** controlled by the `default_format_preset` config:

| Theme Key | Name | Use Case |
|-----------|------|----------|
| `tech-blue` (default) | 默认科技蓝 | Technical tutorials, principle analysis |
| `minimal-mono` | 极简黑白 | Deep opinions, industry analysis |
| `warm-orange` | 温暖橙 | Hands-on sharing, experience summaries |
| `business-navy` | 商务深蓝 | Architecture design, technical specs, reports |
| `fresh-green` | 清新绿 | Beginner tutorials, getting-started guides |

Each theme defines full styling for headings, code blocks, tables, inline elements, blockquotes, cover gradients, and layout spacing. Theme selection is configured via `config/article-writing.yaml` → `default_format_preset`.

### Code Duplication
4. `config/.env` 中的 `ARK_*` 配置
5. 默认值

### Code Duplication (Resolved)

Previously `main.py`, `src/agents/agent.py`, and `src/tools/publish_draft.py` each contained near-identical copies of `markdown_to_wechat_html`, `_build_default_cover_bytes`, `_load_cn_font`, `get_access_token`, `upload_thumb_media`, and `add_draft`.

**As of 2026-07-14 refactoring**: All shared logic has been extracted into `src/tools/`:
- `html_converter.py` → `markdown_to_wechat_html`
- `cover_generator.py` → `_build_default_cover_bytes`, `_resolve_cover_image_bytes`, `_load_cn_font`
- `wechat_api.py` → `get_wechat_access_token`, `upload_image_to_wechat`, `upload_thumb_media`, `add_wechat_draft`

All three callers now import from the shared modules. Changes to HTML conversion, cover generation, or WeChat API calls only need to be made in one place.

### Output Structure

All generated articles are saved under the **`output/`** directory. Two naming conventions coexist:

**Agent pipeline output** (`output/YYYYMMDD_HHMMSS_标题/`):
```
output/
  YYYYMMDD_HHMMSS_标题/
    article.yaml     # Article metadata (title, author, status, etc.)
    outline.md       # LLM-generated outline
    draft.md         # Initial draft with image placeholders
    article.md       # Final article after review
    article.html     # WeChat-compatible HTML
    cover.jpg        # Default/generated cover image
    image_1.png      # Inline article image (if --images flag used)
    review.md        # Review report with issues checklist
    log.txt          # LLM response log
```

**Standalone/manual workflow** (`output/YYYYMMDD-topic-slug/`):
```
output/
  YYYYMMDD-topic-slug/
    article.yaml       # Metadata
    article.md         # Final markdown article
    article.html       # WeChat-compatible HTML
    cover.png/jpg      # Cover image
    topic-card.md      # Topic card / abstract
    draft.md           # Working draft
    draft-stripped.md  # Draft without image placeholders
    imgs/
      prompts/         # Image prompt files per section
        01-cover.md
        02-section.md
      *.png            # Generated section images
```

**说明**：
- `article.yaml`：文章元数据
- `draft.md`：初稿（含配图标记），审稿后生成 `article.md`
- `review.md`：审稿报告，记录发现的问题和建议

### Skills System

The `.claude/skills/` directory is intended for modular skills for the article workflow. Skills use `aws.env` for API keys and `config/article-writing.yaml` for non-secret configuration. Currently the skills directory is empty — all pipeline logic lives in `src/agents/agent.py`.

### WeChat HTML Constraints

When converting Markdown to WeChat HTML, the following CSS restrictions apply:
- No `<style>` tags or class selectors
- No `linear-gradient` or `border-radius` (filtered out)
- `<ol>` tags are filtered; `list-style` doesn't work
- All styles must be inline, using only solid colors

### API Endpoints

- **LLM**: `https://ark.cn-beijing.volces.com/api/v3/chat/completions`
- **Image**: `https://ark.cn-beijing.volces.com/api/v3/images/generations`
- **WeChat**: `https://api.weixin.qq.com/cgi-bin/` (token, draft, material, media)
