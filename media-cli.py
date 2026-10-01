#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
media-cli — AI 自媒体内容生产中台 统一命令行入口

用法：
    python media-cli.py --help
    python media-cli.py status                     # 查看整体状态
    python media-cli.py video info <path>          # 获取视频信息
    python media-cli.py video merge <files...> -o output.mp4
    python media-cli.py asr transcribe <audio>     # 语音转写
    python media-cli.py llm chat "你的问题"         # 调用大模型
    python media-cli.py feishu publish --title xxx --content file.md
    python media-cli.py storage stats              # 存储统计
"""

import sys
import os
import argparse

# 确保 core 包可导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_status(args):
    """查看整体状态"""
    from core.config import config
    from core.storage import Storage
    from core.task_manager import TaskManager
    from core.asset_manager import AssetManager
    from core.publisher_base import MultiPlatformPublisher

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
    app_dirs = [d for d in [
        'hello_doubao_video', 'hello_feishu', 'hello_novel',
        'hello_webchat_official', 'hello_webchat_solo', 'hello_weixin_book',
    ] if os.path.isdir(os.path.join(config.BASE_DIR, d))]
    if app_dirs:
        print(f"  📁  业务线:           {', '.join(app_dirs)}")
        print()

    print("=" * 60)


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


def cmd_asr_transcribe(args):
    """语音转写"""
    from core.asr_client import ASRClient

    asr = ASRClient()

    if args.local:
        result = asr.transcribe_local(args.audio)
        if args.srt and result.get('success'):
            srt_path = os.path.splitext(args.audio)[0] + '.srt'
            result = asr.transcribe_with_srt(args.audio, srt_path)
    else:
        result = asr.transcribe(args.audio)

    if result.get('success'):
        text = result.get('text', '')
        print(f"✅ 转写完成（{len(text)} 字符）")
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"已保存到: {args.output}")
        else:
            print()
            print("--- 转写文本 ---")
            print(text[:500] + ("..." if len(text) > 500 else ""))
    else:
        print(f"❌ 转写失败: {result.get('error', '未知错误')}")
        sys.exit(1)


def cmd_llm_chat(args):
    """调用大模型"""
    from core.llm_client import LLMClient

    llm = LLMClient(system_prompt=args.system or '你是一个专业的AI助手。')

    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            prompt = f.read()
    else:
        prompt = args.prompt

    if args.stream:
        print("--- 流式输出 ---")
        result = llm.chat_stream(prompt)
    else:
        result = llm.chat(prompt)
        print(result)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"\n已保存到: {args.output}")


def cmd_feishu_publish(args):
    """发布到飞书"""
    from core.feishu_publisher import FeishuPublisher

    pub = FeishuPublisher()

    # 读取内容
    if args.content_file:
        with open(args.content_file, 'r', encoding='utf-8') as f:
            content = f.read()
    elif args.content:
        content = args.content
    else:
        print("❌ 请提供 --content 或 --content-file")
        sys.exit(1)

    # 图片列表
    images = []
    if args.images:
        for i, img_path in enumerate(args.images):
            images.append({'path': img_path, 'caption': f'图片{i+1}'})

    result = pub.publish_article(args.title, content, images=images if images else None)

    if result.get('success'):
        print(f"✅ 发布成功!")
        print(f"   文档链接: {result.get('doc_url')}")
        if result.get('images_count'):
            print(f"   插入图片: {result['images_count']} 张")
    else:
        print(f"❌ 发布失败: {result.get('error', '未知错误')}")
        sys.exit(1)


def cmd_wechat_publish(args):
    """发布到微信公众号草稿箱"""
    from core.wechat_publisher import WechatPublisher
    from core.config import config

    pub = WechatPublisher()

    # 读取内容
    if args.content_file:
        with open(args.content_file, 'r', encoding='utf-8') as f:
            content = f.read()
    elif args.content:
        content = args.content
    else:
        print("❌ 请提供 --content 或 --content-file")
        sys.exit(1)

    # 封面图
    cover_path = args.cover

    # 作者
    author = args.author or config.WECHAT_DEFAULT_AUTHOR or ''

    # 评论开关
    open_comment = 1 if args.open_comment else int(config.WECHAT_OPEN_COMMENT)
    fans_only = 1 if args.fans_only else 0

    result = pub.publish_article_from_markdown(
        title=args.title,
        markdown_content=content,
        cover_image_path=cover_path,
        author=author,
        digest=args.digest or '',
        content_source_url=args.source_url or '',
        need_open_comment=open_comment,
        only_fans_can_comment=fans_only,
        auto_publish=args.publish_now,
    )

    if result.get('success'):
        print(f"✅ 草稿创建成功!")
        print(f"   media_id: {result.get('media_id')}")
        if result.get('publish_id'):
            print(f"   已发布! publish_id: {result['publish_id']}")
        else:
            print(f"   (已保存到草稿箱，未发布)")
    else:
        print(f"❌ 发布失败: {result.get('error', '未知错误')}")
        if result.get('errcode'):
            print(f"   错误码: {result['errcode']}")
        sys.exit(1)


def cmd_wechat_upload_image(args):
    """上传图片到微信（永久素材/正文图片）"""
    from core.wechat_publisher import WechatPublisher

    pub = WechatPublisher()

    if args.permanent:
        result = pub.upload_material_image(args.image)
        if result.get('success'):
            print(f"✅ 永久素材上传成功!")
            print(f"   media_id: {result.get('media_id')}")
            print(f"   url: {result.get('url')}")
        else:
            print(f"❌ 上传失败: {result.get('error')}")
            sys.exit(1)
    else:
        result = pub.upload_image_for_article(args.image)
        if result.get('success'):
            print(f"✅ 正文图片上传成功!")
            print(f"   url: {result.get('url')}")
        else:
            print(f"❌ 上传失败: {result.get('error')}")
            sys.exit(1)


def cmd_wechat_drafts(args):
    """查看草稿列表/数量"""
    from core.wechat_publisher import WechatPublisher

    pub = WechatPublisher()

    if args.action == 'count':
        result = pub.get_draft_count()
        if result.get('success'):
            print(f"草稿总数: {result.get('total_count')}")
        else:
            print(f"❌ 获取失败: {result.get('error')}")
            sys.exit(1)
    elif args.action == 'list':
        result = pub.get_draft_list(offset=args.offset, count=args.count, no_content=1)
        if result.get('success'):
            items = result.get('item', [])
            total = result.get('total_count', len(items))
            print(f"草稿列表 (共 {total} 条，显示 {len(items)} 条):")
            for i, item in enumerate(items, 1):
                media_id = item.get('media_id', '?')
                content = item.get('content', {})
                articles = content.get('news_item', [])
                if articles:
                    title = articles[0].get('title', '(无标题)')
                    print(f"  {i}. {title}  [media_id: {media_id[:20]}...]")
                else:
                    print(f"  {i}. media_id: {media_id[:20]}...")
        else:
            print(f"❌ 获取失败: {result.get('error')}")
            sys.exit(1)


def cmd_wechat_publish_draft(args):
    """发布草稿"""
    from core.wechat_publisher import WechatPublisher

    pub = WechatPublisher()
    result = pub.publish(args.media_id)

    if result.get('success'):
        print(f"✅ 发布请求已提交!")
        print(f"   publish_id: {result.get('publish_id')}")
        print(f"   提示: 发布是异步的，可用 `wechat status <publish_id>` 查询状态")
    else:
        print(f"❌ 发布失败: {result.get('error')}")
        sys.exit(1)


def cmd_wechat_publish_status(args):
    """查询发布状态"""
    from core.wechat_publisher import WechatPublisher

    pub = WechatPublisher()
    result = pub.get_publish_status(args.publish_id)

    if result.get('success'):
        status_map = {
            0: '发布成功',
            1: '发布中',
            2: '发布失败',
            3: '原创检测中',
        }
        status_code = result.get('publish_status', -1)
        status_text = status_map.get(status_code, f'未知状态({status_code})')
        print(f"发布状态: {status_text}")
        if result.get('article_id'):
            print(f"文章ID: {result['article_id']}")
        if result.get('fail_idx'):
            print(f"失败索引: {result['fail_idx']}")
    else:
        print(f"❌ 查询失败: {result.get('error')}")
        sys.exit(1)


def cmd_story_script(args):
    """小说章节 → 视频分镜脚本"""
    from core.story_to_script import StoryToScript

    # 读取章节内容
    with open(args.input, 'r', encoding='utf-8') as f:
        chapter_text = f.read()

    title = args.title or args.input

    converter = StoryToScript(style=args.style)
    result = converter.chapter_to_script(
        chapter_text,
        style=args.style,
        num_shots=args.num_shots,
        title=title,
    )

    if result.get('success'):
        print(f"\n✅ 分镜脚本生成完成！共 {len(result['shots'])} 个分镜")
        print(f"   风格: {result['style']}")

        # 输出摘要
        if result.get('summary'):
            print(f"\n📝 章节摘要: {result['summary'][:100]}...")

        # 列出分镜概览
        print(f"\n🎬 分镜概览:")
        for shot in result['shots']:
            desc = shot.get('description', '')[:50]
            print(f"   [{shot.get('shot_num')}] {shot.get('shot_type', '-')} - {desc}...")

        # 保存
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result['full_script'])
            print(f"\n💾 完整脚本已保存: {args.output}")

        # 单独输出提示词
        if args.prompts_output:
            with open(args.prompts_output, 'w', encoding='utf-8') as f:
                for i, p in enumerate(result['prompt_list'], 1):
                    f.write(f"【分镜{i}】\n{p}\n\n")
            print(f"💾 提示词已保存: {args.prompts_output}")
    else:
        print(f"❌ 生成失败: {result.get('error', '未知错误')}")
        sys.exit(1)


def cmd_story_article(args):
    """小说章节 → 公众号/飞书文章"""
    from core.story_to_article import StoryToArticle

    # 读取章节
    with open(args.input, 'r', encoding='utf-8') as f:
        chapter_text = f.read()

    title = args.title or args.input

    converter = StoryToArticle()

    type_map = {
        'deep': 'deep_analysis',
        'summary': 'summary',
        'character': 'character',
        'worldview': 'worldview',
    }
    article_type = type_map.get(args.type, 'deep_analysis')

    if article_type == 'deep_analysis':
        result = converter.chapter_to_deep_article(chapter_text, title=title)
    elif article_type == 'summary':
        result = converter.chapter_to_summary(chapter_text, title=title)
    elif article_type == 'character':
        result = converter.chapter_to_character_analysis(
            chapter_text, args.character or '主角', title=title
        )
    elif article_type == 'worldview':
        result = converter.chapter_to_worldview_article(
            chapter_text, args.topic or '', title=title
        )
    else:
        result = converter.chapter_to_deep_article(chapter_text, title=title)

    if result.get('success'):
        print(f"\n✅ 文章生成完成！")
        print(f"   标题: {result['title']}")
        print(f"   类型: {result.get('article_type', args.type)}")
        print(f"   字数: 约 {result.get('word_count', 0)} 字")

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result['content'])
            print(f"💾 文章已保存: {args.output}")
        else:
            print(f"\n--- 文章预览 ---\n{result['content'][:300]}...")
    else:
        print(f"❌ 生成失败: {result.get('error', '未知错误')}")
        sys.exit(1)


def cmd_asset_scan(args):
    """扫描目录注册素材"""
    from core.asset_manager import AssetManager

    am = AssetManager()

    if args.type == 'novel':
        count = am.scan_novel_project(args.project, args.dir)
        print(f"✅ 扫描完成，注册了 {count} 个章节素材")
    else:
        print(f"❌ 暂不支持的类型: {args.type}")
        sys.exit(1)


def cmd_asset_list(args):
    """列出素材"""
    from core.asset_manager import AssetManager

    am = AssetManager()
    assets = am.list_assets(
        asset_type=args.asset_type,
        project=args.project,
        limit=args.limit,
        offset=args.offset,
    )

    if not assets:
        print("暂无素材")
        return

    print(f"共 {len(assets)} 个素材:\n")
    for a in assets:
        tags = ' '.join([f'[{t}]' for t in a['tags'][:3]])
        print(f"  [{a['id']:>4}] {a['asset_type']:<18} {a['title'][:30]:<30} {tags}")
        if a.get('project'):
            print(f"        项目: {a['project']}  更新: {a['updated_at']}")


def cmd_asset_search(args):
    """按标签搜索素材"""
    from core.asset_manager import AssetManager

    am = AssetManager()
    assets = am.search_by_tags(
        args.tags,
        match_all=not args.any,
        asset_type=args.asset_type,
        project=args.project,
    )

    print(f"找到 {len(assets)} 个匹配素材:\n")
    for a in assets:
        tags = ' '.join([f'[{t}]' for t in a['tags'][:3]])
        print(f"  [{a['id']:>4}] {a['title'][:40]:<40} {tags}")


def cmd_asset_stats(args):
    """素材统计"""
    from core.asset_manager import AssetManager

    am = AssetManager()
    stats = am.stats()

    print("=" * 50)
    print("  📊 素材资产统计")
    print("=" * 50)
    print(f"  素材总数:     {stats['total']}")
    print(f"  标签总数:     {stats['tag_count']}")
    print(f"  总大小:       {stats['total_size_mb']} MB")
    print()
    print("  按类型分布:")
    for t, c in stats['by_type'].items():
        print(f"    {t:<25} {c}")
    if stats['by_project']:
        print()
        print("  按项目分布:")
        for p, c in stats['by_project'].items():
            print(f"    {p:<25} {c}")
    print("=" * 50)


def cmd_task_list(args):
    """列出任务"""
    from core.task_manager import TaskManager

    tm = TaskManager()
    tasks = tm.list_tasks(
        status=args.status,
        task_type=args.type,
        limit=args.limit,
        offset=args.offset,
    )

    if not tasks:
        print("暂无任务")
        return

    status_icon = {
        'done': '✅', 'running': '🔄', 'pending': '⏳',
        'failed': '❌', 'skipped': '⏭️'
    }

    print(f"共 {len(tasks)} 个任务:\n")
    for t in tasks:
        icon = status_icon.get(t['status'], '❓')
        duration = f"{t['duration']:.1f}s" if t['duration'] else '-'
        print(f"  {icon} [{t['id']}] {t['name'][:40]:<40} "
              f"{t['task_type']:<18} {t['status']:<8} {duration}")


def cmd_task_stats(args):
    """任务统计"""
    from core.task_manager import TaskManager

    tm = TaskManager()
    stats = tm.stats()

    print("=" * 50)
    print("  📋 任务统计")
    print("=" * 50)
    print(f"  任务总数:     {stats['total']}")
    print(f"  今日完成:     {stats['today_done']}")
    print(f"  今日失败:     {stats['today_failed']}")
    print(f"  平均耗时:     {stats['avg_duration_seconds']} 秒")
    print()
    print("  按状态分布:")
    for s, c in stats['by_status'].items():
        print(f"    {s:<12} {c}")
    print()
    print("  按类型分布:")
    for t, c in stats['by_type'].items():
        print(f"    {t:<25} {c}")
    print("=" * 50)


def cmd_task_retry(args):
    """重试失败任务"""
    from core.task_manager import TaskManager

    tm = TaskManager()
    count = tm.retry_failed_tasks(task_type=args.type)
    print(f"已重置 {count} 个失败任务为待处理状态")


def cmd_task_detail(args):
    """查看任务详情"""
    from core.task_manager import TaskManager

    tm = TaskManager()
    task = tm.get_task(args.task_id)
    if not task:
        print(f"❌ 任务不存在: {args.task_id}")
        sys.exit(1)

    print("=" * 60)
    print(f"  任务: {task['name']}")
    print(f"  ID:   {task['id']}")
    print("=" * 60)
    print(f"  状态:       {task['status']}")
    print(f"  类型:       {task['task_type']}")
    print(f"  优先级:     {task['priority']}")
    print(f"  重试:       {task['retry_count']}/{task['max_retries']}")
    print(f"  创建时间:   {task['created_at_str']}")
    if task['started_at_str']:
        print(f"  开始时间:   {task['started_at_str']}")
    if task['completed_at_str']:
        print(f"  完成时间:   {task['completed_at_str']}")
    if task['duration']:
        print(f"  耗时:       {task['duration']:.1f} 秒")
    print()
    print(f"  参数:")
    import json
    print(f"    {json.dumps(task['params'], ensure_ascii=False, indent=2)}")
    if task['error']:
        print(f"\n  错误: {task['error']}")
    if task['result'] and task['result'] != {}:
        print(f"\n  结果:")
        print(f"    {json.dumps(task['result'], ensure_ascii=False, indent=2)}")

    # 日志
    logs = tm.get_task_logs(args.task_id)
    if logs:
        print(f"\n  执行日志 ({len(logs)} 条):")
        for log in logs:
            print(f"    [{log['created_at']}] [{log['status']}] {log['message']}")

    print("=" * 60)


def cmd_dashboard_start(args):
    """启动 Web 数据看板"""
    import importlib.util
    spec = importlib.util.find_spec('flask')
    if spec is None:
        print("Flask 未安装，正在安装...")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask'])

    print("🎬 启动 AI 内容生产中台 — Web 数据看板")
    print(f"   访问地址: http://localhost:{args.port}")
    print("   按 Ctrl+C 停止\n")

    from dashboard.app import create_app
    app = create_app()
    app.run(host='0.0.0.0', port=args.port, debug=False)


def cmd_publish_all(args):
    """一键多平台发布"""
    from core.publisher_base import MultiPlatformPublisher

    # 读取内容
    if args.content_file:
        with open(args.content_file, 'r', encoding='utf-8') as f:
            content = f.read()
    elif args.content:
        content = args.content
    else:
        print("❌ 请提供 --content 或 --content-file")
        sys.exit(1)

    publisher = MultiPlatformPublisher()
    available = publisher.available_platforms()

    platforms = args.platforms if args.platforms else available
    # 过滤不可用的
    platforms = [p for p in platforms if p in available]

    if not platforms:
        print(f"❌ 没有可用的发布平台。可用平台: {', '.join(available)}")
        sys.exit(1)

    # 组装各平台 options
    options = {}
    if args.images:
        options['feishu'] = {'images': [{'path': p} for p in args.images]}
    if args.cover or args.author or args.publish_now:
        options['wechat'] = {
            'cover_image': args.cover,
            'author': args.author or '',
            'digest': args.digest or '',
            'publish_now': args.publish_now,
            'open_comment': 1 if args.open_comment else 0,
        }

    print(f"🚀 开始发布到 {len(platforms)} 个平台: {', '.join(platforms)}\n")

    result = publisher.publish_all(args.title, content, platforms=platforms, options=options)

    print()
    print("=" * 50)
    print(f"  发布结果：成功 {result['success_count']} / 总计 {result['total']}")
    print("=" * 50)

    for r in result['results']:
        icon = '✅' if r.get('success') else '❌'
        platform = r.get('platform', '')
        url = r.get('url', '')
        err = r.get('error', '')

        if r.get('success'):
            line = f"  {icon} {platform:<12} 成功"
            if url:
                line += f"  → {url[:60]}..."
            print(line)
        else:
            print(f"  {icon} {platform:<12} 失败: {err[:60]}")

    print("=" * 50)

    if result['fail_count'] > 0:
        sys.exit(1)


def cmd_storage_stats(args):
    """存储统计"""
    from core.storage import Storage

    storage = Storage()
    stats = storage.stats()

    print("=" * 50)
    print("  📦 存储统计")
    print("=" * 50)
    print(f"  根目录: {storage.base_dir}")
    print()
    print(f"  输入视频:    {stats['videos_input']} 个")
    print(f"  文章数量:    {stats['articles']} 篇")
    print(f"  小说项目:    {stats['novel_projects']} 个")
    print("=" * 50)


def cmd_storage_list(args):
    """列出存储内容"""
    from core.storage import Storage

    storage = Storage()

    if args.type == 'videos':
        videos = storage.list_videos()
        if videos:
            print(f"找到 {len(videos)} 个视频:")
            for v in videos:
                print(f"  {v}")
        else:
            print("暂无视频")

    elif args.type == 'articles':
        articles = storage.list_articles()
        if articles:
            print(f"找到 {len(articles)} 篇文章:")
            for a in articles:
                print(f"  {a}")
        else:
            print("暂无文章")

    elif args.type == 'novels':
        projects = storage.list_novel_projects()
        if projects:
            print(f"找到 {len(projects)} 个小说项目:")
            for p in projects:
                print(f"  {p}")
        else:
            print("暂无小说项目")


def main():
    parser = argparse.ArgumentParser(
        prog='media-cli',
        description='AI 自媒体内容生产中台 — 统一命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s status                              查看整体状态
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

    # ---- status ----
    p_status = subparsers.add_parser('status', help='查看整体状态')
    p_status.set_defaults(func=cmd_status)

    # ---- video ----
    p_video = subparsers.add_parser('video', help='视频处理相关')
    video_sub = p_video.add_subparsers(dest='video_cmd', help='视频子命令')

    # video info
    p_vi = video_sub.add_parser('info', help='获取视频信息')
    p_vi.add_argument('path', help='视频文件路径')
    p_vi.set_defaults(func=cmd_video_info)

    # video merge
    p_vm = video_sub.add_parser('merge', help='合并多个视频')
    p_vm.add_argument('files', nargs='+', help='输入视频文件（按顺序）')
    p_vm.add_argument('-o', '--output', required=True, help='输出文件路径')
    p_vm.add_argument('--fade', action='store_true', help='添加淡入淡出转场')
    p_vm.add_argument('--fade-duration', type=float, default=0.5, help='转场时长（秒）')
    p_vm.add_argument('--reencode', action='store_true', help='重新编码（默认无损合并）')
    p_vm.set_defaults(func=cmd_video_merge)

    # video extract
    p_ve = video_sub.add_parser('extract', help='提取帧或音频')
    p_ve.add_argument('type', choices=['frames', 'audio'], help='提取类型')
    p_ve.add_argument('input', help='输入视频路径')
    p_ve.add_argument('output', help='输出目录')
    p_ve.set_defaults(func=cmd_video_extract)

    # ---- asr ----
    p_asr = subparsers.add_parser('asr', help='语音转写相关')
    asr_sub = p_asr.add_subparsers(dest='asr_cmd', help='ASR 子命令')

    p_at = asr_sub.add_parser('transcribe', help='语音转写')
    p_at.add_argument('audio', help='音频文件路径')
    p_at.add_argument('--local', action='store_true', help='使用本地 faster-whisper')
    p_at.add_argument('--srt', action='store_true', help='生成 SRT 字幕（仅本地模式）')
    p_at.add_argument('-o', '--output', help='输出文本文件路径')
    p_at.set_defaults(func=cmd_asr_transcribe)

    # ---- llm ----
    p_llm = subparsers.add_parser('llm', help='大模型调用')
    llm_sub = p_llm.add_subparsers(dest='llm_cmd', help='LLM 子命令')

    p_lc = llm_sub.add_parser('chat', help='单轮对话')
    p_lc.add_argument('prompt', nargs='?', help='提示词')
    p_lc.add_argument('-f', '--file', help='从文件读取提示词')
    p_lc.add_argument('-s', '--system', help='系统提示词')
    p_lc.add_argument('--stream', action='store_true', help='流式输出')
    p_lc.add_argument('-o', '--output', help='输出文件路径')
    p_lc.set_defaults(func=cmd_llm_chat)

    # ---- feishu ----
    p_feishu = subparsers.add_parser('feishu', help='飞书发布相关')
    feishu_sub = p_feishu.add_subparsers(dest='feishu_cmd', help='飞书子命令')

    p_fp = feishu_sub.add_parser('publish', help='发布文章到飞书')
    p_fp.add_argument('--title', required=True, help='文档标题')
    p_fp.add_argument('--content', help='Markdown 内容')
    p_fp.add_argument('--content-file', help='从文件读取 Markdown 内容')
    p_fp.add_argument('--images', nargs='*', help='要插入的图片路径')
    p_fp.set_defaults(func=cmd_feishu_publish)

    # ---- wechat ----
    p_wechat = subparsers.add_parser('wechat', help='微信公众号发布相关')
    wechat_sub = p_wechat.add_subparsers(dest='wechat_cmd', help='微信子命令')

    # wechat publish
    p_wp = wechat_sub.add_parser('publish', help='发布文章到公众号草稿箱（Markdown 输入）')
    p_wp.add_argument('--title', required=True, help='文章标题（不超过32字）')
    p_wp.add_argument('--content', help='Markdown 正文内容')
    p_wp.add_argument('--content-file', help='从文件读取 Markdown 正文')
    p_wp.add_argument('--cover', help='封面图本地路径')
    p_wp.add_argument('--author', help='作者名')
    p_wp.add_argument('--digest', help='文章摘要（不超过120字）')
    p_wp.add_argument('--source-url', help='原文链接（阅读原文）')
    p_wp.add_argument('--open-comment', action='store_true', help='打开评论')
    p_wp.add_argument('--fans-only', action='store_true', help='仅粉丝可评论')
    p_wp.add_argument('--publish-now', action='store_true', help='创建草稿后立即发布')
    p_wp.set_defaults(func=cmd_wechat_publish)

    # wechat upload-image
    p_wu = wechat_sub.add_parser('upload-image', help='上传图片到微信')
    p_wu.add_argument('image', help='图片路径')
    p_wu.add_argument('--permanent', action='store_true', help='上传为永久素材（用于封面图），默认上传为正文图片')
    p_wu.set_defaults(func=cmd_wechat_upload_image)

    # wechat drafts
    p_wd = wechat_sub.add_parser('drafts', help='草稿管理')
    p_wd.add_argument('action', choices=['list', 'count'], help='操作：list(列表) / count(数量)')
    p_wd.add_argument('--offset', type=int, default=0, help='偏移量')
    p_wd.add_argument('--count', type=int, default=10, help='数量（最多20）')
    p_wd.set_defaults(func=cmd_wechat_drafts)

    # wechat publish-draft
    p_wpd = wechat_sub.add_parser('publish-draft', help='发布已有草稿')
    p_wpd.add_argument('media_id', help='草稿的 media_id')
    p_wpd.set_defaults(func=cmd_wechat_publish_draft)

    # wechat status
    p_ws = wechat_sub.add_parser('status', help='查询发布状态')
    p_ws.add_argument('publish_id', help='发布任务的 publish_id')
    p_ws.set_defaults(func=cmd_wechat_publish_status)

    # ---- story ----
    p_story = subparsers.add_parser('story', help='小说内容转换（分镜/文章）')
    story_sub = p_story.add_subparsers(dest='story_cmd', help='内容转换子命令')

    # story script
    p_ss2 = story_sub.add_parser('script', help='小说章节 → 视频分镜脚本')
    p_ss2.add_argument('input', help='章节文件路径')
    p_ss2.add_argument('-t', '--title', help='章节标题')
    p_ss2.add_argument('-s', '--style', default='玄幻',
                       help='视频风格: 玄幻/科幻/都市/悬疑/古风/末日废土')
    p_ss2.add_argument('-n', '--num-shots', type=int, default=8, help='分镜数量')
    p_ss2.add_argument('-o', '--output', help='输出脚本文件(.md)')
    p_ss2.add_argument('--prompts-output', help='单独输出AI提示词文件')
    p_ss2.set_defaults(func=cmd_story_script)

    # story article
    p_sa = story_sub.add_parser('article', help='小说章节 → 公众号/飞书文章')
    p_sa.add_argument('input', help='章节文件路径')
    p_sa.add_argument('-t', '--title', help='章节标题')
    p_sa.add_argument('--type', default='deep',
                      choices=['deep', 'summary', 'character', 'worldview'],
                      help='文章类型: deep(深度解读)/summary(速读)/character(人物分析)/worldview(世界观)')
    p_sa.add_argument('--character', help='人物分析时指定人物名')
    p_sa.add_argument('--topic', help='世界观科普时指定主题')
    p_sa.add_argument('-o', '--output', help='输出文章文件(.md)')
    p_sa.set_defaults(func=cmd_story_article)

    # ---- asset ----
    p_asset = subparsers.add_parser('asset', help='素材资产管理（标签/检索/统计）')
    asset_sub = p_asset.add_subparsers(dest='asset_cmd', help='素材子命令')

    # asset scan
    p_as = asset_sub.add_parser('scan', help='扫描目录注册素材')
    p_as.add_argument('type', choices=['novel'], help='素材类型')
    p_as.add_argument('--project', required=True, help='项目名称')
    p_as.add_argument('--dir', required=True, help='目录路径')
    p_as.set_defaults(func=cmd_asset_scan)

    # asset list
    p_al = asset_sub.add_parser('list', help='列出素材')
    p_al.add_argument('--type', dest='asset_type', help='按类型过滤')
    p_al.add_argument('--project', help='按项目过滤')
    p_al.add_argument('--limit', type=int, default=20, help='数量限制')
    p_al.add_argument('--offset', type=int, default=0, help='偏移量')
    p_al.set_defaults(func=cmd_asset_list)

    # asset search
    p_ase = asset_sub.add_parser('search', help='按标签搜索素材')
    p_ase.add_argument('tags', nargs='+', help='标签列表')
    p_ase.add_argument('--any', action='store_true', help='任一标签匹配即可(默认全部匹配)')
    p_ase.add_argument('--type', dest='asset_type', help='按类型过滤')
    p_ase.add_argument('--project', help='按项目过滤')
    p_ase.set_defaults(func=cmd_asset_search)

    # asset stats
    p_ast = asset_sub.add_parser('stats', help='素材统计')
    p_ast.set_defaults(func=cmd_asset_stats)

    # ---- task ----
    p_task = subparsers.add_parser('task', help='任务管理（调度/状态/重试）')
    task_sub = p_task.add_subparsers(dest='task_cmd', help='任务子命令')

    # task list
    p_tl = task_sub.add_parser('list', help='列出任务')
    p_tl.add_argument('--status', choices=['pending', 'running', 'done', 'failed', 'skipped'],
                      help='按状态过滤')
    p_tl.add_argument('--type', help='按类型过滤')
    p_tl.add_argument('--limit', type=int, default=20, help='数量限制')
    p_tl.add_argument('--offset', type=int, default=0, help='偏移量')
    p_tl.set_defaults(func=cmd_task_list)

    # task stats
    p_ts = task_sub.add_parser('stats', help='任务统计')
    p_ts.set_defaults(func=cmd_task_stats)

    # task detail
    p_td = task_sub.add_parser('detail', help='任务详情')
    p_td.add_argument('task_id', help='任务 ID')
    p_td.set_defaults(func=cmd_task_detail)

    # task retry
    p_tr = task_sub.add_parser('retry', help='重试失败任务')
    p_tr.add_argument('--type', help='按类型过滤')
    p_tr.set_defaults(func=cmd_task_retry)

    # ---- dashboard ----
    p_dash = subparsers.add_parser('dashboard', help='Web 数据看板')
    dash_sub = p_dash.add_subparsers(dest='dash_cmd', help='看板子命令')

    p_ds = dash_sub.add_parser('start', help='启动 Web 看板')
    p_ds.add_argument('--port', type=int, default=5000, help='端口号')
    p_ds.set_defaults(func=cmd_dashboard_start)

    # ---- publish ----
    p_pub = subparsers.add_parser('publish', help='一键多平台发布（飞书+公众号）')
    p_pub.add_argument('--title', required=True, help='文章标题')
    p_pub.add_argument('--content', help='Markdown 正文内容')
    p_pub.add_argument('--content-file', help='从文件读取 Markdown 正文')
    p_pub.add_argument('--platforms', nargs='+',
                       help='目标平台 (feishu wechat)，默认所有可用平台')
    p_pub.add_argument('--images', nargs='*', help='飞书：要插入的图片路径')
    p_pub.add_argument('--cover', help='微信：封面图路径')
    p_pub.add_argument('--author', help='微信：作者名')
    p_pub.add_argument('--digest', help='微信：文章摘要')
    p_pub.add_argument('--open-comment', action='store_true', help='微信：打开评论')
    p_pub.add_argument('--publish-now', action='store_true', help='微信：立即发布（默认仅草稿）')
    p_pub.set_defaults(func=cmd_publish_all)

    # ---- storage ----
    p_storage = subparsers.add_parser('storage', help='存储管理')
    storage_sub = p_storage.add_subparsers(dest='storage_cmd', help='存储子命令')

    p_ss = storage_sub.add_parser('stats', help='存储统计')
    p_ss.set_defaults(func=cmd_storage_stats)

    p_sl = storage_sub.add_parser('list', help='列出内容')
    p_sl.add_argument('type', choices=['videos', 'articles', 'novels'], help='类型')
    p_sl.set_defaults(func=cmd_storage_list)

    # ---- 解析 ----
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
