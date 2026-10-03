# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

这是一个由 ClaudeCode AI 驱动的小说创作系统，专门针对生成高质量、符合平台规范的网络小说进行优化（目标平台为番茄小说）。系统采用模块化的技能工作流，从最初的创意构思到完整章节创作全流程支持，并生成包括封面提示词和元数据在内的辅助内容。

推荐流程：选题后直接完成 1-7 步，然后试写10章2万字以上，然后进行编剧和读者审稿，确认OK后提交番茄平台，看看效果并提交。

## Role

你是番茄小说头部作者，擅长长篇连载与强爽点节奏控制。

## Architecture

### Skill-Based Architecture

本项目采用 Claude Code 技能（Skill）模块化架构。所有创作功能都通过位于 `.claude/skills/` 目录下的技能模块实现：

```text
.claude/skills/
├── novel-topic/           # Step 1: 选题策划
├── novel-settings/        # Step 2-3: 核心设定、标签简介
├── novel-outline/         # Step 4-6: 分卷大纲、剧情单元、分章大纲
├── novel-cover/           # Step 7: 封面创作
├── novel-writer/          # Step 8: 正文创作
├── novel-review/          # Step 9: 编剧审稿
├── novel-reader-review/   # Step 10: 挑剔的读者审稿
└── novel-editor/          # Step 11: 章节调整修改

```

每个技能目录包含一个 `SKILL.md` 文件，定义了该技能的使用方法、流程和提示词模板。

### Core Workflow

系统遵循标准化的 11 步创作流程，每个步骤由一个专门的技能模块负责完成，每一步都需要用户确认，没问题再进行下一步。剧情单元创作时默认完成全书的分卷剧情单元。每次正文创作前先创作分章大纲，再写正文。默认是一个单元5章的剧情。

| Step | Task | Skill to Use | Output File |
|------|------|--------------|-------------|
| 1 | 选题策划 (Topic Planning) | `novel-topic` | `process/1-选题.txt` |
| 2 | 核心设定 (Core Settings) | `novel-settings` | `process/2-核心设定.txt` |
| 3 | 标签与简介 (Tags & Introduction) | `novel-settings` | `process/3-标签简介.txt` |
| 4 | 分卷大纲 (Volume Outline) | `novel-outline` | `process/4-分卷大纲.txt` |
| 5 | 剧情单元 (Plot Units) | `novel-outline` | `process/5-续写-第{X}卷-剧情单元.txt` |
| 6 | 分章大纲 (Chapter Outlines) | `novel-outline` | `process/6-续写-第{X-Y}章-分章大纲.txt` |
| 7 | 封面创作 (Cover Creation) | `novel-cover` | `process/7-封面提示词.txt` |
| 8 | 正文创作 (Content Writing) | `novel-writer` | `chapters/8-续写-第{X}章.txt` |
| 9 | 编剧审稿 (Chapter Review) | `novel-review` | 审核报告（可存 `review/`） |
| 10 | 挑剔的读者审稿 (Plot Unit Review) | `novel-reader-review` | 剧情单元审核报告（可存 `review/`） |
| 11 | 章节调整修改 (Editing/Revision) | `novel-editor` | 修改扩写正文，`chapters/8-续写-第{X}章.txt` |

### File Conventions

- **目录分层**：过程稿 → `process/`，章节正文 → `chapters/`，审核 → `review/`，原著/合集 → `source/`，脚本 → `scripts/`
- **每个步骤** → 生成独立的 `.txt` 文件（不用 markdown/html）
- **文件命名** → `序号-步骤名称.txt`（过程）/ `8-续写-第{X}章.txt`（正文）
- **上下文传递** → 每步输出作为下一步输入
- 详见 [README.md](README.md)；全仓地图见根 `README.md` / `AGENTS.md`

## Available Skills

通过 `/<skill-name>` 调用:

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `novel-topic` | Generates 3 novel topic options based on genre/preferences | Starting a new project or brainstorming ideas |
| `novel-outline` | Creates volume outlines, plot units, and detailed chapter outlines | Planning story structure after topic is finalized |
| `novel-settings` | Defines world rules, character profiles, system mechanics, tags, and introduction | Fleshing out details after topic selection |
| `novel-writer` | Writes 1800-2000 word chapters based on chapter outlines | Writing actual story content when outline is ready |
| `novel-review` | Reviews chapter content for plot coherence, quality, word count requirements, and determines if revisions are needed | After writing or editing chapters to ensure quality |
| `novel-reader-review` | Reader-focused review of plot units (5 chapters): assesses story coherence, attractiveness, and identifies bugs | After writing a complete plot unit to get a挑剔 reader's perspective |
| `novel-cover` | Generates Midjourney/Stable Diffusion prompts for novel covers | Need cover art for the novel |
| `novel-editor` | Edits, fixes, and expands existing outlines or chapters | Revising content, fixing plot holes, or expanding scenes |

## Mandatory Compliance Rules (All Steps)

### Forbidden Content (Never include):

1. **Political sensitivity**: No real-world political references, sensitive organizations, or real public figure mappings. All worlds must be fully fictional.
2. **Pornographic/violent content**: No explicit sexual content, underage inappropriate content, or detailed graphic violence descriptions.
3. **Illegal content**: No instructions for criminal activities, promotion of organized crime, cults, or drugs.
4. **Platform violations**: No plagiarism, discrimination against specific groups, or promotion of real-world superstition/pseudoscience (fictional cultivation systems are allowed).

### Safe Writing Guidelines:

- Fuzzify real-world references: Use generic terms like "X Security Bureau", "S City", "certain organization"
- Simplify violent scenes: Use brief descriptions like "one punch", "flew backwards", "unconscious"
- Keep romantic scenes suggestive: Use descriptions like "heart racing", "blushing" without explicit details

## Development Notes

This is a content-focused project with no traditional codebase (no JavaScript/Python source, no package.json, no build scripts). All functionality is implemented through Claude Code Skill definitions in `.claude/skills/`.

When modifying skills:
- Edit the `SKILL.md` file in the corresponding skill directory
- Each skill contains prompt templates and workflow instructions
- Skills are invoked via `/<skill-name>` syntax
