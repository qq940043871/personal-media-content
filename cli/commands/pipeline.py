"""pipeline 命令域 — 内容生产流水线（教学视频→文章）"""

import sys


def cmd_pipeline_video_article(args):
    """教学视频→文章流水线（抽帧/转写/成文，断点续跑）"""
    from core.video_to_article import VideoToArticlePipeline

    pipeline = VideoToArticlePipeline()
    result = pipeline.run(input_dir=args.input_dir, video_path=args.video)

    print()
    print(f"  视频 {result['videos']} 个 · 新转写 {result['transcribed']} 个"
          f" · 新成文 {result['articles']} 篇")


def cmd_pipeline_status(args):
    """查看单个视频的流水线步骤状态"""
    from core.video_to_article import VideoToArticlePipeline

    status = VideoToArticlePipeline.check_step_status(args.video_name)
    icons = {True: '✅', False: '⏳'}
    print(f"视频: {args.video_name}")
    print(f"  {icons[status['frames_done']]} 抽帧")
    print(f"  {icons[status['audio_done']]} 音频")
    print(f"  {icons[status['txt_done']]} 转写")
    print(f"  {icons[status['article_done']]} 成文")
    if status['all_done']:
        print("  已全部完成")


def register(subparsers):
    p_pipeline = subparsers.add_parser('pipeline', help='内容生产流水线（视频→文章）')
    pipeline_sub = p_pipeline.add_subparsers(dest='pipeline_cmd', help='流水线子命令')

    p_va = pipeline_sub.add_parser(
        'video-article', help='教学视频→文章（抽帧/ASR/成文，四步断点续跑）')
    p_va.add_argument('--input-dir', help='批量输入目录（默认 storage/videos_input）')
    p_va.add_argument('--video', help='单个视频文件路径（与 --input-dir 二选一）')
    p_va.set_defaults(func=cmd_pipeline_video_article)

    p_st = pipeline_sub.add_parser('status', help='查看视频的流水线步骤状态')
    p_st.add_argument('video_name', help='视频名（相对输入目录的去扩展名路径）')
    p_st.set_defaults(func=cmd_pipeline_status)
