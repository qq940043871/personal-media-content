---
name: webchat-article-writing
description: 公众号写稿｜AI写稿｜文章润色｜大纲生成 — 基于豆包大模型(Doubao/DeepSeek)生成技术文章，从主题/大纲生成完整初稿，支持改写、续写、润色、标题优化。面向技术自媒体、AI内容创作者。触发词（**单独触发仅限对已有产物的修改**）：「起标题」「优化标题」「润色」「改写」「续写」「重写」「润色这段」「优化用词」。新写一篇请走webchat-article-main；需要多环节串联也走main。
homepage: https://github.com/haswhere/webchat-article-solo
url: https://github.com/haswhere/webchat-article-solo
metadata:
  openclaw:
    requires:
      env:
        - ARK_API_KEY
      bins:
        - python3
    primaryEnv: config/.env
---

# 长文写作

**公众号技术文章 AI 写作引擎** —— 基于豆包大模型，从提纲或主题生成完整初稿，支持改写、续写、润色、标题优化。

> **套件说明** · 本 skill 属 `webchat-article-*` 套件（共 6 个 slug，入口 `webchat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录。

## 脚本

| 脚本 | 用途 |
|------|------|
| `{baseDir}/scripts/write_article.py outline <topic>` | 生成文章大纲 |
| `{baseDir}/scripts/write_article.py article <title>` | 根据大纲撰写文章 |
| `{baseDir}/scripts/write_article.py polish <file>` | 润色文章内容 |
| `{baseDir}/scripts/write_article.py optimize-title <titles>` | 优化标题 |

用法示例：

```bash
python {baseDir}/scripts/write_article.py outline "LangGraph 开发实战" -o outline.md
python {baseDir}/scripts/write_article.py article "LangGraph 开发实战" --outline outline.md -o article.md
python {baseDir}/scripts/write_article.py polish article.md -o polished.md
python {baseDir}/scripts/write_article.py optimize-title "标题1" "标题2" "标题3"
```

## 能力披露（Capabilities）

本 skill 调用 `src/tools/doubao_llm.py` 生成文章初稿，**会把文章内容发送给火山方舟 LLM 端点**。使用前请阅读以下全部行为说明：

- **凭证读取**：读取 `config/.env` 的 `ARK_API_KEY`
- **凭证外发**：该 API key 以 `Authorization: Bearer <key>` 头发送到火山方舟 Chat Completions API
- **内容外发**：Prompt 包含文章主题/大纲/配置约束，整体 POST 给 LLM 端点
- **文件读（项目内）**：`config/.env`、`config/settings.py`
- **文件写**：`drafts/YYYYMMDD-标题slug/draft.md`
- **shell**：仅 `python3` 执行辅助脚本

## 路由

从零发文、一条龙、完整流程 → [webchat-article-main](../webchat-article-main/SKILL.md)。

## 配置检查 ⛔

**任何操作执行前**，须确认 `config/.env` 中 `ARK_API_KEY` 存在且非空。

`config/settings.py` 中写作模型默认值：
- 模型：`doubao-seed-2-0-pro-260215`
- API URL：`https://ark.cn-beijing.volces.com/api/v3`

## 工作流

```
写稿进度：
- [ ] 第1步：⛔ 确认 ARK_API_KEY 已配置
- [ ] 第2步：确认写作意图（主题/大纲/参考素材）
- [ ] 第3步：生成文章大纲（generate_article_outline）
- [ ] 第4步：撰写完整文章（generate_article）
- [ ] 第5步：优化标题（optimize_title）
- [ ] 第6步：润色内容（polish_content）
- [ ] 第7步：保存到 drafts/ 目录
- [ ] 第8步：展示并等待用户确认 ⛔
```

### 第1步：配置检查 ⛔

确认 `config/.env` 中 `ARK_API_KEY` 已配置且非空。不通过时引导用户补全。

### 第2步：确定输入

**输入来源**：用户口述主题 / 已有大纲 / 已有草稿 / 参考素材

**写作方式**：
1. **优先**：调用 `src/tools/doubao_llm.py` 的 `generate_article_outline` + `generate_article`
2. **降级**：API 不可用时由 Agent 直接写稿（须告知用户）

### 第3步：生成大纲

使用 `generate_article_outline(topic, word_count)` 生成文章大纲。

```python
from src.tools.doubao_llm import generate_article_outline
outline = generate_article_outline(topic=topic, word_count=3000)
```

### 第4步：撰写文章

使用 `generate_article(title, outline, word_count)` 生成完整文章。

### 第5步：优化标题

使用 `optimize_title(titles)` 从候选标题中优化推荐。

### 第6步：润色内容

使用 `polish_content(content)` 对文章进行整体润色。

### 第7步：保存

- 创建目录：`drafts/YYYYMMDD-标题slug/`
- 保存 `draft.md`、`article.md`
- 创建 `article.yaml`（含 `publish_completed: false`）

### 第8步：展示并等待用户确认 ⛔

向用户展示文章，确认后移交下游 skill（themes / images / publish）。

## 过程文件

| 读取 | 产出 |
|------|------|
| `config/.env`、`config/settings.py` | `draft.md`、`article.md`、`article.yaml` |
