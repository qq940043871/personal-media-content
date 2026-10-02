---
name: webchat-article-agent
description: LangGraph智能体｜自动化工作流 — 基于LangGraph构建的文章发布智能体，串联大纲→写作→HTML转换→封面→配图→发布的完整自动化流程。面向高级用户、开发者。触发词：「自动生成」「智能体模式」「全自动」「批量生成」「LangGraph模式」「一键生成」。需要多环节串联也可以走webchat-article-main。
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

# LangGraph 智能体

**自动化文章发布工作流** —— 基于 LangGraph 的 StateGraph，串联大纲生成→文章撰写→HTML 转换→封面生成→配图生成→微信发布的完整自动化流程。

> **套件说明** · 本 skill 属 `webchat-article-*` 套件（共 6 个 slug，入口 `webchat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录。

## 脚本

| 脚本 | 用途 |
|------|------|
| `{baseDir}/scripts/run_agent.py run <title>` | 运行完整 LangGraph 工作流 |
| `{baseDir}/scripts/run_agent.py simple <title>` | 简化接口（只需标题） |

用法示例：

```bash
python {baseDir}/scripts/run_agent.py run "LangGraph 多智能体开发实战" --publish
python {baseDir}/scripts/run_agent.py run "Transformer 注意力机制" --type "原理分析" --length 5000
python {baseDir}/scripts/run_agent.py simple "RAG 系统架构设计"
```

## 能力披露（Capabilities）

本 skill 调用 `src/agents/agent.py` 的 `WeChatArticleAgent` + `main.py` 的 CLI 入口。使用 LangGraph `StateGraph` 编排多步骤工作流：

- **凭证读取**：`config/.env` 的 `ARK_API_KEY`、`WECHAT_APPID`、`WECHAT_APPSECRET`
- **凭证外发**：API key 发给火山方舟 LLM 和图像端点；微信凭证发给 `api.weixin.qq.com`
- **内容外发**：文章内容发给 LLM；图片描述发给 SeeDream；正文/封面发给微信
- **文件读**：`config/.env`、`config/settings.py`
- **文件写**：`assets/wechat/drafts/YYYYMMDD-标题slug/` 下的 `outline.md`、`article.md`、`article.html`、`imgs/`

## 路由

从零发文、一条龙、完整流程 → [webchat-article-main](../webchat-article-main/SKILL.md)。

## 架构

### ArticleState

LangGraph 的 `StateGraph` 使用 `ArticleState`（TypedDict）管理整个工作流的状态，包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | str | 文章标题 |
| `outline` | str | 文章大纲 |
| `content_markdown` | str | 文章 Markdown 正文 |
| `content_html` | str | 转换后的 HTML |
| `article_dir` | str | 文章目录路径 |
| `cover_path` | str | 封面图路径 |
| `images` | list | 配图路径列表 |
| `media_id` | str | 微信草稿 media_id |
| `error` | str | 错误信息 |

### 工作流节点

```
generate_outline_node (生成大纲)
    ↓
write_article_node (撰写文章)
    ↓
convert_html_node (Markdown → HTML)
    ↓
generate_cover_node (生成封面图)
    ↓
generate_article_images_node (生成配图)
    ↓
publish_draft_node (发布到微信)
```

### 使用方式

#### 方式一：交互式模式（推荐）

```bash
python main.py
```

进入交互式 CLI，输入主题即可启动完整流程。

#### 方式二：命令行模式

```bash
# 仅生成文章
python main.py "Transformer 注意力机制"

# 生成并保存到文件
python main.py "RAG系统架构设计" -o article.md

# 生成并自动发布到微信草稿箱
python main.py "LangGraph多智能体开发实战" -p
```

#### 方式三：程序化调用

```python
from src.agents import create_agent

agent = create_agent()
result = await agent.run(title="文章主题")
# result: {"title", "outline", "content_markdown", "content_html", "media_id", ...}
```

## 配置检查 ⛔

### 必需配置

- `config/.env` 中 `ARK_API_KEY` 须非空
- 如需发布到微信：`WECHAT_APPID` + `WECHAT_APPSECRET` 也须非空

### 配置验证命令

```bash
python -c "from config import get_settings; s=get_settings(); print('ARK_API_KEY:', bool(s.ARK_API_KEY)); print('WECHAT:', bool(s.WECHAT_APPID and s.WECHAT_APPSECRET))"
```

## 工作流

```
- [ ] 第1步：⛔ 配置检查（config/.env）
- [ ] 第2步：用户输入文章主题
- [ ] 第3步：生成大纲
- [ ] 第4步：撰写完整文章
- [ ] 第5步：转换 HTML
- [ ] 第6步：生成封面图
- [ ] 第7步：生成配图
- [ ] 第8步：发布到微信（可选）
- [ ] 第9步：展示结果
```

### 第1步：配置检查 ⛔

确认 `config/.env` 中 `ARK_API_KEY` 已配置且非空。

### 第2步：用户输入

交互式模式：提示用户输入文章主题。
命令行模式：通过 `sys.argv` 获取主题参数。

### 第3-8步：自动执行

LangGraph 自动执行 6 个节点，每个节点完成后状态更新到 `ArticleState`。

### 第9步：展示结果

输出文章标题、大纲预览、长度、草稿 media_id（如已发布）。

## 过程文件

| 读取 | 产出 |
|------|------|
| `config/.env`、`config/settings.py` | `assets/wechat/drafts/YYYYMMDD-标题slug/outline.md`、`article.md`、`article.html`、`imgs/` |
