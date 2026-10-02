"""storage 命令域 — 存储统计/列举"""


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


def register(subparsers):
    p_storage = subparsers.add_parser('storage', help='存储管理')
    storage_sub = p_storage.add_subparsers(dest='storage_cmd', help='存储子命令')

    p_ss = storage_sub.add_parser('stats', help='存储统计')
    p_ss.set_defaults(func=cmd_storage_stats)

    p_sl = storage_sub.add_parser('list', help='列出内容')
    p_sl.add_argument('type', choices=['videos', 'articles', 'novels'], help='类型')
    p_sl.set_defaults(func=cmd_storage_list)
