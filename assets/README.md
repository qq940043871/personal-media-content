# assets/ — 创作资产库 + 发布状态流转

本仓的**内容资产总库**（2026-10 起，原 hello_novel / hello_doubao_video / family-life-video 内容收敛于此），
同时是 tools/ 发布工具的**数据契约**：技能的输入输出都落在这里，技能之间无隐藏状态。

## 结构

```
assets/
  novels/                        # 创作资产：每本小说/主题一个文件夹
    <书名>/                      #   小说书目（含 chapters/ 或 novel/chapters/，正文+过程稿全在此）
      drafts/ published/         #     该书的发布资产状态区（每本小说一个资产文件夹）
    <主题>/                      #   亲情视频主题（短视频脚本.md、视频分镜脚本.md）与 guides 文集
  douyin/                        # 短视频线（原 hello_doubao_video）— 一个文件夹
    README.md  docs/  scripts/   #   提示词、方案、去水印/合并脚本
    media/                       #   mp4 原件不入库（.gitignore 拦截）
    assets/                      #   帧图等运行时生成，不入库
    drafts/ published/           #   发布资产状态区
  wechat/                        # 公众号 — 一个文件夹
    drafts/ published/           #   发布资产状态区（图文 .md）
  feishu/                        # 飞书 — 按知识库分文件夹（名称须配 FEISHU_WIKI_SPACES）
    <知识库名>/drafts|published/ #   一个知识库一个文件夹；未配置映射时占位为 默认知识库/
```

**一键建骨架**（幂等，新增书目/知识库后重跑即可补齐；空目录写 `.gitkeep`，git 才跟踪得到）：

```bash
python media-cli.py asset init
```

## 发布状态流转（drafts → published）

- 草稿放 `drafts/`；发布成功后由工具**自动移入 `published/`** 并写同名 `<文件名>.meta.json`
  （记录 platform / space / title / url / id / published_at）。
- 同一篇内容发多个平台 = 各目标的 drafts/ 各放一份，各自归档。
- 本目录**入库**（Markdown/正文/元数据）；视频等大文件与帧图仍被根 .gitignore 的类型规则拦截。
- 空目录靠 `.gitkeep` 占位（git 不跟踪空目录）；`.gitkeep` 与 `.meta.json` 都不进资产清单。
- 小说章节批量发飞书走 `python -m tools.novel_publisher`（幂等记录在 `storage/db/feishu_published.json`），
  不占 drafts/published 状态区。

## 常用命令

```bash
python -m tools.asset_store init                            # 建齐目录骨架（等价 media-cli.py asset init）
python -m tools.asset_store ls --platform wechat --json     # 发布资产清单
python -m tools.asset_store put --platform wechat --name x.md --content-file 本地.md
python -m tools.asset_store publish --file assets/wechat/drafts/x.md --json  # 发布并自动归档
python -m tools.asset_store spaces                           # 飞书知识库映射
```

也可以直接把文件放进对应 drafts/ 后调用平台工具：

```bash
python -m tools.wechat publish --asset assets/wechat/drafts/x.md --json
python -m tools.feishu publish --asset assets/feishu/我的知识库/drafts/x.md --json
python -m tools.douyin publish --asset assets/douyin/drafts/v.mp4 --json
```

创作统计（dashboard 首页 / `python media-cli.py status`）按本目录盘点：
书目章节数/字数、主题/文集份数、发布资产 drafts/published 计数、发布记录。
