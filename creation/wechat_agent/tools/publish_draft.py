"""
直接调用微信公众号 API 发布草稿
不依赖 coze_workload_identity，使用 AppID + AppSecret 获取 access_token
"""
import re
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)
sys.path.insert(0, r"d:\ai_coder\p000_webchat_solo")

from creation.wechat_agent.config.settings import settings
from creation.wechat_agent.tools.html_converter import markdown_to_wechat_html
from creation.wechat_agent.tools.cover_generator import _build_default_cover_bytes
from creation.wechat_agent.tools.wechat_api import (
    get_wechat_access_token,
    upload_thumb_media,
    add_wechat_draft,
)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="发布文章到微信公众号草稿箱")
    parser.add_argument(
        "--md", default=r"d:\ai_coder\p000_webchat_solo\AI_Agent_设计规范.md",
        help="Markdown 文件路径",
    )
    parser.add_argument(
        "--title", default="AI Agent 设计规范：构建生产级智能体的完整工程指南",
        help="文章标题",
    )
    parser.add_argument(
        "--cover", default=None,
        help="封面图文件路径（jpg/png），不传则使用默认封面",
    )
    parser.add_argument("--author", default="AI技术专栏", help="作者名")
    args = parser.parse_args()

    md_file = args.md
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    md_content = re.sub(r'^# .+\n\n?', '', md_content, count=1, flags=re.MULTILINE)
    title = args.title

    print("=" * 60)
    print("📤 微信公众号草稿发布")
    print("=" * 60)

    # Step 1: access_token
    print("\n[1/3] 正在获取 access_token...")
    appid = settings.WECHAT_APPID
    appsecret = settings.WECHAT_APPSECRET
    if not appid or not appsecret:
        print("❌ 微信公众号未配置（WECHAT_APPID / WECHAT_APPSECRET）")
        sys.exit(1)

    try:
        access_token = get_wechat_access_token(appid, appsecret)
        print(f"✅ access_token 获取成功: {access_token[:20]}...")
    except Exception as e:
        print(f"❌ 获取 access_token 失败: {e}")
        sys.exit(1)

    # Step 2: 封面图
    print("\n[2/3] 正在上传封面图...")
    try:
        cover_src = args.cover
        if cover_src and not os.path.isfile(cover_src):
            print(f"⚠️ 封面图文件不存在: {cover_src}，使用默认封面")
            cover_src = None

        if cover_src:
            with open(cover_src, "rb") as f:
                cover_bytes = f.read()
        else:
            cover_bytes = _build_default_cover_bytes(title)

        thumb_media_id = upload_thumb_media(access_token, cover_image=cover_bytes, title=title)
        print(f"✅ 封面图上传成功, thumb_media_id: {thumb_media_id}")
    except Exception as e:
        print(f"❌ 上传封面图失败: {e}")
        sys.exit(1)

    # Step 3: 转换 HTML 并创建草稿
    print("\n[3/3] 正在转换内容格式并创建草稿...")
    content_html = markdown_to_wechat_html(md_content)

    try:
        media_id = add_wechat_draft(access_token, title, content_html, thumb_media_id, author=args.author)
        print(f"✅ 草稿创建成功!")
        print(f"\n{'=' * 60}")
        print(f"🎉 发布结果")
        print(f"{'=' * 60}")
        print(f"📝 标题: {title}")
        print(f"📄 草稿 media_id: {media_id}")
        print(f"💡 请登录微信公众号后台 → 草稿箱 查看和发布")
        print(f"{'=' * 60}")
    except Exception as e:
        print(f"❌ 创建草稿失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()