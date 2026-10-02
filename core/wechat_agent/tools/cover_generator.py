"""
封面图生成工具

提供默认的蓝紫渐变封面图（PIL 渲染），以及图片数据解析。
"""
import base64
import io
import requests
from pathlib import Path


def _load_cn_font(size: int):
    """尝试加载中文字体，fallback 到默认字体"""
    from PIL import ImageFont
    candidates = [
        "msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc",
        "Microsoft YaHei", "SimHei", "SimSun",
        "arial.ttf",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _build_default_cover_bytes(title: str = "AI技术文章") -> bytes:
    """
    生成带标题的默认封面图（蓝紫渐变），返回 JPEG bytes。
    使用 PIL 渲染渐变背景 + 标题文字。
    """
    try:
        from PIL import Image, ImageDraw

        img = Image.new('RGB', (900, 383), color='#1a1a2e')
        draw = ImageDraw.Draw(img)
        for y in range(383):
            r = int(24 + (114 - 24) * y / 383)
            g = int(144 + (46 - 144) * y / 383)
            b = int(255 + (209 - 255) * y / 383)
            draw.line([(0, y), (900, y)], fill=(r, g, b))

        font_title = _load_cn_font(42)
        font_sub = _load_cn_font(22)

        if len(title) > 20:
            title = title[:20] + "…"
        draw.text((450, 160), title, fill="white", anchor="mm", font=font_title)
        draw.text((450, 220), "Powered by AI Agent", fill="rgba(255,255,255,180)", anchor="mm", font=font_sub)

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=90)
        return buf.getvalue()
    except ImportError:
        # PIL 未安装时返回一张极小的占位图（1x1 白像素 JPEG base64）
        return base64.b64decode('/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAACf/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AKp//2Q==')


def _resolve_cover_image_bytes(cover_image, title: str = "AI技术文章") -> bytes:
    """
    将 cover_image（bytes / base64 str / URL str）解析为 JPEG/PNG bytes。
    None 或空字符串时回退到默认封面。
    """
    if cover_image is None or (isinstance(cover_image, str) and not cover_image.strip()):
        return _build_default_cover_bytes(title)
    if isinstance(cover_image, bytes):
        return cover_image
    if isinstance(cover_image, str):
        if cover_image.startswith(("http://", "https://")):
            resp = requests.get(cover_image, timeout=30)
            resp.raise_for_status()
            return resp.content
        b64_str = cover_image
        if "," in b64_str:
            b64_str = b64_str.split(",")[1]
        return base64.b64decode(b64_str.strip())
    return _build_default_cover_bytes(title)