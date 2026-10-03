---
name: webchat-article-publish
description: 公众号发布｜草稿箱｜API发布 — 将文章发布到微信公众号草稿箱，支持Markdown→HTML转换、封面上传、草稿创建。面向公众号运营、技术自媒体。触发词：「发布」「提交」「群发」「推送」「发出去」「上传到公众号」「发到公众号」「可以发了吗」。需要多环节串联请走webchat-article-main。
homepage: https://github.com/haswhere/webchat-article-solo
url: https://github.com/haswhere/webchat-article-solo
metadata:
  openclaw:
    requires:
      env:
        - WECHAT_APPID
        - WECHAT_APPSECRET
      bins:
        - python3
    primaryEnv: config/.env
---

# 发布

**公众号 API 直连发布** —— 图文入草稿箱，Markdown→HTML 转换、封面上传一站式完成。

> **套件说明** · 本 skill 属 `webchat-article-*` 套件（共 6 个 slug，入口 `webchat-article-main`）。跨 skill 的相对引用依赖同一 `skills/` 目录。

## 脚本

| 脚本 | 用途 |
|------|------|
| `{baseDir}/scripts/publish.py draft <md_file>` | 发布 Markdown 文件到微信草稿箱 |
| `{baseDir}/scripts/publish.py check` | 检查微信配置是否就绪 |
| `{baseDir}/scripts/publish.py info` | 显示发布信息 |

用法示例：

```bash
python {baseDir}/scripts/publish.py check
python {baseDir}/scripts/publish.py draft article.md --title "文章标题" --author "作者"
python {baseDir}/scripts/publish.py draft assets/articles/公众号/drafts/20260610-文章标题/ --title "文章标题"
```

## 能力披露（Capabilities）

本 skill 调用 `main.py` 中的 `publish_to_wechat` **直连微信公众号官方 API** 发布图文。具体行为：

- **凭证读取**：`config/.env` 的 `WECHAT_APPID` / `WECHAT_APPSECRET`
- **凭证外发**：`APPID` / `APPSECRET` 以 query string 发给 `api.weixin.qq.com/cgi-bin/token` 换 `access_token`
- **内容外发**：封面以 multipart upload 发给 `material/add_material`；正文 HTML 以 JSON POST 发给 `draft/add`
- **网络目标**：`api.weixin.qq.com`
- **文件读**：`config/.env`、`config/settings.py`、文章目录下的 `article.md` 或 `article.html`
- **文件写**：发布结果日志（可选）

## 配套 skill

本 skill 是 `webchat-article-*` 套件的**发布环节**（入口 `webchat-article-main`）。

## 配置检查 ⛔

### `publish_method`

| 值 | 含义 | 行为 |
|----|------|------|
| **`draft`**（默认） | 只进公众号**草稿箱** | 创建草稿后不提交发布 |
| **`published`** | 草稿 + **提交发布** | 创建草稿后继续提交发布（异步） |
| **`none`** | 用户明确不填微信 | 跳过所有微信 API 调用 |

### 环境要求

- `config/.env` 中 `WECHAT_APPID` 和 `WECHAT_APPSECRET` 须非空
- 可通过 `python -c "from config import get_settings; s=get_settings(); print(bool(s.WECHAT_APPID and s.WECHAT_APPSECRET))"` 验证

## 工作流

```
发布进度：
- [ ] 第1步：⛔ 确认微信配置已就绪
- [ ] 第2步：读取文章 markdown 内容
- [ ] 第3步：转换 HTML（markdown_to_wechat_html）
- [ ] 第4步：上传封面图（upload_thumb_media）
- [ ] 第5步：创建草稿（add_draft）
- [ ] 第6步：输出结果 media_id
```

### 第1步：配置检查 ⛔

确认 `WECHAT_APPID` 和 `WECHAT_APPSECRET` 在 `config/.env` 中已配置且非空。

### 第2步：读取文章

读取 `assets/articles/公众号/drafts/YYYYMMDD-标题slug/article.md` 或用户指定的 markdown 文件。

### 第3步：转换 HTML

```python
from main import markdown_to_wechat_html
html = markdown_to_wechat_html(md_content)
```

处理微信的 CSS 限制：内联样式、不支持 `<style>` 标签、不支持 `border-radius`/`linear-gradient`。

### 第4步：上传封面

```python
from main import upload_thumb_media
thumb_media_id = upload_thumb_media(access_token, title)
```

### 第5步：创建草稿

```python
from main import add_draft
media_id = add_draft(access_token, title, content_html, thumb_media_id, author)
```

### 第6步：输出结果

展示 `media_id`，记录到 `article.yaml`。

## 命令示例（项目根）

```bash
python main.py "文章标题" -p
python main.py "文章标题" -o article.md -p
```

## 过程文件

| 读取 | 产出 |
|------|------|
| `config/.env`、`config/settings.py`、`article.md`/`article.html` | 发布到公众号草稿箱；`media_id` 回执 |
