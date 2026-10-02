# .claude/skills — 项目技能库（公众号官方文章技能线）

原 `hello_wechat/official/`（公众号官方文章技能流水线）2026-10 并入主工程：
技能包统一放本目录，工作文件回到仓库根约定，稿件包归入资产库。

## 两族技能

- `aws-wechat-article-*` + `aws-wechat-sticker`：选题/写作/配图/格式化/审稿/发布全流水线（上游技能包）
- `webchat-article-*`：本线自维护技能（agent 编排、主题、写作、配图、发布）

各技能的用法见其 `SKILL.md`；主线入口为 `aws-wechat-article-main/SKILL.md`。

## 工作文件约定（与技能文本一致）

```
仓库根/
  aws.env                    # 密钥与微信账号槽位（不入库）
  .aws-article/              # 运行配置与 presets（config.yaml 含密钥，不入库）
    ├── presets/             # 封面/格式/结构/标题等预设
    ├── config.yaml          # 真实配置（仅存本地磁盘）
    └── tmp/                 # 运行时临时目录（不入库）
assets/wechat/drafts/        # 本篇稿件包 YYYYMMDD-AX/
    └── <篇名>/
        ├── article.md / article.html / article.yaml
        ├── cover.png
        └── imgs/cover_prompt.md
```

## 常用流程

1. 选题、写大纲、成文（`aws-wechat-article-main/SKILL.md`）
2. 稿件落在 `assets/wechat/drafts/<日期>-<编号>/`
3. 配图与封面按 `aws-wechat-article-images` 技能生成
4. 发布走 `aws-wechat-article-publish`（默认进公众号草稿箱；`publish_method` 由
   `.aws-article/config.yaml` 控制）

> 凭据与 `.aws-article/` 由根 `.gitignore` 的 `*.env` / `**/.aws-article/*` 规则保护，永不入库。
