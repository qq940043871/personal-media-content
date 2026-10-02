# 发布工作台（publish_workbench）

## 定位

自媒体发布跟踪工作台：管理内容选题，跟踪**公众号 / 抖音 / 飞书**三平台的发布进度（草稿 → 已排期 → 已发布）。单文件 HTML 类 APP，iPad / 平板 / 手机全屏触控使用，断网可用。

与 `media-cli.py publish` 的关系：CLI 负责**执行**发布（调 API 推送内容），本工作台负责**人工跟踪**每篇内容在各平台的状态、排期与链接，两者互补，数据不打通。

## 目录地图

| 文件 | 说明 |
|------|------|
| `index.html` | 工作台本体（单文件，CSS/JS/SVG 全内联，浏览器直接打开即用） |
| `README.md` | 本文档 |

## 使用方式

浏览器打开 `index.html` 即可；iPad 上可用 Safari「添加到主屏幕」全屏运行。数据存浏览器 localStorage，仅本机可见；换设备前用「设置 → 导出备份（JSON）」。

功能：内容选题库（增删改查 + 搜索筛选）、三平台发布状态跟踪、发布日历（月视图 + 当日安排）、各平台发布检查清单、看板（完成率 / 近 7 天发布 / 平台进度）。

## 文档索引

- 主题与组件规范：`~/.agents/skills/app-workbench-builder/references/design-system.md`
- 若需多人共享 / 多设备同步：可用 lark-apps（妙搭）把单文件发布成链接或升级为数据库应用，见该 skill 的 `references/library-commands.md`

## 状态与已知问题

- v1.0（2026-10-01）：localStorage 版本；示例数据可一键恢复 / 清空。
- 抖音暂无 CLI 发布管道（仓库现有发布管道为 feishu / wechat），抖音状态为纯人工记录。
