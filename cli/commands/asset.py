"""asset 命令域 — 素材资产扫描/检索/统计"""

import sys


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


def register(subparsers):
    p_asset = subparsers.add_parser('asset', help='素材资产管理（标签/检索/统计）')
    asset_sub = p_asset.add_subparsers(dest='asset_cmd', help='素材子命令')

    p_as = asset_sub.add_parser('scan', help='扫描目录注册素材')
    p_as.add_argument('type', choices=['novel'], help='素材类型')
    p_as.add_argument('--project', required=True, help='项目名称')
    p_as.add_argument('--dir', required=True, help='目录路径')
    p_as.set_defaults(func=cmd_asset_scan)

    p_al = asset_sub.add_parser('list', help='列出素材')
    p_al.add_argument('--type', dest='asset_type', help='按类型过滤')
    p_al.add_argument('--project', help='按项目过滤')
    p_al.add_argument('--limit', type=int, default=20, help='数量限制')
    p_al.add_argument('--offset', type=int, default=0, help='偏移量')
    p_al.set_defaults(func=cmd_asset_list)

    p_ase = asset_sub.add_parser('search', help='按标签搜索素材')
    p_ase.add_argument('tags', nargs='+', help='标签列表')
    p_ase.add_argument('--any', action='store_true', help='任一标签匹配即可(默认全部匹配)')
    p_ase.add_argument('--type', dest='asset_type', help='按类型过滤')
    p_ase.add_argument('--project', help='按项目过滤')
    p_ase.set_defaults(func=cmd_asset_search)

    p_ast = asset_sub.add_parser('stats', help='素材统计')
    p_ast.set_defaults(func=cmd_asset_stats)
