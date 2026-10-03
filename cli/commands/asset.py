"""asset 命令域 — 素材资产扫描/检索/统计 + 待发布资产库（assets/）"""

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


def cmd_asset_ls(args):
    """待发布资产库清单（assets/）"""
    from publishing.asset_store import AssetStore

    store = AssetStore(root=args.root)
    items = store.list(type_=args.type_, project=args.project, status=args.status)

    if args.json:
        import json
        print(json.dumps({'assets': items, 'total': len(items)},
                         ensure_ascii=False, indent=2))
        return

    if not items:
        print("资产库为空（结构见 assets/README.md）")
        return
    print(f"共 {len(items)} 个资产:\n")
    for it in items:
        rel = it['path'].replace('\\', '/')
        meta = it.get('meta')
        extra = f" → {meta['url']}" if meta and meta.get('url') else ''
        print(f"  [{it['status']:<9}] {it['type']}"
              + (f"/{it['project']}" if it.get('project') else '')
              + f"  {rel}{extra}")


def cmd_asset_put(args):
    """写入一个待发布资产（默认进 drafts）"""
    import json
    from publishing.asset_store import AssetStore

    content = args.content
    if args.content_file:
        with open(args.content_file, 'r', encoding='utf-8') as f:
            content = f.read()

    r = AssetStore(root=args.root).put(args.type_, args.name, content=content,
                                       src=args.src, project=args.project,
                                       status=args.status)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    if not r['success']:
        print(f"❌ {r['error']}")
        sys.exit(1)
    else:
        print(f"   位置: {r['path']}")


def cmd_asset_publish(args):
    """发布一个 drafts 资产（成功自动归档到 published/ + meta.json）"""
    import json
    from publishing.asset_store import AssetStore, _publish_one

    r = _publish_one(AssetStore(root=args.root), args)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    if r.get('success'):
        if not args.json:
            print(f"   平台: {r.get('platform')}  链接: {r.get('url') or '(平台后台查看)'}")
    else:
        if not args.json:
            print(f"❌ {r.get('error')}")
        sys.exit(1)


def cmd_asset_spaces(args):
    """列出飞书知识库映射（FEISHU_WIKI_SPACES）"""
    import json
    from publishing.asset_store import AssetStore

    spaces = AssetStore(root=args.root).spaces()
    if args.json:
        print(json.dumps({'spaces': spaces}, ensure_ascii=False, indent=2))
    elif spaces:
        for s in spaces:
            print(f"  {s['name']} → {s['space_id']}")
    else:
        print("（FEISHU_WIKI_SPACES 未配置，在 .env 加 名称:space_id,...）")


def cmd_asset_init(args):
    """建齐资产库目录骨架（平台 × 草稿/已发布）"""
    import json
    from publishing.asset_store import AssetStore

    r = AssetStore(root=args.root).ensure_layout(gitkeep=not args.no_gitkeep)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    if not r['created']:
        print(f"✅ 资产库骨架已就绪（{len(r['existing'])} 个目录，无事可做）")
        return
    print(f"✅ 新建 {len(r['created'])} 个目录：")
    for rel in r['created']:
        print(f"   + {rel}")
    if r['existing']:
        print(f"   （已有 {len(r['existing'])} 个目录保持不变）")


def register(subparsers):
    p_asset = subparsers.add_parser('asset', help='素材资产管理（标签/检索/统计）+ 待发布资产库')
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

    # ---- 待发布资产库（assets/，publishing/ 的数据契约）----
    p_als = asset_sub.add_parser('ls', help='待发布资产清单（drafts/published）')
    p_als.add_argument('--type', dest='type_', choices=['novels', 'articles', 'videos', 'wikis'],
                       help='按创作域过滤')
    p_als.add_argument('--project', help='按工程过滤（书名/专栏/系列/知识库）')
    p_als.add_argument('--status', choices=['drafts', 'published'])
    p_als.add_argument('--json', action='store_true', help='输出 JSON')
    p_als.add_argument('--root', help='资产库根目录（默认 <仓库>/assets）')
    p_als.set_defaults(func=cmd_asset_ls)

    p_aput = asset_sub.add_parser('put', help='写入待发布资产（默认 drafts）')
    p_aput.add_argument('--type', dest='type_',
                        choices=['novels', 'articles', 'videos', 'wikis'], required=True)
    p_aput.add_argument('--project', help='工程名（书名/专栏/系列/知识库；wikis 可省略）')
    p_aput.add_argument('--name', required=True, help='资产文件名')
    p_aput.add_argument('--content', help='文本内容')
    p_aput.add_argument('--content-file', help='从文件读取内容')
    p_aput.add_argument('--src', help='源文件路径（视频/图片拷贝）')
    p_aput.add_argument('--status', choices=['drafts', 'published'], default='drafts')
    p_aput.add_argument('--json', action='store_true', help='输出 JSON')
    p_aput.add_argument('--root', help='资产库根目录（默认 <仓库>/assets）')
    p_aput.set_defaults(func=cmd_asset_put)

    p_apub = asset_sub.add_parser('publish', help='发布 drafts 资产（成功自动归档）')
    p_apub.add_argument('--file', required=True, help='资产文件路径')
    p_apub.add_argument('--platform', choices=['feishu', 'wechat', 'douyin'],
                        help='目标平台（默认按创作域推断，可覆盖）')
    p_apub.add_argument('--space', help='飞书目标知识库名（wikis 默认取工程名）')
    p_apub.add_argument('--title', help='标题（默认取文件名）')
    p_apub.add_argument('--tags', nargs='*', help='抖音话题标签')
    p_apub.add_argument('--cover', help='公众号封面图路径')
    p_apub.add_argument('--json', action='store_true', help='输出 JSON')
    p_apub.add_argument('--root', help='资产库根目录（默认 <仓库>/assets）')
    p_apub.set_defaults(func=cmd_asset_publish)

    p_asp = asset_sub.add_parser('spaces', help='列出飞书知识库映射')
    p_asp.add_argument('--json', action='store_true', help='输出 JSON')
    p_asp.add_argument('--root', help='资产库根目录（默认 <仓库>/assets）')
    p_asp.set_defaults(func=cmd_asset_spaces)

    p_ainit = asset_sub.add_parser('init', help='建齐资产库目录骨架（创作域×草稿/已发布）')
    p_ainit.add_argument('--no-gitkeep', action='store_true', help='不写 .gitkeep 占位文件')
    p_ainit.add_argument('--json', action='store_true', help='输出 JSON')
    p_ainit.add_argument('--root', help='资产库根目录（默认 <仓库>/assets）')
    p_ainit.set_defaults(func=cmd_asset_init)
