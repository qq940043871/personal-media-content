"""
微信公众号文章发布智能体 — 主模块

基于 LangGraph 实现 7 节点线性管线：
  生成大纲 → 撰写正文 → 审稿 → 转 HTML → 封面图 → 配图 → 发布

用法：
    python -m src.agents.agent "文章标题"
    python -m src.agents.agent "文章标题" --type "原理分析" --length 5000
"""
import asyncio
import argparse
import sys
from pathlib import Path

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# 子模块
from creation.wechat_agent.agents.state import ArticleState
from creation.wechat_agent.agents.config import load_article_config
from creation.wechat_agent.agents.nodes import (
    generate_outline_node,
    write_article_node,
    review_article_node,
    convert_to_html_node,
    generate_cover_node,
    generate_article_images_node,
    publish_draft_node,
    should_continue,
)


# ==================== 构建工作流 ====================

def build_article_agent():
    """
    构建文章发布 Agent 工作流（LangGraph StateGraph）
    7 节点线性管线，参考 skills 系统：
      选题 → 写稿 → 审稿 → 排版 → 配图 → 发布
    """
    workflow = StateGraph(ArticleState)

    workflow.add_node("generate_outline", generate_outline_node)
    workflow.add_node("write_article", write_article_node)
    workflow.add_node("review_article", review_article_node)
    workflow.add_node("convert_html", convert_to_html_node)
    workflow.add_node("generate_cover", generate_cover_node)
    workflow.add_node("generate_article_images", generate_article_images_node)
    workflow.add_node("publish_draft", publish_draft_node)

    workflow.set_entry_point("generate_outline")

    workflow.add_edge("generate_outline", "write_article")
    workflow.add_edge("write_article", "review_article")
    workflow.add_edge("review_article", "convert_html")
    workflow.add_edge("convert_html", "generate_cover")
    workflow.add_edge("generate_cover", "generate_article_images")
    workflow.add_edge("generate_article_images", "publish_draft")
    workflow.add_edge("publish_draft", END)

    return workflow.compile()


# ==================== 主 Agent 类 ====================

class WeChatArticleAgent:
    """
    微信公众号文章发布智能体

    使用示例:
        agent = WeChatArticleAgent()
        result = await agent.run(title="LangGraph 多智能体开发实战")
    """

    def __init__(self):
        self.graph = build_article_agent()
        self.config = load_article_config()

    async def run(
        self,
        title: str,
        article_type: str = "技术教程",
        target_length: int = 3000,
        include_code: bool = True,
        include_images: bool = True,
    ) -> ArticleState:
        """
        运行 Agent 管线

        Args:
            title: 文章标题
            article_type: 文章类型（技术教程/原理分析/实战案例/架构设计）
            target_length: 目标字数
            include_code: 是否包含代码示例
            include_images: 是否插入配图

        Returns:
            最终状态（ArticleState）
        """
        config = self.config

        initial_state: ArticleState = {
            "title": title,
            "article_type": article_type,
            "target_length": target_length,
            "include_code": include_code,
            "include_images": include_images,
            "config": config,
            "target_reader": config.get("target_reader", ""),
            "tone": config.get("tone", ""),
            "writing_style": config.get("writing_style", ""),
            "forbidden_words": config.get("forbidden_words", []),
            "article_dir": "",
            "outline": "",
            "content_markdown": "",
            "content_html": "",
            "cover_image": "",
            "article_images": [],
            "review_result": {},
            "media_id": "",
            "status": "初始化",
            "error": "",
            "messages": [],
        }

        print(f"\n{'='*60}")
        print(f"[BOT] 开始处理文章: {title}")
        print(f"[CONFIG] 目标读者: {config.get('target_reader', '未配置')}")
        print(f"[IMAGE] 调性: {config.get('tone', '未配置')}")
        print(f"{'='*60}\n")

        final_state = await self.graph.ainvoke(initial_state)

        print(f"\n{'='*60}")
        if final_state.get("error"):
            print(f"[ERR] 处理失败: {final_state['error']}")
        else:
            print(f"[OK] 处理完成!")
            print(f"[DOC] 草稿ID: {final_state.get('media_id', 'N/A')}")
            if final_state.get("article_dir"):
                print(f"[DIR] 文章已保存到: {final_state['article_dir']}")
        print(f"{'='*60}\n")

        return final_state

    async def run_simple(self, title: str) -> str:
        """
        简化接口：只需标题，返回发布结果信息

        Args:
            title: 文章标题

        Returns:
            发布结果信息
        """
        result = await self.run(title=title)

        if result.get("error"):
            return f"[ERR] 发布失败: {result['error']}"

        review = result.get("review_result", {})
        review_summary = ""
        if review:
            issues_count = review.get("total_issues", 0)
            if issues_count > 0:
                review_summary = f"[WARN] 审稿: {issues_count} 个建议（已自动处理）"
            else:
                review_summary = "[OK] 审稿: 通过"

        return f"""[OK] 文章发布成功！

[NOTE] 标题: {result['title']}
[DOC] 草稿ID: {result.get('media_id', 'N/A')}
[STAT] 字数: {len(result.get('content_markdown', ''))}
{review_summary}
[IMAGE] 主题: {self.config.get('default_format_preset', ['default'])[0]}
👤 目标读者: {result.get('target_reader', '未配置')}

请登录微信公众号后台查看和发布。"""


# 导出
__all__ = [
    "ArticleState",
    "WeChatArticleAgent",
    "build_article_agent",
]


# ==================== 命令行接口 ====================

def main():
    """
    命令行入口：直接生成文章并发布到微信公众号草稿箱

    使用示例:
        python -m src.agents.agent "LangGraph 多智能体开发实战"
    """
    parser = argparse.ArgumentParser(
        description="[BOT] 微信公众号文章发布智能体 - 直接生成文章并发布到草稿箱",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""使用示例:
  python -m src.agents.agent "LangGraph 多智能体开发实战"
  python -m src.agents.agent "Transformer 注意力机制" --type "原理分析" --length 5000 --no-code
        """,
    )

    parser.add_argument("title", help="文章标题（必填）")
    parser.add_argument("--type", "-t", default="技术教程",
                        choices=["技术教程", "原理分析", "实战案例", "架构设计"],
                        help="文章类型（默认：技术教程）")
    parser.add_argument("--length", "-l", type=int, default=3000, help="目标字数（默认：3000）")
    parser.add_argument("--no-code", action="store_true", help="不包含代码示例（默认包含）")
    parser.add_argument("--no-images", action="store_true", help="不生成 AI 配图（默认生成）")
    parser.add_argument("--save", "-s", metavar="FILE", help="保存 Markdown 内容到指定文件")

    args = parser.parse_args()

    agent = WeChatArticleAgent()

    async def run_agent():
        result = await agent.run(
            title=args.title,
            article_type=args.type,
            target_length=args.length,
            include_code=not args.no_code,
            include_images=not args.no_images,
        )

        if args.save and result.get("content_markdown"):
            try:
                with open(args.save, "w", encoding="utf-8") as f:
                    f.write(result["content_markdown"])
                print(f"[NOTE] 文章已保存到: {args.save}")
            except Exception as e:
                print(f"[WARN] 保存文件失败: {e}")

        return result

    final_state = asyncio.run(run_agent())

    return 1 if final_state.get("error") else 0


if __name__ == "__main__":
    sys.exit(main())