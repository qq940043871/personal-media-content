"""
Web 数据看板 + 项目工作台 — Flask 轻量管理面板

功能：
- 总览仪表盘（任务统计、素材统计、产出统计）
- 任务列表（按状态/类型过滤）
- 任务详情与日志
- 素材检索
- 项目工作台：新建/管理图文、小说、视频项目，编辑正文，一键发布（后台线程），
  发布历史与平台体检

启动方式：
    python -m workbench.app
    python media-cli.py dashboard start

绑定地址默认 127.0.0.1（仅本机），可用环境变量 DASHBOARD_HOST 覆盖。
默认端口：5000，访问地址：http://localhost:5000
"""

import os
import sys
import threading
from flask import Flask, render_template, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.task_manager import TaskManager
from core.asset_manager import AssetManager
from core.project_manager import ProjectManager, PROJECT_STATUSES, ProjectError
from core.inventory import ContentInventory
from core.config import config


def _article_content_path(pid):
    """图文项目正文默认路径（system/storage/articles/projects/<id>.md，不入库）"""
    return os.path.join(config.STORAGE_ARTICLES, 'projects', f'{pid}.md')


def _read_article_content(project):
    try:
        with open(project['content_path'], 'r', encoding='utf-8') as f:
            return f.read()
    except OSError:
        return ''


def _count_chapters(book_name):
    """小说项目关联章节统计（找不到目录返回 0）"""
    for sub in ('chapters', os.path.join('novel', 'chapters')):
        base = os.path.join(config.BASE_DIR, 'assets', 'novels', book_name, sub)
        if os.path.isdir(base):
            return len([f for f in os.listdir(base)
                        if f.lower().endswith(('.txt', '.md'))
                        and not f.upper().startswith('README')])
    return 0


def _run_publish(pid, platform, project, record_id):
    """发布线程：独立实例（SQLite 每操作独立连接），结果回写发布记录"""
    from publishing.publisher_base import MultiPlatformPublisher

    pm = ProjectManager()
    try:
        mp = MultiPlatformPublisher()
        if project['project_type'] == 'article':
            content = _read_article_content(project)
            result = mp.publish(platform, project['name'], content,
                                options={'cover_image': project.get('cover_path') or None})
        else:
            result = mp.publish(platform, project['name'], '',
                                options={'video': project.get('video_path')})
        pm.finish_publish(record_id, 'success' if result.success else 'failed',
                          url=result.get('url', ''), error=result.get('error', ''))
    except Exception as e:
        pm.finish_publish(record_id, 'failed', error=f'{type(e).__name__}: {e}')


def create_app():
    app = Flask(__name__)
    app.config['JSON_AS_ASCII'] = False

    tm = TaskManager()
    am = AssetManager()
    pm = ProjectManager()
    inv = ContentInventory()

    # ===== 页面路由 =====

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/workbench')
    def workbench_page():
        return render_template('workbench.html')

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

    @app.route('/api/inventory')
    def api_inventory():
        """创作统计：小说/文章/分析/视频稿/成片/发布记录盘点"""
        return jsonify(inv.summary())

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

    # ===== 项目工作台 API =====

    @app.route('/api/projects')
    def api_projects():
        """项目列表 + 统计"""
        projects = pm.list_projects(
            project_type=request.args.get('type') or None,
            status=request.args.get('status') or None,
        )
        return jsonify({'projects': projects, 'stats': pm.stats()})

    @app.route('/api/projects', methods=['POST'])
    def api_create_project():
        """新建项目；图文项目自动创建正文文件"""
        data = request.get_json() or {}
        try:
            project = pm.create_project(
                name=data.get('name', ''),
                project_type=data.get('project_type', ''),
                description=data.get('description', ''),
                content_path=data.get('content_path', ''),
                video_path=data.get('video_path', ''),
                cover_path=data.get('cover_path', ''),
                book_name=data.get('book_name', ''),
                tags=data.get('tags'),
            )
        except ProjectError as e:
            return jsonify({'error': str(e)}), 400

        if project['project_type'] == 'article' and not project['content_path']:
            path = _article_content_path(project['id'])
            body = f"# {project['name']}\n\n"
            if project['description']:
                body += f"{project['description']}\n"
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(body)
            project = pm.update_project(project['id'], content_path=path)
        return jsonify({'project': project}), 201

    @app.route('/api/projects/<pid>')
    def api_project_detail(pid):
        """项目详情：资料 + 正文 + 发布记录 + 小说章节统计"""
        project = pm.get_project(pid)
        if not project:
            return jsonify({'error': '项目不存在'}), 404

        detail = {
            'project': project,
            'publish_records': pm.list_publish_records(project_id=pid),
        }
        if project['project_type'] == 'article' and project['content_path']:
            detail['content'] = _read_article_content(project)
        if project['project_type'] == 'novel' and project['book_name']:
            detail['chapter_count'] = _count_chapters(project['book_name'])
        return jsonify(detail)

    @app.route('/api/projects/<pid>', methods=['PUT'])
    def api_update_project(pid):
        """更新项目资料（白名单字段）"""
        data = request.get_json() or {}
        if data.get('status') and data['status'] not in PROJECT_STATUSES:
            return jsonify({'error': f"未知状态: {data['status']}"
                                     f'（可选: {", ".join(PROJECT_STATUSES)}）'}), 400
        fields = {k: v for k, v in data.items() if k in (
            'name', 'status', 'description', 'content_path',
            'video_path', 'cover_path', 'book_name', 'tags')}
        try:
            project = pm.update_project(pid, **fields)
        except ProjectError as e:
            return jsonify({'error': str(e)}), 404
        return jsonify({'project': project})

    @app.route('/api/projects/<pid>', methods=['DELETE'])
    def api_delete_project(pid):
        deleted = pm.delete_project(pid)
        if not deleted:
            return jsonify({'error': '项目不存在'}), 404
        return jsonify({'ok': True})

    @app.route('/api/projects/<pid>/content', methods=['POST'])
    def api_save_content(pid):
        """保存图文项目正文"""
        project = pm.get_project(pid)
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        if project['project_type'] != 'article':
            return jsonify({'error': '仅图文项目支持正文编辑'}), 400

        data = request.get_json() or {}
        path = project['content_path'] or _article_content_path(pid)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(data.get('content', ''))
        project = pm.update_project(pid, content_path=path)
        return jsonify({'ok': True, 'content_path': path, 'project': project})

    @app.route('/api/platforms')
    def api_platforms():
        """发布平台可用性（未配置原因见 error）"""
        from publishing.publisher_base import MultiPlatformPublisher, KNOWN_PLATFORMS
        mp = MultiPlatformPublisher()
        available = mp.available_platforms()
        platforms = [{'id': pid, 'available': pid in available,
                      'error': mp.init_errors.get(pid, '')}
                     for pid in KNOWN_PLATFORMS]
        return jsonify({'platforms': platforms})

    @app.route('/api/platforms/health', methods=['POST'])
    def api_platforms_health():
        """平台体检（实测连通性，较慢：飞书走 lark-cli、抖音会启动无头浏览器）"""
        from publishing.publisher_base import MultiPlatformPublisher
        mp = MultiPlatformPublisher()
        health = {pid: {'success': r.success, 'error': r.error}
                  for pid, r in mp.health_check_all().items()}
        return jsonify({'health': health, 'init_errors': mp.init_errors})

    @app.route('/api/projects/<pid>/publish', methods=['POST'])
    def api_publish_project(pid):
        """发布项目到指定平台（后台线程，立即返回；结果轮询详情接口）"""
        project = pm.get_project(pid)
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        data = request.get_json() or {}
        platforms = data.get('platforms') or []
        if not platforms:
            return jsonify({'error': '未指定发布平台'}), 400

        # 发布前同步校验，材料缺失直接 400（不让问题落到后台线程）
        if project['project_type'] == 'article':
            if not _read_article_content(project).strip():
                return jsonify({'error': '正文为空，请先在详情中编辑并保存正文'}), 400
        elif project['project_type'] == 'video':
            if not project['video_path'] or not os.path.exists(project['video_path']):
                return jsonify({'error': f'视频文件不存在: {project["video_path"]}，'
                                         f'请先在详情中填写成片路径'}), 400
        else:
            return jsonify({'error': '小说项目暂不支持直接发布'
                                     '（可先用 story article 转化为图文项目）'}), 400

        from publishing.publisher_base import MultiPlatformPublisher, KNOWN_PLATFORMS
        mp = MultiPlatformPublisher()
        for p in platforms:
            if p not in KNOWN_PLATFORMS:
                return jsonify({'error': f'未知平台: {p}'}), 400
            if p not in mp.available_platforms():
                return jsonify({'error': f'平台 {p} 不可用: '
                                         f'{mp.init_errors.get(p, "未配置")}'}), 400

        started = []
        for p in platforms:
            rid = pm.start_publish(pid, p, title=project['name'])
            started.append({'record_id': rid, 'platform': p})
            threading.Thread(target=_run_publish, args=(pid, p, project, rid),
                             daemon=True).start()
        return jsonify({'started': started}), 202

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
