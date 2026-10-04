"""story 命令域 — 小说章节转分镜/文章"""

import sys


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


def cmd_story_merge(args):
    """短章合并为平台规格长章（剧情单元边界优先，原稿只读）"""
    from core.chapter_merge import merge_chapters

    mode = f"单章目标 {args.target} 字" if args.target > 0 else f"每组 ≤ {args.per} 章"
    print(f"正在合并 {args.source_dir} → {args.output}（{mode}"
          f"{'，预览' if args.dry_run else ''}）...")
    try:
        result = merge_chapters(args.source_dir, args.output, per=args.per,
                                target=args.target, unit_glob=args.units,
                                dry_run=args.dry_run)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ 合并失败: {e}")
        sys.exit(1)

    groups = result['groups']
    chars = [g['chars'] for g in groups]
    print(f"✅ 合并方案: {len(groups)} 章 / {result['total_chars']} 字"
          f"（单章 {min(chars)}-{max(chars)} 字）")
    for g in groups[:3] + ([{'num': 0, 'title': '…', 'sources': [], 'chars': 0}] if len(groups) > 6 else []) + groups[-3:]:
        if g['num'] == 0:
            print('    ……')
            continue
        src = f"{g['sources'][0]}-{g['sources'][-1]}章" if g['sources'] else '-'
        print(f"    第{g['num']}章 {g['title']}（源 {src}，{g['chars']} 字）")
    if not args.dry_run:
        print(f"💾 已输出: {result['out_dir']}（含 合并对照.md）")


def register(subparsers):
    p_story = subparsers.add_parser('story', help='小说章节工具（合并/转分镜/转文章）')
    story_sub = p_story.add_subparsers(dest='story_cmd', help='内容转换子命令')

    p_ss2 = story_sub.add_parser('script', help='小说章节 → 视频分镜脚本')
    p_ss2.add_argument('input', help='章节文件路径')
    p_ss2.add_argument('-t', '--title', help='章节标题')
    p_ss2.add_argument('-s', '--style', default='玄幻',
                       help='视频风格: 玄幻/科幻/都市/悬疑/古风/末日废土')
    p_ss2.add_argument('-n', '--num-shots', type=int, default=8, help='分镜数量')
    p_ss2.add_argument('-o', '--output', help='输出脚本文件(.md)')
    p_ss2.add_argument('--prompts-output', help='单独输出AI提示词文件')
    p_ss2.set_defaults(func=cmd_story_script)

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
    p_sm = story_sub.add_parser('merge', help='短章合并为平台规格长章（原稿只读）')
    p_sm.add_argument('source_dir', help='源章节目录（文件名含 第N章）')
    p_sm.add_argument('-o', '--output', required=True, help='输出目录（自动创建，含 合并对照.md）')
    p_sm.add_argument('--per', type=int, default=4,
                      help='每个合并章最多包含的源章数（默认 4；target 模式下为章数上限）')
    p_sm.add_argument('--target', type=int, default=0,
                      help='单章字数目标（>0 时按字数贪婪分组，适合源章字数不均的书）')
    p_sm.add_argument('--units', help='剧情单元文件 glob（默认自动找 ../process/5-第*卷-剧情单元.txt）')
    p_sm.add_argument('--dry-run', action='store_true', help='只输出合并方案不写文件')
    p_sm.set_defaults(func=cmd_story_merge)
