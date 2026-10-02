"""
Web 数据看板 — Flask 轻量管理面板

功能：
- 总览仪表盘（任务统计、素材统计、产出统计）
- 任务列表（按状态/类型过滤）
- 任务详情与日志
- 素材检索

启动方式：
    python -m dashboard.app
    python media-cli.py dashboard start

绑定地址默认 127.0.0.1（仅本机），可用环境变量 DASHBOARD_HOST 覆盖。
默认端口：5000，访问地址：http://localhost:5000
"""

import os
import sys
from flask import Flask, render_template, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.task_manager import TaskManager
from core.asset_manager import AssetManager
from core.config import config


def create_app():
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False

    tm = TaskManager()
    am = AssetManager()

    # ===== 页面路由 =====

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/tasks')
    def tasks_page():
        return render_template('tasks.html')

    @app.route('/assets')
    def assets_page():
        return render_template('assets.html')
    # ===== API 路由 =====

    @app.route('/api/stats')
    def api_stats():
        """总览统计"""
        task_stats = tm.stats()
        asset_stats = am.stats()

        # 存储统计（文件系统）
        from core.storage import Storage
        storage = Storage()
        storage_stats = storage.stats()

        return jsonify({
            'tasks': task_stats,
            'assets': asset_stats,
            'storage': storage_stats,
        })

    @app.route('/api/tasks')
    def api_tasks():
        """任务列表"""
        status = request.args.get('status')
        task_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        tasks = tm.list_tasks(status=status, task_type=task_type, limit=limit, offset=offset)
        return jsonify({'tasks': tasks, 'total': len(tasks)})

    @app.route('/api/tasks/<task_id>')
    def api_task_detail(task_id):
        """任务详情"""
        task = tm.get_task(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        logs = tm.get_task_logs(task_id)
        return jsonify({'task': task, 'logs': logs})

    @app.route('/api/tasks/retry', methods=['POST'])
    def api_retry_tasks():
        """重试失败任务"""
        data = request.get_json() or {}
        task_type = data.get('type')
        count = tm.retry_failed_tasks(task_type=task_type)
        return jsonify({'reset_count': count})

    @app.route('/api/assets')
    def api_assets():
        """素材列表"""
        asset_type = request.args.get('type')
        project = request.args.get('project')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        assets = am.list_assets(asset_type=asset_type, project=project, limit=limit, offset=offset)
        stats = am.stats()
        return jsonify({'assets': assets, 'stats': stats})

    @app.route('/api/assets/search')
    def api_assets_search():
        """按标签搜索素材"""
        tags = request.args.get('tags', '').split(',')
        tags = [t.strip() for t in tags if t.strip()]
        if not tags:
            return jsonify({'assets': []})

        match_all = request.args.get('match', 'all') == 'all'
        assets = am.search_by_tags(tags, match_all=match_all)
        return jsonify({'assets': assets})

    @app.route('/api/tags')
    def api_tags():
        """所有标签"""
        project = request.args.get('project')
        tags = am.list_all_tags(project=project)
        return jsonify({'tags': tags})

    return app


def main():
    host = os.getenv('DASHBOARD_HOST', '127.0.0.1')
    port = int(os.getenv('DASHBOARD_PORT', '5000'))
    app = create_app()
    print("🎬 AI 内容生产中台 — 数据看板")
    print(f"访问地址: http://localhost:{port}（绑定 {host}）")
    print("按 Ctrl+C 停止\n")
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    main()
