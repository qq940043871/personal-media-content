"""
LangGraph 智能体运行脚本 — 启动文章生成工作流。

子命令:
  run     <title>    运行完整工作流（大纲→写稿→HTML→封面→配图→发布）
  simple  <title>    简化接口（只需标题）

用法:
  python scripts/run_agent.py run "LangGraph 多智能体开发实战" --publish
  python scripts/run_agent.py run "Transformer 注意力机制" --type "原理分析" --length 5000
  python scripts/run_agent.py simple "RAG 系统架构设计"
"""
import sys
import os
import asyncio
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

from src.agents import WeChatArticleAgent


def cmd_run(args):
    """运行完整工作流"""
    agent = WeChatArticleAgent()

    async def _run():
        result = await agent.run(
            title=args.title,
            article_type=args.type,
            target_length=args.length,
            include_code=not args.no_code,
            include_images=args.images,
        )

        if args.save and result.get("content_markdown"):
            with open(args.save, "w", encoding="utf-8") as f:
                f.write(result["content_markdown"])
            print(f"📝 文章已保存到: {args.save}")

        return result

    final_state = asyncio.run(_run())
    return 1 if final_state.get("error") else 0


def cmd_simple(args):
    """简化接口"""
    agent = WeChatArticleAgent()

    async def _run():
        result = await agent.run_simple(title=args.title)
        print(result)
        return result

    asyncio.run(_run())


def main():
    parser = argparse.ArgumentParser(
        description="LangGraph 智能体运行工具 — 启动文章生成工作流"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = sub.add_parser("run", help="运行完整工作流")
    p_run.add_argument("title", help="文章标题")
    p_run.add_argument("--type", "-t", default="技术教程",
                       choices=["技术教程", "原理分析", "实战案例", "架构设计"],
                       help="文章类型")
    p_run.add_argument("--length", "-l", type=int, default=3000, help="目标字数")
    p_run.add_argument("--no-code", action="store_true", help="不包含代码示例")
    p_run.add_argument("--images", action="store_true", help="插入配图")
    p_run.add_argument("--save", "-s", metavar="FILE", help="保存 Markdown 到文件")
    p_run.add_argument("--publish", "-p", action="store_true", help="自动发布到微信")

    # simple
    p_simple = sub.add_parser("simple", help="简化接口")
    p_simple.add_argument("title", help="文章标题")

    args = parser.parse_args()

    try:
        sys.exit(cmd_run(args) if args.command == "run" else cmd_simple(args) or 0)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
