"""
公众号主题应用脚本 — 列出可用主题或应用主题到文章 HTML。

子命令:
  list                     列出所有可用主题
  apply   <theme> <html>   应用主题到 HTML 文件

用法:
  python scripts/apply_theme.py list
  python scripts/apply_theme.py apply tech-blue article.html -o article-themed.html
"""
import sys
import os
import argparse
import re
from pathlib import Path

_script_path = Path(__file__).resolve()
for _parent in _script_path.parents:
    if (_parent / "config" / "settings.py").exists():
        PROJECT_DIR = _parent
        break
else:
    PROJECT_DIR = _script_path.parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.tools.wechat_themes import (
    get_theme,
    list_themes,
    THEMES,
    LayoutTheme,
)


def _apply_theme_styles(html: str, theme: LayoutTheme) -> str:
    """将主题样式应用到 HTML 内容（替换内联样式中的颜色值）"""
    h = theme.heading
    c = theme.code_block
    t = theme.table
    i = theme.inline

    # 替换 section 外层容器样式
    section_pattern = r'(<section[^>]*style="[^"]*font-size:15px;color:#[^;]+;)'
    html = re.sub(
        section_pattern,
        f'<section style="font-size:15px;color:{theme.section_text_color};'
        f'line-height:1.8;padding:20px 16px;',
        html
    )

    # 替换 H1 样式
    html = re.sub(
        r'(<h1[^>]*style="[^"]*)color:#[a-fA-F0-9]+([^"]*border-bottom:\s*[^;]+;)',
        rf'\1color:{h.h1_color}\2border-bottom:{h.h1_border_bottom};',
        html
    )

    # 替换 H2 样式
    html = re.sub(
        r'(<h2[^>]*style="[^"]*)color:#[a-fA-F0-9]+([^"]*)background:#[^;]+([^"]*)border-left:\s*[^;]+',
        rf'\1color:{h.h2_color}\2background:{h.h2_bg}\3border-left:{h.h2_border_left}',
        html
    )

    # 替换 H3 样式
    html = re.sub(
        r'(<h3[^>]*style="[^"]*)color:#[a-fA-F0-9]+([^"]*)border-left:\s*[^;]+',
        rf'\1color:{h.h3_color}\2border-left:{h.h3_border_left}',
        html
    )

    # 替换 strong 颜色
    html = re.sub(
        r'(<strong[^>]*style="[^"]*)color:#[a-fA-F0-9]+',
        rf'\1color:{i.strong_color}',
        html
    )

    # 替换 code 颜色
    html = re.sub(
        r'(<code[^>]*style="[^"]*)background:#[^;]+;color:#[a-fA-F0-9]+',
        rf'\1background:{i.code_bg};color:{i.code_text}',
        html
    )

    # 替换 a 链接颜色
    html = re.sub(
        r'(<a[^>]*style="[^"]*)color:#[a-fA-F0-9]+',
        rf'\1color:{i.link_color}',
        html
    )

    # 替换段落颜色
    html = re.sub(
        r'(<p[^>]*style="[^"]*margin:10px 0 14px;line-height:2;font-size:15px;)color:#[a-fA-F0-9]+',
        rf'\1color:{theme.paragraph_color}',
        html
    )

    # 替换列表项目颜色
    html = re.sub(
        r'(<li[^>]*style="[^"]*color:#[a-fA-F0-9]+)',
        rf'<li style="color:{theme.list_item_color}',
        html
    )

    return html


def cmd_list(args):
    """列出所有主题"""
    list_themes()


def cmd_apply(args):
    """应用主题"""
    theme = get_theme(args.theme)
    print(f"\n🎨 应用主题: {theme.name} ({theme.description})\n")

    html_file = args.html
    if not os.path.isfile(html_file):
        print(f"❌ HTML 文件不存在: {html_file}")
        sys.exit(1)

    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()

    themed_html = _apply_theme_styles(html, theme)

    output = args.output or html_file
    with open(output, "w", encoding="utf-8") as f:
        f.write(themed_html)

    print(f"✅ 主题已应用，保存到: {output}")


def main():
    parser = argparse.ArgumentParser(
        description="公众号主题应用工具 — 列出主题或应用主题到文章 HTML"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="列出所有可用主题")

    p_apply = sub.add_parser("apply", help="应用主题到 HTML 文件")
    p_apply.add_argument("theme", help="主题标识（tech-blue/minimal-mono/warm-orange/business-navy/fresh-green）")
    p_apply.add_argument("html", help="HTML 文件路径")
    p_apply.add_argument("-o", "--output", help="输出文件路径（默认覆盖原文件）")

    args = parser.parse_args()

    try:
        if args.command == "list":
            cmd_list(args)
        elif args.command == "apply":
            cmd_apply(args)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
