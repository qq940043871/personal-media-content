# 文档总索引

> 全仓文档导航。入口类文档优先；过程稿与技能文档下沉到各业务线。

## 根文档

| 文档 | 用途 |
|------|------|
| [../README.md](../README.md) | 仓库地图、CLI、业务线入口 |
| [../ARCHITECTURE.md](../ARCHITECTURE.md) | 平台架构与 core 模块说明 |
| [../AGENTS.md](../AGENTS.md) | Agent/协作导航与硬性约定 |
| [../.env.example](../.env.example) | 配置模板 |
| [DIRECTORY_STANDARD.md](DIRECTORY_STANDARD.md) | 目录与文档分层规范 |

## 业务线

| 业务线 | 入口 | 关键子文档 |
|--------|------|------------|
| 短视频 | [../assets/douyin/README.md](../assets/douyin/README.md) | `docs/分镜提示词大全.md`、`docs/视频合并导出方案.md` |
| 视频→文章流水线 | `core/video_to_article.py`、`media-cli.py pipeline video-article` | 归档：`docs/_archive/hello_feishu/` |
| 创作资产库 | [../assets/README.md](../assets/README.md) | 各书目 `novels/*/README.md`、`time_rift/AGENTS.md`、douyin 视频线 |
| 公众号 | [../.claude/skills/README.md](../.claude/skills/README.md) + [core/wechat_agent/CLAUDE.md](../core/wechat_agent/CLAUDE.md) | 技能线（SKILL.md）+ 写作智能体 |
| 亲情短视频稿 | `assets/novels/<主题>/` | `<主题>/短视频脚本.md`、`视频分镜脚本.md` |

## 小说作品索引

| 作品 | 目录 | 状态摘要 |
|------|------|----------|
| 沧元图（续写） | [../assets/novels/cangyuantu/README.md](../assets/novels/cangyuantu/README.md) | process + 300 章 `chapters/` |
| 平凡人生 | [../assets/novels/diff_life/README.md](../assets/novels/diff_life/README.md) | 选题→大纲→300 章正文 |
| 普通人的一生 | [../assets/novels/little_man/README.md](../assets/novels/little_man/README.md) | 完整版 + 分章 |
| 时间裂隙：2089 | [../assets/novels/time_rift/README.md](../assets/novels/time_rift/README.md) | 600 章完结，含分镜/视频脚本/审查 |

## 平台能力相关

| 文档 | 位置 |
|------|------|
| 平台架构（Provider 注册表 / 发布契约 / CLI） | [../ARCHITECTURE.md](../ARCHITECTURE.md) |
| 环境自检 | `python media-cli.py doctor --live`（命令实现 `cli/commands/doctor.py`） |
| 平台层单测 | `../tests/`（pytest） |
| 飞书流水线架构细节 | `docs/_archive/hello_feishu/CLAUDE.md`（历史）；现行见 `core/video_to_article.py` 头注释 |
| 公众号写作智能体架构 | `core/wechat_agent/CLAUDE.md` |
| 时间裂隙创作系统 | `assets/novels/time_rift/README.md`、`AGENTS.md` |

## 内容产出位置（非过程文档）

| 类型 | 路径 |
|------|------|
| 小说章节正文 | `assets/novels/*/chapters/`（time_rift 为 `novels/time_rift/novel/chapters/`） |
| 小说过程稿（选题/大纲/审核） | `assets/novels/*/process/`、`review/` |
| 书评 HTML | 已迁出至 personal-read-book 仓库 |
| 公众号草稿 | `assets/wechat/drafts/<篇名>/` |
| 写作智能体生成文章 | `storage/articles/solo_output/`（运行时生成，不入库） |
| 流水线产物 | `storage/videos_output/`、`storage/articles/`（运行时生成，不入库） |
| 短视频媒体 | `assets/douyin/media/`（mp4 原件不入库） |
| 亲情短视频口播/分镜稿 | `assets/novels/<主题>/` |

## 跨仓文档

| 文档 | 位置 |
|------|------|
| 《工作台手册》（三域归属/发布流程/Git 约定） | 工作台 `D:\ai_person\p000_0000_it\it\knowledge-base\pages\00_overview\工作台手册.md` |

## 维护约定

新增或搬迁文档时：

1. 在本索引登记
2. 更新业务线 README 的目录地图
3. 若影响 CLI 示例路径，同步改根 README / ARCHITECTURE / AGENTS.md
