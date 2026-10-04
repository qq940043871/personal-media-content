"""
HTML → 视频渲染器 — 知识科普视频方案（读平面无关，创作/发布共用的能力底座）

把带时间线动画的 HTML 页面逐帧渲染成 mp4：Playwright 无头 Chromium 逐帧
截图，ffmpeg 合成 H.264。相比录屏，帧步进输出帧率精确、画面确定性可复现。

HTML 契约（页面需遵守）：
- 总时长：<meta name="video-duration" content="15">（秒；render(duration=) 可覆盖）
- 时间线：优先 CSS animations——渲染器对 document.getAnimations() 逐帧
  pause + 设置绝对 currentTime（页面按绝对秒编排 keyframe/delay 即可）；
  pause 不可省：仅设 currentTime 时合成器层可能不跟随主线程 seek，
  截图会拿到陈旧画面（表现为部分 fill-forwards 元素随机缺失）；
  JS 时间线可监听 window 事件 'htmlvideo:seek'（detail.t，单位秒）自行摆姿
- 版式按视口设计（默认 1080x1920 竖屏），不滚动、不依赖真实时钟

用法：
    from core.html_video import HtmlVideoRenderer
    HtmlVideoRenderer().render('video.html', 'out.mp4', fps=30)   # → {'success': ...}

CLI：
    python media-cli.py video html2video video.html -o out.mp4 [--music bg.mp3]
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from .config import config


class HtmlVideoError(RuntimeError):
    """HTML 渲染或合成失败"""


class HtmlVideoRenderer:
    """HTML 动画页面 → mp4 渲染器（Playwright 帧步进 + ffmpeg 合成）"""

    SEEK_JS = """(t) => {
        for (const a of document.getAnimations()) {
            a.pause();
            a.currentTime = t * 1000;
        }
        window.dispatchEvent(new CustomEvent('htmlvideo:seek', {detail: {t}}));
        return document.getAnimations().length;
    }"""

    def __init__(self, ffmpeg_path=None):
        self.ffmpeg = ffmpeg_path or config.FFMPEG_PATH

    def render(self, html_path, output, fps=30, duration=None,
               width=1080, height=1920, music=None, crf=18):
        """
        渲染一个 HTML 文件为 mp4。

        Args:
            html_path: HTML 源文件（本地文件，相对/绝对均可）
            output: 输出 mp4 路径（父目录自动创建）
            fps: 帧率（默认 30）
            duration: 总秒数（默认读页面 <meta name="video-duration">，都没有则 10s）
            width/height: 视口尺寸（默认 1080x1920 竖屏）
            music: 背景音乐文件（可选；比视频长则 -shortest 截断）
            crf: 画质（x264 CRF，越小越清晰，默认 18）

        Returns:
            {'success', 'output', 'duration', 'fps', 'frames'}
        """
        html_path = Path(html_path)
        if not html_path.exists():
            raise HtmlVideoError(f'HTML 文件不存在: {html_path}')
        if music and not Path(music).exists():
            raise HtmlVideoError(f'背景音乐不存在: {music}')
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)

        frames_dir = Path(tempfile.mkdtemp(prefix='htmlvideo_'))
        try:
            duration = self._render_frames(html_path, frames_dir, fps, duration, width, height)
            self._encode(frames_dir, output, fps, duration, music, crf)
            return {'success': True, 'output': str(output),
                    'duration': duration, 'fps': fps, 'frames': round(duration * fps)}
        finally:
            shutil.rmtree(frames_dir, ignore_errors=True)

    # ===== 内部 =====

    def _render_frames(self, html_path, frames_dir, fps, duration, width, height):
        """逐帧 seek + 截图；返回实际使用的总秒数"""
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': width, 'height': height},
                                    device_scale_factor=1)
            page.goto(html_path.resolve().as_uri())
            page.wait_for_load_state('networkidle')  # 等本地图片/字体就绪

            if not duration:
                meta = page.evaluate(
                    "document.querySelector('meta[name=video-duration]')?.content || ''")
                duration = float(meta) if meta else 10.0
            total = round(duration * fps)

            for i in range(total):
                t = i / fps
                page.evaluate(self.SEEK_JS, t)
                page.screenshot(path=str(frames_dir / f'f{i:06d}.jpg'),
                                type='jpeg', quality=92)
            browser.close()
        return float(duration)

    def _encode(self, frames_dir, output, fps, duration, music, crf):
        """帧序列 → H.264 mp4（可选混音乐）"""
        cmd = [self.ffmpeg, '-y', '-v', 'error',
               '-framerate', str(fps), '-i', str(frames_dir / 'f%06d.jpg')]
        if music:
            cmd += ['-i', str(music), '-c:a', 'aac', '-b:a', '128k', '-shortest']
        cmd += ['-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', str(crf),
                '-r', str(fps), '-movflags', '+faststart', str(output)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise HtmlVideoError(f'ffmpeg 合成失败: {proc.stderr[-500:]}')
