"""
公众号文章写稿脚本 — 调用豆包大模型生成大纲/文章/润色/标题优化。

子命令:
  outline   <topic>        生成文章大纲
  article   <title>        根据大纲撰写文章
  polish    <file>         润色文章内容
  optimize-title <titles>  优化标题

用法:
  python scripts/write_article.py outline "LangGraph 多智能体开发实战"
  python scripts/write_article.py article "LangGraph 多智能体开发实战" --outline outline.md
"""
import sys
import os
import argparse
from pathlib import Path

_script_path = Path(__file__).resolve()
for _parent in _script_path.parents:
    if (_parent / "config" / "settings.py").exists():
        PROJECT_DIR = _parent
        break
else:
    PROJECT_DIR = _script_path.parent.parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.tools.doubao_llm import DoubaoLLMClient


def cmd_outline(args):
    """生成大纲"""
    print(f"\n正在为「{args.topic}」生成大纲...\n")
    client = DoubaoLLMClient()
    prompt = f"请为以下主题生成详细的文章大纲：\n\n主题：{args.topic}\n预计总字数：{args.word_count}字"
    system = """你是一位资深的技术内容策划专家。为技术文章生成详细、专业的大纲。
结构清晰，包含引言、核心章节、总结，使用Markdown格式输出。"""
    result = client.generate(prompt, system, temperature=0.7, max_tokens=2000, stream=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\n大纲已保存到: {args.output}")
    else:
        print(result)


def cmd_article(args):
    """撰写文章"""
    outline = ""
    if args.outline:
        with open(args.outline, "r", encoding="utf-8") as f:
            outline = f.read()
        print(f"\n已读取大纲: {args.outline}")
    else:
        print(f"\n正在为「{args.title}」生成大纲...")
        client = DoubaoLLMClient()
        outline = client.generate(
            f"请为以下主题生成详细的文章大纲：\n\n主题：{args.title}\n预计总字数：{args.word_count}字",
            "你是一位资深的技术内容策划专家。为技术文章生成详细、专业的大纲。使用Markdown格式。",
            temperature=0.7, max_tokens=2000, stream=True
        )
        print("\n--- 大纲 ---\n")
        print(outline)

    print(f"\n正在撰写文章...\n")
    client = DoubaoLLMClient()
    system = """你是一位资深的技术写作专家。根据大纲撰写高质量的技术文章。
要求：语言专业易懂，原理讲解清晰，包含代码示例，使用Markdown格式。
标注需要配图的位置（格式：[配图：描述]）。"""
    prompt = f"请根据以下大纲撰写完整的技术文章：\n\n标题：{args.title}\n\n大纲：\n{outline}\n\n目标字数：{args.word_count}字"
    content = client.generate(prompt, system, temperature=0.7, max_tokens=6000, stream=True)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n文章已保存到: {args.output} ({len(content)} 字符)")
    else:
        print("\n--- 文章 ---\n")
        print(content)


def cmd_polish(args):
    """润色文章"""
    with open(args.file, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"\n正在润色文章...\n")
    client = DoubaoLLMClient()
    system = "你是一位资深的技术编辑，优化技术文章的可读性和专业性。保持原意不变。"
    prompt = f"请润色以下技术文章内容：\n\n{content}"
    result = client.generate(prompt, system, temperature=0.5, max_tokens=6000, stream=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"\n润色结果已保存到: {args.output}")
    else:
        print(result)


def cmd_optimize_title(args):
    """优化标题"""
    titles = args.titles
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
        titles = [line.strip() for line in content.split("\n") if line.strip()]
    client = DoubaoLLMClient()
    titles_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(titles)])
    system = "你是一位资深的新媒体运营专家，擅长撰写吸引技术读者的标题。"
    prompt = f"请从以下候选标题中选择或优化出最佳标题：\n\n{titles_text}\n\n请输出最佳标题及理由。"
    result = client.generate(prompt, system, temperature=0.8, max_tokens=1000, stream=True)
    print(result)


def main():
    parser = argparse.ArgumentParser(
        description="公众号文章写稿工具 — 调用豆包大模型生成大纲/文章/润色/标题优化"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_outline = sub.add_parser("outline", help="生成文章大纲")
    p_outline.add_argument("topic", help="文章主题")
    p_outline.add_argument("-w", "--word-count", type=int, default=2000, help="预计字数")
    p_outline.add_argument("-o", "--output", help="输出文件路径")

    p_article = sub.add_parser("article", help="撰写完整文章")
    p_article.add_argument("title", help="文章标题")
    p_article.add_argument("-w", "--word-count", type=int, default=3000, help="目标字数")
    p_article.add_argument("--outline", help="大纲文件路径（不传则自动生成）")
    p_article.add_argument("-o", "--output", help="输出文件路径")

    p_polish = sub.add_parser("polish", help="润色文章")
    p_polish.add_argument("file", help="文章文件路径")
    p_polish.add_argument("-o", "--output", help="输出文件路径")

    p_opt = sub.add_parser("optimize-title", help="优化标题")
    p_opt.add_argument("titles", nargs="*", help="候选标题")
    p_opt.add_argument("-f", "--file", help="从文件读取候选标题（每行一个）")

    args = parser.parse_args()

    try:
        if args.command == "outline":
            cmd_outline(args)
        elif args.command == "article":
            cmd_article(args)
        elif args.command == "polish":
            cmd_polish(args)
        elif args.command == "optimize-title":
            cmd_optimize_title(args)
    except Exception as e:
        print(f"\n错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
