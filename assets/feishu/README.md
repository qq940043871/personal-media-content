# assets/feishu/ — 飞书发布资产（按知识库分文件夹）

## 结构

```
assets/feishu/
  <知识库名>/
    drafts/       # 待发布（.md 正文）
    published/    # 已发布（正文 + 同名 <文件名>.meta.json 记录 url/doc_id/published_at）
```

- **一个知识库 = 一个文件夹**，文件夹名必须能在 `.env` 的 `FEISHU_WIKI_SPACES` 里查到 space_id：
  `FEISHU_WIKI_SPACES=知识库A:space_id_1,知识库B:space_id_2`
- 发布时空间从路径推断：`assets/feishu/<知识库名>/drafts/x.md` → 发完自动移进 `<知识库名>/published/`。
- 尚未配置 `FEISHU_WIKI_SPACES` 时，`media-cli.py asset init` 会建一个占位目录 `默认知识库/`；
  配置好映射后再跑一次 init 会自动补齐真实知识库文件夹（占位目录需手工删除或改名）。
- 空目录带 `.gitkeep`（git 不跟踪空目录），且 `.gitkeep`/`.meta.json` 不进资产清单。

## 常用命令

```bash
python media-cli.py asset init                       # 按 FEISHU_WIKI_SPACES 建齐知识库文件夹
python media-cli.py asset spaces                     # 查看 名称 → space_id 映射
python media-cli.py asset ls --platform feishu --json
python media-cli.py asset publish --file assets/feishu/<知识库名>/drafts/x.md --json
```

小说章节批量发飞书不走这里，用 `python -m tools.novel_publisher`（幂等记录在
`storage/db/feishu_published.json`）。
