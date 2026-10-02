"""task 命令域 — 任务列表/统计/详情/重试"""

import sys


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


def register(subparsers):
    p_task = subparsers.add_parser('task', help='任务管理（调度/状态/重试）')
    task_sub = p_task.add_subparsers(dest='task_cmd', help='任务子命令')

    p_tl = task_sub.add_parser('list', help='列出任务')
    p_tl.add_argument('--status', choices=['pending', 'running', 'done', 'failed', 'skipped'],
                      help='按状态过滤')
    p_tl.add_argument('--type', help='按类型过滤')
    p_tl.add_argument('--limit', type=int, default=20, help='数量限制')
    p_tl.add_argument('--offset', type=int, default=0, help='偏移量')
    p_tl.set_defaults(func=cmd_task_list)

    p_ts = task_sub.add_parser('stats', help='任务统计')
    p_ts.set_defaults(func=cmd_task_stats)

    p_td = task_sub.add_parser('detail', help='任务详情')
    p_td.add_argument('task_id', help='任务 ID')
    p_td.set_defaults(func=cmd_task_detail)

    p_tr = task_sub.add_parser('retry', help='重试失败任务')
    p_tr.add_argument('--type', help='按类型过滤')
    p_tr.set_defaults(func=cmd_task_retry)
