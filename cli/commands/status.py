"""status / 业务线总览"""

import os


# 业务线目录（media-cli status 探测用；新增业务线在此登记并同步根文档）
# 2026-10 业务线已全部并入主工程：内容资产在 assets/，能力在 core/，技能在 .claude/skills/
BUSINESS_LINES = []


def cmd_status(args):
    """查看整体状态"""
    from core.config import config
    from core.storage import Storage
    from core.task_manager import TaskManager
    from core.asset_manager import AssetManager
    from publishing.publisher_base import MultiPlatformPublisher

    storage = Storage()
    storage_stats = storage.stats()

    tm = TaskManager()
    task_stats = tm.stats()

    am = AssetManager()
    asset_stats = am.stats()

    mp = MultiPlatformPublisher()
    platforms = mp.available_platforms()

    print("=" * 60)
    print("  AI 自媒体内容生产中台 — 状态总览")
    print("=" * 60)
    print()
    print(f"  📂  存储根目录:       {storage.base_dir}")
    print()

    print("  ━━━ 内容产出 ━━━")
    print(f"  📹  输入视频数量:     {storage_stats['videos_input']}")
    print(f"  📝  文章数量:         {storage_stats['articles']}")
    print(f"  📚  小说项目数:       {storage_stats['novel_projects']}")
    print()

    print("  ━━━ 任务中心 ━━━")
    print(f"  📋  任务总数:         {task_stats['total']}")
    print(f"  ✅  已完成:           {task_stats['by_status'].get('done', 0)}")
    print(f"  ⏳  待处理:           {task_stats['by_status'].get('pending', 0)}")
    print(f"  🔄  运行中:           {task_stats['by_status'].get('running', 0)}")
    print(f"  ❌  失败:             {task_stats['by_status'].get('failed', 0)}")
    print(f"  📊  今日完成:         {task_stats['today_done']}")
    print()

    print("  ━━━ 素材资产 ━━━")
    print(f"  📦  素材总数:         {asset_stats['total']}")
    print(f"  🏷️   标签数量:         {asset_stats['tag_count']}")
    print(f"  💾  总大小:           {asset_stats['total_size_mb']} MB")
    print()

    print("  ━━━ 发布平台 ━━━")
    platform_status = ' / '.join(platforms) if platforms else '（无可用平台）'
    print(f"  🚀  可用平台:         {platform_status}")
    print()

    print("  ━━━ AI 能力 ━━━")
    print(f"  🤖  LLM 模型:         {config.LLM_MODEL}")
    print(f"  🎤  ASR 模式:         {'本地(faster-whisper)' if config.ASR_LOCAL_ENABLED else '云端(小米mimo)'}")
    print(f"  🎬  FFmpeg 路径:      {config.FFMPEG_PATH}")
    print()

    # 列出现有业务线目录
    app_dirs = [d for d in BUSINESS_LINES
                if os.path.isdir(os.path.join(config.BASE_DIR, d))]
    if app_dirs:
        print(f"  📁  业务线:           {', '.join(app_dirs)}")
        print()

    print("  环境自检请运行: python media-cli.py doctor")
    print("=" * 60)


def register(subparsers):
    p_status = subparsers.add_parser('status', help='查看整体状态')
    p_status.set_defaults(func=cmd_status)
