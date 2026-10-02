"""
公众号配图生成脚本 — 调用豆包 SeeDream 模型生成封面图和正文配图。

子命令:
  cover   <title>            生成文章封面图
  image   <description>      生成单张配图
  batch   <file>             从 Markdown 扫描 [配图：描述] 标记批量生成

用法:
  python scripts/generate_images.py cover "文章标题"
  python scripts/generate_images.py image "系统架构图描述"
  python scripts/generate_images.py batch article.md -o imgs/
"""
import sys
import os
import re
import argparse
import base64
from pathlib import Path

_script_path = Path(__file__).resolve()
for _parent in _script_path.parents:
    if (_parent / "config" / "settings.py").exists():
        PROJECT_DIR = _parent
        break
else:
    PROJECT_DIR = _script_path.parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.tools.generate_image import (
    ImageGenerator,
    get_image_generator,
    generate_cover_image,
    generate_article_image,
    generate_image_from_markdown,
)


def _save_image_data(result: dict, output_dir: Path, prefix: str = "cover") -> str:
    """保存图像数据到文件，返回保存路径"""
    output_dir.mkdir(parents=True, exist_ok=True)

    if result.get("b64_json"):
        data = base64.b64decode(result["b64_json"])
        ext = ".png"
    elif result.get("url"):
        import requests
        resp = requests.get(result["url"], timeout=30)
        data = resp.content
        ext = ".png"
    else:
        return ""

    filepath = output_dir / f"{prefix}{ext}"
    with open(filepath, "wb") as f:
        f.write(data)
    return str(filepath)


def cmd_cover(args):
    """生成封面图"""
    print(f"\n🎨 正在为「{args.title}」生成封面图...\n")
    result = generate_cover_image(args.title, style=args.style)
    print(result)

    if args.output:
        # 从 result 中提取 URL 或 base64
        gen = get_image_generator()
        r = gen.generate(f"封面图: {args.title}", size="2K")
        if r.get("success"):
            path = _save_image_data(r, Path(args.output), "cover")
            if path:
                print(f"\n💾 封面图已保存到: {path}")


def cmd_image(args):
    """生成单张配图"""
    print(f"\n🎨 正在生成配图...\n")
    result = generate_article_image(args.description, image_type=args.type)
    print(result)

    if args.output:
        gen = get_image_generator()
        r = gen.generate(args.description, size="2K")
        if r.get("success"):
            path = _save_image_data(r, Path(args.output), "image_1")
            if path:
                print(f"\n💾 配图已保存到: {path}")


def cmd_batch(args):
    """从 Markdown 批量生成配图"""
    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"\n🎨 正在扫描配图标记...\n")
    result = generate_image_from_markdown(content)
    print(result)

    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 提取 [配图：描述] 并逐一生成
        pattern = r'\[配图[：:]([^\]]+)\]'
        matches = re.findall(pattern, content)
        gen = get_image_generator()
        for i, desc in enumerate(matches, 1):
            r = gen.generate(desc.strip(), size="2K")
            if r.get("success"):
                path = _save_image_data(r, output_dir, f"img_{i:02d}")
                if path:
                    print(f"  💾 配图 {i} 已保存到: {path}")


def main():
    parser = argparse.ArgumentParser(
        description="公众号配图生成工具 — 调用豆包 SeeDream 生成封面图和正文配图"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # cover
    p_cover = sub.add_parser("cover", help="生成文章封面图")
    p_cover.add_argument("title", help="文章标题")
    p_cover.add_argument("-s", "--style", default="modern", choices=["modern", "minimal", "tech", "artistic"],
                         help="封面风格")
    p_cover.add_argument("-o", "--output", help="输出目录")

    # image
    p_img = sub.add_parser("image", help="生成单张配图")
    p_img.add_argument("description", help="配图内容描述")
    p_img.add_argument("-t", "--type", default="diagram",
                       choices=["diagram", "flowchart", "architecture", "concept"],
                       help="配图类型")
    p_img.add_argument("-o", "--output", help="输出目录")

    # batch
    p_batch = sub.add_parser("batch", help="从 Markdown 批量生成配图")
    p_batch.add_argument("file", help="Markdown 文件路径")
    p_batch.add_argument("-o", "--output", help="输出目录（默认 imgs/）")

    args = parser.parse_args()

    try:
        if args.command == "cover":
            cmd_cover(args)
        elif args.command == "image":
            cmd_image(args)
        elif args.command == "batch":
            cmd_batch(args)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
