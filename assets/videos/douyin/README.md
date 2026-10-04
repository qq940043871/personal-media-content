# assets/videos/douyin — 短视频生产线（原 hello_doubao_video，2026-10 迁入）

豆包 AI 生成视频 + FFmpeg 后期，生产可发抖音等平台的动画短视频。

## 目录地图

```
assets/videos/douyin/
├── README.md
├── docs/
│   ├── 分镜提示词大全.md      # 各类分镜 AI 提示词
│   └── 视频合并导出方案.md    # 合并与导出方法说明
├── scripts/
│   ├── remove_watermark.py
│   ├── synth_bgm.py           # 本地合成 BGM（numpy，无版权）
│   └── 一键合并视频.bat
├── source/                    # HTML 动画源稿（1080x1920，契约同 kepu/README.md）
├── assets/                    # 帧图、去水印图、预览图（运行时生成，不入库）
│   ├── image/                 # 原始帧/图
│   └── image_nowm/            # 去水印图
└── media/
    ├── merge_list.txt         # 合并清单（入库）
    └── *.mp4 / *.wav          # 分段、成片与 BGM（原件不入库）
```

## 常用流程

1. 用分镜提示词在豆包等平台生成片段  
2. 片段放入 `media/`，在 `media/merge_list.txt` 维护合并顺序  
3. 合并（平台 CLI 或本地脚本）：

```bash
# 推荐：仓库根统一入口
python media-cli.py video merge media/doubao_video_1.mp4 media/doubao_video_2.mp4 \
    -o media/full.mp4 --fade

# 本地 bat / 脚本见 scripts/
```

4. 需要去水印或处理帧图时使用 `scripts/` 与 `assets/`

## HTML 动画线（无需 AI 文生视频，本地直出成片）

叙事/图文类短片可直接写 HTML 时间线动画（版式契约见 `../kepu/README.md`），
配乐用 `scripts/synth_bgm.py` 本地合成：

```bash
python scripts/synth_bgm.py --out media/bgm_xxx.wav --seconds 66
python media-cli.py video html2video source/xxx.html \
    -o drafts/xxx.mp4 --music media/bgm_xxx.wav
```

## 发布（含草稿箱）

```bash
python media-cli.py douyin publish --video-file drafts/xxx.mp4 \
    --title "标题" --tags 生活 --draft    # 存入抖音草稿箱（App 内检查后手动发）
python -m publishing.douyin publish --asset drafts/xxx.mp4 --json   # 直接发布，成功自动归档
```

`--draft` 存草稿箱：点击创作者后台的「存草稿/暂存离开」按钮（2026-10 实测按钮
文案为「暂存离开」），作品不进资产归档（drafts/≠published），适合先在 App 内
挑选封面/音乐/位置再手动发布的场景。注意：PC 端内容管理页没有草稿列表入口
（审核状态筛选仅 全部/已发布/审核中/未通过），草稿箱在抖音 App 内查看。

## 文档

| 文档 | 说明 |
|------|------|
| [docs/分镜提示词大全.md](docs/分镜提示词大全.md) | 提示词库 |
| [docs/视频合并导出方案.md](docs/视频合并导出方案.md) | 合并方案 |

## 已知问题

- `docs/视频合并导出方案.md` 内仍可能残留历史绝对路径（如 `d:/ai_coder/...`），以本 README 与仓库根 CLI 为准。
- 与 `core/video_toolkit.py` / `media-cli.py video` 能力重叠时，优先用统一 CLI。
