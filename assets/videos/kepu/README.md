# kepu — 知识科普视频工程（HTML → 视频）

「每期 15 秒讲清一个日常现象」的科普短视频线。**源稿是 HTML**：版式与动画全部
写成 CSS 时间线，渲染器逐帧截图后 ffmpeg 合成 H.264——帧率精确、画面可复现、
文字/图表锐利（相对 AI 文生视频 `douyin/scripts/agnes_video.py` 而言的优势）。

## 目录

```
kepu/
  source/   # 每期源稿：<题目>.html（自包含，无外部资源）
  drafts/   # 成片草稿（html2video 输出，待发布）
  published/# 已发布归档（发布工具自动移入 + .meta.json）
```

## 一期的创作流程

1. **写源稿**：复制 `source/` 里已有某期的 HTML 改内容（或从零写），
   遵守下面的契约；版式按 1080x1920 竖屏设计。
2. **渲染成片**：

   ```bash
   python media-cli.py video html2video source/为什么天空是蓝色的.html \
       -o drafts/为什么天空是蓝色的.mp4            # 时长/帧率/尺寸可覆盖
   ```

   （能力实现在 `core/html_video.py`：Playwright 无头 Chromium + ffmpeg）
3. **预览**：HTML 直接双击浏览器里看（页面按绝对时间线播放），
   或抽帧检查：`ffprobe` / `python media-cli.py video info drafts/x.mp4`
4. **发布**：`python media-cli.py asset publish --file drafts/x.mp4`
   （默认发抖音；成功自动归档到 published/）

## HTML 契约（渲染器与页面的约定）

- `<meta name="video-duration" content="15">` —— 总秒数（CLI `--duration` 可覆盖）
- 时间线用 **CSS animations** 编排：渲染器对 `document.getAnimations()` 逐帧设置
  绝对 `currentTime`，因此 keyframe/`animation-delay` 都按绝对秒写
  （场景出入场建议用「15s 主时间线 + 百分比 keyframe」的写法，见源稿）
- JS 时间线可监听 `window` 事件 `htmlvideo:seek`（`detail.t`，秒）自行摆姿
- 不滚动、不依赖真实时钟/网络（字体用系统字体，资源内联）
