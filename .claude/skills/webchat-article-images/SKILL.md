---
name: webchat-article-images
description: 公众号封面｜配图生成｜AI插图 — 使用豆包SeeDream模型为文章生成封面图和正文配图，支持多种风格预设。面向公众号编辑、技术自媒体。触发词：「封面」「配图」「插图」「生成图片」「给文章加图」「做个封面」「文章插图」「配图」。不写正文只发一组图请走webchat-article-agent；需要多环节串联请走webchat-article-main。
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

# 配图生成

**AI 文章配图引擎** —— 使用豆包 SeeDream 模型为公众号文章生成封面图和正文插图，支持 PIL 回退方案。

> **套件说明** · 本 skill 属 `webchat-article-*` 套件（共 6 个 slug，入口 `webchat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录。

## 脚本

| 脚本 | 用途 |
|------|------|
| `{baseDir}/scripts/generate_images.py cover <title>` | 生成文章封面图 |
| `{baseDir}/scripts/generate_images.py image <description>` | 生成单张配图 |
| `{baseDir}/scripts/generate_images.py batch <file>` | 从 Markdown 扫描配图标记批量生成 |

用法示例：

```bash
python {baseDir}/scripts/generate_images.py cover "文章标题" -s tech -o imgs/
python {baseDir}/scripts/generate_images.py image "系统架构图描述" -t architecture -o imgs/
python {baseDir}/scripts/generate_images.py batch article.md -o imgs/
```

## 能力披露（Capabilities）

本 skill 调用 `src/tools/generate_image.py` 的 `ImageGenerator`，**会把图片描述发送到火山方舟 SeeDream 图像生成 API**：

- **凭证读取**：`config/.env` 的 `ARK_API_KEY`
- **凭证外发**：API key 以 `Authorization: Bearer <key>` 头发送到图像生成端点
- **内容外发**：图片描述 prompt（可能包含文章标题/章节摘要）发送给 SeeDream 模型
- **文件读**：`config/.env`、`config/settings.py`、文章目录下的 `article.md`
- **文件写**：文章目录下的 `imgs/cover.png`、`imgs/img_*.png`
- **shell**：仅 `python3` 执行辅助脚本

**回退机制**：当 SeeDream API 不可用时，使用 PIL（`_build_default_cover_bytes`）生成渐变色封面图，无配图。

## 路由

从零发文、一条龙、完整流程 → [webchat-article-main](../webchat-article-main/SKILL.md)。

## 配置检查 ⛔

`config/.env` 中 `ARK_API_KEY` 须存在且非空。

图像模型默认值（`config/settings.py`）：
- 模型：`doubao-seedream-5-0-260128`
- API URL：`https://ark.cn-beijing.volces.com/api/v3`

## 封面图 vs 配图

### 封面图

- **AI 生成**：使用 `generate_cover_image(title, style)` 调用 SeeDream
- **PIL 回退**：使用 `_build_default_cover_bytes(title)` 生成 900×383 蓝紫渐变图
- **风格**：`tech-blue` / `minimal-mono` / `warm-orange` / `business-navy` / `fresh-green`

### 正文配图

- **AI 生成**：使用 `generate_article_image(description, image_type)` 按描述生成
- **批量处理**：使用 `generate_image_from_markdown(article_content)` 扫描 `[配图：描述]` 标记批量生成
- **占位替换**：将 `![类型名：画面内容](placeholder)` 替换为实际图片引用

## 工作流

```
- [ ] 第1步：⛔ 确认 ARK_API_KEY 已配置
- [ ] 第2步：读取文章 `article.md`
- [ ] 第3步：扫描配图标记 `[配图：...]` 或 `![...](placeholder)`
- [ ] 第4步：生成封面图
- [ ] 第5步：逐一生成配图
- [ ] 第6步：保存到 `imgs/` 目录
- [ ] 第7步：更新 `article.md` 中的图片引用
- [ ] 第8步：展示结果并等待用户确认 ⛔
```

### 第1步：配置检查 ⛔

确认 `config/.env` 中 `ARK_API_KEY` 已配置且非空。

### 第2步：读取文章

读取 `assets/articles/公众号/drafts/YYYYMMDD-标题slug/article.md` 获取文章内容和配图标记。

### 第3步：分析配图需求

扫描文章中的配图标记：
- `[配图：描述]` → 按描述生成
- `![类型名：画面内容](placeholder)` → 按画面内容生成

### 第4步：生成封面

```python
from src.tools.generate_image import generate_cover_image
result = generate_cover_image(title="文章标题", style="tech-blue")
```

### 第5步：生成配图

```python
from src.tools.generate_image import generate_image_from_markdown
result = generate_image_from_markdown(article_content)
```

### 第6步：保存

保存到 `assets/articles/公众号/drafts/YYYYMMDD-标题slug/imgs/`。

### 第7步：更新引用

将 `article.md` 和 `article.html` 中的 `placeholder` 替换为实际图片路径。

### 第8步：展示并确认 ⛔

展示生成的封面和配图，等待用户确认。

## 过程文件

| 读取 | 产出 |
|------|------|
| `config/.env`、`config/settings.py`、`article.md` | `imgs/cover.png`、`imgs/img_*.png` |
