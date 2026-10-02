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
| 短视频 | [../hello_doubao_video/README.md](../hello_doubao_video/README.md) | `docs/分镜提示词大全.md`、`docs/视频合并导出方案.md` |
| 视频→飞书 | [../hello_feishu/README.md](../hello_feishu/README.md) | `CLAUDE.md`、`docs/legacy/CODEBUDDY.md` |
| 小说创作 | [../hello_novel/README.md](../hello_novel/README.md) | 各作品 `novels/*/README.md`、`time_rift/AGENTS.md` |
| 公众号官方 | [../hello_webchat_official/README.md](../hello_webchat_official/README.md) | `.claude/skills/**/SKILL.md` |
| 公众号 Solo | [../hello_webchat_solo/README.md](../hello_webchat_solo/README.md) | `CLAUDE.md`（程序架构） |
| 书评分析 | [../hello_weixin_book/README.md](../hello_weixin_book/README.md) | [INDEX.md](../hello_weixin_book/INDEX.md) |
| 亲情短视频稿 | [../family-life-video/README.md](../family-life-video/README.md) | `<主题>/短视频脚本.md`、`视频分镜脚本.md` |
| 发布工作台 | [../publish_workbench/README.md](../publish_workbench/README.md) | `index.html` 单文件 APP（公众号/抖音/飞书发布跟踪，数据存浏览器 localStorage） |

## 小说作品索引

| 作品 | 目录 | 状态摘要 |
|------|------|----------|
| 沧元图（续写） | [../hello_novel/novels/cangyuantu/README.md](../hello_novel/novels/cangyuantu/README.md) | process + 300 章 `chapters/` |
| 平凡人生 | [../hello_novel/novels/diff_life/README.md](../hello_novel/novels/diff_life/README.md) | 选题→大纲→300 章正文 |
| 普通人的一生 | [../hello_novel/novels/little_man/README.md](../hello_novel/novels/little_man/README.md) | 完整版 + 分章 |
| 时间裂隙：2089 | [../hello_novel/novels/time_rift/README.md](../hello_novel/novels/time_rift/README.md) | 600 章完结，含分镜/视频脚本/审查 |

## 平台能力相关

| 文档 | 位置 |
|------|------|
| 平台架构（Provider 注册表 / 发布契约 / CLI） | [../ARCHITECTURE.md](../ARCHITECTURE.md) |
| 环境自检 | `python media-cli.py doctor --live`（命令实现 `cli/commands/doctor.py`） |
| 平台层单测 | `../tests/`（pytest） |
| 飞书流水线架构细节 | `hello_feishu/CLAUDE.md` |
| Solo 公众号程序架构 | `hello_webchat_solo/CLAUDE.md` |
| 时间裂隙创作系统 | `hello_novel/novels/time_rift/README.md`、`AGENTS.md` |

## 内容产出位置（非过程文档）

| 类型 | 路径 |
|------|------|
| 小说章节正文 | `hello_novel/novels/*/chapters/`（time_rift 为 `novels/time_rift/novel/chapters/`） |
| 小说过程稿（选题/大纲/审核） | `hello_novel/novels/*/process/`、`review/` |
| 书评 HTML | `hello_weixin_book/analyses/` |
| 公众号草稿 | `hello_webchat_official/drafts/` |
| Solo 生成文章 | `hello_webchat_solo/output/`（运行时生成，不入库） |
| 飞书流水线产物 | `hello_feishu/output/`（运行时生成，不入库）、`articles/` |
| 短视频媒体 | `hello_doubao_video/media/`（mp4 原件不入库） |
| 亲情短视频口播/分镜稿 | `family-life-video/<主题>/` |

## 跨仓文档

| 文档 | 位置 |
|------|------|
| 《工作台手册》（三域归属/发布流程/Git 约定） | 工作台 `D:\ai_person\p000_0000_it\it\knowledge-base\pages\00_overview\工作台手册.md` |

## 维护约定

新增或搬迁文档时：

1. 在本索引登记
2. 更新业务线 README 的目录地图
3. 若影响 CLI 示例路径，同步改根 README / ARCHITECTURE / AGENTS.md
