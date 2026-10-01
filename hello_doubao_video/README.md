# hello_doubao_video — 短视频生产线

豆包 AI 生成视频 + FFmpeg 后期，生产可发抖音等平台的动画短视频。

## 目录地图

```
hello_doubao_video/
├── README.md
├── docs/
│   ├── 分镜提示词大全.md      # 各类分镜 AI 提示词
│   └── 视频合并导出方案.md    # 合并与导出方法说明
├── scripts/
│   ├── remove_watermark.py
│   └── 一键合并视频.bat
├── assets/                    # 帧图、去水印图（运行时生成，不入库）
│   ├── image/                 # 原始帧/图
│   └── image_nowm/            # 去水印图
└── media/
    ├── merge_list.txt         # 合并清单（入库）
    └── *.mp4                  # 分段与成片（原件不入库）
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

## 文档

| 文档 | 说明 |
|------|------|
| [docs/分镜提示词大全.md](docs/分镜提示词大全.md) | 提示词库 |
| [docs/视频合并导出方案.md](docs/视频合并导出方案.md) | 合并方案 |

## 已知问题

- `docs/视频合并导出方案.md` 内仍可能残留历史绝对路径（如 `d:/ai_coder/...`），以本 README 与仓库根 CLI 为准。
- 与 `core/video_toolkit.py` / `media-cli.py video` 能力重叠时，优先用统一 CLI。
