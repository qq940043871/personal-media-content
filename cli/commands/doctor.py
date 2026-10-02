"""
media-cli doctor — 环境自检

把「接入新模型 / 发布链路排查」的人工验证步骤产品化：

    python media-cli.py doctor            # 静态检查（配置/依赖/存储/数据库）
    python media-cli.py doctor --live     # 加做探活（LLM 实调 + 发布平台健康检查）
    python media-cli.py doctor --json     # 机器可读输出（供 Agent 消化）

退出码：有 FAIL 项 → 1，否则 0（WARN 不影响）。
"""

import os
import shutil
import subprocess
import sys


def _mask(value, keep=8):
    if not value:
        return '（空）'
    return f"{value[:keep]}****({len(value)}字符)"


def _run_cmd(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, encoding='utf-8', errors='replace', timeout=60)
        return (r.returncode, (r.stdout or '').strip(), (r.stderr or '').strip())
    except Exception as e:
        return -1, '', str(e)


def _collect_checks(live):
    """执行全部检查，返回 [{name, status, detail}]；status ∈ pass/warn/fail"""
    checks = []

    def add(name, ok, detail='', warn_if_fail=False):
        status = 'pass' if ok else ('warn' if warn_if_fail else 'fail')
        checks.append({'name': name, 'status': status, 'detail': detail})

    # ---- 1. core / .env ----
    try:
        from core.config import config, PROVIDER_ERRORS
        add('core 导入', True, f"BASE_DIR={config.BASE_DIR}")
    except Exception as e:
        add('core 导入', False, f'{type(e).__name__}: {e}')
        return checks

    env_path = os.path.join(config.BASE_DIR, '.env')
    add('.env 存在', os.path.exists(env_path),
        env_path if os.path.exists(env_path) else f'缺少 {env_path}（可从 .env.example 复制）')

    # ---- 2. Provider 注册表 ----
    from core.providers.registry import list_providers, resolve, ProviderError

    providers = list_providers()
    add('Provider 注册表', bool(providers),
        ', '.join(sorted(providers)) or '空（各能力将回落旧键 LLM_* / ASR_*）',
        warn_if_fail=True)

    for task, var in (('chat', 'LLM_PROVIDER'), ('asr', 'ASR_PROVIDER'), ('image', 'IMAGE_PROVIDER')):
        try:
            c = resolve(task)
            add(f'模型能力 {task}', True,
                f"provider={c.provider}  base={c.base_url}  model={c.model}  key={_mask(c.api_key)}",
                warn_if_fail=(task == 'image'))
        except ProviderError as e:
            add(f'模型能力 {task}', False, str(e), warn_if_fail=(task == 'image'))

    if PROVIDER_ERRORS:
        for task, err in PROVIDER_ERRORS.items():
            add(f'注册表回退 {task}', False, err, warn_if_fail=True)

    # ---- 3. 存储可写 ----
    try:
        config.ensure_base_directories()
        probe = os.path.join(config.STORAGE_BASE, '.doctor_write_test')
        with open(probe, 'w') as f:
            f.write('ok')
        os.remove(probe)
        add('存储目录可写', True, config.STORAGE_BASE)
    except Exception as e:
        add('存储目录可写', False, str(e))

    # ---- 4. 外部工具 ----
    ffmpeg = shutil.which(config.FFMPEG_PATH)
    if ffmpeg:
        code, out, _ = _run_cmd([config.FFMPEG_PATH, '-version'])
        first_line = out.splitlines()[0] if out else ''
        add('FFmpeg', code == 0, first_line or ffmpeg)
    else:
        add('FFmpeg', False, f"找不到 {config.FFMPEG_PATH}，请安装或设 .env 的 FFMPEG_PATH")

    node = shutil.which('node')
    if node:
        code, out, _ = _run_cmd(['node', '--version'])
        add('Node.js', code == 0, (out or node).splitlines()[0])
    else:
        add('Node.js', False, '找不到 node（飞书发布依赖）')

    lark = config.LARK_CLI_RUN_JS
    add('lark-cli run.js', os.path.exists(lark), lark if os.path.exists(lark)
        else f'不存在: {lark}（npm i -g @larksuite/cli 或设 LARK_CLI_RUN_JS）')

    # ---- 5. 数据库 ----
    try:
        from core.task_manager import TaskManager
        stats = TaskManager().stats()
        add('任务库 tasks.db', True, f"任务总数 {stats['total']}")
    except Exception as e:
        add('任务库 tasks.db', False, str(e), warn_if_fail=True)

    try:
        from core.asset_manager import AssetManager
        stats = AssetManager().stats()
        add('素材库 assets.db', True, f"素材总数 {stats['total']}")
    except Exception as e:
        add('素材库 assets.db', False, str(e), warn_if_fail=True)

    # ---- 6. 探活（--live）----
    if live:
        try:
            from core.providers.llm import get_llm_client
            llm = get_llm_client()
            reply = (llm.chat('请只回复两个字：正常') or '').strip()
            add('LLM 探活', bool(reply), f"{llm.model} 回复: {reply[:20]}")
        except Exception as e:
            add('LLM 探活', False, f"{type(e).__name__}: {str(e)[:200]}")

        try:
            from core.publisher_base import MultiPlatformPublisher
            mp = MultiPlatformPublisher()
            for pid, err in mp.init_errors.items():
                add(f'平台 {pid}', False, err, warn_if_fail=(pid == 'wechat' and '未配置' in err))
            for pid, health in mp.health_check_all().items():
                add(f'平台 {pid} 健康', health.success,
                    '连通正常' if health.success else (health.error or '未知原因')[:200])
        except Exception as e:
            add('发布平台检查', False, str(e), warn_if_fail=True)

    return checks


def cmd_doctor(args):
    """环境自检：配置/依赖/存储/数据库（--live 加做探活）"""
    import contextlib

    if args.json:
        # 探活过程中的过程 print（如 access_token 提示）改道 stderr，保持 stdout 纯 JSON
        with contextlib.redirect_stdout(sys.stderr):
            checks = _collect_checks(live=args.live)
    else:
        checks = _collect_checks(live=args.live)

    if args.json:
        import json
        fails = sum(1 for c in checks if c['status'] == 'fail')
        print(json.dumps({'checks': checks, 'fail_count': fails},
                         ensure_ascii=False, indent=2))
    else:
        icon = {'pass': '✅', 'warn': '⚠️ ', 'fail': '❌'}
        print("=" * 62)
        print("  media-cli doctor — 环境自检" + ("（含探活）" if args.live else ""))
        print("=" * 62)
        for c in checks:
            print(f"  {icon[c['status']]} {c['name']:<14} {c['detail']}")
        print("=" * 62)

    if any(c['status'] == 'fail' for c in checks):
        sys.exit(1)


def register(subparsers):
    p_doctor = subparsers.add_parser('doctor', help='环境自检（配置/依赖/探活）')
    p_doctor.add_argument('--live', action='store_true',
                          help='加做探活：LLM 实调 + 发布平台健康检查（会产生一次模型调用）')
    p_doctor.add_argument('--json', action='store_true', help='输出 JSON（供 Agent/脚本消化）')
    p_doctor.set_defaults(func=cmd_doctor)
