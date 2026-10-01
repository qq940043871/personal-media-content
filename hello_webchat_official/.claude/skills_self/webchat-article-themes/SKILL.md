---
name: webchat-article-themes
description: 公众号排版主题｜视觉风格切换 — 5套预定义微信公众号文章视觉主题，覆盖科技、极简、温暖、商务、清新风格。面向公众号编辑、排版岗。触发词：「换个主题」「换主题」「改样式」「换个风格」「改颜色」「排版主题」「主题设置」「选主题」。需要多环节串联请走webchat-article-main。
homepage: https://github.com/haswhere/webchat-article-solo
url: https://github.com/haswhere/webchat-article-solo
metadata:
  openclaw:
    requires:
      env: []
      bins:
        - python3
---

# 排版主题

**文章视觉主题管理** —— 5 套预定义主题，覆盖技术教程、深度分析、实战分享、架构设计、新手入门等场景。

> **套件说明** · 本 skill 属 `webchat-article-*` 套件（共 6 个 slug，入口 `webchat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录。

## 脚本

| 脚本 | 用途 |
|------|------|
| `{baseDir}/scripts/apply_theme.py list` | 列出所有可用主题 |
| `{baseDir}/scripts/apply_theme.py apply <theme> <html>` | 应用主题到 HTML 文件 |

用法示例：

```bash
python {baseDir}/scripts/apply_theme.py list
python {baseDir}/scripts/apply_theme.py apply tech-blue article.html -o article-themed.html
python {baseDir}/scripts/apply_theme.py apply warm-orange article.html
```

## 能力披露（Capabilities）

**纯本地 skill**。零网络请求，零凭证需求。

- **文件读**：读取 `src/tools/wechat_themes.py` 中的主题定义
- **文件写**：无（仅展示主题信息）
- **网络**：无

## 可用主题

| 标识 | 名称 | 适用场景 |
|------|------|---------|
| `tech-blue` | 默认科技蓝 | 技术教程、原理分析类文章。深色代码块 + 蓝色系标题/链接，专业感强。 |
| `minimal-mono` | 极简黑白 | 深度观点、行业分析类文章。去掉所有装饰色，靠字号和间距区分层级。 |
| `warm-orange` | 温暖橙 | 实战分享、经验总结类文章。暖色调标题和强调色，营造轻松的阅读氛围。 |
| `business-navy` | 商务深蓝 | 架构设计、技术规范、行业报告类正式文章。深蓝主色调，稳重专业。 |
| `fresh-green` | 清新绿 | 新手教程、入门指南类文章。绿色系主线，清晰明快，降低阅读压力。 |

## 主题影响范围

每个主题定义以下元素的视觉样式：

- **标题**（h1-h4）：颜色、字号、边框、背景
- **代码块**：背景色、文字色、边框、语言栏
- **表格**：表头色、斑马纹、边框
- **行内元素**：加粗、行内代码、链接、列表标记
- **引用块**：背景、左边框
- **封面图渐变**：封面图的渐变色（与主题色系一致）

## 工作流

```
- [ ] 第1步：列出可用主题（list_themes）
- [ ] 第2步：用户选择主题
- [ ] 第3步：获取主题定义（get_theme）
- [ ] 第4步：应用到文章 HTML
- [ ] 第5步：展示效果并等待用户确认 ⛔
```

### 第1步：列出主题

```python
from src.tools.wechat_themes import list_themes
list_themes()
```

### 第2步：用户选择

询问用户选择哪个主题，或根据文章类型推荐。

### 第3步：获取主题

```python
from src.tools.wechat_themes import get_theme
theme = get_theme("tech-blue")
```

`LayoutTheme` 包含完整的样式定义（section、paragraph、heading、code_block、table、inline、blockquote、cover_gradient）。

### 第4步：应用

读取文章 HTML，将主题样式应用于内联 CSS 属性（标题颜色/边框、代码块样式、表格颜色等）。

### 第5步：展示

展示应用主题后的效果，等待用户确认。

## 代码示例

```python
from src.tools.wechat_themes import get_theme, list_themes, THEMES

# 列出所有主题
list_themes()

# 获取特定主题
theme = get_theme("warm-orange")

# 访问主题属性
print(theme.name)                          # "温暖橙"
print(theme.heading.h2_border_left)        # "5px solid #ed8936"
print(theme.cover_gradient_start)          # "237,137,54"
```

## 路由

从零发文、一条龙、完整流程 → [webchat-article-main](../webchat-article-main/SKILL.md)。
