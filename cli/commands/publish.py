"""publish 命令域 — 飞书 / 微信公众号 / 抖音 / 一键多平台"""

import sys


def cmd_feishu_publish(args):
    """发布到飞书"""
    from publishing.feishu_publisher import FeishuPublisher

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
    from publishing.wechat_publisher import WechatPublisher
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
    from publishing.wechat_publisher import WechatPublisher

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
    from publishing.wechat_publisher import WechatPublisher

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
                    # 前 20 位是微信 media_id 的公共前缀，截到 24 位才可区分
                    print(f"  {i}. {title}  [media_id: {media_id[:24]}...]")
                else:
                    print(f"  {i}. media_id: {media_id[:24]}...")
        else:
            print(f"❌ 获取失败: {result.get('error')}")
            sys.exit(1)


def cmd_wechat_publish_draft(args):
    """发布草稿"""
    from publishing.wechat_publisher import WechatPublisher

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
    from publishing.wechat_publisher import WechatPublisher

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


def cmd_douyin_login(args):
    """扫码登录抖音创作者平台，保存登录态 Cookie"""
    from publishing.douyin_publisher import DouyinPublisher

    result = DouyinPublisher().login(timeout=args.timeout)
    if result.success:
        print("✅ 抖音登录态已就绪，可以发布视频了")
    else:
        print(f"❌ 登录失败: {result.error}")
        sys.exit(1)


def cmd_douyin_publish(args):
    """上传视频到抖音（--draft 存入草稿箱）"""
    from publishing.douyin_publisher import DouyinPublisher

    pub = DouyinPublisher()
    result = pub.publish_markdown(args.title, '', options={
        'video': args.video_file,
        'tags': args.tags or [],
        'desc': args.desc or '',
        'draft': args.draft,
    })

    if result.success and args.draft:
        print("✅ 已存入抖音草稿箱!")
        print(f"   请在抖音 App 草稿箱内检查后手动发布，创作者后台: {result.url}")
    elif result.success:
        print("✅ 发布流程完成!")
        print(f"   作品进入平台审核，稍后可在创作者后台查看: {result.url}")
    else:
        print(f"❌ 发布失败: {result.error}")
        sys.exit(1)


def cmd_douyin_check(args):
    """检查抖音登录态是否有效"""
    from publishing.douyin_publisher import DouyinPublisher

    result = DouyinPublisher().health_check()
    if result.success:
        print("✅ 抖音登录态有效")
    else:
        print(f"❌ {result.error}")
        sys.exit(1)


def cmd_wechat_compose(args):
    """AI 写作助手（LangGraph 智能体：选题→写作→配图→审稿→草稿箱）"""
    import sys
    from creation.wechat_agent.app import main as agent_main

    argv = ['wechat-agent']
    if args.topic:
        argv.append(args.topic)
    if args.output:
        argv += ['-o', args.output]
    if args.publish:
        argv.append('-p')
    sys.argv = argv
    agent_main()


def cmd_publish_all(args):
    """一键多平台发布"""
    from publishing.publisher_base import MultiPlatformPublisher

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

    # 抖音为视频平台：需要 --video；显式指定却没给视频则报错，默认携带时跳过
    explicit_platforms = set(args.platforms or [])
    if 'douyin' in platforms:
        if args.video:
            options['douyin'] = {'video': args.video, 'tags': args.tags or []}
        elif 'douyin' in explicit_platforms:
            print("❌ 平台 douyin 需要视频文件：--video <视频路径>")
            sys.exit(1)
        else:
            platforms = [p for p in platforms if p != 'douyin']
            print("[跳过] douyin：未提供 --video（抖音为视频平台，单发请用 douyin publish）")

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


def register(subparsers):
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

    p_wu = wechat_sub.add_parser('upload-image', help='上传图片到微信')
    p_wu.add_argument('image', help='图片路径')
    p_wu.add_argument('--permanent', action='store_true', help='上传为永久素材（用于封面图），默认上传为正文图片')
    p_wu.set_defaults(func=cmd_wechat_upload_image)

    p_wd = wechat_sub.add_parser('drafts', help='草稿管理')
    p_wd.add_argument('action', choices=['list', 'count'], help='操作：list(列表) / count(数量)')
    p_wd.add_argument('--offset', type=int, default=0, help='偏移量')
    p_wd.add_argument('--count', type=int, default=10, help='数量（最多20）')
    p_wd.set_defaults(func=cmd_wechat_drafts)

    p_wpd = wechat_sub.add_parser('publish-draft', help='发布已有草稿')
    p_wpd.add_argument('media_id', help='草稿的 media_id')
    p_wpd.set_defaults(func=cmd_wechat_publish_draft)

    p_wc = wechat_sub.add_parser('compose', help='AI 写作助手生成公众号文章（LangGraph 智能体）')
    p_wc.add_argument('topic', nargs='?', help='文章主题（不指定则进入交互式模式）')
    p_wc.add_argument('-o', '--output', help='输出文件路径（如 article.md）')
    p_wc.add_argument('-p', '--publish', action='store_true', help='生成后自动发布到微信公众号草稿箱')
    p_wc.set_defaults(func=cmd_wechat_compose)

    p_ws = wechat_sub.add_parser('status', help='查询发布状态')
    p_ws.add_argument('publish_id', help='发布任务的 publish_id')
    p_ws.set_defaults(func=cmd_wechat_publish_status)

    # ---- douyin ----
    p_douyin = subparsers.add_parser('douyin', help='抖音发布相关（Playwright 自动化创作者后台）')
    douyin_sub = p_douyin.add_subparsers(dest='douyin_cmd', help='抖音子命令')

    p_dl = douyin_sub.add_parser('login', help='扫码登录抖音创作者平台，保存登录态 Cookie')
    p_dl.add_argument('--timeout', type=int, default=300, help='等待扫码的超时秒数（默认300）')
    p_dl.set_defaults(func=cmd_douyin_login)

    p_dp = douyin_sub.add_parser('publish', help='上传视频到抖音（--draft 存草稿箱）')
    p_dp.add_argument('--video-file', required=True, help='视频文件路径')
    p_dp.add_argument('--title', required=True, help='视频标题/描述文案')
    p_dp.add_argument('--desc', help='描述文案（默认用标题）')
    p_dp.add_argument('--tags', nargs='*', help='话题标签（如 生活 vlog）')
    p_dp.add_argument('--draft', action='store_true',
                      help='存入抖音草稿箱而非直接发布')
    p_dp.set_defaults(func=cmd_douyin_publish)

    p_dc = douyin_sub.add_parser('check', help='检查抖音登录态是否有效')
    p_dc.set_defaults(func=cmd_douyin_check)

    # ---- publish（多平台）----
    p_pub = subparsers.add_parser('publish', help='一键多平台发布（飞书+公众号+抖音）')
    p_pub.add_argument('--title', required=True, help='文章标题')
    p_pub.add_argument('--content', help='Markdown 正文内容')
    p_pub.add_argument('--content-file', help='从文件读取 Markdown 正文')
    p_pub.add_argument('--platforms', nargs='+',
                       help='目标平台 (feishu wechat douyin)，默认所有可用平台')
    p_pub.add_argument('--images', nargs='*', help='飞书：要插入的图片路径')
    p_pub.add_argument('--cover', help='微信：封面图路径')
    p_pub.add_argument('--author', help='微信：作者名')
    p_pub.add_argument('--digest', help='微信：文章摘要')
    p_pub.add_argument('--open-comment', action='store_true', help='微信：打开评论')
    p_pub.add_argument('--publish-now', action='store_true', help='微信：立即发布（默认仅草稿）')
    p_pub.add_argument('--video', help='抖音：视频文件路径（多平台发布时提供才包含 douyin）')
    p_pub.add_argument('--tags', nargs='*', help='抖音：话题标签')
    p_pub.set_defaults(func=cmd_publish_all)
