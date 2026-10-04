"""video 命令域 — 视频信息/合并/抽帧抽音"""

import sys


def cmd_video_info(args):
    """获取视频信息"""
    from core.video_toolkit import VideoToolkit

    vt = VideoToolkit()
    info = vt.get_info(args.path)
    if info:
        print(f"视频: {args.path}")
        print(f"  时长: {info['duration']:.2f} 秒 ({info['duration']/60:.2f} 分钟)")
        print(f"  分辨率: {info['width']}x{info['height']}")
        print(f"  帧率: {info['fps']:.2f} fps")
    else:
        print("获取视频信息失败")
        sys.exit(1)


def cmd_video_merge(args):
    """合并多个视频"""
    from core.video_toolkit import VideoToolkit

    vt = VideoToolkit()

    if args.fade:
        print(f"正在合并 {len(args.files)} 个视频（带淡入淡出转场 {args.fade_duration}s）...")
        result = vt.concat_with_fade(args.files, args.output, args.fade_duration)
    else:
        print(f"正在无损合并 {len(args.files)} 个视频...")
        result = vt.concat(args.files, args.output, lossless=not args.reencode)

    if result.get('success'):
        print(f"✅ 合并完成: {result['output_path']}")
    else:
        print(f"❌ 合并失败: {result.get('error', '未知错误')}")
        sys.exit(1)


def cmd_video_extract(args):
    """提取视频帧或音频"""
    from core.video_toolkit import VideoToolkit

    vt = VideoToolkit()

    if args.type == 'frames':
        print(f"正在从 {args.input} 提取关键帧到 {args.output} ...")
        result = vt.extract_key_frames(args.input, args.output)
        if result.get('success'):
            print(f"✅ 提取完成: {result['frame_count']} 帧")
        else:
            print(f"❌ 提取失败: {result.get('error')}")
            sys.exit(1)

    elif args.type == 'audio':
        print(f"正在从 {args.input} 提取音频到 {args.output} ...")
        result = vt.extract_audio(args.input, args.output)
        if result.get('success'):
            print(f"✅ 音频已保存: {result['audio_path']}")
        else:
            print(f"❌ 提取失败: {result.get('error')}")
            sys.exit(1)


def cmd_video_html2video(args):
    """HTML 动画页面 → mp4（知识科普视频方案：帧步进 + ffmpeg 合成）"""
    from core.html_video import HtmlVideoRenderer

    renderer = HtmlVideoRenderer()
    print(f"正在渲染 {args.html} → {args.output} "
          f"（{args.width}x{args.height} @ {args.fps}fps，"
          f"时长 {str(args.duration) + 's' if args.duration else '读页面 meta'}）...")
    try:
        result = renderer.render(args.html, args.output, fps=args.fps,
                                 duration=args.duration, width=args.width,
                                 height=args.height, music=args.music)
    except Exception as e:
        print(f"❌ 渲染失败: {e}")
        sys.exit(1)
    print(f"✅ 渲染完成: {result['output']} "
          f"（{result['duration']:.1f}s / {result['frames']} 帧）")


def register(subparsers):
    p_video = subparsers.add_parser('video', help='视频处理相关')
    video_sub = p_video.add_subparsers(dest='video_cmd', help='视频子命令')

    p_vi = video_sub.add_parser('info', help='获取视频信息')
    p_vi.add_argument('path', help='视频文件路径')
    p_vi.set_defaults(func=cmd_video_info)

    p_vm = video_sub.add_parser('merge', help='合并多个视频')
    p_vm.add_argument('files', nargs='+', help='输入视频文件（按顺序）')
    p_vm.add_argument('-o', '--output', required=True, help='输出文件路径')
    p_vm.add_argument('--fade', action='store_true', help='添加淡入淡出转场')
    p_vm.add_argument('--fade-duration', type=float, default=0.5, help='转场时长（秒）')
    p_vm.add_argument('--reencode', action='store_true', help='重新编码（默认无损合并）')
    p_vm.set_defaults(func=cmd_video_merge)

    p_ve = video_sub.add_parser('extract', help='提取帧或音频')
    p_ve.add_argument('type', choices=['frames', 'audio'], help='提取类型')
    p_ve.add_argument('input', help='输入视频路径')
    p_ve.add_argument('output', help='输出目录')
    p_ve.set_defaults(func=cmd_video_extract)

    p_vh = video_sub.add_parser('html2video', help='HTML 动画页面渲染成视频（知识科普方案）')
    p_vh.add_argument('html', help='HTML 源文件（含 video-duration meta 与 CSS 时间线）')
    p_vh.add_argument('-o', '--output', required=True, help='输出 mp4 路径')
    p_vh.add_argument('--fps', type=int, default=30, help='帧率（默认 30）')
    p_vh.add_argument('--duration', type=float, help='总秒数（默认读 <meta name="video-duration">）')
    p_vh.add_argument('--width', type=int, default=1080, help='视口宽（默认 1080）')
    p_vh.add_argument('--height', type=int, default=1920, help='视口高（默认 1920）')
    p_vh.add_argument('--music', help='背景音乐文件（可选）')
    p_vh.set_defaults(func=cmd_video_html2video)
