---
name: webchat-article-main
description: 公众号写作助手｜AI文章生成｜微信公众号发布｜全流程编排 — 微信公众号AI文章写作全流程总控入口，主题输入→大纲→写稿→排版→封面图→配图→发布串联5个子skill，单条指令完成整篇图文从0到发布。面向技术自媒体、AI内容创作者、公众号运营。触发词分层：**完整流程**「写一篇公众号文章」「帮我写篇文章」「从0到发布」「完整流程」「做一篇公众号」「帮我发一篇」；**写作起点**「写一篇关于...的文章」「帮我写篇关于...的技术文章」「生成文章」；**流程恢复**「继续上次那篇」「接着之前的进度」「继续昨天的」；**单步路由**「帮我起标题」「润色文章」「生成封面」「配图」「发布到微信」「换个主题」「审稿」。子skill（writing/images/publish/themes/agent）单独触发仅限对**已有产物**的修改场景；新做/多环节串联一律走本入口。
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

# 公众号写作助手总览

**一键式 AI 内容流水线** —— 从主题输入到微信发布，5 个子 skill 串联，技术自媒体 / AI 内容创作者 / 公众号运营一键产出整篇图文。

> **套件说明** · `webchat-article-*` 是微信公众号AI写作套件，共 6 个 slug：`webchat-article-main / writing / images / publish / themes / agent`。跨 skill 的相对引用依赖同一 `skills/` 根目录。

## 能力披露（Capabilities）

本 skill 作为套件**编排入口**；真正调用外部 API 的是子 skill（writing / images / publish / agent）。**本入口自身行为**：

- **凭证读取**：读取 `config/.env` 中的 `ARK_API_KEY`、`WECHAT_APPID`、`WECHAT_APPSECRET`，**仅用于校验键是否存在且非空**
- **网络**：本入口无外发请求；**子 skill 有外发**（详见各子 skill 的能力披露）
- **文件读**：项目内 `config/settings.py`、`config/.env`
- **shell**：仅 `python3` 执行子 skill 脚本

> **注意**：整体套件（含子 skill）会调用豆包 LLM API、SeeDream 图像 API 与微信 API，并在调用时外发 API key 与文章内容。完整行为见各子 skill 的「能力披露」。

## 配套 skill

本 skill 是 `webchat-article-*` 套件的入口，编排 5 个子 skill：`writing / images / publish / themes / agent`。

- **装齐全部 6 个 slug** 到同一 `skills/` 根目录，才能走完整流程（主题→写稿→主题→配图→发布）。
- 只装 main 一个时，仍可用于环境校验；进入内容流水线会因对应子 skill 缺失而无法执行相关步骤。

**Agent 执行**：确定本 SKILL.md 所在目录为 `{baseDir}`。

## 脚本

| 脚本 | 用途 |
|------|------|
| `{baseDir}/scripts/validate_env.py` | 校验 `config/.env` 中 ARK_API_KEY 和微信凭证 |

## 配置检查 ⛔ BLOCKING

### 第 0 步：判断操作系统

智能体在执行下列检测命令前，**先判断当前环境**：

- **Linux / macOS**：使用 Bash 命令（`test`、`echo` 等）。
- **Windows**：使用 **PowerShell** 命令（`Test-Path` 等）。

### 第 1 步：`config/.env` 与 `config/settings.py` 是否存在

在**项目根目录**（当前工作目录为项目根）执行：

**Linux / macOS：**
```bash
test -f config/.env && test -f config/settings.py && echo "ok" || echo "missing"
```

**Windows（PowerShell）：**
```powershell
if ((Test-Path -LiteralPath "config\.env") -and (Test-Path -LiteralPath "config\settings.py")) { "ok" } else { "missing" }
```

⛔ 输出为 `missing` → 创建 `config/.env`（参考 `config/.env.example`），填入 `ARK_API_KEY`。

### 第 2 步：校验 `config/.env` 内容

两文件均存在后，读 `config/.env` 检查：

- **`ARK_API_KEY`** 须存在且非空，且不等于占位符 `your_ark_api_key_here`
- **写作模型**：代码默认 `doubao-seed-2-0-pro-260215`，URL 默认 `https://ark.cn-beijing.volces.com/api/v3`

**不通过** → 引导用户补全 `config/.env`。

### 第 3 步：微信配置（仅发布前需要）

如果用户明确要发布到微信：

- **`WECHAT_APPID`** 和 **`WECHAT_APPSECRET`** 须在 `config/.env` 中非空
- 缺微信字段时：引导用户补全，或设 `publish_method: none` 跳过

**智能体行为约束（禁止自作主张）**：
- **禁止**在未询问用户的情况下，自行决定跳过微信配置或假装流程完整
- Agent **不得索取、不得接收**用户在对话里粘贴的 `APPSECRET` / `API_KEY`；所有密钥由用户在编辑器里写入 `config/.env`
- Agent 只校验存在性、不读取值、不外发值

## 主要配置文件

| 文件 | 位置 | 作用 |
|------|------|------|
| `config/.env` | 项目根下 config/ | **密钥**：`ARK_API_KEY`、`WECHAT_APPID`、`WECHAT_APPSECRET` |
| `config/settings.py` | 项目根下 config/ | Pydantic Settings：模型名、URL、调试开关等 |
| `config/.env.example` | 项目根下 config/ | 模板，`ARK_API_KEY=your_ark_api_key_here` |

### 发布方式

1. **默认**：`draft` 模式，只进微信草稿箱不自动群发
2. **published**：创建草稿后提交发布（异步）
3. **none**：不接微信，跳过发布步骤

## 交互顺序（一步步，最小提问）

按以下顺序与用户交互，**上一步完成再进下一步**。

### 1) 配置自检（必做）

按上文 **配置检查** 完成：`config/.env` 存在且 `ARK_API_KEY` 非空 → 进入下一步。

### 2) 写作意图确认

- **必须问清用户本篇要写什么**（具体主题、角度、体裁或目标）
- 用户已说清楚的，口头确认即可，不必重复盘问

### 3) 本篇准备

#### A. 新建一篇（默认）

1. **定题**：确定文章标题，生成 slug
2. **建目录**：创建 `drafts/YYYYMMDD-标题slug/`
3. **初始化元数据**：创建 `article.yaml`（含 `publish_completed: false`）

#### B. 我已有草稿

- 用户给出路径 → 读取 `drafts/…/article.yaml` → 判断是否继续

### 4) 内容流水线（子 skill）

```
写稿 → 应用主题 → 配图 → 发布
```

1. **写稿**（[writing](../webchat-article-writing/SKILL.md)）：生成大纲 → 写全文 → 润色
2. **主题**（[themes](../webchat-article-themes/SKILL.md)）：用户选主题 → 应用排版样式
3. **配图**（[images](../webchat-article-images/SKILL.md)）：生成封面 + 正文配图
4. **发布**（[publish](../webchat-article-publish/SKILL.md)）：微信草稿箱或发布

### 5) 发布后

- 输出小结与回执
- 记录 `publish_completed: true`

## 路由

| 用户说法 | 路由到 |
|---------|--------|
| 写一篇公众号文章、帮我写篇文章、从0到发布、完整流程、做一篇公众号、帮我发一篇（含各前置步） | **main** |
| **只要**起标题、润色、改写、续写（已有草稿，不要全流程） | writing |
| **只要**封面、配图、插图（有正文或插图位） | images |
| **只要**执行发布/提交/群发（已有约定产物） | publish |
| **只要**换主题、改样式、选主题 | themes |
| 自动生成、智能体模式、全自动、LangGraph模式 | agent |

## 流程

```
写稿 → 主题 → 配图 → 发布
```

## 中间产物门禁

| 阶段 | 必要产物 | 缺失时动作 |
|------|---------|------------|
| 写稿完成 | `article.md` 存在且非空 | 继续写稿 |
| 配图完成 | 封面图存在，正文无 placeholder | 先执行 images 生成 |
| 发布就绪 | 元数据齐全，环境检查通过 | 先补环境 |
| 发布闭环 | 发布命令成功且回执可用 | 才写回 `publish_completed: true` |

## 运行模式

### 一条龙

用户说「写一篇公众号文章」「完整流程」时启用。按交互顺序 1→2→3→4→5 执行；流水线中每步完成后暂停等用户确认。

### 单步

用户**明确只要某一步**且已有对应输入产物时，可仅执行该步骤。

### 智能体模式

路由到 **webchat-article-agent** skill，使用 LangGraph 全自动流程。
