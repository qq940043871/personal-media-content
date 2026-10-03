"""doctor 检查结构与 CLI 解析器冒烟（不触网）"""

from cli.app import build_parser
from cli.commands.doctor import _collect_checks


def test_collect_checks_structure():
    """静态自检在任意环境都应产出结构完整的检查项"""
    checks = _collect_checks(live=False)
    assert checks, "至少应有一条检查"
    names = [c['name'] for c in checks]
    assert 'core 导入' in names
    assert '.env 存在' in names
    for c in checks:
        assert c['status'] in ('pass', 'warn', 'fail')
        assert isinstance(c['detail'], str)
    # core 能导入时该项必须 pass
    core_check = next(c for c in checks if c['name'] == 'core 导入')
    assert core_check['status'] == 'pass'


def test_parser_registers_all_commands():
    parser = build_parser()
    usage = parser.format_usage()
    for cmd in ('status', 'doctor', 'video', 'asr', 'llm', 'feishu',
                'wechat', 'publish', 'story', 'asset', 'task', 'storage',
                'dashboard', 'pipeline'):
        assert cmd in usage, cmd


def test_leaf_commands_get_handler():
    parser = build_parser()
    # 顶层叶子命令直接带 func；带子命令的组解析其叶子后也应带 func
    assert parser.parse_args(['status']).func
    assert parser.parse_args(['doctor']).func
    assert parser.parse_args(['publish', '--title', 't']).func
    assert parser.parse_args(['video', 'info', 'x.mp4']).func
    assert parser.parse_args(['storage', 'stats']).func
    assert parser.parse_args(['pipeline', 'video-article']).func


def test_doctor_flags_parse():
    parser = build_parser()
    args = parser.parse_args(['doctor', '--live', '--json'])
    assert args.live is True and args.json is True


def test_status_lists_business_lines():
    from cli.commands.status import BUSINESS_LINES
    # 业务线目录已全部并入主工程（内容在 assets/，能力在 core/，技能在 .claude/skills/）
    assert BUSINESS_LINES == []
    assert 'publish_workbench' not in BUSINESS_LINES
    assert 'hello_webchat_official' not in BUSINESS_LINES
    assert 'hello_novel' not in BUSINESS_LINES
