#!/usr/bin/env python3
"""
微信公众号智能体 - 主入口
支持交互式模式和命令行模式
"""
import sys
import asyncio
import argparse
import re
from typing import Optional

sys.path.insert(0, '.')

from core.wechat_agent.agents import create_agent
from core.wechat_agent.tools.html_converter import markdown_to_wechat_html
from core.wechat_agent.tools.cover_generator import _build_default_cover_bytes
from core.wechat_agent.tools.wechat_api import (
    get_wechat_access_token,
    upload_thumb_media,
    add_wechat_draft,
)
from core.wechat_agent.config import get_settings


def publish_to_wechat(title: str, content_markdown: str, author: str = None):
    """
    将文章发布到微信公众号草稿箱。

    Args:
        title: 文章标题
        content_markdown: Markdown 格式的文章内容
        author: 作者

    Returns:
        media_id: 草稿的 media_id
    """
    settings = get_settings()
    appid = settings.WECHAT_APPID
    appsecret = settings.WECHAT_APPSECRET

    if not appid or not appsecret:
        raise Exception("微信公众号未配置（WECHAT_APPID / WECHAT_APPSECRET）")

    print("\n📤 正在发布到微信公众号...")

    # Step 1: 获取 access_token
    print("  [1/4] 获取 access_token...")
    access_token = get_wechat_access_token(appid, appsecret)
    print(f"  ✅ access_token 获取成功")

    # Step 2: 去掉正文中的第一个 # 标题
    md_content = re.sub(r'^# .+\n\n?', '', content_markdown, count=1, flags=re.MULTILINE)

    # Step 3: 转换 HTML
    print("  [2/4] 转换 HTML 格式...")
    content_html = markdown_to_wechat_html(md_content)

    # Step 4: 上传封面图
    print("  [3/4] 上传封面图...")
    cover_bytes = _build_default_cover_bytes(title)
    thumb_media_id = upload_thumb_media(access_token, cover_bytes, title)
    print(f"  ✅ 封面图上传成功")

    # Step 5: 创建草稿
    print("  [4/4] 创建草稿...")
    media_id = add_wechat_draft(
        access_token, title, content_html, thumb_media_id,
        author=author, digest=title[:120], need_open_comment=1,
    )
    print(f"  ✅ 草稿创建成功")

    return media_id


def print_banner():
    """打印欢迎信息"""
    banner = """
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     🤖 微信公众号智能体 - AI技术文章写作助手              ║
║                                                          ║
║     支持：大纲生成 → 文章撰写 → 配图生成 → 微信发布      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """
    print(banner)


def interactive_mode():
    """交互式模式"""
    print_banner()
    print("💡 提示：输入主题即可生成文章，输入 'quit' 退出\n")

    agent = create_agent()

    while True:
        try:
            topic = input("\n📝 请输入文章主题: ").strip()

            if not topic:
                print("⚠️  主题不能为空，请重新输入")
                continue

            if topic.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见！")
                break

            result = asyncio.run(agent.run(title=topic))

            if result.get("error"):
                print(f"\n❌ 生成失败: {result['error']}")
                continue

            print("\n" + "=" * 60)
            print("📄 生成结果")
            print("=" * 60)
            print(f"\n标题: {result.get('title')}")
            print(f"\n大纲预览:\n{result.get('outline', '')[:500]}...")
            print(f"\n文章长度: {len(result.get('content_markdown', ''))} 字符")

            publish_choice = input("\n🚀 是否发布到微信公众号草稿箱? (y/n): ").strip().lower()
            if publish_choice == 'y':
                try:
                    media_id = publish_to_wechat(
                        title=result.get('title', topic),
                        content_markdown=result.get('content_markdown', ''),
                    )
                    print(f"\n✅ 发布成功！草稿 media_id: {media_id}")
                except Exception as e:
                    print(f"\n❌ 发布失败: {e}")

            save_choice = input("\n💾 是否保存文章到本地文件? (y/n): ").strip().lower()
            if save_choice == 'y':
                filename = input("请输入文件名（默认: article.md）: ").strip() or "article.md"
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(result.get('content_markdown', ''))
                    print(f"✅ 文章已保存到: {filename}")
                except Exception as e:
                    print(f"❌ 保存失败: {str(e)}")

        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 发生错误: {str(e)}")


def command_line_mode(topic: str, auto_publish: bool = False, output: Optional[str] = None):
    """
    命令行模式

    Args:
        topic: 文章主题
        auto_publish: 是否自动发布
        output: 输出文件路径
    """
    print_banner()
    print(f"📝 主题: {topic}\n")

    agent = create_agent()

    result = asyncio.run(agent.run(title=topic))

    if result.get("error"):
        print(f"\n❌ 生成失败: {result['error']}")
        sys.exit(1)

    print(f"\n✅ 文章生成完成，长度: {len(result.get('content_markdown', ''))} 字符")

    if output:
        try:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(result.get('content_markdown', ''))
            print(f"✅ 文章已保存到: {output}")
        except Exception as e:
            print(f"\n❌ 保存失败: {str(e)}")

    if auto_publish:
        try:
            media_id = publish_to_wechat(
                title=result.get('title', topic),
                content_markdown=result.get('content_markdown', ''),
            )
            print(f"\n✅ 发布成功！草稿 media_id: {media_id}")
        except Exception as e:
            print(f"\n❌ 发布失败: {e}")

    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='微信公众号智能体 - AI技术文章写作助手',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""使用示例:
  # 交互式模式
  python main.py

  # 命令行模式 - 仅生成文章
  python main.py "LangGraph多智能体开发实战"

  # 命令行模式 - 生成并保存到文件
  python main.py "Transformer注意力机制" -o article.md

  # 命令行模式 - 生成并发布到微信草稿箱
  python main.py "RAG系统架构设计" -p
        """,
    )

    parser.add_argument('topic', nargs='?', help='文章主题（不指定则进入交互式模式）')
    parser.add_argument('-o', '--output', help='输出文件路径（如 article.md）')
    parser.add_argument('-p', '--publish', action='store_true', help='生成后自动发布到微信公众号草稿箱')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')

    args = parser.parse_args()

    # 检查配置
    try:
        settings = get_settings()
        if not settings.ARK_API_KEY or settings.ARK_API_KEY == 'your_ark_api_key_here':
            print("❌ 错误: 请先配置 ARK_API_KEY")
            print("请复制 config/.env.example 为 config/.env 并填写您的API密钥")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 配置加载失败: {str(e)}")
        sys.exit(1)

    if args.topic:
        command_line_mode(topic=args.topic, auto_publish=args.publish, output=args.output)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()