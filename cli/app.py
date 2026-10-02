"""
cli.app — media-cli 的解析器组装与入口

命令实现在 cli/commands/ 各域模块；本文件只做 argparse 组装与分发。
"""

import argparse
import sys

from .commands import register_all


def build_parser():
    parser = argparse.ArgumentParser(
        prog='media-cli',
        description='AI 自媒体内容生产中台 — 统一命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s status                              查看整体状态
  %(prog)s doctor                              环境自检（配置/依赖）
  %(prog)s doctor --live                       环境自检 + LLM/发布平台探活
  %(prog)s video info video.mp4                获取视频信息
  %(prog)s video merge v1.mp4 v2.mp4 -o out.mp4  合并视频
  %(prog)s video extract frames video.mp4 out/   提取关键帧
  %(prog)s video extract audio video.mp4 out/    提取音频
  %(prog)s asr transcribe audio.mp3              语音转写
  %(prog)s asr transcribe audio.mp3 --local --srt  本地转写+字幕
  %(prog)s llm chat "写一首诗"                    调用大模型
  %(prog)s llm chat --stream "写个故事"           流式输出
  %(prog)s feishu publish --title "标题" --content-file doc.md  发布飞书
  %(prog)s wechat publish --title "标题" --content-file doc.md   公众号草稿
  %(prog)s wechat publish --title "标题" --content-file doc.md --cover cover.jpg --publish-now  一键发布
  %(prog)s wechat drafts list                              草稿列表
  %(prog)s wechat upload-image cover.jpg --permanent        上传封面图
  %(prog)s storage stats                         存储统计
  %(prog)s storage list videos                   列出视频
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    register_all(subparsers)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)
