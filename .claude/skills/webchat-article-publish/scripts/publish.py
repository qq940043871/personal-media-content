"""
公众号发布脚本 — 将文章发布到微信公众号草稿箱。

子命令:
  draft     <md_file>        发布到草稿箱
  check                     检查微信配置
  info                      显示发布信息

用法:
  python scripts/publish.py draft article.md --title "文章标题" --author "作者"
  python scripts/publish.py check
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

from config import get_settings


def cmd_draft(args):
    """发布到微信草稿箱"""
    settings = get_settings()

    if not settings.WECHAT_APPID or not settings.WECHAT_APPSECRET:
        print("❌ 微信公众号未配置（WECHAT_APPID / WECHAT_APPSECRET）")
        print("💡 请在 config/.env 中配置微信凭证")
        sys.exit(1)

    # 读取 Markdown
    md_file = args.md
    if not os.path.isfile(md_file):
        # 尝试在 assets/articles/公众号/drafts/ 下找
        candidate = (PROJECT_DIR / "assets" / "articles" / "公众号"
                     / "drafts" / md_file / "article.md")
        if candidate.exists():
            md_file = str(candidate)
        else:
            print(f"❌ 文件不存在: {md_file}")
            sys.exit(1)

    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    # 导入发布函数
    sys.path.insert(0, str(PROJECT_DIR))
    from main import publish_to_wechat

    title = args.title or os.path.basename(os.path.dirname(md_file))
    author = args.author or "AI技术专栏"

    try:
        media_id = publish_to_wechat(
            title=title,
            content_markdown=md_content,
            author=author,
        )
        print(f"\n{'=' * 60}")
        print(f"✅ 发布成功！")
        print(f"📝 标题: {title}")
        print(f"📄 草稿 media_id: {media_id}")
        print(f"{'=' * 60}")
    except Exception as e:
        print(f"\n❌ 发布失败: {e}")
        sys.exit(1)


def cmd_check(args):
    """检查微信配置"""
    settings = get_settings()
    appid = settings.WECHAT_APPID
    appsecret = settings.WECHAT_APPSECRET

    print("\n=== 微信配置检查 ===\n")
    print(f"  WECHAT_APPID:     {'✅ 已配置' if appid else '❌ 未配置'}")
    print(f"  WECHAT_APPSECRET: {'✅ 已配置' if appsecret else '❌ 未配置'}")

    if appid and appsecret:
        try:
            from main import get_access_token
            token = get_access_token(appid, appsecret)
            print(f"  access_token:    ✅ 获取成功 ({token[:20]}...)")
            print("\n✅ 微信配置正常，可以发布")
        except Exception as e:
            print(f"\n❌ access_token 获取失败: {e}")
            sys.exit(1)
    else:
        sys.exit(1)


def cmd_info(args):
    """显示发布信息"""
    print("\n=== 发布信息 ===\n")
    print("  发布模式: draft（草稿箱）")
    print("  平台: 微信公众号")
    print("  API: api.weixin.qq.com")
    print("\n  流程:")
    print("    1. 读取 Markdown 文件")
    print("    2. 转换为微信兼容 HTML")
    print("    3. 上传封面图到素材库")
    print("    4. 创建草稿到微信草稿箱")
    print("\n  先决条件:")
    print("    - config/.env 中配置 WECHAT_APPID")
    print("    - config/.env 中配置 WECHAT_APPSECRET")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="公众号发布工具 — 将文章发布到微信公众号草稿箱"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_draft = sub.add_parser("draft", help="发布到草稿箱")
    p_draft.add_argument("md", help="Markdown 文件路径或 assets/articles/公众号/drafts/ 下的目录名")
    p_draft.add_argument("--title", help="文章标题（默认从目录名推断）")
    p_draft.add_argument("--author", default="AI技术专栏", help="作者名")

    sub.add_parser("check", help="检查微信配置")
    sub.add_parser("info", help="显示发布信息")

    args = parser.parse_args()

    try:
        if args.command == "draft":
            cmd_draft(args)
        elif args.command == "check":
            cmd_check(args)
        elif args.command == "info":
            cmd_info(args)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
