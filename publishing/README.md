# publishing/ — 对外动作层（发布工具，skill 化预备）

与 `core/`（对内能力层：config / providers / 内容转化 / 存储与统计）的分工：
**core 是被 import 的库，tools 是可独立运行的命令**——每个工具未来对应一个 skill，
封装时只需一层 `SKILL.md`（触发词 + 说明）+ 一行 `python -m publishing.*` 调用。

## 接口契约（每个工具必须遵守）

1. **可独立运行**：`python -m publishing.<tool> <action>`；路径锚定仓库根，不依赖调用方 CWD
2. **统一输出**：默认人读文本，`--json` 输出机器可读结果；退出码 **0=成功 1=失败**
3. **统一凭据**：只读根 `.env`，密钥不进命令行参数、不进日志
4. **统一头注释**：定位 / 用法 / 示例 / 输出 / 依赖 五段式——抽成 SKILL.md 正文即可
5. **数据契约 = assets/**：草稿从 `assets/**/drafts/` 读，发布成功自动归档到 `published/`
   并写 `<文件名>.meta.json`（见 [assets/README.md](../assets/README.md)）

## 工具清单与未来 skill 映射

| 工具 | 用途 | 独立运行示例 | 未来 skill |
|------|------|--------------|-----------|
| `wechat_publisher` | 公众号发布（草稿箱） | `python -m publishing.wechat publish --asset assets/articles/公众号/drafts/x.md --json` | publish-wechat |
| `feishu_publisher` | 飞书文档发布（可移入知识库） | `python -m publishing.feishu publish --asset assets/wikis/<库>/drafts/x.md --json` | publish-feishu |
| `douyin_publisher` | 抖音视频发布（Playwright 自动化；`--draft` 存草稿箱，成功不归档） | `python -m publishing.douyin publish --asset assets/videos/douyin/drafts/v.mp4 [--draft] --json` | publish-douyin |
| `novel_publisher` | 小说章节批量发飞书（幂等） | `python -m publishing.novel_publisher --chapters-dir <章节目录>` | novel-publish |
| `asset_store` | 资产库读写/状态流转/建骨架 | `python -m publishing.asset_store ls --json`、`... init` | asset-store |

## 新增一个发布平台

1. 实现 `publishing/publisher_base.BasePublisher`（`publish_markdown` + 建议 `health_check`/`check_config`）
2. 在 `publishing/publisher_base._load_publisher` 登记，`KNOWN_PLATFORMS` 加一项 → `doctor` 自动体检
3. 按契约加 `main()` + `--json`；资产文件夹约定加进 `publishing/asset_store.ASSET_TYPES`
4. 更新 publishing/README 与 ARCHITECTURE
