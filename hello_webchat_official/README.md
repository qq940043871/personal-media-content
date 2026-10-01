# hello_webchat_official — 公众号官方文章技能流水线

基于 Claude 技能（`.claude/skills/` 与 `skills_self/`）的微信公众号选题、写作、配图、审稿与发布流程。

## 目录地图

```
hello_webchat_official/
├── README.md
├── .aws-article/              # 运行配置与 presets
│   ├── presets/               # 封面/格式/结构/标题等预设
│   ├── config.yaml            # 真实配置（含密钥），仅存本地磁盘，不入库
│   └── tmp/                   # 运行时临时目录，不入库
├── .claude/
│   ├── skills/                # aws-wechat-article-* 技能包
│   └── skills_self/           # 本线自维护技能
└── drafts/                    # 按日期编号的稿件包
    └── YYYYMMDD-AX/
        ├── article.md / article.html / article.yaml
        ├── cover.png
        └── imgs/cover_prompt.md
```

> `aws.env`（密钥）等本地文件不入库，按需放在本线目录下（见根 `.gitignore`）。

## 常用流程

1. 在技能规范下选题、写大纲、成文（见 `.claude/skills/aws-wechat-article-main/SKILL.md`）
2. 稿件落在 `drafts/<日期>-<编号>/`
3. 配图与封面按 `aws-wechat-article-images` 技能生成
4. 审稿、发布按 `aws-wechat-article-review` / `aws-wechat-article-publish`

也可使用仓库根统一发布（配置好公众号凭证后）：

```bash
python media-cli.py wechat publish --title "标题" --content-file drafts/.../article.md
```

## 文档

| 路径 | 说明 |
|------|------|
| `.claude/skills/aws-wechat-article-main/SKILL.md` | 主流程 |
| `.claude/skills/*/references/` | 预设、清单、API 参考 |
| `.claude/skills_self/` | 自维护技能变体 |

## 状态

- 草稿：`20260620`–`20260712` 若干包，完整度不一（有的仅有 yaml/封面提示词）
- 与 `hello_webchat_solo` 的区别：本线以**技能包**驱动；solo 是**独立 Python 程序**
