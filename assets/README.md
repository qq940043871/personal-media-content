# assets/ — 创作资产库（工程 × 状态流转）

本仓的**内容资产总库**，同时是 publishing/ 发布工具的**数据契约**：技能的输入输出都落在这里，
技能之间无隐藏状态。

原则：**按作品建工程、按平台做动作**——工程（创作域/工程名）是独立创作空间；
发布平台由创作域默认（TYPE_PLATFORM）或 `--platform` 指定，成功后归档回本工程。

## 结构（类型 / 工程 / 状态 三级）

```
assets/
  novels/                        # 小说工程（原样保留，早已是工程制）
    <书名>/                      #   chapters/ process/ source/ ... + 该书的 drafts/ published/
    <主题>/                      #   亲情视频主题（短视频脚本.md、视频分镜脚本.md）与 guides 文集
  articles/                      # 图文工程 → 默认发公众号（wechat）
    公众号/drafts/<篇名>/         #   公众号技能线工作区（article.yaml + article.md + cover + imgs）
    公众号/published/             #   已发布归档 + <文件名>.meta.json
    <专栏名>/drafts|published/    #   其他图文工程同构
  videos/                        # 短视频工程 → 默认发抖音（douyin）
    douyin/                      #   短视频工具与素材区（docs/ scripts/ media/ assets/）
    <系列名>/drafts|published/   #   系列工程的发布状态区
  wikis/                         # 知识库工程 → 默认发飞书（feishu）
    <知识库名>/drafts|published/ #   名称须配 FEISHU_WIKI_SPACES；未配置时占位 默认知识库/
```

**一键建骨架**（幂等；articles/videos 只建域目录、工程自建，wikis 按知识库、novels 按书目；
空目录写 `.gitkeep`）：

```bash
python media-cli.py asset init
```

## 发布状态流转（drafts → published）

- 草稿放工程 `drafts/`；发布成功后由工具**自动移入本工程 `published/`** 并写同名
  `<文件名>.meta.json`（记录 type / project / platform / title / url / id / published_at）。
- 同一篇发多平台：`--platform` 覆盖默认目标，各自归档一份。
- 本目录**入库**（Markdown/正文/元数据）；mp4 等媒体原件被根 .gitignore 类型规则拦截。
- `.gitkeep` 与 `.meta.json` 都不进资产清单；工程内的子文件夹（如技能线的 `<篇名>/`）
  也不进清单（清单只收单文件资产）。
- 小说章节批量发飞书走 `python -m publishing.novel_publisher`（幂等记录在
  `system/storage/db/feishu_published.json`），不占 drafts/published 状态区。
- 旧版平台平铺布局（`wechat|douyin/<状态>/`、`feishu/<库>/<状态>/`）仍可识别、发布与归档
  （按原布局回流），新工程一律用上面的三级布局。

## 常用命令

```bash
python -m publishing.asset_store init                                       # 建齐目录骨架（等价 media-cli.py asset init）
python -m publishing.asset_store ls --type articles --json                  # 发布资产清单
python -m publishing.asset_store put --type articles --project 我的专栏 --name x.md --content-file 本地.md
python -m publishing.asset_store publish --file assets/articles/我的专栏/drafts/x.md --json  # 发布并自动归档
python media-cli.py asset publish --file assets/articles/我的专栏/drafts/x.md --platform feishu  # 覆盖默认平台
python -m publishing.asset_store spaces                                     # 飞书知识库映射
```

也可以直接把文件放进对应 drafts/ 后调用平台工具：

```bash
python -m publishing.wechat publish --asset assets/articles/公众号/drafts/x.md --json
python -m publishing.feishu publish --asset assets/wikis/我的知识库/drafts/x.md --json
python -m publishing.douyin publish --asset assets/videos/douyin/drafts/v.mp4 --json
```

创作统计（dashboard 首页 / `python media-cli.py status`）按本目录盘点：
书目章节数/字数、主题/文集份数、发布资产 drafts/published 计数、发布记录。
