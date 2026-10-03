"""dashboard 命令域 — Web 看板启动（默认仅本机可访问）"""

import os
import sys


def cmd_dashboard_start(args):
    """启动 Web 数据看板"""
    import importlib.util
    spec = importlib.util.find_spec('flask')
    if spec is None:
        print("Flask 未安装，正在安装...")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask'])

    host = args.host
    print("🎬 启动 AI 内容生产中台 — Web 数据看板")
    print(f"   访问地址: http://localhost:{args.port}（绑定 {host}）")
    if host != '127.0.0.1':
        print("   ⚠️  当前绑定非本机地址，看板无鉴权，请确保网络环境可信")
    print("   按 Ctrl+C 停止\n")

    from workbench.app import create_app
    app = create_app()
    app.run(host=host, port=args.port, debug=False)


def register(subparsers):
    p_dash = subparsers.add_parser('dashboard', help='Web 数据看板')
    dash_sub = p_dash.add_subparsers(dest='dash_cmd', help='看板子命令')

    p_ds = dash_sub.add_parser('start', help='启动 Web 看板')
    p_ds.add_argument('--port', type=int, default=5000, help='端口号')
    p_ds.add_argument('--host', default=os.getenv('DASHBOARD_HOST', '127.0.0.1'),
                      help='绑定地址（默认 127.0.0.1 仅本机；环境变量 DASHBOARD_HOST 可覆盖）')
    p_ds.set_defaults(func=cmd_dashboard_start)
